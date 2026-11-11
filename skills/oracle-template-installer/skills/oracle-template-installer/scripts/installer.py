"""Scope selection and recoverable publication of the frozen Oracle library."""

from __future__ import annotations

import base64
import ctypes
import difflib
import fcntl
import hashlib
import hmac
import json
import os
import secrets
import shutil
import signal
import stat
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import runtime as rt


SCHEMA = 1
KINDS = ("brand", "layout")
RELATIVE_OBJECTS = {
    "brand": "templates/brands/oracle",
    "layout": "templates/layouts/oracle",
    "brand_index": "templates/brands/brands_index.json",
    "layout_index": "templates/layouts/layouts_index.json",
}
EXIT = {"usage": 2, "blocked": 3, "stale": 4, "busy": 5,
        "confirmation_required": 6, "recovery_conflict": 7,
        "rolled_back": 8, "invalid_plan": 9, "interrupted": 10}


class InjectedFailure(RuntimeError):
    pass


class InstallFailure(ValueError):
    def __init__(self, code: str, message: str, **details):
        super().__init__(message)
        self.code, self.details = code, details

    def result(self) -> dict:
        return {"status": self.code, "message": str(self), **self.details}


@dataclass(frozen=True)
class RuntimeCandidate:
    real_path: str
    display_paths: list[str]
    scope: Literal["global", "project"]
    sources: list[str]
    python: str | None = None
    compatibility: str = "unprobed"
    reason: str = "Run inspect --probe or plan with an isolated --work directory."


@dataclass(frozen=True)
class Selection:
    ppt_scope: Literal["global", "project"]
    oracle_scope: Literal["global", "project"]
    project: str | None
    home: str

    @property
    def root(self) -> Path:
        return Path(self.project if self.ppt_scope == "project" else self.home)


@dataclass(frozen=True)
class InstallPlan:
    schema: int
    id: str
    selection: dict
    work: str
    runtime: str
    explicit_runtime: str | None
    runtime_action: Literal["reuse", "install", "blocked"]
    template_action: Literal["keep", "register", "install", "replace", "blocked"]
    python: str
    bound_python: str
    environment: str | None
    release_sha256: str
    implementation: dict
    ancestors: dict
    discovery: dict
    preimages: dict
    code_preimages: dict
    interpreter: dict
    proof: dict
    indices: dict
    expected_entries: dict
    changes: list
    backups: dict
    postconditions: dict
    paths: dict
    consent_required: bool


@dataclass
class TransactionReceipt:
    schema: int
    plan_id: str
    plan_digest: str
    status: str
    runtime: str
    work: str
    ancestors: dict
    preimages: dict
    operations: list
    backups: dict
    environment: dict | None
    events: list
    verification: dict
    error: str | None = None


def canonical_json(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value) -> str:
    return rt.sha256(canonical_json(value))


def same_json(left, right) -> bool:
    return canonical_json(left) == canonical_json(right)


def json_value(raw: bytes):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise InstallFailure("blocked", f"Duplicate JSON key: {key}")
            value[key] = item
        return value

    def bad_constant(value):
        raise InstallFailure("blocked", f"Non-finite JSON number: {value}")

    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=bad_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise InstallFailure("blocked", f"Malformed JSON: {exc}") from exc


def absolute(value: str | Path) -> Path:
    return Path(os.path.abspath(os.path.expanduser(str(value))))


def inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def identity(path: Path) -> dict:
    info = path.lstat()
    return {"device": info.st_dev, "inode": info.st_ino, "mode": info.st_mode}


def safe_path(path: Path, *, directory: bool | None = None, absent_ok: bool = True) -> dict:
    if not path.is_absolute() or absolute(path) != path:
        raise InstallFailure("blocked", f"Path is not normalized and absolute: {path}")
    found = {}
    chain = [*reversed(path.parents), path]
    missing = False
    for component in chain:
        if missing:
            continue
        try:
            info = component.lstat()
        except FileNotFoundError:
            missing = True
            continue
        if stat.S_ISLNK(info.st_mode):
            raise InstallFailure("blocked", f"Symlink target or ancestor: {component}")
        if component != path or directory is True:
            if not stat.S_ISDIR(info.st_mode):
                raise InstallFailure("blocked", f"Expected a directory: {component}")
        elif directory is False and not stat.S_ISREG(info.st_mode):
            raise InstallFailure("blocked", f"Expected a regular file: {component}")
        found[str(component)] = identity(component)
    if missing and not absent_ok:
        raise InstallFailure("blocked", f"Path does not exist: {path}")
    return found


def snapshot(path: Path, *, links: bool = False) -> dict:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return {"kind": "absent"}
    entries = {}

    def visit(node: Path, name: str):
        st = node.lstat()
        item = {"device": st.st_dev, "inode": st.st_ino,
                "mode": st.st_mode, "mtime_ns": st.st_mtime_ns}
        if stat.S_ISLNK(st.st_mode) and links:
            item.update(kind="symlink", target=os.readlink(node))
        elif stat.S_ISDIR(st.st_mode):
            item["kind"] = "directory"
        elif stat.S_ISREG(st.st_mode):
            item.update(kind="file", size=st.st_size, sha256=rt.sha256(node.read_bytes()))
            if node.lstat() != st:
                # Reading may update atime, which is deliberately outside the preimage.
                later = node.lstat()
                if (st.st_ino, st.st_mtime_ns, st.st_size, st.st_mode) != (later.st_ino, later.st_mtime_ns, later.st_size, later.st_mode):
                    raise InstallFailure("stale", f"File changed while being read: {node}")
        else:
            raise InstallFailure("blocked", f"Symlink or special object: {node}")
        entries[name] = item
        if item["kind"] == "directory":
            for child in sorted(node.iterdir()):
                visit(child, child.name if name == "." else name + "/" + child.name)

    visit(path, ".")
    return {"kind": entries["."]["kind"], "entries": entries}


def content(snapshot_value: dict, *, metadata: bool = False) -> dict:
    if snapshot_value["kind"] == "absent":
        return snapshot_value
    keys = {"kind", "sha256", "size", "target"}
    if metadata:
        keys.update({"mode", "mtime_ns"})
    return {"kind": snapshot_value["kind"], "entries": {
        name: {key: value for key, value in item.items() if key in keys}
        for name, item in snapshot_value["entries"].items()}}


