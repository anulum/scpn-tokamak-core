# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — channels diagnostic tests

"""Diagnostic channel plans: identity, carrier, sampling and evidence.

Sampling is checked against the declared signal frequency, the clock
binding against the declared clock, and the evidence keys against the
binding they name.

All plans in this module are synthetic fixtures; none describes any real
diagnostic, measurement, or facility.
"""

from __future__ import annotations

from typing import Any

import pytest

from observability_fixtures import (
    CLOCK_RELATIONS,
    CLOCK_TOPOLOGY,
    DERIVED_BINDINGS,
    DERIVED_SIGNALS,
    EVENT_BINDINGS,
    EVENT_SIGNALS,
    NUMERICAL_BINDINGS,
    NUMERICAL_SIGNALS,
    REFERENCE_FRAMES,
    REFERENCE_TRANSFORMATIONS,
    channel_elm_train,
    channel_equilibrium,
    channel_mirnov,
    channel_oscillator,
    clock_facility,
    clock_shot,
    clock_simulation,
    mirnov_channel,
    signal_declaration,
)
from scpn_tokamak_core.errors import DiagnosticPlanError
from scpn_tokamak_core.observability import (
    CATALOGUE_BINDING,
    DiagnosticChannelPlan,
    DiagnosticPlan,
    ObservabilityClass,
    SemanticCarrier,
    SignalDeclaration,
    SignalRole,
)


def _event_channel(**overrides: Any) -> DiagnosticChannelPlan:
    """Build the event-relative channel with keyword overrides applied."""
    values: dict[str, Any] = {
        "identifier": "ch_elm_train",
        "candidate_id": "closed.recurrent_transient",
        "carrier": SemanticCarrier.EVENT_CYCLE,
        "clock_identifier": "clk_shot",
        "sample_rate_hz": 1.0e6,
        "max_signal_frequency_hz": 0.0,
        "timing_uncertainty_s": 1.0e-5,
        "acquisition_start_s": 0.0,
        "acquisition_duration_s": 10.0,
        "element_count": 1,
        "evidence_bindings": dict(EVENT_BINDINGS),
        "signals": EVENT_SIGNALS,
        "synthetic": True,
    }
    values.update(overrides)
    return DiagnosticChannelPlan(**values)


def _oscillator_channel(**overrides: Any) -> DiagnosticChannelPlan:
    """Build the numerical-only channel with keyword overrides applied."""
    values: dict[str, Any] = {
        "identifier": "ch_synthetic_oscillator",
        "candidate_id": "model.synthetic_oscillator_coordinate",
        "carrier": SemanticCarrier.NUMERICAL_PHASE,
        "clock_identifier": "clk_sim",
        "sample_rate_hz": 1.0e4,
        "max_signal_frequency_hz": 0.0,
        "timing_uncertainty_s": None,
        "acquisition_start_s": 0.0,
        "acquisition_duration_s": 1.0,
        "element_count": 1,
        "evidence_bindings": dict(NUMERICAL_BINDINGS),
        "signals": NUMERICAL_SIGNALS,
        "synthetic": True,
    }
    values.update(overrides)
    return DiagnosticChannelPlan(**values)


def test_channel_rejects_empty_signal_inventory() -> None:
    """A channel must declare at least one signal."""
    with pytest.raises(DiagnosticPlanError, match="at least one signal"):
        mirnov_channel(signals=())


def test_channel_rejects_unsorted_or_duplicate_signals() -> None:
    """Signal identifiers must be unique and sorted."""
    with pytest.raises(DiagnosticPlanError, match="unique and sorted"):
        mirnov_channel(signals=tuple(reversed(DERIVED_SIGNALS)))
    with pytest.raises(DiagnosticPlanError, match="unique and sorted"):
        mirnov_channel(signals=(*DERIVED_SIGNALS, DERIVED_SIGNALS[-1]))


@pytest.mark.parametrize("count", [0, 2])
def test_channel_requires_exactly_one_carrier_signal(count: int) -> None:
    """Exactly one carrier signal is required."""
    carriers = tuple(
        signal_declaration(identifier=f"sig_carrier_{index}", role=SignalRole.CARRIER)
        for index in range(count)
    )
    with pytest.raises(DiagnosticPlanError, match="exactly one carrier"):
        mirnov_channel(signals=(*carriers, DERIVED_SIGNALS[0]))


