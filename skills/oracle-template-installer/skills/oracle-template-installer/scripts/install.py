#!/usr/bin/env python3
"""Noninteractive Oracle template installation with explicit scopes and plans."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import installer
import runtime


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise installer.InstallFailure("usage", message)


def parser() -> argparse.ArgumentParser:
    result = Parser(description=__doc__, epilog="Exit codes: 0 success; 2 usage; 3 blocked; 4 stale; 5 lock busy; 6 confirmation required; 7 recovery conflict; 8 failure rolled back; 9 invalid plan; 10 recovery interrupted.")
    commands = result.add_subparsers(dest="command", required=True, parser_class=Parser)
    for name in ("inspect", "plan"):
        command = commands.add_parser(name, help="Read selected scope; probe and plan preparation write only isolated work")
        command.add_argument("--ppt-scope", choices=("global", "project"), required=name == "plan", default=None if name == "plan" else "global")
        command.add_argument("--oracle-scope", choices=("global", "project"), required=name == "plan")
        command.add_argument("--project", help="Existing real project root; required for project scope")
        command.add_argument("--home", default=str(Path.home()), help="Discovery home; use an isolated existing home for acceptance")
        command.add_argument("--runtime", help="Select one existing real runtime within the selected scope; no symlink")
        command.add_argument("--python", default=sys.executable, help="Base Python for new installs; durable interpreter for unmanaged reuse. Managed reuse reads its binding.")
        command.add_argument("--work", required=name == "plan", help="Private durable directory, initially empty or absent; retain it for apply/recover")
        if name == "inspect":
            command.add_argument("--probe", action="store_true", help="Run real isolated compatibility checks, or reuse a matching authenticated receipt")
        else:
            command.add_argument("--out", required=True, help="New plan file inside --work; includes complete changes and backups")
            command.add_argument("--archive", help="Pinned archive for a new install's private planning reference. Otherwise downloaded after scope validation.")
    for name in ("apply", "recover"):
        command = commands.add_parser(name, help="Publish a reviewed plan" if name == "apply" else "Reconcile a receipt in a fresh process; retain all third-party changes")
        command.add_argument("--plan", required=True, help="Original authenticated plan file")
        command.add_argument("--work", required=True, help="The same durable work directory used for plan")
        command.add_argument("--fault-at", help="Acceptance only: inject at a before/after publication, record, environment, or completion boundary")
        command.add_argument("--fault-mode", choices=("exception", "kill", "stop"), default="exception", help="Acceptance only: raise, SIGKILL, or SIGSTOP at the named boundary")
        if name == "apply":
            command.add_argument("--confirm", help="Exact current plan digest, required only for replacement after reviewing its changes and backup paths. A digest alone is not consent.")
            command.add_argument("--archive", help="Optional pinned archive for the actual new runtime build")
    return result


def main(argv=None) -> int:
    try:
        args = parser().parse_args(argv)
        path = lambda value: installer.absolute(value) if value else None
        if args.command in {"inspect", "plan"}:
            selected = installer.selection(args.ppt_scope, args.oracle_scope or args.ppt_scope, args.project, args.home)
            if args.command == "inspect":
                result = installer.inspect(selected, path(args.runtime), path(args.python), path(args.work), args.probe)
            else:
                result = installer.plan_install(selected, path(args.runtime), path(args.python), path(args.work), path(args.out), path(args.archive))
        elif args.command == "apply":
            result = installer.apply_plan(path(args.plan), path(args.work), args.confirm, path(args.archive), args.fault_at, args.fault_mode)
        else:
            result = installer.recover_plan(path(args.plan), path(args.work), args.fault_at, args.fault_mode)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
        return 0
    except installer.InstallFailure as exc:
        print(json.dumps(exc.result(), ensure_ascii=False, sort_keys=True))
        return installer.EXIT[exc.code]
    except (runtime.RuntimeFailure, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "blocked", "message": str(exc)}, ensure_ascii=False, sort_keys=True))
        return installer.EXIT["blocked"]


if __name__ == "__main__":
    raise SystemExit(main())
