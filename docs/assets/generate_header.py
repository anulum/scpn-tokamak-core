# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Tokamak Core — repository header artwork generator

"""Generate the three README header images (1280x640) for this repository.

Every image is original generated artwork derived from this repository's
own domain surface — the device configuration model (Miller-parameterised
geometry, coil topology, operational limits) and the diagnostic and clock
semantics model — never from plasma-equilibrium physics, which belongs to
the flagship fusion solver repository. The right-hand text panel states
only facts backed by the repository itself.

Outputs (written next to this script):

- ``repo_header.png`` — device cross-section with coils, diagnostic
  sight-lines and the magnetic probe ring (used by ``README.md``).
- ``repo_header_registry_split.png`` — the two owned registry
  identifiers side by side with their aspect-ratio split.
- ``repo_header_diagnostics.png`` — synthetic diagnostic channels over
  a shared monotonic time-base with a device-section inset.

Generation-time tooling only: requires ``numpy`` and ``matplotlib``,
which are deliberately not part of the pinned development lock. Run as
``python3 docs/assets/generate_header.py`` from the repository root.
The output is deterministic (fixed geometry, seeded noise).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:  # pragma: no cover - typing aid only
    from numpy.typing import NDArray

OUT_DIR = Path(__file__).resolve().parent

BG = "#00050a"
CYAN = "#00ccff"
MAGENTA = "#ff00ff"
STEEL = "#334466"
PROBE = "#66aaff"

WIDTH_IN, HEIGHT_IN, DPI = 12.8, 6.4, 100

TITLE_METRICS: list[tuple[str, str]] = [
    ("Device Configurations", "conventional + spherical (A ≤ 2 split)"),
    ("Configuration Model", "geometry · coils · limits, SHA-256 canon"),
    ("Diagnostics & Clocks", "fail-closed vs pinned SPO catalogue"),
    ("Plan Envelope", "v1.1.0 · synthetic · review-only"),
    ("Evidence Maturity", "computational_prototype"),
    ("Quality Gates", "100% branch cov · mypy --strict"),
]


def _pyplot() -> Any:
    """Return pyplot configured for headless Agg rendering."""
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _glow_cmap() -> Any:
    """Build the family glow colormap (deep navy to cyan)."""
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list(
        "scpn_glow",
        ["#00050a", "#001428", "#002d55", "#005588", "#0088bb", "#00ccff"],
    )


def miller_boundary(
    major_radius: float,
    minor_radius: float,
    elongation: float,
    triangularity: float,
    samples: int = 400,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return a Miller-parameterised plasma-facing boundary in the R-Z plane."""
    theta = np.linspace(0.0, 2.0 * np.pi, samples)
    radial = major_radius + minor_radius * np.cos(theta + triangularity * np.sin(theta))
    vertical = elongation * minor_radius * np.sin(theta)
    return radial, vertical


