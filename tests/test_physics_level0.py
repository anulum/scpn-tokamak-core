# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — level-0 record tests

"""The composed operating point, and the two printed regimes it anchors on."""

from __future__ import annotations

import hashlib
import json

from physics_fixtures import (
    ANCHOR_CONVENTIONAL_ASPECT_RATIO_FLOOR,
    ANCHOR_CONVENTIONAL_ELONGATION_CEILING,
    ANCHOR_SPHERICAL_ASPECT_RATIO,
    ANCHOR_SPHERICAL_ELONGATION,
    conventional_configuration,
    spherical_configuration,
)

from scpn_tokamak_core.physics.equilibrium import (
    normalised_current_ma_per_mt,
    plasma_volume_m3,
    toroidal_field_at_radius_t,
)
from scpn_tokamak_core.physics.level0 import (
    LEVEL0_NON_CLAIMS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    level0_physics,
)


def test_the_record_is_schema_tagged_and_states_its_non_claims() -> None:
    """The record names its schema and carries the non-claims verbatim."""
    record = level0_physics(conventional_configuration()).to_record()
    assert record["schema"] == LEVEL0_SCHEMA
    assert record["schema_version"] == LEVEL0_SCHEMA_VERSION
    assert record["non_claims"] == list(LEVEL0_NON_CLAIMS)
    assert list(record) == [
        "schema",
        "schema_version",
        "configuration_digest_sha256",
        "operating_point",
        "non_claims",
    ]


def test_the_non_claims_disown_the_limits_and_the_triangularity() -> None:
    """Two things this record could be over-read as saying."""
    joined = " ".join(LEVEL0_NON_CLAIMS)
    assert "not predictions" in joined
    assert "triangularity" in joined
    assert "vacuum field" in joined


def test_the_record_binds_the_configuration_it_was_built_from() -> None:
    """The record carries the digest of its own configuration."""
    configuration = conventional_configuration()
    assert level0_physics(configuration).configuration_digest_sha256 == (
        configuration.digest_sha256()
    )


def test_the_record_calls_the_repository_relations_rather_than_restating() -> None:
    """The limits stay on the limits object; this record composes them.

    The point of the test is that there is one source of truth per number:
    the values in the record are the ones the configuration's own methods
    return, not a second implementation that could drift from them.
    """
    configuration = conventional_configuration()
    point = level0_physics(configuration).operating_point
    limits, geometry = configuration.limits, configuration.geometry
    assert point.greenwald_density_limit_1e20_m3 == (
        limits.greenwald_density_limit_1e20_m3(geometry)
    )
    assert point.cylindrical_safety_factor == limits.cylindrical_safety_factor(geometry)
    assert point.plasma_volume_m3 == plasma_volume_m3(geometry)
    assert point.normalised_current_ma_per_mt == normalised_current_ma_per_mt(
        limits.plasma_current_ma, geometry.minor_radius_m, limits.toroidal_field_t
    )


def test_the_field_is_reported_across_the_plasma_width() -> None:
    """A tokamak's field is stronger inboard, and by how much is the point."""
    configuration = conventional_configuration()
    point = level0_physics(configuration).operating_point
    geometry = configuration.geometry
    major, minor = geometry.major_radius_m, geometry.minor_radius_m
    assert point.inboard_field_t == toroidal_field_at_radius_t(
        point.axis_field_t, major, major - minor
    )
    assert point.outboard_field_t == toroidal_field_at_radius_t(
        point.axis_field_t, major, major + minor
    )
    assert point.inboard_field_t > point.axis_field_t > point.outboard_field_t
    assert point.field_ratio == point.inboard_field_t / point.outboard_field_t


def test_the_operating_density_is_the_declared_fraction_of_the_limit() -> None:
    """The record does the multiplication the reader would otherwise do."""
    configuration = conventional_configuration()
    point = level0_physics(configuration).operating_point
    assert point.operating_density_1e20_m3 == (
        point.greenwald_fraction * point.greenwald_density_limit_1e20_m3
    )
    assert point.operating_density_1e20_m3 < point.greenwald_density_limit_1e20_m3


def test_the_safety_margin_is_the_estimate_minus_the_floor() -> None:
    """Reported, not enforced: a floor is a declaration and not a law."""
    point = level0_physics(conventional_configuration()).operating_point
    assert point.safety_factor_margin == (
        point.cylindrical_safety_factor - point.safety_factor_floor
    )


def test_both_anchor_regimes_meet_their_own_declared_floor() -> None:
    """A fixture that declares a floor its own point misses is incoherent."""
    for configuration in (spherical_configuration(), conventional_configuration()):
        assert level0_physics(configuration).operating_point.safety_factor_margin > 0.0


def test_canonical_bytes_are_already_in_canonical_form() -> None:
    """Re-canonicalising the bytes is a no-op, and they round-trip."""
    record = level0_physics(conventional_configuration())
    data = record.canonical_bytes()
    assert data.endswith(b"\n")
    decoded = json.loads(data)
    assert decoded == record.to_record()
    assert list(decoded) == sorted(decoded)
    again = json.dumps(decoded, sort_keys=True, separators=(",", ":"))
    assert data == (again + "\n").encode("utf-8")
    assert record.digest_sha256() == hashlib.sha256(data).hexdigest()


def test_the_two_regimes_have_different_digests() -> None:
    """Two configurations are two records, and stably so."""
    spherical = level0_physics(spherical_configuration())
    conventional = level0_physics(conventional_configuration())
    assert spherical.digest_sha256() != conventional.digest_sha256()
    assert (
        spherical.digest_sha256()
        == level0_physics(spherical_configuration()).digest_sha256()
    )


def test_the_spherical_anchor_is_the_printed_pairing() -> None:
    """A = 1.5 with kappa = 2 is what the source pairs, and both are exact.

    The radii are 1.5 and 1.0 so the ratio is exactly 1.5 in binary; 1.2
    over 0.8 is 1.4999999999999998 and could not carry this equality.
    """
    configuration = spherical_configuration()
    point = level0_physics(configuration).operating_point
    assert point.aspect_ratio == ANCHOR_SPHERICAL_ASPECT_RATIO
    assert configuration.geometry.elongation == ANCHOR_SPHERICAL_ELONGATION


def test_the_conventional_anchor_is_the_other_printed_pairing() -> None:
    """Above A = 2.5 the source prints a natural elongation below 1.4.

    The pairing is what makes this anchorable: it can be got wrong in two
    directions, and a fixture that satisfied only one half would not be
    sitting where the source says such a device sits.
    """
    configuration = conventional_configuration()
    point = level0_physics(configuration).operating_point
    assert point.aspect_ratio > ANCHOR_CONVENTIONAL_ASPECT_RATIO_FLOOR
    assert configuration.geometry.elongation < ANCHOR_CONVENTIONAL_ELONGATION_CEILING


def test_the_spherical_regime_is_the_more_elongated_of_the_two() -> None:
    """The whole content of the printed pairing, stated as an ordering."""
    spherical = spherical_configuration().geometry
    conventional = conventional_configuration().geometry
    assert spherical.aspect_ratio < conventional.aspect_ratio
    assert spherical.elongation > conventional.elongation
