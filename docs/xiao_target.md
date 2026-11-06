# XIAO ESP32-S3 Sense beam target for the cube

Older variants are in the git history (commit `ec8295e`).

## 1. What it has to do

Slide in, from the top with or without a puzzle piece or from the side, and observe the centre of the optical axis as precisely as a printed part allows. No face outside the cube can be used: the top of a puzzle piece and a bare cube face are 5 mm apart. So the tool locates on the cube's 45 deg edge chamfers, which are the same everywhere.

## 2. Parts (provisional numbers, native parametric Inventor parts in `INVENTOR/`)

| part | what | print (no supports) |
| --- | --- | --- |
| `PRT - 9040 - CAMTARXIA - V04` | chassis: rails and lands on -x, long flexure arms on +x, nose, square camera seat, funnel and hood, stepped board pocket, slot of the wedge key, lens tube with jaw and lock screw, USB-C channel, long stick with grip waist and stop shoulder | PETG, on the front face; arms lie in the layer plane; the 1.5 mm arms all walls, 4 walls elsewhere |
| `PRT - 9041 - CAMTARCOV - V04` | back cover: lies in a recess of the back (0.3 mm clearance per side), three M3 screws, two spring tongues press the XIAO on its ledges, the slits are the vents | PETG, on the back face |
| `PRT - 9033 - CAMTARKEY - V04` | wedge key: flat front on the module, sloped back in the sloped slot (1:12) | PETG in a second colour, on its side, so the wedge face is a wall |
| `PRT - 9034 - CAMTARSCR - V04` | screen cap: 0.6 mm white screen, target on the front for the eye, reticle on the inner face for the camera, ring that centres on the hood's cone, 2 magnets | white PETG, on the screen |
| `PRT - 9035 - CAMTARNDF - V04` | ND cap for the bare chip: D12.7 filter up to 2.5 mm, tilted ~3.5 deg by a pad, same ring and magnets | PETG, on the front |
| `ASS - 9039 - CAMTARXIA - V04` | seated in an ASS-2000 cube with a PUZ11 on top, entered from the top | |
| `ASS - 9039 - ... - side entry` | the same turned 90 deg about the beam | |

Bought: XIAO ESP32-S3 Sense, 6 x `BUY - NeFeB-Magnet - ø8x3 N40 Ni` (2 chassis, 2 per cap), 3 x M3 x 10 ISO 10642, 1 x M3 x 8 ISO 4762, 4 x Ruthex RX-M3Sx4.0,
a USB-C cable with a slim plug (up to 12.4 x 6.6). PLA is not recommended: the arms run at 1.6 % strain and the board gets warm
(the Sense board is known to run hot, the slits and the USB channel let the air through). On the Form 4 use Tough 2000, not Standard.

## 3. How it locates

All 12 inner edges of the cube carry the same 45 deg flat on |a| + |b| = 38.00 (measured). Behind every port the throat is only
3.9 mm long; inside it the opening widens along that flat.

- **Two rails on -x are rigid.** Each has a flat lying on a chamfer, 27 mm long, from y -15.1 to the front face. Together they are a V block that defines x and z, and the tilts about x and z.
  They do **not** define the rotation about the beam: a contact on a 45 deg chamfer pushes almost through the axis (force lines 1.4 mm from it), so it cannot resist that rotation.
- **Two flexure arms on +x push and click.** Each pad ridge stands 1.2 mm past its seat in the corner of the +x chamfer and the throat wall when free. Seated they give 7.1 N each, 14.2 N into the V; pushing in peaks at about 19 N, a straight pull starts at 24 N and peaks at 36 N (estimates for PETG, mu 0.25).
  The ridges sit on the chamfer just below its corner with the throat wall, the only groove a cube has; that gives the click.
