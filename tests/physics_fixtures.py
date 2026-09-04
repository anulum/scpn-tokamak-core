# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — level-0 physics fixtures

"""Fixtures of the level-0 physics tests: two anchored regimes.

This family's anchor is unusual: the filed source prints **relations
between regimes** rather than one machine. Peng and Strickler
(ORNL/FEDC-85/6, 1985) print that a spherical torus is a device of aspect
ratio below two; that at ``A ~ 1.5`` an elongation of ``kappa = 2`` occurs
naturally with only a dipole vertical field; that for ``A > 2.5`` the
natural elongation is **less than 1.4**; and that the normalised plasma
current reaches about ``7 MA/(m T)``.

So there are two anchor fixtures, one for each configuration this
repository owns, and each sits at a printed pairing: the spherical one at
``A = 1.5`` with ``kappa = 2``, the conventional one above ``A = 2.5``
with an elongation below ``1.4``. A pairing is anchorable in a way a lone
number is not — it can be got wrong in two directions.

The density limit itself is anchored differently and more directly:
Greenwald (Plasma Phys. Control. Fusion 44 (2002) R27) prints
``nG = I_P / (pi a^2)`` as its equation 1.3, "where nG is the
line-averaged density in units of 10^20 m^-3", which is the form and the
units this repository already implements.

Declared here, and said to be declared: every absolute dimension. Neither
source prints a machine's major radius, field or current, only the
relations among them, so the fixtures choose values that sit at the
printed pairings and nothing more is claimed for them.
"""

from __future__ import annotations

from scpn_tokamak_core.coils import CoilSystem
from scpn_tokamak_core.configuration import DeviceConfiguration, RegistryBinding
from scpn_tokamak_core.geometry import ToroidalGeometry
from scpn_tokamak_core.limits import OperationalLimits

REGISTRY = RegistryBinding(version="1.0.0", digest_sha256="0" * 64)

#: Aspect ratio below which Peng and Strickler call a device a spherical
#: torus, and the ratio at which they print a natural elongation of two.
ANCHOR_SPHERICAL_ASPECT_RATIO = 1.5
ANCHOR_SPHERICAL_ELONGATION = 2.0
#: Above this aspect ratio the same paper prints a natural elongation
#: below 1.4.
ANCHOR_CONVENTIONAL_ASPECT_RATIO_FLOOR = 2.5
ANCHOR_CONVENTIONAL_ELONGATION_CEILING = 1.4
#: Normalised plasma current the same paper prints as reachable, in
#: megaampere per metre-tesla.
ANCHOR_NORMALISED_CURRENT_CEILING = 7.0


def spherical_configuration() -> DeviceConfiguration:
    """Build a spherical torus at the printed aspect ratio and elongation.

    Returns
    -------
    DeviceConfiguration
        A validated configuration whose aspect ratio is exactly 1.5 and
        whose elongation is exactly the 2 the source pairs with it. The
        radii are 1.5 and 1.0 rather than 1.2 and 0.8 for a measured
        reason: 1.2/0.8 is 1.4999999999999998 in binary and 1.5/1.0 is
        exact, so the anchor test can assert an equality.
    """
    return DeviceConfiguration(
        identifier="spherical_tokamak",
        geometry=ToroidalGeometry(
            major_radius_m=1.5,
            minor_radius_m=1.0,
            elongation=ANCHOR_SPHERICAL_ELONGATION,
            triangularity=0.4,
        ),
        coils=CoilSystem(
            toroidal_field_coil_count=12,
            poloidal_field_coil_count=6,
            has_central_solenoid=False,
        ),
        limits=OperationalLimits(
            toroidal_field_t=0.5,
            plasma_current_ma=2.0,
            safety_factor_floor=2.0,
            greenwald_fraction=0.6,
            flat_top_duration_s=5.0,
        ),
        registry=REGISTRY,
    )


def conventional_configuration() -> DeviceConfiguration:
    """Build a conventional tokamak above the printed aspect ratio.

    Returns
    -------
    DeviceConfiguration
        A validated configuration above ``A = 2.5`` whose elongation sits
        below the 1.4 the source prints as natural there.
    """
    return DeviceConfiguration(
        identifier="conventional_tokamak",
        geometry=ToroidalGeometry(
            major_radius_m=6.0,
            minor_radius_m=2.0,
            elongation=1.35,
            triangularity=0.3,
        ),
        coils=CoilSystem(
            toroidal_field_coil_count=18,
            poloidal_field_coil_count=8,
            has_central_solenoid=True,
        ),
        limits=OperationalLimits(
            toroidal_field_t=5.3,
            plasma_current_ma=15.0,
            safety_factor_floor=1.5,
            greenwald_fraction=0.85,
            flat_top_duration_s=400.0,
        ),
        registry=REGISTRY,
    )
