"""Repeatable Oracle runtime release qualification, independent of installation."""

from __future__ import annotations

import argparse
from collections import Counter
import io
import json
from pathlib import Path
import posixpath
import re
import shutil
import sys
import tarfile
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

import runtime as rt


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
RELATIONSHIP = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"


def require(condition, message):
    if not condition:
        raise rt.RuntimeFailure(message)


def relationship_target(source: str, target: str) -> str:
    return target[1:] if target.startswith("/") else posixpath.normpath(posixpath.join(posixpath.dirname(source), target))


def typed_targets(parts: dict[str, bytes], source: str, kind: str) -> list[str]:
    path = posixpath.join(posixpath.dirname(source), "_rels", posixpath.basename(source) + ".rels")
    return [relationship_target(source, rel.get("Target", "")) for rel in ET.fromstring(parts[path])
            if rel.get("Type") == RELATIONSHIP + kind]


def relationship_graph(parts: dict[str, bytes]) -> dict[str, set[str]]:
    graph = {}
    for name, data in parts.items():
        if not name.endswith(".rels"):
            continue
        source = "" if name == "_rels/.rels" else name.replace("/_rels/", "/")[:-5]
        targets = {}
        for rel in ET.fromstring(data):
            require(rel.get("TargetMode") != "External", f"external relationship: {name}")
            target = rel.get("Target", "")
            require(":" not in target and "\\" not in target, f"absolute sender relationship: {name}")
            resolved = relationship_target(source, target)
            require(resolved in parts, f"missing relationship target: {name} -> {resolved}")
            rid = rel.get("Id")
            require(rid not in targets, f"duplicate relationship id: {name}")
            targets[rid] = resolved
        graph[source] = set(targets.values())
        if source in parts and source.endswith(".xml"):
            for node in ET.fromstring(parts[source]).iter():
                for attr, value in node.attrib.items():
                    if attr.startswith("{" + NS["r"] + "}"):
                        require(value in targets, f"unbound relationship: {source} {value}")
    return graph


