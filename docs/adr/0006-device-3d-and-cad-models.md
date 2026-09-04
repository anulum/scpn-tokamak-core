<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Tokamak Core — ADR 0006
-->

# ADR 0006 — Device 3D and CAD models of the cylindrical periodic equivalent

Status: accepted (2026-09-04). Adds the fourth and fifth implemented
capabilities, `device_3d_model` and `device_cad_model`, under the
evidence-maturity ceiling rule of ADR 0002.

## Context

A tokamak plasma is a torus with a shaped cross-section, and every
primitive the shared kernel library builds is a solid of revolution about
`z`. That looks like an obstruction and is not one: an axisymmetric torus
*is* a solid of revolution, and the standard reduced model of one — the
same the reversed-field-pinch family already uses — unrolls it into a
straight cylinder of periodic length `2 pi R0`.

What that construction drops is the toroidal curvature, and with it every
quantity that distinguishes the inboard side of a torus from the outboard
one. It is a real limitation and the model records say so rather than
leaving a reader to infer it.

## Decision

Build the two tiers on the cylindrical periodic equivalent, with three
bodies: the plasma column, the vacuum vessel wall at its edge, and the
toroidal-field winding outside the gap.

**The elongation is carried, not discarded.** The column is built at the
*area-equivalent* radius `a sqrt(kappa)`, so its circular cross-section
has the ellipse's area and its volume over the periodic length is exactly
the volume
`scpn_tokamak_core.physics.equilibrium.plasma_volume_m3` computes by
Pappus's theorem. Building at `a` would have thrown away a declared
parameter and left the two capabilities disagreeing about the same
plasma.

**The triangularity is not carried, and cannot be.** No body of
revolution can represent a fore-aft asymmetry. The physics record already
says the triangularity does not enter its volume; the geometry tests say
the same about the bodies, by building two configurations that differ only
in triangularity and showing every body's volume identical.

**The package is named `device`, not `geometry`.** Every sibling family
uses `geometry`; here `scpn_tokamak_core.geometry` already belongs to the
plasma shape, because for a tokamak the shape is a configuration
parameter. Renaming a published submodule to free the word is the owner's
decision, not a tier landing's, so the tier took the other name and this
record says why.

The envelope refuses a radial build that reaches half the periodic
length, because an unrolled machine wider than that self-intersects. The
refusal names the field and prints both sides.

## The faceting deflections, and why this family differs

The tier-G2 evidence kernel checks each body's faceted volume against a
declared bound of `2 d / r`, with `d` the linear deflection and `r` the
body's smallest circular radius. Every magneto-inertial family in this
group tunes `d` to control that check.

**On this family that is the wrong knob, and copying it would have been a
silent error.** Those devices are millimetres across, so `2 d / r` is
loose and the linear criterion binds the mesher. This one is metres
across, which makes `2 d / r` tight, and the mesher's *angular* criterion
is what sets the tessellation.

Measured, not assumed:

- Across a tenfold change in the linear deflection — 1e-4 down to 1e-5 —
  the relative faceting deficit did not move at all. It stayed at
  1.663e-5 to nine significant figures.
- Halving the angular deflection quartered it, which is the square law an
  inscribed polygon obeys.
- The deficit is the same for all three bodies and both anchored regimes,
  though their radii differ by tens of per cent and a factor of nearly
  two. An angular criterion divides every circle into the same number of
  segments whatever its radius, so the relative area lost is a constant of
  the angular step alone.

So the declared angular deflection is 0.02 rad, at which every body of
both regimes clears its bound by between five and nine times and a build
costs about a second. A test asserts the consequence directly: a tenfold
finer linear deflection is **refused**, because it tightens the bound
tenfold and leaves the faceting untouched.

## Consequences

Both capabilities are registered at `computational_prototype` with their
evidence pointers in `VALIDATION.md`, and the package carries 100 %
statement and branch coverage.

This landing gives the repository its first dependency. It pins the
shared kernel library by commit, with the CAD back-end as an optional
extra naming the same commit, and CI gains an install step and the system
library the mesher links against.

The cross-capability identity is the tier's strongest statement: the
tier-G1 column volume over the physics record's Pappus volume is the
inscribed-polygon ratio and nothing else. It is asserted within a
relative tolerance rather than as an equality, because the two sides
group their factors differently and a mesh volume is a sum over many
triangles; measured, the gap runs from 3 units in the last place at 8
segments to 133 at 256, which is 3e-14 relative.
