# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — device configuration container tests

"""Every branch of the device configuration container and its parsers.

All parameter sets in this module are synthetic fixtures; none describes
any real machine.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest

from scpn_tokamak_core.coils import CoilSystem
from scpn_tokamak_core.configuration import (
    DeviceConfiguration,
    RegistryBinding,
    configuration_from_bytes,
    configuration_from_record,
)
from scpn_tokamak_core.errors import DeviceConfigurationError
from scpn_tokamak_core.geometry import ToroidalGeometry
from scpn_tokamak_core.limits import OperationalLimits

REGISTRY = RegistryBinding(version="1.0.0", digest_sha256="0" * 64)


def synthetic_conventional() -> DeviceConfiguration:
    """Build a valid synthetic conventional-tokamak configuration."""
    return DeviceConfiguration(
        identifier="conventional_tokamak",
        geometry=ToroidalGeometry(
            major_radius_m=3.0,
            minor_radius_m=1.0,
            elongation=1.6,
            triangularity=0.3,
        ),
        coils=CoilSystem(
            toroidal_field_coil_count=12,
            poloidal_field_coil_count=6,
            has_central_solenoid=True,
        ),
        limits=OperationalLimits(
            toroidal_field_t=4.0,
            plasma_current_ma=5.0,
            safety_factor_floor=2.0,
            greenwald_fraction=0.8,
            flat_top_duration_s=10.0,
        ),
        registry=REGISTRY,
    )


def synthetic_spherical(safety_factor_floor: float = 1.5) -> DeviceConfiguration:
    """Build a valid synthetic spherical-tokamak configuration."""
    return DeviceConfiguration(
        identifier="spherical_tokamak",
        geometry=ToroidalGeometry(
            major_radius_m=1.5,
            minor_radius_m=1.0,
            elongation=2.2,
            triangularity=0.4,
        ),
        coils=CoilSystem(
            toroidal_field_coil_count=8,
            poloidal_field_coil_count=4,
            has_central_solenoid=False,
        ),
        limits=OperationalLimits(
            toroidal_field_t=1.0,
            plasma_current_ma=5.0,
            safety_factor_floor=safety_factor_floor,
            greenwald_fraction=0.85,
            flat_top_duration_s=5.0,
        ),
        registry=REGISTRY,
    )


def test_registry_binding_rejects_bad_pins() -> None:
    """Malformed registry pins are rejected."""
    with pytest.raises(DeviceConfigurationError, match=r"registry\.version"):
        RegistryBinding(version="", digest_sha256="0" * 64)
    with pytest.raises(DeviceConfigurationError, match=r"registry\.digest_sha256"):
        RegistryBinding(version="1.0.0", digest_sha256="ZZ")


def test_unowned_identifier_is_rejected() -> None:
    """Identifiers outside this repository's ownership are rejected."""
    with pytest.raises(DeviceConfigurationError, match="not owned"):
        DeviceConfiguration(
            identifier="stellarator",
            geometry=synthetic_conventional().geometry,
            coils=synthetic_conventional().coils,
            limits=synthetic_conventional().limits,
            registry=REGISTRY,
        )


def test_spherical_identifier_rejects_high_aspect_ratio() -> None:
    """A spherical identifier with conventional aspect ratio is refused."""
    with pytest.raises(DeviceConfigurationError, match="spherical_tokamak requires"):
        DeviceConfiguration(
            identifier="spherical_tokamak",
            geometry=synthetic_conventional().geometry,
            coils=synthetic_conventional().coils,
            limits=synthetic_conventional().limits,
            registry=REGISTRY,
        )


def test_conventional_identifier_rejects_low_aspect_ratio() -> None:
    """A conventional identifier with spherical aspect ratio is refused."""
    with pytest.raises(DeviceConfigurationError, match="conventional_tokamak requires"):
        DeviceConfiguration(
            identifier="conventional_tokamak",
            geometry=synthetic_spherical().geometry,
            coils=synthetic_spherical().coils,
            limits=synthetic_spherical().limits,
            registry=REGISTRY,
        )


