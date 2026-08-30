# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — coil-system topology tests

"""Every validation branch of the coil-system topology model."""

from __future__ import annotations

import pytest

from scpn_tokamak_core.coils import CoilSystem
from scpn_tokamak_core.errors import DeviceConfigurationError


def test_valid_coil_system() -> None:
    """A valid topology constructs with its declared counts."""
    coils = CoilSystem(
        toroidal_field_coil_count=12,
        poloidal_field_coil_count=6,
        has_central_solenoid=True,
    )
    assert coils.toroidal_field_coil_count == 12
    assert coils.poloidal_field_coil_count == 6
    assert coils.has_central_solenoid is True


def test_zero_poloidal_coils_is_valid() -> None:
    """A topology without shaping coils is representable."""
    coils = CoilSystem(
        toroidal_field_coil_count=1,
        poloidal_field_coil_count=0,
        has_central_solenoid=False,
    )
    assert coils.poloidal_field_coil_count == 0


def test_toroidal_count_below_one_is_rejected() -> None:
    """A tokamak topology requires at least one toroidal-field coil."""
    with pytest.raises(DeviceConfigurationError, match="toroidal_field_coil_count"):
        CoilSystem(
            toroidal_field_coil_count=0,
            poloidal_field_coil_count=0,
            has_central_solenoid=True,
        )


def test_negative_poloidal_count_is_rejected() -> None:
    """Negative shaping-coil counts are rejected."""
    with pytest.raises(DeviceConfigurationError, match="poloidal_field_coil_count"):
        CoilSystem(
            toroidal_field_coil_count=8,
            poloidal_field_coil_count=-1,
            has_central_solenoid=False,
        )