def inspect_pptx(path: Path, *, slides: int = 23, oracle: bool = True, chinese: bool = False) -> dict:
    with ZipFile(path) as z:
        require(z.testzip() is None, "PPTX CRC failure")
        parts = {n: z.read(n) for n in z.namelist()}
    graph = relationship_graph(parts)
    require(all(b"file://" not in data and b"/Users/" not in data for name, data in parts.items() if name.endswith((".xml", ".rels"))), "sender path leaked into PPTX")
    presentation = ET.fromstring(parts["ppt/presentation.xml"])
    presentation_rels = {r.get("Id"): r for r in ET.fromstring(parts["ppt/_rels/presentation.xml.rels"])}
    names = []
    for entry in presentation.findall("p:sldIdLst/p:sldId", NS):
        rel = presentation_rels.get(entry.get("{" + NS["r"] + "}id"))
        require(rel is not None and rel.get("Type") == RELATIONSHIP + "slide", "active slide relationship has wrong type")
        names.append(relationship_target("ppt/presentation.xml", rel.get("Target", "")))
    packaged_slides = {n for n in parts if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)}
    require(len(names) == len(set(names)) and set(names) == packaged_slides, "active slide list differs from packaged slides")
    masters = sorted(n for n in parts if re.fullmatch(r"ppt/slideMasters/slideMaster\d+\.xml", n))
    layouts = sorted(n for n in parts if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", n))
    themes = sorted(n for n in parts if re.fullmatch(r"ppt/theme/theme\d+\.xml", n))
    require(len(names) == slides, f"slide count differs: {len(names)} != {slides}")
    require(masters and layouts and themes, "native structure is missing")
    texts = []
    placeholder_count = 0
    roster = sorted((rt.PAYLOAD / "templates/layouts/oracle/templates").glob("*.svg")) if oracle else []
    aliases = {"subtitle": "subTitle", "date": "dt", "footer": "ftr", "slide-number": "sldNum", "picture": "pic", "object": "obj", "table": "tbl"}
    for number, name in enumerate(names):
        node = ET.fromstring(parts[name])
        text = "".join(n.text or "" for n in node.findall(".//a:t", NS))
        require(text, f"editable text is missing: {name}")
        texts.append(text)
        placeholder_count += len(node.findall(".//p:ph", NS))
        active_layouts = typed_targets(parts, name, "slideLayout")
        require(len(active_layouts) == 1 and active_layouts[0] in layouts, f"slide layout relationship type or target differs: {name}")
        if oracle:
            source = ET.parse(roster[number]).getroot()
            expected = Counter((aliases.get(n.get("data-pptx-placeholder"), n.get("data-pptx-placeholder")), n.get("data-pptx-idx", "0"))
                               for n in source.iter() if n.get("data-pptx-placeholder"))
            actual = Counter((n.get("type", "obj"), n.get("idx", "0")) for n in node.findall(".//p:ph", NS))
            require(actual == expected, f"slide placeholder bindings differ: {name}")
            layout = ET.fromstring(parts[active_layouts[0]])
            require(layout.find("p:cSld", NS).get("name") == source.get("data-pptx-layout-name"), f"layout roster order differs: {name}")
            bindings = Counter((n.get("type", "obj"), n.get("idx", "0")) for n in layout.findall(".//p:ph", NS))
            require(not (expected - bindings), f"layout placeholder bindings differ: {name}")
    for name in layouts:
        active_masters = typed_targets(parts, name, "slideMaster")
        require(len(active_masters) == 1 and active_masters[0] in masters, f"layout master relationship type or target differs: {name}")
    for name in masters:
        active_themes = typed_targets(parts, name, "theme")
        require(len(active_themes) == 1 and active_themes[0] in themes, f"master theme relationship type or target differs: {name}")
    assets = {}
    if oracle:
        brand = rt.PAYLOAD / "templates/brands/oracle"
        theme = (brand / "templates/brand_theme.xml").read_bytes()
        require(all(parts[n] == theme for n in themes), "full Brand theme differs")
        require(len(layouts) == 23 and len(masters) == 1, "Oracle master/layout count differs")
        manifest = rt.read_json(brand / "templates/brand_assets.json")
        media = {rt.sha256(v): n for n, v in parts.items() if n.startswith("ppt/media/")}
        referenced = set().union(*graph.values())
        for role, asset in manifest["assets"].items():
            name = media.get(asset["sha256"])
            require(name is not None and name in referenced, f"missing bound media: {role}")
            assets[role] = name
        master = ET.fromstring(parts[masters[0]])
        roles = {n.get("type") for n in master.findall(".//p:ph", NS)}
        require({"title", "body", "dt", "ftr", "sldNum"} <= roles, "master is missing one of five placeholder roles")
        title = master.find("p:txStyles/p:titleStyle/a:lvl1pPr/a:defRPr", NS)
        body = master.findall("p:txStyles/p:bodyStyle/*/a:defRPr", NS)
        require(title is not None and title.get("sz") == "2400", "master title default differs from 24pt")
        require(len(body) == 9 and all(n.get("sz") == "1600" for n in body), "master body levels differ from 16pt")
        require(any(ET.fromstring(parts[n]).find(".//p:hf", NS) is not None for n in layouts), "native header/footer capabilities missing")
        require(any(b'type="datetime1"' in parts[n] for n in layouts), "optional native date field missing")
        require(any(b'type="slidenum"' in parts[n] for n in names), "native slide-number field missing")
        for name in names + masters + layouts:
            require(b"data-pptx-local" not in parts[name], f"transient metadata survived: {name}")
            for node in ET.fromstring(parts[name]).iter():
                face = node.get("typeface")
                if face and chinese:
                    require(face.startswith(("+mj-", "+mn-")), f"text face bypasses Brand theme: {name} {face}")
        if chinese:
            require(any("运行时验证" in t for t in texts), "formal editable Chinese content missing")
            defaults = master.findall("p:txStyles//a:defRPr", NS)
            require(defaults and all(n.get("lang") == "zh-CN" for n in defaults), "Chinese master language defaults differ")
            require(any(b'lang="zh-CN"' in parts[n] for n in names), "Chinese run language missing")
        theme_xml = ET.fromstring(theme)
        faces = sorted({n.get("typeface") for n in theme_xml.iter() if n.get("typeface")})
    else:
        faces = []
    charts = sorted(n for n in parts if re.fullmatch(r"ppt/charts/chart\d+\.xml", n))
    chart_faces = sorted({node.get("typeface") for name in charts
                          for node in ET.fromstring(parts[name]).iter() if node.get("typeface")})
    part_faces = {name: sorted({node.get("typeface") for node in ET.fromstring(data).iter() if node.get("typeface")})
                  for name, data in parts.items() if name.endswith(".xml")}
    part_faces = {name: faces for name, faces in part_faces.items() if faces}
    text_faces = sorted({node.get("typeface") for name in names + masters + layouts
                         for node in ET.fromstring(parts[name]).iter() if node.get("typeface")})
    return {"sha256": rt.sha256(path.read_bytes()), "slides": len(names), "masters": len(masters),
            "layouts": len(layouts), "themes": len(themes), "slide_placeholders": placeholder_count,
            "asset_media": assets, "font_declarations": faces, "text_font_references": text_faces,
            "chart_font_references": chart_faces,
            "font_references_by_part": part_faces,
            "native_tables": sum(parts[n].count(b"<a:tbl>") for n in names),
            "chart_parts": len(charts)}


def check_bindings(project: Path) -> dict:
    data = rt.read_json(project / "templates/brand_assets.json")
    seen = set()
    for svg in (project / "templates").glob("*.svg"):
        for node in ET.parse(svg).getroot().iter():
            role = node.get("data-pptx-brand-asset")
            if role:
                href = node.get("href") or node.get("{http://www.w3.org/1999/xlink}href")
                require(href and not Path(href).is_absolute() and ":" not in href, f"nonportable asset: {role}")
                asset = (svg.parent / href).resolve()
                require(asset.is_relative_to(project.resolve()), f"escaping bound asset: {role}")
                require(rt.sha256(asset.read_bytes()) == data["assets"][role]["sha256"], f"bound asset hash mismatch: {role}")
                seen.add(role)
    require(seen == set(data["assets"]), "not every Brand asset role was applied")
    return {role: data["assets"][role]["sha256"] for role in sorted(seen)}


def formal_pages(project: Path) -> None:
    target = project / "svg_output"
    target.mkdir()
    for number, svg in enumerate(sorted((project / "templates").glob("*.svg")), 1):
        text = svg.read_text().replace('font-family="Arial"', 'font-family="Arial" lang="zh-CN"', 1)
        def content(match):
            token = match[1]
            if token.endswith("_NUM"):
                return str(number)
            if token == "DATE":
                return "2026-11-11"
            return "运行时验证" if "TITLE" in token else "可编辑内容"
        text = re.sub(r"\{\{([A-Z][A-Z0-9_]*)\}\}", content, text)
        (target / svg.name).write_text(text)


def export_formal(runtime: Path, python: Path, project: Path, output: Path, logs: Path) -> None:
    rt.run([str(python), "-B", str(runtime / "scripts/svg_quality_checker.py"), str(project), "--quick-generate", "--json"], work=logs, name="formal-check")
    rt.run([str(python), "-B", str(runtime / "scripts/svg_to_pptx.py"), str(project), "--quick-generate",
            "--primary-language", "zh-CN", "--native-charts-and-tables", "--no-image-optimize", "-o", str(output)], work=logs, name="formal-export")


def generic_contracts(runtime: Path, work: Path) -> dict:
    sys.path.insert(0, str(runtime / "scripts"))
    from pptx import Presentation
    from svg_to_pptx.drawingml.theme_fonts import MasterTextStyleSpec
    from svg_to_pptx.pptx_package.builder import create_pptx_with_native_svg
    from svg_to_pptx.drawingml.text_properties import project_text_property_diagnostics
    reset = ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg"><text font-size="24" data-pptx-native-defaults="true" baseline-shift="baseline">Reset</text></svg>')
    require(not [d for d in project_text_property_diagnostics(reset) if d.severity == "error"], "native baseline reset is rejected")
    source = work / "generic"
    (source / "templates").mkdir(parents=True)
    svg = source / "templates/page.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" font-family="Arial" data-pptx-master="plain" data-pptx-master-name="Plain" data-pptx-layout="plain" data-pptx-layout-name="Plain"><g id="title" data-pptx-placeholder="title" data-pptx-idx="0" data-pptx-bounds="80 100 1000 100"><text data-pptx-carrier="true" x="80" y="160" font-size="32">Ordinary editable title</text></g></svg>')
    out = source / "ordinary.pptx"
    require(create_pptx_with_native_svg([svg], out, resource_root=source, master_text_style_spec=MasterTextStyleSpec(2400, 1600), verbose=False), "ordinary authored export failed")
    ordinary = inspect_pptx(out, slides=1, oracle=False)
    seed = source / "source.pptx"
    Presentation().save(seed)
    with ZipFile(seed) as z:
        original_theme = z.read("ppt/theme/theme1.xml")
    mirror = source / "mirror.pptx"
    require(create_pptx_with_native_svg([svg], mirror, resource_root=source,
            master_text_style_spec=MasterTextStyleSpec(2400, 1600), source_theme_xml_by_master={"plain": original_theme}, verbose=False), "source-theme mirror export failed")
    mirrored = inspect_pptx(mirror, slides=1, oracle=False)
    with ZipFile(mirror) as z:
        require(z.read("ppt/theme/theme1.xml") == original_theme, "source theme was altered")
    profile = source / "templates/master_defaults.json"
    profile.write_text('{"schema":"ppt-master.master-defaults.v1"}')
    rejected = {}
    expect_failure("oracle_in_mirror", lambda: create_pptx_with_native_svg([svg], source / "invalid.pptx", resource_root=source,
        master_text_style_spec=MasterTextStyleSpec(2400, 1600), source_theme_xml_by_master={"plain": original_theme}, verbose=False), "requires authored structured export", rejected)
    profile.unlink()
    return {"authored": ordinary, "source_theme_mirror": mirrored, "native_baseline_reset": "passed", "unsupported_mode": rejected}


def probe(runtime: Path, work: Path) -> dict:
    require(not work.exists(), f"probe workspace already exists: {work}")
    work.mkdir(parents=True)
    python = Path(sys.executable)
    logs = work / "logs"
    for script in ("apply_template.py", "template_preview_pptx.py", "svg_to_pptx.py"):
        rt.run([str(python), "-B", str(runtime / "scripts" / script), "--help"], work=logs, name=script + "-help")
    project = work / "project"
    project.mkdir()
    rt.run([str(python), "-B", str(runtime / "scripts/apply_template.py"), str(project),
            "--root", str(runtime / "templates/brands/oracle"), "--root", str(runtime / "templates/layouts/oracle")], work=logs, name="apply")
    before = check_bindings(project)
    moved = work / "moved-project"
    project.rename(moved)
    require(check_bindings(moved) == before, "assets changed after workspace relocation")
    preview = work / "preview.pptx"
    rt.run([str(python), "-B", str(runtime / "scripts/template_preview_pptx.py"), str(moved), "-o", str(preview)], work=logs, name="preview")
    preview_result = inspect_pptx(preview)
    formal_pages(moved)
    formal = work / "formal.pptx"
    export_formal(runtime, python, moved, formal, logs)
    formal_result = inspect_pptx(formal, chinese=True)
    require(formal_result["native_tables"] >= 1 and formal_result["chart_parts"] >= 1, "formal native table/chart missing")
    return {"status": "passed", "contract": "oracle-native-v1", "python": str(python), "runtime": str(runtime),
            "binding_roles": before, "relocation": "passed", "preview": preview_result, "formal": formal_result,
            "generic": generic_contracts(runtime, work),
            "visual_acceptance": "Not claimed. Fonts are not bundled; no native PowerPoint visual acceptance."}


def expect_failure(name: str, fn, expected: str, results: dict) -> None:
    try:
        fn()
    except Exception as exc:
        require(expected.lower() in str(exc).lower(), f"{name} failed for an unexpected reason: {exc}")
        results[name] = {"status": "expected_failure", "reason": str(exc)[-4000:]}
    else:
        raise rt.RuntimeFailure(f"{name} mutation was not detected")


def mutate_zip(source: Path, target: Path, edit) -> None:
    with ZipFile(source) as z:
        parts = {n: z.read(n) for n in z.namelist()}
    edit(parts)
    with ZipFile(target, "w", ZIP_DEFLATED) as z:
        for name, value in parts.items():
            z.writestr(name, value)


def mutations(runtime: Path, python: Path, probe_work: Path, work: Path) -> dict:
    work.mkdir()
    results = {}
    bad_layout = work / "bad-layout"
    shutil.copytree(rt.PAYLOAD / "templates/layouts/oracle", bad_layout)
    profile = bad_layout / "templates/master_defaults.json"
    data = rt.read_json(profile)
    data["schema"] = "deliberately-invalid"
    profile.write_text(json.dumps(data))
    expect_failure("invalid_defaults_schema", lambda: rt.run([str(python), "-B", str(runtime / "scripts/svg_quality_checker.py"),
        str(bad_layout / "templates"), "--template-mode"], work=work / "profile-logs", name="invalid-profile"), "unknown schema", results)
    source = probe_work / "formal.pptx"
    broken = work / "broken-master.pptx"
    def break_master(parts):
        name = next(n for n in parts if re.fullmatch(r"ppt/slideLayouts/_rels/slideLayout\d+\.xml\.rels", n))
        tree = ET.fromstring(parts[name])
        rel = next(n for n in tree if n.get("Type", "").endswith("/slideMaster"))
        rel.set("Target", "../slideMasters/absent.xml")
        parts[name] = ET.tostring(tree)
    mutate_zip(source, broken, break_master)
    expect_failure("master_relationship", lambda: inspect_pptx(broken, chinese=True), "missing relationship target", results)
    for edge, folder, message in (("slideMaster", "slideLayouts", "layout master relationship type"), ("theme", "slideMasters", "master theme relationship type")):
        invalid = work / ("invalid-" + edge + "-type.pptx")
        def replace_type(parts):
            for name in parts:
                if name.startswith("ppt/" + folder + "/_rels/"):
                    tree = ET.fromstring(parts[name])
                    for relation in tree:
                        if relation.get("Type") == RELATIONSHIP + edge:
                            relation.set("Type", RELATIONSHIP + "image")
                    parts[name] = ET.tostring(tree)
        mutate_zip(source, invalid, replace_type)
        expect_failure(edge + "_relationship_type", lambda: inspect_pptx(invalid, chinese=True), message, results)
    broken_size = work / "broken-size.pptx"
    def break_size(parts):
        name = "ppt/slideMasters/slideMaster1.xml"
        tree = ET.fromstring(parts[name])
        tree.find("p:txStyles/p:titleStyle/a:lvl1pPr/a:defRPr", NS).set("sz", "9999")
        parts[name] = ET.tostring(tree)
    mutate_zip(source, broken_size, break_size)
    expect_failure("master_font_size", lambda: inspect_pptx(broken_size, chinese=True), "title default differs", results)
    empty = work / "empty-active-slides.pptx"
    def remove_active_slides(parts):
        tree = ET.fromstring(parts["ppt/presentation.xml"])
        tree.find("p:sldIdLst", NS).clear()
        parts["ppt/presentation.xml"] = ET.tostring(tree)
    mutate_zip(source, empty, remove_active_slides)
    expect_failure("empty_active_slides", lambda: inspect_pptx(empty, chinese=True), "active slide list", results)
    missing = work / "missing-placeholders.pptx"
    def remove_placeholders(parts):
        for name in list(parts):
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name):
                tree = ET.fromstring(parts[name])
                for parent in tree.iter():
                    for child in list(parent):
                        if child.tag == "{" + NS["p"] + "}ph":
                            parent.remove(child)
                parts[name] = ET.tostring(tree)
    mutate_zip(source, missing, remove_placeholders)
    expect_failure("missing_slide_placeholders", lambda: inspect_pptx(missing, chinese=True), "placeholder bindings differ", results)
    bad_brand = work / "bad-brand"
    shutil.copytree(rt.PAYLOAD / "templates/brands/oracle", bad_brand)
    manifest = bad_brand / "templates/brand_assets.json"
    data = rt.read_json(manifest)
    data["assets"]["corner-mark"]["sha256"] = "0" * 64
    manifest.write_text(json.dumps(data))
    project = work / "bad-project"
    project.mkdir()
    expect_failure("asset_hash", lambda: rt.run([str(python), "-B", str(runtime / "scripts/apply_template.py"), str(project),
        "--root", str(bad_brand), "--root", str(rt.PAYLOAD / "templates/layouts/oracle")], work=work / "asset-logs", name="asset-hash"), "hash", results)
    require(not list(project.iterdir()), "bad assets wrote project files")
    changed = work / "mutated-runtime"
    shutil.copytree(runtime, changed)
    language = changed / "scripts/svg_to_pptx/pptx_package/template_language.py"
    language.unlink()
    expect_failure("missing_template_language", lambda: rt.run([str(python), "-B", str(changed / "scripts/template_preview_pptx.py"), "--help"],
        work=work / "language-logs", name="missing-language"), "template_language", results)
    shutil.copyfile(runtime / language.relative_to(changed), language)
    builder = changed / "scripts/svg_to_pptx/pptx_package/builder.py"
    text = builder.read_text()
    require(text.count("apply_brand_theme(extract_dir, brand_theme)") == 1, "theme mutation target drifted")
    builder.write_text(text.replace("apply_brand_theme(extract_dir, brand_theme)", "pass  # qualification mutation"))
    no_theme = work / "no-theme.pptx"
    export_formal(changed, python, probe_work / "moved-project", no_theme, work / "theme-logs")
    expect_failure("theme_disabled", lambda: inspect_pptx(no_theme, chinese=True), "full Brand theme differs", results)
    return results


