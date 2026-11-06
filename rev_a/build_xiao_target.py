"""Build the XIAO camera target as native, parametric Inventor parts and assemblies.

    python build_xiao_target.py                    # 5 parts, assembly in the cube + standalone on the riser, interference
    python build_xiao_target.py --set screen_d=22  # any parameter of xiao_target.py
    python build_xiao_target.py --only body cover

Writes into INVENTOR/ (provisional numbers, see xiao_target.NAMES): the five printed parts (.ipt, .stp, .stl),
"ASS - 9020 - CAMTARXIA - V04.iam" (target hanging in an ASS-2000 cube, with the XIAO, tube, screen
and magnets), "... - standalone.iam" (on the 5 mm riser, no cube), STEP copies and "<assembly> - build.json".
Every dimension is an Inventor user parameter (fx). Needs the miniforge `pyinventor` env and a running
Inventor; the session helper restores SilentOperation and closes only the documents this script opened.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE.parent))           # cadlib
from cadlib.inventor_helpers import Builder, close_if_open, kAssemblyDocumentObject, safe, session  # noqa: E402
from cadlib.native_part import NativePart, export_step, kCut, kJoin, read_user_parameters  # noqa: E402
from cadlib.params import ParamSet  # noqa: E402
from xiao_target import INV_DIR, NAMES, PARTS, checks, make_params, overrides_from, report  # noqa: E402

PRINT = ("Smooth - White", "Satin - White", "White")
DARK = ("Satin - Black", "Smooth - Black", "Black")
I3 = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
MAG_Y = ((1, 0, 0), (0, 0, -1), (0, 1, 0))          # magnet axis (part z) along cube y
XIAO_COLS = ((0, 0, 1), (0, 1, 0), (-1, 0, 0))      # vendor bx -> z, by -> y, bz -> -x


def _part(app, ps, path, description, body_fn, look=PRINT) -> dict:
    part = NativePart(app, ps, description)
    try:
        body_fn(part)
        part.set_appearance(look)
        part.save(path, stl=True)
        return part.report()
    finally:
        part.close()


# ---------------------------------------------------------------------- holder body
def body_features(part: NativePart) -> None:
    s = part.sketch_z("-cube_half", "plate sketch")
    part.rect(s, "-body_half", "body_y0", "body_half", "front_y", "plate", wu="2 * body_half", sym_u=True,
              pin_v0="body_y0", pin_v1="front_y")
    part.extrude_toward(s, "2 * cube_half", kJoin, "hanging plate", "z", True)
    s = part.sketch_z("cube_half", "cap sketch")
    part.rect(s, "-cap_half_x", "-cap_half_y", "cap_half_x", "cap_half_y", "cap", wu="2 * cap_half_x", sym_u=True,
              wv="2 * cap_half_y", sym_v=True)
    part.extrude_toward(s, "cap_t", kJoin, "cap (rests on the cube top)", "z", True)
    s = part.sketch_x("-body_half", "foot sketch")
    part.polygon(s, [("body_y0", "pocket_z0"), ("front_y", "pocket_z0"), ("flare_front", "-cube_half"),
                     ("-flare_back", "-cube_half"), ("body_y0", "flare_back_z")], "foot")
    part.extrude_toward(s, "2 * body_half", kJoin, "foot (45 deg slopes)", "x", True)
    s = part.sketch_y("body_y0 - 1 mm", "board pocket sketch")
    part.rect(s, "pocket_x0", "pocket_z0", "pocket_x1", "pocket_z1", "board pocket",
              pin_u0="pocket_x0", pin_u1="pocket_x1", pin_v0="pocket_z0", pin_v1="pocket_z1")
    part.extrude_toward(s, "wall_in_y - body_y0 + 1 mm", kCut, "board pocket (open at the back)", "y", True)
    s = part.sketch_z("cap_z1 + 1 mm", "cover slot sketch")
    part.rect(s, "slot_x0", "slot_y0", "slot_x1", "slot_y1", "cover slot",
              pin_u0="slot_x0", pin_u1="slot_x1", pin_v0="slot_y0", pin_v1="slot_y1")
    part.extrude_toward(s, "cap_z1 + 1 mm - slot_z0", kCut, "cover slots", "z", False)
    s = part.sketch_z("cap_z1 + 1 mm", "USB channel sketch")
    part.rect(s, "usb_ch_x0", "usb_ch_y0", "usb_ch_x1", "usb_ch_y1", "USB channel",
              pin_u0="usb_ch_x0", pin_u1="usb_ch_x1", pin_v0="usb_ch_y0", pin_v1="usb_ch_y1")
    part.extrude_toward(s, "cap_z1 + 2 mm - pocket_z1", kCut, "USB-C plug channel", "z", False)
    s = part.sketch_y("wall_in_y - 0.5 mm", "camera seat sketch")
    part.rect(s, "-seat_w / 2", "-seat_w / 2", "seat_w / 2", "seat_w / 2", "camera seat", wu="seat_w", sym_u=True,
              wv="seat_w", sym_v=True)
    part.extrude_toward(s, "seat_y1 - wall_in_y + 0.5 mm", kCut, "camera module seat", "y", True)
    s = part.sketch_y("seat_y1 - 0.1 mm", "holder tube bore sketch")
    part.circle(s, 0, 0, "tube_bore_d", "holder tube bore")
    part.extrude_toward(s, "tube_bore_y1 - seat_y1 + 0.1 mm", kCut, "lens holder tube bore", "y", True)
    s = part.sketch_y("front_y", "spigot sketch")
    part.circle(s, 0, 0, "spigot_d", "spigot")
    part.extrude_toward(s, "spigot_h", kJoin, "locating spigot for the screen tube", "y", True)
    s = part.sketch_y("tube_bore_y1 - 0.1 mm", "lens hole sketch")
    part.circle(s, 0, 0, "lens_hole_d", "lens hole")
    part.extrude_toward(s, "front_y + spigot_h - tube_bore_y1 + 1 mm", kCut, "lens hole", "y", True)
    s = part.sketch_y("front_y", "front magnet sketch")
    part.circle(s, 0, "mag_z", "mag_pocket_d", "magnet top")
    part.circle(s, 0, "-mag_z", "mag_pocket_d", "magnet bottom")
    part.extrude_toward(s, "mag_pocket_h", kCut, "front magnet pockets", "y", False)
    s = part.sketch_z("cube_half", "boss pocket sketch")
    for sx in ("", "-"):
        for sy in ("", "-"):
            part.circle(s, f"{sx}boss_x", f"{sy}boss_y", "boss_pocket_d", f"boss pocket {sx or '+'}{sy or '+'}")
    part.extrude_toward(s, "boss_pocket_h", kCut, "pockets for the cube's top bosses", "z", True)
    s = part.sketch_z("-cube_half", "foot magnet sketch")
    part.circle(s, "foot_mag_x", 0, "mag_pocket_d", "foot magnet +x")
    part.circle(s, "-foot_mag_x", 0, "mag_pocket_d", "foot magnet -x")
    part.extrude_toward(s, "mag_pocket_h", kCut, "foot magnet pockets (riser)", "z", True)
    s = part.sketch_y("front_y", "mark sketch")
    for sx in ("", "-"):
        part.rect(s, f"{sx}(spigot_d / 2 + 0.8 mm)", "-mark_w / 2", f"{sx}(body_half - 0.8 mm)", "mark_w / 2",
                  f"mark {sx or '+'}x", wv="mark_w", sym_v=True, pin_u0=f"{sx}(spigot_d / 2 + 0.8 mm)",
                  pin_u1=f"{sx}(body_half - 0.8 mm)")
    part.rect(s, "-mark_w / 2", "mag_z + mag_pocket_d / 2 + 0.8 mm", "mark_w / 2", "cube_half - 0.8 mm", "mark up",
              wu="mark_w", sym_u=True, pin_v0="mag_z + mag_pocket_d / 2 + 0.8 mm", pin_v1="cube_half - 0.8 mm")
    part.extrude_toward(s, "mark_h", kCut, "alignment marks through the axis", "y", False)


def cover_features(part: NativePart) -> None:
    s = part.sketch_y("cov_y0", "cover sketch")
    part.rect(s, "cov_x0", "slot_z0", "cov_x1", "cov_z1", "cover", pin_u0="cov_x0", pin_u1="cov_x1",
              pin_v0="slot_z0", pin_v1="cov_z1")
    part.extrude_toward(s, "cov_t", kJoin, "back cover", "y", True)
    s = part.sketch_y("cov_y0 - 1 mm", "notch sketch")
    part.rect(s, "notch_x0", "pocket_z1", "notch_x1", "cov_z1 + 1 mm", "notch", pin_u0="notch_x0", pin_u1="notch_x1",
              pin_v0="pocket_z1", pin_v1="cov_z1 + 1 mm")
    part.extrude_toward(s, "cov_t + 2 mm", kCut, "notch for the USB-C plug", "y", True)
    s = part.sketch_y("cov_y1", "rib sketch")
    for sx in ("", "-"):
        part.rect(s, f"{sx}(5 mm - rib_w / 2)", "pocket_z0 + 2 mm", f"{sx}(5 mm + rib_w / 2)", "pocket_z1 - 2 mm",
                  f"rib {sx or '+'}", pin_u0=f"{sx}(5 mm - rib_w / 2)", pin_u1=f"{sx}(5 mm + rib_w / 2)",
                  pin_v0="pocket_z0 + 2 mm", pin_v1="pocket_z1 - 2 mm")
    part.extrude_toward(s, "rib_h", kJoin, "pressure ribs", "y", True)


def tube_features(part: NativePart) -> None:
    s = part.sketch_y("front_y", "flange sketch")
    part.rect(s, "-fl_half_x", "-fl_half_z", "fl_half_x", "fl_half_z", "flange", wu="2 * fl_half_x", sym_u=True,
              wv="2 * fl_half_z", sym_v=True)
    part.extrude_toward(s, "fl_t", kJoin, "flange", "y", True)
    s = part.sketch_y("fl_y1", "tube sketch")
    part.circle(s, 0, 0, "tube_od", "tube")
    part.extrude_toward(s, "tube_end_y - fl_y1", kJoin, "screen tube", "y", True)
    s = part.sketch_y("front_y - 1 mm", "bore sketch")
    part.circle(s, 0, 0, "fl_bore_d", "flange bore")
    part.extrude_toward(s, "fl_t + 2 mm", kCut, "flange bore", "y", True)
    s = part.sketch_y("fl_y1", "tube bore sketch")
    part.circle(s, 0, 0, "tube_id", "tube bore")
    part.extrude_toward(s, "tube_end_y - fl_y1 + 1 mm", kCut, "tube bore", "y", True)
    s = part.sketch_y("front_y - 1 mm", "recess sketch")
    part.circle(s, 0, 0, "recess_d", "recess")
    part.extrude_toward(s, "recess_h + 1 mm", kCut, "recess for the holder's spigot", "y", True)
    s = part.sketch_y("front_y - 1 mm", "tube magnet sketch")
    part.circle(s, 0, "mag_z", "mag_pocket_d", "magnet top")
    part.circle(s, 0, "-mag_z", "mag_pocket_d", "magnet bottom")
    part.extrude_toward(s, "mag_pocket_h + 1 mm", kCut, "magnet pockets", "y", True)


def screen_features(part: NativePart) -> None:
    s = part.sketch_y("scr_y0", "screen cap sketch")
    part.circle(s, 0, 0, "scr_od", "cap")
    part.extrude_toward(s, "skirt + scr_t", kJoin, "screen cap", "y", True)
    s = part.sketch_y("scr_y0 - 1 mm", "skirt sketch")
    part.circle(s, 0, 0, "scr_id", "skirt bore")
    part.extrude_toward(s, "skirt + 1 mm", kCut, "skirt (slides on the tube)", "y", True)


def riser_features(part: NativePart) -> None:
    s = part.sketch_z("-cube_half - riser_t", "riser sketch")
    part.rect(s, "-(riser_x + riser_wall)", "riser_y0 - riser_wall", "riser_x + riser_wall", "riser_y1 + riser_wall",
              "riser", wu="2 * (riser_x + riser_wall)", sym_u=True, pin_v0="riser_y0 - riser_wall",
              pin_v1="riser_y1 + riser_wall")
    part.extrude_toward(s, "riser_t + riser_rim", kJoin, "riser plate", "z", True)
    s = part.sketch_z("-cube_half", "pocket sketch")
    part.rect(s, "-riser_x", "riser_y0", "riser_x", "riser_y1", "foot pocket", wu="2 * riser_x", sym_u=True,
              pin_v0="riser_y0", pin_v1="riser_y1")
    part.extrude_toward(s, "riser_rim + 1 mm", kCut, "pocket for the holder's foot", "z", True)
    s = part.sketch_z("-cube_half", "riser magnet sketch")
    part.circle(s, "foot_mag_x", 0, "mag_pocket_d", "magnet +x")
    part.circle(s, "-foot_mag_x", 0, "mag_pocket_d", "magnet -x")
    part.extrude_toward(s, "mag_pocket_h", kCut, "magnet pockets", "z", False)


PART_SPECS = {
    "body": ("Camera target for the XIAO ESP32-S3 Sense: hangs in an openUC2 cube from the top (cap on four corner bosses), "
             "camera module in a square seat on the cube axis, board slid in from the back, USB-C from the top. "
             "FDM, print upside down on the cap, no supports. Magnets 8x3: 2 front, 2 foot.", body_features),
    "cover": ("Back cover of the camera target: slides down through the cap into the side-wall slots and presses the board "
              "forward with two ribs. FDM, print flat, ribs up.", cover_features),
    "tube": ("Screen tube: sits on the target's front spigot, held by two 8x3 magnets; carries the screen cap. "
             "FDM, print on the flange back.", tube_features),
    "screen": ("Screen cap: printed 0.6 mm white screen, slides on the tube to set the distance to the sensor. "
               "FDM in white, print screen down.", screen_features),
    "riser": ("5 mm riser: the target standing on a table at the height of cubes on puzzle pieces; two 8x3 magnets. "
              "FDM, print flat.", riser_features),
}


# ---------------------------------------------------------------------- assemblies
def interference(app, cd, a, b):
    s1 = app.TransientObjects.CreateObjectCollection()
    s2 = app.TransientObjects.CreateObjectCollection()
    s1.Add(a)
    s2.Add(b)
    try:
        res = cd.AnalyzeInterference(s1, s2)
    except Exception as exc:
        return None, [str(exc)[:60]]
    vol, boxes = 0.0, []
    for r in res:
        vol += safe(lambda: r.Volume, 0.0)
        rb = safe(lambda: r.InterferenceBody.RangeBox)
        if rb is not None:
            boxes.append([round(v * 10, 2) for v in (rb.MinPoint.X, rb.MinPoint.Y, rb.MinPoint.Z, rb.MaxPoint.X, rb.MaxPoint.Y, rb.MaxPoint.Z)])
    return round(vol * 1000, 3), boxes


def placements(ps: ParamSet, files: dict, standalone: bool) -> list[tuple]:
    p = ps
    xiao_o = (p.cam_bz, p.sensor_y - p.sensor_by, -p.cam_bx)
    out = [
        ("holder", files["body"], (0, 0, 0), I3),
        ("back cover", files["cover"], (0, 0, 0), I3),
        ("XIAO ESP32-S3 Sense", files["xiao"], xiao_o, XIAO_COLS),
        ("screen tube", files["tube"], (0, 0, 0), I3),
        ("screen cap", files["screen"], (0, 0, 0), I3),
    ]
    yh = p.front_y - p.mag_pocket_h + p.mag_h / 2
    yt = p.front_y + p.mag_pocket_h - p.mag_h / 2
    for tag, z in (("top", p.mag_z), ("bottom", -p.mag_z)):
        out.append((f"magnet holder {tag}", files["magnet"], (0, yh, z), MAG_Y))
        out.append((f"magnet tube {tag}", files["magnet"], (0, yt, z), MAG_Y))
    zf = -p.cube_half + p.mag_pocket_h - p.mag_h / 2
    for tag, x in (("+x", p.foot_mag_x), ("-x", -p.foot_mag_x)):
        out.append((f"magnet foot {tag}", files["magnet"], (x, 0, zf), I3))
    if standalone:
        out.append(("riser", files["riser"], (0, 0, 0), I3))
        zr = -p.cube_half - p.mag_pocket_h + p.mag_h / 2
        for tag, x in (("+x", p.foot_mag_x), ("-x", -p.foot_mag_x)):
            out.append((f"magnet riser {tag}", files["magnet"], (x, 0, zr), I3))
    else:
        out.insert(0, ("cube", files["cube"], (0, 0, 0), I3))
    return out


def build_assembly(app, ps: ParamSet, files: dict, path: Path, standalone: bool) -> dict:
    close_if_open(app, path)
    if path.exists():
        doc = app.Documents.Open(str(path), False)
    else:
        doc = app.Documents.Add(kAssemblyDocumentObject, app.FileManager.GetTemplateFile(kAssemblyDocumentObject), False)
        doc.SaveAs(str(path), False)
    rep = {}
    try:
        b = Builder(app, doc)
        occ = {}
        for role, f, origin, cols in placements(ps, files, standalone):
            occ[role] = b.place(role, Path(f), origin, cols)
        rep["removed"] = b.prune()
        doc.Update()
        doc.Save()
        cd = doc.ComponentDefinition
        roles = list(occ)
        rep["interference_mm3"] = {}
        for i, a in enumerate(roles):
            for c in roles[i + 1:]:
                if a.startswith("magnet") and c.startswith("magnet"):
                    continue
                vol, boxes = interference(app, cd, occ[a], occ[c])
                if vol:
                    rep["interference_mm3"][f"{a} / {c}"] = {"mm3": vol, "boxes": boxes[:3]}
        rep["occurrences"] = b.placed
        export_step(app, doc, path.with_suffix(".stp"))
    finally:
        doc.Close(True)
    return rep


# ---------------------------------------------------------------------- main
def build(app, ps: ParamSet, only: set[str] | None, do_assembly: bool) -> dict:
    INV_DIR.mkdir(parents=True, exist_ok=True)
    if report(ps):
        raise SystemExit("design checks failed (see [error] above) - fix the parameters")
    for key, p in PARTS.items():
        if not Path(p).exists():
            raise SystemExit(f"{key}: {p} not found - adjust xiao_target.PARTS")
    files = {k: INV_DIR / f"{NAMES[k]}.ipt" for k in PART_SPECS}
    files.update({k: PARTS[k] for k in ("cube", "xiao", "magnet")})
    rep = {"names": NAMES, "files": {k: str(v) for k, v in files.items()}}
    for key, (desc, fn) in PART_SPECS.items():
        if only and key not in only:
            continue
        print(f"\n== {files[key].name}")
        rep[key] = _part(app, ps, files[key], desc, fn)
        print(json.dumps({k: v for k, v in rep[key].items() if k != "range_mm"}, indent=1))
    if do_assembly:
        for standalone, name in ((False, NAMES["assembly"]), (True, NAMES["assembly"] + " - standalone")):
            asm = INV_DIR / f"{name}.iam"
            print(f"\n== {asm.name}")
            r = build_assembly(app, ps, files, asm, standalone)
            rep["standalone" if standalone else "in_cube"] = r
            inter = r["interference_mm3"]
            print("interference:", json.dumps(inter, indent=1) if inter else "none")
    rep["checks"] = checks(ps)
    rep["overrides"] = ps.overrides_vs(make_params())
    ps.dump(INV_DIR / f"{NAMES['assembly']} - build.json", rep)
    return rep


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--set", action="append", metavar="NAME=VALUE", help="override a parameter (repeatable)")
    ap.add_argument("--params", help="JSON file {name: value} with overrides")
    ap.add_argument("--from-ipt", help="take the base parameters of a generated .ipt (edits made in Inventor)")
    ap.add_argument("--only", nargs="*", choices=list(PART_SPECS), help="rebuild only these parts")
    ap.add_argument("--no-assembly", action="store_true")
    a = ap.parse_args()
    with session() as app:
        overrides = {}
        if a.from_ipt:
            known = make_params().items
            overrides.update({k: v for k, v in read_user_parameters(app, Path(a.from_ipt)).items()
                              if k in known and not known[k].derived})
        overrides.update(overrides_from(a))
        build(app, make_params(overrides), set(a.only) if a.only else None, not a.no_assembly)


if __name__ == "__main__":
    main()
