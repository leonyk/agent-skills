"""Pinned PPT Master preparation and isolated qualification; no target policy."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
from dataclasses import asdict, dataclass
from typing import Literal


SKILL = Path(__file__).resolve().parents[1]
RELEASE = SKILL / "runtime-release"
PAYLOAD = SKILL / "payload"
KINDS = ("brand", "layout")
BINDING = "oracle-runtime-binding.json"
PROXY = "http://127.0.0.1:8080"


class RuntimeFailure(ValueError):
    """A preparation or qualification condition that the caller must report."""


@dataclass(frozen=True)
class RuntimeBinding:
    python: str
    environment: str
    release_sha256: str


@dataclass(frozen=True)
class RuntimeAssessment:
    action: Literal["install", "reuse", "blocked"]
    runtime: str
    python: str | None
    reason: str
    fingerprint: dict[str, str]
    evidence: str | None = None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise RuntimeFailure(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_bytes(), object_pairs_hook=unique)


def relative(name: str) -> Path:
    p = PurePosixPath(name)
    if not name or p.is_absolute() or ".." in p.parts or "\\" in name or str(p) != name:
        raise RuntimeFailure(f"unsafe relative path: {name!r}")
    return Path(*p.parts)


def regular(root: Path, name: str) -> Path:
    rel = relative(name)
    p = root
    for part in rel.parts:
        p = p / part
        if p.is_symlink():
            raise RuntimeFailure(f"symlink in controlled path: {p}")
    if not p.is_file():
        raise RuntimeFailure(f"missing regular file: {p}")
    return p


def library_file(name: str) -> bool:
    parts = PurePosixPath(name).parts
    return len(parts) > 1 and parts[0] == "templates" and parts[1] in {
        "brands", "layouts", "styles", "decks"
    }


def load_release() -> dict:
    lock = read_json(RELEASE / "runtime-lock.json")
    if lock["schema"] != 1:
        raise RuntimeFailure("unsupported release schema")
    for section in ("source_files", "runtime_files"):
        for name in lock[section]:
            relative(name)
    for patch in lock["patches"]:
        path = regular(RELEASE, patch["path"])
        if sha256(path.read_bytes()) != patch["sha256"]:
            raise RuntimeFailure(f"patch hash mismatch: {patch['path']}")
        declared = set(patch["files"])
        seen = set()
        for line in path.read_text().splitlines():
            if line.startswith(("--- ", "+++ ")):
                name = line[4:].split("\t")[0]
                if name == "/dev/null":
                    continue
                if not name.startswith(("a/", "b/")):
                    raise RuntimeFailure("invalid patch header")
                name = name[2:]
                relative(name)
                if name not in declared:
                    raise RuntimeFailure(f"undeclared patch target: {name}")
                seen.add(name)
        if seen != declared:
            raise RuntimeFailure("patch target inventory mismatch")
    deps = regular(RELEASE, "requirements.lock")
    if sha256(deps.read_bytes()) != lock["dependencies_sha256"]:
        raise RuntimeFailure("dependency lock hash mismatch")
    verify_payload(lock)
    return lock


def release_digest() -> str:
    load_release()
    return sha256((RELEASE / "runtime-lock.json").read_bytes())


def verify_package() -> dict:
    """Check this module's owned distribution paths; the parent owns other files."""
    specification = read_json(RELEASE / "package-files.json")
    actual = {p.relative_to(SKILL).as_posix() for directory in (PAYLOAD, RELEASE)
              for p in directory.rglob("*") if p.is_file() or p.is_symlink()}
    actual.update({"scripts/runtime.py", "scripts/verify_runtime.py"})
    if actual != set(specification["files"]):
        raise RuntimeFailure("runtime package allowlist mismatch")
    for name in specification["files"]:
        regular(SKILL, name)
    for name, digest in specification["source_notices"].items():
        if sha256(regular(SKILL, name).read_bytes()) != digest:
            raise RuntimeFailure(f"source notice hash mismatch: {name}")
    load_release()
    return {"files": len(actual), "status": "passed"}


def verify_payload(lock: dict | None = None) -> dict:
    lock = lock or read_json(RELEASE / "runtime-lock.json")
    manifest = regular(PAYLOAD, "manifest.json")
    if sha256(manifest.read_bytes()) != lock["payload_manifest_sha256"]:
        raise RuntimeFailure("payload manifest hash mismatch")
    data = read_json(manifest)
    for kind, count in (("brand", 7), ("layout", 131)):
        root = PAYLOAD / "templates" / (kind + "s") / "oracle"
        expected = data["templates"][kind]["sha256"]
        actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() or p.is_symlink()}
        if len(expected) != count or actual != set(expected):
            raise RuntimeFailure(f"payload file inventory mismatch: {kind}")
        for name, digest in expected.items():
            if sha256(regular(root, name).read_bytes()) != digest:
                raise RuntimeFailure(f"payload hash mismatch: {kind}/{name}")
    pages = list((PAYLOAD / "templates/layouts/oracle/templates").glob("*.svg"))
    if len(pages) != 23:
        raise RuntimeFailure("payload must contain 23 page SVGs")
    return data