def test_consistency_report_clean_and_finding() -> None:
    """The report is empty when consistent and precise when not."""
    assert synthetic_conventional().consistency_report() == ()
    findings = synthetic_spherical(safety_factor_floor=2.0).consistency_report()
    assert len(findings) == 1
    assert findings[0].field == "limits.safety_factor_floor"
    assert "below the declared floor" in findings[0].message


def test_canonical_round_trip_and_digest() -> None:
    """Canonical bytes round-trip losslessly and digest deterministically."""
    configuration = synthetic_conventional()
    data = configuration.canonical_bytes()
    assert data.endswith(b"\n")
    restored = configuration_from_bytes(data)
    assert restored == configuration
    expected = hashlib.sha256(data).hexdigest()
    assert configuration.digest_sha256() == expected


def test_from_record_round_trip_both_classes() -> None:
    """Both owned configuration classes round-trip through records."""
    for configuration in (synthetic_conventional(), synthetic_spherical()):
        assert configuration_from_record(configuration.to_record()) == configuration


@pytest.mark.parametrize(
    ("mutate", "fragment"),
    [
        (lambda _: "not-a-dict", "record: must be an object"),
        (lambda r: {**r, "extra": 1}, "unknown fields"),
        (lambda r: {**r, "geometry": None}, "geometry: must be an object"),
        (lambda r: {**r, "coils": []}, "coils: must be an object"),
        (lambda r: {**r, "limits": "x"}, "limits: must be an object"),
        (lambda r: {**r, "registry": 7}, "registry: must be an object"),
        (lambda r: {**r, "identifier": 3}, "identifier: must be a string"),
    ],
)
def test_from_record_shape_violations(mutate: Any, fragment: str) -> None:
    """Each record-shape violation is rejected with a precise message."""
    record = synthetic_conventional().to_record()
    with pytest.raises(DeviceConfigurationError, match=fragment):
        configuration_from_record(mutate(record))


def test_from_record_field_type_violations() -> None:
    """Nested field-type violations name the offending field."""
    record = synthetic_conventional().to_record()
    record["geometry"]["major_radius_m"] = "big"
    with pytest.raises(DeviceConfigurationError, match="major_radius_m: must be"):
        configuration_from_record(record)
    record = synthetic_conventional().to_record()
    record["geometry"]["major_radius_m"] = True
    with pytest.raises(DeviceConfigurationError, match="major_radius_m: must be"):
        configuration_from_record(record)
    record = synthetic_conventional().to_record()
    record["coils"]["toroidal_field_coil_count"] = 1.5
    with pytest.raises(
        DeviceConfigurationError, match="toroidal_field_coil_count: must be"
    ):
        configuration_from_record(record)
    record = synthetic_conventional().to_record()
    record["coils"]["toroidal_field_coil_count"] = True
    with pytest.raises(
        DeviceConfigurationError, match="toroidal_field_coil_count: must be"
    ):
        configuration_from_record(record)
    record = synthetic_conventional().to_record()
    record["coils"]["has_central_solenoid"] = "yes"
    with pytest.raises(DeviceConfigurationError, match="has_central_solenoid: must be"):
        configuration_from_record(record)
    record = synthetic_conventional().to_record()
    record["registry"]["version"] = None
    with pytest.raises(DeviceConfigurationError, match="version: must be a string"):
        configuration_from_record(record)


def test_from_bytes_rejects_invalid_documents() -> None:
    """Invalid UTF-8, invalid JSON, and non-finite literals are rejected."""
    with pytest.raises(DeviceConfigurationError, match="invalid JSON document"):
        configuration_from_bytes(b"\xff\xfe")
    with pytest.raises(DeviceConfigurationError, match="invalid JSON document"):
        configuration_from_bytes(b"{not json")
    record = synthetic_conventional().to_record()
    text = json.dumps(record).replace("3.0", "NaN", 1)
    with pytest.raises(DeviceConfigurationError, match="non-finite JSON literal"):
        configuration_from_bytes(text.encode("utf-8"))


def test_integer_accepted_where_number_expected() -> None:
    """Integral JSON numbers are accepted for real-valued fields."""
    record = synthetic_conventional().to_record()
    record["geometry"]["major_radius_m"] = 3
    restored = configuration_from_record(record)
    assert restored.geometry.major_radius_m == 3.0
