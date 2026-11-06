"""Build the XIAO beam target rev C as native, parametric Inventor parts and assemblies.

    python build_xiao_target.py                    # 5 parts, assemblies (entry from the top / side), interference
    python build_xiao_target.py --set screen_d=21  # any parameter of xiao_target.py
    python build_xiao_target.py --only chassis key
    python build_xiao_target.py --only cover --no-assembly

Writes into INVENTOR/ (provisional numbers, see xiao_target.NAMES): the printed parts (.ipt, .stp, .stl),
"ASS - 9036 - CAMTARXIA - V04.iam" (seated in an ASS-2000 cube with a PUZ11 on top, entered from the top),
"... - side entry.iam" (turned 90 deg about the beam), STEP copies and "<assembly> - build.json".
Every dimension is an Inventor user parameter (fx). Parts are modelled as printed: in the assemblies the two
flexure pads overlap the +x throat walls by pad_over, which is their preload. Needs the miniforge `pyinventor` env.

The build runs in its OWN hidden Inventor, started here and quit here, so a hang or a crash cannot touch the
session Benedict works in (2026-11-05: Documents.Open in the live session crashed it). If no new process
appears the script stops without doing anything. --live-session uses the running Inventor instead.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from cadlib.inventor_helpers import Builder, close_if_open, kAssemblyDocumentObject, safe, session  # noqa: E402
from cadlib.native_part import NativePart, export_step, kCut, kJoin, kNeg, read_user_parameters  # noqa: E402
from cadlib.params import ParamSet  # noqa: E402
from xiao_target import INV_DIR, NAMES, PARTS, chassis_outline, checks, make_params, overrides_from, report  # noqa: E402

DARK = ("Smooth - Dark Gray", "Satin - Dark Gray", "Dark Gray", "Smooth - Black", "Satin - Black", "Black")
WHITE = ("Smooth - White", "Satin - White", "White")
GREY = ("Smooth - Light Gray", "Satin - Light Gray", "Light Gray")
ORANGE = ("Smooth - Orange", "Satin - Orange", "Orange")
I3 = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
MAG_Y = ((1, 0, 0), (0, 0, -1), (0, 1, 0))          # magnet axis (part z) along tool y
XIAO_COLS = ((0, 0, 1), (0, 1, 0), (-1, 0, 0))      # vendor bx -> z, by -> y, bz -> -x
SCREW_Y = ((1, 0, 0), (0, 0, 1), (0, -1, 0))        # ISO 10642: shank (part -z) along +y
SIDE = ((0, 0, -1), (0, 1, 0), (1, 0, 0))           # turned about the beam: handle to +x, rails to +z


def _inventor_pids() -> set[int]:
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Inventor.exe", "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout
    return {int(line.split('","')[1]) for line in out.splitlines() if line.startswith('"Inventor')}


@contextmanager
def private_session(limit_s: int = 1500):
    """A separate hidden Inventor. Never attaches to a running one; a watchdog kills only this process."""
    import win32com.client
    before = _inventor_pids()
    app = win32com.client.DispatchEx("Inventor.Application")
    new = _inventor_pids() - before
    if len(new) != 1:
        raise SystemExit(f"no new Inventor process (found {new}): stopping before anything was touched")
    pid = new.pop()

    def kill():
        print(f"[watchdog] {limit_s} s reached, killing the private Inventor {pid}", flush=True)
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        os._exit(3)

    dog = threading.Timer(limit_s, kill)
    dog.daemon = True
    dog.start()
    print(f"private Inventor pid {pid}, others untouched: {sorted(before)}", flush=True)
    try:
        app.Visible = False
        app.SilentOperation = True
        t0 = time.time()
        while not app.Ready and time.time() - t0 < 180:
            time.sleep(1)
        print("project:", safe(lambda: app.DesignProjectManager.ActiveDesignProject.FullFileName), flush=True)
        yield app
    finally:
        dog.cancel()
        safe(lambda: app.Quit())
        for _ in range(30):
            if pid not in _inventor_pids():
                break
            time.sleep(1)
        else:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        print(f"private Inventor {pid} closed", flush=True)


def _part(app, ps, path, description, body_fn, look=DARK) -> dict:
    part = NativePart(app, ps, description)
    try:
        body_fn(part)
        part.set_appearance(look)
        part.save(path, stl=True)
        return part.report()
    finally:
        part.close()


def y_edges(part: NativePart, points, tol=0.06, min_len=4.0):
    """Edges along y through the given (x, z) points."""
    return part.edges_parallel("y", min_len, lambda x, y, z: any(abs(x - a) < tol and abs(z - b) < tol for a, b in points))


def edges_on_plane_y(part: NativePart, y0: float, rmin: float, tol=0.02):
    """Edges lying in the plane y = y0 and further than rmin from the axis (the outer loop of a cap)."""
    ec = part.app.TransientObjects.CreateEdgeCollection()
    for e in part.body().Edges:
        try:
            a, b = e.StartVertex.Point, e.StopVertex.Point
        except Exception:
            continue
        if abs(a.Y * 10 - y0) < tol and abs(b.Y * 10 - y0) < tol and (a.X ** 2 + a.Z ** 2) ** 0.5 * 10 > rmin:
            ec.Add(e)
    return ec


def flare_cuts(part: NativePart, y_expr: str, length: str, x_side: float) -> None:
    """The waist of the handle: a circle cut into each side, blended into the straight side at +-x_side."""
    p = part.ps
    s = part.sketch_y(y_expr, "flare sketch")
    part.circle(s, "flare_x", "flare_z", "flare_d", "flare +x")
    part.circle(s, "-flare_x", "flare_z", "flare_d", "flare -x")
    part.extrude_toward(s, length, kCut, "waist of the handle", "y", True)
    z = p.flare_z - math.sqrt((p.flare_d / 2) ** 2 - (p.flare_x - x_side) ** 2)
    part.fillet(y_edges(part, [(x_side, z), (-x_side, z)], tol=0.15, min_len=1.5), "r_flare", "blend into the flare")


# ---------------------------------------------------------------------- chassis
def chassis_features(part: NativePart) -> None:
    p = part.ps
    s = part.sketch_y("back_y", "silhouette sketch")
    part.polygon(s, chassis_outline(), "silhouette")
    part.extrude_toward(s, "front_y - back_y", kJoin, "chassis prism (rails, flexure arms, neck, handle)", "y", True)
    part.fillet(y_edges(part, [(p.body_right, -p.nose_z)]), "r_small", "corner of the nose")
    part.fillet(y_edges(part, [(-p.neck_half, p.land_top)]), "r_root", "corner above the near land")
    part.fillet(y_edges(part, [(p.arm_in, p.root_h), (p.arm_in, -p.root_h), (p.body_right, p.root_h), (p.body_right, -p.root_h)]),
                "r_root", "flexure roots")
    flare_cuts(part, "back_y - 1 mm", "front_y - back_y + 2 mm", p.neck_half)
    part.fillet(y_edges(part, [(-p.bar_half, p.top_z), (p.bar_half, p.top_z)], min_len=2.0), "r_bar", "handle corners")
    # front slope of the handle and the back corners that pass the puzzle's corner chamfers
    s = part.sketch_x("-bar_half - 1 mm", "slope sketch")
    part.polygon(s, [("front_y + 1 mm", "slope_z0 - 1 mm"), ("front_y + 1 mm", "top_z + 1 mm"),
                     ("front_y + slope_z0 - top_z - 1 mm", "top_z + 1 mm")], "slope")
    part.extrude_toward(s, "2 * bar_half + 2 mm", kCut, "front slope", "x", True)
    s = part.sketch_z("top_z + 1 mm", "back corner sketch")
    for sx in ("-", ""):
        part.polygon(s, [(f"{sx}(edge_sum + back_y - 1 mm)", "back_y - 1 mm"), (f"{sx}(rail_tip + 3 mm)", "back_y - 1 mm"),
                         (f"{sx}(rail_tip + 3 mm)", "-(edge_sum - rail_tip - 3 mm)")], f"back corner {sx or '+'}")
    part.extrude_toward(s, "top_z + nose_z + 2 mm", kCut, "back corners", "z", False)
    # hood, funnel, lens hole and the camera seat, from the front
    s = part.sketch_y("front_y + 1 mm", "hood sketch")
    part.circle(s, 0, 0, "bore_d", "hood bore")
    part.extrude_toward(s, "front_y + 1 mm - cone_y1", kCut, "hood bore", "y", False)
    s = part.sketch_y("cone_y1", "funnel sketch")
    part.circle(s, 0, 0, "bore_d", "funnel")
    part.extrude(s, "cone_len", kNeg, kCut, "funnel to the lens", taper="-cone_ang")
    part.chamfer(part.circle_edges_at(0, p.front_y, 0, p.bore_d / 2), "seat_c", "seat of the caps' ring")
    s = part.sketch_y("cone_y0 + 1 mm", "lens hole sketch")
    part.circle(s, 0, 0, "lens_hole_d", "lens hole")
    part.extrude_toward(s, "cone_y0 + 1 mm - tube_y1 + 0.5 mm", kCut, "lens hole", "y", False)
    s = part.sketch_y("tube_y1", "ring bore sketch")
    part.circle(s, 0, 0, "tube_bore_d", "ring bore")
    part.extrude_toward(s, "tube_y1 - shoulder_y + 0.5 mm", kCut, "bore of the module's ring", "y", False)
    # board pocket from the back, stepping with the XIAO stack
    s = part.sketch_y("back_y - 1 mm", "main zone sketch")
    part.rect(s, "pocket_x0", "pocket_z0", "pocket_x1", "pocket_z1", "main zone", pin_u0="pocket_x0", pin_u1="pocket_x1",
              pin_v0="pocket_z0", pin_v1="pocket_z1")
    part.extrude_toward(s, "main_zone_y - back_y + 1 mm", kCut, "board pocket, main PCB", "y", True)
    s = part.sketch_y("main_zone_y - 1 mm", "Sense zone sketch")
    part.rect(s, "sense_zone_x0", "sense_zone_z0", "sense_zone_x1", "pocket_z1", "Sense zone", pin_u0="sense_zone_x0", pin_u1="sense_zone_x1",
              pin_v0="sense_zone_z0", pin_v1="pocket_z1")
    part.extrude_toward(s, "sense_front_y - main_zone_y + 1 mm", kCut, "board pocket, Sense PCB (ledges at its front)", "y", True)
    s = part.sketch_y("sense_front_y - 1 mm", "connector zone sketch")
    part.rect(s, "fpc_zone_x0", "sense_zone_z0", "fpc_zone_x1", "fpc_zone_z1", "connector zone", pin_u0="fpc_zone_x0", pin_u1="fpc_zone_x1",
              pin_v0="sense_zone_z0", pin_v1="fpc_zone_z1")
    part.extrude_toward(s, "fpc_zone_y - sense_front_y + 1 mm", kCut, "FPC connector zone", "y", True)
    s = part.sketch_y("sense_front_y - 1 mm", "socket zone sketch")
    part.rect(s, "sd_zone_x0", "fpc_zone_z1 - 0.5 mm", "sd_zone_x1", "slot_z0 + 0.2 mm", "socket zone", pin_u0="sd_zone_x0", pin_u1="sd_zone_x1",
              pin_v0="fpc_zone_z1 - 0.5 mm", pin_v1="slot_z0 + 0.2 mm")
    part.extrude_toward(s, "zone_y - sense_front_y + 1 mm", kCut, "microSD socket and flex zone", "y", True)
    # square seat of the camera block, then the slot of the wedge key right behind it
    s = part.sketch_y("shoulder_y", "camera seat sketch")
    part.rect(s, "-seat_w / 2", "-seat_w / 2", "seat_w / 2", "seat_w / 2", "camera seat", wu="seat_w", sym_u=True, wv="seat_w", sym_v=True)
    part.extrude_toward(s, "shoulder_y - zone_y + 1 mm", kCut, "camera seat", "y", False)
    s = part.sketch_z("slot_z0", "key slot sketch")
    part.polygon(s, [("-body_left - 1 mm", "slot_back_head"), ("slot_x1", "slot_back_tip"), ("slot_x1", "zone_y"), ("-body_left - 1 mm", "zone_y")], "key slot")
    part.extrude_toward(s, "slot_z1 - slot_z0", kCut, "slot of the wedge key, sloped back wall", "z", True)
    s = part.sketch_x("-body_left - 1 mm", "key notch sketch")
    part.rect(s, "key_notch_y - 1.4 mm", "-1.5 mm", "key_notch_y + 0.1 mm", "1.5 mm", "key notch", pin_u0="key_notch_y - 1.4 mm", pin_u1="key_notch_y + 0.1 mm",
              wv="3 mm", sym_v=True)
    part.extrude_toward(s, "4.5 mm", kCut, "notch to lever the key out", "x", True)
    # USB-C channel down through the neck, rabbet and dovetail of the cover
    s = part.sketch_z("top_z + 1 mm", "USB channel sketch")
    part.rect(s, "usb_ch_x0", "cov_in_y - 1 mm", "usb_ch_x1", "usb_ch_y1", "USB channel", pin_u0="usb_ch_x0", pin_u1="usb_ch_x1",
              pin_v0="cov_in_y - 1 mm", pin_v1="usb_ch_y1")
    part.extrude_toward(s, "top_z + 1 mm - pocket_z1 + 0.5 mm", kCut, "USB-C plug channel", "z", False)
    s = part.sketch_y("back_y - 1 mm", "rabbet sketch")
    part.rect(s, "-rab_half", "rab_z0", "rab_half", "top_z + 1 mm", "rabbet", wu="2 * rab_half", sym_u=True, pin_v0="rab_z0", pin_v1="top_z + 1 mm")
    part.extrude_toward(s, "cover_t + 1 mm", kCut, "rabbet of the cover", "y", True)
    s = part.sketch_z("rab_z0 + 1 mm", "dovetail sketch")
    part.polygon(s, [("-dov_out_x0", "back_y - 1 mm"), ("dov_out_x1", "back_y - 1 mm"), ("dov_in_x1", "cov_in_y"), ("-dov_in_x0", "cov_in_y")], "dovetail")
    part.extrude_toward(s, "rab_z0 + 1 mm + dov_z0", kCut, "dovetail of the cover", "z", False)
    s = part.sketch_y("cov_in_y", "insert sketch")
    part.circle(s, "screw_x", "screw_z", "insert_d", "insert hole")
    part.extrude_toward(s, "insert_h", kCut, "hole of the thread insert", "y", True)
    # magnets
    s = part.sketch_y("front_y", "magnet sketch")
    part.circle(s, 0, "mag_z", "mag_pocket_d", "magnet top")
    part.circle(s, 0, "-mag_z", "mag_pocket_d", "magnet bottom")
    part.extrude_toward(s, "mag_pocket_h", kCut, "magnet pockets", "y", False)
    # engraved arrow on the handle: this side faces the beam
    s = part.sketch_z("top_z", "arrow sketch")
    part.polygon(s, [("-13.6 mm", "-10.5 mm"), ("-11.2 mm", "-5.5 mm"), ("-8.8 mm", "-10.5 mm"), ("-11.2 mm", "-9.4 mm")], "arrow", pin=False)
    part.extrude_toward(s, "0.4 mm", kCut, "arrow: the camera looks this way", "z", False)
    # lead-in on the bottom edge, soft edges of the slope, last so that the cuts above see plain planes
    near = lambda v, w: abs(v - w) < 0.1
    part.chamfer(part.edges_parallel("x", 3.0, lambda x, y, z: near(y, p.front_y) and near(z, -p.nose_z)), "lead_c", "lead-in, bottom front edge")
    part.chamfer(part.edges_parallel("z", 5.0, lambda x, y, z: near(y, p.front_y) and near(x, -p.body_left)), "lead_c", "front edge, left wall")
    part.fillet(part.edges_parallel("x", 4.0, lambda x, y, z: abs(y - (p.front_y + p.slope_z0 - p.top_z)) < 0.1 and abs(z - p.top_z) < 0.1),
                "r_slope", "top edge of the slope")
    part.fillet(part.edges_parallel("x", 4.0, lambda x, y, z: abs(y - p.front_y) < 0.1 and abs(z - p.slope_z0) < 0.1), "r_slope", "bottom edge of the slope")


# ---------------------------------------------------------------------- back cover
def cover_features(part: NativePart) -> None:
    s = part.sketch_z("-cov_z0", "cover sketch")
    part.polygon(s, [("-cov_x0", "back_y"), ("cov_x1", "back_y"), ("cov_in_x1", "cov_in_y"), ("-cov_in_x0", "cov_in_y")], "cover section")
    part.extrude_toward(s, "cov_z0 + rab_z0 + 1 mm", kJoin, "lower part in the dovetail", "z", True)
    s = part.sketch_y("back_y", "upper cover sketch")
    part.rect(s, "-rab_w", "rab_z0", "rab_w", "top_z", "upper part", wu="2 * rab_w", sym_u=True, pin_v0="rab_z0", pin_v1="top_z")
    part.extrude_toward(s, "cover_t", kJoin, "upper part on the neck", "y", True)
    flare_cuts(part, "back_y - 1 mm", "cover_t + 2 mm", part.ps.rab_w)
    s = part.sketch_y("back_y - 1 mm", "tongue sketch")
    for sg in ("-", "+"):
        c = f"usb_x {sg} ton_c"
        part.polygon(s, [(f"{c} - tongue_w / 2 - slit_w", "ton_z1"), (f"{c} - tongue_w / 2 - slit_w", "ton_z0 - slit_w"),
                         (f"{c} + tongue_w / 2 + slit_w", "ton_z0 - slit_w"), (f"{c} + tongue_w / 2 + slit_w", "ton_z1"),
                         (f"{c} + tongue_w / 2", "ton_z1"), (f"{c} + tongue_w / 2", "ton_z0"),
                         (f"{c} - tongue_w / 2", "ton_z0"), (f"{c} - tongue_w / 2", "ton_z1")], f"tongue {sg}")
    part.extrude_toward(s, "cover_t + 2 mm", kCut, "spring tongues (the slits are the vents)", "y", True)
    s = part.sketch_y("cov_in_y", "bump sketch")
    for sg in ("-", "+"):
        c = f"usb_x {sg} ton_c"
        part.rect(s, f"{c} - 1.5 mm", "ton_z0 + 0.6 mm", f"{c} + 1.5 mm", "ton_z0 + 2.6 mm", f"bump {sg}", pin_u0=f"{c} - 1.5 mm", pin_u1=f"{c} + 1.5 mm",
                  pin_v0="ton_z0 + 0.6 mm", pin_v1="ton_z0 + 2.6 mm")
    part.extrude_toward(s, "bump_y - cov_in_y", kJoin, "bumps on the main PCB", "y", True)
    s = part.sketch_y("back_y - 1 mm", "screw sketch")
    part.circle(s, "screw_x", "screw_z", "clear_d", "M3 clearance")
    part.extrude_toward(s, "cover_t + 2 mm", kCut, "M3 clearance", "y", True)
    s = part.sketch_y("back_y", "countersink sketch")
    part.circle(s, "screw_x", "screw_z", "csk_d", "countersink")
    part.extrude(s, "csk_h", 20993, kCut, "countersink", taper="-cone_ang")


# ---------------------------------------------------------------------- wedge key
def key_features(part: NativePart) -> None:
    s = part.sketch_z("key_z0", "key sketch")
    part.polygon(s, [("-key_x0", "key_back_head"), ("key_x1", "key_back_tip"), ("key_x1", "key_front_y"), ("-key_x0", "key_front_y")], "key")
    part.extrude_toward(s, "key_h", kJoin, "wedge key", "z", True)


# ---------------------------------------------------------------------- caps
def cap_base(part: NativePart) -> None:
    s = part.sketch_y("cap_back_y", "cap sketch")
    part.rect(s, "-cap_w", "-cap_h", "cap_w", "cap_h", "cap", wu="2 * cap_w", sym_u=True, wv="2 * cap_h", sym_v=True)
    part.extrude_toward(s, "cap_t", kJoin, "cap", "y", True)
    part.fillet(part.edges_parallel("y", 1.0), "cap_w - 0.02 mm", "round ends")
    s = part.sketch_y("cap_back_y", "ring sketch")
    part.circle(s, 0, 0, "ring_d0", "ring")
    part.extrude(s, "ring_h", kNeg, kJoin, "centring ring", taper="-cone_ang")


def cap_magnets(part: NativePart) -> None:
    s = part.sketch_y("cap_back_y", "cap magnet sketch")
    part.circle(s, 0, "mag_z", "mag_pocket_d", "magnet top")
    part.circle(s, 0, "-mag_z", "mag_pocket_d", "magnet bottom")
    part.extrude_toward(s, "mag_pocket_h", kCut, "magnet pockets", "y", True)


def cap_edge(part: NativePart) -> None:
    p = part.ps
    part.chamfer(edges_on_plane_y(part, p.screen_out_y, p.cap_w - 1.0), "cap_edge", "front edge")


def screen_features(part: NativePart) -> None:
    cap_base(part)
    s = part.sketch_y("ring_tip_y - 1 mm", "cap bore sketch")
    part.circle(s, 0, 0, "cap_bore_d", "cap bore")
    part.extrude_toward(s, "screen_in_y - ring_tip_y + 1 mm", kCut, "bore up to the screen", "y", True)
    cap_magnets(part)
    cap_edge(part)
    s = part.sketch_y("screen_out_y", "target sketch")
    w = "groove_w / 2"
    part.rect(s, "groove_r", f"-{w}", "rib_r1 + 1.5 mm", w, "groove +x", wv="groove_w", sym_v=True, pin_u0="groove_r", pin_u1="rib_r1 + 1.5 mm")
    part.rect(s, "-rib_r1 - 1.5 mm", f"-{w}", "-groove_r", w, "groove -x", wv="groove_w", sym_v=True, pin_u0="-rib_r1 - 1.5 mm", pin_u1="-groove_r")
    part.rect(s, f"-{w}", "groove_r", w, "rib_r1 + 1.5 mm", "groove +z", wu="groove_w", sym_u=True, pin_v0="groove_r", pin_v1="rib_r1 + 1.5 mm")
    part.rect(s, f"-{w}", "-rib_r1 - 1.5 mm", w, "-groove_r", "groove -z", wu="groove_w", sym_u=True, pin_v0="-rib_r1 - 1.5 mm", pin_v1="-groove_r")
    part.extrude_toward(s, "groove_h", kCut, "target: crosshair for the eye", "y", False)
    s = part.sketch_y("screen_out_y", "target ring sketch")
    part.circle(s, 0, 0, "groove_d1", "ring outer")
    part.circle(s, 0, 0, "groove_d0", "ring inner")
    part.extrude_toward(s, "groove_h", kCut, "target: ring", "y", False)
    s = part.sketch_y("screen_in_y", "reticle sketch")
    part.rect(s, "rib_r0", "-rib_w / 2", "rib_r1", "rib_w / 2", "rib +x", wv="rib_w", sym_v=True, pin_u0="rib_r0", pin_u1="rib_r1")
    part.rect(s, "-rib_r1", "-rib_w / 2", "-rib_r0", "rib_w / 2", "rib -x", wv="rib_w", sym_v=True, pin_u0="-rib_r1", pin_u1="-rib_r0")
    part.rect(s, "-rib_w / 2", "rib_r0", "rib_w / 2", "rib_r1", "rib +z", wu="rib_w", sym_u=True, pin_v0="rib_r0", pin_v1="rib_r1")
    part.rect(s, "-rib_w / 2", "-rib_r1", "rib_w / 2", "-rib_r0", "rib -z", wu="rib_w", sym_u=True, pin_v0="-rib_r1", pin_v1="-rib_r0")
    part.extrude_toward(s, "rib_h", kJoin, "reticle ribs (open at the centre)", "y", False)
    s = part.sketch_y("screen_in_y", "tick sketch")
    w = "rib_w / 2"
    for sg in ("", "-"):
        part.rect(s, f"{sg}(tick_r - {w})", "-tick_l", f"{sg}(tick_r + {w})", "tick_l", f"tick {sg}x", wv="2 * tick_l", sym_v=True,
                  pin_u0=f"{sg}(tick_r - {w})", pin_u1=f"{sg}(tick_r + {w})")
        part.rect(s, "-tick_l", f"{sg}(tick_r - {w})", "tick_l", f"{sg}(tick_r + {w})", f"tick {sg}z", wu="2 * tick_l", sym_u=True,
                  pin_v0=f"{sg}(tick_r - {w})", pin_v1=f"{sg}(tick_r + {w})")
    part.rect(s, "0.8 mm", "rib_r1 - 1.2 mm", "2.4 mm", "rib_r1 - 1.2 mm + rib_w", "up mark", pin_u0="0.8 mm", pin_u1="2.4 mm",
              pin_v0="rib_r1 - 1.2 mm", pin_v1="rib_r1 - 1.2 mm + rib_w")
    part.extrude_toward(s, "rib_h", kJoin, "ticks at +-tick_r and the mark for up", "y", False)


def ndcap_features(part: NativePart) -> None:
    cap_base(part)
    s = part.sketch_y("ring_tip_y - 1 mm", "filter pocket sketch")
    part.circle(s, 0, 0, "nd_d + nd_clr", "filter pocket")
    part.extrude_toward(s, "screen_out_y - nd_wall - ring_tip_y + 1 mm", kCut, "filter pocket", "y", True)
    s = part.sketch_y("screen_out_y + 1 mm", "window sketch")
    part.circle(s, 0, 0, "nd_win_d", "window")
    part.extrude_toward(s, "nd_wall + 2 mm", kCut, "window", "y", False)
    cap_magnets(part)
    cap_edge(part)
    s = part.sketch_y("screen_out_y - nd_wall", "pad sketch")
    part.rect(s, "nd_win_d / 2 + 0.2 mm", "-3 mm", "nd_d / 2 + 1 mm", "3 mm", "pad", pin_u0="nd_win_d / 2 + 0.2 mm", pin_u1="nd_d / 2 + 1 mm", wv="6 mm", sym_v=True)
    part.extrude_toward(s, "nd_pad", kJoin, "pad: tilts the filter", "y", False)


PART_SPECS = {
    "chassis": ("Beam target for the XIAO ESP32-S3 Sense, chassis: slides into an openUC2 cube, two rigid rails on -x seat on the 45 deg edge chamfers "
                "(x, z); two long flexure arms on +x press on the throat walls, two lands on -x limit the roll. Camera block in a square seat, "
                "XIAO from the back, USB-C from the top. PETG, print on the front face, no supports.", chassis_features, DARK),
    "cover": ("Back cover: slides down in the dovetail, tongues press the XIAO forward, the slits are the vents. One M3 x 10 into a Ruthex insert. "
              "Print on the back face.", cover_features, DARK),
    "key": ("Wedge key: pushed in from the side between the camera module and the USB-C shell, clamps the module into its seat. "
            "Print on its side.", key_features, ORANGE),
    "screen": ("Screen cap: 0.6 mm printed white screen with a reticle on the inner face, cone-centred, two 8x3 magnets. Print on the screen, white.",
               screen_features, WHITE),
    "ndcap": ("ND cap for the bare chip: filter D12.7 tilted by a pad, same seat and magnets. Print on the front.", ndcap_features, GREY),
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


def _turn(R, v):
    return tuple(sum(R[j][i] * v[j] for j in range(3)) for i in range(3))


def placements(ps: ParamSet, files: dict, side: bool) -> list[tuple]:
    p = ps
    xiao_o = (p.cam_bz, p.sensor_y - p.sensor_by, -p.cam_bx)
    tool = [
        ("chassis", files["chassis"], (0, 0, 0), I3),
        ("back cover", files["cover"], (0, 0, 0), I3),
        ("wedge key", files["key"], (0, 0, 0), I3),
        ("screen cap", files["screen"], (0, 0, 0), I3),
        ("XIAO ESP32-S3 Sense", files["xiao"], xiao_o, XIAO_COLS),
        ("thread insert", files["insert"], (p.screw_x, p.cov_in_y, p.screw_z), I3),
        ("M3 screw", files["screw"], (p.screw_x, p.back_y, p.screw_z), SCREW_Y),
    ]
    yc = p.front_y - p.mag_pocket_h + p.mag_t / 2 + p.mag_sink
    ys = p.cap_back_y + p.mag_pocket_h - p.mag_t / 2 - p.mag_sink
    for tag, z in (("top", p.mag_z), ("bottom", -p.mag_z)):
        tool.append((f"magnet chassis {tag}", files["magnet"], (0, yc, z), MAG_Y))
        tool.append((f"magnet cap {tag}", files["magnet"], (0, ys, z), MAG_Y))
    if side:
        tool = [(role, f, _turn(SIDE, o), tuple(_turn(SIDE, c) for c in cols)) for role, f, o, cols in tool]
    return [("cube", files["cube"], (0, 0, 0), I3), ("puzzle piece on top", files["puzzle"], (0, 0, p.cube_half + 0.1 + 30.0), I3)] + tool


def build_assembly(app, ps: ParamSet, files: dict, path: Path, side: bool) -> dict:
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
        for role, f, origin, cols in placements(ps, files, side):
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
                if {a, c} == {"cube", "puzzle piece on top"}:
                    continue
                vol, boxes = interference(app, cd, occ[a], occ[c])
                if vol:
                    rep["interference_mm3"][f"{a} / {c}"] = {"mm3": vol, "boxes": boxes[:4]}
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
    files.update({k: PARTS[k] for k in ("cube", "puzzle", "xiao", "magnet", "insert", "screw")})
    rep = {"names": NAMES, "files": {k: str(v) for k, v in files.items()}}
    for key, (desc, fn, look) in PART_SPECS.items():
        if only and key not in only:
            continue
        print(f"\n== {files[key].name}")
        rep[key] = _part(app, ps, files[key], desc, fn, look)
        print(json.dumps({k: v for k, v in rep[key].items() if k != "range_mm"}, indent=1))
        print("range", rep[key].get("range_mm"))
    if do_assembly:
        for side, name in ((False, NAMES["assembly"]), (True, NAMES["assembly"] + " - side entry")):
            asm = INV_DIR / f"{name}.iam"
            print(f"\n== {asm.name}")
            r = build_assembly(app, ps, files, asm, side)
            rep["side" if side else "top"] = r
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
    ap.add_argument("--live-session", action="store_true", help="use the running Inventor instead of a private hidden one")
    a = ap.parse_args()
    with (session() if a.live_session else private_session()) as app:
        overrides = {}
        if a.from_ipt:
            known = make_params().items
            overrides.update({k: v for k, v in read_user_parameters(app, Path(a.from_ipt)).items()
                              if k in known and not known[k].derived})
        overrides.update(overrides_from(a))
        build(app, make_params(overrides), set(a.only) if a.only else None, not a.no_assembly)


if __name__ == "__main__":
    main()
