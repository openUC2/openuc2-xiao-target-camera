# XIAO ESP32-S3 Sense beam target for the cube (rev C, 2026-11-05)

Rev A (hanging on the top bosses, 2026-10-31) is kept in `rev_a/`. Rev B (chassis PRT-9031, cover PRT-9032, ASS-9030) stays in `INVENTOR/` with Benedict's
edits of 11:47 (arms 2 mm, nose to z -23.5). Rev C is PRT-9037 + PRT-9038 + ASS-9036 and shares the key and the caps (9033-9035) with rev B.

## 0. What changed from rev B to rev C, and why

Benedict's review of rev B: the tool needs something that keeps it parallel and in the centre; he circled the four corners and tried elongating the part into the far port.

**Rev B had a real fault, and this note claimed otherwise.** It said the two rails define "x, z and all three tilts". They do not. A contact on a 45 deg chamfer pushes almost through the
axis: the force lines of all four contacts pass 1.4 mm from it. Such a contact cannot resist a rotation about the beam; the tool slides around the chamfers like a square in a circle. Only the
width of the rail flats (1.3 mm) and a weak spring term held the roll: a few tenths of a newton on top of the handle would start it rocking, until the neck hits the throat. A USB cable does that.

**Elongating was the right idea.** A throat wall pushes across the axis, at 22 mm from it: 16 times the lever. Rev C:

- The **rails stay**: the V on the chamfers still fixes x and z, the two numbers that matter.
- The **arms are longer** (root to ridge 20.4 mm instead of 15.5) and press on the **+x throat walls of the near and the far port** instead of on the chamfers. Their force still loads the V, now with a lever against the roll. The pads have a ridge, not a flat: the arm tilts as it bends, a flat would stand on one edge.
- **Two rigid lands on -x**, near port and far port, stand 0.05-0.1 mm off the -x throat walls. They touch only when something tries to roll the tool: one for each direction. They are stops, not locators.
- The **nose** reaches into the far throat, z -24.4, still inside the cube's envelope.

Benedict's two edits, and what became of them: the nose is kept, but on +x it sat on the sprung pad, which moves 1.4 mm away from the wall when seated, so it would not have touched; rev C takes the rigid contact on the -x side. His 2 mm arms on the short rev B arm
need 71 N each through the throat at 3.2 % strain. On the longer arm 2 mm is possible (1.7 %), but the straight pull-out rises to about 65 N, more than a cube's seat on its plate is likely to take, so rev C starts at 1.5 mm (`arm_t`, `arm_out`).

| | rev B | rev C (1.5 mm) | rev C with 1.25 / 2 mm arms |
| --- | --- | --- | --- |
| spring force seated, each arm | 3.8 N | 8.4 N | 4.9 / 19.6 N |
| into the V | 7.7 N | 16.8 N | 9.8 / 39 N |
| lever of the springs about the beam | 1.4 mm | 22.4 mm | |
| free rock | until the neck hits, degrees | +-0.13 deg (side) to +-0.25 deg (top), between the lands | |
| load on top of the handle before a land lifts | none: no land | 6.3 N (+x), 24.5 N (-x) | 3.7 / 14.7 N (+x) |
| arm travel, strain | 3.47 mm, 1.6 % | 2.39 mm, 1.3 % | 1.1 / 1.7 % |
| push in, peak then sliding | about 19 N | about 23 N, then 14 N | 15 then 8 / 39 then 33 N |
| straight pull out | | about 28 N, less when rocked (see 7) | 16 / 65 N |

All forces are estimates for PETG with mu 0.25. The rock moves the image centre by about 2 mm x 0.25 deg = 0.01 mm, because the tool turns about a point 2 mm from the axis.

## 1. The ask (Benedict, 2026-11-05)

> Re-iterate the design to make it more beautiful / visually appealing and robust. Between the camera and the
> XIAO there is nothing, so if the camera is floating it's not very robust. Take all the knowledge from this
> session into account. In the end we want a camera that we can slide in and observe the center of the optical
> axis maximal precise. We should be able to do that from the side or from top, where from top we may have the
> puzzle pieces - so maybe it's smarter to have some kind of snap fit (flexure spring) that fits into the
> chamfers of the cube since those are rotational symmetric and don't have the issue of the 5 mm step. Should
> have a nice industrial design and be practical. Screen with magnets still sounds good to me?