def qualify(work: Path, archive: Path | None) -> dict:
    require(not work.exists(), f"qualification workspace already exists: {work}")
    work.mkdir(parents=True)
    runtime = work / "runtime"
    binding = rt.build_runtime(runtime, work / "environment", work / "build", archive=archive)
    python = Path(binding.python)
    view = work / "view"
    sentinel = {"retained": {"summary": "unchanged", "nested": [1, False, None], "custom": "value"}}
    original = {k: (json.dumps(sentinel) + "\n").encode() for k in rt.KINDS}
    indices = rt.prepare_registration_view(runtime, python, view, work / "registration", indices=original)
    report = work / "probe.json"
    rt.run([str(python), "-B", str(Path(__file__).resolve()), "probe", "--runtime", str(view), "--work", str(work / "probe"), "--report", str(report)], work=work / "driver", name="probe")
    results = rt.read_json(report)
    results["release_sha256"] = rt.release_digest()
    results["registered_indices"] = {k: rt.index_value(v) for k, v in indices.items()}
    results["mutations"] = mutations(view, python, work / "probe", work / "mutations")
    generic = work / "official-template.pptx"
    rt.run([str(python), "-B", str(runtime / "scripts/template_preview_pptx.py"), str(runtime / "templates/layouts/report_core"), "-o", str(generic)], work=work / "generic-logs", name="official-generic")
    results["official_report_core"] = inspect_pptx(generic, slides=13, oracle=False)
    results["boundaries"] = boundary_checks(runtime, python, archive or work / "build/upstream.tar.gz", work / "boundaries")
    results["classifications"] = classification_checks(runtime, python, work / "classifications")
    return results


