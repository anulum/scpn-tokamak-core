<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Tokamak Core — ADR 0001: repository boundary
-->

# ADR 0001 — Repository boundary and ownership

**Status:** accepted (2026-08-30)  
**Deciders:** project owner; SCPN Reactor Systems Research Group standard

## Context

The SCPN reactor portfolio assigns every built-in configuration of the SCPN
Phase Orchestrator reactor registry (version `1.0.0`, 32 configurations) to
exactly one device-family repository. Tokamak workflows previously had no
dedicated device home; solver mathematics lives in the shared solver
laboratory. A boundary decision was needed on (a) which configurations this
repository owns, (b) what it explicitly does not own, and (c) how it relates
to the solver, semantic, control, presentation, and machine-protection
layers.

## Decision

1. `SCPN-TOKAMAK-CORE` owns exactly two registry configurations:
   `conventional_tokamak` and `spherical_tokamak`. They share all five
   boundary surfaces (axisymmetric toroidal confinement physics, inductive
   drive with auxiliary systems, pulsed/long-pulse shot lifecycle, common
   diagnostic and clock model, one solver/evidence/control contract), so one
   repository serves both; aspect ratio is a configuration parameter, not a
   repository boundary.
2. The repository owns device-level truth only: configuration policy, shot
   lifecycle semantics, diagnostic/reference-frame/clock declarations,
   actuator-response model boundaries, the safety-envelope declaration, and
   the device-owned CONTROL adapter specification.
3. Solver mathematics and validation evidence remain in `SCPN-FUSION-CORE`
   until an exact surface passes the family migration gate (freeze, parity
   proof, versioned adapter switch, governed deprecation). No solver code is
   copied here — not for scaffolding, not "temporarily".
4. Typed semantics remain in `SCPN-PHASE-ORCHESTRATOR` (review-only towards
   control). Admission and `ControlAction` formation remain exclusively in
   `SCPN-CONTROL`. Machine protection remains independent with the final
   veto. Presentation, entitlement, and execution gating remain in
   `SCPN-STUDIO`; this project is `not_federated` until a real capability
   passes federation gates.
5. The repository starts, and remains until evidenced otherwise, at
   `architecture_only` with empty capability and claim inventories.

## Alternatives considered

- **One combined toroidal-confinement repository** (tokamaks +
  stellarators): rejected — three-dimensional equilibria, coil topology,
  and lifecycle differ on surfaces 1, 2, and 4; merging recreates the
  undifferentiated-container problem the portfolio standard exists to
  prevent.
- **Separate repositories for conventional and spherical tokamaks**:
  rejected — all five surfaces are substantially shared; the split would
  duplicate every contract for a parameter difference.
- **Absorbing tokamak solver code from the solver laboratory at scaffold
  time**: rejected — it forks mathematical ownership before parity evidence
  exists and violates the migration gate.

## Consequences

- Downstream consumers (SPO, CONTROL, STUDIO) get one stable identity per
  tokamak configuration and a manifest to bind against.
- Tokamak-specific plant workflows in the solver laboratory have a declared
  future home, reachable only through the migration gate.
- The repository must keep its inventories truthful: the validator fails on
  any capability or claim entry while maturity is `architecture_only`.
- Boundary changes require a portfolio-level map change first (see
  `GOVERNANCE.md`); a future ADR records any such change here.
