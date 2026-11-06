"""Checks and figures of the XIAO beam target from its STEP exports (no Inventor needed).

    uv run --with cadquery --with trimesh --with rtree --with scipy --with shapely --with networkx ^
        --with matplotlib --with pyvista --with pillow python check_xiao_target.py [--no-figures]

Point sampling on the meshes, never booleans. Checks: rails and pad ridges on the real chamfers and lands against
the real throat walls (ray casting), only the two pads overlap the cube when seated (entry from the top and from
the side), the tool passes the near port and enters the far throat, the hard stop of an overshoot, the lens sees the screen field, the bare
chip's acceptance, the USB-C plug's channel, the key behind the module. Figures in docs/: sections, the levers
against the roll, entry sequence, views and an exploded view.
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from xiao_target import INV_DIR, NAMES, PARTS, chassis_outline, flexure, make_params, screen_optics  # noqa: E402

DOCS = HERE / "docs"
COL = {"chassis": "#4a525c", "cover": "#5d6672", "key": "#e8791e", "screen": "#f2f1ec", "ndcap": "#9aa1aa", "magnet": "#b8bdc4",
       "xiao": "#1f6f54", "cube": "#c9ccd1", "puzzle": "#d9dbdf", "hardware": "#8d939b"}
PRINTED = ("chassis", "cover", "key", "screen", "ndcap")


def meshes_of(step: Path, tol=0.03):
    import cadquery as cq
    shape = cq.importers.importStep(str(step)).val()
    out = []
    for s in shape.Solids():
        v, f = s.tessellate(tol, 0.2)
        if len(f) < 4:
            continue
        out.append((trimesh.Trimesh(np.array([(q.x, q.y, q.z) for q in v]), np.array(f), process=True), s.Volume()))
    return out


def classify(m, vol, refs, p) -> str:
    lo, hi = m.bounds
    c = (lo + hi) / 2
    for key, (rlo, rhi, rvol) in refs.items():
        if abs(vol - rvol) < 0.01 * rvol and np.allclose(sorted(hi - lo), sorted(rhi - rlo), atol=0.06):
            return key
    e = sorted(hi - lo)
    if abs(e[0] - 3.0) < 0.05 and abs(e[2] - 8.0) < 0.05:
        return "magnet"
    d = hi - lo
    if abs(d[0] - 49.8) < 0.2 and abs(d[1] - 49.8) < 0.2 and d[2] > 40:
        return "cube"                        # the two CUBHLF111 halves
    if lo[2] > 24.5 and abs(d[0] - 60) < 12 and d[2] < 8:
        return "puzzle"
    if abs(c[0] - p.screw_x) < 1.0 and abs(c[2] - p.screw_z) < 1.0:
        return "hardware"                    # the M3 screw and its insert
    return "xiao"


def inside_any(pts, meshes):
    hit = np.zeros(len(pts), bool)
    for m in meshes:
        hit |= m.contains(pts)
    return hit


def section(ax, items, origin, normal, to2d, xlim=None, ylim=None):
    from matplotlib.patches import Polygon as MPoly
    for m, grp in items:
        sec = m.section(plane_origin=origin, plane_normal=normal)
        if sec is None:
            continue
        try:
            planar, _ = sec.to_2D(to_2D=to2d)
        except Exception:
            continue
        for poly in planar.polygons_full:
            ax.add_patch(MPoly(np.array(poly.exterior.coords), closed=True, fc=COL[grp], ec="k", lw=0.3,
                               alpha=0.55 if grp in ("cube", "puzzle") else 1.0))
            for hole in poly.interiors:
                ax.add_patch(MPoly(np.array(hole.coords), closed=True, fc="white", ec="k", lw=0.3))
    ax.set_aspect("equal")
    if xlim:
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
    ax.grid(alpha=0.2)


TO_YZ = np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0], [0, 0, 0, 1]], float)
TO_XZ = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
TO_XY = np.eye(4)
SIDE_R = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], float)      # tool -> world, entry from the side (x -> -z, z -> +x)


def seated_outline(p, dx=0.0, dz=0.0, deflect=None):
    """Silhouette (x, z) with the arms bent by `deflect` = (upper, lower) at the pad tips (default: the seated pad_over)."""
    corners = np.array([(p.ev(a), p.ev(b)) for a, b in chassis_outline()], float)
    pts = []
    for c0, c1 in zip(corners, np.roll(corners, -1, axis=0)):
        n = max(1, int(np.linalg.norm(c1 - c0) / 0.5))
        pts += [c0 + (c1 - c0) * i / n for i in range(n)]
    pts = np.array(pts)
    up, low = (p.pad_over, p.pad_over) if deflect is None else deflect
    for i, (x, z) in enumerate(pts):
        if x > p.arm_in - 0.01 and abs(z) > p.root_h + 0.01 and -p.pad_far_end - 0.01 <= z <= p.pad_end + 0.01:
            s = (min(abs(z), p.pad_z) - p.root_h) / (p.pad_z - p.root_h)
            pts[i, 0] -= (up if z > 0 else low) * s * s * (3 - s) / 2
    return pts + [dx, dz]


def main() -> None:
    do_figs = "--no-figures" not in sys.argv
    p = make_params()
    DOCS.mkdir(exist_ok=True)
    refs, printed = {}, {}
    for key in PRINTED:
        (m, vol), = meshes_of(INV_DIR / f"{NAMES[key]}.stp")
        printed[key] = m
        refs[key] = (*m.bounds, vol)
    items = [(m, classify(m, v, refs, p)) for m, v in meshes_of(INV_DIR / f"{NAMES['assembly']}.stp")]
    count = {g: sum(1 for _, x in items if x == g) for g in COL}
    print("assembly solids:", count)
    opt = screen_optics(p)
    if "--figures-only" in sys.argv:
        figures(p, items, printed, opt)
        sys.stdout.flush()
        os._exit(0)
    problems, results = [], {}
    for key in ("chassis", "cover", "key", "screen"):
        if count[key] != 1:
            problems.append(f"{key}: {count[key]} solids found in the assembly STEP")
    for key in PRINTED:
        if not printed[key].is_watertight:
            problems.append(f"{key}: mesh not watertight - sampling unreliable")
    cube = [m for m, g in items if g == "cube"]
    puzzle = [m for m, g in items if g == "puzzle"]
    if len(cube) != 2 or len(puzzle) != 1:
        problems.append(f"expected 2 cube halves and 1 puzzle piece, found {len(cube)} / {len(puzzle)}")

    # 1) rails on the real chamfers: rays from each rail flat along its outward normal
    rails = []
    rmesh = trimesh.util.concatenate(cube)
    ri = trimesh.ray.ray_triangle.RayMeshIntersector(rmesh)
    y_rail = np.linspace(p.rail_tip - p.edge_sum + 0.3, p.front_y - 0.3, 139)
    for sz, tag in ((1, "upper"), (-1, "lower")):
        for along in (0.1, 0.5, 0.9):
            xr = -(p.rail_tip + (p.rail_end_x - p.rail_tip) * along)
            zr = sz * (p.cham_sum - p.cham_gap + xr)
            org = np.array([(xr, y, zr) for y in y_rail])
            n = np.array([-1, 0, sz]) / math.sqrt(2)
            loc, idx, _ = ri.intersects_location(org, np.tile(n, (len(org), 1)), multiple_hits=False)
            gaps = np.full(len(org), np.nan)
            gaps[idx] = np.linalg.norm(loc - org[idx], axis=1)
            good = gaps < 0.1
            rails.append((tag, round(along, 1), float(np.nanmin(gaps)), float(good.mean())))
    results["rails"] = rails
    contact = np.mean([r[3] for r in rails if r[1] == 0.1])
    inner = np.mean([r[3] for r in rails if r[1] == 0.9])
    gap_min = min(r[2] for r in rails)
    print(f"[{'ok' if contact > 0.95 and gap_min > 0 else 'FAIL'}] rails on the chamfers: flat parallel to the chamfer at {gap_min:.3f} mm in the model; "
          f"contact along the rail {100 * contact:.0f} % near the tip, {100 * inner:.0f} % at the inner end (the notches, top entry)")
    if contact < 0.95:
        problems.append("rail tips do not lie on the chamfers")

    # 2) seated, top and side entry: what overlaps the cube. Only the two pads may.
    for label, R in (("top", np.eye(3)), ("side", SIDE_R)):
        for key in ("chassis", "cover", "key", "screen"):
            smp, face = trimesh.sample.sample_surface_even(printed[key], 14000)
            smp = smp - 0.04 * printed[key].face_normals[face]
            inside = inside_any(smp @ R.T, cube)
            pad = (smp[:, 0] > p.arm_in) & (np.abs(smp[:, 2]) > p.pad_low_z - 0.5)
            wrong = inside & ~pad
            if wrong.any():
                problems.append(f"{label}, {key}: {wrong.sum()} samples inside the cube outside the pads, e.g. {np.round(smp[wrong][0], 2)}")
    print(f"[{'ok' if not any('inside the cube' in x for x in problems) else 'FAIL'}] seated from the top and from the side: only the pads overlap the cube "
          f"(their preload, {p.pad_over:.2f} mm as modelled)")

    # 2b) lands and pad ridges against the real throat walls, in both entries
    y_st = np.linspace(-14.5, 11.5, 105)
    for label, R in (("top", np.eye(3)), ("side", SIDE_R)):
        row = {}
        for tag, x0, z0, dirn in (("near land", -p.land_x, p.land_top - 0.8, -1), ("far land", -p.land_x, -(p.relief_end + 1.0), -1),
                                  ("near pad", 16.0, p.pad_z, 1), ("far pad", 16.0, -p.pad_z, 1)):
            org = np.array([(x0, y, z0) for y in y_st]) @ R.T
            dv = (np.array([dirn, 0.0, 0.0]) @ R.T)
            loc, idx, _ = ri.intersects_location(org, np.tile(dv, (len(org), 1)), multiple_hits=False)
            d = np.full(len(org), np.nan)
            d[idx] = np.linalg.norm(loc - org[idx], axis=1)
            wall = (x0 * dirn + d)                                  # wall position as |x| in the tool frame
            near = wall < p.pad_seat + 0.1
            row[tag] = {"wall": round(float(np.nanpercentile(wall, 20)), 3), "share": round(float(near.mean()), 2)}
        results[f"throat walls {label}"] = row
        gaps = [row[k]["wall"] - p.land_x for k in ("near land", "far land")]
        over = [p.pad_tip - row[k]["wall"] for k in ("near pad", "far pad")]
        good = all(0.02 < g < 0.2 for g in gaps) and all(p.pad_over - 0.1 < o < p.pad_over + 0.1 for o in over)
        print(f"[{'ok' if good else 'FAIL'}] throat walls, {label} entry: land gaps {gaps[0]:.3f} / {gaps[1]:.3f} mm (walls under {100 * row['near land']['share']:.0f} / "
              f"{100 * row['far land']['share']:.0f} % of the length), pad ridges past the chamfer {over[0]:.2f} / {over[1]:.2f} mm "
              f"(chamfer under {100 * row['near pad']['share']:.0f} / {100 * row['far pad']['share']:.0f} % of the length)")
        if not good:
            problems.append(f"throat walls, {label}: {row}")

    # 3) the port: rigid parts swept along the entry, top with puzzle piece and side; the tool may shift across
    rigid = []
    for key in ("chassis", "cover", "key", "screen"):
        smp, _ = trimesh.sample.sample_surface_even(printed[key], 16000)
        rigid.append(smp)
    rigid = np.vstack(rigid)
    is_arm = (rigid[:, 0] > p.body_right + 0.02) & (rigid[:, 2] < p.stop_z - p.stop_lead - 0.02) & (rigid[:, 0] > p.neck_half + 0.02)
    rigid_pts, arm_pts = rigid[~is_arm], rigid[is_arm]
    obstacles = [(lambda P_: inside_any(P_, cube + puzzle)), (lambda P_: inside_any(P_, cube))]
    for label, R, obstacle, axis in (("top, puzzle piece on", np.eye(3), obstacles[0], 2), ("side", SIDE_R, obstacles[1], 0)):
        worst, travel, bad, shifts = 0.0, 0, [], []
        across = np.array([1, 0, 0.0]) if axis == 2 else np.array([0, 0, 1.0])
        for h in list(np.arange(0.0, 6.01, 0.25)) + list(np.arange(8.0, 50.1, 2.0)):
            pts0 = rigid_pts @ R.T
            arm0 = arm_pts @ R.T
            pts0 = pts0 + np.eye(3)[axis] * h
            arm0 = arm0 + np.eye(3)[axis] * h
            band = ((pts0[:, axis] > 18.0) & (pts0[:, axis] < p.cube_half + p.puz_t + 1.0)) | ((pts0[:, axis] < -18.0) & (pts0[:, axis] > -26.0))
            sub = pts0[band]
            ok_shift = None
            for ds in sorted(np.arange(-1.6, 1.61, 0.1), key=abs):
                if not obstacle(sub + across * ds).any():
                    ok_shift = float(ds)
                    break
            if ok_shift is None:
                bad.append(float(h))
                continue
            shifts.append((float(h), ok_shift))
            arm = arm0 + across * ok_shift
            a = arm[(np.abs(arm[:, axis]) > 20.97) & (np.abs(arm[:, axis]) < 24.9)]
            if len(a):
                c = a @ across
                worst = max(worst, float(max(c.max() - p.throat, -c.min() - p.throat, 0.0)))
            travel += 1
        if bad:
            problems.append(f"port {label}: rigid parts blocked at heights {bad}")
        results[f"port {label}"] = {"steps_ok": travel, "blocked": bad, "arm_yield_mm": round(worst, 2), "shifts": shifts}
        print(f"[{'ok' if not bad else 'FAIL'}] port, {label}: rigid parts pass both throats at {travel} heights with a shift of at most "
              f"{max(abs(s) for _, s in shifts) if shifts else 0:.1f} mm; the arms yield up to {worst:.2f} mm "
              f"(free gap beside the neck {p.pad_in - p.neck_half:.2f} mm)")

    # 3b) the hard stop: rigid parts pushed past the seat, the tool free to shift across. How deep can it go?
    smp, _ = trimesh.sample.sample_surface_even(printed["chassis"], 90000)
    keep = ~((smp[:, 0] > p.neck_half + 0.02) & (smp[:, 2] < p.stop_z - p.stop_lead - 0.02)) & ((np.abs(smp[:, 0]) > 14.5) & (np.abs(smp[:, 2]) > 16.0))
    stop_pts = smp[keep]
    for label, R, obstacle, axis in (("top, puzzle piece on", np.eye(3), obstacles[0], 2), ("side", SIDE_R, obstacles[1], 0)):
        across = np.array([1, 0, 0.0]) if axis == 2 else np.array([0, 0, 1.0])
        sign = 1.0
        deepest = 0.0
        for depth in np.arange(0.1, 3.01, 0.1):
            pts = stop_pts @ R.T - np.eye(3)[axis] * depth
            if any(not obstacle(pts + across * sign * s).any() for s in np.arange(0.0, 2.01, 0.05)) or \
                    any(not obstacle(pts - across * sign * s).any() for s in np.arange(0.05, 2.01, 0.05)):
                deepest = float(depth)
            else:
                break
        results[f"stop {label}"] = deepest
        good = 0.5 < deepest < 1.3
        print(f"[{'ok' if good else 'FAIL'}] hard stop, {label}: the rigid parts can go {deepest:.1f} mm past the seat, no further at any shift")
        if not good:
            problems.append(f"no hard stop, {label}: {deepest} mm")

    # 4) lens mode: the view from the lens pupil to the screen field is free of printed material
    y_lens = p.sensor_y + opt["s_i"]
    fw, fh = opt["field_w"] / 2, opt["field_h"] / 2
    starts = [(r * math.cos(a), y_lens, r * math.sin(a)) for r in (0.0, 0.8) for a in np.linspace(0, 2 * math.pi, 9)[:-1]]
    ends = [(u * fw, p.screen_in_y - p.rib_h - 0.02, w * fh) for u in (-1, -0.5, 0, 0.5, 1) for w in (-1, -0.5, 0, 0.5, 1)]
    pts = np.array([np.array(s) + t * (np.array(e) - np.array(s)) for s in starts for e in ends for t in np.linspace(0.0, 1, 60)])
    hit = inside_any(pts, [printed["chassis"]])
    if hit.any():
        problems.append(f"lens view blocked at {hit.sum()} of {len(pts)} points, e.g. {np.round(pts[hit][0], 2)}")
    print(f"[{'ok' if not hit.any() else 'FAIL'}] lens at y {y_lens:.2f} sees the field {opt['field_w']:.1f} x {opt['field_h']:.1f} mm at y {p.screen_in_y:.1f} "
          f"past the chassis ({len(pts)} points)")

    # 5) bare chip: acceptance half-angle through the seat and funnel (cap off, ring of the module not counted)
    def free(theta, corner, direction):
        d = np.array([math.sin(theta) * direction[0], math.cos(theta), math.sin(theta) * direction[1]])
        q = np.array(corner) + np.outer(np.linspace(0.3, (p.front_y + 0.5 - p.sensor_y) / math.cos(theta), 120), d)
        return not inside_any(q, [printed["chassis"]]).any()

    acc = {}
    for name, corner, direction in (("centre", (0, p.sensor_y, 0), (1, 0)), ("corner, outward", (p.sensor_w / 2, p.sensor_y, p.sensor_h / 2), (1, 0)),
                                    ("corner, inward", (p.sensor_w / 2, p.sensor_y, p.sensor_h / 2), (-1, 0))):
        lo, hi = 0.0, math.radians(89)
        for _ in range(26):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if free(mid, corner, direction) else (lo, mid)
        acc[name] = round(math.degrees(lo), 1)
    results["bare_chip_deg"] = acc
    print(f"[info] bare chip, light reaches the sensor up to these angles from the axis (chassis only): {acc}")

    # 6) USB-C plug: a 12.4 x 6.6 overmould from the mouth to the top of the handle
    yy, zz, xx = np.meshgrid(np.linspace(p.usb_y - 3.3, p.usb_y + 3.3, 9), np.linspace(p.usb_z1 + 0.5, p.top_z + 1, 80),
                             np.linspace(p.usb_x - 6.2, p.usb_x + 6.2, 13), indexing="ij")
    plug = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])
    hit = inside_any(plug, [printed["chassis"], printed["cover"], printed["key"]])
    if hit.any():
        problems.append(f"USB plug envelope hits printed parts at {hit.sum()} points, e.g. {np.round(plug[hit][0], 2)}")
    print(f"[{'ok' if not hit.any() else 'FAIL'}] USB-C plug 12.4 x 6.6 free from the mouth (z {p.usb_z1:.2f}) to the top of the stick")

    # 7) the key really sits behind the module
    ky = p.mod_back_y
    grid = np.array([(x, ky - 0.02, z) for x in np.linspace(-3.9, 3.9, 17) for z in np.linspace(-3.9, 3.9, 17)])
    back = inside_any(grid, [printed["key"]]).mean()
    results["module_back_on_key"] = float(back)
    print(f"[{'ok' if back > 0.75 else 'FAIL'}] the key backs {100 * back:.0f} % of the module's back; the lower edge carries the flex")
    if back < 0.75:
        problems.append("key covers too little of the module")

    results["flexure"] = {k: round(v, 3) for k, v in flexure(p).items()}
    results["problems"] = problems
    (INV_DIR / "check_results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")

    if do_figs:
        figures(p, items, printed, opt)
    for pr in problems:
        print("[FAIL]", pr)
    print("ok" if not problems else f"{len(problems)} problems")
    sys.stdout.flush()
    os._exit(1 if problems else 0)


def is_card(m) -> bool:
    """The microSD card of the vendor model: this tool runs without one."""
    lo, hi = m.bounds
    return abs((hi - lo)[2] - 15.06) < 0.1 and abs((hi - lo)[0] - 11.18) < 0.1


def tool_outline(p, dx=0.0, dz=0.0, deflect=None):
    """The silhouette as a shapely polygon, with the arms bent and the handle's waist cut."""
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union
    poly = Polygon(seated_outline(p, dx, dz, deflect)).buffer(0)
    cuts = unary_union([Point(s * p.flare_x + dx, p.flare_z + dz).buffer(p.flare_d / 2, 64) for s in (1, -1)])
    return poly.difference(cuts)