def boundary_checks(runtime: Path, python: Path, archive: Path, work: Path) -> dict:
    work.mkdir()
    results = {}
    lock = rt.load_release()
    source = work / "preimage"
    rt.extract_source(archive, source, lock)
    path = source / "scripts/apply_template.py"
    path.write_bytes(path.read_bytes() + b"\n")
    before = {p.relative_to(source).as_posix(): rt.sha256(p.read_bytes()) for p in source.rglob("*") if p.is_file()}
    expect_failure("patch_preimage", lambda: rt.apply_patches(source, lock, work / "patch-logs"), "patch preimage mismatch", results)
    require(before == {p.relative_to(source).as_posix(): rt.sha256(p.read_bytes()) for p in source.rglob("*") if p.is_file()}, "wrong preimage caused source writes")
    expect_failure("missing_dependencies", lambda: rt.run([str(python), "-S", "-B", str(runtime / "scripts/template_preview_pptx.py"), "--help"], work=work / "dependency-logs", name="missing-dependencies"), "No module named 'pptx'", results)
    for kind in ("traversal", "symlink"):
        bad_archive = work / (kind + ".tar.gz")
        with tarfile.open(bad_archive, "w:gz") as tf:
            info = tarfile.TarInfo("../escape" if kind == "traversal" else "link")
            if kind == "symlink":
                info.type, info.linkname = tarfile.SYMTYPE, "/outside"
            else:
                info.size = 1
            tf.addfile(info, io.BytesIO(b"x") if kind == "traversal" else None)
        altered = dict(lock, upstream=dict(lock["upstream"], archive_sha256=rt.sha256(bad_archive.read_bytes())))
        target = work / (kind + "-output")
        expect_failure(kind, lambda: rt.extract_source(bad_archive, target, altered), "unsafe relative path" if kind == "traversal" else "archive link or special member", results)
        require(not target.exists(), "invalid archive created a runtime")
    return results


