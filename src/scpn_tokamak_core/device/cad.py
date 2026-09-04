# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — tier-G2 device model

"""Tier-G2 B-rep model of the cylindrical periodic equivalent.

The same three bodies as tier G1, built as exact solids through the
shared library's ``cad`` group instead of tessellated, with every body
checked fail-closed by the library's evidence kernel against its analytic
closed forms and against its tier-G1 twin, and exported as normalised
STEP bytes with a digest.

Every body is a cylinder or an annular tube, so each has a well-defined
smallest circular radius and the faceting deficit bound needs no special
case here.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from scpn_reactor_kernels.cad import (
    MANIFEST_SCHEMA,
    BodyEvidence,
    BrepAssembly,
    annular_tube_brep,
    assembly_evidence,
    backend_versions,
    cylinder_solid_brep,
    facet_assembly,
    step_bytes,
    step_sha256,
)
from scpn_reactor_kernels.errors import CadError, GeometryError
from scpn_reactor_kernels.geometry import TriangleMesh

from scpn_tokamak_core.configuration import DeviceConfiguration
from scpn_tokamak_core.device.envelope import DeviceEnvelope
from scpn_tokamak_core.device.model import (
    BODY_NAMES,
    BODY_PLASMA_COLUMN,
    BODY_TOROIDAL_FIELD_WINDING,
    BODY_VACUUM_VESSEL,
    MATERIAL_COIL_CONDUCTOR,
    MATERIAL_PLASMA,
    MATERIAL_VESSEL_WALL,
    ROLE_COIL,
    ROLE_PLASMA,
    ROLE_VACUUM_BOUNDARY,
    build_device_model,
    equivalent_column_radius_m,
    periodic_length_m,
)
from scpn_tokamak_core.errors import DeviceGeometryError

CAD_MODEL_SCHEMA: Final = "scpn.tokamak-cad-model.v1"
CAD_MODEL_SCHEMA_VERSION: Final = "1.0.0"
CAD_MODEL_UNITS: Final = {
    "length": "metre",
    "handedness": "right",
    "axis": "z along the axis of the cylindrical periodic equivalent",
    "origin": "z = 0 at one end of the periodic length 2 pi R0",
}
CAD_MODEL_NON_CLAIMS: Final = (
    "exact solids of revolution of a synthetic configuration and envelope",
    (
        "the cylindrical periodic equivalent of the toroidal device is "
        "modelled: the toroidal curvature is not, so nothing here "
        "distinguishes the inboard side of a torus from the outboard one"
    ),
    (
        "the plasma column carries the elongation through an area-equivalent "
        "radius and cannot carry the triangularity"
    ),
    (
        "the toroidal-field winding is one tube of declared size; no coil, "
        "turn count, circuit, ripple or field map is modelled, and the "
        "poloidal field coils are absent"
    ),
    (
        "determinism of the STEP bytes is claimed within one pinned back-end "
        "environment only, never across back-end versions"
    ),
    "no body is an engineering model and no fabrication tolerance is carried",
    "no value describes or validates any real machine",
)

#: Reference tessellation the B-rep bodies are checked against.
DEFAULT_REFERENCE_MESH_SEGMENTS: Final = 8
#: Mesher deflections of the faceting comparison, both set by measurement.
#:
#: On this family it is the **angular** deflection that binds, not the
#: linear one, and that is the opposite of the magneto-inertial families.
#: The declared bound is ``2 d / r``; with radii of metres rather than
#: millimetres it is already tighter than what the mesher delivers, so the
#: linear deflection sets the bound and the angular criterion sets the
#: tessellation. Measured: across a tenfold change in the linear deflection
#: the deficit did not move at all, while halving the angular deflection
#: quartered it. The group's convention of tuning the linear deflection
#: would have tightened the bound without improving the faceting and turned
#: a sound model into a refusal.
#:
#: At 0.02 rad every body of both anchored regimes clears its bound by
#: between five and nine times, and a build costs about a second; 0.01 rad
#: buys another factor of four for three times the cost, which no test
#: here needs.
DEFAULT_LINEAR_DEFLECTION_M: Final = 1.0e-4
DEFAULT_ANGULAR_DEFLECTION_RAD: Final = 0.02


@dataclass(frozen=True, slots=True)
class DeviceModelCAD:
    """The B-rep device model of one configuration and envelope.

    Parameters
    ----------
    configuration_digest_sha256, envelope_digest_sha256
        Digests of the inputs the model was built from.
    reference_mesh_segments
        Tier-G1 reference the bodies were checked against.
    linear_deflection_m, angular_deflection_rad
        Mesher deflections of the faceting comparison.
    backend_versions
        Versions of the pinned back-ends that produced the solids.
    assembly_manifest
        The library's assembly manifest of the three bodies.
    step_sha256
        Digest of the normalised STEP bytes.
    bodies
        Checked evidence of each body, in the fixed order.
    step_data
        The normalised STEP bytes themselves.
    faceted_meshes
        The faceted meshes the evidence was computed from.

    Raises
    ------
    DeviceGeometryError
        If the manifest schema, the body count or the body order is wrong.
    """

    configuration_digest_sha256: str
    envelope_digest_sha256: str
    reference_mesh_segments: int
    linear_deflection_m: float
    angular_deflection_rad: float
    backend_versions: dict[str, str]
    assembly_manifest: dict[str, Any]
    step_sha256: str
    bodies: tuple[BodyEvidence, ...]
    step_data: bytes
    faceted_meshes: tuple[TriangleMesh, ...]

    def __post_init__(self) -> None:
        """Validate the manifest and the body set.

        Raises
        ------
        DeviceGeometryError
            If the manifest schema, the body count or the body order is
            wrong.
        """
        if self.assembly_manifest.get("schema") != MANIFEST_SCHEMA:
            raise DeviceGeometryError(
                f"assembly_manifest.schema: must be {MANIFEST_SCHEMA!r}"
            )
        if self.assembly_manifest.get("body_count") != len(BODY_NAMES):
            raise DeviceGeometryError(
                f"assembly_manifest.body_count: must be {len(BODY_NAMES)}, got "
                f"{self.assembly_manifest.get('body_count')!r}"
            )
        names = tuple(body.name for body in self.bodies)
        if names != BODY_NAMES:
            raise DeviceGeometryError(
                f"bodies: must be exactly {BODY_NAMES!r} in order, got {names!r}"
            )

    def to_record(self) -> dict[str, Any]:
        """Project the model to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            The schema-tagged record with one entry per body.
        """
        return {
            "schema": CAD_MODEL_SCHEMA,
            "schema_version": CAD_MODEL_SCHEMA_VERSION,
            "units": dict(CAD_MODEL_UNITS),
            "non_claims": list(CAD_MODEL_NON_CLAIMS),
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "envelope_digest_sha256": self.envelope_digest_sha256,
            "reference_mesh_segments": self.reference_mesh_segments,
            "linear_deflection_m": self.linear_deflection_m,
            "angular_deflection_rad": self.angular_deflection_rad,
            "backend_versions": dict(self.backend_versions),
            "assembly_manifest": self.assembly_manifest,
            "step_sha256": self.step_sha256,
            "bodies": [body.to_record() for body in self.bodies],
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the model record canonically.

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
        """Identify the exact model record.

        Returns
        -------
        str
            SHA-256 of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def build_device_cad(
    configuration: DeviceConfiguration,
    envelope: DeviceEnvelope,
    segments: int = DEFAULT_REFERENCE_MESH_SEGMENTS,
    linear_deflection_m: float = DEFAULT_LINEAR_DEFLECTION_M,
    angular_deflection_rad: float = DEFAULT_ANGULAR_DEFLECTION_RAD,
) -> DeviceModelCAD:
    """Build the B-rep device model of a validated design.

    Parameters
    ----------
    configuration
        Validated tokamak configuration.
    envelope
        Validated mechanical envelope.
    segments
        Segment count of the tier-G1 reference mesh of the comparison.
    linear_deflection_m, angular_deflection_rad
        Mesher deflections of the faceting comparison.

    Returns
    -------
    DeviceModelCAD
        The composed, fail-closed checked model with its STEP export.

    Raises
    ------
    DeviceGeometryError
        If a count or a deflection is invalid, if the configuration and
        the envelope do not fit together, or if a body violates a declared
        evidence bound; the library's refusals are re-raised under the
        device error type with their messages.
        :class:`~scpn_reactor_kernels.errors.CadUnavailableError` if the
        optional CAD back-end is absent.
    """
    reference = build_device_model(configuration, envelope, segments)
    geometry = configuration.geometry
    column = equivalent_column_radius_m(geometry)
    length = periodic_length_m(geometry)
    vessel_outer = column + envelope.vessel_wall_thickness_m
    winding_inner = vessel_outer + envelope.winding_gap_m
    winding_outer = winding_inner + envelope.winding_thickness_m
    try:
        assembly = BrepAssembly(
            (
                cylinder_solid_brep(
                    column,
                    0.0,
                    length,
                    BODY_PLASMA_COLUMN,
                    ROLE_PLASMA,
                    MATERIAL_PLASMA,
                ),
                annular_tube_brep(
                    column,
                    vessel_outer,
                    0.0,
                    length,
                    BODY_VACUUM_VESSEL,
                    ROLE_VACUUM_BOUNDARY,
                    MATERIAL_VESSEL_WALL,
                ),
                annular_tube_brep(
                    winding_inner,
                    winding_outer,
                    0.0,
                    length,
                    BODY_TOROIDAL_FIELD_WINDING,
                    ROLE_COIL,
                    MATERIAL_COIL_CONDUCTOR,
                ),
            )
        )
        faceted = facet_assembly(assembly, linear_deflection_m, angular_deflection_rad)
        smallest_radii = (column, column, winding_inner)
        bodies = assembly_evidence(
            assembly.bodies,
            smallest_radii,
            faceted,
            reference.meshes,
            linear_deflection_m,
            segments,
        )
    except (CadError, GeometryError) as exc:
        raise DeviceGeometryError(str(exc)) from exc
    manifest = assembly.manifest()
    extras = {
        "schema": CAD_MODEL_SCHEMA,
        "schema_version": CAD_MODEL_SCHEMA_VERSION,
        "configuration_digest_sha256": configuration.digest_sha256(),
        "envelope_digest_sha256": envelope.digest_sha256(),
        "assembly_manifest_sha256": assembly.manifest_sha256(),
        "units": dict(CAD_MODEL_UNITS),
        "non_claims": list(CAD_MODEL_NON_CLAIMS),
        "backend_versions": backend_versions(),
    }
    step_data = step_bytes(assembly, extras)
    return DeviceModelCAD(
        configuration_digest_sha256=configuration.digest_sha256(),
        envelope_digest_sha256=envelope.digest_sha256(),
        reference_mesh_segments=segments,
        linear_deflection_m=linear_deflection_m,
        angular_deflection_rad=angular_deflection_rad,
        backend_versions=backend_versions(),
        assembly_manifest=manifest,
        step_sha256=step_sha256(step_data),
        bodies=bodies,
        step_data=step_data,
        faceted_meshes=faceted,
    )
