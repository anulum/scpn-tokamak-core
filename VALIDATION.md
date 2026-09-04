<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Tokamak Core — VALIDATION
-->

# Validation

Every gate currently active in this repository, with its exact scope,
followed by the evidence record of each implemented capability.

## Local gates

| Gate | Command | Scope |
|---|---|---|
| Lint | `ruff check .` | all Python under `src/`, `tools/`, and `tests/` |
| Format | `ruff format --check .` | same scope |
| Typing | `mypy --strict src tools tests` | zero errors, strict mode |
| Tests + coverage | `pytest -q --cov=src --cov=tools --cov-branch --cov-fail-under=100` | 100 % statement and branch coverage of `src/` and `tools/` |
| Domain manifest | `python3 tools/validate_reactor_domain.py reactor-domain.json` | schema, registry version/digest, exact configuration set, capability inventory shape and ceiling rule, safety boundary |
| Studio descriptor | `python3 tools/derive_studio_descriptor.py --check` | committed descriptor byte-identical to a fresh derivation |
| Capability inventory | `python3 tools/generate_capability_inventory.py --check` | committed inventory byte-identical to a fresh generation |
| Licensing | `reuse lint` | REUSE 3.x compliance of the full tree |
| Workflow lint | `actionlint` | all files under `.github/workflows/` |
| Workflow modularity | `python3 tools/audit_workflows.py` | distributed workflow inventory: single ownership per job, coordinator/gate contract, action pinning, size ceilings |
| Documentation | `python3 tools/preflight.py --only docs` | UTF-8 readability and relative-link integrity of every Markdown file |
| Orchestrated | `python3 tools/preflight.py` | fail-closed run of all gates above |

## Workflow gates

Definitions are present in-repository; they run on the hosted platform
only once a remote exists under separate owner authority.

The hosted surface is modular: `ci.yml` is a coordinator that carries
only trigger policy, two reusable-workflow calls, and one stable
fail-closed `gate` job aggregating every category (failure,
cancellation, and unexpected skips all fail the gate). Every job is
declared and owned exactly once in the versioned inventory
`.github/workflow-inventory.json`, which the workflow-modularity guard
verifies locally and in hosted CI.

| Workflow | Purpose |
|---|---|
| `ci.yml` | coordinator and stable required gate |
| `reusable-static-policy.yml` | lint, format, typing, domain policy, workflow guard |
| `reusable-tests.yml` | tests with complete statement and branch coverage |
| `pre-commit.yml` | exact pre-commit parity |
| `codeql.yml` | Python code scanning |
| `security-audit.yml` | secrets, dependency, licence, and workflow policy |
| `docs.yml` | strict documentation and link validation, no deployment |
| `sbom.yml` | reproducible dependency inventory, no release |
| `scorecard.yml` | read-only supply-chain analysis |

## Shared ecosystem gate

From the monorepo root:

```bash
python3 agentic-shared/scripts/repository_tier0_scaffold_audit.py \
  03_CODE/SCPN-TOKAMAK-CORE --json
```

proves the Tier-0 local-scaffold machine profile (required and forbidden
paths, Git/remote boundary, workflow pins and permissions, badge non-claims,
JSON integrity, defensive ignore rules).

## Device configuration model

