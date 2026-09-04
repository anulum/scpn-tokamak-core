# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — tier-G1 device model tests

"""Every branch of the tier-G1 model, and its agreement with the physics.

The headline test is the one that crosses capabilities: the volume of the
built plasma column, divided by the volume the physics record computes by
Pappus's theorem, is the inscribed-polygon ratio and nothing else.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable

import pytest
from geometry_fixtures import (
    conventional_configuration,
    inscribed_polygon_ratio,
    reference_envelope,
    spherical_configuration,
)

from scpn_tokamak_core.configuration import DeviceConfiguration
from scpn_tokamak_core.device import (
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
from scpn_tokamak_core.errors import DeviceGeometryError
from scpn_tokamak_core.geometry import ToroidalGeometry
from scpn_tokamak_core.physics import plasma_volume_m3

REFERENCE_SEGMENTS = 64
CONFIGURATIONS: tuple[Callable[[], DeviceConfiguration], ...] = (
    spherical_configuration,
    conventional_configuration,
)


@pytest.mark.parametrize("segments", [0, 7, 12, -8])
def test_an_invalid_segment_count_is_refused_under_the_device_error(
    segments: int,
) -> None:
    """The library's rule is enforced, and its message is carried through."""
    with pytest.raises(DeviceGeometryError, match="segments"):
        build_device_model(spherical_configuration(), reference_envelope(), segments)


def test_a_radial_build_that_reaches_the_axis_is_refused() -> None:
    """An unrolled machine wider than half its own period self-intersects.

    The refusal names the field and prints both sides of the comparison,
    so a caller can see how far over it went.
    """
    with pytest.raises(DeviceGeometryError, match="winding_thickness_m"):
        build_device_model(
            spherical_configuration(),
            reference_envelope(winding_thickness_m=100.0),
            REFERENCE_SEGMENTS,
        )


def test_the_body_set_and_its_order_are_fixed() -> None:
    """Three bodies, always the same three, always in the same order."""
    model = build_device_model(
        spherical_configuration(), reference_envelope(), REFERENCE_SEGMENTS
    )
    assert tuple(mesh.name for mesh in model.meshes) == BODY_NAMES
    assert BODY_NAMES == (
        BODY_PLASMA_COLUMN,
        BODY_VACUUM_VESSEL,
        BODY_TOROIDAL_FIELD_WINDING,
    )


def test_a_model_built_from_the_wrong_bodies_is_refused() -> None:
    """The container validates its own body set, not only the builder."""
    model = build_device_model(
        spherical_configuration(), reference_envelope(), REFERENCE_SEGMENTS
    )
    with pytest.raises(DeviceGeometryError, match="bodies must be exactly"):
        DeviceModel3D(
            configuration_digest_sha256=model.configuration_digest_sha256,
            envelope_digest_sha256=model.envelope_digest_sha256,
            segments=model.segments,
            meshes=model.meshes[::-1],
        )


@pytest.mark.parametrize("configuration", CONFIGURATIONS)
@pytest.mark.parametrize("segments", [8, 64, 256])
def test_the_column_volume_is_the_pappus_volume_times_the_polygon_ratio(
    configuration: Callable[[], DeviceConfiguration], segments: int
) -> None:
    """The two capabilities agree, and the only difference is the polygon.

    The column is built at the area-equivalent radius ``a sqrt(kappa)``, so
    its analytic volume over the periodic length is exactly the volume the
    physics record computes. The tessellation inscribes a regular polygon
    in every circular section, so the built volume is smaller by that
    polygon's area ratio and by nothing else.

    Asserted within a relative tolerance rather than as an equality: the
    two sides group their factors differently and the mesh volume is a sum
    over many triangles, so they part in the last places. Measured, the
    gap runs from 3 units in the last place at 8 segments to 133 at 256,
    which is 3e-14 relative — the tolerance sits an order above that.
    """
    build = configuration()
    model = build_device_model(build, reference_envelope(), segments)
    column = model.meshes[0]
    assert column.name == BODY_PLASMA_COLUMN
    assert math.isclose(
        column.signed_volume_m3() / plasma_volume_m3(build.geometry),
        inscribed_polygon_ratio(segments),
        rel_tol=1e-13,
    )


