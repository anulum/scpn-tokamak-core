<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Tokamak Core — Architecture
-->

# Architecture

## Purpose and evidence state

`SCPN-TOKAMAK-CORE` is the device-family owner for tokamak fusion systems in
the SCPN Reactor Systems Research Group portfolio. The repository is
`architecture_only`: every section below describes boundaries and contracts,
not implemented capability. The capability inventory is empty and the claim
inventory is empty; both are generated and drift-checked.

## The five-surface boundary

The reactor family standard defines a repository as one coherent combination
of five surfaces. For this project they are:

1. **Governing confinement physics** — toroidal magnetic confinement in
   axisymmetric equilibria: the conventional tokamak (`conventional_tokamak`,
   axisymmetric torus) and the spherical tokamak (`spherical_tokamak`,
   low-aspect-ratio axisymmetric torus). Aspect ratio changes the equilibrium
   and stability landscape but not the governing axisymmetric confinement
   principle, the driver class, or the shot lifecycle, so both configurations
   share this repository. Three-dimensional stellarator-family equilibria,
   relaxed-current RFP states, self-organised spheromaks, and FRC plasmas
   fail that sharing test and are excluded.
2. **Primary driver and energy delivery** — inductive current drive via the
   central solenoid, with auxiliary heating and current-drive systems
   (neutral beams, radio-frequency systems) as configuration facets of the
   device family.
3. **Plant and shot lifecycle** — pulsed or long-pulse discharge lifecycle:
   breakdown, current ramp-up, flat-top, ramp-down, and termination,
   including disruption as a lifecycle hazard whose device-level semantics
   belong here (its solver physics stays with the solver owner).
4. **Diagnostic, reference-frame, and clock model** — declaration of
   diagnostic channels, coordinate conventions (flux coordinates, laboratory
   frame), and clock identities used by every downstream consumer.
5. **Solver, evidence, and control-contract boundary** — versioned seams
   towards `SCPN-FUSION-CORE`, review-only semantics towards
   `SCPN-PHASE-ORCHESTRATOR`, and the device-owned CONTROL adapter
   specification towards `SCPN-CONTROL`.

## Position in the SCPN ecosystem

```text
SCPN-TOKAMAK-CORE (device truth: configuration policy, lifecycle,
                   diagnostics/clocks, safety envelope, adapter spec)
   │  optional versioned solver seams (none active)
   ├──────────────► SCPN-FUSION-CORE      (solver mathematics, evidence)
   │  typed review-only semantics
   ├──────────────► SCPN-PHASE-ORCHESTRATOR (semantics, comparability)
   │  device-owned adapter (specification only; no implementation)
   ├──────────────► SCPN-CONTROL          (admission; sole ControlAction author)
   │  derived portfolio descriptor (not_federated)
   └──────────────► SCPN-STUDIO           (catalogue, evidence UI, gating)

SCPN-CONTROL ──admitted ControlAction──► independent machine protection
                                          (final veto) ─► plant actuators
```

Reading the diagram: information flows from this repository outward as
declarations and contracts. Nothing flows from this repository to an
actuator. The only software authority that forms an admitted `ControlAction`
is `SCPN-CONTROL`, and the independent machine-protection layer retains the
final veto on every plant path.

## Repository layout

| Path | Role |
|---|---|
| `reactor-domain.json` | portable source of project identity and contracts |
| `studio/portfolio-descriptor.json` | derived Studio descriptor, `not_federated` |
| `capability-inventory.json` | generated, truthfully empty inventory |
| `docs/CONTROL_ADAPTER_SPECIFICATION.md` | device-owned adapter contract |
| `docs/THREAT_MODEL.md` | assets, trust boundaries, misuse paths |
| `docs/adr/0001-repository-boundary.md` | boundary decision record |
| `tools/` | validators, derivation tools, preflight orchestrator |
| `tests/` | statement- and branch-complete tests for `tools/` |
| `.github/workflows/` | read-only CI definitions (no publication) |

## Contract surfaces and versioning

- `reactor-domain.json` follows schema `scpn.reactor-domain.v1`. Schema
  changes are versioned; consumers reject unknown schemas.
- The Studio descriptor is derived deterministically from the manifest and
  embeds the manifest's SHA-256; manual edits are detected as drift.
- The CONTROL adapter contract is specification-only at version
  `0.1.0-spec`. An implementation may appear only with replay fixtures and
  the evidence the reactor family standard requires, and is versioned
  independently of the manifest schema.
- SPO binding is fixed to reactor registry `1.0.0`, digest
  `786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090`. A
  registry upgrade is a reviewed contract change, never a silent re-pin.

## What would change this architecture

Three future events, each gated outside this repository, would extend (not
silently alter) this architecture: acceptance of a FUSION solver seam through
the family migration gate; ratification of an SPO `ControlIntent`-class
contract; and Studio federation after a real capability passes producer and
consumer gates. Each arrives as a versioned, evidence-bound contract change
recorded in a new ADR.
