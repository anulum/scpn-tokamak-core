# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — level-0 physics record

"""Level-0 physics record of one validated tokamak configuration.

The record composes what the configuration already knows how to compute
with the closed forms of :mod:`scpn_tokamak_core.physics.equilibrium`, and
adds nothing that either already owns.

That is deliberate. The Greenwald density limit and the elongation-
corrected cylindrical safety factor live on
:class:`~scpn_tokamak_core.limits.OperationalLimits` because they are
properties of an operating point, and this module **calls** them rather
than restating them. A level-0 record that reimplemented its own
repository's relations would be two sources of truth for one number.

What it adds is the composition: the plasma the geometry encloses, the
field it sits in across its own width, the density the declared Greenwald
fraction asks for against the limit, and the safety factor against its
declared floor — each with the margin stated rather than left to a reader
to subtract.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from scpn_tokamak_core.configuration import DeviceConfiguration
from scpn_tokamak_core.physics.equilibrium import (
    normalised_current_ma_per_mt,
    plasma_volume_m3,
    toroidal_field_at_radius_t,
)

LEVEL0_SCHEMA: Final = "scpn.tokamak-level0-physics.v1"
LEVEL0_SCHEMA_VERSION: Final = "1.0.0"
LEVEL0_NON_CLAIMS: Final = (
    (
        "closed-form evaluation of a shaped torus and its vacuum field on a "
        "declared operating point"
    ),
    "no equilibrium, stability, transport or current-drive equation is solved",
    (
        "the toroidal field is the vacuum field; the plasma's own paramagnetism "
        "and the discreteness of the coils are not modelled"
    ),
    (
        "the density limit and the cylindrical safety factor are empirical "
        "consistency instruments with documented applicability, not predictions "
        "of disruption or stability"
    ),
    (
        "the triangularity is carried by the configuration and does not enter "
        "the volume, which is exact only for the elliptic cross-section"
    ),
    "no yield, gain, reactivity, confinement or breakeven statement",
    (
        "no value describes or validates any real machine; an anchor reproduces "
        "a number the filed source prints and nothing further"
    ),
)


@dataclass(frozen=True, slots=True)
class OperatingPoint:
    """The composed operating point of one validated configuration.

    Parameters
    ----------
    aspect_ratio
        ``R / a`` of the validated geometry.
    plasma_volume_m3
        Volume the elliptic cross-section encloses.
    axis_field_t
        Toroidal field on the magnetic axis, from the limits.
    inboard_field_t, outboard_field_t
        The vacuum field at the inboard and outboard edges of the plasma,
        where a tokamak's field is strongest and weakest.
    field_ratio
        Inboard over outboard: how much the field varies across the
        plasma's own width.
    plasma_current_ma
        Plasma current, from the limits.
    normalised_current_ma_per_mt
        ``I_p / (a B_t)``.
    greenwald_density_limit_1e20_m3
        The limit for this current and minor radius.
    operating_density_1e20_m3
        The declared Greenwald fraction times that limit.
    greenwald_fraction
        The declared fraction itself.
    cylindrical_safety_factor
        The elongation-corrected estimate.
    safety_factor_floor
        The declared floor.
    safety_factor_margin
        Estimate minus floor. Negative means the declared operating point
        sits below its own declared floor; the record reports it and
        refuses nothing, because the floor is a declaration and not a law.
    """

    aspect_ratio: float
    plasma_volume_m3: float
    axis_field_t: float
    inboard_field_t: float
    outboard_field_t: float
    field_ratio: float
    plasma_current_ma: float
    normalised_current_ma_per_mt: float
    greenwald_density_limit_1e20_m3: float
    operating_density_1e20_m3: float
    greenwald_fraction: float
    cylindrical_safety_factor: float
    safety_factor_floor: float
    safety_factor_margin: float

    def to_record(self) -> dict[str, Any]:
        """Project the operating point to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            One key per field, in the declaration order of the class.
        """
        return {
            "aspect_ratio": self.aspect_ratio,
            "plasma_volume_m3": self.plasma_volume_m3,
            "axis_field_t": self.axis_field_t,
            "inboard_field_t": self.inboard_field_t,
            "outboard_field_t": self.outboard_field_t,
            "field_ratio": self.field_ratio,
            "plasma_current_ma": self.plasma_current_ma,
            "normalised_current_ma_per_mt": self.normalised_current_ma_per_mt,
            "greenwald_density_limit_1e20_m3": self.greenwald_density_limit_1e20_m3,
            "operating_density_1e20_m3": self.operating_density_1e20_m3,
            "greenwald_fraction": self.greenwald_fraction,
            "cylindrical_safety_factor": self.cylindrical_safety_factor,
            "safety_factor_floor": self.safety_factor_floor,
            "safety_factor_margin": self.safety_factor_margin,
        }


@dataclass(frozen=True, slots=True)
class Level0Physics:
    """Composed level-0 record of one configuration.

    Parameters
    ----------
    configuration_digest_sha256
        Digest of the configuration the record was built from.
    operating_point
        The composed operating point.
    """

    configuration_digest_sha256: str
    operating_point: OperatingPoint

    def to_record(self) -> dict[str, Any]:
        """Project the record to a JSON-serialisable object.

        Returns
        -------
        dict[str, Any]
            The schema-tagged record with its non-claims.
        """
        return {
            "schema": LEVEL0_SCHEMA,
            "schema_version": LEVEL0_SCHEMA_VERSION,
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "operating_point": self.operating_point.to_record(),
            "non_claims": list(LEVEL0_NON_CLAIMS),
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the record canonically.

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
        """Identify the exact record.

        Returns
        -------
        str
            SHA-256 of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def level0_physics(configuration: DeviceConfiguration) -> Level0Physics:
    """Compose the level-0 physics record of one validated configuration.

    Parameters
    ----------
    configuration
        Validated tokamak configuration. It needs no declared inputs of
        its own: unlike the other families of this group, everything the
        level-0 relations use is already in the configuration.

    Returns
    -------
    Level0Physics
        The composed record.

    Raises
    ------
    DeviceConfigurationError
        If a derived quantity falls outside its model bound; the
        refusals name the field.
    """
    geometry = configuration.geometry
    limits = configuration.limits
    axis_field = limits.toroidal_field_t
    major = geometry.major_radius_m
    minor = geometry.minor_radius_m
    inboard = toroidal_field_at_radius_t(axis_field, major, major - minor)
    outboard = toroidal_field_at_radius_t(axis_field, major, major + minor)
    limit = limits.greenwald_density_limit_1e20_m3(geometry)
    safety = limits.cylindrical_safety_factor(geometry)
    return Level0Physics(
        configuration_digest_sha256=configuration.digest_sha256(),
        operating_point=OperatingPoint(
            aspect_ratio=geometry.aspect_ratio,
            plasma_volume_m3=plasma_volume_m3(geometry),
            axis_field_t=axis_field,
            inboard_field_t=inboard,
            outboard_field_t=outboard,
            field_ratio=inboard / outboard,
            plasma_current_ma=limits.plasma_current_ma,
            normalised_current_ma_per_mt=normalised_current_ma_per_mt(
                limits.plasma_current_ma, minor, axis_field
            ),
            greenwald_density_limit_1e20_m3=limit,
            operating_density_1e20_m3=limits.greenwald_fraction * limit,
            greenwald_fraction=limits.greenwald_fraction,
            cylindrical_safety_factor=safety,
            safety_factor_floor=limits.safety_factor_floor,
            safety_factor_margin=safety - limits.safety_factor_floor,
        ),
    )
