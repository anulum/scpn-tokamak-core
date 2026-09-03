# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — report diagnostic tests

"""The review report and the ranges it flags.

The report advises; it does not refuse. Each flag names the quantity, the
range it fell outside, and the channel it came from.

All plans in this module are synthetic fixtures; none describes any real
diagnostic, measurement, or facility.
"""

from __future__ import annotations

from observability_fixtures import (
    CLOCK_RELATIONS,
    CLOCK_TOPOLOGY,
    DERIVED_SIGNALS,
    EVENT_BINDINGS,
    EVENT_SIGNALS,
    NONCYCLIC_BINDINGS,
    NONCYCLIC_SIGNALS,
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
    plan_with,
    synthetic_plan,
)
from scpn_tokamak_core.observability import (
    CATALOGUE_BINDING,
    ClockKind,
    ClockModel,
    DeferredCandidate,
    DiagnosticChannelPlan,
    DiagnosticPlan,
    SemanticCarrier,
)


def test_report_flags_cyclic_array_without_amplitude_signal() -> None:
    """A multi-element cyclic array without an amplitude signal draws the advisory."""
    channel = mirnov_channel(signals=(DERIVED_SIGNALS[1],))
    plan = plan_with(
        channels=tuple(
            channel if entry.identifier == channel.identifier else entry
            for entry in synthetic_plan().channels
        )
    )
    findings = plan.consistency_report()
    assert len(findings) == 1
    assert "amplitude" in findings[0].message


def test_report_flags_mhd_band_outside_typical_range() -> None:
    """An MHD band outside 1-100 kHz draws the cited advisory."""
    channel = mirnov_channel(sample_rate_hz=2.0e7, max_signal_frequency_hz=5.0e6)
    plan = DiagnosticPlan(
        identifier="tokamak_reference_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock_shot(), clock_simulation()),
        frames=REFERENCE_FRAMES,
        clock_relations=CLOCK_RELATIONS,
        frame_transformations=REFERENCE_TRANSFORMATIONS,
        clock_topology=CLOCK_TOPOLOGY,
        channels=(
            channel_elm_train(),
            channel_equilibrium(),
            channel,
            channel_oscillator(),
        ),
        deferrals=(),
    )
    findings = plan.consistency_report()
    assert len(findings) == 1
    assert "Hutchinson" in findings[0].message


def test_report_flags_coarse_transient_timing() -> None:
    """A transient timing bound above 100 us draws the cited advisory."""
    channel = DiagnosticChannelPlan(
        identifier="ch_elm_train",
        candidate_id="closed.recurrent_transient",
        carrier=SemanticCarrier.EVENT_CYCLE,
        clock_identifier="clk_shot",
        sample_rate_hz=1.0e6,
        max_signal_frequency_hz=0.0,
        timing_uncertainty_s=1.0e-3,
        acquisition_start_s=0.0,
        acquisition_duration_s=10.0,
        element_count=1,
        evidence_bindings=dict(EVENT_BINDINGS),
        signals=EVENT_SIGNALS,
        synthetic=True,
    )
    plan = DiagnosticPlan(
        identifier="tokamak_reference_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock_shot(), clock_simulation()),
        frames=REFERENCE_FRAMES,
        clock_relations=CLOCK_RELATIONS,
        frame_transformations=REFERENCE_TRANSFORMATIONS,
        clock_topology=CLOCK_TOPOLOGY,
        channels=(
            channel,
            channel_equilibrium(),
            channel_mirnov(),
            channel_oscillator(),
        ),
        deferrals=(),
    )
    findings = plan.consistency_report()
    assert len(findings) == 1
    assert "Zohm" in findings[0].message


def test_report_flags_clock_coarser_than_sampling() -> None:
    """A clock that cannot separate samples draws the advisory."""
    clock = ClockModel(
        identifier="clk_shot",
        kind=ClockKind.SHOT_EVENT_EPOCH,
        epoch="shot trigger t0",
        resolution_s=1.0e-2,
        uncertainty_s=1.0e-6,
    )
    channel = DiagnosticChannelPlan(
        identifier="ch_equilibrium_set",
        candidate_id="closed.equilibrium_profiles",
        carrier=SemanticCarrier.BOUNDED_FEATURE,
        clock_identifier="clk_shot",
        sample_rate_hz=1.0e3,
        max_signal_frequency_hz=0.0,
        timing_uncertainty_s=None,
        acquisition_start_s=0.0,
        acquisition_duration_s=10.0,
        element_count=12,
        evidence_bindings=dict(NONCYCLIC_BINDINGS),
        signals=NONCYCLIC_SIGNALS,
        synthetic=True,
    )
    plan = DiagnosticPlan(
        identifier="tokamak_partial_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock, clock_simulation()),
        frames=REFERENCE_FRAMES,
        clock_relations=CLOCK_RELATIONS,
        frame_transformations=REFERENCE_TRANSFORMATIONS,
        clock_topology=CLOCK_TOPOLOGY,
        channels=(channel, channel_mirnov(), channel_oscillator()),
        deferrals=(
            DeferredCandidate(
                candidate_id="closed.recurrent_transient",
                reason="transient train deferred pending event fixtures",
            ),
        ),
    )
    findings = plan.consistency_report()
    assert len(findings) == 1
    assert "cannot distinguish" in findings[0].message


def test_report_flags_window_beyond_device_ceiling() -> None:
    """An acquisition window beyond the device scale draws the advisory."""
    channel = mirnov_channel(acquisition_duration_s=1000.0)
    plan = synthetic_plan()
    plan = DiagnosticPlan(
        identifier=plan.identifier,
        binding=plan.binding,
        clocks=plan.clocks,
        frames=plan.frames,
        clock_relations=plan.clock_relations,
        frame_transformations=REFERENCE_TRANSFORMATIONS,
        clock_topology=CLOCK_TOPOLOGY,
        channels=tuple(
            channel if entry.identifier == channel.identifier else entry
            for entry in plan.channels
        ),
        deferrals=plan.deferrals,
    )
    findings = plan.consistency_report()
    assert len(findings) == 1
    assert "acquisition window" in findings[0].message


def test_report_flags_array_size_outside_common_range() -> None:
    """A two-element array below the common range draws the advisory."""
    channel = mirnov_channel(element_count=2)
    plan = synthetic_plan()
    plan = DiagnosticPlan(
        identifier=plan.identifier,
        binding=plan.binding,
        clocks=plan.clocks,
        frames=plan.frames,
        clock_relations=plan.clock_relations,
        frame_transformations=REFERENCE_TRANSFORMATIONS,
        clock_topology=CLOCK_TOPOLOGY,
        channels=tuple(
            channel if entry.identifier == channel.identifier else entry
            for entry in plan.channels
        ),
        deferrals=plan.deferrals,
    )
    findings = plan.consistency_report()
    assert len(findings) == 1
    assert "array size" in findings[0].message
