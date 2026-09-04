# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — tier-G2 device model tests

"""Every branch of the tier-G2 model, and what sets its faceting.

The builds are cached: each costs a second or three, and rebuilding one
per test buys no evidence a single build does not already carry.
"""

from __future__ import annotations

import functools
import hashlib
import json
from collections.abc import Callable

import pytest
from geometry_fixtures import (
    conventional_configuration,
    reference_envelope,
    spherical_configuration,
)

from scpn_tokamak_core.device import (
    BODY_NAMES,
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
from scpn_tokamak_core.errors import DeviceGeometryError

#: Relative agreement the three bodies' faceting deficits hold to. They are
#: not bit-equal — measured, they part around the ninth significant figure.
DEFICIT_AGREEMENT = 1e-7


@functools.cache
def spherical_model() -> DeviceModelCAD:
    """Build and cache the spherical-torus B-rep model."""
    return build_device_cad(spherical_configuration(), reference_envelope())


@functools.cache
def conventional_model() -> DeviceModelCAD:
    """Build and cache the conventional-aspect B-rep model."""
    return build_device_cad(conventional_configuration(), reference_envelope())


def deficits(model: DeviceModelCAD) -> list[float]:
    """Return each body's relative faceted-volume deficit."""
    return [
        body.to_record()["faceted_volume_relative_deficit"] for body in model.bodies
    ]


def bounds(model: DeviceModelCAD) -> list[float]:
    """Return each body's declared faceted-volume deficit bound."""
    return [body.to_record()["faceted_volume_deficit_bound"] for body in model.bodies]


def test_the_body_set_and_its_order_are_fixed() -> None:
    """The same three bodies as tier G1, in the same order."""
    assert tuple(body.name for body in spherical_model().bodies) == BODY_NAMES


@pytest.mark.parametrize("model", [spherical_model, conventional_model])
def test_every_body_stays_inside_its_declared_bound(
    model: Callable[[], DeviceModelCAD],
) -> None:
    """The evidence kernel checked each body, and each passed with margin.

    The margins are measured rather than asserted tightly: the narrowest is
    at the conventional regime's winding, and it is still nearly five
    times.
    """
    built = model()
    for deficit, bound in zip(deficits(built), bounds(built), strict=True):
        assert 0.0 < deficit < bound
        assert bound / deficit > 4.0


def test_the_faceting_deficit_does_not_depend_on_the_radius() -> None:
    """One angular step is used everywhere, so one deficit appears everywhere.

    The three bodies differ in radius by tens of per cent and the two
    regimes by a factor of nearly two, yet every deficit agrees to about
    nine significant figures. That is the signature of an angular
    criterion: the mesher divides each circle into the same number of
    segments whatever its radius, so the relative area lost is the same.
    """
    every = deficits(spherical_model()) + deficits(conventional_model())
    for value in every[1:]:
        assert value == pytest.approx(every[0], rel=DEFICIT_AGREEMENT)
    assert len(set(every)) > 1


def test_a_finer_linear_deflection_is_refused_rather_than_helping() -> None:
    """The linear deflection sets the bound here, not the tessellation.

    This is the trap this family sits in and the magneto-inertial families
    do not. The declared bound is ``2 d / r``; on a device whose radii are
    metres rather than millimetres that is already tighter than what the
    mesher delivers, and the angular criterion is what binds. So making the
    linear deflection ten times finer tightens the bound tenfold, leaves
    the faceting untouched, and turns a passing model into a refusal.

    The refusal is the assertion. A tier that had copied a sibling's
    deflection without measuring would have discovered this in CI or not at
    all.
    """
    with pytest.raises(DeviceGeometryError, match="faceted_volume_relative_deficit"):
        build_device_cad(
            spherical_configuration(),
            reference_envelope(),
            linear_deflection_m=DEFAULT_LINEAR_DEFLECTION_M / 10.0,
        )


def test_a_coarser_angular_deflection_is_what_actually_loosens_the_faceting() -> None:
    """Halving the angular deflection quarters the deficit.

    The deficit of an inscribed polygon falls as the square of its angular
    step, so this is the relation to expect, and it is what separates the
    criterion that binds from the one that does not.
    """
    fine = build_device_cad(
        spherical_configuration(),
        reference_envelope(),
        angular_deflection_rad=DEFAULT_ANGULAR_DEFLECTION_RAD / 2.0,
    )
    ratio = deficits(spherical_model())[0] / deficits(fine)[0]
    assert ratio == pytest.approx(4.0, rel=0.02)


def test_a_manifest_of_the_wrong_shape_is_refused() -> None:
    """The container validates the manifest it was handed, not only the build."""
    built = spherical_model()
    for broken, match in (
        ({**built.assembly_manifest, "schema": "wrong"}, "assembly_manifest.schema"),
        ({**built.assembly_manifest, "body_count": 2}, "body_count"),
    ):
        with pytest.raises(DeviceGeometryError, match=match):
            DeviceModelCAD(
                configuration_digest_sha256=built.configuration_digest_sha256,
                envelope_digest_sha256=built.envelope_digest_sha256,
                reference_mesh_segments=built.reference_mesh_segments,
                linear_deflection_m=built.linear_deflection_m,
                angular_deflection_rad=built.angular_deflection_rad,
                backend_versions=built.backend_versions,
                assembly_manifest=broken,
                step_sha256=built.step_sha256,
                bodies=built.bodies,
                step_data=built.step_data,
                faceted_meshes=built.faceted_meshes,
            )


def test_bodies_out_of_order_are_refused() -> None:
    """The fixed order is enforced on the container as well as the builder."""
    built = spherical_model()
    with pytest.raises(DeviceGeometryError, match="must be exactly"):
        DeviceModelCAD(
            configuration_digest_sha256=built.configuration_digest_sha256,
            envelope_digest_sha256=built.envelope_digest_sha256,
            reference_mesh_segments=built.reference_mesh_segments,
            linear_deflection_m=built.linear_deflection_m,
            angular_deflection_rad=built.angular_deflection_rad,
            backend_versions=built.backend_versions,
            assembly_manifest=built.assembly_manifest,
            step_sha256=built.step_sha256,
            bodies=built.bodies[::-1],
            step_data=built.step_data,
            faceted_meshes=built.faceted_meshes,
        )


def test_the_step_export_is_present_and_its_digest_matches_its_bytes() -> None:
    """The digest names the exact bytes the model carries."""
    built = spherical_model()
    assert built.step_data.startswith(b"ISO-10303-21;")
    assert built.step_sha256 == hashlib.sha256(built.step_data).hexdigest()


def test_two_regimes_produce_different_step_bytes() -> None:
    """The export carries the design, not a template."""
    assert spherical_model().step_sha256 != conventional_model().step_sha256


def test_the_record_carries_the_schema_units_and_non_claims() -> None:
    """The projection states what the model is and what it is not."""
    record = spherical_model().to_record()
    assert record["schema"] == CAD_MODEL_SCHEMA
    assert record["schema_version"] == CAD_MODEL_SCHEMA_VERSION
    assert record["units"] == dict(CAD_MODEL_UNITS)
    assert record["non_claims"] == list(CAD_MODEL_NON_CLAIMS)
    assert record["reference_mesh_segments"] == DEFAULT_REFERENCE_MESH_SEGMENTS
    assert record["linear_deflection_m"] == DEFAULT_LINEAR_DEFLECTION_M
    assert record["angular_deflection_rad"] == DEFAULT_ANGULAR_DEFLECTION_RAD
    assert [body["name"] for body in record["bodies"]] == list(BODY_NAMES)
    assert record["backend_versions"]


def test_the_canonical_bytes_are_canonical_and_the_digest_identifies_them() -> None:
    """One trailing newline, idempotent re-canonicalisation, matching digest."""
    built = spherical_model()
    data = built.canonical_bytes()
    assert data.endswith(b"\n")
    assert data.count(b"\n") == 1
    again = json.dumps(
        json.loads(data), sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    assert (again + "\n").encode("utf-8") == data
    assert built.digest_sha256() == hashlib.sha256(data).hexdigest()


def test_the_two_tiers_are_bound_to_the_same_inputs() -> None:
    """Both tiers name the configuration and the envelope they were built from."""
    built = spherical_model()
    configuration = spherical_configuration()
    assert built.configuration_digest_sha256 == configuration.digest_sha256()
    assert built.envelope_digest_sha256 == reference_envelope().digest_sha256()