def isolated_env(work: Path) -> dict[str, str]:
    env = dict(os.environ)
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        env.pop(name, None)
    for key, folder in (("HOME", "home"), ("CODEX_HOME", "codex"), ("TMPDIR", "tmp"), ("XDG_CACHE_HOME", "cache")):
        path = work / folder
        path.mkdir(parents=True, exist_ok=True)
        env[key] = str(path)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env["PIP_NO_INPUT"] = "1"
    env["PIP_CONFIG_FILE"] = os.devnull
    return env


def run(command: list[str], *, work: Path, name: str, cwd: Path | None = None, network: bool = False) -> str:
    work.mkdir(parents=True, exist_ok=True)
    env = isolated_env(work)
    if cwd:
        env["GIT_CEILING_DIRECTORIES"] = str(cwd.parent)
    proc = subprocess.run(command, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = proc.stdout
    connection_error = any(word in output.lower() for word in (
        "connection", "timed out", "timeout", "could not resolve", "network is unreachable", "temporary failure"
    ))
    if proc.returncode and network and connection_error:
        for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
            env[key] = PROXY
        proc = subprocess.run(command, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output += "\n--- proxy retry ---\n" + proc.stdout
    (work / (name + ".log")).write_text(output)
    if proc.returncode:
        raise RuntimeFailure(f"{name} exited {proc.returncode}: {output[-4000:]}")
    return output


def fetch_archive(destination: Path, work: Path) -> Path:
    lock = load_release()
    if destination.exists():
        raise RuntimeFailure(f"archive destination exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    run(["curl", "--fail", "--location", "--connect-timeout", "20", "--max-time", "300",
         lock["upstream"]["url"], "--output", str(destination)], work=work, name="fetch", network=True)
    if sha256(destination.read_bytes()) != lock["upstream"]["archive_sha256"]:
        raise RuntimeFailure("official archive hash mismatch")
    return destination


def extract_source(archive: Path, destination: Path, lock: dict) -> None:
    if destination.exists():
        raise RuntimeFailure(f"runtime destination exists: {destination}")
    if sha256(archive.read_bytes()) != lock["upstream"]["archive_sha256"]:
        raise RuntimeFailure("official archive hash mismatch")
    prefix = "ppt-master-" + lock["upstream"]["commit"] + "/" + lock["upstream"]["skill_root"] + "/"
    with tarfile.open(archive) as tf:
        members = {}
        for member in tf.getmembers():
            relative(member.name.rstrip("/"))
            if not (member.isfile() or member.isdir()):
                raise RuntimeFailure(f"archive link or special member: {member.name}")
            if member.name in members:
                raise RuntimeFailure(f"duplicate archive member: {member.name}")
            members[member.name] = member
        payloads = {}
        for name, digest in lock["source_files"].items():
            member = members.get(prefix + name)
            if member is None or not member.isfile():
                raise RuntimeFailure(f"missing official source: {name}")
            data = tf.extractfile(member).read()
            if sha256(data) != digest:
                raise RuntimeFailure(f"official source hash mismatch: {name}")
            payloads[name] = data
        destination.mkdir(parents=True)
        for name, data in payloads.items():
            path = destination / relative(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)


def apply_patches(destination: Path, lock: dict, work: Path) -> None:
    for number, patch in enumerate(lock["patches"]):
        for name, expected in patch["files"].items():
            p = destination / relative(name)
            if p.is_symlink():
                raise RuntimeFailure(f"symlink patch target: {name}")
            actual = sha256(regular(destination, name).read_bytes()) if p.exists() else None
            if actual != expected["before"]:
                raise RuntimeFailure(f"patch preimage mismatch: {name}")
        path = regular(RELEASE, patch["path"])
        if sha256(path.read_bytes()) != patch["sha256"]:
            raise RuntimeFailure("patch changed after release validation")
        run(["git", "apply", "--check", str(path)], cwd=destination, work=work, name=f"patch-{number}-check")
        run(["git", "apply", "--whitespace=nowarn", str(path)], cwd=destination, work=work, name=f"patch-{number}-apply")
        for name, expected in patch["files"].items():
            if sha256(regular(destination, name).read_bytes()) != expected["after"]:
                raise RuntimeFailure(f"patch postimage mismatch: {name}")
    actual = {p.relative_to(destination).as_posix(): sha256(p.read_bytes()) for p in destination.rglob("*") if p.is_file()}
    if actual != lock["runtime_files"]:
        raise RuntimeFailure("rebuilt runtime inventory differs from release")


def interpreter_facts(python: Path, work: Path) -> dict:
    output = run([str(python), "-I", "-B", "-c",
                  "import json,sys; print(json.dumps({'python':sys.executable,'prefix':sys.prefix,'version':list(sys.version_info[:3])}))"],
                 work=work, name="interpreter")
    return json.loads(output)


def build_runtime(destination: Path, environment: Path, work: Path, *, python: Path = Path(sys.executable), archive: Path | None = None) -> RuntimeBinding:
    """Prepare a new runtime and FINAL-path venv; caller owns cleanup/publication."""
    destination, environment, work = (Path(os.path.abspath(p)) for p in (destination, environment, work))
    if destination.exists() or environment.exists() or destination.is_symlink() or environment.is_symlink():
        raise RuntimeFailure("build requires absent runtime and environment paths")
    lock = load_release()
    facts = interpreter_facts(python, work)
    if facts["version"][:2] < lock["python"]["minimum"]:
        raise RuntimeFailure("unsupported Python version")
    archive = archive or fetch_archive(work / "upstream.tar.gz", work)
    extract_source(archive, destination, lock)
    apply_patches(destination, lock, work)
    # Resolve a base-interpreter launcher symlink before venv writes pyvenv.cfg.
    run([str(python.resolve()), "-m", "venv", str(environment)], work=work, name="venv")
    bound_python = environment / "bin/python"
    run([str(bound_python), "-m", "pip", "install", "--require-hashes", "--only-binary=:all:",
         "-r", str(RELEASE / "requirements.lock")], work=work, name="dependencies", network=True)
    if Path(interpreter_facts(bound_python, work)["prefix"]) != environment:
        raise RuntimeFailure("environment did not bind to its final path")
    binding = RuntimeBinding(str(bound_python), str(environment), release_digest())
    (destination / BINDING).write_text(json.dumps(asdict(binding), indent=2) + "\n")
    run([str(bound_python), "-B", str(destination / "scripts/attribution_guard.py")], work=work, name="attribution")
    return binding


def read_binding(runtime: Path) -> RuntimeBinding | None:
    if not (runtime / BINDING).exists():
        return None
    data = read_json(regular(runtime, BINDING))
    result = RuntimeBinding(**data)
    if not Path(result.python).is_absolute() or not Path(result.environment).is_absolute():
        raise RuntimeFailure("binding paths must be absolute")
    return result


def fingerprint(runtime: Path, lock: dict | None = None) -> dict[str, str]:
    lock = lock or load_release()
    names = {name for name in lock["runtime_files"] if not library_file(name)}
    for directory, folders, files in os.walk(runtime / "scripts", followlinks=False):
        parent = Path(directory)
        for name in folders + files:
            if (parent / name).is_symlink():
                raise RuntimeFailure(f"symlink in import tree: {parent / name}")
        for name in files:
            path = parent / name
            relative_name = path.relative_to(runtime).as_posix()
            if relative_name in names:
                continue
            cached = re.fullmatch(r"(.+)\.cpython-\d+(?:\.opt-\d+)?\.pyc", name)
            source = parent.parent / (cached[1] + ".py") if cached else None
            if parent.name != "__pycache__" or source is None or source.relative_to(runtime).as_posix() not in names:
                raise RuntimeFailure(f"unexpected import-tree file: {relative_name}")
            names.add(relative_name)
    return {name: sha256(regular(runtime, name).read_bytes()) for name in sorted(names)}


def check_integrity(runtime: Path, python: Path, work: Path) -> dict[str, str]:
    lock = load_release()
    actual = fingerprint(runtime, lock)
    for name in ("scripts/attribution_guard.py", "scripts/console_encoding.py", "LICENSE", "SPONSORS.md", "SPONSORS_CN.md"):
        if actual[name] != lock["runtime_files"][name]:
            raise RuntimeFailure(f"protected attribution hash mismatch: {name}")
    binding = read_binding(runtime)
    if binding:
        if Path(binding.python) != python or binding.release_sha256 != release_digest():
            raise RuntimeFailure("managed interpreter/release binding mismatch")
        expected = {n: h for n, h in lock["runtime_files"].items() if not library_file(n)}
        if {n: actual[n] for n in expected} != expected:
            raise RuntimeFailure("managed runtime hash mismatch")
        if Path(interpreter_facts(python, work)["prefix"]) != Path(binding.environment):
            raise RuntimeFailure("managed environment path mismatch")
    run([str(python), "-B", str(runtime / "scripts/attribution_guard.py")], work=work, name="integrity")
    return actual


def index_value(raw: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise RuntimeFailure(f"duplicate index key: {key}")
            result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise RuntimeFailure("index must be a JSON object")
    return value


def prepare_registration_view(runtime: Path, python: Path, view: Path, work: Path, *, indices: dict[str, bytes] | None = None) -> dict[str, bytes]:
    """Return candidate index bytes after own-CLI dry and actual registration."""
    if view.exists() or view.is_symlink():
        raise RuntimeFailure(f"registration view already exists: {view}")
    lock = load_release()
    before = check_integrity(runtime, python, work)
    if indices is None:
        indices = {k: regular(runtime, f"templates/{k}s/{k}s_index.json").read_bytes() for k in KINDS}
    values = {k: index_value(indices[k]) for k in KINDS}
    view.mkdir(parents=True)
    for name in before:
        dst = view / relative(name)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(regular(runtime, name), dst)
    for kind in KINDS:
        folder = view / "templates" / (kind + "s")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / (kind + "s_index.json")).write_bytes(indices[kind])
        shutil.copytree(PAYLOAD / "templates" / (kind + "s") / "oracle", folder / "oracle")
    for kind in KINDS:
        command = [str(python), "-B", str(view / "scripts/register_template.py"), "oracle", "--kind", kind]
        index = view / "templates" / (kind + "s") / (kind + "s_index.json")
        run(command + ["--dry-run"], work=work, name=f"register-{kind}-dry")
        if index.read_bytes() != indices[kind]:
            raise RuntimeFailure("register dry-run modified its index")
        run(command, work=work, name=f"register-{kind}")
    result = {}
    for kind in KINDS:
        raw = (view / "templates" / (kind + "s") / (kind + "s_index.json")).read_bytes()
        actual = index_value(raw)
        if "oracle" not in actual or {k: v for k, v in actual.items() if k != "oracle"} != {k: v for k, v in values[kind].items() if k != "oracle"}:
            raise RuntimeFailure(f"registration changed non-Oracle values: {kind}")
        if actual["oracle"] != lock["oracle_entries"][kind]:
            raise RuntimeFailure(f"invalid Oracle registry entry: {kind}")
        root = view / "templates" / (kind + "s") / "oracle"
        for name, digest in verify_payload(lock)["templates"][kind]["sha256"].items():
            if sha256(regular(root, name).read_bytes()) != digest:
                raise RuntimeFailure("registration modified frozen template bytes")
        result[kind] = raw
    if fingerprint(runtime, lock) != before:
        raise RuntimeFailure("runtime changed during isolated registration")
    return result


def assess_runtime(runtime: Path, *, python: Path | None = None, work: Path) -> RuntimeAssessment:
    """Read target; write only work. Unknown hashes require the full real probe."""
    runtime = runtime.absolute()
    if not runtime.exists() and not runtime.is_symlink():
        return RuntimeAssessment("install", str(runtime), None, "runtime absent", {})
    before = {}
    try:
        runtime = runtime.resolve(strict=True)
        if not runtime.is_dir():
            raise RuntimeFailure("runtime target is not a directory")
        binding = read_binding(runtime)
        python = python or (Path(binding.python) if binding else None)
        if python is None:
            raise RuntimeFailure("existing runtime requires an explicit durable interpreter")
        python = python.absolute()
        before = check_integrity(runtime, python, work)
        view = work / "registration-view"
        prepare_registration_view(runtime, python, view, work / "registration")
        report = work / "capability.json"
        run([str(python), "-B", str(SKILL / "scripts/verify_runtime.py"), "probe",
             "--runtime", str(view), "--work", str(work / "capability"), "--report", str(report)],
            work=work, name="capability")
        if read_json(report).get("status") != "passed":
            raise RuntimeFailure("capability probe did not pass")
        if fingerprint(runtime) != before:
            raise RuntimeFailure("runtime changed during capability probe")
        return RuntimeAssessment("reuse", str(runtime), str(python), "integrity and isolated capability passed", before, str(report))
    except (RuntimeFailure, OSError, ValueError, KeyError, TypeError) as exc:
        return RuntimeAssessment("blocked", str(runtime), str(python) if python else None, str(exc), before)
