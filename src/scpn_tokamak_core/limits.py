# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — operational limit model

"""Operational limits of a tokamak device configuration.

The derived quantities implement two standard textbook estimates and
nothing more. Both are rough consistency instruments with documented
applicability bounds; neither is an equilibrium calculation, and no claim
about any real machine follows from them.

- Greenwald density limit ``n_G = I_p / (pi * a**2)`` in units of
  ``10^20 m^-3`` with ``I_p`` in MA and ``a`` in metres
  (M. Greenwald, Plasma Phys. Control. Fusion 44 (2002) R27).
- Cylindrical equivalent safety factor
  ``q_cyl = 5 a^2 B_t (1 + kappa^2) / (2 R0 I_p)`` with ``B_t`` in tesla
  and ``I_p`` in MA — the elongation-corrected cylindrical estimate
  (ITER Physics Basis, Nucl. Fusion 39 (1999) 2137, ch. 1); it
  approximates edge safety only for large aspect ratio and moderate
  shaping.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scpn_tokamak_core.errors import DeviceConfigurationError
from scpn_tokamak_core.geometry import (
    ToroidalGeometry,
    require_finite,
    require_positive,
)


@dataclass(frozen=True, slots=True)
class OperationalLimits:
    """Declared operating-point limits of a tokamak configuration.

    Parameters
    ----------
    toroidal_field_t
        Toroidal magnetic field ``B_t`` at the major radius, in tesla;
        strictly positive.
    plasma_current_ma
        Flat-top plasma current ``I_p`` in mega-amperes; strictly
        positive.
    safety_factor_floor
        Declared lower bound on the edge safety factor the operating
        point must respect; strictly positive.
    greenwald_fraction
        Declared operating fraction of the Greenwald density limit, in
        ``(0, 1]``.
    flat_top_duration_s
        Declared flat-top duration in seconds; non-negative.

    Raises
    ------
    DeviceConfigurationError
        If any limit is non-finite or outside its model bound.
    """

    toroidal_field_t: float
    plasma_current_ma: float
    safety_factor_floor: float
    greenwald_fraction: float
    flat_top_duration_s: float

    def __post_init__(self) -> None:
        """Validate every declared limit.

        Raises
        ------
        DeviceConfigurationError
            If any limit is non-finite or outside its model bound.
        """
        require_positive("toroidal_field_t", self.toroidal_field_t)
        require_positive("plasma_current_ma", self.plasma_current_ma)
        require_positive("safety_factor_floor", self.safety_factor_floor)
        require_finite("greenwald_fraction", self.greenwald_fraction)
        if not 0.0 < self.greenwald_fraction <= 1.0:
            raise DeviceConfigurationError(
                "greenwald_fraction: must be within (0, 1], "
                f"got {self.greenwald_fraction!r}"
            )
        require_finite("flat_top_duration_s", self.flat_top_duration_s)
        if self.flat_top_duration_s < 0.0:
            raise DeviceConfigurationError(
                "flat_top_duration_s: must be non-negative, "
                f"got {self.flat_top_duration_s!r}"
            )

    def greenwald_density_limit_1e20_m3(self, geometry: ToroidalGeometry) -> float:
        """Greenwald density limit for this current in the given geometry.

        Parameters
        ----------
        geometry
            Validated toroidal geometry supplying the minor radius.

        Returns
        -------
        float
            ``n_G = I_p / (pi * a**2)`` in units of ``10^20 m^-3``.
        """
        return self.plasma_current_ma / (math.pi * geometry.minor_radius_m**2)

    def cylindrical_safety_factor(self, geometry: ToroidalGeometry) -> float:
        """Elongation-corrected cylindrical safety-factor estimate.

        Parameters
        ----------
        geometry
            Validated toroidal geometry supplying radii and elongation.

        Returns
        -------
        float
            ``q_cyl = 5 a^2 B_t (1 + kappa^2) / (2 R0 I_p)``; a rough
            consistency instrument only, valid for large aspect ratio
            and moderate shaping.
        """
        return (
            5.0
            * geometry.minor_radius_m**2
            * self.toroidal_field_t
            * (1.0 + geometry.elongation**2)
        ) / (2.0 * geometry.major_radius_m * self.plasma_current_ma)
