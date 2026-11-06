"""Checks and figures of the XIAO camera target from its STEP exports (no Inventor needed).

    uv run --with cadquery --with trimesh --with rtree --with scipy --with shapely --with networkx ^
        --with matplotlib --with pyvista python check_xiao_target.py

Checks (point sampling on the meshes, never booleans): the lens's view of the screen is free of
printed material; the bare chip's acceptance angle through the front wall; nothing printed
inside the cube's parts. Figures: docs/xiao_target_section_x0.png (side), _z0.png (top),
docs/xiao_target_iso.png (in the cube) and _parts.png (exploded, standalone on the riser).
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE.parent))           # cadlib
from xiao_target import INV_DIR, NAMES, make_params, screen_optics  # noqa: E402

DOCS = HERE / "docs"
COL = {"body": "#e67e22", "cover": "#d35400", "tube": "#2980b9", "screen": "#ecf0f1", "riser": "#27ae60",
       "magnet": "#7f8c8d", "xiao": "#2c3e50", "cube": "#bdbdbd"}
PRINTED = ("body", "cover", "tube", "screen", "riser")


def meshes_of(step: Path, tol=0.03):
    import cadquery as cq
    shape = cq.importers.importStep(str(step)).val()
    out = []
    for s in shape.Solids():
        v, f = s.tessellate(tol, 0.2)
        if len(f) < 4:
            continue
        out.append((trimesh.Trimesh(np.array([(p.x, p.y, p.z) for p in v]), np.array(f), process=True), s.Volume()))
    return out


def classify(m, vol, refs) -> str:
    lo, hi = m.bounds
    for key, (rlo, rhi, rvol) in refs.items():
        if np.allclose(lo, rlo, atol=0.05) and np.allclose(hi, rhi, atol=0.05) and abs(vol - rvol) < 0.01 * rvol:
            return key
    d = sorted(hi - lo)
    if abs(d[0] - 3.0) < 0.05 and abs(d[2] - 8.0) < 0.05:
        return "magnet"
    if abs((hi - lo)[0] - 49.8) < 0.2 and abs((hi - lo)[1] - 49.8) < 0.2 and (hi - lo)[2] > 40:
        return "cube"                        # the two CUBHLF111 halves
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
                               alpha=0.45 if grp == "cube" else 1.0))
            for hole in poly.interiors:
                ax.add_patch(MPoly(np.array(hole.coords), closed=True, fc="white", ec="k", lw=0.3))
    ax.set_aspect("equal")
    if xlim:
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
    ax.grid(alpha=0.25)


def main() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ps = make_params()
    p = ps
    DOCS.mkdir(exist_ok=True)
    refs = {}
    printed = {}
    for key in PRINTED:
        (m, vol), = meshes_of(INV_DIR / f"{NAMES[key]}.stp")
        printed[key] = m
        refs[key] = (*m.bounds, vol)
    items = [(m, classify(m, v, refs)) for m, v in meshes_of(INV_DIR / f"{NAMES['assembly']}.stp")]
    count = {g: sum(1 for _, x in items if x == g) for g in COL}
    print("assembly solids:", count)
    problems = []
    for key in ("body", "cover", "tube", "screen"):
        if count[key] != 1:
            problems.append(f"{key}: {count[key]} solids found in the assembly STEP")
        if not printed[key].is_watertight:
            problems.append(f"{key}: mesh not watertight - sampling unreliable")

    # 1) lens mode: the view from the lens pupil to the screen field is free of printed material
    opt = screen_optics(p)
    y_lens = p.sensor_y + opt["s_i"]
    fw, fh = opt["field_w"] / 2, opt["field_h"] / 2
    starts = [(r * math.cos(a), y_lens, r * math.sin(a)) for r in (0.0, 0.8) for a in np.linspace(0, 2 * math.pi, 9)[:-1]]
    ends = [(u * fw, p.screen_d - 0.05, w * fh) for u in (-1, -0.5, 0, 0.5, 1) for w in (-1, -0.5, 0, 0.5, 1)]
    pts = np.array([np.array(s) + t * (np.array(e) - np.array(s)) for s in starts for e in ends for t in np.linspace(0.02, 1, 60)])
    hit = inside_any(pts, [printed[k] for k in ("body", "tube", "screen")])
    view_ok = not hit.any()
    if not view_ok:
        problems.append(f"lens view to the screen blocked at {hit.sum()} of {len(pts)} sample points, e.g. {np.round(pts[hit][0], 2)}")
    print(f"[{'ok' if view_ok else 'FAIL'}] lens at y {y_lens:.2f} sees the screen field {opt['field_w']:.1f} x {opt['field_h']:.1f} mm "
          f"at y {p.screen_d:g} without touching printed parts ({len(pts)} points)")

    # 2) bare chip: acceptance half-angle through the front wall (holder only, tube off), from the sensor corners
    def free(theta, corner, direction):
        d = np.array([math.sin(theta) * direction[0], math.cos(theta), math.sin(theta) * direction[1]])
        q = np.array(corner) + np.outer(np.linspace(0.2, (p.front_y + p.spigot_h + 1 - p.sensor_y) / math.cos(theta), 120), d)
        return not inside_any(q, [printed["body"]]).any()

    acc = {}
    for name, corner, direction in (("centre, x", (0, p.sensor_y, 0), (1, 0)), ("centre, z", (0, p.sensor_y, 0), (0, 1)),
                                    ("corner, outward x", (p.sensor_w / 2, p.sensor_y, p.sensor_h / 2), (1, 0)),
                                    ("corner, inward x", (p.sensor_w / 2, p.sensor_y, p.sensor_h / 2), (-1, 0))):
        lo, hi = 0.0, math.radians(89)
        for _ in range(30):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if free(mid, corner, direction) else (lo, mid)
        acc[name] = round(math.degrees(lo), 1)
    print(f"[info] bare chip, light reaches the sensor up to these angles from the axis (front wall only; the module's own "
          f"holder tube, if left on, limits further): {acc}")

    # 3) nothing printed inside the cube's parts (samples of each printed part's surface)
    cube = [m for m, g in items if g == "cube"]
    for key in ("body", "cover", "tube", "screen"):
        smp, _ = trimesh.sample.sample_surface_even(printed[key], 4000)
        smp = smp + 0.05 * printed[key].face_normals[trimesh.proximity.closest_point(printed[key], smp)[2]] * -1
        inside = inside_any(smp, cube)
        if inside.any():
            problems.append(f"{key}: {inside.sum()} surface samples inside the cube, e.g. {np.round(smp[inside][0], 2)}")
    print(f"[{'ok' if not problems else 'FAIL'}] printed parts vs cube by sampling")

    # figures: sections
    rays = [(np.array(s), np.array(e)) for s in starts[:1] for e in ((fw, p.screen_d, 0), (-fw, p.screen_d, 0), (0, p.screen_d, fh), (0, p.screen_d, -fh))]
    to_yz = np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0], [0, 0, 0, 1]], float)
    fig, ax = plt.subplots(figsize=(10, 9))
    section(ax, items, (0, 0, 0), (1, 0, 0), to_yz, (-32, 32), (-32, 36))
    for s, e in rays:
        if abs(e[0]) < 1e-6:
            ax.plot([s[1], e[1]], [s[2], e[2]], color="crimson", lw=0.8)
    ax.axhline(0, color="crimson", lw=0.5, ls="--")
    ax.annotate("beam ->", (30, 0.8), color="crimson", fontsize=8, ha="right")
    ax.set_xlabel("y [mm] (beam axis; the beam comes from +y)")
    ax.set_ylabel("z [mm]")
    ax.set_title("section x = 0: cube (grey), holder (orange), cover, XIAO (dark), magnets, screen tube (blue) + screen cap; "
                 f"lens view to the screen at {p.screen_d:g} mm (red)", fontsize=8)
    fig.tight_layout()
    fig.savefig(DOCS / "xiao_target_section_x0.png", dpi=140)
    plt.close(fig)

    to_xy = np.eye(4)
    fig, ax = plt.subplots(figsize=(10, 9))
    section(ax, items, (0, 0, 0), (0, 0, 1), to_xy, (-32, 32), (-32, 32))
    for s, e in rays:
        if abs(e[2]) < 1e-6:
            ax.plot([s[0], e[0]], [s[1], e[1]], color="crimson", lw=0.8)
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm] (beam axis)")
    ax.set_title("section z = 0 (through the sensor): holder hanging in the cube, camera module in its seat", fontsize=8)
    fig.tight_layout()
    fig.savefig(DOCS / "xiao_target_section_z0.png", dpi=140)
    plt.close(fig)

    # figures: iso views (pyvista, off screen)
    try:
        import pyvista as pv
        pv.OFF_SCREEN = True

        def render(meshes, path, title, cpos):
            pl = pv.Plotter(off_screen=True, window_size=(1400, 1100))
            for m, grp in meshes:
                pl.add_mesh(pv.wrap(m), color=COL[grp], opacity=0.35 if grp == "cube" else 1.0, smooth_shading=False,
                            show_edges=False)
            pl.add_text(title, font_size=10, color="black")
            pl.set_background("white")
            pl.camera_position = cpos
            pl.camera.zoom(1.25)
            pl.screenshot(str(path))
            pl.close()

        render(items, DOCS / "xiao_target_iso.png", "camera target hanging in an ASS-2000 cube (screen tube + cap on the beam side)",
               [(95, 120, 70), (0, 0, 2), (0, 0, 1)])
        expl = []
        offs = {"cover": (0, -25, 0), "tube": (0, 25, 0), "screen": (0, 45, 0), "riser": (0, 0, -18)}
        for m, v in meshes_of(INV_DIR / f"{NAMES['assembly']} - standalone.stp"):
            g = classify(m, v, refs)
            if g == "magnet":
                c = m.centroid
                g2 = "tube" if c[1] > p.front_y else ("riser" if c[2] < -p.cube_half else None)
                if g2:
                    m = m.copy()
                    m.apply_translation(offs[g2])
            elif g in offs:
                m = m.copy()
                m.apply_translation(offs[g])
            expl.append((m, g))
        render(expl, DOCS / "xiao_target_parts.png", "exploded: riser (green), holder + XIAO, back cover, screen tube, screen cap; 8 x 3 magnets grey",
               [(-120, 140, 70), (0, 5, -5), (0, 0, 1)])
    except Exception as exc:
        print("[warn] no iso figures:", str(exc)[:120])

    for pr in problems:
        print("[FAIL]", pr)
    print("figures written to", DOCS)
    sys.stdout.flush()
    os._exit(1 if problems else 0)


if __name__ == "__main__":
    main()
