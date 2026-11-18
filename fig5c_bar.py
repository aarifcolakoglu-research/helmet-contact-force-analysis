"""
Figure 5c – per-sensor contact force at the four clinically anchored volumes.
Bars = mean across fittings, whiskers = ±1 SD (sample SD), label on every bar = (mean ± SD).
Set LABEL_MIN_GF = 0 to label zero bars as well.
Usage:  python fig5c_bar.py      -> outputs/Figure5c_bars.png, outputs/fig5c_values.csv
"""
import sys, os
import numpy as np
import matplotlib.pyplot as plt
from pipeline import (FONT_PT, STYLE, RAW_DIR, OUT_DIR, load_manifest, series_stats, summarise, age_label,
                      SENSORS, GRAM_PER_NEWTON)
VOLUMES = ["704", "732", "843", "860"]
COLORS = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]      # one-hue ramp: volume order
GROUP_NAMES = {"A": "Frontal (A)", "B": "Occipital (B)", "C": "Spheno-temporal (C)"}
YMAX_GF = 300          # top tick
YLIM_GF = 345          # head-room for the vertical labels
LEGEND_TITLE = True    # the composite figure turns this off (its panel title says it)
LABEL_MIN_GF = 0.5     # bars below this mean are left unlabelled (no contact)
# Expanded low-force band: below Y_SPLIT_GF the axis is stretched so that this band fills
# Y_SPLIT_FRAC of the axis height; above it the scale is linear. One continuous axis, no gap.
# Set Y_SPLIT_GF = None for the plain linear axis.
Y_SPLIT_GF = 5.0
Y_SPLIT_FRAC = 0.40


def _split_scale():
    """Forward/inverse functions of the piecewise-linear y scale (gf)."""
    b = Y_SPLIT_GF
    k = Y_SPLIT_FRAC * (YLIM_GF - b) / ((1 - Y_SPLIT_FRAC) * b)
    fwd = lambda y: np.where(np.asarray(y) <= b, np.asarray(y) * k, b * k + (np.asarray(y) - b))
    inv = lambda u: np.where(np.asarray(u) <= b * k, np.asarray(u) / k, b + (np.asarray(u) - b * k))
    return fwd, inv


def fmt(m, sd):
    """Same precision for mean and SD: integers when mean >= 10 gf, one decimal below."""
    d = 0 if abs(m) >= 10 else 1
    return f"({m:.{d}f} ± {sd:.{d}f})"

MM = 1 / 25.4
plt.rcParams.update(STYLE)


def draw_bars(ax, st, n):
    """Draw the grouped bars into an existing axes (used by fig5_compose.py)."""
    k = len(VOLUMES); bw = 0.19; x = np.arange(len(SENSORS)) * 1.0
    split = Y_SPLIT_GF is not None
    if split:
        fwd, inv = _split_scale()
        ax.set_yscale("function", functions=(fwd, inv))
        lab_y = lambda top: float(inv(fwd(top) + 4))           # same visual gap in both bands
    else:
        lab_y = lambda top: top + 3

    for j, (vol, col) in enumerate(zip(VOLUMES, COLORS)):
        s = st[st.volume == vol].set_index("sensor").reindex(SENSORS)
        xs = x + (j - (k - 1) / 2) * bw
        ax.bar(xs, s.mean_gf, bw * 0.88, color=col, zorder=3, label=age_label(vol))
        lo = np.minimum(s.sd_gf, s.mean_gf)            # whisker not below zero
        ax.errorbar(xs, s.mean_gf, [lo, s.sd_gf],
                    fmt="none", ecolor="#222222", elinewidth=0.6, capsize=1.3, capthick=0.6, zorder=4)
        for xi, m, sd in zip(xs, s.mean_gf, s.sd_gf):
            if m >= LABEL_MIN_GF:
                ax.text(xi, lab_y(m + sd), fmt(m, sd), rotation=90, ha="center", va="bottom",
                        fontsize=FONT_PT, color="#222222", zorder=5)

    # region separators + labels
    for b in (3.5, 7.5):
        ax.axvline(b, color="#999999", lw=0.6, ls=(0, (3, 3)), zorder=1)
    for gi, (g, name) in enumerate(GROUP_NAMES.items()):
        ax.text(gi * 4 + 1.5, YLIM_GF, name, ha="center", va="bottom", fontsize=FONT_PT, fontweight="bold", color="#444444")

    ax.set_xticks(x); ax.set_xticklabels(SENSORS, fontweight="bold")
    ax.set_xlim(-0.6, len(SENSORS) - 0.4)
    ax.set_ylim(0, YLIM_GF)
    if split:
        b = Y_SPLIT_GF
        ax.set_yticks(list(np.arange(0, b + 1e-9, 1)) + list(np.arange(50, YMAX_GF + 1, 50)))
        ax.set_yticks(list(np.arange(0.5, b, 1)) + list(np.arange(10, YMAX_GF + 1, 10)), minor=True)
        ax.axhspan(0, b, color="#f2f5fa", zorder=0)
        ax.axhline(b, color="#888888", lw=0.7, ls=(0, (4, 3)), zorder=2)
        ax.text(4.5, b * 0.96, f"0–{b:g} gf expanded;\nscale changes at {b:g} gf", ha="center", va="top",
                fontsize=FONT_PT, color="#555555", zorder=5)
    else:
        ax.set_yticks(np.arange(0, YMAX_GF + 1, 50))
        ax.set_yticks(np.arange(0, YMAX_GF + 1, 10), minor=True)
    ax.set_ylabel("Contact force [gf]")
    ax.grid(axis="y", which="major", color="#dddddd", lw=0.6, zorder=0)
    ax.tick_params(axis="x", length=0)

    ax2 = ax.twinx()                           # same quantity, second unit
    if split:                                  # same piecewise scale, expressed in newtons
        ax2.set_yscale("function", functions=(lambda yN: fwd(np.asarray(yN) * GRAM_PER_NEWTON),
                                              lambda u: inv(u) / GRAM_PER_NEWTON))
        ax2.set_ylim(0, YLIM_GF / GRAM_PER_NEWTON)
        ax2.set_yticks([0, 0.01, 0.02, 0.03, 0.04] + list(np.arange(0.5, 3.0 + 1e-9, 0.5)))
        from matplotlib.ticker import FuncFormatter
        ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.2f}" if 0 < v < 0.05 else f"{v:.1f}"))
    else:
        ax2.set_ylim(0, YLIM_GF / GRAM_PER_NEWTON)
        ax2.set_yticks(np.arange(0, 3.0 + 1e-9, 0.5))
    ax2.set_ylabel("Contact force [N]", rotation=270, labelpad=12)
    ax2.spines["top"].set_visible(False)

    ax.legend(ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.06), frameon=False,
              handlelength=1.2, columnspacing=1.6, title=(f"Mean ± SD, n = {n} fittings" if LEGEND_TITLE else None),
              title_fontsize=FONT_PT)
    return ax


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    man = load_manifest()
    long = series_stats(man, RAW_DIR)
    st = summarise(long)
    st.to_csv(os.path.join(OUT_DIR, "fig5c_values.csv"), index=False)
    n = len(man)

    fig, ax = plt.subplots(figsize=(180 * MM, 105 * MM))
    fig.subplots_adjust(left=0.075, right=0.925, top=0.84, bottom=0.08)
    draw_bars(ax, st, n)
    fig.savefig(os.path.join(OUT_DIR, "Figure5c_bars.png"), dpi=600)
    plt.close(fig)
    print("saved Figure 5c, n =", n)


if __name__ == "__main__":
    main()
