<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Tokamak Core — device model contract
-->

# Device model contract

What a consumer of this repository's device models may rely on, written
from the code rather than from a template. Design record:
`docs/adr/0006-device-3d-and-cad-models.md`.

## The two tiers

| Tier | Record | Schema | Built from |
|---|---|---|---|
| G1, tessellated | `DeviceModel3D` | `scpn.tokamak-3d-model.v1` 1.0.0 | the library's `geometry` group |
| G2, B-rep | `DeviceModelCAD` | `scpn.tokamak-cad-model.v1` 1.0.0 | the library's `cad` group |

Both are built from the same validated `DeviceConfiguration` and
`DeviceEnvelope` and describe the same three bodies. Tier G2 is optional:
it needs the `cad` extra, and every other capability of this package works
without a B-rep back-end.

**The package is `scpn_tokamak_core.device`, not `.geometry`.** Every
sibling family uses `geometry`; here that name already belongs to the
plasma shape, because for a tokamak the shape is a configuration
parameter. Renaming a published submodule to free the word is the owner's
decision and not a tier landing's.

## What is modelled: the cylindrical periodic equivalent

A tokamak is a torus. The bodies are the standard reduced model of one —
the torus unrolled into a straight cylinder of periodic length `2 pi R0`,
the same construction the reversed-field-pinch family uses.

**The elongation is carried; the triangularity cannot be.** The plasma
column is built at the *area-equivalent* radius `a sqrt(kappa)`, so its
circular cross-section has the ellipse's area and its volume over the
periodic length is exactly the volume
`scpn_tokamak_core.physics.equilibrium.plasma_volume_m3` computes by
Pappus's theorem. No body of revolution can represent a fore-aft
asymmetry, so the triangularity does not reach the bodies — which is
asserted by building two configurations that differ only in it.

## Units and frame

| Quantity | Value |
|---|---|
| length | metre |
| handedness | right |
| axis | `z` along the axis of the cylindrical periodic equivalent |
| origin | `z = 0` at one end of the periodic length `2 pi R0` |

## The bodies, in this order

| Name | Role | Material token |
|---|---|---|
| `plasma_column` | `plasma` | `plasma` |
| `vacuum_vessel` | `vacuum_boundary` | `vessel_wall` |
| `toroidal_field_winding` | `coil` | `coil_conductor` |

The order is fixed and checked at construction on both tiers. A record
whose bodies are reordered or renamed is refused, not sorted.

## Where each dimension comes from

The configuration owns the plasma: major and minor radii, elongation and
triangularity. The envelope owns the radial build outside it — the vessel
wall thickness, the winding gap and the winding thickness. Neither repeats
the other.

One relation between them is checked before any body is built: the radial
build must stay inside half the periodic length, or the unrolled machine
self-intersects. It is refused naming the field and printing both sides.

## Exports and identity

Both records serialise canonically (sorted keys, minimal separators, a
trailing newline, NaN and infinity refused) and carry a SHA-256 digest of
those bytes. Each binds the digests of the configuration and the envelope
it was built from. Tier G2 additionally carries normalised STEP bytes with
their own digest and the versions of the pinned back-ends.

## Declared limits

- **STEP determinism is claimed inside one pinned back-end environment
  only**, never across back-end versions. The record carries the versions.
- The faceting comparison runs at a linear deflection of `1e-4 m` and an
  angular deflection of `0.02 rad`, against an 8-segment tier-G1
  reference. **Both are set by measurement, and the binding one is the
  angular deflection** — the opposite of the magneto-inertial families.
  This device is metres across, which makes the bound `2 d / r` tight, so
  the linear deflection sets the bound while the angular criterion sets
  the tessellation. Measured: across a tenfold change in the linear
  deflection the deficit did not move at all; halving the angular
  deflection quartered it.
- Consequently **a finer linear deflection is refused**, because it
  tightens the bound tenfold and leaves the faceting untouched. A test
  asserts that refusal.

## Non-claims

- The toroidal curvature is not modelled, so nothing here distinguishes
  the inboard side of a torus from the outboard one. The end caps of the
  cylinders are an artefact of the primitive.
- The poloidal field coils have no place in a straight equivalent and are
  absent. The toroidal-field winding is one tube of declared size; no
  coil, turn count, circuit, ripple or field map is modelled.
- No body is an equilibrium boundary, a CAD solid or an engineering
  model; no material property, load, field, neutronic quantity or
  fabrication tolerance is carried.
- No value describes or validates any real machine.