def figures(p, items, printed, opt):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MPoly

    fh = opt["field_h"] / 2
    items = [(m, g) for m, g in items if not is_card(m)]

    # section through the axis (side view)
    fig, ax = plt.subplots(figsize=(10, 10.5))
    section(ax, items, (0, 0, 0), (1, 0, 0), TO_YZ, (-30, 30), (-30, 42))
    y_lens = p.sensor_y + opt["s_i"]
    for sgn in (1, -1):
        ax.plot([y_lens, p.screen_in_y], [0, sgn * fh], color="crimson", lw=0.8)
    ax.axhline(0, color="crimson", lw=0.5, ls="--")
    ax.annotate("beam", (28, 0.8), color="crimson", fontsize=9, ha="right")
    ax.annotate("sensor plane", (p.sensor_y, 0), (-29, -7), arrowprops=dict(arrowstyle="-", lw=0.5), fontsize=8)
    ax.annotate("flexible cable", (-5.0, -8.5), (-29, -14), arrowprops=dict(arrowstyle="-", lw=0.5), fontsize=8)
    ax.annotate("spring tongue", (-14.2, -10), (-29, -20), arrowprops=dict(arrowstyle="-", lw=0.5), fontsize=8)
    ax.annotate("magnets", (12.2, 15.5), (19, 34), arrowprops=dict(arrowstyle="-", lw=0.5), fontsize=8)
    ax.annotate("screen with reticle", (p.screen_out_y, 8), (20, 31), arrowprops=dict(arrowstyle="-", lw=0.5), fontsize=8)
    ax.annotate("wedge key behind the module", (-6.8, 2), (-29, 12), arrowprops=dict(arrowstyle="-", lw=0.5), fontsize=8)
    ax.annotate("USB-C plug comes down here", (-11, 30), (-29, 40), arrowprops=dict(arrowstyle="-", lw=0.5), fontsize=8)
    ax.set_xlabel("y [mm] (the beam comes from +y)")
    ax.set_ylabel("z [mm]")
    ax.set_title("section x = 0: cube + puzzle piece (light), chassis, cover, wedge key (orange), XIAO (green, no microSD card), screen cap", fontsize=9)
    fig.tight_layout()
    fig.savefig(DOCS / "xiao_target_section_x0.png", dpi=140)
    plt.close(fig)

    # section across the axis: the seat on the chamfers
    fig, axs = plt.subplots(1, 4, figsize=(23, 10), gridspec_kw={"width_ratios": [1.5, 1, 1, 1]})
    ax = axs[0]
    section(ax, items, (0, 2.5, 0), (0, 1, 0), TO_XZ, (-30, 30), (-30, 72))
    ax.set_title("section y = 2.5: rails and lands on -x, arms on +x, drawn as printed:\nthe pads overlap the chamfers by their preload", fontsize=9)
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("z [mm]")
    ax = axs[1]
    section(ax, items, (0, 2.5, 0), (0, 1, 0), TO_XZ, (-22, -13), (15, 26))
    ax.set_title("-x, near end: rail on the chamfer, relief at the lip, land 0.05-0.1 mm off the wall", fontsize=9)
    ax = axs[2]
    section(ax, items, (0, 2.5, 0), (0, 1, 0), TO_XZ, (12, 21), (-26, -15))
    ax.plot([p.pad_seat], [-p.pad_z], "o", color="crimson", ms=5)
    ax.set_title("+x, far end: the ridge (drawn as printed) sits where the red dot is,\nin the corner of chamfer and throat wall", fontsize=9)
    ax = axs[3]
    section(ax, items, (0, 2.5, 0), (0, 1, 0), TO_XZ, (12, 21), (17, 28))
    ax.plot([p.pad_seat], [p.pad_z], "o", color="crimson", ms=5)
    ax.set_title(f"+x, near end: ridge in the near corner; the stick's shoulder enters the throat\nwith {p.throat - p.bar_half:.2f} mm of gap: the hard stop", fontsize=9)
    fig.tight_layout()
    fig.savefig(DOCS / "xiao_target_section_y.png", dpi=130)
    plt.close(fig)

    # entry sequence, top entry with a puzzle piece on
    frame = [(m, g) for m, g in items if g in ("cube", "puzzle")]
    fig, axs = plt.subplots(1, 5, figsize=(24, 12.5))
    fx = flexure(p)
    g = p.throat - p.bar_half
    stages = [(f"1  above the port: pads stand out by {p.pad_over:.1f} mm", 52.0, 0.0, (0.0, 0.0)),
              ("2  far rail and pad in the near throat: the tool shifts, the arm folds in", 44.0, p.rail_far - p.throat, (0.0, fx["d_far"])),
              ("3  near rail in the throat, nose entering the far throat", 3.0, p.rail_tip - p.throat, (fx["d_pass"], fx["d_pass"])),
              ("4  seated: rails on the chamfers, ridges click into the corners", 0.0, 0.0, None),
              (f"5  pushed too far: stops {g:.1f} mm deeper, the shoulder on the wall,\nthe far rail still on the chamfer; springs back to 4", -g, g, (p.pad_over, p.pad_over + 2 * (p.pad_seat - p.throat) + g - (p.pad_seat - p.throat)))]
    for ax, (title, dz, dx, d) in zip(axs, stages):
        section(ax, frame, (0, 2.5, 0), (0, 1, 0), TO_XZ, (-30, 30), (-30, 126))
        shape = tool_outline(p, dx, dz, d)
        for g in getattr(shape, "geoms", [shape]):
            ax.add_patch(MPoly(np.array(g.exterior.coords), closed=True, fc=COL["chassis"], ec="k", lw=0.5))
        ax.add_patch(plt.Circle((dx, dz), p.bore_d / 2, fc="white", ec="k", lw=0.4))
        ax.axhline(0, color="crimson", lw=0.4, ls="--")
        ax.set_title(title, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(DOCS / "xiao_target_entry.png", dpi=110)
    plt.close(fig)

    # what holds the roll: contacts on chamfers against contacts on the throat walls
    frame_s = [(m, g) for m, g in items if g == "cube"]
    fig, axs = plt.subplots(1, 2, figsize=(15, 7.6))
    arrow = dict(arrowstyle="-|>", color="#c1121f", lw=2.0)

    for ax in axs:
        section(ax, frame_s, (0, 2.5, 0), (0, 1, 0), TO_XZ, (-29, 29), (-29, 29))
        ax.plot(0, 0, "+", color="crimson", ms=14, mew=1.5)
    ax = axs[0]
    for sx, sz in ((-1, 1), (-1, -1), (1, 1), (1, -1)):
        px, pz = 18.0 * sx, 20.0 * sz                       # rails and pads both touched here
        ax.plot([px, -2.0 * sx], [pz, 0.0], color="#c1121f", lw=0.9, ls="--")
        ax.annotate("", xy=(px - 6.0 * sx, pz - 6.0 * sz), xytext=(px, pz), arrowprops=arrow)
    ax.set_title("four contacts on the 45 deg chamfers alone: every force passes 1.4 mm from the axis,\nnothing stops the tool rotating about the beam", fontsize=11)
    ax = axs[1]
    shape = tool_outline(p)
    for g in getattr(shape, "geoms", [shape]):
        ax.add_patch(MPoly(np.array(g.exterior.coords), closed=True, fc="#566070", ec="k", lw=0.4, alpha=0.75))
    for sz in (1, -1):
        ax.annotate("", xy=(p.pad_seat - 6.0, sz * (p.pad_z - 6.0)), xytext=(p.pad_seat, sz * p.pad_z), arrowprops=arrow)
        ax.annotate("", xy=(-13.0, sz * 15.0), xytext=(-18.0, sz * 20.0), arrowprops=arrow)
        ax.annotate("", xy=(-11.0, sz * 22.3), xytext=(-p.throat, sz * 22.3), arrowprops=dict(arrow, color="#1d6fa5"))
        ax.plot([-p.throat, 0], [sz * 22.3, sz * 22.3], color="#1d6fa5", lw=0.8, ls="--")
    ax.annotate("", xy=(0, 22.3), xytext=(0, 0), arrowprops=dict(arrowstyle="<->", color="#1d6fa5", lw=1.2))
    ax.text(0.8, 11, "lever 22 mm", color="#1d6fa5", fontsize=11)
    ax.set_title("rev D: rails and ridges in the chamfers fix x and z (red).\nThe lands, 0.05-0.1 mm off the -x walls, stop the roll (blue)", fontsize=11)
    fig.tight_layout()
    fig.savefig(DOCS / "xiao_target_roll.png", dpi=125)
    plt.close(fig)

    # views
    try:
        import pyvista as pv
        from PIL import Image
        pv.OFF_SCREEN = True
        look = {"chassis": ("#566070", 0.3), "cover": ("#626c7b", 0.3), "key": ("#e8791e", 0.3), "screen": ("#f4f3ee", 0.15), "ndcap": ("#9aa1aa", 0.3),
                "magnet": ("#b8bdc4", 0.5), "xiao": ("#1f6f54", 0.3), "cube": ("#c9ccd1", 0.1), "puzzle": ("#d9dbdf", 0.1), "hardware": ("#8d939b", 0.6)}

        def render(meshes, path, cpos, zoom=1.3, size=(1500, 1250), opacity=None):
            pl = pv.Plotter(off_screen=True, window_size=size, lighting="none")
            for m, grp in meshes:
                c, sp = look[grp]
                mesh = pv.wrap(m).compute_normals(feature_angle=28, split_vertices=True)
                pl.add_mesh(mesh, color=c, smooth_shading=True, ambient=0.3, diffuse=0.7, specular=sp, specular_power=30, opacity=(opacity or {}).get(grp, 1.0))
            for pos, i in (((180, 220, 240), 0.8), ((-220, 120, 100), 0.4), ((60, -240, 60), 0.35)):
                pl.add_light(pv.Light(position=pos, intensity=i, light_type="scene light"))
            pl.set_background("white")
            pl.camera_position = cpos
            pl.camera.zoom(zoom)
            pl.enable_anti_aliasing("ssaa")
            pl.screenshot(str(path))
            pl.close()

        tool = [(m, g) for m, g in items if g not in ("cube", "puzzle")]
        render(items, DOCS / "xiao_target_iso.png", [(210, 290, 230), (0, 0, 22), (0, 0, 1)], opacity={"cube": 0.45, "puzzle": 0.45})
        render(tool, DOCS / "xiao_target_hero.png", [(150, 250, 120), (0, 0, 22), (0, 0, 1)], 1.15)
        render(tool, DOCS / "xiao_target_back.png", [(-155, -250, 120), (0, 0, 22), (0, 0, 1)], 1.15)
        side = [(m, classify_side(g)) for m, g in meshes_side(items)]
        render(side, DOCS / "xiao_target_side_entry.png", [(260, 240, 190), (22, 0, 0), (0, 0, 1)], opacity={"cube": 0.45, "puzzle": 0.45})
        expl = []
        offs = {"cover": (0, -62, 0), "key": (-34, 0, 0), "screen": (0, 30, 0), "xiao": (0, -30, 0), "hardware": (0, -80, 0)}
        for m, g in tool:
            mm = m.copy()
            if g == "magnet":
                mm.apply_translation((0, 30, 0) if m.centroid[1] > p.front_y else (0, 0, 0))
            elif g in offs:
                mm.apply_translation(offs[g])
            expl.append((mm, g))
        ndm = printed["ndcap"].copy()
        ndm.apply_translation((0, 62, 0))
        expl.append((ndm, "ndcap"))
        render(expl, DOCS / "xiao_target_parts.png", [(-330, 120, 190), (0, -14, 22), (0, 0, 1)], 1.5, size=(1900, 1100))
    except Exception as exc:
        print("[warn] no views:", str(exc)[:160])


def classify_side(g):
    return g


def meshes_side(items):
    """The tool of the seated assembly turned to the side entry; cube and puzzle stay."""
    T = np.eye(4)
    T[:3, :3] = SIDE_R
    out = []
    for m, g in items:
        if g in ("cube", "puzzle"):
            out.append((m, g))
        else:
            mm = m.copy()
            mm.apply_transform(T)
            out.append((mm, g))
    return out


if __name__ == "__main__":
    main()
