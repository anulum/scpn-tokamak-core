# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — device envelope tests

"""Every branch of the device envelope and its parser.

All parameter sets are synthetic; none describes any real machine.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

import pytest
from geometry_fixtures import REFERENCE_ENVELOPE_FIELDS, reference_envelope

from scpn_tokamak_core.device import (
    ENVELOPE_FIELDS,
    DeviceEnvelope,
    envelope_from_record,
)
from scpn_tokamak_core.errors import DeviceGeometryError


@pytest.mark.parametrize("field", ENVELOPE_FIELDS)
@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_every_field_is_refused_by_name_when_not_positive(
    field: str, value: float
) -> None:
    """Each declared value is validated, and the refusal names it."""
    with pytest.raises(DeviceGeometryError, match=field):
        reference_envelope(**{field: value})


def test_the_radial_build_is_the_sum_of_the_three_thicknesses() -> None:
    """The build is what separates the plasma edge from the winding's outside."""
    envelope = reference_envelope()
    assert envelope.radial_build_m == pytest.approx(
        sum(REFERENCE_ENVELOPE_FIELDS.values())
    )


def test_the_record_carries_exactly_the_declared_fields() -> None:
    """The projection neither loses nor invents a field."""
    record = reference_envelope().to_record()
    assert set(record) == set(ENVELOPE_FIELDS)
    assert record == REFERENCE_ENVELOPE_FIELDS


def test_the_canonical_bytes_are_canonical() -> None:
    """Sorted keys, minimal separators and exactly one trailing newline."""
    data = reference_envelope().canonical_bytes()
    assert data.endswith(b"\n")
    assert data.count(b"\n") == 1
    again = json.dumps(
        json.loads(data), sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    assert (again + "\n").encode("utf-8") == data


def test_the_digest_identifies_the_envelope() -> None:
    """The digest is the SHA-256 of the canonical bytes and moves with them."""
    envelope = reference_envelope()
    assert (
        envelope.digest_sha256()
        == hashlib.sha256(envelope.canonical_bytes()).hexdigest()
    )
    assert reference_envelope(winding_gap_m=0.2).digest_sha256() != (
        envelope.digest_sha256()
    )


def test_a_record_round_trips_through_the_parser() -> None:
    """Parsing a projection reproduces the envelope exactly."""
    envelope = reference_envelope()
    assert envelope_from_record(envelope.to_record()) == envelope


@pytest.mark.parametrize(
    ("record", "match"),
    [
        ({}, "vessel_wall_thickness_m"),
        ({**REFERENCE_ENVELOPE_FIELDS, "extra": 1.0}, "unknown fields"),
        ({**REFERENCE_ENVELOPE_FIELDS, "winding_gap_m": "0.15"}, "real number"),
        ({**REFERENCE_ENVELOPE_FIELDS, "winding_gap_m": True}, "real number"),
        ({**REFERENCE_ENVELOPE_FIELDS, "winding_gap_m": -1.0}, "winding_gap_m"),
    ],
)
def test_the_parser_refuses_by_name(record: dict[str, Any], match: str) -> None:
    """A missing, unknown, mistyped or invalid field is refused, not coerced.

    A boolean is refused explicitly: Python would otherwise accept it as an
    integer and read ``True`` as a thickness of one metre.
    """
    with pytest.raises(DeviceGeometryError, match=match):
        envelope_from_record(record)


def test_an_integer_thickness_is_accepted_as_a_real_number() -> None:
    """JSON carries no float-integer distinction, so an integer is a length."""
    record = {**REFERENCE_ENVELOPE_FIELDS, "winding_thickness_m": 1}
    assert envelope_from_record(record).winding_thickness_m == 1.0


def test_the_reference_envelope_is_a_valid_envelope() -> None:
    """The fixture the other suites build on is itself validated."""
    assert isinstance(reference_envelope(), DeviceEnvelope)
