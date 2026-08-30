# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — toroidal geometry model tests

"""Every validation branch of the toroidal geometry model.

All parameter sets in this module are synthetic fixtures; none describes
any real machine.
"""

from __future__ import annotations

import math

import pytest

from scpn_tokamak_core.errors import DeviceConfigurationError
from scpn_tokamak_core.geometry import (
    ToroidalGeometry,
    require_finite,
    require_positive,
)


def synthetic_geometry(**overrides: float) -> ToroidalGeometry:
    """Build a valid synthetic geometry with optional field overrides."""
    values: dict[str, float] = {
        "major_radius_m": 3.0,
        "minor_radius_m": 1.0,
        "elongation": 1.6,
        "triangularity": 0.3,
    }
    values.update(overrides)
    return ToroidalGeometry(**values)


def test_valid_geometry_and_aspect_ratio() -> None:
    """A valid torus constructs and derives its aspect ratio."""
    geometry = synthetic_geometry()
    assert geometry.aspect_ratio == pytest.approx(3.0)


def test_require_finite_accepts_and_rejects() -> None:
    """The finite guard returns the value and rejects NaN and infinity."""
    assert require_finite("x", 1.5) == 1.5
    for bad in (math.nan, math.inf, -math.inf):
        with pytest.raises(DeviceConfigurationError, match="x: must be finite"):
            require_finite("x", bad)


def test_require_positive_accepts_and_rejects() -> None:
    """The positive guard returns the value and rejects zero and below."""
    assert require_positive("x", 0.1) == 0.1
    for bad in (0.0, -2.0):
        with pytest.raises(DeviceConfigurationError, match="strictly positive"):
            require_positive("x", bad)
    with pytest.raises(DeviceConfigurationError, match="must be finite"):
        require_positive("x", math.nan)


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"major_radius_m": 0.0}, "major_radius_m"),
        ({"minor_radius_m": -1.0}, "minor_radius_m"),
        ({"minor_radius_m": 3.0}, "strictly smaller than major_radius_m"),
        ({"minor_radius_m": 4.0}, "strictly smaller than major_radius_m"),
        ({"elongation": 0.9}, "elongation"),
        ({"elongation": 3.1}, "elongation"),
        ({"elongation": math.nan}, "elongation"),
        ({"triangularity": -1.5}, "triangularity"),
        ({"triangularity": 1.5}, "triangularity"),
        ({"triangularity": math.inf}, "triangularity"),
    ],
)
def test_invalid_geometry_is_rejected(
    overrides: dict[str, float], fragment: str
) -> None:
    """Each geometric invariant violation is rejected with its field name."""
    with pytest.raises(DeviceConfigurationError, match=fragment):
        synthetic_geometry(**overrides)


def test_boundary_values_are_accepted() -> None:
    """The documented model bounds are inclusive."""
    assert synthetic_geometry(elongation=1.0).elongation == 1.0
    assert synthetic_geometry(elongation=3.0).elongation == 3.0
    assert synthetic_geometry(triangularity=-1.0).triangularity == -1.0
    assert synthetic_geometry(triangularity=1.0).triangularity == 1.0
