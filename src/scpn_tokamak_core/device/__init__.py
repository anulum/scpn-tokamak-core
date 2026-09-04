# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — device model package

"""Device envelope and the two geometry tiers of the tokamak family.

The package is named ``device`` rather than ``geometry``, which every
sibling family uses, for one reason: in this repository
``scpn_tokamak_core.geometry`` already belongs to the plasma shape — the
major and minor radii, the elongation and the triangularity — because for
a tokamak the shape *is* a configuration parameter. Renaming a published
submodule to free the word is the owner's decision and not a tier
landing's, so the tier took the other name. The class and body vocabulary
is the group's throughout. Design record: ADR 0006.
"""

from __future__ import annotations

from scpn_tokamak_core.device.cad import (
    CAD_MODEL_NON_CLAIMS,
    CAD_MODEL_SCHEMA,
    CAD_MODEL_SCHEMA_VERSION,
    CAD_MODEL_UNITS,
    DEFAULT_ANGULAR_DEFLECTION_RAD,
    DEFAULT_LINEAR_DEFLECTION_M,
    DEFAULT_REFERENCE_MESH_SEGMENTS,
    DeviceModelCAD,
    build_device_cad,
)
from scpn_tokamak_core.device.envelope import (
    ENVELOPE_FIELDS,
    DeviceEnvelope,
    envelope_from_record,
)
from scpn_tokamak_core.device.model import (
    BODY_NAMES,
    BODY_PLASMA_COLUMN,
    BODY_TOROIDAL_FIELD_WINDING,
    BODY_VACUUM_VESSEL,
    MODEL_NON_CLAIMS,
    MODEL_SCHEMA,
    MODEL_SCHEMA_VERSION,
    MODEL_UNITS,
    DeviceModel3D,
    build_device_model,
    equivalent_column_radius_m,
    periodic_length_m,
)

__all__ = [
    "BODY_NAMES",
    "BODY_PLASMA_COLUMN",
    "BODY_TOROIDAL_FIELD_WINDING",
    "BODY_VACUUM_VESSEL",
    "CAD_MODEL_NON_CLAIMS",
    "CAD_MODEL_SCHEMA",
    "CAD_MODEL_SCHEMA_VERSION",
    "CAD_MODEL_UNITS",
    "DEFAULT_ANGULAR_DEFLECTION_RAD",
    "DEFAULT_LINEAR_DEFLECTION_M",
    "DEFAULT_REFERENCE_MESH_SEGMENTS",
    "ENVELOPE_FIELDS",
    "MODEL_NON_CLAIMS",
    "MODEL_SCHEMA",
    "MODEL_SCHEMA_VERSION",
    "MODEL_UNITS",
    "DeviceEnvelope",
    "DeviceModel3D",
    "DeviceModelCAD",
    "build_device_cad",
    "build_device_model",
    "envelope_from_record",
    "equivalent_column_radius_m",
    "periodic_length_m",
]
