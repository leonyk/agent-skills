#!/usr/bin/env python3
"""Run the installer through its real CLI in caller-owned isolated directories."""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import traceback

import installer as ins
import runtime as rt


def require(value, message):
    if not value:
        raise AssertionError(message)


def source_fingerprints():
    files = [Path(__file__).with_name(name) for name in
             ("installer.py", "install.py", "verify.py", "test_installer.py", "runtime.py", "verify_runtime.py")]
    files += [rt.RELEASE / "runtime-lock.json", rt.RELEASE / "requirements.lock", rt.PAYLOAD / "manifest.json"]
    files += sorted((rt.RELEASE / "patches").glob("*"))
    return {str(path): rt.sha256(path.read_bytes()) if path.is_file() else None for path in files}


class Acceptance:
    def __init__(self, root: Path, archive: Path, python: Path, report: Path, resume: bool, wheelhouse: Path | None = None):
        self.sources = source_fingerprints()
        self.release_sha256 = self.sources[str(rt.RELEASE / "runtime-lock.json")]
        self.root, self.archive, self.python, self.report = root, archive, python, report
        self.archive_sha256 = rt.sha256(archive.read_bytes())
        self.wheelhouse = wheelhouse or root / "wheels"
        self.stopped_processes = []
        self.run_id = os.urandom(6).hex()
        self.control, self.logs = root / "control", root / "logs"
        self.home, self.a, self.b = root / "home", root / "project-a", root / "project-b"
        self.cli = Path(__file__).with_name("install.py")
        self.results, self.calls = [], []
        self.serial = 0
        self.sentinel = {"summary": "untouched", "nested": [1, 1.0, True, False, None, {"unicode": "保留"}], "custom": {"opaque": "value"}}
        ins.safe_path(root, directory=True)
        if root.exists():
            require(resume and (root / "acceptance-owner.json").is_file(), "Acceptance work must be new, or explicitly resumed with its ownership marker")
        else:
            root.mkdir(parents=True)
            (root / "acceptance-owner.json").write_bytes(ins.canonical_json({"schema": 1, "purpose": "oracle-installer-acceptance", "root": str(root)}))
        for directory in (self.logs, self.home, self.a, self.b):
            directory.mkdir(exist_ok=True)
        self.serial = max((int(p.name.split("-", 1)[0]) for p in self.logs.glob("*.json")
                           if p.name.split("-", 1)[0].isdigit()), default=0)
        self.fixture_path = root / "fixtures.json"
        self.fixtures = ins.json_value(self.fixture_path.read_bytes()) if self.fixture_path.exists() else {}
        self.process_environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    def prepare_wheels(self):
        wheels = self.wheelhouse
        receipt = wheels / "receipt.json"
        if not receipt.exists():
            require(wheels == self.root / "wheels", "A supplied read-only wheelhouse needs its hash receipt")
            wheels.mkdir(exist_ok=True)
            if self.fixtures:
                download_python = Path(next(iter(self.fixtures.values()))["python"])
            else:
                tools = self.root / "wheel-tools"
                if not tools.exists():
                    rt.run([str(self.python.resolve()), "-m", "venv", str(tools)], work=self.root / "wheel-tool-logs", name="venv")
                download_python = tools / "bin/python"
            rt.run([str(download_python), "-m", "pip", "download", "--require-hashes", "--only-binary=:all:",
                    "--dest", str(wheels), "-r", str(rt.RELEASE / "requirements.lock")],
                   work=self.root / "wheel-download", name="download", network=True)
            receipt.write_bytes(ins.canonical_json({p.name: rt.sha256(p.read_bytes()) for p in wheels.glob("*.whl")}) + b"\n")
        expected = ins.json_value(receipt.read_bytes())
        require(expected == {p.name: rt.sha256(p.read_bytes()) for p in wheels.glob("*.whl")}, "Isolated wheelhouse changed")
        require(len(expected) == 6, "Wheelhouse does not contain all six locked distributions")
        self.process_environment.update(PIP_NO_INDEX="1", PIP_FIND_LINKS=str(wheels), PIP_CACHE_DIR=str(self.root / "pip-cache"))

    def save(self, status="running", error=None):
        current = source_fingerprints()
        unchanged = current == self.sources
        if status in {"passed", "partial_passed"}:
            require(unchanged, "Sources changed before the final acceptance receipt")
        value = {"schema": 1, "status": status, "scope": "installer implementation acceptance; no independent review or client acceptance",
                 "work": str(self.root), "release_sha256": self.release_sha256,
                 "source_fingerprints": self.sources, "source_fingerprints_at_write": current, "sources_unchanged": unchanged,
                 "archive": {"path": str(self.archive), "sha256": self.archive_sha256}, "wheelhouse": str(self.wheelhouse),
                 "platform": {"system": os.uname().sysname, "release": os.uname().release, "machine": os.uname().machine, "python": sys.version},
                 "checks": self.results, "cli_calls": self.calls, "fixtures": self.fixtures}
        if error:
            value["error"] = error
        ins.atomic_bytes(self.report, json.dumps(value, ensure_ascii=False, indent=2).encode() + b"\n")

    def checked(self, name, detail):
        require(source_fingerprints() == self.sources, "Installer or runtime sources changed during acceptance; use a fresh final run")
        self.results.append({"name": name, "status": "passed", **detail})
        self.save()
        print(json.dumps({"check": name, "status": "passed"}, ensure_ascii=False), flush=True)

    def command(self, args):
        return [str(self.python), "-B", str(self.cli), *map(str, args)]

    def run(self, args, expected=0, contains=None):
        require(source_fingerprints() == self.sources, "Installer or runtime sources changed before a CLI call")
        self.serial += 1
        command = self.command(args)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   env=self.process_environment, start_new_session=True)
        try:
            stdout, stderr = process.communicate(timeout=900)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise AssertionError("CLI timed out: " + " ".join(command))
        except BaseException:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise
        result = ins.json_value(stdout) if stdout.strip() else {}
        log = self.logs / f"{self.serial:04d}-{args[0]}.json"
        summary = {key: result[key] for key in ("status", "message", "digest", "plan", "runtime_action", "template_action", "consent_required", "receipt", "original_error") if key in result}
        log.write_bytes(ins.canonical_json({"argv": command, "exit": process.returncode, "result": summary, "stderr": stderr.decode(errors="replace")}) + b"\n")
        self.calls.append({"argv": command, "exit": process.returncode, "log": str(log), "status": result.get("status")})
        require(source_fingerprints() == self.sources, "Installer or runtime sources changed during a CLI call")
        allowed = {expected} if isinstance(expected, int) else set(expected)
        require(process.returncode in allowed, f"Expected exit {allowed}, got {process.returncode}: {result} {stderr.decode(errors='replace')}")
        if contains:
            require(contains.lower() in (stdout + stderr).decode(errors="replace").lower(), f"Expected failure evidence {contains!r}, got {result}")
        return result

    def plan(self, project: Path | None, name: str, *, explicit: Path | None = None, python: Path | None = None, expected=0, contains=None):
        scope = "project" if project else "global"
        out = self.control / (name + "-" + os.urandom(6).hex() + ".json")
        args = ["plan", "--ppt-scope", scope, "--oracle-scope", scope, "--home", self.home,
                "--python", python or self.python, "--work", self.control, "--out", out, "--archive", self.archive]
        if project:
            args += ["--project", project]
        if explicit:
            args += ["--runtime", explicit]
        result = self.run(args, expected, contains)
        if expected != 0:
            return result
        envelope = ins.json_value(out.read_bytes())
        self.remove_registration_copy(self.control / 'registration' / envelope['value']['id'])
        return {"path": out, "value": envelope["value"], "digest": envelope["digest"], "result": result}

    def remove_registration_copy(self, path):
        if path.exists():
            ins.safe_path(path, directory=True, absent_ok=False)
            require(ins.inside(path, self.control), 'Registration scratch escaped the verifier work directory')
            shutil.rmtree(path)

    def apply(self, plan, *, approved=False, fault=None, mode="exception", expected=0):
        args = ["apply", "--plan", plan["path"], "--work", self.control, "--archive", self.archive]
        if approved:
            args += ["--confirm", plan["digest"]]
        if fault:
            args += ["--fault-at", fault, "--fault-mode", mode]
        result = self.run(args, expected)
        if result.get('status') in {'committed', 'kept'}:
            self.remove_registration_copy(self.control / 'apply-registration' / plan['value']['id'])
        return result

    def recover(self, plan, *, expected=0, fault=None, mode="exception"):
        args = ["recover", "--plan", plan["path"], "--work", self.control]
        if fault:
            args += ["--fault-at", fault, "--fault-mode", mode]
        return self.run(args, expected)

    def read_receipt(self, plan):
        return ins.json_value(Path(plan["value"]["paths"]["receipt"]).read_bytes())["value"]

    def template_paths(self, target):
        return {name: target / relative for name, relative in ins.RELATIVE_OBJECTS.items()}

    def library_snapshot(self, target):
        return {name: ins.snapshot(path) for name, path in self.template_paths(target).items()}

    def registrar_count(self):
        return len(list(self.control.rglob("register-*.log")))

    def backup_count(self, target):
        state = Path(ins.paths_for(target, "0" * 32, self.control)["state"])
        return len(list(state.glob("transactions/*/backups")))

    def sentinel_install(self, target):
        for kind in ins.KINDS:
            directory = target / "templates" / (kind + "s")
            sentinel = directory / "acceptance_sentinel"
            sentinel.mkdir(exist_ok=True)
            (sentinel / "keep.txt").write_text("global and project libraries are independent\n")
            index = directory / (kind + "s_index.json")
            data = ins.json_value(index.read_bytes())
            data["acceptance_sentinel"] = self.sentinel
            index.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def setup(self):
        self.prepare_wheels()
        for key, project in (("global", None), ("project_a", self.a), ("project_b", self.b)):
            if key in self.fixtures:
                continue
            planned = self.plan(project, "new-" + key)
            require(planned["value"]["runtime_action"] == "install", "New scope did not select install")
            target = Path(planned["value"]["runtime"])
            require(not target.exists(), "Plan exposed an unbuilt runtime")
            result = self.apply(planned)
            require(result["status"] == "committed", "New install did not commit")
            binding = rt.read_binding(target)
            root = project or self.home
            require(binding and ins.inside(Path(binding.environment), root), "Dependency environment is outside scope")
            facts = rt.interpreter_facts(Path(binding.python), self.root / "interpreter-readbacks" / key)
            require(facts["prefix"] == binding.environment, "Fresh process lost the final environment binding")
            receipt = self.read_receipt(planned)
            require(receipt["verification"]["capability"]["source"] == "isolated_probe", "Actual new runtime did not run the real capability probe")
            for name in ins.RELATIVE_OBJECTS:
                marker = Path(receipt["backups"][name]["absence_marker"])
                require(ins.json_value(marker.read_bytes())["before"] == "absent", "New install lost an absence marker")
            self.sentinel_install(target)
            if key == "global":
                second_global = self.home / ".cursor/skills/ppt-master"
                second_global.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(target, second_global)
            self.fixtures[key] = {"runtime": str(target), "python": binding.python, "environment": binding.environment,
                                  "release_sha256": self.release_sha256,
                                  "plan": str(planned["path"]), "receipt": result["receipt"],
                                  "capability": receipt["verification"]["capability"]["evidence"]}
            self.fixture_path.write_bytes(ins.canonical_json(self.fixtures) + b"\n")
            self.checked("new_" + key, self.fixtures[key])
        self.global_target = Path(self.fixtures["global"]["runtime"])
        self.target = Path(self.fixtures["project_a"]["runtime"])
        require(all(value.get("release_sha256") == self.release_sha256 for value in self.fixtures.values()), "Fixture release differs; start a new --work directory")
        for key, project in (("global", None), ("project_a", self.a), ("project_b", self.b)):
            fixture = self.fixtures[key]
            target = Path(fixture["runtime"])
            before = ins.snapshot(target)
            args = ["inspect", "--probe", "--ppt-scope", "project" if project else "global", "--home", self.home,
                    "--runtime", target, "--python", fixture["python"], "--work", self.control]
            if project:
                args += ["--project", project]
            result = self.run(args)
            require(result["probe"] in {"isolated_probe", "cached_receipt"} and ins.snapshot(target) == before, "Inspect probe mutated its target")
        self.global_before = ins.snapshot(self.global_target)
        require(len({value["environment"] for value in self.fixtures.values()}) == 3, "Independent scopes share an environment")
        self.good_indices = {kind: (self.target / ins.RELATIVE_OBJECTS[kind + "_index"]).read_bytes() for kind in ins.KINDS}

    def reset(self, *, conflict=False):
        for kind in ins.KINDS:
            target = self.target / ins.RELATIVE_OBJECTS[kind]
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(rt.PAYLOAD / "templates" / (kind + "s") / "oracle", target)
            raw = self.good_indices[kind]
            if conflict:
                spec = target / "templates/design_spec.md"
                spec.write_bytes(spec.read_bytes() + b"\nUser customization retained in the full backup.\n")
                extra = target / "private-notes/extra-user-file.bin"
                extra.parent.mkdir()
                extra.write_bytes(b"\x00unknown user bytes\xff\n")
                data = ins.json_value(raw)
                data["oracle"] = {"summary": "custom registration", "nested": [True, 1, 1.0]}
                raw = json.dumps(data, ensure_ascii=False, indent=4).encode() + b"\n"
            (self.target / ins.RELATIVE_OBJECTS[kind + "_index"]).write_bytes(raw)

    def validate_sentinels(self):
        for kind in ins.KINDS:
            directory = self.target / "templates" / (kind + "s")
            actual = ins.json_value((directory / (kind + "s_index.json")).read_bytes())["acceptance_sentinel"]
            require(ins.same_json(actual, self.sentinel), "A non-Oracle JSON value or type changed")
            require((directory / "acceptance_sentinel/keep.txt").read_text() == "global and project libraries are independent\n", "A non-Oracle workspace changed")

    def core(self):
        before, registrations, backups = self.library_snapshot(self.target), self.registrar_count(), self.backup_count(self.target)
        planned = self.plan(self.a, "equal-keep")
        require(planned["value"]["template_action"] == "keep", "Equal templates did not select keep")
        require(planned["value"]["proof"]["source"] == "cached_receipt", "Repeat keep did not use the qualified receipt")
        self.apply(planned)
        require(self.library_snapshot(self.target) == before, "Keep changed bytes, identity, or mtime")
        require(self.registrar_count() == registrations, "Keep invoked a registrar")
        require(self.backup_count(self.target) == backups, "Keep created a backup")
        self.checked("equal_keep", {"bytes_mtimes_identities_unchanged": True, "registrar_calls": 0, "new_backups": 0})

        code_before = ins.code_snapshot(self.target)
        env_before = ins.snapshot(Path(self.fixtures["project_a"]["environment"]), links=True)
        for kind in ins.KINDS:
            shutil.rmtree(self.target / ins.RELATIVE_OBJECTS[kind])
            index = self.target / ins.RELATIVE_OBJECTS[kind + "_index"]
            value = ins.json_value(index.read_bytes())
            value.pop("oracle")
            index.write_text(json.dumps(value, ensure_ascii=False) + "\n")
        planned = self.plan(self.a, "compatible-reuse")
        require((planned["value"]["runtime_action"], planned["value"]["template_action"]) == ("reuse", "install"), "Compatible reuse selected wrong actions")
        self.apply(planned)
        receipt = self.read_receipt(planned)
        for kind in ins.KINDS:
            require(Path(receipt["backups"][kind]["absence_marker"]).is_file(), "Missing Oracle tree absence marker")
        require(ins.code_snapshot(self.target) == code_before and ins.snapshot(Path(self.fixtures["project_a"]["environment"]), links=True) == env_before, "Reuse wrote code or dependencies")
        self.validate_sentinels()
        self.checked("compatible_reuse", {"runtime_and_dependencies_unchanged": True, "receipt": planned["value"]["paths"]["receipt"]})

        unknown = self.a / "unmanaged-compatible-runtime"
        if unknown.exists():
            shutil.rmtree(unknown)
        shutil.copytree(self.target, unknown)
        (unknown / rt.BINDING).unlink()
        config = unknown / "scripts/config.py"
        config.write_bytes(config.read_bytes() + b"\n")
        unknown_before = ins.snapshot(unknown)
        planned = self.plan(self.a, "unknown-compatible", explicit=unknown, python=Path(self.fixtures["project_a"]["python"]))
        require(planned["value"]["proof"]["source"] == "isolated_probe", "Unknown fingerprint did not receive a real probe")
        self.apply(planned)
        require(ins.snapshot(unknown) == unknown_before, "Unknown compatible reuse modified its runtime")
        self.checked("unknown_fingerprint_reuse", {"probe": planned["value"]["proof"]["evidence"], "target_unchanged": True})
        registrar = unknown / "scripts/register_template.py"
        text = registrar.read_text()
        assignment = 'index[tid] = payload["entry"]'
        require(text.count(assignment) == 1, "Pinned registrar mutation target drifted")
        registrar.write_text(text.replace(assignment, "index[tid] = None"))
        poisoned = ins.snapshot(unknown)
        self.plan(self.a, "poisoned-registry", explicit=unknown, python=Path(self.fixtures["project_a"]["python"]),
                  expected=3, contains="invalid Oracle registry entry")
        require(ins.snapshot(unknown) == poisoned, "Rejected registrar was modified")
        registrar.write_text(text)
        shadow = self.target / "scripts/brand_assets"
        shadow.mkdir()
        (shadow / "__init__.py").write_text("raise RuntimeError('installer acceptance import shadow')\n")
        shadowed = ins.snapshot(self.target)
        self.plan(self.a, "import-shadow", expected=3, contains="unexpected import-tree file")
        require(ins.snapshot(self.target) == shadowed, "Import-shadow rejection modified the runtime")
        shutil.rmtree(shadow)
        self.checked("runtime_review_regressions", {"extra_import_tree_blocked": True, "invalid_oracle_registry_blocked": True, "target_writes": 0})
        self.timestamp_cache_regression()

        for kind in ins.KINDS:
            index = self.target / ins.RELATIVE_OBJECTS[kind + "_index"]
            value = ins.json_value(index.read_bytes())
            value.pop("oracle")
            index.write_text(json.dumps(value, ensure_ascii=False) + "\n")
        trees_before = {kind: ins.snapshot(self.target / ins.RELATIVE_OBJECTS[kind]) for kind in ins.KINDS}
        planned = self.plan(self.a, "missing-registration")
        require(planned["value"]["template_action"] == "register", "Missing registration did not select register")
        registrations = self.registrar_count()
        self.apply(planned)
        require(self.registrar_count() == registrations, "Apply reran a registration already bound into the plan")
        require(trees_before == {kind: ins.snapshot(self.target / ins.RELATIVE_OBJECTS[kind]) for kind in ins.KINDS}, "Register rewrote a matching Oracle tree")
        self.validate_sentinels()
        self.checked("missing_registration", {"matching_trees_unchanged": True, "apply_registrar_calls": 0})

        self.reset(conflict=True)
        before = self.library_snapshot(self.target)
        originals = {kind: (self.target / ins.RELATIVE_OBJECTS[kind + "_index"]).read_bytes() for kind in ins.KINDS}
        planned = self.plan(self.a, "replacement")
        require(planned["value"]["template_action"] == "replace", "Conflict did not require replacement")
        changed = {item["path"] for item in planned["value"]["changes"]}
        require(all(ins.RELATIVE_OBJECTS[kind] + "/private-notes/extra-user-file.bin" in changed for kind in ins.KINDS), "Plan omitted unknown user files")
        backups = self.backup_count(self.target)
        self.apply(planned, expected=6)
        require(self.library_snapshot(self.target) == before and self.backup_count(self.target) == backups, "Unconfirmed conflict wrote the target or backup")
        self.run(["apply", "--plan", planned["path"], "--work", self.control, "--confirm", "0" * 64], expected=6)
        self.apply(planned, approved=True)
        receipt = self.read_receipt(planned)
        for name, entry in receipt["backups"].items():
            require(ins.content(ins.snapshot(Path(entry["path"])), metadata=True) == ins.content(before[name], metadata=True), "Full backup omitted original bytes or mtimes")
        for kind in ins.KINDS:
            require(Path(receipt["backups"][kind + "_index"]["path"]).read_bytes() == originals[kind], "Backup changed original index bytes")
        self.validate_sentinels()
        self.checked("conflict_refusal_and_full_backup", {"receipt": planned["value"]["paths"]["receipt"], "unknown_user_files": True, "original_index_bytes": True})

        self.stale_and_untrusted()
        self.discovery_and_invalid_inputs()
        require(ins.snapshot(self.global_target) == self.global_before, "Project operations wrote the global sentinel library")
        self.checked("project_isolation", {"independent_project_roots": [str(self.a), str(self.b)], "global_bytes_mtimes_identities_unchanged": True})

    def timestamp_cache_regression(self):
        runtime = self.a / ("timestamp-runtime-" + self.run_id)
        shutil.copytree(self.target, runtime)
        (runtime / rt.BINDING).unlink()
        config = runtime / "scripts/config.py"
        original = config.read_bytes()
        prefix = b"raise RuntimeError('installer cache timestamp proof')\n"
        config.write_bytes(prefix + b'#' + b'x' * (len(original) - len(prefix) - 2) + b'\n')
        valid_time, invalid_time = 1700000000, 1700000002
        os.utime(config, (valid_time, valid_time))
        python = Path(self.fixtures['project_a']['python'])
        rt.run([str(python), '-I', '-B', '-c',
                'import py_compile,sys; py_compile.compile(sys.argv[1],doraise=True,invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)',
                str(config)], work=self.root / ('timestamp-compile-' + self.run_id), name='compile')
        config.write_bytes(original)
        os.utime(config, (invalid_time, invalid_time))
        fingerprint = rt.fingerprint(runtime)
        first = self.plan(self.a, 'timestamp-cold', explicit=runtime, python=python)
        require(first['value']['proof']['source'] == 'isolated_probe', 'Timestamp fixture did not run a real cold probe')
        os.utime(config, (valid_time, valid_time))
        actual = subprocess.run([str(python), '-B', str(runtime / 'scripts/apply_template.py'), '--help'],
                                capture_output=True, text=True, env=self.process_environment, timeout=60)
        output = actual.stdout + actual.stderr
        log = self.logs / ('timestamp-actual-' + self.run_id + '.log')
        log.write_text(output)
        require(actual.returncode != 0 and 'installer cache timestamp proof' in output, 'Retimed pyc did not activate the intended counterexample')
        require(rt.fingerprint(runtime) == fingerprint, 'Timestamp fixture changed bytes instead of only execution metadata')
        self.plan(self.a, 'timestamp-retimed', explicit=runtime, python=python, expected=3, contains='installer cache timestamp proof')
        self.checked('cached_proof_respects_code_metadata', {'unchanged_byte_fingerprint': True, 'retimed_runtime_blocked': True,
                     'counterexample_runtime': str(runtime), 'actual_failure_log': str(log)})

    def stale_and_untrusted(self):
        file = self.target / "templates/brands/oracle/templates/design_spec.md"
        for mode in ("bytes", "mtime", "inode", "index", "interpreter"):
            planned = self.plan(self.a, "stale-" + mode)
            path = file if mode in {"bytes", "mtime", "inode"} else self.target / ins.RELATIVE_OBJECTS["brand_index"] if mode == "index" else Path(self.fixtures["project_a"]["environment"]) / "pyvenv.cfg"
            raw, info = path.read_bytes(), path.stat()
            moved = self.root / ("stale-original-" + mode + "-" + self.run_id)
            if mode == "inode":
                path.rename(moved)
                shutil.copy2(moved, path)
            elif mode in {"mtime", "interpreter"}:
                os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns + 1))
            else:
                path.write_bytes(raw + b"\n")
            before = ins.snapshot(path)
            self.apply(planned, expected=4)
            require(ins.snapshot(path) == before, "Stale plan modified the changed input")
            if mode == "inode":
                path.unlink()
                moved.rename(path)
            else:
                path.write_bytes(raw)
                os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns))
            self.checked("stale_" + mode, {"exit": 4})

        planned = self.plan(self.a, "tamper-base")
        envelope = ins.json_value(planned["path"].read_bytes())
        before = ins.snapshot(self.target)
        for field in ("runtime", "stage", "consent", "indices"):
            changed = copy.deepcopy(envelope)
            if field == "runtime":
                changed["value"]["runtime"] = str(self.root / "unrelated")
            elif field == "stage":
                changed["value"]["paths"]["stage"] = str(self.root / "unrelated")
            elif field == "consent":
                changed["value"]["consent_required"] = True
            else:
                changed["value"]["indices"]["brand"] = "e30="
            changed["digest"] = ins.digest(changed["value"])
            path = self.control / ("tampered-" + field + ".json")
            path.write_bytes(ins.canonical_json(changed))
            self.run(["apply", "--plan", path, "--work", self.control], expected=9, contains="invalid")
        require(ins.snapshot(self.target) == before and not (self.root / "unrelated").exists(), "Edited plan redirected a write")
        self.checked("untrusted_plan_fields", {"recomputed_digest_still_rejected": True, "fields": ["runtime", "stage", "consent", "indices"]})
        forged = copy.deepcopy(envelope["value"])
        forged["paths"]["stage"] = str(self.root / "unrelated")
        signed = self.control / "forged-derived-path.json"
        signed.write_bytes(ins.canonical_json(ins.seal(forged, ins.work_key(self.control), "plan")))
        self.run(["apply", "--plan", signed, "--work", self.control], expected=9, contains="Derived transaction paths")
        require(not (self.root / "unrelated").exists() and ins.snapshot(self.target) == before, "A re-signed field bypassed derived path validation")
        self.checked("derived_paths_revalidated", {"valid_seal_does_not_authorize_arbitrary_paths": True})

        bad_archive = self.root / "invalid-upstream.tar.gz"
        bad_archive.write_bytes(b"not the pinned upstream archive")
        self.run(["apply", "--plan", planned["path"], "--work", self.control, "--archive", bad_archive], expected=3, contains="Archive hash")
        copied = self.root / "corrupt-payload-skill"
        if copied.exists():
            shutil.rmtree(copied)
        shutil.copytree(rt.SKILL, copied)
        damaged = copied / "payload/templates/brands/oracle/templates/design_spec.md"
        damaged.write_bytes(damaged.read_bytes() + b"\ncorrupt payload\n")
        original_cli = self.cli
        self.cli = copied / "scripts/install.py"
        try:
            self.run(["apply", "--plan", planned["path"], "--work", self.control], expected=3, contains="payload hash mismatch")
        finally:
            self.cli = original_cli
        require(ins.snapshot(self.target) == before, "Invalid archive or payload wrote to the target")
        self.checked("invalid_release_inputs", {"archive_rejected_before_publication": True, "payload_rejected_before_publication": True})

    def discovery_and_invalid_inputs(self):
        other = self.a / ".cursor/skills/ppt-master"
        other.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.target, other)
        before = self.library_snapshot(self.target)
        self.plan(self.a, "ambiguous", expected=3, contains="Multiple real")
        planned = self.plan(self.a, "explicit-runtime", explicit=self.target)
        self.apply(planned)
        require(self.library_snapshot(self.target) == before, "Explicit compatible keep wrote templates")
        shutil.rmtree(other)
        for client in (".cursor", ".codex"):
            alias = self.a / client / "skills/ppt-master"
            alias.parent.mkdir(parents=True, exist_ok=True)
            alias.symlink_to(self.target, target_is_directory=True)
        result = self.run(["inspect", "--ppt-scope", "project", "--project", self.a, "--home", self.home])
        require(len(result["candidates"]) == 1 and len(result["candidates"][0]["display_paths"]) == 3, "Aliases were not merged by canonical target")
        for client in (".cursor", ".codex"):
            (self.a / client / "skills/ppt-master").unlink()
        self.checked("ambiguity_and_aliases", {"ambiguous_exit": 3, "merged_aliases": 3, "explicit_selection": True})

        bad_work = self.root / "must-stay-absent"
        self.run(["plan", "--ppt-scope", "global", "--oracle-scope", "project", "--project", self.a, "--home", self.home,
                  "--work", bad_work, "--out", bad_work / "plan.json"], expected=3, contains="scopes differ")
        require(not bad_work.exists(), "Scope mismatch wrote or downloaded anything")
        self.plan(self.a, "project-escape", explicit=self.global_target, expected=3, contains="escapes")
        for variant in ("target-symlink", "ancestor-symlink", "target-file", "root-symlink"):
            project = self.root / (variant + "-" + self.run_id)
            if variant == "root-symlink":
                project.symlink_to(self.a, target_is_directory=True)
            else:
                project.mkdir()
                target = project / ".agents/skills/ppt-master"
                if variant == "ancestor-symlink":
                    (project / ".agents").symlink_to(self.home / ".agents", target_is_directory=True)
                else:
                    target.parent.mkdir(parents=True)
                    if variant == "target-file":
                        target.write_text("a file is not a runtime")
                    else:
                        target.symlink_to(self.global_target, target_is_directory=True)
            self.plan(project, "invalid-" + variant, expected=3, contains="directory" if variant == "target-file" else "Symlink")
        self.checked("scope_and_path_guards", {"scope_mismatch_writes": 0, "project_escape": "blocked", "symlink_and_file_variants": 4})

        index = self.target / ins.RELATIVE_OBJECTS["brand_index"]
        raw, info = index.read_bytes(), index.stat()
        invalid = {
            "orphan": (json.dumps({**ins.json_value(raw), "absent_workspace": {}}).encode(), "Orphan"),
            "oracle_orphan": (raw, "Orphan"),
            "malformed": (b'{broken', "Malformed JSON"),
            "duplicate": (b'{"x":1,"x":2}', "Duplicate JSON"),
            "nested_duplicate": (b'{"x":{"y":1,"y":2}}', "Duplicate JSON"),
            "nonfinite": (b'{"x":NaN}', "Non-finite"),
            "array": (b'[]', "JSON object"),
        }
        for name, (value, evidence) in invalid.items():
            moved = self.root / "orphan-oracle"
            if name == "oracle_orphan":
                (self.target / ins.RELATIVE_OBJECTS["brand"]).rename(moved)
            index.write_bytes(value)
            before = self.library_snapshot(self.target)
            self.plan(self.a, name, expected=3, contains=evidence)
            require(self.library_snapshot(self.target) == before, "Invalid index caused target writes")
            if name == "oracle_orphan":
                moved.rename(self.target / ins.RELATIVE_OBJECTS["brand"])
            index.write_bytes(raw)
            os.utime(index, ns=(info.st_atime_ns, info.st_mtime_ns))
        self.checked("invalid_indices", {"variants": list(invalid), "target_writes": 0})

        module = self.target / "scripts/svg_to_pptx/pptx_package/template_language.py"
        saved = self.root / "incompatible-language.py"
        module.rename(saved)
        before = ins.snapshot(self.target)
        self.plan(self.a, "incompatible", expected=3, contains="missing regular file")
        require(ins.snapshot(self.target) == before, "Incompatible runtime was patched")
        saved.rename(module)
        self.checked("incompatible_runtime", {"in_place_patch": False, "exit": 3})

    def stop_at(self, plan, boundary, *, recovery=False):
        require(source_fingerprints() == self.sources, "Sources changed before the fault process")
        args = ["recover" if recovery else "apply", "--plan", plan["path"], "--work", self.control,
                "--fault-at", boundary, "--fault-mode", "stop"]
        if not recovery:
            args += ["--archive", self.archive]
            if plan["value"]["consent_required"]:
                args += ["--confirm", plan["digest"]]
        ready = self.control / ("fault-" + plan["value"]["id"] + ".json")
        if ready.exists():
            ready.unlink()
        command = self.command(args)
        output = self.logs / ("stopped-" + plan["value"]["id"] + ".log")
        stream = output.open("wb")
        process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT,
                                   env=self.process_environment, start_new_session=True)
        self.stopped_processes.append((process, stream))
        end = time.monotonic() + 900
        while not ready.exists():
            if process.poll() is not None:
                stream.close()
                raise AssertionError("CLI exited before fault boundary: " + output.read_text())
            if time.monotonic() > end:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                stream.close()
                raise AssertionError("CLI did not reach " + boundary)
            time.sleep(0.05)
        require(ins.json_value(ready.read_bytes())["boundary"] == boundary, "Wrong fault boundary")
        require(source_fingerprints() == self.sources, "Sources changed while preparing the fault process")
        self.calls.append({"argv": command, "exit": "SIGKILL after SIGSTOP", "boundary": boundary, "log": str(output)})
        return process, stream

    def kill_stopped(self, stopped):
        process, stream = stopped
        os.killpg(process.pid, signal.SIGKILL)
        require(process.wait(timeout=30) == -signal.SIGKILL, "Fault process was not killed")
        stream.close()

    def cleanup_processes(self):
        for process, stream in self.stopped_processes:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=30)
            if not stream.closed:
                stream.close()

    def third_mutation(self, plan, boundary):
        value = plan["value"]
        if ":active:" in boundary:
            path = Path(value["paths"]["state"]) / "active.json"
        elif value["runtime_action"] == "install" and (boundary.endswith(":environment") or not Path(value["runtime"]).exists()):
            path = Path(value["environment"])
        else:
            name = boundary.split(":")[-1]
            path = Path(value["runtime"]) / ins.RELATIVE_OBJECTS.get(name, ins.RELATIVE_OBJECTS["brand"])
        if path.is_dir():
            candidates = [path / "templates/design_spec.md", path / "pyvenv.cfg"]
            path = next((p for p in candidates if p.is_file()), next((p for p in path.rglob("*") if p.is_file()), path / "third-party.txt"))
        if path.exists():
            raw, info = path.read_bytes(), path.stat()
            path.write_bytes(raw + b"\nthird-party edit must survive\n")

            def restore():
                path.write_bytes(raw)
                os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns))
        else:
            parent, info = path.parent, path.parent.stat()
            path.write_bytes(b"third-party owned object\n")

            def restore():
                path.unlink()
                os.utime(parent, ns=(info.st_atime_ns, info.st_mtime_ns))
        return path, restore

    def outcome(self, plan, before):
        receipt = self.read_receipt(plan)
        target = Path(plan["value"]["runtime"])
        if receipt["status"] == "committed":
            ins.verify_postconditions(ins.InstallPlan(**plan["value"]), target)
            self.remove_registration_copy(self.control / 'apply-registration' / plan['value']['id'])
            return "complete_target"
        require(receipt["status"] == "aborted", "Recovery did not settle the transaction")
        actual = self.library_snapshot(target) if plan["value"]["runtime_action"] == "reuse" else ins.snapshot(target)
        require(actual == before, "Recovery did not restore exact original identities, bytes, and mtimes")
        self.remove_registration_copy(self.control / 'apply-registration' / plan['value']['id'])
        return "complete_original"

    def faults(self):
        boundaries = ins.publication_boundaries(list(ins.RELATIVE_OBJECTS))
        for boundary in boundaries:
            for mode in ("exception", "kill", "third_party"):
                self.reset(conflict=True)
                before = self.library_snapshot(self.target)
                plan = self.plan(self.a, "fault-" + mode)
                require(len(ins.initial_receipt(ins.InstallPlan(**plan["value"])).operations) == 4, "Fault fixture does not publish all four objects")
                if mode == "third_party":
                    stopped = self.stop_at(plan, boundary)
                    changed, restore = self.third_mutation(plan, boundary)
                    self.kill_stopped(stopped)
                    third = ins.snapshot(self.target)
                    self.recover(plan, expected=7)
                    require(ins.snapshot(self.target) == third, "Recovery changed third-party content or another object before reporting conflict")
                    require(b"third-party" in changed.read_bytes(), "Recovery lost third-party bytes")
                    restore()
                else:
                    expected = -signal.SIGKILL if mode == "kill" else (0 if boundary in {"after:receipt-complete", "before:active:committed", "after:active:committed", "after:complete"} else 8)
                    self.apply(plan, approved=True, fault=boundary, mode=mode, expected=expected)
                self.recover(plan)
                outcome = self.outcome(plan, before)
                self.validate_sentinels()
                self.checked("transaction_" + mode + "_" + boundary, {"boundary": boundary, "fault": mode, "outcome": outcome, "receipt": plan["value"]["paths"]["receipt"]})
        for location in ("stage", "backup", "receipt"):
            self.reset(conflict=True)
            before = self.library_snapshot(self.target)
            plan = self.plan(self.a, "third-party-" + location)
            self.apply(plan, approved=True, fault="before:complete", mode="kill", expected=-signal.SIGKILL)
            path = (Path(plan["value"]["paths"][location]) / "brand/templates/design_spec.md"
                    if location != "receipt" else Path(plan["value"]["paths"]["receipt"]))
            raw, info = path.read_bytes(), path.stat()
            path.write_bytes(raw + b"\nthird-party edit must survive\n")
            actual = ins.snapshot(self.target)
            self.recover(plan, expected=9 if location == "receipt" else 7)
            require(ins.snapshot(self.target) == actual and path.read_bytes().endswith(b"third-party edit must survive\n"), "Recovery overwrote a changed stage, backup, or receipt")
            path.write_bytes(raw)
            os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns))
            self.recover(plan)
            self.outcome(plan, before)
            self.checked("third_party_" + location, {"preserved": True, "receipt": plan["value"]["paths"]["receipt"]})

    def new_faults(self):
        boundaries = ["before:environment", "after:environment", *ins.publication_boundaries(["runtime"])]
        for boundary in boundaries:
            for mode in ("exception", "kill", "third_party"):
                project = self.root / "new-faults" / self.run_id / (mode + "-" + boundary.replace(":", "-"))
                project.mkdir(parents=True)
                plan = self.plan(project, "new-fault-" + mode)
                before = {"kind": "absent"}
                if mode == "third_party":
                    stopped = self.stop_at(plan, boundary)
                    changed, restore = self.third_mutation(plan, boundary)
                    self.kill_stopped(stopped)
                    target, env = Path(plan["value"]["runtime"]), Path(plan["value"]["environment"])
                    third = (ins.snapshot(target), ins.snapshot(env, links=True))
                    self.recover(plan, expected=7)
                    require((ins.snapshot(target), ins.snapshot(env, links=True)) == third, "New-install recovery changed third-party content")
                    require(b"third-party" in changed.read_bytes(), "New-install recovery lost third-party marker bytes")
                    restore()
                else:
                    expected = -signal.SIGKILL if mode == "kill" else (0 if boundary in {"after:receipt-complete", "before:active:committed", "after:active:committed", "after:complete"} else 8)
                    self.apply(plan, fault=boundary, mode=mode, expected=expected)
                self.recover(plan)
                outcome = self.outcome(plan, before)
                self.checked("new_runtime_" + mode + "_" + boundary, {"boundary": boundary, "fault": mode, "outcome": outcome,
                             "environment_renamed": False, "receipt": plan["value"]["paths"]["receipt"]})

    def recovery_faults(self):
        boundaries = ins.publication_boundaries(list(ins.RELATIVE_OBJECTS), recovery=True)
        for boundary in boundaries:
            for mode in ("exception", "kill", "third_party"):
                self.reset(conflict=True)
                before = self.library_snapshot(self.target)
                plan = self.plan(self.a, "recovery-fault-" + mode)
                self.apply(plan, approved=True, fault="before:complete", mode="kill", expected=-signal.SIGKILL)
                if mode == "third_party":
                    stopped = self.stop_at(plan, boundary, recovery=True)
                    changed, restore = self.third_mutation(plan, boundary)
                    self.kill_stopped(stopped)
                    third = ins.snapshot(self.target)
                    self.recover(plan, expected=7)
                    require(ins.snapshot(self.target) == third and b"third-party" in changed.read_bytes(), "Interrupted recovery overwrote a third-party edit")
                    restore()
                else:
                    self.recover(plan, fault=boundary, mode=mode, expected=-signal.SIGKILL if mode == "kill" else 10)
                self.recover(plan)
                outcome = self.outcome(plan, before)
                self.checked("recovery_" + mode + "_" + boundary, {"boundary": boundary, "fault": mode, "outcome": outcome, "receipt": plan["value"]["paths"]["receipt"]})

    def new_recovery_faults(self):
        project = self.root / ("new-recovery-fixture-" + self.run_id)
        project.mkdir()
        plan = self.plan(project, "new-recovery")
        self.apply(plan, fault="before:complete", mode="kill", expected=-signal.SIGKILL)
        receipt_path = Path(plan["value"]["paths"]["receipt"])
        original_receipt = receipt_path.read_bytes()
        active = Path(plan["value"]["paths"]["state"]) / "active.json"
        retained_active = self.root / ("new-recovery-active-" + plan["value"]["id"])
        os.link(active, retained_active)
        target = Path(plan["value"]["runtime"])
        stage = Path(plan["value"]["paths"]["stage"]) / "runtime"
        postimage = ins.snapshot(target)
        boundaries = ins.publication_boundaries(["runtime"], recovery=True)
        for boundary in boundaries:
            for mode in ("exception", "kill", "third_party"):
                actual = ins.snapshot(target)
                if actual == {"kind": "absent"}:
                    require(ins.snapshot(stage) == postimage, "Recovery replay lost the genuine prepared runtime")
                    ins.atomic_rename(stage, target, replace=False)
                else:
                    require(actual == postimage, "Recovery replay target has unexpected content")
                restore_active = self.root / ("restore-active-inode-" + plan["value"]["id"])
                if not active.samefile(retained_active):
                    os.link(retained_active, restore_active)
                    os.replace(restore_active, active)
                ins.atomic_bytes(receipt_path, original_receipt)
                if mode == "third_party":
                    stopped = self.stop_at(plan, boundary, recovery=True)
                    changed, restore = self.third_mutation(plan, boundary)
                    self.kill_stopped(stopped)
                    third = ins.snapshot(target), ins.snapshot(Path(plan["value"]["environment"]), links=True)
                    self.recover(plan, expected=7)
                    require((ins.snapshot(target), ins.snapshot(Path(plan["value"]["environment"]), links=True)) == third,
                            "New-runtime recovery changed third-party state")
                    require(b"third-party" in changed.read_bytes(), "New-runtime recovery lost third-party marker bytes")
                    restore()
                else:
                    self.recover(plan, fault=boundary, mode=mode, expected=-signal.SIGKILL if mode == "kill" else 10)
                interrupted = self.logs / ("new-recovery-" + mode + "-" + boundary.replace(":", "-") + ".json")
                interrupted.write_bytes(receipt_path.read_bytes())
                self.recover(plan)
                outcome = self.outcome(plan, {"kind": "absent"})
                self.checked("new_recovery_" + mode + "_" + boundary, {
                    "boundary": boundary, "fault": mode, "outcome": outcome, "interrupted_receipt": str(interrupted),
                    "fixture": "replayed genuine qualified new-runtime transaction; unchanged original environment and postimage inodes"})

    def locking(self):
        self.reset(conflict=True)
        before = self.library_snapshot(self.target)
        first, second = self.plan(self.a, "lock-first"), self.plan(self.a, "lock-second")
        stopped = self.stop_at(first, "before:publish:brand")
        lock = Path(first["value"]["paths"]["lock"])
        identity = ins.identity(lock)
        first_receipt = Path(first["value"]["paths"]["receipt"])
        receipt_bytes = first_receipt.read_bytes()
        self.apply(second, approved=True, expected=5)
        self.recover(first, expected=5)
        require(first_receipt.read_bytes() == receipt_bytes, "A blocked lock contender changed the owner's receipt")
        require(ins.identity(lock) == identity and self.library_snapshot(self.target) == before, "A lock contender bypassed exclusion")
        self.kill_stopped(stopped)
        self.recover(first)
        self.apply(second, approved=True)
        require(ins.identity(lock) == identity, "Lock inode was unlinked or replaced")
        self.checked("stable_flock_exclusion", {"two_processes": True, "contender_exit": 5, "owner_receipt_preserved": True, "lock_identity": identity})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("accept", choices=("accept",))
    parser.add_argument("--work", type=Path, required=True, help="New isolated root for all targets and command work")
    parser.add_argument("--archive", type=Path, required=True, help="Read-only pinned upstream archive")
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--wheelhouse", type=Path, help="Read-only wheel directory and receipt.json from an earlier verifier run; pip still enforces the release hash lock")
    parser.add_argument("--suite", choices=("all", "core", "faults", "new-faults", "recovery-faults", "new-recovery-faults", "locking"), default="all")
    parser.add_argument("--resume", action="store_true", help="Reuse only this verifier's existing isolated fixtures for a focused recheck")
    args = parser.parse_args()
    runner = Acceptance(ins.absolute(args.work), ins.absolute(args.archive), ins.absolute(args.python), ins.absolute(args.report), args.resume,
                        ins.absolute(args.wheelhouse) if args.wheelhouse else None)
    try:
        runner.setup()
        suites = {"core": runner.core, "faults": runner.faults, "new-faults": runner.new_faults,
                  "recovery-faults": runner.recovery_faults, "new-recovery-faults": runner.new_recovery_faults, "locking": runner.locking}
        for name, run in suites.items():
            if args.suite in {"all", name}:
                run()
        require(ins.snapshot(runner.global_target) == runner.global_before, "Global sentinel library changed during project acceptance")
        runner.save("passed" if args.suite == "all" else "partial_passed")
        print(json.dumps({"status": "passed" if args.suite == "all" else "partial_passed", "report": str(runner.report), "checks": len(runner.results)}), flush=True)
        return 0
    except Exception as exc:
        runner.save("failed", {"message": str(exc), "traceback": traceback.format_exc()})
        print(json.dumps({"status": "failed", "message": str(exc), "report": str(runner.report)}), flush=True)
        return 1
    finally:
        runner.cleanup_processes()


if __name__ == "__main__":
    raise SystemExit(main())