- **Two lands on -x limit the roll**, near and far, one for each direction of rotation, with a lever of 22 mm. They stand 0.05-0.1 mm off the walls: stops, not locators. The rock of +-0.13 to 0.25 deg moves the image centre by about 0.01 mm. The lands sit at z 21.65..23.4 and the same below: inside the throat of the top ports (21..24.9) and of the side ports (21..23.8).
- **Hard stop.** To go deeper than the seat the far rail must climb its chamfer, which moves the tool toward +x. The +x shoulder of the stick (x 16.1) then enters the near throat and meets the wall after 0.93 mm; the far rail (18.4 instead of 18.0) still bites 0.44 mm on its chamfer. Let go and the springs lift the tool back. On the way in the shoulder is still above the lip while the near rail needs the throat (shift 0.97 mm), and has 0.18 mm to spare in a puzzle piece.
- **The stick** reaches z 70, +-16.1 wide, grip at z 57, 14 mm thick. Above z 31.5 the USB channel is open at the back. A long stick is a long lever: a rail lifts at 3.5 N (+x) / 6.7 N (-x) at the top and comes back when released, so let go of it for a measurement. `top_z` shortens it.
- **Why not four springs.** Four balanced springs centre the tool only as well as friction lets them (about mu x spring travel, a few tenths of a mm
  here), and a cable pull of 1 N would move it by about 0.1 mm. A V with a spring stays on its contacts until the pull exceeds the preload.
- **The rails do not fit the port.** They reach 18.0 (near) and 18.4 (far), the throat 17.03, so the tool shifts 1.0 to 1.4 mm sideways while a rail passes, and the arm on
  the other side folds in by 2.49 mm (near) and 2.89 mm (far). The rail's sloped
  underside and the throat's edge do that shift by themselves. Near the end the springs pull the rail down its chamfer: the tool draws itself in, the click comes from there.
- **The lands do not hinder the entry.** While a rail is in the throat the tool is shifted toward +x, so the -x lands stay clear; they reach their wall only in the last millimetre.
- **Same from four sides.** The tool turned 90 deg about the beam enters a side port and lands on the next pair of chamfers. A puzzle piece on top
  changes nothing (the check sweeps both entries through both throats). The camera image turns with the tool; the mark for "up" on the reticle tells the software which way.
- **Along the beam** only friction holds the tool. Its back reaches the throat's wall (0.23 mm clearance), which gives a defined position: push it away from the beam. It could slide up to 4.8 mm forward from there, which does not matter for a beam parallel to the axis.

## 4. The camera does not float

The module sits on a 10 mm flex in front of the microSD socket, with nothing behind it (vendor model: 0.2 to 3.7 mm of air). So:

- The square block of the module sits in a seat 8.4 x 8.4 and stops with its front on the seat floor.
- A wedge key is pushed in from the left side, into the gap between the module's back and the USB-C shell, above the Sense PCB. Its flat front lies on
  82 % of the module's back and presses it onto the seat floor. The lower edge stays free: the flex leaves there.
- The key's sloped back runs on a sloped slot wall in the left and right walls of the chassis, so the clamping force goes into the chassis, not into the USB-C
  shell or the board. 1:12 is self-locking; the key's position takes up the tolerance (0.1 mm of stack = 1.2 mm of key travel; nominal head 1.5 mm under the wall).
- The XIAO stack is held on its own: main PCB on the pocket floor (USB-C insertion) and under two shoulders (pulling a plug), Sense PCB on two ledges beside the socket, pressed
  there by the cover's tongues. Neither touches the module; the flex stays relaxed.

Clearances are set for an FDM printer: 0.5 mm around the PCBs and connectors, 0.2 mm per side around the module, 0.15 mm around the key, 0.3 mm around the cover. The cover is screwed, three M3 into Ruthex inserts: two beside the USB channel at z 27, one in the nose at z -20.9.

Cost: no microSD card in this tool (the key is where the card would be; the vendor model shows a card, which is the only overlap there). Streaming does not need it.

## 5. Screen on magnets

