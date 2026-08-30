<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Tokamak Core — Architecture summary
-->

# Architecture summary

`SCPN-TOKAMAK-CORE` is the device-family owner for conventional and spherical
tokamak configurations inside the SCPN Reactor Systems Research Group. The
repository holds one implemented capability — the device configuration model
at `computational_prototype` (`src/scpn_tokamak_core/`, ADR 0002) — alongside
the device boundary, its ecosystem contracts, and the validation tooling that
enforces both.

The authoritative architecture record is
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). The ownership decision and its
consequences are fixed in
[`docs/adr/0001-repository-boundary.md`](docs/adr/0001-repository-boundary.md).

Boundary in one paragraph: this repository owns tokamak plant and experiment
truth — configuration policy, shot lifecycle, diagnostic and clock semantics,
actuator-response boundaries, safety-envelope declarations, and the
device-owned CONTROL adapter specification. Solver mathematics stays in
`SCPN-FUSION-CORE`; typed semantics stay in `SCPN-PHASE-ORCHESTRATOR`
(review-only); admitted control actions are formed only by `SCPN-CONTROL`;
independent machine protection keeps the final veto; portfolio presentation
belongs to `SCPN-STUDIO`, towards which this project is `not_federated`.