## 2. What changed from rev A to rev B

| rev A | rev B | why |
| --- | --- | --- |
| cap on the top bosses | two rigid rails + two flexure pads on the 45 deg edge chamfers | no 5 mm step: works under a puzzle piece and from the side |
| camera module floating on its flex behind a thin wall | module clamped between its seat and a wedge key | the module has a solid back; the board does not load it |
| screen tube added through the beam-side port | screen cap on the tool, everything inside the port's +-17 | goes in as one piece, also between two neighbouring cubes |
| sensor at the cube centre | sensor at y -4.5, screen at y +15.5 | 20 mm lens-to-screen distance fits inside the port |
| riser and foot | gone | a cube on the table is the stand; the chamfers do not care about the height |
| print on the cap, cover in slots | print on the front, dovetail cover | no bridges except the magnet pockets and the key slot |

## 3. Parts (provisional numbers, native parametric Inventor parts in `INVENTOR/`)

| part | what | print (no supports) |
| --- | --- | --- |
| `PRT - 9037 - CAMTARXIA - V04` | chassis: rails and lands on -x, long flexure arms on +x, nose, square camera seat, funnel and hood, stepped board pocket, slot of the wedge key, USB-C channel, waisted handle | PETG, on the front face; arms lie in the layer plane; the 1.5 mm arms all walls, 4 walls elsewhere |
| `PRT - 9038 - CAMTARCOV - V04` | back cover: dovetail, two spring tongues press the XIAO on its ledges, the slits are the vents, one M3 | PETG, on the back face |
| `PRT - 9033 - CAMTARKEY - V04` | wedge key: flat front on the module, sloped back in the sloped slot (1:12) | PETG in a second colour, on its side, so the wedge face is a wall |
| `PRT - 9034 - CAMTARSCR - V04` | screen cap: 0.6 mm white screen, target on the front for the eye, reticle on the inner face for the camera, ring that centres on the hood's cone, 2 magnets | white PETG, on the screen |
| `PRT - 9035 - CAMTARNDF - V04` | ND cap for the bare chip: D12.7 filter up to 2.5 mm, tilted ~3.5 deg by a pad, same ring and magnets | PETG, on the front |
| `ASS - 9036 - CAMTARXIA - V04` | seated in an ASS-2000 cube with a PUZ11 on top, entered from the top | |
| `ASS - 9036 - ... - side entry` | the same turned 90 deg about the beam | |

Bought: XIAO ESP32-S3 Sense, 6 x `BUY - NeFeB-Magnet - ø8x3 N40 Ni` (2 chassis, 2 per cap), M3 x 10 ISO 10642, Ruthex RX-M3Sx4.0,
a USB-C cable with a slim plug (up to 12.4 x 6.6). PLA is not recommended: the arms run at 1.6 % strain and the board gets warm
(the Sense board is known to run hot, the slits and the USB channel let the air through). On the Form 4 use Tough 2000, not Standard.

## 4. How it locates

All 12 inner edges of the cube carry the same 45 deg flat on |a| + |b| = 38.00 (measured). Behind every port the throat is only
3.9 mm long; inside it the opening widens along that flat.

- **Two rails on -x are rigid.** Each has a flat lying on a chamfer, 27 mm long, from y -15.1 to the front face. Together they are a V block that defines x and z, and the tilts about x and z.
  They do **not** define the rotation about the beam (section 0).
- **Two flexure arms on +x only push.** Each pad ridge stands 1.4 mm past the +x throat wall when free. Seated they give 8.4 N each, 16.8 N into the V (estimate for PETG).
- **Two lands on -x limit the roll**, near and far, one for each direction of rotation. The ridges sit at z +-22.4, the lands at z 21.65..23.4 and the same below: inside the throat of the top ports (21..24.9) and of the side ports (21..23.8).
- **Why not four springs.** Four balanced springs centre the tool only as well as friction lets them (about mu x spring travel, a few tenths of a mm
  here), and a cable pull of 1 N would move it by about 0.1 mm. A V with a spring stays on its contacts until the pull exceeds the preload.
- **The rails do not fit the port.** They reach 18.0, the throat 17.03, so the tool shifts 1.0 mm sideways while a rail passes, and the arm on
  the other side folds in by up to 2.39 mm (free gap 2.7 mm, then the pad stops on the neck, which protects the arm). The rail's sloped
  underside and the throat's edge do that shift by themselves. Near the end the springs pull the rail down its chamfer: the tool draws itself in, the click comes from there.
