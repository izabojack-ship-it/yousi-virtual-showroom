"""STEP / IGES → GLB / OBJ 轉換（移植 PAS StepConverterService 邏輯）"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

CACHE_VERSION = "v1"
MAX_OUTPUT_MB = 40
CAD_EXT = {".step", ".stp", ".iges", ".igs"}


@dataclass
class ConvertResult:
    success: bool = False
    data: bytes = b""
    output_format: str = ""
    output_name: str = ""
    error: str = ""
    install_hint: str = ""


def _cache_dir() -> Path:
    d = Path(settings.MEDIA_ROOT) / "products" / "cad_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _temp_dir() -> Path:
    d = Path(tempfile.gettempdir()) / "yousi_3dconvert"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def detect_tool() -> tuple[str, str] | None:
    freecad_paths = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/FreeCAD 1.1/bin/freecadcmd.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/FreeCAD/bin/freecadcmd.exe",
        Path(r"C:\Program Files\FreeCAD 1.1\bin\FreeCADCmd.exe"),
        Path(r"C:\Program Files\FreeCAD\bin\FreeCADCmd.exe"),
        Path(r"C:\Program Files (x86)\FreeCAD\bin\FreeCADCmd.exe"),
    ]
    for p in freecad_paths:
        if p.is_file():
            return "freecad", str(p)

    occ = shutil.which("opencascade-tools") or shutil.which("opencascade-tools.cmd")
    if occ:
        return "opencascade", occ

    npm_occ = Path(os.environ.get("APPDATA", "")) / "npm/opencascade-tools.cmd"
    if npm_occ.is_file():
        return "opencascade", str(npm_occ)

    return None


def is_converter_available() -> bool:
    return detect_tool() is not None


def convert_step_file(path: Path, quality: str = "low") -> ConvertResult:
    """將 STEP/IGES 檔轉為 GLB 或 OBJ（含快取）"""
    result = ConvertResult()
    ext = path.suffix.lower()
    if ext not in CAD_EXT:
        result.error = f"不支援的格式：{ext}"
        return result

    tool_info = detect_tool()
    if not tool_info:
        result.error = "伺服器未安裝轉換工具。請執行：npm install -g opencascade-tools"
        result.install_hint = "npm install -g opencascade-tools"
        return result

    tool, exe = tool_info
    file_hash = _file_hash(path)
    cache_ext = ".obj" if tool == "freecad" else ".glb"
    cache_name = f"{CACHE_VERSION}_{file_hash}_{quality}{cache_ext}"
    cache_path = _cache_dir() / cache_name

    if cache_path.is_file():
        result.data = cache_path.read_bytes()
        result.output_format = cache_ext.lstrip(".")
        result.output_name = path.stem + cache_ext
        result.success = True
        return result

    work = _temp_dir()
    uid = uuid.uuid4().hex[:12]
    input_path = work / f"{uid}{ext}"
    output_path = work / f"{uid}.glb"

    try:
        shutil.copy2(path, input_path)
        ok = False
        actual_output = output_path

        if tool == "freecad":
            actual_output = output_path.with_suffix(".obj")
            ok = _run_freecad(exe, input_path, actual_output, quality)
        else:
            ok = _run_opencascade(exe, input_path, output_path, quality)
            actual_output = output_path

        if not ok or not actual_output.is_file():
            result.error = f"轉換失敗（工具={tool}），請確認 STEP 檔案是否有效"
            return result

        size_mb = actual_output.stat().st_size / (1024 * 1024)
        if size_mb > MAX_OUTPUT_MB:
            result.error = f"轉換後檔案過大（{size_mb:.1f} MB），請使用「快速」品質"
            return result

        result.data = actual_output.read_bytes()
        result.output_format = actual_output.suffix.lstrip(".").lower()
        result.output_name = path.stem + actual_output.suffix.lower()
        result.success = True

        try:
            cache_path.write_bytes(result.data)
        except OSError:
            pass
    finally:
        for p in (input_path, output_path, output_path.with_suffix(".obj"), input_path.with_suffix(".py")):
            try:
                if p.is_file():
                    p.unlink()
            except OSError:
                pass

    return result


def _run_process(exe: str, args: str, timeout: int, cwd: str | None = None) -> bool:
    try:
        proc = subprocess.run(
            f'"{exe}" {args}',
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except OSError:
        return False


def _run_opencascade(exe: str, input_path: Path, output_path: Path, quality: str) -> bool:
    lin = "0.1" if quality == "high" else "1.0" if quality == "medium" else "5.0"
    ang = "0.2" if quality == "high" else "1.0" if quality == "medium" else "2.0"
    args = f'"{input_path.name}" -f glb -l {lin} -a {ang}'
    ok = _run_process(exe, args, timeout=600, cwd=str(input_path.parent))
    if not ok:
        return False
    expected = input_path.with_suffix(".glb")
    if expected.is_file() and expected != output_path:
        shutil.move(str(expected), str(output_path))
    return output_path.is_file()


def _run_freecad(exe: str, input_path: Path, output_path: Path, quality: str) -> bool:
    max_facets = 500_000 if quality == "high" else 400_000 if quality == "medium" else 150_000
    lin_def = "0.1" if quality == "high" else "1.0" if quality == "medium" else "5.0"
    ang_def = "0.15" if quality == "high" else "0.8" if quality == "medium" else "1.5"

    input_esc = str(input_path).replace("\\", "/")
    output_esc = str(output_path).replace("\\", "/")
    script = f'''
import sys, os, re
import FreeCAD
import Part
import MeshPart

MAX_FACETS_TOTAL = {max_facets}

def sanitize(name):
    if not name:
        return 'Part'
    s = re.sub(r'[^0-9A-Za-z._\\-\\u4e00-\\u9fff]+', '_', name).strip('_')
    return (s or 'Part')[:64]

doc = FreeCAD.newDocument('convert')
Part.insert(r'{input_esc}', 'convert')
raw = []
for o in doc.Objects:
    shp = getattr(o, 'Shape', None)
    if shp is None or shp.isNull():
        continue
    lbl = sanitize(o.Label or o.Name or 'Part')
    solids = list(getattr(shp, 'Solids', []) or [])
    if len(solids) > 1:
        for i, s in enumerate(solids):
            raw.append((lbl + '_' + str(i + 1), s))
    elif len(solids) == 1:
        raw.append((lbl, solids[0]))
    else:
        raw.append((lbl, shp))

pairs = []
total = 0
used = {{}}
for lbl, shape in raw:
    name = lbl
    if name in used:
        used[name] += 1
        name = lbl + '_' + str(used[name])
    else:
        used[name] = 1
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection={lin_def}, AngularDeflection={ang_def}, Relative=False)
    if m.CountFacets == 0:
        continue
    pairs.append((name, m))
    total += m.CountFacets

if total > MAX_FACETS_TOTAL:
    ratio = max(0.25, MAX_FACETS_TOTAL / float(total))
    for name, m in pairs:
        if m.CountFacets > 1000:
            m.decimate(ratio)

out_path = r'{output_esc}'
with open(out_path, 'w', encoding='utf-8', newline='\\n') as f:
    f.write('# multi-part OBJ from STEP\\n')
    offset = 0
    for name, m in pairs:
        f.write('o ' + name + '\\n')
        for pt in m.Points:
            f.write('v %.4f %.4f %.4f\\n' % (pt.x, pt.y, pt.z))
        for facet in m.Facets:
            idx = facet.PointIndices
            f.write('f %d %d %d\\n' % (idx[0]+1+offset, idx[1]+1+offset, idx[2]+1+offset))
        offset += len(m.Points)
'''
    script_path = input_path.with_suffix(".py")
    script_path.write_text(script, encoding="utf-8")
    ok = _run_process(exe, f'"{script_path}"', timeout=600)
    try:
        script_path.unlink(missing_ok=True)
    except OSError:
        pass
    return ok and output_path.is_file()
