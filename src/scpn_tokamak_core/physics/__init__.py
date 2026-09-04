# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — level-0 device physics package

"""Level-0 device physics of the tokamak family.

The closed forms of a shaped torus — the volume its elliptic cross-section
encloses, the vacuum toroidal field across the plasma's own width, and the
normalised plasma current — composed with the density limit and the
cylindrical safety factor the configuration's own operational limits
already compute. Nothing is restated here that the repository already
owns. Design record: ADR 0005.
"""

from __future__ import annotations

from scpn_tokamak_core.physics.equilibrium import (
    SPHERICAL_TORUS_ASPECT_RATIO,
    SPHERICAL_TORUS_NORMALISED_CURRENT_CEILING,
    normalised_current_ma_per_mt,
    plasma_volume_m3,
    toroidal_field_at_radius_t,
)
from scpn_tokamak_core.physics.level0 import (
    LEVEL0_NON_CLAIMS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    Level0Physics,
    OperatingPoint,
    level0_physics,
)

__all__ = [
    "LEVEL0_NON_CLAIMS",
    "LEVEL0_SCHEMA",
    "LEVEL0_SCHEMA_VERSION",
    "SPHERICAL_TORUS_ASPECT_RATIO",
    "SPHERICAL_TORUS_NORMALISED_CURRENT_CEILING",
    "Level0Physics",
    "OperatingPoint",
    "level0_physics",
    "normalised_current_ma_per_mt",
    "plasma_volume_m3",
    "toroidal_field_at_radius_t",
]
