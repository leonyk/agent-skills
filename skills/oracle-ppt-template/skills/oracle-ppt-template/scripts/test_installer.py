"""Focused filesystem and input-boundary checks; verify.py owns real CLI acceptance."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

import installer as ins


TEST_ROOT: Path | None = None


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=TEST_ROOT)
        self.root = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def test_duplicate_nested_keys_and_nonfinite_numbers_fail(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":{"b":1,"b":2}}', b'{"a":NaN}', b'[]x'):
            with self.subTest(raw=raw), self.assertRaises(ins.InstallFailure):
                ins.json_value(raw)

    def test_json_value_comparison_preserves_types(self):
        self.assertFalse(ins.same_json({"x": True}, {"x": 1}))
        self.assertFalse(ins.same_json({"x": 1.0}, {"x": 1}))
        self.assertTrue(ins.same_json({"b": None, "a": [False]}, {"a": [False], "b": None}))

    def test_seal_cannot_be_repaired_by_recomputing_a_digest(self):
        key = ins.work_key(self.root / "work", create=True)
        envelope = ins.seal({"runtime": "authorized"}, key, "plan")
        envelope["value"]["runtime"] = "elsewhere"
        envelope["digest"] = ins.digest(envelope["value"])
        with self.assertRaises(ins.InstallFailure) as context:
            ins.unseal(ins.canonical_json(envelope), key, "plan")
        self.assertEqual(context.exception.code, "invalid_plan")

    def test_snapshot_distinguishes_identity_mtime_and_unknown_files(self):
        target = self.root / "tree"
        target.mkdir()
        file = target / "same.txt"
        file.write_text("same bytes")
        before = ins.snapshot(target)
        st = file.stat()
        os.utime(file, ns=(st.st_atime_ns, st.st_mtime_ns + 1))
        self.assertNotEqual(before, ins.snapshot(target))
        self.assertEqual(ins.content(before), ins.content(ins.snapshot(target)))
        os.utime(file, ns=(st.st_atime_ns, st.st_mtime_ns))
        replacement = self.root / "replacement"
        shutil.copy2(file, replacement)
        os.replace(replacement, file)
        self.assertNotEqual(before, ins.snapshot(target))
        (target / "unknown").mkdir()
        self.assertNotEqual(ins.content(before), ins.content(ins.snapshot(target)))

    def test_target_and_ancestor_symlinks_fail(self):
        real = self.root / "real"
        real.mkdir()
        link = self.root / "link"
        link.symlink_to(real, target_is_directory=True)
        for target in (link, link / "missing"):
            with self.subTest(target=target), self.assertRaises(ins.InstallFailure):
                ins.safe_path(target)

    def test_client_aliases_merge_but_cannot_escape_scope(self):
        home, project = self.root / "home", self.root / "project"
        home.mkdir()
        project.mkdir()
        target = home / ".agents/skills/ppt-master"
        target.mkdir(parents=True)
        for client in (".codex", ".cursor"):
            alias = home / client / "skills/ppt-master"
            alias.parent.mkdir(parents=True)
            alias.symlink_to(target, target_is_directory=True)
        chosen = ins.selection("global", "global", str(project), str(home))
        candidates, _ = ins.discover(chosen)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(len(candidates[0].display_paths), 3)
        alias = project / ".agents/skills/ppt-master"
        alias.parent.mkdir(parents=True)
        alias.symlink_to(target, target_is_directory=True)
        with self.assertRaises(ins.InstallFailure):
            ins.choose_runtime(ins.selection("project", "project", str(project), str(home)), None)

    def test_project_discovery_ignores_invalid_global_runtime(self):
        home, project = self.root / "home", self.root / "project"
        home.mkdir()
        project.mkdir()
        target = home / ".agents/skills/ppt-master"
        target.parent.mkdir(parents=True)
        target.write_text("not a runtime")
        chosen = ins.selection("project", "project", str(project), str(home))
        actual, _, candidates = ins.choose_runtime(chosen, None)
        self.assertEqual(actual, project / ".agents/skills/ppt-master")
        self.assertEqual(candidates, [])

    def test_safe_client_aliases_keep_the_existing_actual_location(self):
        home = self.root / "home"
        home.mkdir()
        target = home / "local-runtime"
        target.mkdir()
        for client in (".codex", ".cursor"):
            alias = home / client / "skills/ppt-master"
            alias.parent.mkdir(parents=True)
            alias.symlink_to(target, target_is_directory=True)
        chosen = ins.selection("global", "global", None, str(home))
        actual, _, candidates = ins.choose_runtime(chosen, None)
        self.assertEqual(actual, target)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(len(candidates[0].display_paths), 2)

    def test_scope_mismatch_does_not_create_paths(self):
        with self.assertRaises(ins.InstallFailure):
            ins.selection("global", "project", str(self.root / "missing"), str(self.root / "absent"))
        self.assertEqual(list(self.root.iterdir()), [])

    def test_atomic_directory_exchange_retains_exact_objects(self):
        a, b = self.root / "a", self.root / "b"
        for path, value in ((a, "old"), (b, "new")):
            path.mkdir()
            (path / "file").write_text(value)
        old, new = ins.snapshot(a), ins.snapshot(b)
        ins.exchange(a, b)
        self.assertEqual(ins.snapshot(a), new)
        self.assertEqual(ins.snapshot(b), old)
        ins.exchange(a, b)
        self.assertEqual(ins.snapshot(a), old)
        self.assertEqual(ins.snapshot(b), new)

    def test_atomic_file_exchange_retains_mtime_and_inode(self):
        a, b = self.root / "a", self.root / "b"
        a.write_text("old")
        b.write_text("new")
        old, new = ins.snapshot(a), ins.snapshot(b)
        ins.exchange(a, b)
        self.assertEqual(ins.snapshot(a), new)
        self.assertEqual(ins.snapshot(b), old)

    def test_new_publication_cannot_replace_an_unexpected_destination(self):
        staged, destination = self.root / "stage", self.root / "destination"
        staged.mkdir()
        destination.mkdir()
        (staged / "ours").write_text("ready")
        (destination / "theirs").write_text("preserve")
        before = ins.snapshot(staged), ins.snapshot(destination)
        with self.assertRaises(FileExistsError):
            ins.atomic_rename(staged, destination, replace=False)
        self.assertEqual(before, (ins.snapshot(staged), ins.snapshot(destination)))


def main():
    global TEST_ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    args = parser.parse_args()
    TEST_ROOT = args.work.absolute()
    ins.safe_path(TEST_ROOT, directory=True)
    TEST_ROOT.mkdir(parents=True, exist_ok=True)
    unittest.main(argv=[__file__])


if __name__ == "__main__":
    main()