- **The lands do not hinder the entry.** While a rail is in the throat the tool is shifted toward +x, so the -x lands stay clear; they reach their wall only in the last millimetre.
- **Same from four sides.** The tool turned 90 deg about the beam enters a side port and lands on the next pair of chamfers. A puzzle piece on top
  changes nothing (the check sweeps both entries through both throats). The camera image turns with the tool; the mark for "up" on the reticle tells the software which way.
- **Along the beam** only friction holds the tool. Its back reaches the throat's wall (0.23 mm clearance), which gives a defined position: push it away from the beam. It could slide up to 4.8 mm forward from there, which does not matter for a beam parallel to the axis.

## 5. The camera no longer floats

The module sits on a 10 mm flex in front of the microSD socket, with nothing behind it (vendor model: 0.2 to 3.7 mm of air). Rev B:

- The square block of the module sits in a seat 8.2 x 8.2 and stops with its front on the seat floor.
- A wedge key is pushed in from the left side, into the gap between the module's back and the USB-C shell, above the Sense PCB. Its flat front lies on
  82 % of the module's back and presses it onto the seat floor. The lower edge stays free: the flex leaves there.
- The key's sloped back runs on a sloped slot wall in the left and right walls of the chassis, so the clamping force goes into the chassis, not into the USB-C
  shell or the board. 1:12 is self-locking; the key's position takes up the tolerance (0.1 mm of stack = 1.2 mm of key travel; nominal head 1.5 mm under the wall).
- The XIAO stack is held on its own: main PCB on the pocket floor (USB-C insertion) and under two shoulders (pulling a plug), Sense PCB on two ledges beside the socket, pressed
  there by the cover's tongues. Neither touches the module; the flex stays relaxed.

Cost: no microSD card in this tool (the key is where the card would be; the vendor model shows a card, which is the only overlap there). Streaming does not need it.

## 6. Screen on magnets: yes

The screen stays the main mode and it stays magnetic, with four changes:

1. **It is the reference, not the camera.** The camera only images it, so the module's tolerance no longer matters in this mode.
2. **Cone instead of a plain spigot.** The cap's ring lands on the hood's 45 deg chamfer, pulled by the magnets: no play, the cap's back stays 0.1 mm off the face.
3. **Keyed.** Top magnet N out on the chassis, bottom S out, the cap the opposite way: the wrong way round repels. Magnets sit 0.4 mm under each face, 0.9 mm apart: firm, still removable.
4. **Reticle on the inner face**, one line wide, open inside r 1.5 so that it does not cut the beam's centre, with ticks at r 5 and a mark for up. The target on the front is for the eye.

Optics as in rev A: lens ~1 mm unscrewed from infinity focus, screen 20 mm from the sensor, field 12 x 9 mm, all with the assumed f 3.5 mm.
The bare chip works behind the ND cap: light reaches the sensor up to 31.7 deg (from a corner 18.6 to 35.7 deg, chassis only), and the filter is tilted so
that its reflections leave the chip, as Bullseye's notes ask. Leave the glass on the sensor.

## 7. Using it, and how the 4 fold symmetry buys precision

Printed parts land within maybe +-0.3 mm of the axis (rails +-0.1, seat +-0.1, sensor in its module +-0.1..0.2; estimates, nothing measured yet). The repeatability
should be far better, and the symmetry lets the tool calibrate itself without a known beam:

1. Beam fixed, tool from the top: reading r0 (beam relative to the reticle or the sensor centre, in raw image coordinates).
2. Tool from the side: reading r1, in the same raw image coordinates, not turned back.
3. r0 = b - t and r1 = R b - t, with b the beam's offset from the cube axis, t the tool's own offset and R the 90 deg turn. Two readings give both: b = (1 - R)^-1 (r0 - r1), t = b - r0.
4. Store t with the tool; from then on one reading gives the true offset. Repeat after re-gluing or swapping a cap.

For the beam's angle measure in two cubes along the path, like two irises, and walk the beam with two mirrors (BeamDelta's procedure).

Assembly:

