# Runtime API

`scripts/runtime.py` uses the Python standard library. It owns source preparation, interpreter binding, integrity checks, capability checks, and isolated registration. It does not choose a scope, obtain approval, lock a real library, publish files, or recover a transaction.

## Release and payload

`load_release() -> dict` verifies patch bytes, declared patch paths, the dependency lock, the original payload manifest, and all 138 Oracle files. `release_digest() -> str` identifies that validated release manifest. The installer binds this digest into its plan and rechecks it before preparation and publication.

`verify_payload() -> dict` returns the original manifest after checking the complete Brand and Layout file sets and 23 page SVGs. `PAYLOAD` is the plugin-local payload directory. Workspaces are `PAYLOAD / "templates/brands/oracle"` and `PAYLOAD / "templates/layouts/oracle"`.

`fingerprint(runtime: Path) -> dict[str, str]` hashes the controlled code, documentation, and static resources. It excludes the four mutable template libraries. Missing files and symlinks inside controlled paths fail. This fingerprint is not a capability verdict.

## New runtime

`build_runtime(destination: Path, environment: Path, work: Path, *, python: Path = Path(sys.executable), archive: Path | None = None) -> RuntimeBinding`

Both `destination` and `environment` must be absent. All paths are explicit. The caller validates scope and canonical ancestry first. `destination` may be a staging directory that the caller later publishes by rename. `environment` is its final, durable path and must never be renamed.

The function verifies the official archive, rejects unsafe members, extracts only `source_files`, applies patches in order after exact preimage checks and `git apply --check`, then checks the complete resulting file inventory. It creates the environment at its final path and installs the six hash-locked dependencies. It runs the unmodified attribution guard and writes `oracle-runtime-binding.json` inside the prepared runtime.

`RuntimeBinding` contains `python`, `environment`, and `release_sha256`. All stored interpreter paths are absolute. `read_binding(runtime) -> RuntimeBinding | None` reads the durable binding without activating a shell environment. The environment's `sys.prefix` must match the stored environment during integrity checks.

`fetch_archive(destination, work) -> Path` downloads the pinned official archive. An explicitly supplied archive is checked identically. Network connection failures and timeouts retry with all six uppercase and lowercase proxy variables set to `http://127.0.0.1:8080`.

Preparation failures raise `RuntimeFailure`. Newly created paths remain available for the caller's rollback. This function never removes or replaces an existing runtime or environment. The caller records ownership before calling it and cleans only objects created by its transaction.

## Existing runtime

`assess_runtime(runtime: Path, *, python: Path | None = None, work: Path) -> RuntimeAssessment`

`work` is a new, caller-owned scratch path. The target remains read-only. The assessment uses a saved binding when `python` is omitted. An unmanaged candidate needs an explicit interpreter. A display alias is resolved to the real runtime path.

The result contains `action`, `runtime`, `python`, `reason`, `fingerprint`, and optional `evidence`:

| action | Meaning |
| --- | --- |
| `install` | The requested runtime path is absent. No runtime or environment is created. |
| `reuse` | Integrity, interpreter, isolated registration, actual Oracle previews, relocated formal export, and generic behavior passed. |
| `blocked` | A precise prerequisite or behavior failed. No in-place repair is attempted. |

A managed candidate must match its release and controlled hashes. An unmanaged candidate may have unknown hashes. Protected attribution files must still match, the official guard must pass, and the complete isolated behavioral probe must pass. Version strings never authorize reuse. The snapshot is checked again after the probe. The caller still rechecks target identity and the plan's preimages under its publication lock.

`check_integrity(runtime, python, work) -> dict[str, str]` implements the integrity layer alone. It is not sufficient to authorize reuse.

## Registration view

`prepare_registration_view(runtime: Path, python: Path, view: Path, work: Path, *, indices: dict[str, bytes] | None = None) -> dict[str, bytes]`

`view` must be absent and must be a caller-owned isolated location. `work` holds logs and isolated process homes. The function copies the declared runtime code and static resources, excluding mutable libraries and the managed binding. It copies the frozen Oracle workspaces and the supplied original index bytes. `indices` has the keys `brand` and `layout`. When omitted, these two indices are read from the selected runtime. Malformed JSON, duplicate keys, and non-object indices fail.

The copied runtime's own `register_template.py oracle --kind <kind>` runs first with `--dry-run`, then without it. The dry run must preserve index bytes. Both final Oracle entries must equal the pinned official registrar's output in `runtime-lock.json`, and every other JSON value must remain unchanged. The frozen Oracle files are checked again. The return value contains the two candidate index byte strings. The caller publishes them through its own transaction; the real library's registration CLI is never invoked.

An unexpected file in the runtime's script import tree blocks reuse. Bytecode caches for declared source files are copied with their source timestamps so the isolated interpreter sees the same import behavior. The view excludes credentials, environment directories, and user projects. Required unlisted modules cannot disappear silently from the program being tested.

## Verification command

```sh
python3 -B <skill>/scripts/verify_runtime.py qualify \
  --work <new-isolated-directory> \
  --report <report.json>
```

`--archive <file>` optionally supplies a previously downloaded archive with the locked hash. `qualify` always rebuilds the runtime and its environment. It checks registration, both export CLIs, ZIP structure, failing mutations, an official unextended template, generic source-theme preservation, safe extraction, wrong patch preimages, missing dependencies, and all three classifications. Exit zero and `status: passed` mean runtime qualification only.

The internal `probe --runtime <isolated-view> --work <new-directory> --report <report.json>` command runs under the selected runtime interpreter. It is also the capability authority used by `assess_runtime`.

The verifier creates a complete 23-page Chinese content roster for formal Quick export. The unmodified full `master_defaults.json` requires all 23 layout definitions. A smaller Quick roster needs a deliberately scoped project profile or the ordinary locked export's retained layout definitions. Preview samples and formal native charts retain Arial and Microsoft YaHei declarations. Formal slide, table, layout, and master text uses theme references. Reports enumerate fonts by XML part, including charts. Native PowerPoint interaction and visual layout acceptance remain separate.
