# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — device model fixtures

"""Fixtures shared by the tier-G1 and tier-G2 tests.

The configurations come from the physics fixtures rather than being
declared again here, so the two capabilities are anchored on the same two
regimes and cannot drift apart. What this module adds is the mechanical
envelope, which the physics does not carry, and the closed form the
tessellation is checked against.

Every parameter set is synthetic and describes no real machine.
"""

from __future__ import annotations

import math
from typing import Final

from physics_fixtures import conventional_configuration, spherical_configuration

from scpn_tokamak_core.device import DeviceEnvelope

__all__ = [
    "REFERENCE_ENVELOPE_FIELDS",
    "conventional_configuration",
    "inscribed_polygon_ratio",
    "reference_envelope",
    "spherical_configuration",
]

REFERENCE_ENVELOPE_FIELDS: Final = {
    "vessel_wall_thickness_m": 0.05,
    "winding_gap_m": 0.15,
    "winding_thickness_m": 0.30,
}
"""A synthetic radial build, in metres. No filed source dimensions the
vessel or the winding of either regime, so these are declared and are not
presented as anchors."""


def reference_envelope(**overrides: float) -> DeviceEnvelope:
    """Build the synthetic reference envelope with optional overrides.

    Parameters
    ----------
    **overrides
        Field values replacing those of
        :data:`REFERENCE_ENVELOPE_FIELDS`.

    Returns
    -------
    DeviceEnvelope
        The validated envelope.
    """
    return DeviceEnvelope(**{**REFERENCE_ENVELOPE_FIELDS, **overrides})


def inscribed_polygon_ratio(segments: int) -> float:
    """Return the area of the inscribed regular polygon over the circle's.

    ``(n / 2 pi) sin(2 pi / n)``. Every body of these tiers is tessellated
    by inscribing a regular polygon in each circular section, so a mesh
    volume is smaller than the analytic volume by exactly this factor and
    by nothing else. It is what lets a tier-G1 volume be compared with a
    closed form as an identity rather than a tolerance.

    Parameters
    ----------
    segments
        Circumferential segment count.

    Returns
    -------
    float
        The ratio, which approaches one from below as the count rises.
    """
    return segments * math.sin(2.0 * math.pi / segments) / (2.0 * math.pi)