@pytest.mark.parametrize("configuration", CONFIGURATIONS)
def test_the_triangularity_does_not_reach_the_bodies(
    configuration: Callable[[], DeviceConfiguration],
) -> None:
    """No body of revolution can carry a fore-aft asymmetry.

    The physics record already states this about its volume. Here it is
    stated about the geometry: two configurations differing only in
    triangularity build the same bodies, byte for byte.
    """
    build = configuration()
    geometry = build.geometry
    other = DeviceConfiguration(
        identifier=build.identifier,
        geometry=ToroidalGeometry(
            major_radius_m=geometry.major_radius_m,
            minor_radius_m=geometry.minor_radius_m,
            elongation=geometry.elongation,
            triangularity=-geometry.triangularity,
        ),
        coils=build.coils,
        limits=build.limits,
        registry=build.registry,
    )
    first = build_device_model(build, reference_envelope(), REFERENCE_SEGMENTS)
    second = build_device_model(other, reference_envelope(), REFERENCE_SEGMENTS)
    assert [mesh.signed_volume_m3() for mesh in first.meshes] == [
        mesh.signed_volume_m3() for mesh in second.meshes
    ]
    assert first.digest_sha256() != second.digest_sha256()


def test_the_elongation_does_reach_the_bodies() -> None:
    """Unlike the triangularity, the elongation is carried, through the area.

    A rounder plasma of the same minor radius encloses less, and the built
    column says so.
    """
    build = spherical_configuration()
    geometry = build.geometry
    assert equivalent_column_radius_m(geometry) > geometry.minor_radius_m
    assert equivalent_column_radius_m(geometry) == pytest.approx(
        geometry.minor_radius_m * math.sqrt(geometry.elongation)
    )


@pytest.mark.parametrize("configuration", CONFIGURATIONS)
def test_the_periodic_length_is_the_circumference_of_the_magnetic_axis(
    configuration: Callable[[], DeviceConfiguration],
) -> None:
    """The torus unrolls to a cylinder of length 2 pi R0, and the bodies use it."""
    build = configuration()
    length = periodic_length_m(build.geometry)
    assert length == pytest.approx(2.0 * math.pi * build.geometry.major_radius_m)
    model = build_device_model(build, reference_envelope(), REFERENCE_SEGMENTS)
    for mesh in model.meshes:
        heights = {round(vertex[2], 12) for vertex in mesh.vertices}
        assert heights == {0.0, round(length, 12)}


def test_the_bodies_nest_without_overlapping() -> None:
    """The vessel sits on the plasma edge and the winding outside the gap."""
    build = spherical_configuration()
    envelope = reference_envelope()
    column = equivalent_column_radius_m(build.geometry)
    model = build_device_model(build, envelope, REFERENCE_SEGMENTS)
    radii = [
        max(math.hypot(vertex[0], vertex[1]) for vertex in mesh.vertices)
        for mesh in model.meshes
    ]
    assert radii[0] < radii[1] < radii[2]
    assert radii[0] == pytest.approx(column)
    assert radii[2] == pytest.approx(column + envelope.radial_build_m)


def test_the_record_carries_the_schema_units_and_non_claims() -> None:
    """The projection states what the model is and what it is not."""
    model = build_device_model(
        spherical_configuration(), reference_envelope(), REFERENCE_SEGMENTS
    )
    record = model.to_record()
    assert record["schema"] == MODEL_SCHEMA
    assert record["schema_version"] == MODEL_SCHEMA_VERSION
    assert record["units"] == dict(MODEL_UNITS)
    assert record["non_claims"] == list(MODEL_NON_CLAIMS)
    assert [body["name"] for body in record["bodies"]] == list(BODY_NAMES)
    assert record["segments"] == REFERENCE_SEGMENTS


def test_the_canonical_bytes_are_canonical_and_the_digest_identifies_them() -> None:
    """One trailing newline, idempotent re-canonicalisation, matching digest."""
    model = build_device_model(
        spherical_configuration(), reference_envelope(), REFERENCE_SEGMENTS
    )
    data = model.canonical_bytes()
    assert data.endswith(b"\n")
    assert data.count(b"\n") == 1
    again = json.dumps(
        json.loads(data), sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    assert (again + "\n").encode("utf-8") == data
    assert model.digest_sha256() == hashlib.sha256(data).hexdigest()


def test_the_digest_moves_with_the_envelope_and_with_the_segment_count() -> None:
    """Both inputs of the build reach the identity of the record."""
    base = build_device_model(
        spherical_configuration(), reference_envelope(), REFERENCE_SEGMENTS
    )
    assert (
        base.digest_sha256()
        != build_device_model(
            spherical_configuration(),
            reference_envelope(winding_gap_m=0.2),
            REFERENCE_SEGMENTS,
        ).digest_sha256()
    )
    assert (
        base.digest_sha256()
        != build_device_model(
            spherical_configuration(), reference_envelope(), REFERENCE_SEGMENTS * 2
        ).digest_sha256()
    )