1. Flash the firmware first: the buttons are out of reach afterwards.
2. Glue the magnets, mind the poles. Press the Ruthex insert into the neck.
3. Set the lens focus for the screen later, from the front, with the cap off.
4. Put the module into its seat from the back, lay the XIAO into the pocket. No microSD card.
5. Push the key in from the left until it stops, firm, not hard. Lever it out at the notch.
6. Slide the cover down from the top, one M3 x 10.
7. Plug USB-C from the top, cap on, push the tool into an empty cube until it clicks.
8. To take it out, hold the cube, tip the handle toward the arms by a few degrees (about 10 N, this lifts the near rail off its chamfer), then pull at the waist. A straight pull needs about 28 N, which could lift a cube off its plate.

## 8. Measured facts (ASS-2000, STEP, this session)

| fact | value |
| --- | --- |
| edge chamfers | all 12 edges, flat on \|a\| + \|b\| = 38.00, from (17.03, 20.97) to (21, 17) |
| port throat | top/bottom: walls +-17.03 at the lip with draft, +-17.05 at z 23, for z 20.97..24.9; side: +-17.00, for 21..23.8, then a 1.1 chamfer |
| notches | only on the +-x walls of the top and bottom ports, y 0, +-5, +-10, +-15, 2 mm wide at the wall, 0.9 deep; the chamfer starts at 17.92 there |
| XIAO camera module | 8 x 8 block y' -0.65..1.45 (y' = from the assumed sensor plane), ring D7.85 to 3.35, lens to 5.11; flex leaves at the lower edge, x +-3 |
| behind the module | Sense PCB ends at z -3.05, USB-C shell front at y' -4.39: a 3.7 mm slot open to the sides and the top |
| PUZ11 part frame | z -30..-25: origin at z 55 to lay it on a cube |

## 9. Checks (rev C)

- Design checks (`xiao_target.py`): all pass. Flexure estimate: k 6.0 N/mm, strain 1.3 % through the throat.
- Inventor interference, all pairs, both assemblies; every overlap classified: the two pads on the throat walls (84 mm3 top, 114 mm3 side, their preload), thread insert in its hole, screw in the
  insert, cover bumps on the main PCB (0.1 mm), key on the module's back (0.05 mm), and the microSD card that the vendor model shows (chassis and key). Nothing with the puzzle piece.
- STEP sampling (`check_xiao_target.py`): rail flats parallel to the real chamfers (contact 100 % near the tip, 69 % at the inner end where the notches cut it, top entry);
  seated from the top and from the side only the pads overlap the cube; land gaps on the real walls 0.099 mm (top entry, walls under 65 % of the length, the rest are the notches) and 0.050 mm (side entry, 100 %);
  pad ridges 1.38 / 1.43 mm past the wall; rigid parts pass both throats from the top with a puzzle piece and from the side, shift at most 1.0 mm, arms yield 2.39 mm; lens view of the 12 x 9 mm field clear;
  USB-C plug 12.4 x 6.6 clear up to the top; the key backs 82 % of the module.
- Figures: `xiao_target_roll.png` (the levers), `_hero.png`, `_back.png`, `_iso.png`, `_side_entry.png`, `_parts.png`, `_entry.png`, `_section_x0.png`, `_section_y.png`.

Not tested: nothing has been printed yet. Forces, strain, repeatability and the calibration are estimates. The moment calculation treats the lands as rigid and the arms as beams; printing decides.

Build: `python build_xiao_target.py --only chassis cover`. It runs in its own hidden Inventor and never attaches to the one in use. The blend `r_flare` is in the rev C parts; rev B's kink at the neck is gone.

## 10. Open points

1. Print one chassis first: the port fit, the arms and the click are what a print decides. Knobs: `arm_t` with `arm_out` (stiffness, keep arm_in 15), `pad_over` (preload), `land_gap` (if a land stands on the wall and lifts a rail, raise it), `rail_tip` (1 mm shift), `seat_clr`.
2. Lens focal length and sensor plane: please measure (assumed f 3.5, sensor 0.65 mm above the module's back). With the sensor elsewhere `screen_d` moves.
3. Can your module's lens be unscrewed by 1 mm? If it is glued, the screen mode needs another distance.
4. Does the real module back have components where the key presses? The vendor model is flat.
5. Numbers 9030-9038 are provisional.
6. If 28 N out is too much even with the rocking, a thumb tab on the near arm above the cube could lift the near pad by hand. Not built.
