# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — installed-wheel contract check

"""Exercise the installed package from outside the source checkout.

The installed-wheel workflow builds the wheel, installs it into a clean
environment and runs this script with ``python -I`` from a directory
outside the checkout. The script fails closed unless the package was
imported from the environment rather than the checkout, ships its
``py.typed`` marker, reports matching installed metadata with the pinned
kernel dependency, and serves the public path from a canonical
configuration document through level-0 physics to the tessellated device
model. In ``base`` mode the optional CAD back-end must be absent and a CAD
request must raise the documented ``CadUnavailableError``; in ``cad`` mode
one B-rep model must be built and exported.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import sys
from pathlib import Path
from typing import Final

DISTRIBUTION: Final = "scpn-tokamak-core"
PACKAGE: Final = "scpn_tokamak_core"
KERNEL_REQUIREMENT: Final = "scpn-reactor-kernels"
MODES: Final = ("base", "cad")

CONFIGURATION_DOCUMENT: Final = (
    b'{"coils":{"has_central_solenoid":true,"poloidal_field_coil_count":6,'
    b'"toroidal_field_coil_count":12},"geometry":{"elongation":1.6,'
    b'"major_radius_m":3.0,"minor_radius_m":1.0,"triangularity":0.3},'
    b'"identifier":"conventional_tokamak","limits":{"flat_top_duration_s":10.0,'
    b'"greenwald_fraction":0.8,"plasma_current_ma":5.0,"safety_factor_floor":2.0,'
    b'"toroidal_field_t":4.0},"registry":{"digest_sha256":'
    b'"0000000000000000000000000000000000000000000000000000000000000000",'
    b'"version":"1.0.0"}}\n'
)
"""A synthetic canonical configuration; it describes no real machine."""

ENVELOPE_RECORD: Final = {
    "vessel_wall_thickness_m": 0.05,
    "winding_gap_m": 0.15,
    "winding_thickness_m": 0.30,
}
"""A synthetic radial build in metres."""


def layout_findings(package_dir: Path, checkout: Path) -> list[str]:
    """Check where the package was imported from and what it ships.

    Parameters
    ----------
    package_dir
        Directory of the imported package.
    checkout
        Source checkout the installed package must not come from.

    Returns
    -------
    list[str]
        Findings; empty when the package lies outside the checkout and
        carries its ``py.typed`` marker.
    """
    return failed(
        [
            (
                not package_dir.resolve().is_relative_to(checkout.resolve()),
                f"{PACKAGE} imported from the checkout: {package_dir}",
            ),
            (
                (package_dir / "py.typed").is_file(),
                f"{PACKAGE} ships no py.typed marker",
            ),
        ]
    )


def failed(checks: list[tuple[bool, str]]) -> list[str]:
    """Return the messages of the checks that did not hold.

    Parameters
    ----------
    checks
        Pairs of an outcome and the finding reported when it is false.

    Returns
    -------
    list[str]
        Findings in check order.
    """
    return [message for holds, message in checks if not holds]


def metadata_findings(
    version: str,
    distribution_name: str = DISTRIBUTION,
    required: str = KERNEL_REQUIREMENT,
) -> list[str]:
    """Check the installed distribution metadata.

    Parameters
    ----------
    version
        ``__version__`` of the imported package.
    distribution_name
        Installed distribution to read.
    required
        Requirement the distribution must declare.

    Returns
    -------
    list[str]
        Findings; empty when the distribution is installed with the same
        version and declares the required dependency.
    """
    try:
        distribution = importlib.metadata.distribution(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return [f"{distribution_name} is not installed"]
    requirements = distribution.requires or []
    return failed(
        [
            (
                distribution.version == version,
                f"installed version {distribution.version} != package {version}",
            ),
            (
                any(item.startswith(required) for item in requirements),
                f"{distribution_name} does not require {required}",
            ),
        ]
    )


def public_path_findings(mode: str) -> list[str]:
    """Serve the public path through the installed package.

    Parameters
    ----------
    mode
        ``base`` when the CAD back-end must be absent, ``cad`` when it must
        build a model.

    Returns
    -------
    list[str]
        Findings; empty when every promised capability of the mode works
        and the absent one fails as documented.
    """
    from scpn_reactor_kernels.errors import CadUnavailableError

    from scpn_tokamak_core import configuration_from_bytes
    from scpn_tokamak_core.device import (
        DEFAULT_REFERENCE_MESH_SEGMENTS,
        build_device_cad,
        build_device_model,
        envelope_from_record,
    )
    from scpn_tokamak_core.physics import level0_physics

    configuration = configuration_from_bytes(CONFIGURATION_DOCUMENT)
    envelope = envelope_from_record(dict(ENVELOPE_RECORD))
    segments = DEFAULT_REFERENCE_MESH_SEGMENTS
    record = level0_physics(configuration).canonical_bytes()
    model = build_device_model(configuration, envelope, segments).digest_sha256()
    findings = failed(
        [
            (
                configuration.canonical_bytes() == CONFIGURATION_DOCUMENT,
                "configuration did not round-trip byte for byte",
            ),
            (
                record == level0_physics(configuration).canonical_bytes(),
                "level-0 record is not deterministic",
            ),
            (
                model
                == build_device_model(
                    configuration, envelope, segments
                ).digest_sha256(),
                "tessellated model is not deterministic",
            ),
        ]
    )
    if mode == "base":
        try:
            build_device_cad(configuration, envelope)
        except CadUnavailableError:
            return findings
        return [*findings, "CAD back-end present in the base environment"]
    cad = build_device_cad(configuration, envelope)
    return findings + failed(
        [
            (bool(cad.step_data), "CAD model exported no STEP data"),
            (
                cad.configuration_digest_sha256 == configuration.digest_sha256(),
                "CAD model is bound to another configuration",
            ),
        ]
    )


def check_installed(mode: str, checkout: Path) -> list[str]:
    """Run every installed-package check for one environment.

    Parameters
    ----------
    mode
        One of :data:`MODES`.
    checkout
        Source checkout the package must not be imported from.

    Returns
    -------
    list[str]
        All findings; empty when the installed package meets its contract.
    """
    package = importlib.import_module(PACKAGE)
    package_dir = Path(package.__file__ or "").parent
    findings = layout_findings(package_dir, checkout)
    findings += metadata_findings(str(package.__version__))
    findings += public_path_findings(mode)
    return findings


def report(mode: str, findings: list[str]) -> int:
    """Print the outcome of one environment and return its exit status.

    Parameters
    ----------
    mode
        Environment mode that was checked.
    findings
        Findings of :func:`check_installed`.

    Returns
    -------
    int
        ``0`` without findings, else ``1``.
    """
    if findings:
        print(f"installed-package: FAIL {mode}", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
        return 1
    print(f"installed-package: PASS {mode}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the installed-package check from the command line.

    Parameters
    ----------
    argv
        Argument vector; ``None`` reads ``sys.argv``.

    Returns
    -------
    int
        ``0`` when the installed package meets its contract, else ``1``.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    args = parser.parse_args(argv)
    return report(args.mode, check_installed(args.mode, args.checkout))


if __name__ == "__main__":
    sys.exit(main())