Evidence record of the `device_configuration_model` capability
(`computational_prototype`; design record: `docs/adr/0002-device-configuration-model.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate:

- Validated frozen parameter objects (`ToroidalGeometry`, `CoilSystem`,
  `OperationalLimits`, `DeviceConfiguration`) rejecting non-finite values,
  bound violations, torus inversions, and identifier/aspect-ratio
  contradictions — every rejection branch is tested.
- Two documented textbook estimates with their applicability bounds
  stated in the code: the Greenwald density limit
  `n_G = I_p / (pi a^2)` (Greenwald, PPCF 44 (2002) R27) and the
  elongation-corrected cylindrical safety-factor estimate
  `q_cyl = 5 a^2 B_t (1 + kappa^2) / (2 R0 I_p)` (ITER Physics Basis,
  Nucl. Fusion 39 (1999) 2137, ch. 1); consistency findings are reported,
  never clamped.
- Canonical serialisation (sorted keys, NaN/infinity rejected on both
  emit and parse), SHA-256 digest identity, and a strict round-trip
  parser that refuses unknown fields.
- A data-only pin equality check binding the model to the SPO reactor
  registry version and digest declared in `reactor-domain.json`.

Bounded claims — what is NOT claimed:

- No parameter set describes, approximates, or validates any real
  machine; every exercised parameter set is a synthetic test fixture.
- The estimates are rough consistency instruments, not equilibrium,
  transport, or stability results; no benchmark, dataset, solver,
  controller, or experimental correlation exists in this repository.

## Diagnostic and clock semantics

Evidence record of the `diagnostic_clock_semantics` capability
(`computational_prototype`; design record: `docs/adr/0003-diagnostic-clock-semantics.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate:

- Validated frozen declaration objects (`ClockModel`,
  `DiagnosticChannelPlan`, `DeferredCandidate`, `DiagnosticPlan`)
  rejecting catalogue misalignment: inapplicable candidates,
  inadmissible carriers, evidence-vocabulary mismatches, incompatible
  clock kinds, Nyquist violations, unresolvable event-timing bounds,
  and incomplete candidate coverage — every rejection branch is tested.
- A data-only pin (`ObservabilityBinding`) to the SPO
  observability-profile catalogue release `1.0.0`
  (`d70c0de696534e5a77066ef8420cf7ca17bc4d7321984b0ac83523dbc1dce609`),
  bound in turn to reactor registry `1.0.0`; a plan pinned to any other
  release is rejected.
- Documented advisory band checks with their sources stated in the
  code: the tokamak tearing/kink band 1–100 kHz (Hutchinson,
  Principles of Plasma Diagnostics, 2nd ed., 2002, ch. 10) and the
  10–100 µs ELM/sawtooth rise scale (Zohm, PPCF 38 (1996) 105);
  findings are reported, never clamped.
- Canonical serialisation (sorted keys, NaN/infinity rejected on both
  emit and parse), SHA-256 digest identity, and a strict round-trip
  parser that refuses unknown fields.

Bounded claims — what is NOT claimed:

- No channel describes a real diagnostic, measurement, or facility;
  every plan is a synthetic declaration of HOW evidence slots would be
  bound, marked `synthetic=True` by hard invariant.
- No SPO semantic-profile ingress is declared; the profile registry
  `ingress_state` for these configurations remains `not_declared`, and
  no adapter, producer, or handoff exists in this repository.

### Portable plan envelope

The `diagnostic_clock_semantics` capability additionally exercises a
producer-owned portable envelope
(`src/scpn_tokamak_core/plan_envelope.py`,
`scpn.reactor-diagnostic-plan-envelope.v1` version `1.0.0`): one
canonically serialised object carrying the exact project identity and
owned configurations, the capability and its maturity, the
synthetic/review-only/non-actuating statements, both SPO registry pins,
the SHA-256 digest of the inner canonical plan, the producer revision,
and fixed no-observation/no-control non-claims. The committed immutable
fixture (`tests/data/plan_envelope_fixture.json`, byte hash pinned in
the tests) is verified together with positive, tamper, wrong-project,
wrong-configuration, registry-drift, duplicate-member, and non-finite
rejection paths, all under the 100 % coverage gate. The envelope claims
nothing beyond the enveloped synthetic declaration.

### Typed frames, clock relations, and acquisition geometry

The deepened model adds typed reference frames (per-repository allowed
`FrameKind` subset; every noncyclic `coordinate_frame` binding must
reference a declared frame), clock synchronisation relations
(synthetic offset/uncertainty BOUNDS between declared non-simulation
clocks with an explicit method statement — no correlation evidence is
claimed and no clock is mapped to physical wall time), and per-channel
acquisition windows and element counts with device-cited advisory
scales. Both decoders are hardened per the SPO intake architecture:
recursive exact-key refusal in every nested entry, duplicate-member
refusal, and byte-canonical refusal (a document that is not exactly
canonical bytes is rejected). Envelope `1.1.0` added `manifest_sha256` —
the SHA-256 of the committed canonical `reactor-domain.json` — verified
in tests against the committed file; the envelope is now `1.2.0` (below).
All declarations remain synthetic; nothing here observes or controls
anything.

### Signal inventories, frame transformations, and clock topology

The depth slice (envelope `1.2.0`; a `1.1.0` document is refused by the
`1.2.0` codec and vice versa — no defaults, no cross-version coercion)
adds three typed declaration surfaces, every branch under the 100 %
statement-and-branch gate:

- A per-channel **signal inventory** (`SignalDeclaration`: identifier,
  quantity, unit, role, description). Hard rules: non-empty, unique and
  sorted; exactly one `carrier`; a `timing_marker` in `"s"` exactly for
  event-relative channels and forbidden otherwise; numerical-only
  channels declare a single `phase`/`rad` carrier. Quantity and unit are
  declared tokens — no SI or UCUM validation is performed or claimed —
  and no declaration creates or overrides a candidate, carrier,
  observation, or phase: the candidate profile stays authoritative. An
  advisory flags a multi-element cyclic array without an amplitude
  signal.
- **Frame transformations** (`FrameTransformation`) between declared
  frames: kind admissibility fixed by frame-kind pair (`flux_mapping`
  for machine↔flux, flux↔Boozer, field-line↔machine; `projection` for
  blanket↔machine; `rigid` for chamber↔beamline), `equilibrium_dependent`
  exactly for flux mappings, at most one transformation per frame pair,
  sorted by source then target, and — with two or more frames — a
  connected transformation graph. Methods are declarations;
  `evidence_claimed` is always `False`.
- A **clock topology** (`ClockDomain`, `ClockTopology`): every physical
  clock in exactly one domain, the simulation clock in none; a domain
  holding a facility clock is rooted there, otherwise at its shot-event
  epoch; every non-root member declares a relation to its root; every
  non-reference root declares a relation to the reference root (star);
  relations must not form a cycle. The reference plan declares one
  domain (`clk_facility` root, `clk_shot` member); multi-domain rules
  are exercised by test-constructed plans. Scopes are declarations;
  `mapping_state` stays `unmapped`.

## Level-0 device physics

Evidence record of the `level0_device_physics` capability
(`computational_prototype`; design record: `docs/adr/0005-level0-device-physics.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate:

- **Three closed forms nothing in the repository owned yet.** The plasma
  volume by Pappus's theorem, exact for the elliptic cross-section; the
  vacuum toroidal field at the inboard and outboard edges and their ratio,
  with the ordering inboard > axis > outboard asserted; and the normalised
  plasma current `I_p / (a B_t)`.
- **Composition, not restatement.** The Greenwald limit and the
  cylindrical safety factor stay on `OperationalLimits`; a test asserts
  the record's values are exactly what those methods return, so there is
  one source of truth per number and no room for two implementations to
  drift apart.
- **A limitation tested rather than mentioned.** The triangularity the
  configuration carries does not enter the volume; a test asserts two
  geometries differing only in triangularity give the same volume, and the
  record's non-claims say that is a limitation.
- **The safety margin is reported and not enforced.** A floor is a
  declaration; refusing a configuration for missing its own floor would be
  an admissibility decision this repository does not own. Both anchor
  fixtures nonetheless meet their own floors, because a fixture that
  declared a floor its own point missed would be incoherent, and a test
  asserts it.
- The Pappus check is asserted to one part in `1e-15` and **within one
  unit in the last place**, not as an equality, because the implementation
  and the theorem's statement group the six factors in different orders
  and floating-point multiplication is not associative. That was measured:
  the two differ by exactly one ulp.
- Every refusal branch: a field, radius or current that is zero, negative,
  infinite or not-a-number, each naming its field.
- Canonical serialisation, digest identity, digest stability, and two
  configurations giving two digests.

Anchoring — a pair of regimes rather than a machine:

- **Greenwald 2002 verifies the relation already implemented**: its
  equation 1.3 prints `nG = I_P / (pi a^2)` in units of `10^20 m^-3`,
  which is the form and the units of
  `OperationalLimits.greenwald_density_limit_1e20_m3`.
- **Peng & Strickler 1985 prints regime pairings**, and the two fixtures
  sit at them: the spherical one at an aspect ratio of exactly `1.5` with
  the elongation `2` the source pairs with it, the conventional one above
  `2.5` with an elongation below the `1.4` the source calls natural there.
  Both stay under the printed normalised-current ceiling of about
  `7 MA/(m T)`.
- The spherical fixture's radii are `1.5` and `1.0` rather than `1.2` and
  `0.8`, because `1.2 / 0.8` is `1.4999999999999998` in binary and the
  anchor asserts an equality.
- **Declared, and said to be declared**: every absolute dimension. Neither
  source prints a major radius, a field or a current, only the relations
  among them.

Bounded claims — what is NOT claimed:

- No equilibrium, stability, transport or current-drive equation is
  solved.
- The toroidal field is the **vacuum** field; the plasma's own
  paramagnetism and the discreteness of the coils are not modelled.
- The density limit and the cylindrical safety factor are empirical
  consistency instruments with documented applicability. They are **not**
  predictions of disruption or stability.
- The volume is exact for the elliptic cross-section only; the
  triangularity does not enter it.
- No yield, gain, confinement or breakeven statement is made, and no value
  describes or validates a real machine.

## Device 3D model

Evidence record of the `device_3d_model` capability
(`computational_prototype`; design record:
`docs/adr/0006-device-3d-and-cad-models.md`).
Consumer contract, written from this repository's own code:
`docs/DEVICE_3D_MODEL_CONTRACT.md`.


What is exercised, all under the 100 % statement-and-branch coverage gate:

- Three bodies of the cylindrical periodic equivalent in a fixed order —
  plasma column, vacuum vessel, toroidal-field winding — each a cylinder
  or an annular tube about `z` from the shared kernel library, over the
  periodic length `2 pi R0`.
- **The cross-capability identity.** The built column's volume divided by
  the volume the physics record computes by Pappus's theorem is the
  inscribed-polygon ratio `(n / 2 pi) sin(2 pi / n)` and nothing else, at
  8, 64 and 256 segments and in both anchored regimes. The column is
  built at the area-equivalent radius `a sqrt(kappa)` precisely so that
  this holds. Asserted within a relative tolerance rather than as an
  equality: measured, the two sides part by 3 units in the last place at
  8 segments and 133 at 256, which is 3e-14 relative.
- The elongation reaching the bodies through that radius, and the
  triangularity provably not reaching them: two configurations differing
  only in triangularity build bodies of identical volume, while their
  record digests still differ.
- The bodies nesting without overlap, and every vertex sitting at one of
  the two ends of the periodic length.
- Fail-closed refusal of an invalid segment count and of a radial build
  that reaches half the periodic length, where the unrolled machine would
  self-intersect. Each refusal names its field and prints both sides.
- The body set and its order validated on the container as well as in the
  builder.
- Canonical serialisation with a SHA-256 digest that moves with the
  envelope and with the segment count.

## Device CAD model

Evidence record of the `device_cad_model` capability
(`computational_prototype`; design record:
`docs/adr/0006-device-3d-and-cad-models.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate:

- The same three bodies as exact B-rep solids through the shared library's
  `cad` group, each checked fail-closed by the library's evidence kernel
  against its analytic closed forms and against its tier-G1 twin, and
  exported as normalised STEP bytes with a digest.
- **Which deflection binds, measured rather than copied.** On a device
  metres across it is the angular criterion that sets the tessellation,
  not the linear one. Three measurements say so: across a tenfold change
  in the linear deflection the relative deficit did not move at all;
  halving the angular deflection quartered it; and the deficit is the
  same for all three bodies and both regimes although their radii differ
  by tens of per cent and a factor of nearly two.
- The consequence asserted directly: a tenfold finer linear deflection is
  **refused**, because the declared bound `2 d / r` tightens with it while
  the faceting does not. A tier that had copied a sibling family's
  deflection would have found this in CI or not at all.
- Every body inside its declared bound with margin, the narrowest still
  nearly five times.
- Fail-closed refusal of a manifest of the wrong schema or body count and
  of bodies out of order, on the container itself.
- STEP bytes present, their digest matching them, and the two regimes
  producing different bytes.
- Canonical serialisation with a SHA-256 digest, and both tiers bound to
  the same configuration and envelope digests.

Determinism of the STEP bytes is claimed within one pinned back-end
environment only, never across back-end versions. No body is an
engineering model, no fabrication tolerance is carried, and no value
describes any real machine.