def test_event_channel_requires_exactly_one_timing_marker() -> None:
    """Event-relative channels declare exactly one timing marker."""
    without_marker = tuple(
        signal
        for signal in EVENT_SIGNALS
        if signal.role is not SignalRole.TIMING_MARKER
    )
    with pytest.raises(DiagnosticPlanError, match="exactly one timing_marker"):
        _event_channel(signals=without_marker)
    doubled = tuple(
        sorted(
            (
                *EVENT_SIGNALS,
                signal_declaration(
                    identifier="sig_second_onset",
                    unit="s",
                    role=SignalRole.TIMING_MARKER,
                ),
            ),
            key=lambda signal: signal.identifier,
        )
    )
    with pytest.raises(DiagnosticPlanError, match="exactly one timing_marker"):
        _event_channel(signals=doubled)


def test_event_channel_timing_marker_must_be_in_seconds() -> None:
    """The timing marker is declared in seconds."""
    signals = tuple(
        signal_declaration(
            identifier=signal.identifier,
            quantity=signal.quantity,
            unit="ms",
            role=signal.role,
            description=signal.description,
        )
        if signal.role is SignalRole.TIMING_MARKER
        else signal
        for signal in EVENT_SIGNALS
    )
    with pytest.raises(DiagnosticPlanError, match="seconds"):
        _event_channel(signals=signals)


def test_non_event_channel_rejects_timing_marker() -> None:
    """Only event-relative channels declare a timing marker."""
    marker = signal_declaration(
        identifier="sig_zz_marker", unit="s", role=SignalRole.TIMING_MARKER
    )
    with pytest.raises(DiagnosticPlanError, match="only event-relative"):
        mirnov_channel(signals=(*DERIVED_SIGNALS, marker))


@pytest.mark.parametrize(
    "signals",
    [
        (NUMERICAL_SIGNALS[0], signal_declaration(identifier="sig_zz_extra")),
        (
            signal_declaration(
                identifier="sig_phase",
                quantity="angle",
                unit="rad",
                role=SignalRole.CARRIER,
            ),
        ),
        (
            signal_declaration(
                identifier="sig_phase",
                quantity="phase",
                unit="deg",
                role=SignalRole.CARRIER,
            ),
        ),
    ],
)
def test_numerical_channel_declares_single_phase_carrier(
    signals: tuple[SignalDeclaration, ...],
) -> None:
    """Numerical-only channels declare exactly one phase carrier in radians."""
    with pytest.raises(DiagnosticPlanError, match="numerical-only"):
        _oscillator_channel(signals=signals)


