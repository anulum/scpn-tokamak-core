# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — toroidal plasma geometry model

"""Toroidal plasma geometry of a tokamak device configuration.

The model bounds documented here are modelling-domain bounds of this
repository, not claims about any real machine: elongation is accepted in
``[1, 3]`` and triangularity in ``[-1, 1]``, which covers published
tokamak operating shapes while rejecting unphysical inputs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

from scpn_tokamak_core.errors import DeviceConfigurationError

ELONGATION_BOUNDS: Final = (1.0, 3.0)
TRIANGULARITY_BOUNDS: Final = (-1.0, 1.0)


def require_finite(name: str, value: float) -> float:
    """Return ``value`` when finite, otherwise fail closed.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    value
        Value under validation.

    Returns
    -------
    float
        The validated value.

    Raises
    ------
    DeviceConfigurationError
        If ``value`` is NaN or infinite; non-finite input is rejected,
        never clamped.
    """
    if not math.isfinite(value):
        raise DeviceConfigurationError(f"{name}: must be finite, got {value!r}")
    return value


def require_positive(name: str, value: float) -> float:
    """Return ``value`` when finite and strictly positive.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    value
        Value under validation.

    Returns
    -------
    float
        The validated value.

    Raises
    ------
    DeviceConfigurationError
        If ``value`` is non-finite or not strictly positive.
    """
    require_finite(name, value)
    if value <= 0.0:
        raise DeviceConfigurationError(
            f"{name}: must be strictly positive, got {value!r}"
        )
    return value


@dataclass(frozen=True, slots=True)
class ToroidalGeometry:
    """Axisymmetric toroidal plasma geometry parameters.

    Parameters
    ----------
    major_radius_m
        Plasma major radius ``R0`` in metres; strictly positive.
    minor_radius_m
        Plasma minor radius ``a`` in metres; strictly positive and
        strictly smaller than ``major_radius_m``.
    elongation
        Plasma elongation ``kappa``; accepted in ``[1, 3]``.
    triangularity
        Plasma triangularity ``delta``; accepted in ``[-1, 1]``.

    Raises
    ------
    DeviceConfigurationError
        If any parameter is non-finite or outside its model bound.
    """

    major_radius_m: float
    minor_radius_m: float
    elongation: float
    triangularity: float

    def __post_init__(self) -> None:
        """Validate every geometric invariant of the torus.

        Raises
        ------
        DeviceConfigurationError
            If any parameter is non-finite or outside its model bound.
        """
        require_positive("major_radius_m", self.major_radius_m)
        require_positive("minor_radius_m", self.minor_radius_m)
        if self.minor_radius_m >= self.major_radius_m:
            raise DeviceConfigurationError(
                "minor_radius_m: must be strictly smaller than major_radius_m "
                f"({self.minor_radius_m!r} >= {self.major_radius_m!r})"
            )
        low, high = ELONGATION_BOUNDS
        require_finite("elongation", self.elongation)
        if not low <= self.elongation <= high:
            raise DeviceConfigurationError(
                f"elongation: must be within [{low}, {high}], got {self.elongation!r}"
            )
        low, high = TRIANGULARITY_BOUNDS
        require_finite("triangularity", self.triangularity)
        if not low <= self.triangularity <= high:
            raise DeviceConfigurationError(
                f"triangularity: must be within [{low}, {high}], "
                f"got {self.triangularity!r}"
            )

    @property
    def aspect_ratio(self) -> float:
        """Aspect ratio ``A = R0 / a`` of the validated torus.

        Returns
        -------
        float
            Ratio of major to minor radius; always greater than one.
        """
        return self.major_radius_m / self.minor_radius_m
