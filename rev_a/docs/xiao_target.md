# XIAO ESP32-S3 Sense camera target for the cube (rev A, 2026-10-31)

## 1. The ask (Benedict, 2026-10-31)

> A little camera holder for the XIAO ESP32 S3 camera that we can slide into the cube, centred on the
> optical axis, to observe beams centred or off-centre. First remove the lens so the bare chip faces the
> laser beam; then a magnetic adapter that attaches the lens and a screen at e.g. 10 mm from the sensor,
> for a larger field of view. Perpendicular to the optical axis, hanging like the Thorlabs VRC1CPT
> "T-shirt" target hangs down a cage system. The 5 mm puzzle-piece elevation switchable with a little
> magnetic adapter. Magnets ø8x3. Easy to assemble, easy to print. (MAS-2010 is a similar slide-in, but
> its grooves do not help.)

## 2. What was built (provisional numbers, all in `INVENTOR/`, native parametric Inventor parts)

| part | what | print (FDM, no supports) |
| --- | --- | --- |
| `PRT - 9021 - CAMTARXIA - V04` | holder: cap ("shoulders") on the cube's top face with pockets for four top corner bosses, plate hanging down through the top port, square seat for the camera module on the axis, board pocket open at the back, USB-C / microSD channel up through the cap, 2 front + 2 foot magnet pockets, spigot Ø12 for the tube, alignment marks | upside down on the cap |
| `PRT - 9022 - CAMTARCOV - V04` | back cover: slides down through the cap into the side-wall slots, two ribs press the board forward, notch for the plug, two pull tabs | flat, ribs up |
| `PRT - 9023 - CAMTARTUB - V04` | screen tube: recess onto the spigot, 2 magnets, tube Ø20 | flange back on the bed |
| `PRT - 9024 - CAMTARSCR - V04` | screen cap: 0.6 mm printed screen (white), skirt slides on the tube | screen down |
| `PRT - 9025 - CAMTARRIS - V04` | 5 mm riser with 2 magnets and a 1 mm rim around the holder's foot | flat |
| `ASS - 9020 - CAMTARXIA - V04` | holder hanging in an ASS-2000 cube with the XIAO, tube, screen cap and 6 magnets | |
| `ASS - 9020 - ... - standalone` | the same on the riser, no cube | |

Magnets: 8 x `BUY - NeFeB-Magnet - ø8x3 N40 Ni` per complete set (holder front 2, tube 2, holder foot 2,
riser 2). Glue them into the 8.2 pockets; mind the poles: holder front N out / tube S out, holder foot N
out / riser S out.

Assembly: (1) lens out for the bare chip test (or in, see 4); (2) XIAO into the board pocket from the back,
camera module first into its square seat; (3) cover down through the cap slot; (4) plug USB-C from above
through the cap; (5) hang the holder into a cube from the top - the cap's four pockets drop onto the
bosses at (±20.65, ±14.5), so the sensor is on the cube axis without adjusting; (6) for the screen, put
the tube on the spigot (magnets) and slide the cap to the wanted distance. Without a cube the holder
stands on its foot: sensor 24.9 mm above the table (cube without puzzle); on the riser 29.9 mm (cube on
PUZ11 pieces).

## 3. Optics of the screen mode

The beam hits the printed screen; the camera images the screen's back side. With the lens back in
its holder (f ≈ 3.5 mm assumed), a screen at D from the sensor needs D ≥ 4 f ≈ 14 mm - **10 mm cannot
be imaged** (it would need f ≤ 2.5 mm). Default D = 20 mm: lens 4.5 mm from the sensor (unscrew it ~1 mm
from infinity focus), magnification 0.29, field on the screen 12 x 9 mm. The cap slides from D 15 to 22
(field ~5 to ~16 mm wide): change `screen_d`, `tube_end_y`, `skirt` for other ranges.

| D (mm) | lens to sensor | m | field |
| --- | --- | --- | --- |
| 16 | 5.2 | 0.48 | 7.4 x 5.5 |
| 20 | 4.5 | 0.29 | 12.0 x 9.0 |
| 24 | 4.25 | 0.22 | 16.4 x 12.3 (cap leaves the cube face, fine on the table) |

## 4. Decisions (to confirm)

1. **The lens stays in the camera module's own holder in screen mode**, and the tube carries only the screen.
   To make the field larger than the sensor, the lens must sit ~4.5 mm from the sensor, and the module's
   holder tube (Ø7.85) already fills that space. A lens carried by the tube would sit ≥ 6 mm out, with a
   magnification near 1, so the field would not grow. If your module's holder comes off with the lens,
   a lens seat in the tube is a small change.
2. Hangs from the top on the cube's own bosses (no grooves, no notch tracks): it centres in x and y by
   the four pockets and in z by the cap on the top face. Expected centring ±0.3 mm (FDM pockets 5.3 on
   bosses 4.9, module seat 8.3 on 8.0, sensor in its module); `boss_pocket_d` 5.1 for SLA.
3. The camera module locates, not the board: the module is on its flex cable, so its square seat sets the
   sensor position; the board floats 0.4 mm in its pocket and is pressed forward by the cover's ribs.
4. USB-C points up and leaves through the cap, so the cube's faces stay free. The microSD mouth is in the
   same channel.
5. Foot with 45 deg slopes so the holder stands by itself and prints without support; it sits inside the
   cube's bottom port, flush with the cube bottom.
6. Sensor plane = cube centre plane (`sensor_y` 0); the beam comes from +y.

## 5. Measured facts (vendor model, frame bx, by, bz; camera looks +by)

Camera axis (bx 8.75, bz -6.75); module base 8 x 8 at by 7.95..10.05, holder tube Ø7.85 to 11.95, lens Ø6.3 /
Ø5.3 / Ø4.65 to 13.71; main PCB back by -0.25; microSD socket by 6.6..8.25, mouth bx 15.39 (beyond the USB-C at
13.81, same end); USB-C centre (by 2.11, bz -6.12); board bx -8.97..13.81, bz -15..2.78. Sensor plane
**assumed** at by 8.6 (module base + 0.65) - please measure. Cube: top bosses Ø4.9 x 1.9 at (±20.65, ±14.5)
and (±14.5, ±20.65), ports ±17.

## 6. Checks (rev A)

- Design checks (`xiao_target.py`): all pass.
- Inventor interference, both assemblies, all pairs: none. Rev A first found the microSD socket (sticks out
  1.2 mm beyond the USB-C) in the pocket roof; the pocket and channel now include it.
- STEP sampling (`check_xiao_target.py`): the lens's view of the full 12 x 9 mm screen field is free of
  printed material (24000 points); printed parts not inside the cube; bare-chip acceptance through the front
  wall 33 deg from the sensor centre, 15..43 deg from a corner (the module's own holder tube, if left on,
  limits more).
- Figures: `xiao_target_section_x0.png`, `_section_z0.png`, `_iso.png`, `_parts.png`.

## 7. Open points

1. Lens mode: OK to keep the lens in the module's holder (decision 1), or does your module's holder come off?
2. Lens focal length and sensor plane: please measure (assumed f 3.5, sensor 0.65 mm above the module base).
3. Screen: printed 0.6 mm white, or a slot for paper / ground glass / a printed mm grid?
4. FDM or SLA? The tolerances are FDM; for SLA set `boss_pocket_d` 5.1, `seat_clr` 0.1, `mag_fit` 0.15.
5. Numbers 9020-9025 are provisional.