def test_channel_rejects_malformed_identifier() -> None:
    """A malformed channel identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"channel\.identifier"):
        mirnov_channel(identifier="Channel!")


def test_channel_rejects_unknown_candidate() -> None:
    """A candidate outside the embedded subset is rejected."""
    with pytest.raises(DiagnosticPlanError, match="not applicable"):
        mirnov_channel(candidate_id="open.drive_reference")


def test_channel_rejects_inadmissible_carrier() -> None:
    """A carrier outside the class table is rejected."""
    with pytest.raises(DiagnosticPlanError, match="not admissible"):
        mirnov_channel(carrier=SemanticCarrier.EVENT_CYCLE)


def test_channel_rejects_malformed_clock_identifier() -> None:
    """A malformed clock reference is rejected."""
    with pytest.raises(DiagnosticPlanError, match="clock_identifier"):
        mirnov_channel(clock_identifier="Clock!")


@pytest.mark.parametrize("rate", [0.0, -1.0, float("nan")])
def test_channel_rejects_bad_sample_rate(rate: float) -> None:
    """Non-positive or non-finite sampling rates are rejected."""
    with pytest.raises(DiagnosticPlanError, match="sample_rate_hz"):
        mirnov_channel(sample_rate_hz=rate)


@pytest.mark.parametrize("frequency", [-1.0, float("inf")])
def test_channel_rejects_bad_signal_frequency(frequency: float) -> None:
    """Negative or non-finite signal frequencies are rejected."""
    with pytest.raises(DiagnosticPlanError, match="max_signal_frequency_hz"):
        mirnov_channel(max_signal_frequency_hz=frequency)


def test_channel_rejects_cyclic_zero_band() -> None:
    """A cyclic channel must declare a positive signal band."""
    with pytest.raises(DiagnosticPlanError, match="positive signal band"):
        mirnov_channel(max_signal_frequency_hz=0.0)


def test_channel_rejects_nyquist_violation() -> None:
    """Sampling below twice the signal band is rejected."""
    with pytest.raises(DiagnosticPlanError, match="Nyquist"):
        mirnov_channel(sample_rate_hz=5.0e4)


@pytest.mark.parametrize("timing", [None, 0.0, -1.0e-6, float("nan")])
def test_event_channel_requires_timing_uncertainty(timing: float | None) -> None:
    """Event-relative channels must declare a positive timing bound."""
    bindings = dict(EVENT_BINDINGS)
    with pytest.raises(DiagnosticPlanError, match="timing_uncertainty_s"):
        DiagnosticChannelPlan(
            identifier="ch_elm_train",
            candidate_id="closed.recurrent_transient",
            carrier=SemanticCarrier.EVENT_CYCLE,
            clock_identifier="clk_shot",
            sample_rate_hz=1.0e6,
            max_signal_frequency_hz=0.0,
            timing_uncertainty_s=timing,
            acquisition_start_s=0.0,
            acquisition_duration_s=10.0,
            element_count=1,
            evidence_bindings=bindings,
            signals=EVENT_SIGNALS,
            synthetic=True,
        )


def test_non_event_channel_rejects_timing_uncertainty() -> None:
    """Only event-relative channels declare a timing uncertainty."""
    with pytest.raises(DiagnosticPlanError, match="only event-relative"):
        mirnov_channel(timing_uncertainty_s=1.0e-5)


def test_channel_rejects_evidence_key_mismatch() -> None:
    """Missing and extra evidence slots are both rejected."""
    bindings = dict(DERIVED_BINDINGS)
    del bindings["mode_identity"]
    bindings["surprise"] = "x"
    with pytest.raises(DiagnosticPlanError, match=r"missing=.*extra="):
        mirnov_channel(evidence_bindings=bindings)


def test_channel_rejects_empty_evidence_statement() -> None:
    """An empty evidence statement is rejected."""
    bindings = dict(DERIVED_BINDINGS)
    bindings["quality"] = ""
    with pytest.raises(DiagnosticPlanError, match="quality"):
        mirnov_channel(evidence_bindings=bindings)


def test_channel_rejects_clock_binding_mismatch() -> None:
    """The clock evidence slot must reference the bound clock."""
    bindings = dict(DERIVED_BINDINGS)
    bindings["clock_epoch"] = "clk_other"
    with pytest.raises(DiagnosticPlanError, match="must reference the bound clock"):
        mirnov_channel(evidence_bindings=bindings)


def test_channel_rejects_non_synthetic() -> None:
    """No channel in this repository may claim to be real."""
    with pytest.raises(DiagnosticPlanError, match="synthetic"):
        mirnov_channel(synthetic=False)


def test_channel_exposes_observability_class() -> None:
    """The class property resolves through the embedded catalogue."""
    assert channel_mirnov().observability_class is ObservabilityClass.DERIVED_CYCLIC


def test_plan_rejects_unsorted_channels() -> None:
    """Channels must be unique and sorted by identifier."""
    with pytest.raises(DiagnosticPlanError, match=r"plan\.channels"):
        DiagnosticPlan(
            identifier="tokamak_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot(), clock_simulation()),
            frames=REFERENCE_FRAMES,
            clock_relations=CLOCK_RELATIONS,
            frame_transformations=REFERENCE_TRANSFORMATIONS,
            clock_topology=CLOCK_TOPOLOGY,
            channels=(
                channel_equilibrium(),
                channel_elm_train(),
                channel_mirnov(),
                channel_oscillator(),
            ),
            deferrals=(),
        )


@pytest.mark.parametrize("start", [float("nan"), float("inf")])
def test_channel_rejects_bad_acquisition_start(start: float) -> None:
    """A non-finite acquisition start is rejected."""
    with pytest.raises(DiagnosticPlanError, match="acquisition_start_s"):
        mirnov_channel(acquisition_start_s=start)


@pytest.mark.parametrize("duration", [0.0, -1.0, float("nan")])
def test_channel_rejects_bad_acquisition_duration(duration: float) -> None:
    """A non-positive acquisition duration is rejected."""
    with pytest.raises(DiagnosticPlanError, match="acquisition_duration_s"):
        mirnov_channel(acquisition_duration_s=duration)


@pytest.mark.parametrize("count", [0, -3, True])
def test_channel_rejects_bad_element_count(count: object) -> None:
    """A non-integer or sub-unit element count is rejected."""
    with pytest.raises(DiagnosticPlanError, match="element_count"):
        mirnov_channel(element_count=count)
