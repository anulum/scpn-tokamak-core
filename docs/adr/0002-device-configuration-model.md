<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Tokamak Core — ADR 0002: device configuration model
-->

# ADR 0002 — Device configuration model and evidence-maturity semantics

**Status:** accepted (2026-08-31)

**Deciders:** project owner; SCPN Reactor Systems Research Group standard

## Context

The repository was established architecture-only (ADR 0001): governed
boundaries and contracts with zero implemented capabilities. The first
capability lane of the roadmap is the device configuration model — the
typed, validated parameter surface on which diagnostics semantics, safety
envelopes, and the CONTROL adapter later stand. Landing it requires two
decisions: (a) the model's claim boundary, and (b) what the manifest's
repository-level `evidence_maturity` field means once per-capability
states exist.

## Decision

1. The package `scpn_tokamak_core` implements the device configuration
   model as frozen, strictly typed value objects: toroidal geometry,
   coil-system counts, operational limits, and a configuration container
   bound to exactly the two SPO registry identifiers this repository owns
   (`conventional_tokamak`, `spherical_tokamak`).
2. Claim boundary — the capability claims ONLY: internal-consistency
   validation of parameter sets, physically standard derived estimates
   with documented applicability bounds (aspect ratio, Greenwald density
   limit, cylindrical safety-factor estimate), canonical serialisation
   with SHA-256 digest, and binding to the pinned SPO reactor registry
   version and digest. It claims nothing about any real machine; the
   parameter sets used to exercise the model are synthetic test fixtures.
3. Hard validation failures are reserved for mathematically or
   semantically invalid inputs (non-finite values, non-positive extents,
   `a >= R0`, elongation or triangularity outside the documented model
   bounds, a spherical/conventional identifier that contradicts the
   aspect ratio). Physics consistency beyond that is reported by
   `consistency_report()` as typed findings, never silently clamped:
   rejecting NaN explicitly rather than clamping is a repository rule.
4. Repository-level `evidence_maturity` semantics from this ADR onward:
   the manifest's top-level value equals the HIGHEST state claimed by any
   entry in `capabilities`; the per-capability states are the
   authoritative claim surface. The repository-level value is a ceiling
   for what may be advertised, never a substitute for the per-capability
   claim (whole-repository and claim-level truths stay distinct).
5. The `capabilities` entry for this lane is
   `device_configuration_model` at `computational_prototype`, with its
   evidence pointer anchored in `VALIDATION.md`. Registry binding stays a
   data pin (version + digest equality with the manifest); the package
   never imports SCPN Phase Orchestrator code, keeping the repository
   hermetic.
6. Everything else is unchanged: `review_only`/non-actionable SPO
   profile, no adapter implementation, empty solver seams,
   `not_federated` Studio state, independent machine-protection veto,
   and all non-claims.

## Consequences

- The Studio descriptor's `capabilities` array carries its first item
  (schema 1.1.0 already defines the shape; descriptor DATA changes, the
  schema does not).
- The reactor-domain validator gains a populated-capabilities branch:
  identifier uniqueness and shape, implemented-state enumeration,
  evidence pointers that resolve to committed files, and the
  repository-level ceiling rule of this ADR.
- Later lanes (diagnostic semantics, safety envelope) build on these
  types; maturity advances per capability only with the evidence the
  family standard requires.
