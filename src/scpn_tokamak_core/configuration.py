# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — device configuration container

"""Device configuration container bound to the SPO reactor registry.

A :class:`DeviceConfiguration` composes validated geometry, coil topology,
and operational limits under exactly one of the two registry identifiers
this repository owns. The spherical/conventional split follows the
low-aspect-ratio convention ``A <= 2`` for spherical tokamaks
(Y-K. M. Peng, D. J. Strickler, Nucl. Fusion 26 (1986) 769); an
identifier that contradicts the aspect ratio is rejected. Serialisation
is canonical (sorted keys, no NaN or infinity accepted anywhere) and the
SHA-256 digest of those bytes identifies the exact parameter set. The
registry binding is a data pin only — this package never imports SCPN
Phase Orchestrator code.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Final

from scpn_tokamak_core.coils import CoilSystem
from scpn_tokamak_core.errors import DeviceConfigurationError
from scpn_tokamak_core.geometry import ToroidalGeometry
from scpn_tokamak_core.limits import OperationalLimits

OWNED_CONFIGURATIONS: Final = ("conventional_tokamak", "spherical_tokamak")
SPHERICAL_MAX_ASPECT_RATIO: Final = 2.0
HEX_DIGEST: Final = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class RegistryBinding:
    """Pin to one SPO reactor registry release.

    Parameters
    ----------
    version
        Registry release version; non-empty.
    digest_sha256
        Registry digest as 64 lowercase hexadecimal characters.

    Raises
    ------
    DeviceConfigurationError
        If either pin component is malformed.
    """

    version: str
    digest_sha256: str

    def __post_init__(self) -> None:
        """Validate the registry pin.

        Raises
        ------
        DeviceConfigurationError
            If either pin component is malformed.
        """
        if not self.version:
            raise DeviceConfigurationError("registry.version: must be non-empty")
        if HEX_DIGEST.fullmatch(self.digest_sha256) is None:
            raise DeviceConfigurationError(
                "registry.digest_sha256: must be 64 lowercase hexadecimal "
                f"characters, got {self.digest_sha256!r}"
            )


@dataclass(frozen=True, slots=True)
class ConsistencyFinding:
    """One internal-consistency finding on a device configuration.

    Parameters
    ----------
    field
        Dotted field path the finding refers to.
    message
        Human-readable statement of the inconsistency.
    """

    field: str
    message: str


@dataclass(frozen=True, slots=True)
class DeviceConfiguration:
    """Validated tokamak device configuration.

    Parameters
    ----------
    identifier
        SPO registry configuration identifier; one of
        ``conventional_tokamak`` or ``spherical_tokamak``.
    geometry
        Validated toroidal geometry.
    coils
        Validated coil-system topology.
    limits
        Validated operational limits.
    registry
        Pin to the SPO reactor registry release the identifier belongs
        to.

    Raises
    ------
    DeviceConfigurationError
        If the identifier is not owned by this repository or contradicts
        the aspect-ratio convention of its class.
    """

    identifier: str
    geometry: ToroidalGeometry
    coils: CoilSystem
    limits: OperationalLimits
    registry: RegistryBinding

    def __post_init__(self) -> None:
        """Validate identifier ownership and aspect-ratio class.

        Raises
        ------
        DeviceConfigurationError
            If the identifier is not owned by this repository or
            contradicts the aspect-ratio convention of its class.
        """
        if self.identifier not in OWNED_CONFIGURATIONS:
            raise DeviceConfigurationError(
                f"identifier: {self.identifier!r} is not owned by "
                f"SCPN-TOKAMAK-CORE; owned: {OWNED_CONFIGURATIONS!r}"
            )
        aspect_ratio = self.geometry.aspect_ratio
        if (
            self.identifier == "spherical_tokamak"
            and aspect_ratio > SPHERICAL_MAX_ASPECT_RATIO
        ):
            raise DeviceConfigurationError(
                "identifier: spherical_tokamak requires aspect ratio "
                f"<= {SPHERICAL_MAX_ASPECT_RATIO}, got {aspect_ratio!r}"
            )
        if (
            self.identifier == "conventional_tokamak"
            and aspect_ratio <= SPHERICAL_MAX_ASPECT_RATIO
        ):
            raise DeviceConfigurationError(
                "identifier: conventional_tokamak requires aspect ratio "
                f"> {SPHERICAL_MAX_ASPECT_RATIO}, got {aspect_ratio!r}"
            )

    def consistency_report(self) -> tuple[ConsistencyFinding, ...]:
        """Report physics-consistency findings without failing.

        Returns
        -------
        tuple of ConsistencyFinding
            Findings from the documented estimates; empty when the
            declared operating point is internally consistent. Findings
            are advisory instruments, not machine claims.
        """
        findings: list[ConsistencyFinding] = []
        q_cyl = self.limits.cylindrical_safety_factor(self.geometry)
        if q_cyl < self.limits.safety_factor_floor:
            findings.append(
                ConsistencyFinding(
                    field="limits.safety_factor_floor",
                    message=(
                        f"cylindrical safety-factor estimate {q_cyl:.3f} is "
                        "below the declared floor "
                        f"{self.limits.safety_factor_floor:.3f}"
                    ),
                )
            )
        return tuple(findings)

    def to_record(self) -> dict[str, Any]:
        """Project the configuration to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Nested record with every declared parameter.
        """
        return {
            "identifier": self.identifier,
            "geometry": {
                "major_radius_m": self.geometry.major_radius_m,
                "minor_radius_m": self.geometry.minor_radius_m,
                "elongation": self.geometry.elongation,
                "triangularity": self.geometry.triangularity,
            },
            "coils": {
                "toroidal_field_coil_count": (self.coils.toroidal_field_coil_count),
                "poloidal_field_coil_count": (self.coils.poloidal_field_coil_count),
                "has_central_solenoid": self.coils.has_central_solenoid,
            },
            "limits": {
                "toroidal_field_t": self.limits.toroidal_field_t,
                "plasma_current_ma": self.limits.plasma_current_ma,
                "safety_factor_floor": self.limits.safety_factor_floor,
                "greenwald_fraction": self.limits.greenwald_fraction,
                "flat_top_duration_s": self.limits.flat_top_duration_s,
            },
            "registry": {
                "version": self.registry.version,
                "digest_sha256": self.registry.digest_sha256,
            },
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the configuration canonically.

        Returns
        -------
        bytes
            UTF-8 JSON with sorted keys, minimal separators, and a
            trailing newline; NaN and infinity are never emitted.
        """
        text = json.dumps(
            self.to_record(),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return (text + "\n").encode("utf-8")

    def digest_sha256(self) -> str:
        """Identify the exact parameter set.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _require_mapping(record: dict[str, Any], field: str) -> dict[str, Any]:
    """Return one required mapping field of a record.

    Parameters
    ----------
    record
        Parent mapping under inspection.
    field
        Key that must hold a mapping.

    Returns
    -------
    dict[str, Any]
        The nested mapping.

    Raises
    ------
    DeviceConfigurationError
        If the field is missing or not a mapping.
    """
    value = record.get(field)
    if not isinstance(value, dict):
        raise DeviceConfigurationError(f"{field}: must be an object")
    return value


def _number(record: dict[str, Any], field: str) -> float:
    """Return one required real-number field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold a real number.

    Returns
    -------
    float
        The numeric value; booleans are rejected.

    Raises
    ------
    DeviceConfigurationError
        If the field is missing or not a real number.
    """
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise DeviceConfigurationError(f"{field}: must be a number, got {value!r}")
    return float(value)


def _integer(record: dict[str, Any], field: str) -> int:
    """Return one required integer field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold an integer.

    Returns
    -------
    int
        The integer value; booleans are rejected.

    Raises
    ------
    DeviceConfigurationError
        If the field is missing or not an integer.
    """
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise DeviceConfigurationError(f"{field}: must be an integer, got {value!r}")
    return value


def _boolean(record: dict[str, Any], field: str) -> bool:
    """Return one required boolean field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold a boolean.

    Returns
    -------
    bool
        The boolean value.

    Raises
    ------
    DeviceConfigurationError
        If the field is missing or not a boolean.
    """
    value = record.get(field)
    if not isinstance(value, bool):
        raise DeviceConfigurationError(f"{field}: must be a boolean, got {value!r}")
    return value


def _string(record: dict[str, Any], field: str) -> str:
    """Return one required string field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold a string.

    Returns
    -------
    str
        The string value.

    Raises
    ------
    DeviceConfigurationError
        If the field is missing or not a string.
    """
    value = record.get(field)
    if not isinstance(value, str):
        raise DeviceConfigurationError(f"{field}: must be a string, got {value!r}")
    return value


def configuration_from_record(record: Any) -> DeviceConfiguration:
    """Build a validated configuration from a decoded record.

    Parameters
    ----------
    record
        Decoded JSON object in the shape produced by
        :meth:`DeviceConfiguration.to_record`.

    Returns
    -------
    DeviceConfiguration
        The fully validated configuration.

    Raises
    ------
    DeviceConfigurationError
        If the record shape or any value violates the model.
    """
    if not isinstance(record, dict):
        raise DeviceConfigurationError("record: must be an object")
    known = {"identifier", "geometry", "coils", "limits", "registry"}
    unknown = sorted(set(record) - known)
    if unknown:
        raise DeviceConfigurationError(f"record: unknown fields {unknown!r}")
    geometry = _require_mapping(record, "geometry")
    coils = _require_mapping(record, "coils")
    limits = _require_mapping(record, "limits")
    registry = _require_mapping(record, "registry")
    return DeviceConfiguration(
        identifier=_string(record, "identifier"),
        geometry=ToroidalGeometry(
            major_radius_m=_number(geometry, "major_radius_m"),
            minor_radius_m=_number(geometry, "minor_radius_m"),
            elongation=_number(geometry, "elongation"),
            triangularity=_number(geometry, "triangularity"),
        ),
        coils=CoilSystem(
            toroidal_field_coil_count=_integer(coils, "toroidal_field_coil_count"),
            poloidal_field_coil_count=_integer(coils, "poloidal_field_coil_count"),
            has_central_solenoid=_boolean(coils, "has_central_solenoid"),
        ),
        limits=OperationalLimits(
            toroidal_field_t=_number(limits, "toroidal_field_t"),
            plasma_current_ma=_number(limits, "plasma_current_ma"),
            safety_factor_floor=_number(limits, "safety_factor_floor"),
            greenwald_fraction=_number(limits, "greenwald_fraction"),
            flat_top_duration_s=_number(limits, "flat_top_duration_s"),
        ),
        registry=RegistryBinding(
            version=_string(registry, "version"),
            digest_sha256=_string(registry, "digest_sha256"),
        ),
    )


def configuration_from_bytes(data: bytes) -> DeviceConfiguration:
    """Build a validated configuration from canonical JSON bytes.

    Parameters
    ----------
    data
        UTF-8 JSON document; NaN and infinity literals are rejected.

    Returns
    -------
    DeviceConfiguration
        The fully validated configuration.

    Raises
    ------
    DeviceConfigurationError
        If the document is not valid strict JSON or violates the model.
    """

    def _reject_constant(literal: str) -> float:
        raise DeviceConfigurationError(
            f"record: non-finite JSON literal {literal!r} is rejected"
        )

    try:
        record = json.loads(data.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeviceConfigurationError(f"record: invalid JSON document: {exc}") from exc
    return configuration_from_record(record)