The screen stays the main mode and it stays magnetic, with four changes:

1. **It is the reference, not the camera.** The camera only images it, so the module's tolerance no longer matters in this mode.
2. **Cone instead of a plain spigot.** The cap's ring lands on the hood's 45 deg chamfer, pulled by the magnets: no play, the cap's back stays 0.1 mm off the face.
3. **Keyed.** Top magnet N out on the chassis, bottom S out, the cap the opposite way: the wrong way round repels. Magnets sit 0.4 mm under each face, 0.9 mm apart: firm, still removable.
4. **Reticle on the inner face**, one line wide, open inside r 1.5 so that it does not cut the beam's centre, with ticks at r 5 and a mark for up. The target on the front is for the eye.

**Lens outside the module.** The thread of the module does not let the lens come far enough forward for a screen this close, so the lens is unscrewed completely and held in front of the sensor, in a tube that stands free in the funnel. The bore is D6.9 for a lens of D6.32 (vendor model, please measure), from y -1 to y 5; the sensor is at y -4.5, so "4 mm in front" is y -0.5. The lens slides in the bore and a thin jaw on the -x side of the tube, between two slits, presses it against the far side, driven by an M3 x 8 through the left wall (thread insert, head in a recess, reachable through the cube's -x port). The jaw takes the screw's point away from the lens; if it cracks after many cycles it still clamps. With f 3.5 mm (assumed) sharp imaging of the screen needs the lens plane 4.52 mm from the sensor, 12 x 9 mm field; the slide covers the unknowns. The assembly shows the vendor's module with the lens in it.

The bare chip works behind the ND cap, lens removed. The tube narrows its view: light reaches the sensor up to 20.2 deg (from a corner 8.6 to 35.7 deg, chassis only); a collimated beam does not care. The filter is tilted so that its reflections leave the chip. Leave the glass on the sensor.

## 6. Using it, and how the 4 fold symmetry buys precision

Printed parts land within maybe +-0.3 mm of the axis (rails +-0.1, seat +-0.1, sensor in its module +-0.1..0.2; estimates, nothing measured yet). The repeatability
should be far better, and the symmetry lets the tool calibrate itself without a known beam:

1. Beam fixed, tool from the top: reading r0 (beam relative to the reticle or the sensor centre, in raw image coordinates).
2. Tool from the side: reading r1, in the same raw image coordinates, not turned back.
3. r0 = b - t and r1 = R b - t, with b the beam's offset from the cube axis, t the tool's own offset and R the 90 deg turn. Two readings give both: b = (1 - R)^-1 (r0 - r1), t = b - r0.
4. Store t with the tool; from then on one reading gives the true offset. Repeat after re-gluing or swapping a cap.

For the beam's angle measure in two cubes along the path, like two irises, and walk the beam with two mirrors (BeamDelta's procedure).

Assembly:

1. Flash the firmware first: the buttons are out of reach afterwards.
2. Glue the magnets, mind the poles. Press the four Ruthex inserts: three in the back, one in the recess in the left wall.
3. Unscrew the lens completely from the module.
4. Put the module into its seat from the back, lay the XIAO into the pocket. No microSD card.
5. Push the key in from the left until it stops, firm, not hard. Lever it out at the notch.
6. Put the cover on, three M3 x 10.
7. Slide the lens into the tube from the front, rear end about 4 mm in front of the sensor, lock it gently. Plug USB-C from the back of the stick, cap on, look at the live image; loosen, cap off, move the lens, repeat until the reticle is sharp.
8. Push the tool into an empty cube until it clicks.
9. To take it out, hold the cube, tip the stick toward the arms by 1-2 deg (about 2 mm at the top, about 5 N, estimate; this lifts the near rail off its chamfer) and pull while it is tipped. A straight pull takes up to 36 N.

## 7. Measured facts (ASS-2000, STEP)

