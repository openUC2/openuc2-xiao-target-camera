"""XIAO ESP32-S3 Sense beam target for the openUC2 cube - parameters and design checks (no Inventor).

    python xiao_target.py                          # table + checks + optics + flexure numbers
    python xiao_target.py --set screen_d=21 --set arm_t=1.2

Cube frame: cube centre at the origin, z up, the beam along y coming from +y, the camera looking
toward +y. The target slides through a port and locates on the cube's 45 deg edge chamfers
(|x| + |z| = 38), so it works from the top with or without a puzzle piece and, turned 90 deg about
the beam, from the side. Two rigid rails on -x sit in the chamfers like a V block and fix x and z. A
contact on a chamfer pushes through the axis (lever 1.4 mm), so it cannot stop a rotation about the
beam: two rigid lands on -x stand 0.05-0.1 mm off the -x throat walls (lever 22 mm) and limit the roll.
Two long flexure arms on +x end in a ridge that drops into the corner between the +x chamfer and the
throat wall, the only groove a cube has: they load the V and give the click. The far rail stands taller than
the near one, and the stick's +x shoulder enters the near throat when the tool overshoots: the tool cannot shift
far enough for the far rail to pass the far throat, a hard stop that needs no face outside the cube (top with
puzzle piece = side). The same table drives build_xiao_target.py and check_xiao_target.py.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from cadlib.params import D, P, ParamSet, parse_sets  # noqa: E402

INV_DIR = HERE / "INVENTOR"
STL_DIR = HERE / "stl"
NAMES = {
    "assembly": "ASS - 9039 - CAMTARXIA - V04",
    "chassis": "PRT - 9040 - CAMTARXIA - V04",
    "cover": "PRT - 9041 - CAMTARCOV - V04",
    "key": "PRT - 9033 - CAMTARKEY - V04",
    "screen": "PRT - 9034 - CAMTARSCR - V04",
    "ndcap": "PRT - 9035 - CAMTARNDF - V04",
}
CADNEW = Path(r"C:\Users\benir\Documents\openUC2-CAD-new\workspace")
XIAO_DIR = CADNEW / "BUY" / "OLD STUFF" / "BUY - Seeed Studio XIAO-ESP32-S3-Sense" / "BUY - Seeed Studio XIAO-ESP32-S3-Sense"
PARTS = {
    "cube": CADNEW / "ASS" / "ASS - 2000 - CUB - V04.iam",
    "puzzle": CADNEW / "PRT" / "PRT - 1004 - PUZ11 - V04 - A.ipt",
    "xiao": XIAO_DIR / "BUY - Seeed Studio XIAO-ESP32-S3-Sense.iam",
    "magnet": CADNEW / "BUY" / "BUY - NeFeB-Magnet - ø8x3 N40 Ni.ipt",
    "insert": CADNEW / "BUY" / "BUY - Ruthex - Thread insert - RX-M3Sx4.0.ipt",
    "screw": CADNEW / "STD" / "ISO 10642 - A2-70" / "ISO 10642 - Countersunk head screw with hex socket - M3 x 10 - A2-70.ipt",
    "lock_screw": CADNEW / "STD" / "ISO 4672 - A2-70" / "ISO 4762 - Cylinder head screw with hex socket - M3 x 8 - A2-70.ipt",
}


def parameters() -> list:
    return [
        # ---- cube ASS-2000 (measured on the STEP, all 12 edges alike)
        P("cube_half", 24.9, comment="cube body half size"),
        P("cham_sum", 38.0, comment="45 deg edge chamfers lie on |a| + |b| = cham_sum"),
        P("throat", 17.03, comment="half width of the port throat (walls +-17.03)"),
        P("throat_z0", 20.97, comment="inner end of the throat, where the chamfer starts"),
        P("cham_x1", 21.0, comment="other end of the chamfer"),
        P("notch_x", 17.92, comment="the notches cut the chamfer back to here (top and bottom ports, x walls only)"),
        P("puz_t", 5.0, comment="PUZ11 puzzle piece on top of the cube"),
        P("puz_half", 17.25, comment="PUZ11 opening half width"),
        P("puz_cor", 2.0, comment="PUZ11 opening corner chamfer"),
        # ---- XIAO ESP32-S3 Sense model (vendor frame bx, by, bz; camera looks +by)
        P("cam_bx", 8.75, comment="camera axis in the vendor frame (bx, bz)"),
        P("cam_bz", -6.75, comment=""),
        P("sensor_by", 8.6, comment="sensor plane (ASSUMED: module back 7.95 + 0.65) - measure"),
        P("pcb_back_by", -0.25, comment="back of the main PCB"),
        P("pcb_front_by", 1.0, comment="front of the main PCB"),
        P("sense_back_by", 3.93, comment="back of the Sense PCB"),
        P("sense_front_by", 5.18, comment="front of the Sense PCB"),
        P("fpc_front_by", 7.18, comment="front of the FPC connector"),
        P("sd_front_by", 7.78, comment="front of the microSD socket"),
        P("usb_front_by", 4.21, comment="front of the USB-C shell"),
        P("mod_w", 8.0, comment="camera module, square block"),
        P("mod_back_by", 7.95, comment="back of the module = its PCB"),
        P("mod_front_by", 10.05, comment="front of the square block"),
        P("tube_d", 7.85, comment="lens holder ring on the block"),
        P("tube_by1", 11.95, comment="front of the ring"),
        P("lens_tip_by", 13.71, comment="lens nose with the lens screwed in"),
        P("lens_d", 6.32, comment="largest lens diameter"),
        P("main_bx0", -8.67, comment="main PCB, lower end"),
        P("main_bx1", 12.28, comment="main PCB, upper end"),
        P("sense_bx0", -8.97, comment="Sense PCB, lower end"),
        P("sense_bx1", 5.7, comment="Sense PCB, upper end"),
        P("main_bz0", -15.0, comment="main PCB edges across"),
        P("main_bz1", 2.78, comment=""),
        P("sense_bz0", -14.5, comment="Sense PCB edges across"),
        P("sense_bz1", 2.28, comment=""),
        P("sd_bz0", -12.52, comment="microSD socket and card across"),
        P("sd_bz1", -0.68, comment=""),
        P("fpc_bx1", -2.2, comment="FPC connector with the flex stiffener, upper end"),
        P("fpc_bz0", -14.18, comment="FPC connector across"),
        P("fpc_bz1", 2.02, comment=""),
        P("usb_bz1", -1.65, comment="USB-C shell, left edge seen from the front"),
        P("usb_bx1", 13.81, comment="USB-C mouth"),
        P("usb_bz", -6.12, comment="USB-C receptacle centre"),
        P("usb_by", 2.11, comment=""),
        # ---- tool frame: stations along the beam
        P("sensor_y", -4.5, comment="sensor plane; everything is built around it so that sensor, lens and screen go through the port together"),
        P("back_y", -16.8, comment="back face of the target"),
        P("front_y", 12.2, comment="front face of the chassis (printed on the bed)"),
        P("cover_t", 2.2, comment="back cover"),
        # ---- rigid rails and lands on -x, flexure arms on +x
        P("rail_tip", 18.0, comment="tip of the near rail; the flat of each rail lies on the chamfer between here and body_top"),
    P("rail_far", 18.4, comment="tip of the far rail: taller, so that it bites on the far chamfer even with the tool shifted to the stop"),
        P("cham_gap", 0.02, comment="rail flat to chamfer in the model (contact in reality)"),
        P("body_left", 16.7, comment="left wall of the chassis"),
        P("body_right", 11.6, comment="right wall of the chassis; the arms' free space is outside it"),
        P("body_top", 20.9, comment="top of the body, just below the throat"),
        P("body_bot", 20.9, comment="bottom of the body"),
        P("nose_z", 24.4, comment="the nose reaches into the far throat; ends inside the cube's envelope"),
        P("land_gap", 0.08, comment="rigid lands on -x to the -x throat walls, per side: limits the roll, the V keeps the contact"),
        P("land_top", 23.4, comment="upper end of the near land, just under the waist cut"),
        P("land_lead", 0.8, comment="lead-in at the nose"),
        P("relief_x", 16.6, comment="relief around the throat's lip, between rail flat and land (printed corners are round)"),
        P("relief_z", 21.3, comment=""),
        P("pad_over", 1.2, comment="free pad ridge stands this far past its seat on the chamfer (its preload travel)"),
        P("pad_z", 20.65, comment="height of the pad ridge: on the +x chamfer, just below its corner with the throat wall"),
        P("pad_end", 22.4, comment="tip of the near arm"),
        P("pad_far_end", 24.2, comment="tip of the far arm: its long slope leads the tool through the near throat"),
        P("pad_lead", 3.0, comment="length of the ridge's slopes"),
        P("pad_in", 15.7, comment="inner face of the pad, beside the neck"),
        P("pad_in_z0", 19.0, comment="the arm thickens into the pad between here and pad_in_z0 + 0.7"),
        P("arm_out", 16.5, comment="outer face of the flexure arms"),
        P("arm_t", 1.4, comment="flexure arm thickness"),
        P("root_h", 1.5, comment="half height of the block carrying both arms"),
        P("edge_sum", 33.1, comment="back corners cut along |x| + |y| = edge_sum to pass the puzzle's corner chamfers"),
        # ---- neck and handle
        P("neck_half", 13.0, comment="neck half width"),
        P("shoulder_z", 21.4, comment="right shoulder above the upper pad"),
        P("bar_half", 16.1, comment="half width of the stick; its +x side is the hard stop in the near throat"),
        P("stop_z", 24.2, comment="lower end of the stick's full width, above the lip while the near rail still needs the throat"),
        P("stop_lead", 1.0, comment="45 deg lead below stop_z"),
        P("stick_sum", 31.4, comment="back corners of the stick cut along |x| + |y| = stick_sum: passes the puzzle's corner chamfers shifted"),
        P("stick_front", -2.8, comment="front face of the stick behind the slope"),
        P("flare_d", 15.0, comment="circle cut into each side of the stick: a waist with finger undercuts"),
        P("flare_x", 19.5, comment="centre of that circle (waist half width = flare_x - flare_d / 2)"),
        P("flare_z", 57.0, comment="centre height: the grip, well above a puzzle piece"),
        P("top_z", 70.0, comment="top of the stick"),
        P("cover_top", 31.5, comment="the cover ends here: above it the USB channel is open at the back (the plug and the cable go in from there)"),
        P("slope_z0", 23.0, comment="the front slope starts here on the front face (45 deg, prints without support)"),
        # ---- camera seat
        P("seat_clr", 0.2, comment="camera module in its square seat, per side"),
        P("tube_clr", 0.4, comment="ring in its bore, on the diameter"),
        P("lens_hole_d", 6.9, comment="bore of the lens tube: the lens, screwed out of the module entirely, slides in it"),
        P("lens_tube_d", 8.9, comment="outer diameter of the lens tube (1 mm wall), it stands free in the funnel"),
        P("lens_tube_y", 5.0, comment="front end of the lens tube"),
        P("jaw_y0", 1.0, comment="root of the jaw cut into the -x side of the tube"),
        P("jaw_z", 1.7, comment="the two slits beside the jaw, centres at z +-jaw_z"),
        P("jaw_slit", 0.8, comment="slit width"),
        P("lock_y", 2.6, comment="lock screw M3 x 8 ISO 4762 through the -x wall, presses the jaw on the lens"),
        P("lock_floor", 11.85, comment="floor of the head recess, |x|; the thread insert starts here"),
        P("lock_head_d", 6.4, comment="head recess"),
        P("lock_l", 8.0, comment="length under the head"),
        P("bore_d", 20.0, comment="hood bore in front of the lens"),
        P("cone_ang", 45.0, "deg", comment="funnel from the lens hole to the hood bore (prints without support)"),
        P("r_bar", 1.0, comment="handle corners"),
        P("r_flare", 6.0, comment="blend from the neck into the flare"),
        P("lead_c", 1.0, comment="lead-in chamfer on the bottom edges"),
        P("r_small", 1.5, comment="silhouette corners"),
        P("r_root", 0.8, comment="flexure roots"),
        P("r_slope", 2.5, comment="edges of the front slope"),
        P("seat_c", 0.5, comment="chamfer at the hood bore; the caps' ring centres on it"),
        # ---- board pocket (the XIAO stack is clamped: main PCB back on the cover's tongues, Sense PCB front on two ledges)
        P("clr_board", 0.5, comment="clearance around the PCBs"),
        P("zone_clr", 0.5, comment="clearance around the socket and the connector"),
        P("flex_gap", 0.75, comment="front of the socket zone: free for the flex in front of the module's back plane"),
        P("usb_ch_w", 13.6, comment="USB-C plug channel (x)"),
        P("usb_ch_t", 7.2, comment="USB-C plug channel (y)"),
        # ---- wedge key behind the camera module (no microSD card in this tool)
        P("key_gap", 0.05, comment="key to the USB-C shell"),
        P("key_h", 7.2, comment="key height"),
        P("key_clr", 0.15, comment="key in its slot, per side (z)"),
        P("key_slope", 0.0833, "ul", comment="wedge slope of the key's BACK face (1:12, self-locking); the front stays parallel to the module"),
        P("key_press", 0.05, comment="key presses the module by this in its nominal position"),
        P("key_blind", 2.0, comment="slot runs this far into the right wall"),
        P("key_sink", 1.5, comment="nominal key head under the left wall: 0.12 mm of stack tolerance before it stands proud"),
        # ---- back cover
        P("low_x0", 12.0, comment="the cover sits in a recess of the back: lower part, left edge"),
        P("low_x1", 10.3, comment="lower part, right edge"),
        P("rab_x0", 14.05, comment="upper part, left edge"),
        P("rab_x1", 13.0, comment="upper part, right edge"),
        P("rab_z0", 22.0, comment="start of the upper part"),
        P("cov_clr", 0.3, comment="cover in its recess, per side"),
        P("tongue_w", 5.0, comment="spring tongues of the cover"),
        P("tongue_l", 11.0, comment=""),
        P("ton_c", 4.6, comment="tongue centres at usb_x +- ton_c"),
        P("ton_z1", -1.0, comment="tongue roots"),
        P("slit_w", 1.2, comment="slits around the tongues (also the vents)"),
        P("bump_press", 0.1, comment="tongue bumps press the main PCB by this"),
        P("screw_x", 9.3, comment="M3 screw 1, cover into the neck, right of the USB channel"),
        P("screw_x2", 10.2, comment="M3 screw 2, left of the USB channel, at x = -screw_x2"),
        P("screw_z", 27.0, comment="height of screws 1 and 2"),
        P("screw_z3", 20.9, comment="M3 screw 3 in the nose below the board, at z = -screw_z3, on the USB axis"),
        P("insert_d", 4.0, comment="hole for the Ruthex M3 insert"),
        P("insert_h", 8.2, comment="deep enough for the M3 x 10 tip"),
        P("csk_d", 6.4, comment="countersink"),
        P("clear_d", 3.4, comment="M3 clearance"),
        # ---- caps (magnets 8 x 3)
        P("mag_d", 8.0, comment="NdFeB magnet 8 x 3"),
        P("mag_t", 3.0, comment=""),
        P("mag_fit", 0.2, comment="magnet pocket oversize (FDM, glue the magnets)"),
        P("mag_sink", 0.4, comment="magnet sits this far under the face (sets the pull of the caps)"),
        P("mag_z", 15.5, comment="magnets at z = +-mag_z"),
        P("cap_w", 11.0, comment="cap half width"),
        P("cap_h", 20.0, comment="cap half height"),
        P("cap_gap", 0.1, comment="cap back to the chassis front: the cone seats first"),
        P("ring_h", 0.6, comment="centring ring on the cap's back"),
        P("cap_bore_d", 18.4, comment="clear bore of the cap"),
        P("scr_t", 0.6, comment="printed screen (white PETG, 3 layers, printed on the bed)"),
        P("screen_d", 20.0, comment="screen (inner face) distance from the sensor"),
        P("cap_edge", 0.6, comment="chamfer around the cap's front"),
        P("rib_w", 0.45, comment="reticle ribs on the inner face of the screen (one line wide)"),
        P("rib_h", 0.35, comment=""),
        P("groove_w", 0.5, comment="target engraved on the front of the screen, for the eye"),
        P("groove_h", 0.2, comment="one layer deep"),
        P("groove_r", 5.0, comment="engraved ring radius"),
        P("rib_r0", 1.5, comment="reticle is open inside this radius (the beam centre)"),
        P("rib_r1", 8.0, comment="reticle reaches this radius"),
        P("tick_l", 1.6, comment="ticks across the reticle at +-tick_r"),
        P("tick_r", 5.0, comment=""),
        P("nd_d", 12.7, comment="ND filter diameter"),
        P("nd_clr", 0.2, comment="filter in its pocket (diameter)"),
        P("nd_t", 2.5, comment="filter thickness, up to"),
        P("nd_win_d", 10.0, comment="window of the ND cap"),
        P("nd_pad", 0.7, comment="pad under one side of the filter: tilts it ~3.5 deg"),
        P("nd_wall", 0.8, comment="ND cap front wall"),
        # ---- optics (assumptions)
        P("lens_f", 3.5, comment="XIAO Sense lens focal length (ASSUMED) - measure"),
        P("sensor_w", 3.52, comment="OV2640 active area 1600 x 1200 x 2.2 um"),
        P("sensor_h", 2.64, comment=""),
        # ---- material for the flexure estimate
        P("arm_e", 2100.0, "ul", comment="Young's modulus of the arms in MPa (PETG; PLA ~3500, Tough 2000 ~2200)"),
        P("mu_est", 0.25, "ul", comment="friction estimate"),
        # ---- derived: XIAO in the tool (x = cam_bz - bz, y = by + ofs_y, z = bx - cam_bx)
        D("ofs_y", "sensor_y - sensor_by", comment="vendor by -> tool y"),
        D("main_x0", "cam_bz - main_bz1"),
        D("main_x1", "cam_bz - main_bz0"),
        D("sense_x0", "cam_bz - sense_bz1"),
        D("sense_x1", "cam_bz - sense_bz0"),
        D("main_z0", "main_bx0 - cam_bx"),
        D("main_z1", "main_bx1 - cam_bx"),
        D("sense_z0", "sense_bx0 - cam_bx"),
        D("sense_z1", "sense_bx1 - cam_bx", comment="the Sense PCB ends below the module: that gap takes the key"),
        D("sd_x0", "cam_bz - sd_bz1"),
        D("sd_x1", "cam_bz - sd_bz0"),
        D("fpc_x0", "cam_bz - fpc_bz1"),
        D("fpc_x1", "cam_bz - fpc_bz0"),
        D("fpc_z1", "fpc_bx1 - cam_bx"),
        D("usb_x", "cam_bz - usb_bz"),
        D("usb_y", "usb_by + ofs_y"),
        D("usb_z1", "usb_bx1 - cam_bx", comment="USB-C mouth (points up)"),
        D("pcb_back_y", "pcb_back_by + ofs_y"),
        D("pcb_front_y", "pcb_front_by + ofs_y"),
        D("sense_back_y", "sense_back_by + ofs_y"),
        D("sense_front_y", "sense_front_by + ofs_y", comment="the two ledges under the Sense PCB"),
        D("fpc_front_y", "fpc_front_by + ofs_y"),
        D("usb_front_y", "usb_front_by + ofs_y"),
        D("mod_back_y", "mod_back_by + ofs_y", comment="the key bears here"),
        D("mod_front_y", "mod_front_by + ofs_y", comment="the block stops here on the seat floor"),
        D("tube_front_y", "tube_by1 + ofs_y"),
        D("lens_tip_y", "lens_tip_by + ofs_y"),
        # ---- derived: rails and pads
        D("rail_z", "cham_sum - cham_gap - rail_tip", comment="rail tip height"),
        D("rail_end_x", "cham_sum - cham_gap - body_top", comment="inner end of the rail flat"),
        D("rail_ramp_z", "rail_z - (rail_tip - body_left)"),
        D("rail_far_z", "cham_sum - cham_gap - rail_far", comment="far rail tip height"),
        D("rail_far_ramp", "rail_far_z - (rail_far - body_left)"),
        D("slope_z1", "slope_z0 + front_y - stick_front", comment="the slope ends on the stick's front face"),
        D("land_x", "throat - land_gap", comment="rigid lands on -x"),
        D("relief_end", "relief_z + (land_x - relief_x)"),
        D("pad_seat", "cham_sum - pad_z", comment="pad ridge seated on the chamfer"),
        D("pad_tip", "pad_seat + pad_over", comment="pad ridge, free"),
        D("pad_low_z", "pad_z - pad_lead", comment="lower end of the ridge's slope"),
        D("arm_in", "arm_out - arm_t"),
        D("pad_in_z1", "pad_in_z0 + 0.7 mm"),
        # ---- derived: stations
        D("cov_in_y", "back_y + cover_t", comment="inner face of the cover"),
        D("main_zone_y", "pcb_front_y + 1.4 mm", comment="main PCB zone ends here"),
        D("zone_y", "mod_back_y + flex_gap", comment="front of the socket zone, also front of the key slot"),
        D("fpc_zone_y", "fpc_front_y + 0.2 mm", comment="front of the connector zone"),
        D("key_y0", "usb_front_y + key_gap", comment="back of the key slot"),
        D("seat_w", "mod_w + 2 * seat_clr"),
        D("shoulder_y", "mod_front_y", comment="seat floor"),
        D("tube_bore_d", "tube_d + tube_clr"),
        D("tube_y1", "tube_front_y + 0.15 mm", comment="ring bore ends here"),
        D("cone_y0", "tube_y1 + 0.9 mm", comment="funnel starts at the lens hole"),
        D("cone_len", "(bore_d - lens_hole_d) / 2", comment="funnel length at 45 deg"),
        D("cone_y1", "cone_y0 + cone_len", comment="funnel ends at the hood bore"),
        D("screen_in_y", "sensor_y + screen_d"),
        D("screen_out_y", "screen_in_y + scr_t"),
        D("cap_back_y", "front_y + cap_gap"),
        D("cap_t", "screen_out_y - cap_back_y"),
        D("seat_r", "bore_d / 2 + seat_c"),
        D("ring_r0", "seat_r + cap_gap", comment="ring base radius"),
        D("ring_d0", "2 * ring_r0"),
        D("ring_tip_y", "cap_back_y - ring_h"),
        D("groove_d1", "2 * groove_r + groove_w"),
        D("groove_d0", "2 * groove_r - groove_w"),
        D("mag_pocket_d", "mag_d + mag_fit"),
        D("mag_pocket_h", "mag_t + mag_sink"),
        # ---- derived: board pocket
        D("pocket_x0", "main_x0 - clr_board"),
        D("pocket_x1", "main_x1 + clr_board"),
        D("pocket_z0", "main_z0 - clr_board - 0.3 mm", comment="main PCB rests here; USB-C insertion loads this floor"),
        D("pocket_z1", "main_z1 + clr_board", comment="main PCB stops here when a plug is pulled"),
        D("sense_zone_x0", "sense_x0 - clr_board"),
        D("sense_zone_x1", "sense_x1 + clr_board"),
        D("sense_zone_z0", "sense_z0 - clr_board"),
        D("sd_zone_x0", "sd_x0 - zone_clr"),
        D("sd_zone_x1", "sd_x1 + zone_clr"),
        D("fpc_zone_x0", "fpc_x0 - zone_clr"),
        D("fpc_zone_x1", "fpc_x1 + zone_clr"),
        D("fpc_zone_z1", "fpc_z1 + zone_clr"),
        D("usb_ch_x0", "usb_x - usb_ch_w / 2"),
        D("usb_ch_x1", "usb_x + usb_ch_w / 2"),
        D("usb_ch_y1", "cov_in_y + usb_ch_t"),
        # ---- derived: key
        D("key_z0", "sense_z1 + 0.15 mm + key_clr", comment="just above the Sense PCB"),
        D("key_z1", "key_z0 + key_h"),
        D("slot_z0", "key_z0 - key_clr"),
        D("slot_z1", "key_z1 + key_clr"),
        D("slot_x1", "pocket_x1 + key_blind"),
        D("key_x0", "body_left - key_sink", comment="key head at x = -key_x0"),
        D("key_x1", "slot_x1 - 1 mm", comment="key tip, 1 mm of travel left"),
        D("key_front_y", "mod_back_y + key_press", comment="flat front of the key"),
        D("usb_x0", "cam_bz - usb_bz1", comment="left edge of the USB-C shell: the sloped back passes it at key_y0"),
        D("slot_back_head", "key_y0 + (-body_left - 1 mm - usb_x0) * key_slope", comment="sloped back wall of the slot at the left wall"),
        D("slot_back_tip", "key_y0 + (slot_x1 - usb_x0) * key_slope"),
        D("key_back_head", "key_y0 + 0.03 mm + (-key_x0 - usb_x0) * key_slope"),
        D("key_back_tip", "key_y0 + 0.03 mm + (key_x1 - usb_x0) * key_slope"),
        D("key_notch_y", "slot_back_head + 1 mm * key_slope", comment="notch to lever the key out"),
        # ---- derived: cover
        D("ton_z0", "ton_z1 - tongue_l", comment="tongue tips"),
        D("csk_h", "(csk_d - clear_d) / 2"),
        D("cov_bot", "nose_z - 0.2 mm", comment="lower end of the cover"),
        D("lock_base", "lock_floor + 0.45 mm", comment="under the head when it clamps, |x|: 0.45 mm of travel left to the floor"),
        D("lock_tip", "lock_base - lock_l", comment="tip of the lock screw when it clamps, |x|"),
        D("bump_y", "pcb_back_y + bump_press", comment="top of the bumps"),
    ]


def make_params(overrides: dict | None = None) -> ParamSet:
    ps = ParamSet(parameters())
    for k, v in (overrides or {}).items():
        ps.set(k, v)
    return ps


def chassis_outline() -> list[tuple[str, str]]:
    """Silhouette of the chassis in (x, z): stick, neck, flexure arms on +x, rails and lands on -x, nose."""
    return [
        ("-bar_half", "top_z"), ("bar_half", "top_z"), ("bar_half", "stop_z"), ("bar_half - stop_lead", "stop_z - stop_lead"),
        ("neck_half", "stop_z - stop_lead"), ("neck_half", "shoulder_z"), ("body_right", "shoulder_z"), ("body_right", "root_h"), ("arm_in", "root_h"),
        ("arm_in", "pad_in_z0"), ("pad_in", "pad_in_z1"), ("pad_in", "pad_end"), ("arm_out", "pad_end"),
        ("pad_tip", "pad_z"), ("arm_out", "pad_low_z"),
        ("arm_out", "-pad_low_z"), ("pad_tip", "-pad_z"), ("arm_out", "-pad_far_end"), ("pad_in", "-pad_far_end"),
        ("pad_in", "-pad_in_z1"), ("arm_in", "-pad_in_z0"), ("arm_in", "-root_h"), ("body_right", "-root_h"),
        ("body_right", "-nose_z"), ("-land_x + land_lead", "-nose_z"), ("-land_x", "-nose_z + land_lead"),
        ("-land_x", "-relief_end"), ("-relief_x", "-relief_z"), ("-relief_x", "-body_bot"), ("-rail_end_x", "-body_bot"),
        ("-rail_far", "-rail_far_z"), ("-body_left", "-rail_far_ramp"),
        ("-body_left", "rail_ramp_z"), ("-rail_tip", "rail_z"), ("-rail_end_x", "body_top"), ("-relief_x", "body_top"),
        ("-relief_x", "relief_z"), ("-land_x", "relief_end"), ("-land_x", "land_top"), ("-bar_half", "land_top"),
    ]


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


def flexure(p) -> dict:
    """Arm as a cantilever with a stiff pad on its end: stiffness at the ridge, forces, strain, what holds the seat."""
    L = p.pad_in_z0 - p.root_h
    e = p.pad_z - p.pad_in_z0
    b = (p.front_y - p.back_y) - max(0.0, p.arm_out + (-p.back_y) - p.edge_sum)      # arm width after the corner cut
    ei = p.arm_e * b * p.arm_t ** 3 / 12
    k = 1 / ((L ** 3 / 3 + e * L ** 2 + e * e * L) / ei)
    seated = p.pad_over * k
    shift = p.rail_tip - p.throat                                              # near rail against one wall
    d_pass = p.pad_tip - (2 * p.throat - p.rail_tip)                           # near rail and near pad in the near throat
    d_far = p.pad_tip - (2 * p.throat - p.rail_far)                            # far rail and far pad in the near throat, the worst bend
    f_pass = d_far * k
    m = f_pass * (L + e)
    stress = m * (p.arm_t / 2) / (b * p.arm_t ** 3 / 12)
    tf = math.tan(math.radians(45) + math.atan(p.mu_est))
    lead = math.atan((p.pad_tip - p.arm_out) / p.pad_lead)
    z_land = (p.relief_end + p.land_top) / 2
    # leaving the seat: the near ridge climbs the chamfer until it reaches the wall (2 mm of bend per mm of shift, force 2 F_near),
    # then runs on the wall (1 mm per mm, force F_near + F_far); the mirror case holds for an overshoot
    on_cham = p.pad_seat - p.throat
    f_near = k * (p.pad_over + 2 * on_cham)
    f_wall = k * d_pass + seated
    stop_gap = p.throat - p.bar_half
    return {"L": L, "e": e, "b": b, "k": k, "seated": seated, "preload": 2 * seated, "d_pass": d_pass, "d_far": d_far, "f_pass": f_pass,
            "stress": stress, "strain": stress / p.arm_e * 100, "push": f_pass * math.tan(lead + math.atan(p.mu_est)), "slide": 2 * p.mu_est * 2 * k * d_pass,
            "start": 2 * seated * tf, "pull": max(2 * f_near, f_wall) * tf, "shift": shift, "stop_gap": stop_gap, "stop_bite": p.rail_far - p.throat - stop_gap,
            "rock_deg": math.degrees(p.land_gap / z_land), "z_land": z_land,
            "handle_plus_x": 2 * seated / (1 + p.top_z / z_land), "handle_minus_x": 2 * seated / (p.top_z / z_land - 1)}


def checks(ps: ParamSet) -> list[tuple[str, str]]:
    out = []
    eps = 1e-3

    def need(ok, msg, level="error"):
        if not ok:
            out.append((level, msg))

    p = ps
    fx = flexure(p)
    # the port: width at every level, with the arms yielding at the pads only
    need(p.land_x + p.arm_out <= 2 * p.throat - 0.2 + eps, "lands + arms wider than the throat")
    need(p.rail_tip + p.body_right <= 2 * p.throat - 0.2 + eps, "rails + right wall wider than the throat")
    need(p.rail_tip + p.neck_half <= 2 * p.throat - 0.2 + eps, "rails level and neck: shifted tool does not pass", "warn")
    need(p.neck_half <= p.throat - 0.5 + eps, "neck touches the throat when seated")
    need(p.body_top < p.throat_z0 - eps and p.body_bot < p.throat_z0 - eps, "rail flat reaches into a throat when seated")
    need(-p.back_y <= p.throat - 0.15 + eps, "target too thick for the port (back)")
    need(p.screen_out_y <= p.throat - 0.3 + eps, "screen does not pass the port (front)")
    need(p.cap_h < p.throat_z0 - eps, "cap reaches a throat")
    need(p.rail_tip >= p.notch_x + 0.05 - eps, "rail tip inside the notch zone: contact only between the notches", "warn")
    need(p.rail_end_x < p.rail_tip and p.rail_end_x >= p.throat, "rail flat outside the chamfer")
    # lands and nose in the throats
    need(p.land_gap >= 0.03 - eps, "land gap too small: a land could lift the rail off its chamfer")
    need(p.relief_end >= p.throat_z0 + 0.4 - eps, "land starts at the lip")
    need(p.relief_x <= p.throat - 0.3 + eps and p.relief_z >= p.throat_z0 + 0.2 - eps, "no relief around the lip")
    need(p.land_top >= 23.0 - eps and p.land_top <= p.cube_half + eps, "near land misses the side port's throat (21..23.8)")
    need(p.nose_z <= p.cube_half - 0.3 + eps, "nose leaves the cube's envelope")
    need(p.pad_seat >= p.throat + 0.1 - eps and p.pad_z <= p.throat_z0 - 0.1 + eps, "pad ridge not on the chamfer")
    # puzzle piece on top: the rail corners against its corner chamfers, tool shifted to the wall
    shift = p.rail_tip - p.puz_half + 0.05
    need(p.rail_tip - shift + (p.edge_sum - p.rail_tip) <= 2 * p.puz_half - p.puz_cor + eps, "rail ends hit the puzzle's corner chamfers")
    need(p.flare_z >= p.cube_half + p.puz_t + 0.5 - eps, "waist of the handle hidden in the puzzle piece")
    need(p.flare_z + p.flare_d / 2 <= p.top_z - 3.0 + eps, "no knob left above the waist")
    # the stick's shoulder: free while the near rail needs the throat, a hard stop in an overshoot
    lip = p.cube_half - p.throat
    need(p.bar_half <= p.stop_z - lip - 0.1 + eps, "stick's shoulder hits the lip while the near rail passes")
    need(p.bar_half - p.stop_lead <= p.stop_z - p.stop_lead - lip - 0.1 + eps, "stick's lead hits the lip while the near rail passes")
    need(p.bar_half + fx["shift"] <= p.puz_half - 0.1 + eps, "stick hits the puzzle piece while the near rail passes")
    need(p.stick_sum + fx["shift"] <= 2 * p.puz_half - p.puz_cor + eps, "stick's back corners hit the puzzle's corner chamfers")
    need(fx["stop_bite"] >= 0.3 - eps, "at the stop the far rail is too close to the far throat")
    need(p.pad_end <= p.stop_z - p.stop_lead - 0.3 + eps, "pad reaches the stick's shoulder")
    need(p.land_x >= p.bar_half + 0.2 - eps, "land does not stand out of the stick")
    need(p.usb_ch_y1 <= p.stick_front - 3.0 + eps, "stick's web in front of the USB channel under 3 mm")
    # arms
    need(p.pad_in - fx["d_pass"] >= p.neck_half + 0.1 - eps, f"pad hits the neck when passing the throat ({fx['d_pass']:.2f} mm)")
    need(p.arm_in - fx["d_far"] >= p.body_right + 0.1 - eps, f"arm hits the body when passing the throat ({fx['d_far']:.2f} mm)")
    need(fx["strain"] <= 2.0 + eps, f"arm strain {fx['strain']:.1f} % too high")
    need(p.arm_t >= 0.8 - eps, "arm thinner than two print lines")
    # camera seat and pocket walls
    need(p.bore_d / 2 + p.seat_c <= p.body_right - 1.0 + eps, "hood wall on the right under 1 mm")
    need(p.pocket_x1 <= p.body_right - 2.0 + eps, "right wall under 2 mm")
    need(p.pocket_z0 >= -p.body_bot + 2.0 - eps, "floor under the board under 2 mm")
    need(p.cone_y1 < p.front_y - 1.0, "hood bore too short")
    need(p.lens_tip_y + 1.2 < p.cone_y1, "unscrewed lens reaches beyond the funnel")
    r_at_tip = p.lens_hole_d / 2 + max(0.0, p.lens_tip_y - p.cone_y0)
    need(r_at_tip >= p.lens_d / 2 - eps, "lens does not fit the hole")
    need(p.zone_y > p.mod_back_y, "socket zone does not clear the flex")
    need(p.zone_y <= p.shoulder_y - 0.6 + eps, "seat shorter than 0.6 mm")
    need(p.sd_x1 + p.zone_clr <= p.main_x1 - 0.5 + eps and p.sd_x0 - p.zone_clr >= p.main_x0 + 0.5 - eps, "no ledge left beside the socket")
    need(p.key_z0 >= p.sense_z1 + 0.05 - eps, "key touches the Sense PCB")
    need(p.key_z1 >= 3.9, "key shorter than the module's back")
    need(p.slot_x1 <= p.body_right - 0.8 + eps, "key tip breaks through the right wall")
    need(p.key_front_y <= p.zone_y + eps, "key front beyond the slot")
    need(p.key_front_y - p.key_back_tip >= 2.0 - eps, "key tip too thin")
    need(p.key_y0 > p.usb_front_y, "key touches the USB-C shell")
    need(p.pocket_x0 - (-p.body_left) >= 3.0 - eps and p.slot_back_head - (p.cov_in_y) >= 2.0 - eps, "left wall around the key slot too thin")
    need(p.usb_ch_x0 >= -p.neck_half + 2.0 - eps and p.usb_ch_x1 <= p.neck_half - 2.0 + eps, "neck walls beside the USB channel under 2 mm")
    need(p.usb_ch_y1 > p.usb_y + 3.3, "USB channel too shallow for a 6.6 mm plug")
    need(p.usb_y - 3.3 > p.cov_in_y - eps, "USB channel behind the cover")
    # cover
    need(p.pocket_x0 >= -p.low_x0 + 1.5 - eps and p.pocket_x1 <= p.low_x1 - 1.0 + eps, "cover does not rest beside the pocket")
    need(p.body_right - p.low_x1 >= 1.0 - eps, "wall beside the cover under 1 mm")
    need(p.screw_x - p.insert_d / 2 >= p.usb_ch_x1 + 0.7 - eps and p.screw_x + p.csk_d / 2 <= p.rab_x1 - p.cov_clr - 0.2 + eps, "screw 1 does not fit between USB channel and cover edge")
    need(-p.screw_x2 + p.insert_d / 2 <= p.usb_ch_x0 - 0.7 + eps and p.screw_x2 + p.csk_d / 2 <= p.rab_x0 - p.cov_clr - 0.2 + eps, "screw 2 does not fit between USB channel and cover edge")
    need(p.screw_z3 - p.insert_d / 2 >= -p.pocket_z0 + 0.6 - eps and p.screw_z3 + p.insert_d / 2 <= p.nose_z - 1.0 + eps, "insert of screw 3 does not fit under the pocket")
    need(p.screw_z3 + p.csk_d / 2 <= p.cov_bot + eps, "head of screw 3 beyond the cover")
    need(p.cover_top >= p.screw_z + p.csk_d / 2 + 0.8 - eps, "screw head beyond the cover (top)")
    # lens tube and lock
    need((p.lens_hole_d - p.lens_d) / 2 >= 0.15 - eps, "lens does not slide in the tube")
    need(p.lens_tube_d - p.lens_hole_d >= 1.6 - eps, "lens tube wall too thin")
    r_lock = p.lens_hole_d / 2 + p.lock_y - p.cone_y0
    need(r_lock >= p.lens_tube_d / 2 + 1.0 - eps, "funnel too tight around the tube at the lock screw")
    need(p.lock_floor - 5.0 >= r_lock + 0.3 - eps, "insert hole of the lock screw breaks into the funnel")
    need(p.lock_tip <= p.lens_tube_d / 2 and p.lock_tip >= p.lens_tube_d / 2 - 0.3, "lock screw does not reach the jaw")
    need(p.lock_base + 3.0 <= p.body_left - 0.2 + eps, "head of the lock screw stands proud of the wall")
    need(p.jaw_y0 <= p.lock_y - 1.0 and p.lock_y <= p.lens_tube_y - 1.0, "lock screw beside the jaw")
    # caps
    need(p.cap_w <= p.body_right + eps, "cap wider than the chassis on the right")
    need(p.mag_z - p.mag_pocket_d / 2 >= p.seat_r + 0.6 - eps, "magnet pockets cut the hood seat")
    need(p.mag_z - p.mag_pocket_d / 2 >= p.ring_r0 + 0.3 - eps, "magnet pockets of the cap cut the ring")
    need(p.mag_z + p.mag_pocket_d / 2 <= p.cap_h - 0.4 + eps, "magnet pockets break the cap's end")
    need(p.cap_t - p.mag_pocket_h >= 0.3 - eps, "skin over the cap's magnets under 0.3 mm")
    need(p.cap_bore_d / 2 <= p.ring_r0 - p.ring_h - 0.5 + eps, "cap ring too thin")
    need(p.nd_t + p.nd_pad + p.nd_wall <= p.cap_t + p.ring_h + eps, "ND filter deeper than the cap")
    # optics
    opt = screen_optics(p)
    need(opt["ok"], f"screen at {p.screen_d:g} mm cannot be imaged with f {p.lens_f:g} (needs >= 4 f = {opt['min_d']:.1f})")
    if opt["ok"]:
        need(p.sensor_y + opt["s_i"] + 1 < p.cone_y1, "lens front beyond the funnel")
        out.append(("info", f"screen at {p.screen_d:g} mm: lens {opt['s_i']:.2f} mm from the sensor (unscrew ~{opt['unscrew']:.1f} mm from infinity focus), "
                            f"m {opt['m']:.2f}, field {opt['field_w']:.1f} x {opt['field_h']:.1f} mm"))
    out.append(("info", f"flexure: k {fx['k']:.2f} N/mm at the ridge, seated {fx['seated']:.1f} N per pad = {fx['preload']:.1f} N into the V; "
                        f"through the throat {fx['d_pass']:.2f} / {fx['d_far']:.2f} mm (near / far rail), {fx['f_pass']:.1f} N, strain {fx['strain']:.2f} %; "
                        f"push about {fx['push']:.0f} N peak, {fx['slide']:.0f} N sliding; a straight pull starts at {fx['start']:.0f} N and peaks at {fx['pull']:.0f} N, an overshoot alike"))
    out.append(("info", f"stop: shoulder {fx['stop_gap']:.2f} mm off the +x throat wall; at the stop the far rail still bites {fx['stop_bite']:.2f} mm on the chamfer"))
    out.append(("info", f"roll: free rock +-{fx['rock_deg']:.2f} deg between the lands; a rail stays down up to {fx['handle_plus_x']:.1f} N (+x) / {fx['handle_minus_x']:.1f} N (-x) at the top of the stick"))
    out.append(("info", f"tool x {-p.rail_tip}..{p.pad_tip:.2f} (free), y {p.back_y}..{p.screen_out_y:.2f}, z {-p.nose_z}..{p.top_z}; sensor at y {p.sensor_y}, "
                        f"screen at y {p.screen_in_y:.2f}, rails y {p.rail_tip - p.edge_sum:.1f}..{p.front_y}"))
    return [o for o in out if o[1]]


def report(ps: ParamSet) -> int:
    print("XIAO ESP32-S3 Sense beam target")
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
