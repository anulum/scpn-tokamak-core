# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — device envelope of the cylindrical periodic equivalent

"""Validated mechanical envelope of the cylindrical periodic equivalent.

The configuration carries the plasma: major and minor radii, elongation
and triangularity. Those are read from there and never repeated here.
What this envelope adds is what surrounds the plasma column — the vacuum
vessel wall at the plasma edge, the gap outside it, and the
toroidal-field winding beyond that.

The construction is the one the reversed-field-pinch family already
uses: the toroidal device is unrolled into a straight cylinder of
periodic length ``2 pi R0``. That is the standard reduced model of an
axisymmetric torus, and what it drops — the toroidal curvature and with
it every quantity that depends on the difference between the inboard and
outboard sides — it drops visibly rather than quietly, because the model
record says so.

Validation is fail-closed, serialisation is canonical, and the SHA-256
digest identifies the exact envelope.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from scpn_tokamak_core.errors import DeviceGeometryError
from scpn_tokamak_core.geometry import require_positive

ENVELOPE_FIELDS: Final = (
    "vessel_wall_thickness_m",
    "winding_gap_m",
    "winding_thickness_m",
)


def _positive(name: str, value: float) -> float:
    """Apply the shared positivity rule under the device error type.

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
    DeviceGeometryError
        If the value is non-finite or not strictly positive.
    """
    try:
        return require_positive(name, value)
    except ValueError as exc:
        raise DeviceGeometryError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class DeviceEnvelope:
    """Validated mechanical envelope around the plasma column.

    Parameters
    ----------
    vessel_wall_thickness_m
        Radial thickness of the vacuum vessel wall, which sits directly
        at the plasma edge; strictly positive.
    winding_gap_m
        Radial clearance between the outside of the vessel wall and the
        inside of the toroidal-field winding; strictly positive.
    winding_thickness_m
        Radial thickness of the toroidal-field winding; strictly
        positive.

    Raises
    ------
    DeviceGeometryError
        If any value is non-finite or not strictly positive.
    """

    vessel_wall_thickness_m: float
    winding_gap_m: float
    winding_thickness_m: float

    def __post_init__(self) -> None:
        """Validate every declared value.

        Raises
        ------
        DeviceGeometryError
            If any value is non-finite or not strictly positive.
        """
        for name in ENVELOPE_FIELDS:
            _positive(name, getattr(self, name))

    @property
    def radial_build_m(self) -> float:
        """Total radial distance from the plasma edge to the winding's outside."""
        return (
            self.vessel_wall_thickness_m + self.winding_gap_m + self.winding_thickness_m
        )

    def to_record(self) -> dict[str, float]:
        """Project the envelope to a JSON-serialisable record.

        Returns
        -------
        dict[str, float]
            Every declared parameter under its name.
        """
        return {name: getattr(self, name) for name in ENVELOPE_FIELDS}

    def canonical_bytes(self) -> bytes:
        """Serialise the envelope canonically.

        Returns
        -------
        bytes
            UTF-8 JSON with sorted keys, minimal separators and a
            trailing newline; NaN and infinity are never emitted.
        """
        text = json.dumps(
            self.to_record(), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        return (text + "\n").encode("utf-8")

    def digest_sha256(self) -> str:
        """Identify the exact envelope.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _number(record: dict[str, Any], field: str) -> float:
    """Return one required real-number field of a record.

    Parameters
    ----------
    record
        Decoded object.
    field
        Field name.

    Returns
    -------
    float
        The value as a float.

    Raises
    ------
    DeviceGeometryError
        If the field is absent or is not a real number.
    """
    if field not in record:
        raise DeviceGeometryError(f"{field}: required")
    value = record[field]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DeviceGeometryError(f"{field}: must be a real number, got {value!r}")
    return float(value)


def envelope_from_record(record: dict[str, Any]) -> DeviceEnvelope:
    """Build an envelope from a decoded record, refusing unknown fields.

    Parameters
    ----------
    record
        Decoded object carrying exactly :data:`ENVELOPE_FIELDS`.

    Returns
    -------
    DeviceEnvelope
        The validated envelope.

    Raises
    ------
    DeviceGeometryError
        If a field is missing, of the wrong type, unknown, or violates a
        model invariant.
    """
    unknown = sorted(set(record) - set(ENVELOPE_FIELDS))
    if unknown:
        raise DeviceGeometryError(f"envelope: unknown fields {unknown!r}")
    return DeviceEnvelope(**{name: _number(record, name) for name in ENVELOPE_FIELDS})
