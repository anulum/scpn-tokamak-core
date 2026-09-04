# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — tier-G1 device model

"""Tier-G1 tessellated model of the cylindrical periodic equivalent.

Three bodies in a fixed order: the plasma column, the vacuum vessel wall
at its edge, and the toroidal-field winding outside the gap. Every body
is a cylinder or an annular tube about ``z``, so this tier needs no
primitive the shared library does not already have.

**The elongation is used, not discarded.** A straight cylinder has a
circular cross-section and a shaped tokamak plasma does not, so the
column is built at the *area-equivalent* radius ``a sqrt(kappa)``. Its
cross-sectional area is then the ellipse's, and over the periodic length
``2 pi R0`` its volume is exactly the volume
:func:`~scpn_tokamak_core.physics.equilibrium.plasma_volume_m3` computes
by Pappus's theorem. Building the column at ``a`` instead would have
thrown away a declared parameter and made the two tiers disagree.

The triangularity does not enter, and that is not an oversight: it does
not enter the Pappus volume either, and the physics record's non-claims
already say so. A cross-section's fore-aft asymmetry has nowhere to go in
a body of revolution.

What the periodic equivalent drops is the toroidal curvature, and with it
every quantity that distinguishes the inboard side from the outboard one.
The non-claims say that too.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Final

from scpn_reactor_kernels.errors import GeometryError
from scpn_reactor_kernels.geometry import (
    TriangleMesh,
    annular_tube,
    cylinder_solid,
    require_segments,
)

from scpn_tokamak_core.configuration import DeviceConfiguration
from scpn_tokamak_core.device.envelope import DeviceEnvelope
from scpn_tokamak_core.errors import DeviceGeometryError
from scpn_tokamak_core.geometry import ToroidalGeometry

MODEL_SCHEMA: Final = "scpn.tokamak-3d-model.v1"
MODEL_SCHEMA_VERSION: Final = "1.0.0"
MODEL_UNITS: Final = {
    "length": "metre",
    "handedness": "right",
    "axis": "z along the axis of the cylindrical periodic equivalent",
    "origin": "z = 0 at one end of the periodic length 2 pi R0",
}
MODEL_NON_CLAIMS: Final = (
    "analytic surfaces tessellated from a synthetic configuration and envelope",
    (
        "the cylindrical periodic equivalent of the toroidal device is "
        "modelled: the toroidal curvature is not, so nothing here "
        "distinguishes the inboard side of a torus from the outboard one, and "
        "the end caps of the cylinders are an artefact of the primitive"
    ),
    (
        "the plasma column carries the elongation through an area-equivalent "
        "radius and cannot carry the triangularity, which no body of "
        "revolution can represent"
    ),
    (
        "the toroidal-field winding is drawn as one tube of declared size; no "
        "coil, turn count, circuit, ripple or field map is modelled, and the "
        "poloidal field coils have no place in a straight equivalent and are "
        "absent"
    ),
    "no body is an equilibrium boundary, a CAD solid or an engineering model",
    "no material property, load, field or neutronic quantity is carried",
    "no value describes or validates any real machine",
)

ROLE_PLASMA: Final = "plasma"
ROLE_VACUUM_BOUNDARY: Final = "vacuum_boundary"
ROLE_COIL: Final = "coil"
MATERIAL_PLASMA: Final = "plasma"
MATERIAL_VESSEL_WALL: Final = "vessel_wall"
MATERIAL_COIL_CONDUCTOR: Final = "coil_conductor"

BODY_PLASMA_COLUMN: Final = "plasma_column"
BODY_VACUUM_VESSEL: Final = "vacuum_vessel"
BODY_TOROIDAL_FIELD_WINDING: Final = "toroidal_field_winding"
BODY_NAMES: Final = (
    BODY_PLASMA_COLUMN,
    BODY_VACUUM_VESSEL,
    BODY_TOROIDAL_FIELD_WINDING,
)


def equivalent_column_radius_m(geometry: ToroidalGeometry) -> float:
    """Return the radius whose circle has the elliptic cross-section's area.

    ``a sqrt(kappa)``. A circle of this radius encloses the same area as
    the ellipse of semi-axes ``a`` and ``kappa a``, so the straight
    column of the periodic equivalent encloses the same volume as the
    shaped torus.

    Parameters
    ----------
    geometry
        Validated toroidal geometry.

    Returns
    -------
    float
        The area-equivalent minor radius in metres.
    """
    return geometry.minor_radius_m * math.sqrt(geometry.elongation)


def periodic_length_m(geometry: ToroidalGeometry) -> float:
    """Return the length the torus unrolls to.

    ``2 pi R0``, the circumference of the magnetic axis.

    Parameters
    ----------
    geometry
        Validated toroidal geometry.

    Returns
    -------
    float
        The periodic length in metres.
    """
    return 2.0 * math.pi * geometry.major_radius_m


@dataclass(frozen=True, slots=True)
class DeviceModel3D:
    """The tessellated device model of one configuration and envelope.

    Parameters
    ----------
    configuration_digest_sha256
        Digest of the configuration the model was built from.
    envelope_digest_sha256
        Digest of the envelope the model was built from.
    segments
        Circumferential segment count every body was tessellated at.
    meshes
        The three bodies in the fixed order of :data:`BODY_NAMES`.

    Raises
    ------
    DeviceGeometryError
        If the body names or their order differ from :data:`BODY_NAMES`.
    """

    configuration_digest_sha256: str
    envelope_digest_sha256: str
    segments: int
    meshes: tuple[TriangleMesh, ...]

    def __post_init__(self) -> None:
        """Validate the body set and its order.

        Raises
        ------
        DeviceGeometryError
            If the body names or their order differ from
            :data:`BODY_NAMES`.
        """
        names = tuple(mesh.name for mesh in self.meshes)
        if names != BODY_NAMES:
            raise DeviceGeometryError(
                f"meshes: bodies must be exactly {BODY_NAMES!r} in order, got {names!r}"
            )

    def to_record(self) -> dict[str, Any]:
        """Project the model to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            The schema-tagged record with one entry per body.
        """
        return {
            "schema": MODEL_SCHEMA,
            "schema_version": MODEL_SCHEMA_VERSION,
            "units": dict(MODEL_UNITS),
            "non_claims": list(MODEL_NON_CLAIMS),
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "envelope_digest_sha256": self.envelope_digest_sha256,
            "segments": self.segments,
            "bodies": [
                {
                    "name": mesh.name,
                    "role": mesh.role,
                    "material_identifier": mesh.material_identifier,
                    "vertex_count": mesh.vertex_count,
                    "face_count": mesh.face_count,
                    "volume_m3": mesh.signed_volume_m3(),
                    "surface_area_m2": mesh.surface_area_m2(),
                }
                for mesh in self.meshes
            ],
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


def _require_envelope(
    configuration: DeviceConfiguration, envelope: DeviceEnvelope
) -> None:
    """Refuse a configuration and envelope that do not fit together.

    Parameters
    ----------
    configuration
        Validated device configuration.
    envelope
        Validated mechanical envelope.

    Raises
    ------
    DeviceGeometryError
        If the radial build reaches the axis of the periodic equivalent,
        which would put the winding inside the machine rather than around
        it. The refusal names both fields and their values.
    """
    length = periodic_length_m(configuration.geometry)
    build = equivalent_column_radius_m(configuration.geometry) + envelope.radial_build_m
    if build >= length / 2.0:
        raise DeviceGeometryError(
            "winding_thickness_m: the radial build must stay inside half the "
            f"periodic length or the unrolled machine self-intersects "
            f"({build!r} >= {length / 2.0!r})"
        )


def build_device_model(
    configuration: DeviceConfiguration, envelope: DeviceEnvelope, segments: int
) -> DeviceModel3D:
    """Tessellate the three bodies of a validated design.

    Parameters
    ----------
    configuration
        Validated tokamak configuration; its geometry supplies the plasma
        radii and the elongation.
    envelope
        Validated mechanical envelope.
    segments
        Circumferential segments for every body; at least 8, multiple
        of 8.

    Returns
    -------
    DeviceModel3D
        The composed model.

    Raises
    ------
    DeviceGeometryError
        If the segment count is invalid or the two do not fit together;
        the library's refusal is re-raised under the device error type
        with its message.
    """
    try:
        require_segments(segments)
    except GeometryError as exc:
        raise DeviceGeometryError(str(exc)) from exc
    _require_envelope(configuration, envelope)
    geometry = configuration.geometry
    column = equivalent_column_radius_m(geometry)
    length = periodic_length_m(geometry)
    vessel_outer = column + envelope.vessel_wall_thickness_m
    winding_inner = vessel_outer + envelope.winding_gap_m
    winding_outer = winding_inner + envelope.winding_thickness_m
    bodies = (
        (
            BODY_PLASMA_COLUMN,
            ROLE_PLASMA,
            MATERIAL_PLASMA,
            cylinder_solid(column, 0.0, length, segments),
        ),
        (
            BODY_VACUUM_VESSEL,
            ROLE_VACUUM_BOUNDARY,
            MATERIAL_VESSEL_WALL,
            annular_tube(column, vessel_outer, 0.0, length, segments),
        ),
        (
            BODY_TOROIDAL_FIELD_WINDING,
            ROLE_COIL,
            MATERIAL_COIL_CONDUCTOR,
            annular_tube(winding_inner, winding_outer, 0.0, length, segments),
        ),
    )
    meshes = tuple(
        TriangleMesh(
            name=name,
            role=role,
            material_identifier=material,
            vertices=vertices,
            faces=faces,
        )
        for name, role, material, (vertices, faces) in bodies
    )
    return DeviceModel3D(
        configuration_digest_sha256=configuration.digest_sha256(),
        envelope_digest_sha256=envelope.digest_sha256(),
        segments=segments,
        meshes=meshes,
    )