def classification_checks(runtime: Path, python: Path, work: Path) -> dict:
    work.mkdir()
    results = {}
    def check(label, candidate, expected, interpreter):
        before = {p.relative_to(candidate).as_posix(): (rt.sha256(p.read_bytes()), p.stat().st_mtime_ns)
                  for p in candidate.rglob("*") if p.is_file()} if candidate.is_dir() else {}
        result = rt.assess_runtime(candidate, python=interpreter, work=work / label)
        require(result.action == expected, f"{label}: {result.action}: {result.reason}")
        after = {p.relative_to(candidate).as_posix(): (rt.sha256(p.read_bytes()), p.stat().st_mtime_ns)
                 for p in candidate.rglob("*") if p.is_file()} if candidate.is_dir() else {}
        require(before == after, f"{label} modified runtime bytes or mtimes")
        results[label] = {"action": result.action, "reason": result.reason, "controlled_files": len(result.fingerprint)}
    check("absent", work / "absent-runtime", "install", None)
    check("managed", runtime, "reuse", None)
    unknown = work / "unknown-runtime"
    shutil.copytree(runtime, unknown)
    (unknown / rt.BINDING).unlink()
    source = unknown / "scripts/apply_template.py"
    source.write_text(source.read_text() + "\n# Isolated unknown-fingerprint qualification fixture.\n")
    rt.run([str(python), "-B", "-c", "import py_compile,sys; py_compile.compile(sys.argv[1], doraise=True)", str(source)],
           work=work / "cache-logs", name="compile-cache")
    (unknown / ".env").write_text("NON_SECRET_SENTINEL=excluded\n")
    check("unknown", unknown, "reuse", python)
    cache = next((unknown / "scripts/__pycache__").glob("apply_template.*.pyc"))
    copied_cache = work / "unknown/registration-view" / cache.relative_to(unknown)
    require(cache.read_bytes() == copied_cache.read_bytes() and cache.stat().st_mtime_ns == copied_cache.stat().st_mtime_ns,
            "view changed cached import bytes or timestamp")
    require(not (work / "unknown/registration-view/.env").exists(), "view copied an unallowlisted file")
    shadow = unknown / "scripts/brand_assets/__init__.py"
    shadow.parent.mkdir()
    shadow.write_text("raise RuntimeError('unexpected shadow package')\n")
    check("shadow_package", unknown, "blocked", python)
    shutil.rmtree(shadow.parent)
    registrar = unknown / "scripts/register_template.py"
    original_registrar = registrar.read_text()
    registrar.write_text(original_registrar.replace('index[tid] = payload["entry"]', 'index[tid] = None'))
    expect_failure("invalid_registry", lambda: rt.prepare_registration_view(unknown, python, work / "bad-registry-view", work / "bad-registry-logs"),
                   "invalid Oracle registry entry", results)
    registrar.write_text(original_registrar)
    (unknown / "scripts/svg_to_pptx/pptx_package/template_language.py").unlink()
    check("incompatible", unknown, "blocked", python)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("probe", "qualify"))
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = probe(args.runtime.resolve(), args.work.resolve()) if args.action == "probe" else qualify(args.work.resolve(), args.archive.resolve() if args.archive else None)
    except Exception as exc:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({"status": "failed", "error": str(exc)}, indent=2) + "\n")
        raise
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"status": result["status"], "report": str(args.report)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
