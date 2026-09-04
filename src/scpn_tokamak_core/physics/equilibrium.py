# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — closed forms of a shaped torus

"""Closed forms of a shaped toroidal plasma and its vacuum field.

Three relations, each exact rather than fitted.

**Plasma volume.** An elliptic cross-section of semi-axes ``a`` and
``kappa a`` swept about a major radius ``R`` encloses ``2 pi^2 R a^2
kappa``. That is Pappus's theorem, not an approximation: the centroid of
the ellipse travels ``2 pi R`` and its area is ``pi kappa a^2``. The
triangularity the configuration also carries does **not** enter it — a
triangular deformation moves area around the centroid without changing it
to first order, and this module does not pretend otherwise.

**Vacuum toroidal field.** Outside the coils the toroidal field falls as
one over the major radius, ``B(R) = B_0 R_0 / R``, so a tokamak plasma
sits in a field that is stronger on the inboard side than the outboard by
the ratio of those radii. Exact for a vacuum field; the plasma's own
paramagnetism is not modelled.

**Normalised plasma current.** ``I_p / (a B_t)`` in megaampere per
metre-tesla, the quantity Peng and Strickler print a ceiling for when
describing the spherical-torus regime (ORNL/FEDC-85/6, 1985: "large plasma
current with I/(a B) up to about 7 MA/mT").
"""

from __future__ import annotations

import math
from typing import Final

from scpn_tokamak_core.errors import DeviceConfigurationError
from scpn_tokamak_core.geometry import ToroidalGeometry

#: Ceiling on the normalised plasma current that Peng and Strickler print
#: for the spherical-torus regime, in megaampere per metre-tesla.
SPHERICAL_TORUS_NORMALISED_CURRENT_CEILING: Final = 7.0
#: Aspect ratio below which that paper calls a device a spherical torus.
SPHERICAL_TORUS_ASPECT_RATIO: Final = 2.0


def _positive(name: str, value: float) -> float:
    """Refuse a value that is not finite and strictly positive.

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
        If the value is non-finite or not strictly positive.
    """
    if not math.isfinite(value) or value <= 0.0:
        raise DeviceConfigurationError(
            f"{name}: must be finite and strictly positive, got {value!r}"
        )
    return value


def plasma_volume_m3(geometry: ToroidalGeometry) -> float:
    """Return the volume enclosed by an elongated toroidal plasma.

    Parameters
    ----------
    geometry
        Validated toroidal geometry.

    Returns
    -------
    float
        ``2 pi^2 R a^2 kappa``, exact by Pappus's theorem for an elliptic
        cross-section swept about the major radius. The triangularity does
        not enter: a triangular deformation redistributes area about the
        centroid without changing it to first order.
    """
    return (
        2.0
        * math.pi
        * math.pi
        * geometry.major_radius_m
        * geometry.minor_radius_m
        * geometry.minor_radius_m
        * geometry.elongation
    )


def toroidal_field_at_radius_t(
    axis_field_t: float, major_radius_m: float, radius_m: float
) -> float:
    """Return the vacuum toroidal field at a major radius.

    Parameters
    ----------
    axis_field_t
        Field on the magnetic axis; strictly positive.
    major_radius_m
        Major radius of that axis; strictly positive.
    radius_m
        Major radius the field is wanted at; strictly positive.

    Returns
    -------
    float
        ``B_0 R_0 / R``. Exact for a vacuum field; the plasma's own
        paramagnetism is not modelled.

    Raises
    ------
    DeviceConfigurationError
        If any argument is non-finite or not strictly positive.
    """
    field = _positive("axis_field_t", axis_field_t)
    axis = _positive("major_radius_m", major_radius_m)
    radius = _positive("radius_m", radius_m)
    return field * axis / radius


def normalised_current_ma_per_mt(
    plasma_current_ma: float, minor_radius_m: float, toroidal_field_t: float
) -> float:
    """Return the normalised plasma current.

    Parameters
    ----------
    plasma_current_ma
        Plasma current in megaampere; strictly positive.
    minor_radius_m
        Plasma minor radius; strictly positive.
    toroidal_field_t
        Toroidal field on axis; strictly positive.

    Returns
    -------
    float
        ``I_p / (a B_t)`` in megaampere per metre-tesla.

    Raises
    ------
    DeviceConfigurationError
        If any argument is non-finite or not strictly positive.
    """
    current = _positive("plasma_current_ma", plasma_current_ma)
    minor = _positive("minor_radius_m", minor_radius_m)
    field = _positive("toroidal_field_t", toroidal_field_t)
    return current / (minor * field)
