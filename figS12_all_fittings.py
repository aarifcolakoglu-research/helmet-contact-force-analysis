"""
Figure S12 – continuous force traces of all seven fittings (n = 7), drawn with the same
function as Figure 5a (fig5a_trace.draw_trace), one panel per fitting.
Usage: python figS12_all_fittings.py   -> outputs/FigureS12_Force_Traces_All_Fittings.png/.tif
"""
import os, sys
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pipeline import FONT_PT, STYLE, SENSORS, OUT_DIR, fitting_number, load_manifest, load_run, segments
import fig5a_trace as A

plt.rcParams.update(STYLE)
MM = 1 / 25.4
REPRESENTATIVE = "R3"            # Figure 5a (main text); see runs_manifest.csv


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    man = load_manifest()
    fig, axes = plt.subplots(4, 2, figsize=(180 * MM, 230 * MM))
    fig.subplots_adjust(left=0.07, right=0.93, top=0.955, bottom=0.04, hspace=0.75, wspace=0.42)
    for k, (_, row) in enumerate(man.iterrows()):
        ax = axes.flat[k]
        df = load_run(os.path.join(A.RAW_DIR, row["file"]))
        A.draw_trace(ax, df, segments(df), compact=True)
        ax.get_legend().remove()
        n = fitting_number(man, row["run_id"])
        title = f"Fitting {n}" + (" (representative, Figure 5a, main text)" if row["run_id"] == REPRESENTATIVE else "")
        ax.set_title(title, loc="left", fontweight="bold", pad=22)
    leg_ax = axes.flat[len(man)]
    leg_ax.set_axis_off()
    handles = [Line2D([], [], color=A.COLOR_MAP[s], lw=1.3) for s in SENSORS]
    # ncol=3 fills column by column: A1–A4 | B1–B4 | C1–C4
    leg_ax.legend(handles, SENSORS, ncol=3, loc="center", frameon=False,
                  title="Sensor (A frontal, B occipital, C spheno-temporal)", handlelength=1.6, columnspacing=1.6)
    for ax in axes.flat[len(man) + 1:]:
        ax.set_axis_off()
    base = os.path.join(OUT_DIR, "FigureS12_Force_Traces_All_Fittings")
    fig.savefig(base + ".png", dpi=600)
    fig.savefig(base + ".tif", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    print("saved", base)


if __name__ == "__main__":
    main()
