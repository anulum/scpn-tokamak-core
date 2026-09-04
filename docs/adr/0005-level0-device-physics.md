<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Tokamak Core — ADR 0005
-->

# ADR 0005 — Level-0 device physics: compose, do not restate

Status: accepted (2026-09-04). Adds the third implemented capability,
`level0_device_physics`, at `computational_prototype`.

## Context

This repository is unlike the other device families of the group in one
respect: it already carried physics. `OperationalLimits` computes the
Greenwald density limit and an elongation-corrected cylindrical safety
factor, and `ToroidalGeometry` computes the aspect ratio.

That changes what a level-0 capability should be here. In the families
that had nothing, the level-0 package **is** the physics. Here, most of
it exists and the question is what a record adds.

## Decision

1. **The record composes; it does not restate.** The density limit and the
   safety factor stay on `OperationalLimits`, and this package calls them.
   A level-0 module that reimplemented its own repository's relations
   would be two sources of truth for one number, and the drift would be
   invisible until they disagreed. A test asserts the record's values are
   the ones the configuration's own methods return.

2. **What it adds are the three closed forms nothing owned yet**, each
   exact rather than fitted:

   *Plasma volume* by Pappus's theorem — an ellipse of area `pi kappa a^2`
   whose centroid travels `2 pi R` encloses their product. Not an
   approximation.

   *The vacuum toroidal field across the plasma's own width*, `B_0 R_0 / R`
   at the inboard and outboard edges, and their ratio. A tokamak plasma
   does not sit in one field, and the record says by how much.

   *The normalised plasma current* `I_p / (a B_t)`, the quantity Peng and
   Strickler print a ceiling for.

3. **And the compositions a reader would otherwise do by hand**: the
   density the declared Greenwald fraction asks for, and the safety factor
   against its declared floor, each with the margin stated. The margin is
   **reported and not enforced**: a floor is a declaration, not a law, and
   a record that refused a configuration for missing its own declared
   floor would be making an admissibility decision that is not this
   repository's to make.

4. **The triangularity does not enter the volume, and that is written
   down.** A triangular deformation moves area about the centroid without
   changing it to first order, so the volume reported is the elliptic one.
   The docstring says so, the record's non-claims say so, and a test
   asserts that two geometries differing only in triangularity give the
   same volume — because a silent limitation is the kind a reader
   discovers too late.

5. **No kernel-library pin.** Every relation here is multiplication and
   division; no transcendental enters, so unlike the three
   magneto-inertial families this repository needs no pin for its physics.

## Anchoring: a pair of regimes, not a machine

Neither filed source prints one machine. Greenwald (2002) prints the
density limit itself — equation 1.3, `nG = I_P / (pi a^2)`, "where nG is
the line-averaged density in units of 10^20 m^-3" — which verifies the
relation this repository already implemented, in both form and units.

Peng and Strickler (ORNL/FEDC-85/6, 1985) print **relations between
regimes**: a spherical torus has aspect ratio below two; at `A ~ 1.5` an
elongation of `kappa = 2` arises naturally from a dipole vertical field
alone; for `A > 2.5` the natural elongation is below `1.4`; and the
normalised current reaches about `7 MA/(m T)`.

So the anchor is two fixtures, one per owned configuration, each sitting
at a printed **pairing**. A pairing anchors better than a lone number
because it can be got wrong in two directions: a fixture that satisfied
only one half would not be where the source says such a device sits.

The spherical fixture's radii are 1.5 and 1.0 rather than 1.2 and 0.8 for
a measured reason: `1.2 / 0.8` is `1.4999999999999998` in binary and
`1.5 / 1.0` is exact, so the anchor test asserts an equality.

Every absolute dimension is declared and said to be declared. Neither
source prints a major radius, a field or a current.

## Consequences

The repository has a level-0 record that adds what was missing and repeats
nothing. Its two anchors sit at printed regime pairings, and the one
limitation of its volume relation is tested rather than merely mentioned.

Nothing here predicts a disruption, a stability boundary or a
performance, and no value describes a real machine.
