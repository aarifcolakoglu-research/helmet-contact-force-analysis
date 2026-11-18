"""
Figures S9–S11 – calibration of the twelve helmet sensors (set S1_MatC).
  S9   step-median reference force against raw B_z, cubic and second-order fits (cycle 3, loading)
  S10  residuals of the second-order (a) and cubic (b) fits
  S11  loading–unloading hysteresis (force against indentation), cycle 3 bold
Data: data/calibration_S1_MatC_step_medians.csv – the step medians of the twelve bound
calibration files, exported from Sensor Tracking Studio (datasets/metadata_fz_median.csv,
bindings in config/selected_sensors.json). The fits are recomputed here and reproduce Table S4.
Usage: python figS9_S11_calibration.py     -> outputs/FigureS9_*, FigureS10_*, FigureS11_*
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pipeline import FONT_PT, STYLE, SENSORS, GRAM_PER_NEWTON, HERE, OUT_DIR

plt.rcParams.update(STYLE)
DATA = os.path.join(HERE, "data", "calibration_S1_MatC_step_medians.csv")
MM = 1 / 25.4
FIT_CYCLE = 3
C_LOAD, C_UNLOAD = "#1f4e99", "#c0504d"
C_GROUP = {"A": "#2e8b57", "B": "#3a6fc4", "C": "#c0504d"}


def load():
    d = pd.read_csv(DATA)
    d["bz_k"] = d.raw_bz_median / 1000.0
    return d


def fit(d, s, deg):
    c = d[(d.position == s) & (d.cycle_id == FIT_CYCLE) & (d["Load/Unload"] == "Loading")]
    p = np.polyfit(c.raw_bz_median, c.fz_median, deg)
    pred = np.polyval(p, c.raw_bz_median)
    r2 = 1 - ((c.fz_median - pred) ** 2).sum() / ((c.fz_median - c.fz_median.mean()) ** 2).sum()
    return p, r2, c


def save(fig, name):
    base = os.path.join(OUT_DIR, name)
    fig.savefig(base + ".png", dpi=600)
    fig.savefig(base + ".tif", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    print("saved", base)


def fig_s9(d):
    fig, axes = plt.subplots(3, 4, figsize=(180 * MM, 150 * MM))
    fig.subplots_adjust(left=0.07, right=0.99, top=0.95, bottom=0.14, hspace=0.55, wspace=0.32)
    for ax, s in zip(axes.flat, SENSORS):
        x = d[d.position == s]
        lo, un = x[x["Load/Unload"] == "Loading"], x[x["Load/Unload"] == "Unloading"]
        ax.plot(lo.bz_k, lo.fz_median, "o", ms=1.6, color=C_LOAD, alpha=0.7, mew=0)
        ax.plot(un.bz_k, un.fz_median, "^", ms=1.6, color=C_UNLOAD, alpha=0.7, mew=0)
        p3, r2, c = fit(d, s, 3)
        p2, _, _ = fit(d, s, 2)
        bz = np.linspace(x.raw_bz_median.min(), x.raw_bz_median.max(), 200)
        ax.plot(bz / 1000, np.polyval(p3, bz), color="black", lw=0.9)
        ax.plot(bz / 1000, np.polyval(p2, bz), color="black", lw=0.8, ls="--")
        ax.set_title(f"{s}   R² = {r2:.5f}", loc="left", fontweight="bold")
        ax.spines["right"].set_visible(False)
    for ax in axes[:, 0]:
        ax.set_ylabel("Reference force [N]")
    for ax in axes[-1, :]:
        ax.set_xlabel("Raw $B_z$ [×10³ counts]")
    h = [Line2D([], [], ls="", marker="o", ms=3, color=C_LOAD), Line2D([], [], ls="", marker="^", ms=3, color=C_UNLOAD),
         Line2D([], [], color="black", lw=0.9), Line2D([], [], color="black", lw=0.8, ls="--")]
    fig.legend(h, ["Loading steps (cycles 1–5)", "Unloading steps (cycles 1–5)",
                   "Cubic fit (cycle 3, loading) – used", "Second-order fit (cycle 3, loading)"],
               loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 0.01))
    save(fig, "FigureS9_Calibration_Curves")


def fig_s10(d):
    fig, axes = plt.subplots(1, 2, figsize=(180 * MM, 70 * MM), sharey=True)
    fig.subplots_adjust(left=0.08, right=0.99, top=0.9, bottom=0.17, wspace=0.08)
    for ax, deg, title in zip(axes, (2, 3), ("a  Second-order fit", "b  Cubic fit (used)")):
        ax.axhspan(-2, 2, color="#ececec", lw=0, zorder=0)
        ax.axhline(0, color="#444444", lw=0.6)
        for s in SENSORS:
            p, _, c = fit(d, s, deg)
            res = (np.polyval(p, c.raw_bz_median) - c.fz_median) * GRAM_PER_NEWTON
            ax.plot(c.fz_median, res, color=C_GROUP[s[0]], lw=0.8)
        ax.set_title(title, loc="left", fontweight="bold")
        ax.set_xlabel("Reference force [N]")
        ax.spines["right"].set_visible(False)
    axes[0].set_ylabel("Fit residual (fit − reference) [gf]")
    axes[1].legend([Line2D([], [], color=c, lw=1) for c in C_GROUP.values()],
                   ["A sensors", "B sensors", "C sensors"], loc="lower left", frameon=False)
    save(fig, "FigureS10_Residuals")


def fig_s11(d):
    fig, axes = plt.subplots(3, 4, figsize=(180 * MM, 150 * MM))
    fig.subplots_adjust(left=0.07, right=0.99, top=0.95, bottom=0.13, hspace=0.5, wspace=0.32)
    for ax, s in zip(axes.flat, SENSORS):
        x = d[d.position == s]
        for cyc in range(1, 6):
            bold = cyc == FIT_CYCLE
            for phase, col in (("Loading", C_LOAD), ("Unloading", C_UNLOAD)):
                c = x[(x.cycle_id == cyc) & (x["Load/Unload"] == phase)].sort_values("pz_step")
                ax.plot(c.pz_median, c.fz_median, color=col if bold else "#9a9a9a",
                        lw=1.1 if bold else 0.5, zorder=3 if bold else 2)
        ax.set_title(s, loc="left", fontweight="bold")
        ax.spines["right"].set_visible(False)
    for ax in axes[:, 0]:
        ax.set_ylabel("Reference force [N]")
    for ax in axes[-1, :]:
        ax.set_xlabel("Indentation [mm]")
    h = [Line2D([], [], color=C_LOAD, lw=1.1), Line2D([], [], color=C_UNLOAD, lw=1.1), Line2D([], [], color="#9a9a9a", lw=0.5)]
    fig.legend(h, ["Loading, cycle 3", "Unloading, cycle 3", "Cycles 1, 2, 4 and 5"],
               loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.01))
    save(fig, "FigureS11_Hysteresis")


def table_s4_check(d):
    """Print the cubic coefficients and R² so they can be compared with Table S4."""
    for s in SENSORS:
        p, r2, _ = fit(d, s, 3)
        print(s, " ".join(f"{v:.4e}" for v in p), f"R2={r2:.5f}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    d = load()
    fig_s9(d); fig_s10(d); fig_s11(d)
    table_s4_check(d)


if __name__ == "__main__":
    main()
