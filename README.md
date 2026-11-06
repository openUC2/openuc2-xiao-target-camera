# openuc2-xiao-target

Beam target for the openUC2 cube: a XIAO ESP32-S3 Sense in a printed tool that slides into an empty cube from the
top (with or without a puzzle piece) or from the side and seats on the cube's 45 deg edge chamfers: two rigid rails
like a V block, two flexure arms that push them in. The camera sees a magnetic screen with a reticle (12 x 9 mm field),
or the bare chip behind a magnetic ND cap. The tool's 4 fold symmetry lets it calibrate itself: read the beam from the
top and from the side. Design note: [`docs/xiao_target.md`](docs/xiao_target.md).

| file | what it does |
| --- | --- |
| `xiao_target.py` | parameters (one table for Python and Inventor), design checks, screen optics, flexure estimate |
| `build_xiao_target.py` | native parametric Inventor parts, assemblies (entry from the top / side), interference, STEP + STL |
| `check_xiao_target.py` | checks on the STEP (rails on the chamfers, passage through the port, lens view, USB-C, key) and figures |
| `cadlib/` | copy of openuc2-frame-opm/common/cadlib |
| `INVENTOR/` | parts, assemblies, STEP/STL, build.json, check_results.json |
| `rev_a/` | rev A (hung on the top bosses), scripts, parts, note |
| `rev_c/` | scripts and note of rev C (its parts stay in `INVENTOR/`) |

```bash
python xiao_target.py --set arm_t=1.2
C:\Users\benir\miniforge3\envs\pyinventor\python.exe build_xiao_target.py
uv run --with cadquery --with trimesh --with rtree --with scipy --with shapely --with networkx --with matplotlib --with pyvista --with pillow --with embreex python check_xiao_target.py
```
