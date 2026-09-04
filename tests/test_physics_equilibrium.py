# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — shaped-torus closed form tests

"""The closed forms of a shaped torus and its vacuum field."""

from __future__ import annotations

import math

import pytest
from physics_fixtures import (
    ANCHOR_NORMALISED_CURRENT_CEILING,
    conventional_configuration,
    spherical_configuration,
)

from scpn_tokamak_core.errors import DeviceConfigurationError
from scpn_tokamak_core.geometry import ToroidalGeometry
from scpn_tokamak_core.physics.equilibrium import (
    SPHERICAL_TORUS_ASPECT_RATIO,
    normalised_current_ma_per_mt,
    plasma_volume_m3,
    toroidal_field_at_radius_t,
)


def test_the_volume_is_pappus_not_an_approximation() -> None:
    """An ellipse of area pi kappa a^2 swept 2 pi R encloses their product.

    Asserted to one part in 1e-15 and not as an equality, and the reason
    was measured rather than assumed: the implementation multiplies the
    six factors in one order and Pappus's statement groups them in
    another, and floating-point multiplication is not associative. The two
    differ by exactly one unit in the last place here. Writing an equality
    would be asserting an operation order, not a theorem.
    """
    geometry = ToroidalGeometry(
        major_radius_m=6.0, minor_radius_m=2.0, elongation=1.8, triangularity=0.0
    )
    ellipse_area = math.pi * 1.8 * 2.0 * 2.0
    swept = 2.0 * math.pi * 6.0 * ellipse_area
    assert math.isclose(plasma_volume_m3(geometry), swept, rel_tol=1.0e-15)
    assert abs(plasma_volume_m3(geometry) - swept) <= math.ulp(swept)


def test_the_volume_scales_linearly_in_the_elongation() -> None:
    """Doubling kappa doubles the cross-section and so the volume."""
    round_plasma = ToroidalGeometry(6.0, 2.0, 1.0, 0.0)
    tall_plasma = ToroidalGeometry(6.0, 2.0, 2.0, 0.0)
    assert plasma_volume_m3(tall_plasma) == 2.0 * plasma_volume_m3(round_plasma)


def test_the_triangularity_does_not_enter_the_volume() -> None:
    """Stated in the docstring and in the non-claims, so it is tested.

    A triangular deformation moves area about the centroid without
    changing it to first order, so the volume this module reports is the
    elliptic one. Two geometries differing only in triangularity give the
    same volume, and the record says that is a limitation rather than a
    result.
    """
    assert plasma_volume_m3(ToroidalGeometry(6.0, 2.0, 1.8, 0.0)) == plasma_volume_m3(
        ToroidalGeometry(6.0, 2.0, 1.8, 0.5)
    )


def test_the_vacuum_field_falls_as_one_over_the_major_radius() -> None:
    """B R is constant outside the coils."""
    assert toroidal_field_at_radius_t(5.3, 6.0, 6.0) == 5.3
    assert toroidal_field_at_radius_t(5.3, 6.0, 12.0) == 5.3 / 2.0
    assert toroidal_field_at_radius_t(5.3, 6.0, 3.0) == 5.3 * 2.0


@pytest.mark.parametrize(
    ("field", "axis", "radius", "field_name"),
    [
        (0.0, 6.0, 6.0, "axis_field_t"),
        (5.3, 0.0, 6.0, "major_radius_m"),
        (5.3, 6.0, 0.0, "radius_m"),
        (math.nan, 6.0, 6.0, "axis_field_t"),
        (5.3, 6.0, math.inf, "radius_m"),
    ],
)
def test_the_field_refuses_each_argument_by_name(
    field: float, axis: float, radius: float, field_name: str
) -> None:
    """Each refusal names the field that is wrong."""
    with pytest.raises(DeviceConfigurationError, match=field_name):
        toroidal_field_at_radius_t(field, axis, radius)


def test_the_normalised_current_is_the_printed_quantity() -> None:
    """``I_p / (a B_t)``, the ratio the spherical-torus paper bounds."""
    assert normalised_current_ma_per_mt(15.0, 2.0, 5.3) == 15.0 / (2.0 * 5.3)


@pytest.mark.parametrize(
    ("current", "minor", "field", "field_name"),
    [
        (0.0, 2.0, 5.3, "plasma_current_ma"),
        (15.0, 0.0, 5.3, "minor_radius_m"),
        (15.0, 2.0, -1.0, "toroidal_field_t"),
    ],
)
def test_the_normalised_current_refuses_each_argument_by_name(
    current: float, minor: float, field: float, field_name: str
) -> None:
    """Each refusal names the field that is wrong."""
    with pytest.raises(DeviceConfigurationError, match=field_name):
        normalised_current_ma_per_mt(current, minor, field)


def test_both_anchor_regimes_sit_under_the_printed_current_ceiling() -> None:
    """The source prints about 7 MA/(m T) as reachable; neither exceeds it."""
    for configuration in (spherical_configuration(), conventional_configuration()):
        limits = configuration.limits
        got = normalised_current_ma_per_mt(
            limits.plasma_current_ma,
            configuration.geometry.minor_radius_m,
            limits.toroidal_field_t,
        )
        assert 0.0 < got <= ANCHOR_NORMALISED_CURRENT_CEILING


def test_the_spherical_fixture_is_below_the_printed_aspect_ratio() -> None:
    """A spherical torus is a device of aspect ratio below two."""
    assert (
        spherical_configuration().geometry.aspect_ratio < SPHERICAL_TORUS_ASPECT_RATIO
    )
    assert (
        conventional_configuration().geometry.aspect_ratio
        > SPHERICAL_TORUS_ASPECT_RATIO
    )
