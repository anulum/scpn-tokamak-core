# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — magnet-system topology model

"""Magnet-system topology of a tokamak device configuration.

Counts describe the coil-system topology only; no field quality,
engineering feasibility, or machine-specific magnet claim is made.
"""

from __future__ import annotations

from dataclasses import dataclass

from scpn_tokamak_core.errors import DeviceConfigurationError


@dataclass(frozen=True, slots=True)
class CoilSystem:
    """Coil-system topology counts of a tokamak configuration.

    Parameters
    ----------
    toroidal_field_coil_count
        Number of toroidal-field coils; at least one.
    poloidal_field_coil_count
        Number of poloidal-field shaping coils; zero or more.
    has_central_solenoid
        Whether the configuration includes a central solenoid for
        inductive current drive.

    Raises
    ------
    DeviceConfigurationError
        If a count violates its lower bound.
    """

    toroidal_field_coil_count: int
    poloidal_field_coil_count: int
    has_central_solenoid: bool

    def __post_init__(self) -> None:
        """Validate the coil-count invariants.

        Raises
        ------
        DeviceConfigurationError
            If a count violates its lower bound.
        """
        if self.toroidal_field_coil_count < 1:
            raise DeviceConfigurationError(
                "toroidal_field_coil_count: must be at least 1, "
                f"got {self.toroidal_field_coil_count!r}"
            )
        if self.poloidal_field_coil_count < 0:
            raise DeviceConfigurationError(
                "poloidal_field_coil_count: must be non-negative, "
                f"got {self.poloidal_field_coil_count!r}"
            )
