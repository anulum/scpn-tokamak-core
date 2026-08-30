# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — operational limit model tests

"""Every validation branch and estimate of the operational limit model.

All parameter sets in this module are synthetic fixtures; none describes
any real machine.
"""

from __future__ import annotations

import math

import pytest

from scpn_tokamak_core.errors import DeviceConfigurationError
from scpn_tokamak_core.geometry import ToroidalGeometry
from scpn_tokamak_core.limits import OperationalLimits


def synthetic_limits(**overrides: float) -> OperationalLimits:
    """Build valid synthetic limits with optional field overrides."""
    values: dict[str, float] = {
        "toroidal_field_t": 4.0,
        "plasma_current_ma": 5.0,
        "safety_factor_floor": 2.0,
        "greenwald_fraction": 0.8,
        "flat_top_duration_s": 10.0,
    }
    values.update(overrides)
    return OperationalLimits(**values)


def synthetic_geometry() -> ToroidalGeometry:
    """Build the reference synthetic geometry for estimate checks."""
    return ToroidalGeometry(
        major_radius_m=3.0,
        minor_radius_m=1.0,
        elongation=1.6,
        triangularity=0.3,
    )


def test_valid_limits_construct() -> None:
    """A valid limit declaration constructs unchanged."""
    limits = synthetic_limits()
    assert limits.toroidal_field_t == 4.0
    assert limits.flat_top_duration_s == 10.0


def test_zero_flat_top_is_valid() -> None:
    """A zero flat-top duration is representable."""
    assert synthetic_limits(flat_top_duration_s=0.0).flat_top_duration_s == 0.0


def test_full_greenwald_fraction_is_valid() -> None:
    """The Greenwald fraction bound is inclusive at one."""
    assert synthetic_limits(greenwald_fraction=1.0).greenwald_fraction == 1.0


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"toroidal_field_t": 0.0}, "toroidal_field_t"),
        ({"plasma_current_ma": -5.0}, "plasma_current_ma"),
        ({"safety_factor_floor": 0.0}, "safety_factor_floor"),
        ({"greenwald_fraction": 0.0}, "greenwald_fraction"),
        ({"greenwald_fraction": 1.1}, "greenwald_fraction"),
        ({"greenwald_fraction": math.nan}, "greenwald_fraction"),
        ({"flat_top_duration_s": -1.0}, "flat_top_duration_s"),
        ({"flat_top_duration_s": math.inf}, "flat_top_duration_s"),
    ],
)
def test_invalid_limits_are_rejected(
    overrides: dict[str, float], fragment: str
) -> None:
    """Each limit violation is rejected with its field name."""
    with pytest.raises(DeviceConfigurationError, match=fragment):
        synthetic_limits(**overrides)


def test_greenwald_density_limit_formula() -> None:
    """The Greenwald limit follows ``I_p / (pi a^2)`` exactly."""
    value = synthetic_limits().greenwald_density_limit_1e20_m3(synthetic_geometry())
    assert value == pytest.approx(5.0 / math.pi)


def test_cylindrical_safety_factor_formula() -> None:
    """The estimate follows ``5 a^2 B (1 + kappa^2) / (2 R0 I_p)`` exactly."""
    value = synthetic_limits().cylindrical_safety_factor(synthetic_geometry())
    expected = 5.0 * 1.0 * 4.0 * (1.0 + 1.6**2) / (2.0 * 3.0 * 5.0)
    assert value == pytest.approx(expected)