def _text_panel(fig: Any, subtitle: str) -> None:
    """Draw the family right-hand text panel onto ``fig``."""
    ax = fig.add_axes([0.62, 0.0, 0.38, 1.0], facecolor=BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(
        0.08,
        0.84,
        "SCPN",
        color="white",
        fontsize=36,
        fontweight="bold",
        fontfamily="monospace",
        alpha=0.95,
    )
    ax.text(
        0.08,
        0.74,
        "TOKAMAK CORE",
        color="white",
        fontsize=30,
        fontweight="bold",
        fontfamily="monospace",
        alpha=0.95,
    )
    ax.text(
        0.08,
        0.66,
        subtitle,
        color=CYAN,
        fontsize=11.5,
        fontfamily="monospace",
        alpha=0.85,
    )
    ax.plot([0.08, 0.85], [0.615, 0.615], color=STEEL, lw=0.8, alpha=0.5)
    y = 0.55
    for label, value in TITLE_METRICS:
        ax.text(
            0.08,
            y,
            f"▸ {label}",
            color="#6688aa",
            fontsize=9,
            fontfamily="monospace",
            alpha=0.9,
        )
        ax.text(
            0.10,
            y - 0.030,
            value,
            color="#99bbdd",
            fontsize=8,
            fontfamily="monospace",
            alpha=0.7,
        )
        y -= 0.072
    ax.text(
        0.08,
        0.06,
        "© 1996–2026 Miroslav Šotek",
        color="#445566",
        fontsize=7,
        fontfamily="monospace",
        alpha=0.6,
    )
    ax.text(
        0.08,
        0.03,
        "anulum.li | AGPL-3.0",
        color="#445566",
        fontsize=7,
        fontfamily="monospace",
        alpha=0.5,
    )


def _art_axes(fig: Any) -> Any:
    """Return the borderless left-hand art axes of ``fig``."""
    ax = fig.add_axes([0.0, 0.0, 0.68, 1.0], facecolor=BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return ax


def _save(fig: Any, plt: Any, name: str) -> None:
    """Save ``fig`` to ``name`` inside the assets directory and close it."""
    target = OUT_DIR / name
    fig.savefig(target, dpi=DPI, facecolor=BG, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    print(f"generated {target}")


def generate_device_section() -> None:
    """Generate ``repo_header.png``: the device cross-section artwork."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    major, minor, kappa, delta = 5.0, 2.2, 1.8, 0.45

    grid_r = np.linspace(major - 2.0 * minor, major + 2.0 * minor, 320)
    grid_z = np.linspace(-kappa * minor * 1.5, kappa * minor * 1.5, 240)
    mesh_r, mesh_z = np.meshgrid(grid_r, grid_z)
    rho = np.sqrt(((mesh_r - major) / minor) ** 2 + (mesh_z / (kappa * minor)) ** 2)
    ax.contourf(
        mesh_r,
        mesh_z,
        np.exp(-rho * 1.6),
        levels=30,
        cmap=_glow_cmap(),
        alpha=0.8,
    )

    walls = [(1.00, 2.2, 0.95, CYAN), (1.08, 1.4, 0.6, PROBE), (1.16, 1.6, 0.7, STEEL)]
    for scale, lw, alpha, colour in walls:
        wall_r, wall_z = miller_boundary(major, minor * scale, kappa, delta)
        ax.plot(wall_r, wall_z, color=colour, lw=lw, alpha=alpha)

    coil_sites = [
        (major - 1.55 * minor, 1.35 * kappa * minor),
        (major + 1.35 * minor, 1.05 * kappa * minor),
        (major + 1.62 * minor, 0.35 * kappa * minor),
    ]
    for coil_r, coil_z in coil_sites:
        for sign in (+1.0, -1.0):
            ax.add_patch(
                plt.Rectangle(
                    (coil_r - 0.16, sign * coil_z - 0.16),
                    0.32,
                    0.32,
                    fill=False,
                    ec=MAGENTA,
                    lw=1.6,
                    alpha=0.85,
                )
            )
    for stack in range(-3, 4):
        ax.add_patch(
            plt.Rectangle(
                (major - 1.85 * minor - 0.14, stack * 0.62 - 0.25),
                0.28,
                0.5,
                fill=False,
                ec=MAGENTA,
                lw=1.2,
                alpha=0.6,
            )
        )

    port_r, port_z = major + 1.72 * minor, 0.5
    for target in np.linspace(-0.75, 0.75, 7):
        ax.plot(
            [port_r, major - 0.9 * minor],
            [port_z, target * kappa * minor],
            color="white",
            lw=0.7,
            alpha=0.35,
        )
    ax.plot(
        [major + 0.15, major + 0.15],
        [-1.35 * kappa * minor, 1.35 * kappa * minor],
        color=CYAN,
        lw=0.9,
        alpha=0.45,
        ls=(0, (6, 3)),
    )

    ring_r, ring_z = miller_boundary(major, minor * 1.24, kappa, delta, 28)
    ax.scatter(ring_r, ring_z, s=10, c=PROBE, alpha=0.8, zorder=5)
    ax.set_xlim(grid_r.min(), grid_r.max())
    ax.set_ylim(grid_z.min(), grid_z.max())

    _text_panel(fig, "Tokamak Device Configuration Truth")
    _save(fig, plt, "repo_header.png")


def generate_registry_split() -> None:
    """Generate ``repo_header_registry_split.png``: the owned identifiers."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(0, 10)
    ax.set_ylim(-3.2, 3.2)

    conv_major, conv_minor, conv_kappa, conv_delta = 2.6, 0.8, 1.7, 0.4
    conv_axis = 0.35
    bound_r, bound_z = miller_boundary(
        conv_axis + conv_major, conv_minor, conv_kappa, conv_delta
    )
    ax.plot(bound_r, bound_z, color=CYAN, lw=2.0, alpha=0.95)
    for fraction in np.linspace(0.15, 0.95, 7):
        inner_r, inner_z = miller_boundary(
            conv_axis + conv_major,
            conv_minor * fraction,
            conv_kappa,
            conv_delta * fraction,
        )
        ax.plot(inner_r, inner_z, color=CYAN, lw=0.6, alpha=0.30)
    ax.axvline(conv_axis, color=STEEL, lw=1.0, alpha=0.6, ls=(0, (2, 2)))
    ax.annotate(
        "",
        xy=(conv_axis + conv_major - conv_minor, -2.85),
        xytext=(conv_axis, -2.85),
        arrowprops={"arrowstyle": "<->", "color": PROBE, "lw": 1.0, "alpha": 0.8},
    )
    ax.text(
        conv_axis + 0.55 * (conv_major - conv_minor),
        -3.1,
        "A = R0/a ≈ 3.2",
        color=PROBE,
        fontsize=8.5,
        fontfamily="monospace",
        ha="center",
    )
    ax.text(
        conv_axis + conv_major,
        2.75,
        "conventional_tokamak",
        color="#99bbdd",
        fontsize=9.5,
        fontfamily="monospace",
        ha="center",
        alpha=0.9,
    )

    sph_major, sph_minor, sph_kappa, sph_delta = 1.15, 0.75, 2.4, 0.5
    sph_offset = 6.3
    bound_r, bound_z = miller_boundary(
        sph_offset + sph_major, sph_minor, sph_kappa, sph_delta
    )
    ax.plot(bound_r, bound_z, color=MAGENTA, lw=2.0, alpha=0.95)
    for fraction in np.linspace(0.15, 0.95, 7):
        inner_r, inner_z = miller_boundary(
            sph_offset + sph_major,
            sph_minor * fraction,
            sph_kappa,
            sph_delta * fraction,
        )
        ax.plot(inner_r, inner_z, color=MAGENTA, lw=0.6, alpha=0.30)
    ax.axvline(sph_offset, color=STEEL, lw=1.0, alpha=0.6, ls=(0, (2, 2)))
    ax.annotate(
        "",
        xy=(sph_offset + sph_major - sph_minor, -2.85),
        xytext=(sph_offset, -2.85),
        arrowprops={"arrowstyle": "<->", "color": PROBE, "lw": 1.0, "alpha": 0.8},
    )
    ax.text(
        sph_offset + 0.5 * (sph_major - sph_minor),
        -3.1,
        "A ≤ 2",
        color=PROBE,
        fontsize=8.5,
        fontfamily="monospace",
        ha="center",
    )
    ax.text(
        sph_offset + sph_major,
        2.75,
        "spherical_tokamak",
        color="#ffaaff",
        fontsize=9.5,
        fontfamily="monospace",
        ha="center",
        alpha=0.9,
    )

    ax.plot([5.05, 5.05], [-2.35, 2.4], color=STEEL, lw=0.8, alpha=0.4)
    ax.text(
        5.05,
        -2.62,
        "Peng–Strickler split · Nucl. Fusion 26 (1986) 769",
        color="#445566",
        fontsize=7.5,
        fontfamily="monospace",
        ha="center",
    )

    _text_panel(fig, "Two Registry Identifiers, One Owner")
    _save(fig, plt, "repo_header_registry_split.png")


def generate_diagnostics_fabric() -> None:
    """Generate ``repo_header_diagnostics.png``: channels over a clock."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    rng = np.random.default_rng(1986)

    time = np.linspace(0.0, 10.0, 1200)
    channels: list[tuple[str, str, NDArray[np.float64]]] = [
        (
            "magnetic_probe",
            CYAN,
            np.sin(2.1 * time) * np.exp(-0.05 * time) + 0.15 * np.sin(9 * time),
        ),
        ("flux_loop", PROBE, 0.8 * np.cos(1.3 * time + 0.7)),
        ("interferometer", "#88ddff", 0.6 * np.sin(0.9 * time) ** 2 - 0.3),
        (
            "bolometer",
            MAGENTA,
            0.5 * np.exp(-((time - 4.2) ** 2) / 2.5)
            + 0.4 * np.exp(-((time - 7.5) ** 2) / 1.2)
            - 0.25,
        ),
        (
            "soft_xray",
            "#ffaaff",
            0.35 * np.sign(np.sin(3.3 * time)) * np.abs(np.sin(3.3 * time)) ** 0.5,
        ),
    ]
    baseline = 8.6
    for name, colour, trace in channels:
        noisy = trace * 0.55 + 0.06 * rng.standard_normal(time.size)
        ax.plot(
            time * 0.98 + 0.05,
            baseline + noisy * 0.9,
            color=colour,
            lw=0.9,
            alpha=0.9,
        )
        ax.text(
            0.1,
            baseline + 0.62,
            name,
            color=colour,
            fontsize=7.5,
            fontfamily="monospace",
            alpha=0.8,
        )
        baseline -= 1.55

    for tick in np.linspace(0.4, 9.6, 24):
        ax.plot([tick, tick], [1.05, 9.55], color=STEEL, lw=0.5, alpha=0.22)
    for tick in np.linspace(0.4, 9.6, 6):
        ax.plot([tick, tick], [0.85, 9.65], color=CYAN, lw=0.8, alpha=0.35)
    ax.text(
        9.35,
        0.45,
        "monotonic clock · shared time-base",
        color="#445566",
        fontsize=7.5,
        fontfamily="monospace",
        ha="right",
        alpha=0.9,
    )

    inset = fig.add_axes([0.505, 0.075, 0.14, 0.30], facecolor=BG)
    inset.set_xticks([])
    inset.set_yticks([])
    for spine in inset.spines.values():
        spine.set_color(STEEL)
        spine.set_alpha(0.4)
    sect_r, sect_z = miller_boundary(0.0, 1.0, 1.8, 0.45)
    inset.plot(sect_r, sect_z, color=CYAN, lw=1.4, alpha=0.9)
    ring_r, ring_z = miller_boundary(0.0, 1.18, 1.8, 0.45, 18)
    inset.scatter(ring_r, ring_z, s=5, c=PROBE, alpha=0.85)
    inset.set_xlim(-2.1, 2.1)
    inset.set_ylim(-2.3, 2.3)

    _text_panel(fig, "Diagnostic & Clock Semantics, Fail-Closed")
    _save(fig, plt, "repo_header_diagnostics.png")


if __name__ == "__main__":
    generate_device_section()
    generate_registry_split()
    generate_diagnostics_fabric()
