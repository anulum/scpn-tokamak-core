# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — level-0 record replay tests

"""A level-0 record is replayable from its declared input custody.

The level-0 relations of this family read nothing but the configuration,
and the record binds that configuration by the digest of its canonical
bytes. These tests prove the consequence end to end: another process that
holds only the configuration bytes reconstructs the configuration through
the public decoder and recomputes the identical record, and a
configuration whose digest differs from the one the record names cannot
reproduce it.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from test_configuration import synthetic_conventional

from scpn_tokamak_core import configuration_from_bytes
from scpn_tokamak_core.physics import level0_physics

REPO = Path(__file__).resolve().parents[1]

REPLAY = """
import sys
from scpn_tokamak_core import configuration_from_bytes
from scpn_tokamak_core.physics import level0_physics
configuration = configuration_from_bytes(sys.stdin.buffer.read())
sys.stdout.buffer.write(level0_physics(configuration).canonical_bytes())
"""


def _replay_in_another_process(configuration_bytes: bytes) -> bytes:
    """Recompute a record in a fresh interpreter from configuration bytes."""
    completed = subprocess.run(
        [sys.executable, "-c", REPLAY],
        input=configuration_bytes,
        capture_output=True,
        check=True,
        env={"PYTHONPATH": str(REPO / "src")},
    )
    return completed.stdout


def test_record_names_the_digest_of_its_only_input() -> None:
    """The record's input digest is the digest of the configuration bytes."""
    configuration = synthetic_conventional()
    record = level0_physics(configuration).to_record()
    data = configuration.canonical_bytes()
    assert record["configuration_digest_sha256"] == hashlib.sha256(data).hexdigest()


def test_another_process_replays_the_whole_record() -> None:
    """Configuration bytes alone reproduce the record byte for byte."""
    configuration = synthetic_conventional()
    expected = level0_physics(configuration).canonical_bytes()
    replayed = _replay_in_another_process(configuration.canonical_bytes())
    assert replayed == expected
    record = json.loads(replayed)
    assert record["configuration_digest_sha256"] == configuration.digest_sha256()


def test_a_stale_configuration_cannot_reproduce_the_record() -> None:
    """Changing any input changes the named digest, so a replay is detectable."""
    original = level0_physics(synthetic_conventional())
    data = synthetic_conventional().canonical_bytes()
    stale = configuration_from_bytes(
        data.replace(b'"plasma_current_ma":5.0', b'"plasma_current_ma":5.5')
    )
    replayed = level0_physics(stale)
    assert replayed.configuration_digest_sha256 != original.configuration_digest_sha256
    assert replayed.canonical_bytes() != original.canonical_bytes()