def fsync_dir(path: Path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def sync_tree(path: Path):
    if path.is_symlink():
        return
    if path.is_dir():
        for child in path.iterdir():
            sync_tree(child)
        fsync_dir(path)
    else:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def mkdirs(path: Path):
    safe_path(path, directory=True)
    missing = []
    current = path
    while not current.exists():
        missing.append(current)
        current = current.parent
    for current in reversed(missing):
        try:
            current.mkdir(mode=0o700)
            fsync_dir(current.parent)
        except FileExistsError:
            safe_path(current, directory=True, absent_ok=False)


def atomic_bytes(path: Path, value: bytes, *, exclusive: bool = False):
    safe_path(path, directory=False)
    mkdirs(path.parent)
    temporary = path.parent / ("." + path.name + "." + secrets.token_hex(8))
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(value)
            output.flush()
            os.fsync(output.fileno())
        if exclusive:
            os.link(temporary, path, follow_symlinks=False)
            temporary.unlink()
        else:
            os.replace(temporary, path)
        fsync_dir(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def work_key(work: Path, *, create: bool = False) -> bytes:
    safe_path(work, directory=True)
    key_path = work / ".oracle-installer-key"
    if not key_path.exists() and create:
        if work.exists() and any(work.iterdir()):
            raise InstallFailure("blocked", f"Work directory is not empty or installer-owned: {work}")
        mkdirs(work)
        atomic_bytes(key_path, secrets.token_bytes(32), exclusive=True)
    safe_path(key_path, directory=False, absent_ok=False)
    key = key_path.read_bytes()
    if len(key) != 32 or key_path.stat().st_mode & 0o077:
        raise InstallFailure("invalid_plan", "Invalid or publicly readable work key")
    return key


def seal(value: dict, key: bytes, kind: str) -> dict:
    body = {"kind": kind, "value": value, "digest": digest(value)}
    return {**body, "seal": hmac.new(key, canonical_json(body), hashlib.sha256).hexdigest()}


def unseal(raw: bytes, key: bytes, kind: str) -> dict:
    try:
        envelope = json_value(raw)
        if set(envelope) != {"kind", "value", "digest", "seal"} or envelope["kind"] != kind:
            raise ValueError("Envelope shape differs")
        expected = seal(envelope["value"], key, kind)
        if not hmac.compare_digest(canonical_json(envelope), canonical_json(expected)):
            raise ValueError("Envelope authentication differs")
        return envelope["value"]
    except (ValueError, TypeError, KeyError) as exc:
        raise InstallFailure("invalid_plan", f"Edited or invalid {kind}: {exc}") from exc


def save_sealed(path: Path, value: dict, key: bytes, kind: str):
    atomic_bytes(path, canonical_json(seal(value, key, kind)) + b"\n")


def selection(ppt_scope: str, oracle_scope: str, project: str | None, home: str) -> Selection:
    if ppt_scope not in {"global", "project"} or oracle_scope not in {"global", "project"}:
        raise InstallFailure("usage", "Both scopes must be global or project")
    if ppt_scope != oracle_scope:
        raise InstallFailure("blocked", "PPT Master and Oracle scopes differ; align the two explicit choices.")
    home_path = absolute(home)
    project_path = absolute(project) if project else None
    safe_path(home_path, directory=True, absent_ok=False)
    if project_path:
        safe_path(project_path, directory=True, absent_ok=False)
    if ppt_scope == "project" and (project_path is None or project_path == home_path):
        raise InstallFailure("blocked", "Project scope requires its own existing project root")
    return Selection(ppt_scope, oracle_scope, str(project_path) if project_path else None, str(home_path))


def discover(chosen: Selection, explicit: Path | None = None) -> tuple[list[RuntimeCandidate], dict]:
    roots = [(chosen.ppt_scope, chosen.root)]
    groups, observed = {}, {}
    for scope, root in roots:
        paths = [(root / client / "skills/ppt-master", client) for client in (".agents", ".codex", ".cursor")]
        if explicit and scope == chosen.ppt_scope:
            paths.append((explicit, "explicit"))
        for path, source in paths:
            if not path.exists() and not path.is_symlink():
                safe_path(path, directory=True)
                observed[str(path)] = {"kind": "absent"}
                continue
            alias = path.is_symlink() and source in {".codex", ".cursor"}
            safe_path(path.parent, directory=True)
            if alias:
                try:
                    real = path.resolve(strict=True)
                except (OSError, RuntimeError) as exc:
                    raise InstallFailure("blocked", f"Unresolvable client alias: {path}") from exc
                observed[str(path)] = {"kind": "alias", **identity(path), "target": os.readlink(path)}
            else:
                safe_path(path, directory=True, absent_ok=False)
                real = path
                observed[str(path)] = {"kind": "directory", **identity(path)}
            safe_path(real, directory=True, absent_ok=False)
            if not inside(real, root) or real == root:
                raise InstallFailure("blocked", f"Runtime escapes selected {scope} root: {real}")
            if scope == "global" and chosen.project and inside(real, Path(chosen.project)):
                raise InstallFailure("blocked", f"Global selection resolves to the supplied project: {real}")
            entry = groups.setdefault((scope, str(real)), {"paths": [], "sources": []})
            entry["paths"].append(str(path))
            entry["sources"].append(source)
    candidates = [RuntimeCandidate(path, sorted(set(value["paths"])), scope, sorted(set(value["sources"])))
                  for (scope, path), value in sorted(groups.items())]
    return candidates, observed


def choose_runtime(chosen: Selection, explicit: Path | None) -> tuple[Path, dict, list[RuntimeCandidate]]:
    candidates, observed = discover(chosen, explicit)
    matching = [item for item in candidates if item.scope == chosen.ppt_scope]
    if explicit:
        safe_path(explicit, directory=True)
        if not inside(explicit, chosen.root) or explicit == chosen.root:
            raise InstallFailure("blocked", "Explicit runtime is outside the selected scope")
        target = explicit
    elif len(matching) > 1:
        raise InstallFailure("blocked", "Multiple real runtimes require --runtime", candidates=[asdict(item) for item in matching])
    elif matching:
        target = Path(matching[0].real_path)
    else:
        target = chosen.root / ".agents/skills/ppt-master"
    if not target.exists() and target != chosen.root / ".agents/skills/ppt-master":
        raise InstallFailure("blocked", "New runtimes use the canonical .agents/skills/ppt-master path")
    observed = {name: value for name, value in observed.items() if inside(Path(name), chosen.root)
                and (chosen.ppt_scope != "global" or not chosen.project or not inside(Path(name), Path(chosen.project)))}
    return target, observed, candidates


def paths_for(target: Path, plan_id: str, work: Path) -> dict:
    state = target.parent / ("." + target.name + ".oracle-installer")
    transaction = state / "transactions" / plan_id
    return {"state": str(state), "lock": str(state / "lock"), "transaction": str(transaction),
            "stage": str(transaction / "stage"), "backup": str(transaction / "backups"),
            "receipt": str(work / "receipts" / (plan_id + ".json")),
            "environment": str(state / "environments" / plan_id / "venv")}


def implementation() -> dict:
    return {name: rt.sha256((Path(__file__).parent / name).read_bytes())
            for name in ("installer.py", "install.py", "runtime.py", "verify_runtime.py")}


LOADED_IMPLEMENTATION = implementation()


def current_sources() -> dict:
    current = implementation()
    if current != LOADED_IMPLEMENTATION:
        raise InstallFailure("stale", "Installer or runtime sources changed after this process loaded them")
    return current


def code_snapshot(target: Path) -> dict:
    result = {name: snapshot(rt.regular(target, name)) for name in rt.fingerprint(target)}
    result[rt.BINDING] = snapshot(target / rt.BINDING)
    return result


def interpreter_snapshot(python: Path, work: Path) -> dict:
    python = absolute(python)
    safe_path(python.parent.resolve(), directory=True, absent_ok=False)
    if not python.exists() or not python.is_file() or not os.access(python, os.X_OK):
        raise InstallFailure("blocked", f"Interpreter is not executable: {python}")
    facts = rt.interpreter_facts(python, work)
    prefix = Path(facts["prefix"])
    result = {"requested": str(python), "launcher": snapshot(python, links=True),
              "executable": snapshot(python.resolve()), "facts": facts,
              "ancestor_links": {str(p): {**identity(p), "target": os.readlink(p)}
                                 for p in python.parents if p.is_symlink()}}
    config = prefix / "pyvenv.cfg"
    if config.exists():
        safe_path(prefix, directory=True, absent_ok=False)
        result["environment"] = snapshot(prefix, links=True)
    else:
        script = ("import importlib.metadata as m,json; r={}; "
                  "\nfor n in " + repr([item["name"] if isinstance(item, dict) else item for item in rt.load_release()["dependencies"]]) + ":\n"
                  " try:\n  d=m.distribution(n);r[n]={'version':d.version,'files':[str(d.locate_file(f)) for f in (d.files or []) if d.locate_file(f).is_file()]}\n"
                  " except m.PackageNotFoundError:r[n]=None\n"
                  "print(json.dumps(r))")
        raw = rt.run([str(python), "-I", "-B", "-c", script], work=work, name="interpreter-packages")
        distributions = json_value(raw.encode())
        result["distributions"] = {name: None if value is None else {
            "version": value["version"], "files": {filename: snapshot(Path(filename), links=True) for filename in value["files"]}}
            for name, value in distributions.items()}
    return result


def read_library(target: Path) -> tuple[dict, dict, dict]:
    images, raw, values = {}, {}, {}
    for name, relative in RELATIVE_OBJECTS.items():
        path = target / relative
        safe_path(path, directory=name in KINDS)
        images[name] = snapshot(path)
    for kind in KINDS:
        directory = target / "templates" / (kind + "s")
        index = directory / (kind + "s_index.json")
        raw[kind] = index.read_bytes() if index.exists() else b"{}\n"
        values[kind] = json_value(raw[kind])
        if not isinstance(values[kind], dict):
            raise InstallFailure("blocked", f"{kind} index must be a JSON object")
        if not index.exists() and directory.exists() and any(p.is_dir() and p.name != "oracle" for p in directory.iterdir()):
            raise InstallFailure("blocked", f"Missing {kind} index beside non-Oracle workspaces")
        for name in values[kind]:
            if not name or name in {".", ".."} or "/" in name or "\\" in name:
                raise InstallFailure("blocked", f"Unsafe index key: {name!r}")
            workspace = directory / name
            if not workspace.exists() and not workspace.is_symlink():
                raise InstallFailure("blocked", f"Orphan {kind} index entry: {name}")
            safe_path(workspace, directory=True, absent_ok=False)
    return images, raw, values


def qualify(target: Path, python: Path, work: Path, key: bytes) -> tuple[dict, dict, dict]:
    code = code_snapshot(target)
    interpreter = interpreter_snapshot(python, work / "interpreter-read")
    authority = {"release": rt.release_digest(), "implementation": {k: v for k, v in current_sources().items() if k in {"runtime.py", "verify_runtime.py"}},
                 "fingerprint": rt.fingerprint(target), "code_preimages_sha256": digest(code),
                 "interpreter_sha256": digest(interpreter)}
    cache_id = digest(authority)
    cache = work / "proofs" / (cache_id + ".json")
    if cache.exists():
        safe_path(cache, directory=False, absent_ok=False)
        proof = unseal(cache.read_bytes(), key, "compatibility")
        if proof["authority"] != authority:
            raise InstallFailure("invalid_plan", "Compatibility receipt authority differs")
        return {**proof, "source": "cached_receipt", "registrar_invoked": False}, code, interpreter
    probe_work = work / "probes" / secrets.token_hex(16)
    assessment = rt.assess_runtime(target, python=python, work=probe_work)
    if assessment.action != "reuse":
        raise InstallFailure("blocked", assessment.reason, runtime=str(target), assessment=asdict(assessment))
    entries = {kind: json_value((probe_work / "registration-view/templates" / (kind + "s") / (kind + "s_index.json")).read_bytes())["oracle"]
               for kind in KINDS}
    if not same_json(entries, rt.load_release()["oracle_entries"]):
        raise InstallFailure("blocked", "Qualified registry differs from the frozen official Oracle entries")
    if code_snapshot(target) != code or interpreter_snapshot(python, work / "interpreter-recheck") != interpreter:
        raise InstallFailure("stale", "Runtime or interpreter changed during qualification")
    current_sources()
    if rt.release_digest() != authority["release"]:
        raise InstallFailure("stale", "Release changed during qualification")
    proof = {"authority": authority, "expected_entries": entries, "evidence": assessment.evidence,
             "source": "isolated_probe", "registrar_invoked": True}
    save_sealed(cache, proof, key, "compatibility")
    return proof, code, interpreter


def reference_runtime(python: Path, work: Path, key: bytes, archive: Path | None) -> tuple[Path, Path]:
    reference = work / "release-reference" / rt.release_digest()
    receipt = reference / "ready.json"
    if receipt.exists():
        data = unseal(receipt.read_bytes(), key, "reference")
        target, bound = Path(data["runtime"]), Path(data["python"])
        if code_snapshot(target) != data["code"] or interpreter_snapshot(bound, work / "reference-read") != data["interpreter"]:
            raise InstallFailure("stale", "Private planning reference changed")
        return target, bound
    if reference.exists():
        raise InstallFailure("blocked", f"Incomplete planning reference is retained at {reference}; use a fresh work directory")
    mkdirs(reference)
    target = reference / "runtime"
    binding = rt.build_runtime(target, reference / "environment", reference / "build", python=python, archive=archive)
    bound = Path(binding.python)
    save_sealed(receipt, {"runtime": str(target), "python": str(bound), "code": code_snapshot(target),
                          "interpreter": interpreter_snapshot(bound, work / "reference-read")}, key, "reference")
    return target, bound


def differences(before: Path, after: Path, old: dict, new: dict, label: str) -> list:
    left, right = content(old).get("entries", {}), content(new).get("entries", {})
    result = []
    for name in sorted(set(left) | set(right)):
        a, b = left.get(name), right.get(name)
        if a == b:
            continue
        item = {"path": label if name == "." else label + "/" + name,
                "before": a, "after": b,
                "change": "add" if a is None else "remove" if b is None else "replace"}
        old_file = before if name == "." else before / name
        new_file = after if name == "." else after / name
        old_bytes = old_file.read_bytes() if a and a["kind"] == "file" else b""
        new_bytes = new_file.read_bytes() if b and b["kind"] == "file" else b""
        try:
            if b"\0" in old_bytes + new_bytes:
                raise UnicodeError("binary")
            item["diff"] = "".join(difflib.unified_diff(old_bytes.decode().splitlines(keepends=True),
                                                       new_bytes.decode().splitlines(keepends=True),
                                                       fromfile="before/" + item["path"], tofile="after/" + item["path"]))
        except UnicodeError:
            item["encoding"] = "binary; exact before/after SHA-256 and size above"
        result.append(item)
    return result


def plan_install(chosen: Selection, explicit: Path | None, python: Path, work: Path,
                 out: Path, archive: Path | None = None) -> dict:
    source_generation = current_sources()
    target, discovery, _ = choose_runtime(chosen, explicit)
    target_exists = target.exists()
    preimages, originals, values = read_library(target)
    plan_id = secrets.token_hex(16)
    paths = paths_for(target, plan_id, work)
    if inside(work, target) or inside(target, work) or inside(work, Path(paths["state"])) or inside(Path(paths["state"]), work):
        raise InstallFailure("blocked", "Work must be isolated from the runtime and its installer state")
    if not inside(out, work):
        raise InstallFailure("blocked", "--out must be inside --work")
    ancestors = safe_path(target, directory=True)
    ancestors.update(safe_path(Path(paths["state"]), directory=True))
    if target_exists:
        for kind, index in values.items():
            for name in index:
                if name != "oracle":
                    ancestors.update(safe_path(target / "templates" / (kind + "s") / name, directory=True, absent_ok=False))
    key = work_key(work, create=True)
    ancestors.update(safe_path(work, directory=True, absent_ok=False))
    release = rt.release_digest()
    payload = {kind: snapshot(rt.PAYLOAD / "templates" / (kind + "s") / "oracle") for kind in KINDS}
    python = absolute(python)
    if target_exists:
        binding = rt.read_binding(target)
        if binding:
            python = Path(binding.python)
            if not inside(Path(binding.environment), chosen.root):
                raise InstallFailure("blocked", "Managed dependency environment escapes the selected scope")
        proof, code, interpreter = qualify(target, python, work, key)
        expected = proof["expected_entries"]
        runtime_action, environment, bound_python = "reuse", None, str(python)
        reference, reference_python = target, python
    else:
        interpreter = interpreter_snapshot(python, work / "base-interpreter")
        code = {}
        reference, reference_python = reference_runtime(python, work, key, archive)
        _, originals, values = read_library(reference)
        generated = rt.prepare_registration_view(reference, reference_python,
            work / "registration" / plan_id, work / "registration-logs" / plan_id, indices=originals)
        expected = {kind: json_value(raw)["oracle"] for kind, raw in generated.items()}
        proof = {"source": "pinned_private_planning_reference", "registrar_invoked": True,
                 "runtime": str(reference), "python": str(reference_python)}
        runtime_action, environment = "install", paths["environment"]
        bound_python = str(Path(environment) / "bin/python")
    equal = all(content(preimages[kind]) == content(payload[kind]) for kind in KINDS)
    if not same_json(expected, rt.load_release()["oracle_entries"]) or any(not isinstance(v, dict) for v in expected.values()):
        raise InstallFailure("blocked", "Oracle entries differ from the frozen official registry")
    registered = all("oracle" in values[kind] and same_json(values[kind]["oracle"], expected[kind]) for kind in KINDS)
    conflict = any(preimages[kind]["kind"] != "absent" and content(preimages[kind]) != content(payload[kind]) for kind in KINDS)
    conflict |= any("oracle" in values[kind] and not same_json(values[kind]["oracle"], expected[kind]) for kind in KINDS)
    action = "replace" if conflict else "keep" if equal and registered else "register" if equal else "install"
    if target_exists and action != "keep":
        generated = rt.prepare_registration_view(reference, reference_python,
            work / "registration" / plan_id, work / "registration-logs" / plan_id, indices=originals)
    elif target_exists:
        generated = originals
    for kind, raw in generated.items():
        candidate = json_value(raw)
        if not same_json({k: v for k, v in candidate.items() if k != "oracle"},
                         {k: v for k, v in values[kind].items() if k != "oracle"}):
            raise InstallFailure("blocked", "Runtime registrar changed a non-Oracle JSON value or type")
        if not same_json(candidate.get("oracle"), expected[kind]):
            raise InstallFailure("blocked", "Runtime registrar disagrees with its qualified Oracle entry")
    candidate_indices = {kind: base64.b64encode(raw).decode() for kind, raw in generated.items()}
    changes = []
    for kind in KINDS:
        changes += differences(target / RELATIVE_OBJECTS[kind], rt.PAYLOAD / "templates" / (kind + "s") / "oracle",
                               preimages[kind], payload[kind], RELATIVE_OBJECTS[kind])
        raw = generated[kind]
        original = (target / RELATIVE_OBJECTS[kind + "_index"]).read_bytes() if target_exists and preimages[kind + "_index"]["kind"] != "absent" else b""
        if original != raw:
            changes.append({"path": RELATIVE_OBJECTS[kind + "_index"], "change": "replace" if original else "add",
                            "before_sha256": rt.sha256(original) if original else None,
                            "after_sha256": rt.sha256(raw), "before_base64": base64.b64encode(original).decode(),
                            "after_base64": base64.b64encode(raw).decode(),
                            "diff": "".join(difflib.unified_diff(original.decode().splitlines(keepends=True), raw.decode().splitlines(keepends=True),
                                                                   fromfile="before/" + RELATIVE_OBJECTS[kind + "_index"], tofile="after/" + RELATIVE_OBJECTS[kind + "_index"]))})
    backups = {name: {"path": str(Path(paths["backup"]) / name),
                      "absence_marker": str(Path(paths["backup"]) / (name + ".absent.json")),
                      "was_absent": preimage["kind"] == "absent"} for name, preimage in preimages.items()}
    if runtime_action == "install":
        changes.insert(0, {"path": str(target), "change": "install_runtime", "files": rt.load_release()["runtime_files"],
                           "binding": {"python": bound_python, "environment": environment, "release_sha256": release}})
    postconditions = {"payload": {kind: content(value) for kind, value in payload.items()},
                      "non_oracle": {kind: {k: v for k, v in value.items() if k != "oracle"} for kind, value in values.items()},
                      "runtime_fingerprint": rt.fingerprint(reference)}
    if runtime_action == "install":
        files = dict(rt.load_release()["runtime_files"])
        for kind in KINDS:
            files[RELATIVE_OBJECTS[kind + "_index"]] = rt.sha256(generated[kind])
            for name, item in content(payload[kind])["entries"].items():
                if item["kind"] == "file":
                    files[RELATIVE_OBJECTS[kind] + "/" + name] = item["sha256"]
        binding = rt.RuntimeBinding(bound_python, environment, release)
        files[rt.BINDING] = rt.sha256((json.dumps(asdict(binding), indent=2) + "\n").encode())
        postconditions["new_runtime_files"] = files
    if choose_runtime(chosen, explicit)[:2] != (target, discovery) or read_library(target)[0] != preimages:
        raise InstallFailure("stale", "Target changed while planning")
    if current_sources() != source_generation or rt.release_digest() != release:
        raise InstallFailure("stale", "Release or implementation changed while planning")
    plan = InstallPlan(SCHEMA, plan_id, asdict(chosen), str(work), str(target), str(explicit) if explicit else None,
                       runtime_action, action, str(python), bound_python, environment, release, source_generation,
                       ancestors, discovery, preimages, code, interpreter, proof, candidate_indices, expected,
                       changes, backups, postconditions, paths, action == "replace")
    value = asdict(plan)
    encoded = canonical_json(seal(value, key, "plan")) + b"\n"
    atomic_bytes(work / "plans" / (plan_id + ".json"), encoded, exclusive=True)
    atomic_bytes(out, encoded, exclusive=True)
    return {"status": "planned", "plan": str(out), "digest": digest(value), "runtime_action": runtime_action,
            "template_action": action, "consent_required": plan.consent_required,
            "compatibility": {k: v for k, v in proof.items() if k != "authority"},
            "changes": changes, "backups": backups, "paths": paths}


def load_plan(path: Path, work: Path) -> tuple[InstallPlan, bytes]:
    key = work_key(work)
    safe_path(path, directory=False, absent_ok=False)
    if not inside(path, work):
        raise InstallFailure("invalid_plan", "Plan is outside its original work directory")
    value = unseal(path.read_bytes(), key, "plan")
    try:
        plan = InstallPlan(**value)
        if plan.schema != SCHEMA or len(plan.id) != 32 or any(c not in "0123456789abcdef" for c in plan.id):
            raise ValueError("Plan schema or identifier differs")
        chosen = selection(**plan.selection)
        target = Path(plan.runtime)
        if str(work) != plan.work or not inside(target, chosen.root) or target == chosen.root:
            raise ValueError("Plan scope or work root differs")
        if plan.explicit_runtime:
            if Path(plan.explicit_runtime) != target:
                raise ValueError("Explicit target differs")
        elif target not in {chosen.root / client / "skills/ppt-master" for client in (".agents", ".codex", ".cursor")}:
            actual, _, _ = choose_runtime(chosen, None)
            if actual != target:
                raise ValueError("Target is not the real target of a known client alias")
        expected_paths = paths_for(target, plan.id, work)
        if plan.paths != expected_paths:
            raise ValueError("Derived transaction paths differ")
        if plan.runtime_action not in {"reuse", "install"} or plan.template_action not in {"keep", "register", "install", "replace"}:
            raise ValueError("Plan action is not executable")
        if plan.consent_required != (plan.template_action == "replace"):
            raise ValueError("Consent rule differs")
        if plan.runtime_action == "install":
            if target != chosen.root / ".agents/skills/ppt-master" or plan.template_action != "install":
                raise ValueError("Invalid new-install target or action")
            if plan.environment != expected_paths["environment"] or plan.bound_python != str(Path(plan.environment) / "bin/python"):
                raise ValueError("Environment path differs")
        elif plan.environment is not None or plan.python != plan.bound_python:
            raise ValueError("Reuse cannot change the environment")
        if set(plan.preimages) != set(RELATIVE_OBJECTS) or set(plan.indices) != set(KINDS) or set(plan.expected_entries) != set(KINDS):
            raise ValueError("Managed object set differs")
        expected_backups = {name: {"path": str(Path(expected_paths["backup"]) / name),
                           "absence_marker": str(Path(expected_paths["backup"]) / (name + ".absent.json")),
                           "was_absent": preimage["kind"] == "absent"} for name, preimage in plan.preimages.items()}
        if expected_backups != plan.backups:
            raise ValueError("Backup paths differ")
        for kind, encoded in plan.indices.items():
            index = json_value(base64.b64decode(encoded, validate=True))
            if not isinstance(plan.expected_entries[kind], dict) or not isinstance(index, dict) or "oracle" not in index or not same_json(index["oracle"], plan.expected_entries[kind]):
                raise ValueError("Candidate Oracle registration differs")
            if not same_json({k: v for k, v in index.items() if k != "oracle"}, plan.postconditions["non_oracle"][kind]):
                raise ValueError("Candidate changed non-Oracle entries")
        stored = work / "plans" / (plan.id + ".json")
        safe_path(stored, directory=False, absent_ok=False)
        if unseal(stored.read_bytes(), key, "plan") != value:
            raise ValueError("Plan differs from the original scope authorization")
    except (TypeError, KeyError, ValueError) as exc:
        raise InstallFailure("invalid_plan", f"Invalid plan fields: {exc}") from exc
    return plan, key


def check_ancestors(expected: dict):
    for name, value in expected.items():
        path = Path(name)
        safe_path(path, directory=True, absent_ok=False)
        if identity(path) != value:
            raise InstallFailure("stale", f"Ancestor identity changed: {path}")


def revalidate(plan: InstallPlan, *, receipt: TransactionReceipt | None = None):
    if plan.release_sha256 != rt.release_digest() or plan.implementation != current_sources():
        raise InstallFailure("stale", "Release or installer implementation changed")
    if not same_json(plan.expected_entries, rt.load_release()["oracle_entries"]):
        raise InstallFailure("stale", "Plan Oracle entries differ from the frozen official registry")
    check_ancestors(receipt.ancestors if receipt else plan.ancestors)
    chosen = selection(**plan.selection)
    actual_target, actual_discovery, _ = choose_runtime(chosen, Path(plan.explicit_runtime) if plan.explicit_runtime else None)
    if actual_target != Path(plan.runtime) or actual_discovery != plan.discovery:
        raise InstallFailure("stale", "Runtime discovery or alias identity changed")
    if plan.runtime_action == "reuse" and code_snapshot(Path(plan.runtime)) != plan.code_preimages:
        raise InstallFailure("stale", "Runtime code or binding changed")
    current = interpreter_snapshot(Path(plan.python), Path(plan.work) / "revalidation")
    if current != plan.interpreter:
        raise InstallFailure("stale", "Interpreter or its dependency environment changed")
    if receipt:
        states = classify_objects(plan, receipt)
        for op, state in zip(receipt.operations, states):
            expected = "after" if op["state"] == "published" else "before"
            if state != expected:
                raise InstallFailure("stale", f"Transaction object changed: {op['name']}")
    elif read_library(Path(plan.runtime))[0] != plan.preimages:
        raise InstallFailure("stale", "Oracle tree or index bytes, mtimes, or identities changed")


def write_receipt(plan: InstallPlan, receipt: TransactionReceipt, key: bytes):
    save_sealed(Path(plan.paths["receipt"]), asdict(receipt), key, "receipt")


def event(plan: InstallPlan, receipt: TransactionReceipt, key: bytes, name: str):
    receipt.events.append(name)
    write_receipt(plan, receipt, key)


def guard_active(plan: InstallPlan, receipt: TransactionReceipt):
    path = Path(plan.paths["state"]) / "active.json"
    safe_path(path, directory=False)
    guard = receipt.verification.get("active_guard")
    if guard:
        actual = snapshot(path)
        allowed = [guard["after"]]
        if guard["pending"]:
            allowed.append(guard["before"])
        if actual not in allowed:
            raise InstallFailure("recovery_conflict", "Active transaction marker has third-party changes", path=str(path))


def set_active(plan: InstallPlan, receipt: TransactionReceipt, key: bytes,
               requested: str | None = None, mode: str = "exception"):
    guard_active(plan, receipt)
    state = Path(plan.paths["state"])
    active = state / "active.json"
    candidate = state / (".active-" + plan.id + "-" + secrets.token_hex(6))
    guard = {"before": snapshot(active), "after": None, "pending": True, "stage": str(candidate)}
    receipt.verification["active_guard"] = guard
    event(plan, receipt, key, "intent:prepare-active:" + receipt.status)
    atomic_bytes(candidate, canonical_json({"plan_id": plan.id, "work": plan.work,
        "status": receipt.status, "receipt": plan.paths["receipt"]}) + b"\n", exclusive=True)
    guard["after"] = snapshot(candidate)
    event(plan, receipt, key, "intent:publish-active:" + receipt.status)
    fault(plan, "before:active:" + receipt.status, requested, mode)
    if snapshot(active) != guard["before"]:
        raise InstallFailure("recovery_conflict", "Active transaction marker changed before publication")
    os.replace(candidate, active)
    fsync_dir(state)
    fault(plan, "after:active:" + receipt.status, requested, mode)
    guard["pending"] = False
    event(plan, receipt, key, "published:active:" + receipt.status)


def fault(plan: InstallPlan, boundary: str, requested: str | None, mode: str):
    if requested != boundary:
        return
    atomic_bytes(Path(plan.work) / ("fault-" + plan.id + ".json"), canonical_json({
        "boundary": boundary, "pid": os.getpid(), "receipt": plan.paths["receipt"]}) + b"\n")
    if mode == "exception":
        raise InjectedFailure("Injected exception at " + boundary)
    if mode == "kill":
        os.kill(os.getpid(), signal.SIGKILL)
    if mode == "stop":
        os.kill(os.getpid(), signal.SIGSTOP)


def publication_boundaries(names: list[str], *, recovery: bool = False) -> list[str]:
    verb = "rollback" if recovery else "publish"
    boundaries = [part + ":" + verb + ":" + name for name in names for part in ("before", "after")]
    boundaries += [part + ":record:" + name for name in names for part in ("before", "after")]
    marker = "aborted" if recovery else "committed"
    return boundaries + ["before:complete", "after:receipt-complete", "before:active:" + marker,
                         "after:active:" + marker, "after:complete"]


@contextmanager
def target_lock(plan: InstallPlan, receipt: TransactionReceipt, key: bytes):
    state = Path(plan.paths["state"])
    check_ancestors(plan.ancestors)
    save_sealed(Path(plan.work) / "bootstrap" / (secrets.token_hex(16) + ".json"),
                {"intent": "create persistent lock infrastructure", "state": str(state),
                 "lock": plan.paths["lock"], "runtime": plan.runtime, "receipt": asdict(receipt)}, key, "bootstrap")
    mkdirs(state)
    owner = state / "owner.json"
    expected_owner = {"schema": SCHEMA, "runtime": plan.runtime}
    if owner.exists():
        safe_path(owner, directory=False, absent_ok=False)
        if json_value(owner.read_bytes()) != expected_owner:
            raise InstallFailure("blocked", "Installer state belongs to another runtime")
    else:
        try:
            atomic_bytes(owner, canonical_json(expected_owner) + b"\n", exclusive=True)
        except FileExistsError:
            if json_value(owner.read_bytes()) != expected_owner:
                raise InstallFailure("blocked", "Installer state ownership changed")
    lock_path = Path(plan.paths["lock"])
    safe_path(lock_path, directory=False)
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise InstallFailure("busy", "Another installer holds the stable target lock", lock=str(lock_path)) from exc
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise InstallFailure("blocked", "Lock is not a singly linked regular file")
        os.fsync(fd)
        fsync_dir(state)

        def locked():
            safe_path(lock_path, directory=False, absent_ok=False)
            current = lock_path.lstat()
            if (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino):
                raise InstallFailure("stale", "Stable lock inode changed")

        locked()
        receipt.ancestors.update(safe_path(state, directory=True, absent_ok=False))
        yield locked
    finally:
        os.close(fd)


def atomic_rename(left: Path, right: Path, *, replace: bool):
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        function, directory = libc.renameatx_np, -2
        flags = 2 if replace else 4
    elif sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        function, directory = libc.renameat2, -100
        flags = 2 if replace else 1
    else:
        raise InstallFailure("blocked", "This platform lacks the required atomic rename exchange")
    function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    if function(directory, os.fsencode(left), directory, os.fsencode(right), flags):
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(right))


def exchange(left: Path, right: Path):
    atomic_rename(left, right, replace=True)


def initial_receipt(plan: InstallPlan) -> TransactionReceipt:
    target, stage = Path(plan.runtime), Path(plan.paths["stage"])
    if plan.runtime_action == "install":
        operations = [{"name": "runtime", "path": str(target), "stage": str(stage / "runtime"),
                       "before": {"kind": "absent"}, "after": None, "state": "preparing"}]
    else:
        operations = []
        for name, rel in RELATIVE_OBJECTS.items():
            before = plan.preimages[name]
            if name in KINDS:
                changed = content(before) != plan.postconditions["payload"][name]
            else:
                raw = base64.b64decode(plan.indices[name.removesuffix("_index")])
                changed = before["kind"] == "absent" or before["entries"]["."]["sha256"] != rt.sha256(raw)
            if changed:
                operations.append({"name": name, "path": str(target / rel), "stage": str(stage / name),
                                   "before": before, "after": None, "state": "preparing"})
    environment = {"path": plan.environment, "state": "pending", "before": {"kind": "absent"}, "snapshot": None} if plan.environment else None
    return TransactionReceipt(SCHEMA, plan.id, digest(asdict(plan)), "preparing", plan.runtime, plan.work,
                              dict(plan.ancestors), plan.preimages, operations, dict(plan.backups), environment, [], {"backups_completed": []})


def check_active(plan: InstallPlan):
    path = Path(plan.paths["state"]) / "active.json"
    if path.exists():
        safe_path(path, directory=False, absent_ok=False)
        active = json_value(path.read_bytes())
        if active["status"] not in {"committed", "aborted"}:
            raise InstallFailure("blocked", "An unfinished transaction requires recover first", active=active)


def make_backups(plan: InstallPlan, receipt: TransactionReceipt, key: bytes):
    event(plan, receipt, key, "intent:complete-backups")
    mkdirs(Path(plan.paths["backup"]))
    for name, specification in plan.backups.items():
        event(plan, receipt, key, "intent:backup:" + name)
        before = plan.preimages[name]
        if before["kind"] == "absent":
            marker = {"object": name, "before": "absent", "plan_id": plan.id}
            atomic_bytes(Path(specification["absence_marker"]), canonical_json(marker) + b"\n", exclusive=True)
        else:
            source, destination = Path(plan.runtime) / RELATIVE_OBJECTS[name], Path(specification["path"])
            if before["kind"] == "directory":
                shutil.copytree(source, destination, copy_function=shutil.copy2)
            else:
                shutil.copy2(source, destination)
            sync_tree(destination)
            if content(snapshot(destination), metadata=True) != content(before, metadata=True):
                raise InstallFailure("stale", f"Backup does not match the complete preimage: {name}")
        receipt.verification["backups_completed"].append(name)
        write_receipt(plan, receipt, key)
    fsync_dir(Path(plan.paths["backup"]))


def verify_postconditions(plan: InstallPlan, target: Path):
    images, _, values = read_library(target)
    for kind in KINDS:
        if content(images[kind]) != plan.postconditions["payload"][kind]:
            raise InstallFailure("recovery_conflict", f"Published {kind} differs from the complete frozen payload")
        if not same_json(values[kind].get("oracle"), plan.expected_entries[kind]):
            raise InstallFailure("recovery_conflict", f"Published {kind} registration differs")
        if not same_json({k: v for k, v in values[kind].items() if k != "oracle"}, plan.postconditions["non_oracle"][kind]):
            raise InstallFailure("recovery_conflict", f"Non-Oracle {kind} values changed")
    if rt.fingerprint(target) != plan.postconditions["runtime_fingerprint"]:
        raise InstallFailure("recovery_conflict", "Published runtime fingerprint differs")
    if plan.runtime_action == "install":
        binding = rt.read_binding(target)
        if binding is None or binding.python != plan.bound_python or binding.environment != plan.environment or binding.release_sha256 != plan.release_sha256:
            raise InstallFailure("recovery_conflict", "Published interpreter binding differs")
        inventory = {name: item["sha256"] for name, item in snapshot(target)["entries"].items() if item["kind"] == "file"}
        if inventory != plan.postconditions["new_runtime_files"]:
            raise InstallFailure("recovery_conflict", "New runtime complete file inventory differs from its plan")


def prepare_transaction(plan: InstallPlan, receipt: TransactionReceipt, key: bytes,
                        archive: Path | None, requested: str | None, mode: str):
    transaction = Path(plan.paths["transaction"])
    if transaction.exists():
        raise InstallFailure("blocked", "Transaction already exists; recover it before replanning")
    event(plan, receipt, key, "intent:prepare-transaction")
    mkdirs(transaction)
    atomic_bytes(transaction / "owner.json", canonical_json({"plan_id": plan.id, "plan_digest": receipt.plan_digest}) + b"\n", exclusive=True)
    make_backups(plan, receipt, key)
    mkdirs(Path(plan.paths["stage"]))
    if plan.runtime_action == "install":
        destination = Path(receipt.operations[0]["stage"])
        environment = Path(plan.environment)
        event(plan, receipt, key, "intent:environment-container")
        if environment.parent.exists():
            raise InstallFailure("stale", "New environment container is no longer absent")
        mkdirs(environment.parent)
        atomic_bytes(environment.parent / "owner.json", canonical_json({"plan_id": plan.id, "plan_digest": receipt.plan_digest}) + b"\n", exclusive=True)
        receipt.environment["state"] = "building"
        event(plan, receipt, key, "intent:build-runtime-and-final-environment")
        fault(plan, "before:environment", requested, mode)
        binding = rt.build_runtime(destination, environment, Path(plan.work) / "builds" / plan.id,
                                   python=Path(plan.python), archive=archive)
        if binding.python != plan.bound_python:
            raise InstallFailure("blocked", "Builder changed the final interpreter path")
        sync_tree(environment)
        receipt.environment.update(state="built", snapshot=snapshot(environment, links=True))
        write_receipt(plan, receipt, key)
        fault(plan, "after:environment", requested, mode)
        proof, _, _ = qualify(destination, Path(binding.python), Path(plan.work), key)
        _, original, _ = read_library(destination)
        indices = rt.prepare_registration_view(destination, Path(binding.python),
            Path(plan.work) / "apply-registration" / plan.id, Path(plan.work) / "apply-registration-logs" / plan.id, indices=original)
        for kind in KINDS:
            if indices[kind] != base64.b64decode(plan.indices[kind]):
                raise InstallFailure("stale", "Actual runtime registrar differs from the planned index bytes")
            shutil.copytree(rt.PAYLOAD / "templates" / (kind + "s") / "oracle", destination / RELATIVE_OBJECTS[kind])
            (destination / RELATIVE_OBJECTS[kind + "_index"]).write_bytes(indices[kind])
        verify_postconditions(plan, destination)
        receipt.verification["capability"] = {"source": proof["source"], "evidence": proof["evidence"]}
        receipt.environment.update(state="qualified", snapshot=snapshot(environment, links=True))
    else:
        for op in receipt.operations:
            destination = Path(op["stage"])
            if op["name"] in KINDS:
                shutil.copytree(rt.PAYLOAD / "templates" / (op["name"] + "s") / "oracle", destination)
            else:
                destination.write_bytes(base64.b64decode(plan.indices[op["name"].removesuffix("_index")]))
    for op in receipt.operations:
        sync_tree(Path(op["stage"]))
        if Path(op["stage"]).stat().st_dev != Path(op["path"]).parent.stat().st_dev:
            raise InstallFailure("blocked", "Stage and destination are not on the same filesystem")
        op.update(after=snapshot(Path(op["stage"])), state="prepared")
        receipt.ancestors.update(safe_path(Path(op["stage"]).parent, directory=True, absent_ok=False))
        receipt.ancestors.update(safe_path(Path(op["path"]).parent, directory=True, absent_ok=False))
    if receipt.environment:
        receipt.ancestors.update(safe_path(Path(receipt.environment["path"]).parent, directory=True, absent_ok=False))
    receipt.status = "prepared"
    event(plan, receipt, key, "prepared")


def classify_objects(plan: InstallPlan, receipt: TransactionReceipt) -> list[str]:
    results, touched = [], set()
    for op in receipt.operations:
        path, stage = Path(op["path"]), Path(op["stage"])
        safe_path(path)
        safe_path(stage)
        actual, staged = snapshot(path), snapshot(stage)
        before, after = op["before"], op["after"]
        if after is None and actual == before:
            results.append("before")
        elif actual == before and staged == after:
            results.append("before")
        elif after is not None and actual == after and staged == before:
            results.append("after")
        else:
            raise InstallFailure("recovery_conflict", "Object is neither its recorded preimage nor its transaction postimage",
                                 object=op["name"], path=str(path), stage=str(stage),
                                 actual_digest=digest(actual), before_digest=digest(before), after_digest=digest(after))
        touched.add(op["name"])
    if plan.runtime_action == "reuse":
        for name, before in plan.preimages.items():
            if name not in touched:
                path = Path(plan.runtime) / RELATIVE_OBJECTS[name]
                safe_path(path)
                if snapshot(path) != before:
                    raise InstallFailure("recovery_conflict", f"Unchanged transaction object has third-party edits: {path}")
    if receipt.environment and receipt.environment["snapshot"] is not None:
        path = Path(receipt.environment["path"])
        safe_path(path, directory=True, absent_ok=False)
        if snapshot(path, links=True) != receipt.environment["snapshot"]:
            raise InstallFailure("recovery_conflict", "Final environment has third-party changes", path=str(path))
    elif receipt.environment and Path(receipt.environment["path"]).exists():
        raise InstallFailure("recovery_conflict", "Unfinished environment has unrecorded contents; retained without deletion", path=receipt.environment["path"])
    return results


def check_backups(plan: InstallPlan, receipt: TransactionReceipt):
    for name, specification in receipt.backups.items():
        if name not in receipt.verification["backups_completed"]:
            continue
        before = plan.preimages[name]
        if before["kind"] == "absent":
            path = Path(specification["absence_marker"])
            safe_path(path, directory=False, absent_ok=False)
            if json_value(path.read_bytes()) != {"object": name, "before": "absent", "plan_id": plan.id}:
                raise InstallFailure("recovery_conflict", "Absence marker changed", path=str(path))
        else:
            path = Path(specification["path"])
            safe_path(path, absent_ok=False)
            if content(snapshot(path), metadata=True) != content(before, metadata=True):
                raise InstallFailure("recovery_conflict", "Full backup changed", path=str(path))


def rollback(plan: InstallPlan, receipt: TransactionReceipt, key: bytes, locked,
             requested: str | None = None, mode: str = "exception") -> dict:
    locked()
    guard_active(plan, receipt)
    check_ancestors(receipt.ancestors)
    if plan.runtime_action == "reuse":
        for name, expected in plan.code_preimages.items():
            path = Path(plan.runtime) / name
            safe_path(path, directory=False)
            if snapshot(path) != expected:
                raise InstallFailure("recovery_conflict", "Runtime code or binding changed during the transaction", path=str(path))
    states = classify_objects(plan, receipt)
    check_backups(plan, receipt)
    if receipt.status == "committed":
        if any(state != "after" for state in states):
            raise InstallFailure("recovery_conflict", "Committed transaction no longer has its complete postimage")
        verify_postconditions(plan, Path(plan.runtime))
        if receipt.operations:
            set_active(plan, receipt, key)
        return {"status": "committed", "receipt": plan.paths["receipt"], "verified": True}
    for index in reversed(range(len(receipt.operations))):
        op = receipt.operations[index]
        if states[index] == "before":
            continue
        receipt.status = "recovering"
        op["state"] = "rollback_intent"
        event(plan, receipt, key, "intent:rollback:" + op["name"])
        fault(plan, "before:rollback:" + op["name"], requested, mode)
        locked()
        guard_active(plan, receipt)
        check_ancestors(receipt.ancestors)
        classify_objects(plan, receipt)
        path, stage = Path(op["path"]), Path(op["stage"])
        if op["before"]["kind"] == "absent":
            atomic_rename(path, stage, replace=False)
        else:
            exchange(stage, path)
        fsync_dir(path.parent)
        fsync_dir(stage.parent)
        fault(plan, "after:rollback:" + op["name"], requested, mode)
        fault(plan, "before:record:" + op["name"], requested, mode)
        op["state"] = "rolled_back"
        event(plan, receipt, key, "rolled_back:" + op["name"])
        fault(plan, "after:record:" + op["name"], requested, mode)
    if any(state != "before" for state in classify_objects(plan, receipt)):
        raise InstallFailure("recovery_conflict", "Rollback did not restore every original object")
    fault(plan, "before:complete", requested, mode)
    receipt.status = "aborted"
    receipt.verification["rollback"] = "all managed preimages restored; private stages, environments, and backups retained"
    event(plan, receipt, key, "complete:aborted")
    fault(plan, "after:receipt-complete", requested, mode)
    set_active(plan, receipt, key, requested, mode)
    fault(plan, "after:complete", requested, mode)
    return {"status": "recovered", "receipt": plan.paths["receipt"], "backups": receipt.backups,
            "retained_environment": receipt.environment, "verified": True}


def apply_plan(path: Path, work: Path, confirm: str | None = None, archive: Path | None = None,
               requested: str | None = None, mode: str = "exception") -> dict:
    plan, key = load_plan(path, work)
    if plan.consent_required and confirm != digest(asdict(plan)):
        raise InstallFailure("confirmation_required", "Replacement requires the exact current plan digest after reviewing every change and backup path",
                             digest=digest(asdict(plan)), changes=plan.changes, backups=plan.backups)
    if confirm is not None and confirm != digest(asdict(plan)):
        raise InstallFailure("invalid_plan", "Confirmation does not name this exact plan")
    revalidate(plan)
    if archive:
        safe_path(archive, directory=False, absent_ok=False)
        if rt.sha256(archive.read_bytes()) != rt.load_release()["upstream"]["archive_sha256"]:
            raise InstallFailure("blocked", "Archive hash differs from the pinned release")
    receipt = initial_receipt(plan)
    allowed = publication_boundaries([op["name"] for op in receipt.operations])
    if plan.environment:
        allowed += ["before:environment", "after:environment"]
    if requested and requested not in allowed:
        raise InstallFailure("usage", "Unknown fault boundary", available=allowed)
    if Path(plan.paths["receipt"]).exists():
        raise InstallFailure("blocked", "This plan already has a receipt; recover or create a fresh plan")
    with target_lock(plan, receipt, key) as locked:
        check_active(plan)
        revalidate(plan)
        if plan.template_action == "keep":
            verify_postconditions(plan, Path(plan.runtime))
            receipt.status = "committed"
            receipt.verification["keep"] = "no registrar, target write, or backup"
            write_receipt(plan, receipt, key)
            return {"status": "kept", "runtime": plan.runtime, "python": plan.bound_python,
                    "registrar_invoked": False, "backups_created": False, "receipt": plan.paths["receipt"]}
        set_active(plan, receipt, key)
        try:
            prepare_transaction(plan, receipt, key, archive, requested, mode)
            for op in receipt.operations:
                op["state"] = "intent"
                receipt.status = "publishing"
                event(plan, receipt, key, "intent:publish:" + op["name"])
                fault(plan, "before:publish:" + op["name"], requested, mode)
                locked()
                guard_active(plan, receipt)
                revalidate(plan, receipt=receipt)
                check_backups(plan, receipt)
                if set(receipt.verification["backups_completed"]) != set(plan.backups):
                    raise InstallFailure("blocked", "Full backups have not completed")
                source, destination = Path(op["stage"]), Path(op["path"])
                if op["before"]["kind"] == "absent":
                    atomic_rename(source, destination, replace=False)
                else:
                    exchange(source, destination)
                fsync_dir(source.parent)
                fsync_dir(destination.parent)
                fault(plan, "after:publish:" + op["name"], requested, mode)
                fault(plan, "before:record:" + op["name"], requested, mode)
                op["state"] = "published"
                event(plan, receipt, key, "published:" + op["name"])
                fault(plan, "after:record:" + op["name"], requested, mode)
            locked()
            classify_objects(plan, receipt)
            verify_postconditions(plan, Path(plan.runtime))
            fault(plan, "before:complete", requested, mode)
            receipt.status = "committed"
            receipt.verification["postconditions"] = "complete payload, Oracle entries, non-Oracle values, runtime, and binding passed"
            event(plan, receipt, key, "complete:committed")
            fault(plan, "after:receipt-complete", requested, mode)
            set_active(plan, receipt, key, requested, mode)
            fault(plan, "after:complete", requested, mode)
            return {"status": "committed", "runtime": plan.runtime, "python": plan.bound_python,
                    "receipt": plan.paths["receipt"], "backups": receipt.backups, "verified": True}
        except Exception as exc:
            receipt.error = str(exc)
            write_receipt(plan, receipt, key)
            try:
                result = rollback(plan, receipt, key, locked)
            except Exception as recovery_error:
                if receipt.status != "committed":
                    receipt.status = "conflict"
                receipt.error = f"{exc}; recovery: {recovery_error}"
                write_receipt(plan, receipt, key)
                try:
                    set_active(plan, receipt, key)
                except InstallFailure:
                    pass
                raise InstallFailure("recovery_conflict", str(recovery_error), original_error=str(exc), receipt=plan.paths["receipt"]) from recovery_error
            if result["status"] == "committed":
                return {**result, "interrupted_after_commit": str(exc)}
            raise InstallFailure("rolled_back", str(exc), receipt=plan.paths["receipt"], recovery=result["status"]) from exc


def recover_plan(path: Path, work: Path, requested: str | None = None, mode: str = "exception") -> dict:
    plan, key = load_plan(path, work)
    receipt_path = Path(plan.paths["receipt"])
    safe_path(receipt_path, directory=False, absent_ok=False)
    try:
        receipt = TransactionReceipt(**unseal(receipt_path.read_bytes(), key, "receipt"))
        if receipt.schema != SCHEMA or receipt.plan_id != plan.id or receipt.plan_digest != digest(asdict(plan)) or receipt.runtime != plan.runtime or receipt.work != plan.work:
            raise ValueError("Receipt identity differs")
        if receipt.preimages != plan.preimages:
            raise ValueError("Receipt preimages differ")
        expected = initial_receipt(plan)
        if len(receipt.operations) != len(expected.operations):
            raise ValueError("Receipt object count differs")
        for op, spec in zip(receipt.operations, expected.operations):
            if {k: op[k] for k in ("name", "path", "stage", "before")} != {k: spec[k] for k in ("name", "path", "stage", "before")}:
                raise ValueError("Receipt has an unexpected object or path")
        if any(plan.backups.get(k) != v for k, v in receipt.backups.items()):
            raise ValueError("Receipt backup differs")
        if receipt.environment and receipt.environment["path"] != plan.environment:
            raise ValueError("Receipt environment differs")
    except (TypeError, KeyError, ValueError) as exc:
        raise InstallFailure("invalid_plan", str(exc)) from exc
    allowed = publication_boundaries([op["name"] for op in receipt.operations], recovery=True)
    if requested and requested not in allowed:
        raise InstallFailure("usage", "Unknown recovery fault boundary", available=allowed)
    try:
        with target_lock(plan, receipt, key) as locked:
            receipt = TransactionReceipt(**unseal(receipt_path.read_bytes(), key, "receipt"))
            active_path = Path(plan.paths["state"]) / "active.json"
            guard_active(plan, receipt)
            if active_path.exists() and not receipt.verification.get("active_guard") and receipt.operations:
                active = json_value(active_path.read_bytes())
                if active["plan_id"] != plan.id:
                    raise InstallFailure("recovery_conflict", "Another transaction now owns this target; old receipts are read-only")
            return rollback(plan, receipt, key, locked, requested, mode)
    except InjectedFailure as exc:
        raise InstallFailure("interrupted", str(exc), receipt=plan.paths["receipt"], next="Rerun recover with the same plan and work") from exc
    except InstallFailure as exc:
        if exc.code in {"blocked", "stale", "recovery_conflict"}:
            raise InstallFailure("recovery_conflict", str(exc), receipt=plan.paths["receipt"], **exc.details) from exc
        raise


def inspect(chosen: Selection, explicit: Path | None, python: Path, work: Path | None, probe: bool) -> dict:
    candidates, observed = discover(chosen, explicit)
    records = []
    for candidate in candidates:
        record = asdict(candidate)
        try:
            binding = rt.read_binding(Path(candidate.real_path))
            record["python"] = binding.python if binding else str(python)
        except (rt.RuntimeFailure, OSError, ValueError, TypeError) as exc:
            record.update(compatibility="blocked", reason=str(exc))
        records.append(record)
    result = {"status": "inspected", "selection": asdict(chosen), "candidates": records,
              "discovery": observed, "probe": "not_run", "target_writes": False}
    if probe:
        if work is None:
            raise InstallFailure("usage", "inspect --probe requires --work")
        target, _, _ = choose_runtime(chosen, explicit)
        read_library(target)
        if not target.exists():
            return {**result, "runtime_action": "install"}
        state = Path(paths_for(target, "0" * 32, work)["state"])
        if inside(work, target) or inside(target, work) or inside(work, state) or inside(state, work):
            raise InstallFailure("blocked", "Probe work is not isolated")
        key = work_key(work, create=True)
        binding = rt.read_binding(target)
        if binding and not inside(Path(binding.environment), chosen.root):
            raise InstallFailure("blocked", "Managed dependency environment escapes the selected scope")
        proof, _, _ = qualify(target, Path(binding.python) if binding else python, work, key)
        for record in records:
            if record["real_path"] == str(target):
                record.update(compatibility="reuse", reason=proof["source"])
        result.update(runtime_action="reuse", probe=proof["source"], compatibility={k: v for k, v in proof.items() if k != "authority"})
    return result
