"""
Figure 5a – continuous force trace of one representative fitting.
Representative fitting = the run closest (RMSE over the 704/732/843/860 mL means of all
sensors) to the series mean; for the published data this is R3 (Fitting 3).
Usage: python fig5a_trace.py [RUN_ID]      -> outputs/Figure5a_trace_<RUN_ID>.png
"""
import sys, os
import numpy as np
import matplotlib.transforms as mtransforms
import matplotlib.pyplot as plt
from pipeline import (FONT_PT, STYLE, RAW_DIR, OUT_DIR, MAIN_VOLS, load_manifest, load_run, segments,
                      series_stats, age_label, SENSORS, GRAM_PER_NEWTON)

RUN_ID = sys.argv[1] if len(sys.argv) > 1 else None
YMAX_GF = 300

# Sensor colours kept from the lab's existing figures (A green, B blue, C red)
COLOR_MAP = {"A1": "#006400", "A2": "#228B22", "A3": "#32CD32", "A4": "#8FBC8F",
             "B1": "#00008B", "B2": "#0000CD", "B3": "#4169E1", "B4": "#87CEFA",
             "C1": "#8B0000", "C2": "#DC143C", "C3": "#FF4500", "C4": "#E9967A"}

MM = 1 / 25.4
plt.rcParams.update(STYLE)


def pick_representative(man):
    long = series_stats(man, RAW_DIR)
    long = long[long.volume.isin(MAIN_VOLS)]
    wide = long.pivot_table(index=["volume", "sensor"], columns="run_id", values="gf")
    rmse = ((wide.sub(wide.mean(axis=1), axis=0)) ** 2).mean() ** 0.5
    return rmse.idxmin(), rmse.sort_values()


