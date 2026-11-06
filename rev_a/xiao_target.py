"""XIAO ESP32-S3 Sense camera target for the openUC2 cube - parameters and design checks (no Inventor).

    python xiao_target.py                          # table + checks + screen optics
    python xiao_target.py --set screen_d=22 --set lens_f=3.3

Everything is modelled in the cube frame: cube centre at the origin, z up (pins up), the beam
along y, the camera looking toward +y. The holder hangs in the cube from the top like a
T-shirt target: its cap rests on the cube's top face and takes four of the top corner bosses,
so the sensor sits on the cube axis (x = z = 0) in the plane y = sensor_y. The same table
drives build_xiao_target.py and check_xiao_target.py.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE.parent))           # cadlib
from cadlib.params import D, P, ParamSet, parse_sets  # noqa: E402

INV_DIR = HERE / "INVENTOR"
NAMES = {
    "assembly": "ASS - 9020 - CAMTARXIA - V04",
    "body": "PRT - 9021 - CAMTARXIA - V04",
    "cover": "PRT - 9022 - CAMTARCOV - V04",
    "tube": "PRT - 9023 - CAMTARTUB - V04",
    "screen": "PRT - 9024 - CAMTARSCR - V04",
    "riser": "PRT - 9025 - CAMTARRIS - V04",
}
CADNEW = Path(r"C:\Users\benir\Documents\openUC2-CAD-new\workspace")
XIAO_DIR = CADNEW / "BUY" / "OLD STUFF" / "BUY - Seeed Studio XIAO-ESP32-S3-Sense" / "BUY - Seeed Studio XIAO-ESP32-S3-Sense"
PARTS = {
    "cube": CADNEW / "ASS" / "ASS - 2000 - CUB - V04.iam",
    "xiao": XIAO_DIR / "BUY - Seeed Studio XIAO-ESP32-S3-Sense.iam",
    "magnet": CADNEW / "BUY" / "BUY - NeFeB-Magnet - ø8x3 N40 Ni.ipt",
}


def parameters() -> list:
    return [
        # ---- cube ASS-2000 (measured)
        P("cube_half", 24.9, comment="cube body half size; top face z = +cube_half"),
        P("port_half", 17.0, comment="face ports +-17 (top, bottom, faces)"),
        P("boss_x", 20.65, comment="top corner bosses at (+-boss_x, +-boss_y) and (+-boss_y, +-boss_x)"),
        P("boss_y", 14.5, comment=""),
        P("boss_d", 4.9, comment="boss diameter"),
        P("boss_h", 1.9, comment="boss height above the top face"),
        # ---- XIAO ESP32-S3 Sense model (vendor frame bx, by, bz; camera looks +by)
        P("cam_bx", 8.75, comment="camera axis in the vendor frame (bx, bz)"),
        P("cam_bz", -6.75, comment=""),
        P("sensor_by", 8.6, comment="sensor plane (ASSUMED: module base bottom 7.95 + 0.65) - measure"),
        P("pcb_back_by", -0.25, comment="back of the main PCB"),
        P("comp_front_by", 8.25, comment="highest part on the board besides the camera (microSD socket)"),
        P("mod_w", 8.0, comment="camera module base, square"),
        P("mod_by1", 10.05, comment="top of the module base"),
        P("tube_d", 7.85, comment="lens holder tube"),
        P("tube_by1", 11.95, comment="top of the holder tube"),
        P("lens_tip_by", 13.71, comment="lens nose (lens screwed in)"),
        P("board_bx0", -8.97, comment="board end without USB (expansion board)"),
        P("usb_bx1", 13.81, comment="USB-C end of the board"),
        P("board_bz0", -15.0, comment="board edges across"),
        P("board_bz1", 2.78, comment=""),
        P("sd_bx1", 15.39, comment="microSD socket mouth - beyond the USB-C, same end"),
        P("usb_bz", -6.12, comment="USB-C receptacle centre"),
        P("usb_by", 2.11, comment=""),
        # ---- where the sensor goes in the cube
        P("sensor_y", 0.0, comment="sensor plane in the cube (0 = centre plane)"),
        # ---- holder body (FDM, printed upside down on the cap)
        P("clr_board", 0.4, comment="clearance around the board outline (the camera module locates, not the board)"),
        P("wall_gap", 0.35, comment="microSD socket to the front wall"),
        P("front_y", 4.6, comment="front face of the holder (sensor plane + 4.6)"),
        P("seat_clr", 0.15, comment="camera module in its square seat, per side"),
        P("lens_hole_d", 7.0, comment="hole for the lens barrel / free view onto the bare chip"),
        P("spigot_d", 12.0, comment="locating boss on the front face for the screen tube"),
        P("spigot_h", 0.8, comment=""),
        P("mag_d", 8.0, comment="NdFeB magnet 8 x 3"),
        P("mag_h", 3.0, comment=""),
        P("mag_fit", 0.2, comment="magnet pocket oversize (FDM, glue the magnets)"),
        P("mag_z", 11.0, comment="front magnets at z = +-mag_z on the axis plane x = 0"),
        P("body_half", 16.0, comment="holder half width (x)"),
        P("cov_gap", 0.3, comment="board back to the cover's front face (ribs close it)"),
        P("cov_t", 2.0, comment="back cover thickness"),
        P("cov_clr", 0.15, comment="cover in its slots"),
        P("slot_depth", 1.5, comment="cover slots reach this far into the side walls"),
        P("lip_t", 1.4, comment="wall lip behind the cover"),
        P("usb_ch_w", 13.0, comment="channel for the USB-C plug (x)"),
        P("usb_ch_t", 7.5, comment="channel for the USB-C plug (y, behind the plug centre x2)"),
        P("cap_t", 4.0, comment="cap (the T's shoulders) on the cube's top face"),
        P("cap_half_x", 24.6, comment="cap half size x"),
        P("cap_half_y", 17.9, comment="cap half size y (clears the bosses at y +-20.65)"),
        P("boss_pocket_d", 5.3, comment="cap pockets for the bosses (FDM; 5.1 for SLA)"),
        P("boss_pocket_h", 2.2, comment=""),
        P("flare_back", 16.5, comment="foot reaches y = -flare_back at the bottom (45 deg, prints without support)"),
        P("foot_mag_x", 9.5, comment="foot magnets at (+-foot_mag_x, 0) in the bottom face"),
        P("mark_w", 0.6, comment="alignment marks (grooves) on the front face"),
        P("mark_h", 0.4, comment=""),
        # ---- back cover
        P("rib_w", 1.2, comment="pressure ribs on the cover"),
        P("rib_h", 0.3, comment=""),
        P("cov_tab", 4.0, comment="cover sticks out of the cap by this (pull tabs)"),
        # ---- screen tube (magnetic) and screen cap
        P("fl_half_x", 15.0, comment="tube flange half size x"),
        P("fl_half_z", 16.5, comment="tube flange half size z"),
        P("fl_t", 4.0, comment="flange thickness"),
        P("fl_bore_d", 11.0, comment="flange bore"),
        P("tube_od", 20.0, comment="screen tube"),
        P("tube_id", 16.0, comment=""),
        P("tube_end_y", 15.0, comment="front end of the tube"),
        P("cap_clr", 0.3, comment="screen cap on the tube (sliding friction fit, FDM)"),
        P("scr_wall", 1.6, comment="screen cap wall"),
        P("skirt", 10.0, comment="screen cap skirt length"),
        P("scr_t", 0.6, comment="printed screen (white PLA/PETG, 0.6 = 3 layers)"),
        P("screen_d", 20.0, comment="screen (inner face) distance from the sensor"),
        # ---- 5 mm riser for standing on a table next to cubes on puzzle pieces
        P("riser_t", 5.0, comment="height added (= PUZ11 thickness)"),
        P("riser_rim", 1.0, comment="rim around the holder's foot"),
        P("riser_clr", 0.3, comment="foot in the riser pocket"),
        P("riser_wall", 2.0, comment="rim wall"),
        # ---- optics (assumptions for the screen distance)
        P("lens_f", 3.5, comment="XIAO Sense lens focal length (ASSUMED, ~66 deg diagonal on OV2640)"),
        P("sensor_w", 3.52, comment="OV2640 active area 1600 x 1200 x 2.2 um"),
        P("sensor_h", 2.64, comment=""),
        # ---- derived: XIAO in the cube (x = cam_bz - bz, y = by + ofs_y, z = bx - cam_bx)
        D("ofs_y", "sensor_y - sensor_by", comment="vendor by -> cube y"),
        D("pcb_back_y", "pcb_back_by + ofs_y"),
        D("comp_front_y", "comp_front_by + ofs_y"),
        D("mod_y1", "mod_by1 + ofs_y"),
        D("tube_y1", "tube_by1 + ofs_y"),
        D("lens_tip_y", "lens_tip_by + ofs_y"),
        D("board_xl", "board_bz1 - cam_bz", comment="board reaches x = -board_xl"),
        D("board_xr", "cam_bz - board_bz0", comment="board reaches x = +board_xr"),
        D("board_z0", "board_bx0 - cam_bx", comment="lower board end"),
        D("usb_z1", "usb_bx1 - cam_bx", comment="USB-C mouth (points up)"),
        D("sd_z1", "sd_bx1 - cam_bx", comment="microSD socket mouth (points up)"),
        D("usb_x", "cam_bz - usb_bz"),
        D("usb_y", "usb_by + ofs_y"),
        # ---- derived: holder
        D("wall_in_y", "comp_front_y + wall_gap", comment="inner face of the front wall"),
        D("seat_w", "mod_w + 2 * seat_clr", comment="square seat of the camera module"),
        D("seat_y1", "mod_y1 + 0.05 mm", comment="seat floor (module base stops here)"),
        D("tube_bore_d", "tube_d + 0.45 mm"),
        D("tube_bore_y1", "tube_y1 + 0.2 mm"),
        D("mag_pocket_d", "mag_d + mag_fit"),
        D("mag_pocket_h", "mag_h + 0.1 mm"),
        D("cov_y1", "pcb_back_y - cov_gap", comment="cover front face"),
        D("cov_y0", "cov_y1 - cov_t", comment="cover back face"),
        D("body_y0", "cov_y0 - cov_clr - lip_t", comment="back face of the holder"),
        D("pocket_x0", "-(board_xl + clr_board)"),
        D("pocket_x1", "board_xr + clr_board"),
        D("pocket_z0", "board_z0 - clr_board", comment="pocket floor = top of the solid foot"),
        D("pocket_z1", "sd_z1 + clr_board", comment="the microSD socket sticks out further than the USB-C"),
        D("slot_x0", "pocket_x0 - slot_depth"),
        D("slot_x1", "pocket_x1 + slot_depth"),
        D("slot_y0", "cov_y0 - cov_clr"),
        D("slot_y1", "cov_y1 + cov_clr"),
        D("slot_z0", "pocket_z0 - 1 mm", comment="cover rests on the slot ends"),
        D("cap_z1", "cube_half + cap_t"),
        D("flare_front", "front_y + pocket_z0 + cube_half", comment="foot front edge at the bottom (45 deg)"),
        D("flare_back_z", "-cube_half + flare_back + body_y0", comment="where the back slope meets the back face"),
        D("usb_ch_x0", "usb_x - usb_ch_w / 2"),
        D("usb_ch_x1", "usb_x + usb_ch_w / 2"),
        D("usb_ch_y0", "usb_y - usb_ch_t / 2"),
        D("usb_ch_y1", "comp_front_y + 0.25 mm", comment="channel also over the microSD socket"),
        # ---- derived: cover
        D("cov_x0", "slot_x0 + 0.25 mm"),
        D("cov_x1", "slot_x1 - 0.25 mm"),
        D("cov_z1", "cap_z1 + cov_tab"),
        D("notch_x0", "usb_ch_x0 - 0.3 mm"),
        D("notch_x1", "usb_ch_x1 + 0.3 mm"),
        # ---- derived: tube, screen cap, riser
        D("fl_y1", "front_y + fl_t"),
        D("recess_d", "spigot_d + 0.3 mm"),
        D("recess_h", "spigot_h + 0.2 mm"),
        D("scr_id", "tube_od + cap_clr"),
        D("scr_od", "scr_id + 2 * scr_wall"),
        D("scr_y0", "screen_d - skirt", comment="back end of the screen cap's skirt"),
        D("scr_y1", "screen_d + scr_t", comment="outer face of the screen"),
        D("riser_x", "body_half + riser_clr", comment="riser pocket"),
        D("riser_y0", "-flare_back - riser_clr"),
        D("riser_y1", "flare_front + riser_clr"),
    ]


def make_params(overrides: dict | None = None) -> ParamSet:
    ps = ParamSet(parameters())
    for k, v in (overrides or {}).items():
        ps.set(k, v)
    return ps


def screen_optics(p) -> dict:
    """Lens between the sensor and a screen at screen_d: conjugates, magnification, field on the screen."""
    d, f = p.screen_d, p.lens_f
    disc = d * d - 4 * f * d
    if disc < 0:
        return {"ok": False, "min_d": 4 * f}
    s_i = (d - math.sqrt(disc)) / 2
    s_o = d - s_i
    m = s_i / s_o
    return {"ok": True, "s_i": s_i, "s_o": s_o, "m": m, "field_w": p.sensor_w / m, "field_h": p.sensor_h / m,
            "unscrew": s_i - f, "min_d": 4 * f}


def checks(ps: ParamSet) -> list[tuple[str, str]]:
    out = []
    eps = 1e-3

    def need(ok, msg, level="error"):
        if not ok:
            out.append((level, msg))

    p = ps
    # passes the cube's top port and sits in the bottom port
    need(p.body_half <= p.port_half - 0.5 + eps, "holder wider than the top port (x)")
    need(p.body_y0 >= -p.port_half + 0.5 - eps and p.front_y + p.spigot_h <= p.port_half - 0.5 + eps, "holder too thick for the top port (y)")
    need(p.flare_back <= p.port_half - 0.3 + eps and p.flare_front <= p.port_half - 0.3 + eps, "foot does not pass the ports (y)")
    need(p.flare_back >= -p.body_y0 - eps, "foot narrower than the holder at the back")
    # cap on the top face
    need(p.cap_half_y <= p.boss_x - p.boss_d / 2 - 0.2 + eps, "cap covers the bosses it should clear (y)")
    need(p.cap_half_x <= p.cube_half - 0.2 + eps, "cap wider than the cube")
    need(p.boss_x + p.boss_pocket_d / 2 <= p.cap_half_x - 1.0 + eps, "boss pockets break the cap edge (x)")
    need(p.boss_y + p.boss_pocket_d / 2 <= p.cap_half_y - 0.6 + eps, "boss pockets break the cap edge (y)")
    need(p.boss_pocket_h >= p.boss_h + 0.2 - eps, "boss pockets too shallow")
    need(p.boss_x - p.boss_pocket_d / 2 >= p.body_half + 1.0 - eps, "boss pockets cut into the hanging plate")
    # board pocket and walls
    need(p.slot_x0 >= -p.body_half + 2.0 - eps and p.slot_x1 <= p.body_half - 2.0 + eps, "side walls thinner than 2 mm at the cover slots")
    need(p.front_y - p.wall_in_y >= p.mag_pocket_h + 1.2 - eps, "front wall too thin for the magnet pockets")
    need(p.seat_y1 > p.wall_in_y, "module seat does not reach into the front wall")
    need(p.tube_bore_y1 < p.front_y - 0.5, "holder tube bore breaks the front face")
    need(p.lens_hole_d >= 6.6 - eps and p.lens_hole_d < p.tube_bore_d, "lens hole must clear the barrel (6.3) and stay smaller than the holder tube bore")
    need(p.mag_z - p.mag_pocket_d / 2 >= p.recess_d / 2 + 0.6 - eps, "front magnets cut into the spigot recess (tube)")
    need(p.mag_z - p.mag_pocket_d / 2 >= p.seat_w / 2 + 1.0 - eps, "front magnets reach the camera seat")
    need(p.mag_z + p.mag_pocket_d / 2 <= p.fl_half_z - 1.0 + eps, "front magnets break the flange edge")
    need(p.usb_ch_x0 >= p.slot_x0 + 1.0 - eps and p.usb_ch_x1 <= p.slot_x1 - 1.0 + eps, "USB channel cuts the cover legs away")
    need(p.usb_ch_y1 <= p.wall_in_y + eps, "USB/microSD channel cuts into the front wall")
    need(p.pocket_z1 + 1.0 <= p.cube_half, "board pocket reaches the cap")
    # foot magnets
    need(p.foot_mag_x + p.mag_pocket_d / 2 <= p.body_half - 1.0 + eps, "foot magnets break the side faces")
    need(p.pocket_z0 - (-p.cube_half + p.mag_pocket_h) >= 2.0 - eps, "less than 2 mm between the foot magnets and the board pocket")
    need(p.flare_back_z <= p.pocket_z0 + eps, "back slope above the pocket floor")
    # tube and screen in the cube
    need(p.fl_half_x <= p.port_half - 0.5 + eps and p.fl_half_z <= p.port_half - 0.4 + eps, "flange does not pass the face port")
    need(p.fl_half_z <= -p.pocket_z0 - 1.0 + eps, "flange sits on the foot's front slope")
    need(p.scr_od / 2 <= p.port_half - 0.5 + eps, "screen cap does not pass the face port")
    need(p.tube_id > p.fl_bore_d, "tube bore smaller than the flange bore")
    need(p.screen_d >= p.tube_end_y - eps, "screen cap pushed further back than the tube end")
    need(p.screen_d <= p.tube_end_y + p.skirt - 3.0 + eps, "screen cap holds the tube over less than 3 mm")
    need(p.scr_y1 <= p.cube_half - 0.3 + eps, "screen reaches out of the cube face (fine on the table, not inside a row)", "warn")
    opt = screen_optics(p)
    need(opt["ok"], f"screen at {p.screen_d:g} mm cannot be imaged with f {p.lens_f:g} (needs >= 4 f = {opt['min_d']:.1f})")
    if opt["ok"]:
        out.append(("info", f"screen at {p.screen_d:g} mm: lens {opt['s_i']:.2f} mm from the sensor (unscrew ~{opt['unscrew']:.1f} mm from infinity "
                            f"focus), screen {opt['s_o']:.2f} mm in front of it, m {opt['m']:.2f}, field {opt['field_w']:.1f} x {opt['field_h']:.1f} mm"))
    out.append(("info", f"holder x +-{p.body_half}, y {p.body_y0:.2f}..{p.front_y} (foot {-p.flare_back}..{p.flare_front:.2f}), z {-p.cube_half}..{p.cap_z1}; "
                        f"board pocket x {p.pocket_x0:.2f}..{p.pocket_x1:.2f} z {p.pocket_z0:.2f}..{p.pocket_z1:.2f}; front wall {p.wall_in_y:.2f}..{p.front_y}"))
    out.append(("info", f"USB-C mouth at (x {p.usb_x:.2f}, y {p.usb_y:.2f}, z {p.usb_z1:.2f}), microSD mouth z {p.sd_z1:.2f}; plug and card come in from the top through the cap"))
    return [o for o in out if o[1]]


def report(ps: ParamSet) -> int:
    print("XIAO ESP32-S3 Sense camera target")
    for row in ps.table():
        expr = f"  = {row['expr']}" if row["expr"] else ""
        print(f"  {row['name']:<14} {row['value']:>9.4g} {row['unit']:<3} {row['comment']}{expr}")
    errors = 0
    for level, msg in checks(ps):
        print(f"  [{level}] {msg}")
        errors += level == "error"
    return errors


def overrides_from(args) -> dict:
    ov = {}
    if getattr(args, "params", None):
        ov.update(json.loads(Path(args.params).read_text(encoding="utf-8")))
    ov.update(parse_sets(getattr(args, "set", None)))
    return ov


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--set", action="append", metavar="NAME=VALUE")
    ap.add_argument("--params", help="JSON file {name: value}")
    a = ap.parse_args()
    sys.exit(1 if report(make_params(overrides_from(a))) else 0)


if __name__ == "__main__":
    main()