| fact | value |
| --- | --- |
| edge chamfers | all 12 edges, flat on \|a\| + \|b\| = 38.00, from (17.03, 20.97) to (21, 17) |
| port throat | top/bottom: walls +-17.03 at the lip with draft, +-17.05 at z 23, for z 20.97..24.9; side: +-17.00, for 21..23.8, then a 1.1 chamfer |
| notches | only on the +-x walls of the top and bottom ports, y 0, +-5, +-10, +-15, 2 mm wide at the wall, 0.9 deep; the chamfer starts at 17.92 there |
| XIAO camera module | 8 x 8 block y' -0.65..1.45 (y' = from the assumed sensor plane), ring D7.85 to 3.35, lens to 5.11; flex leaves at the lower edge, x +-3 |
| behind the module | Sense PCB ends at z -3.05, USB-C shell front at y' -4.39: a 3.7 mm slot open to the sides and the top |
| PUZ11 part frame | z -30..-25: origin at z 55 to lay it on a cube |

## 8. Checks

- Design checks (`xiao_target.py`): all pass. Flexure estimate: k 5.9 N/mm, strain 1.7 % through the throat.
- Inventor interference, all pairs, both assemblies; every overlap classified: the two pads on the chamfers (85 mm3 top, 106 mm3 side, their preload, the parts are modelled as printed), thread inserts in their holes, screws in their
  inserts, cover bumps on the main PCB (0.1 mm), key on the module's back (0.05 mm), and the microSD card that the vendor model shows (chassis and key). Nothing with the puzzle piece.
- STEP sampling (`check_xiao_target.py`): rail flats parallel to the real chamfers (contact 100 % near the tip, 69 % at the inner end where the notches cut it, top entry);
  seated from the top and from the side only the pads overlap the cube; land gaps on the real walls 0.099 mm (top) and 0.050 mm (side); pad ridges 1.20 mm past the real chamfer, chamfer under 75 % of the length from the top (the notches), 100 % from the side;
  rigid parts pass both throats from the top with a puzzle piece and from the side, shift at most 1.4 mm, arms yield 2.9 mm; hard stop 0.9 mm past the seat, top and side; lens view of the 12 x 9 mm field clear; a D6.32 lens slides the whole bore, the jaw is cut free, the lock screw's path is open;
  USB-C plug 12.4 x 6.6 clear up to the top; the key backs 82 % of the module.
- Figures: `xiao_target_entry.png` (entry, seat, overshoot), `_section_y.png`, `_lens.png`, `_roll.png`, `_hero.png`, `_back.png`, `_iso.png`, `_side_entry.png`, `_parts.png`, `_section_x0.png`.

Printed once before the cover, clearance and lens changes: the seat and the snap fit work. Not tested: the screwed cover, the new clearances and the lens tube. Forces, repeatability and the calibration are estimates.

Build: `python build_xiao_target.py --only chassis cover key`. It runs in its own hidden Inventor and never attaches to the one in use.

## 9. Open points

1. Knobs for the next print: `arm_t` (stiffness; 1.5 mm gives 8.7 N per arm, 45 N peak pull), `pad_over` (preload), `bar_half` (stop gap), `top_z` (stick length), `land_gap` (if a land stands on the wall and lifts a rail, raise it), `clr_board`, `seat_clr`, `lens_hole_d`.
2. Lens: please measure the barrel's diameter and length, and the distance that gives a sharp reticle. `lens_d` and `lens_f` are assumed; a loose fit is taken up by `lens_hole_d`.
3. Focusing needs the cap off to move the lens and on to see the reticle. If that is too slow, a window or a screw drive for the lens is the next step.
4. The module's seat now has 0.2 mm per side, which moves the sensor by up to 0.2 mm. The two-entry calibration in section 6 removes that and the lens's own offset.
5. Does the real module back have components where the key presses? The vendor model is flat.
6. Numbers 9033-9035, 9039-9041 are provisional.