def draw_trace(ax, df, seg, legend_ncol=12, legend_y=-0.17, legend_inside=False, legend_top=False,
               compact=False):
    """Draw the representative trace into an existing axes (used by fig5_compose.py and figS12)."""

    # phase shading: stable holds of the main interval
    hdr = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
    ylim_gf = YMAX_GF * (1.12 if legend_top else 1.0)   # band above 300 gf for a one-row legend
    labelled = set()
    t_ext = None
    last_xf, last_y = None, 1.01
    for sid, s in seg.iterrows():
        if s.stable and s.label in MAIN_VOLS and s.label not in labelled:
            ax.axvspan(s.t0, s.t1, color="#eef2f7", zorder=0, lw=0)
            d = age_label(s.label).split(" (")[0]            # "77 d"
            xc = (s.t0 + s.t1) / 2
            if compact:                                     # narrow panels: days only, staggered if crowded
                xf = xc / df.t_s.iloc[-1]
                y = 1.09 if (last_xf is not None and xf - last_xf < 0.1 and last_y < 1.05) else 1.01
                ax.text(xc, y, d, transform=hdr, ha="center", va="bottom", fontsize=FONT_PT, color="#333333")
                last_xf, last_y = xf, y
            else:
                ax.text(xc, 1.01, f"{d}\n{s.label} mL", transform=hdr,
                        ha="center", va="bottom", fontsize=FONT_PT, color="#333333", linespacing=1.1)
            labelled.add(s.label)
        if s.label == "860-900" and t_ext is None:
            t_ext = s.t0
    if t_ext is not None:                      # beyond the Helmet 1 interval
        ax.axvspan(t_ext, df.t_s.iloc[-1], facecolor="#f3f3f3", zorder=0, lw=0, hatch="////", edgecolor="#e6e6e6")
        d9 = age_label("900").split(" (")[0]   # same two-line header as the main steps, in grey
        ext_txt = f"{d9} extension" if compact else f"{d9}\n900 mL extension and unloading"
        ax.text((t_ext + df.t_s.iloc[-1]) / 2, 1.01, ext_txt, transform=hdr,
                ha="center", va="bottom", fontsize=FONT_PT, color="#777777", linespacing=1.1)

    handles = {}
    labels = []
    for s in SENSORS:
        sub = df[df.short_id == s]
        peak = sub.gf.max()
        lw = 1.3 if peak > 5 else 0.8
        h, = ax.plot(sub.t_s, sub.gf, color=COLOR_MAP[s], lw=lw, zorder=3)
        handles[s] = h
        if peak > 5:                          # direct label where the trace is readable
            s860 = seg[seg.label == "860"].iloc[0]
            s900 = seg[seg.label == "900"].iloc[0]
            m860 = sub[(sub.t_s >= s860.t0) & (sub.t_s <= s860.t1)].gf.mean()
            if m860 >= 8:                     # engaged within Helmet 1 interval
                tx, y = s860.t1 + 2, m860
            else:                             # engages only in the 900 ml extension
                tx, y = s900.t1 + 2, sub[(sub.t_s >= s900.t0) & (sub.t_s <= s900.t1)].gf.mean()
            labels.append([tx, y, s])

    # de-overlap labels that share an x position (min 14 gf apart)
    for tx in {l[0] for l in labels}:
        grp = sorted([l for l in labels if l[0] == tx], key=lambda l: l[1])
        for a, b in zip(grp, grp[1:]):
            if b[1] - a[1] < 14:
                b[1] = a[1] + 14
    for tx, y, s in labels:
        ax.text(tx, y, s, color=COLOR_MAP[s], fontsize=FONT_PT, fontweight="bold", va="center", ha="left",
                zorder=5, bbox=dict(facecolor="white", edgecolor="none", pad=0.3, alpha=0.8))

    t_end = df.t_s.iloc[-1]
    ax.set_xlim(0, t_end * (1.16 if legend_inside else 1.0))   # head-room on the right for an inside legend
    ax.set_ylim(0, ylim_gf); ax.set_yticks(np.arange(0, YMAX_GF + 1, 50))
    ax.set_yticks(np.arange(0, YMAX_GF + 1, 10), minor=True)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Contact force [gf]")
    ax.grid(axis="y", color="#dddddd", lw=0.6, zorder=1)
    ax2 = ax.twinx()
    ax2.set_ylim(0, ylim_gf / GRAM_PER_NEWTON)
    ax2.set_yticks(np.arange(0, YMAX_GF / GRAM_PER_NEWTON + 1e-9, 0.5))
    ax2.set_ylabel("Contact force [N]", rotation=270, labelpad=12)
    ax2.spines["top"].set_visible(False)

    group_order = SENSORS                       # A1..A4, B1..B4, C1..C4
    if legend_top:
        # one row inside the plot, in the empty band above 300 gf, grouped A | B | C
        ax.legend([handles[s] for s in group_order], group_order, ncol=12, loc="upper center",
                  bbox_to_anchor=(0.5, 1.0), frameon=False, fontsize=FONT_PT, handlelength=1.0,
                  handletextpad=0.3, columnspacing=0.75, borderaxespad=0.3)
    elif legend_inside:
        # 3 columns = groups A | B | C (legend fills column by column)
        ax.legend([handles[s] for s in group_order], group_order, ncol=3, loc="upper right",
                  bbox_to_anchor=(1.0, 1.0), frameon=True, framealpha=0.92, edgecolor="#cccccc",
                  fontsize=FONT_PT, handlelength=1.1, handletextpad=0.4, columnspacing=0.8,
                  borderpad=0.4, labelspacing=0.25)
    else:
        # one row per group when laid out 4 wide: pass items row-major -> column-major order
        order = [group_order[r * 4 + c] for c in range(4) for r in range(3)]
        ax.legend([handles[s] for s in order], order, ncol=4, loc="upper center",
                  bbox_to_anchor=(0.5, legend_y), frameon=False, handlelength=1.4, columnspacing=1.0)
    return ax


def load_representative(run_id=None):
    man = load_manifest()
    if run_id is None:
        run_id, _ = pick_representative(man)
    row = man[man.run_id == run_id].iloc[0]
    df = load_run(os.path.join(RAW_DIR, row["file"]))
    return run_id, row, df, segments(df)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    man = load_manifest()
    rid = RUN_ID
    if rid is None:
        rid, ranking = pick_representative(man)
        print("RMSE to series mean (gf):\n", ranking.round(1).to_string())
    row = man[man.run_id == rid].iloc[0]
    df = load_run(os.path.join(RAW_DIR, row["file"]))
    seg = segments(df)

    fig, ax = plt.subplots(figsize=(180 * MM, 90 * MM))
    fig.subplots_adjust(left=0.075, right=0.925, top=0.84, bottom=0.2)
    draw_trace(ax, df, seg)
    fig.savefig(os.path.join(OUT_DIR, f"Figure5a_trace_{rid}.png"), dpi=600)
    plt.close(fig)
    print("saved", rid, row["file"])


if __name__ == "__main__":
    main()
