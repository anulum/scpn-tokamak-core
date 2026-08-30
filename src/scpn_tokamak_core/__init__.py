# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — device configuration model package

"""Device configuration model of the SCPN tokamak device family.

Public surface of the ``device_configuration_model`` capability at
``computational_prototype`` maturity: validated parameter objects,
documented consistency estimates, canonical serialisation with SHA-256
digests, and a data-only pin to the SPO reactor registry. No claim about
any real machine is made anywhere in this package.
"""

from __future__ import annotations

from typing import Final

from scpn_tokamak_core.coils import CoilSystem
from scpn_tokamak_core.configuration import (
    OWNED_CONFIGURATIONS,
    SPHERICAL_MAX_ASPECT_RATIO,
    ConsistencyFinding,
    DeviceConfiguration,
    RegistryBinding,
    configuration_from_bytes,
    configuration_from_record,
)
from scpn_tokamak_core.errors import DeviceConfigurationError
from scpn_tokamak_core.geometry import (
    ELONGATION_BOUNDS,
    TRIANGULARITY_BOUNDS,
    ToroidalGeometry,
)
from scpn_tokamak_core.limits import OperationalLimits

__version__: Final = "0.1.0.dev0"

__all__ = [
    "ELONGATION_BOUNDS",
    "OWNED_CONFIGURATIONS",
    "SPHERICAL_MAX_ASPECT_RATIO",
    "TRIANGULARITY_BOUNDS",
    "CoilSystem",
    "ConsistencyFinding",
    "DeviceConfiguration",
    "DeviceConfigurationError",
    "OperationalLimits",
    "RegistryBinding",
    "ToroidalGeometry",
    "__version__",
    "configuration_from_bytes",
    "configuration_from_record",
]
