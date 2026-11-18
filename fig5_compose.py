"""
Figure 5 – full composite (a: representative trace, b: sensor locations, c: bars).
Panels a and c are drawn natively; panel b is a text-free render of the instrumented
helmet (assets/sensor_locations.png) with the sensor labels drawn as text.
Also writes panels a, b and c as separate images.
Usage: python fig5_compose.py [RUN_ID]   -> outputs/Figure5_composite_<RUN_ID>.png/.tiff
"""
import sys, os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pipeline import FONT_PT, STYLE, fitting_number, load_manifest, series_stats, summarise
import fig5a_trace as A
import fig5c_bar as C
from pipeline import HERE, OUT_DIR

RUN_ID = sys.argv[1] if len(sys.argv) > 1 else None
MM = 1 / 25.4
W, H = 180, 190       # mm
LETTER_COLOR = "#C00000"
FRAME_COLOR = "#9a9a9a"


RENDER_NO_TEXT = os.path.join(HERE, "assets", "sensor_locations.png")
CROP_NO_TEXT = (40, 110, 666, 668)          # x0, y0, x1, y1 in the 672 x 720 render
# label anchor points (render pixel coords), found from the labelled version of the same render
LABEL_XY = {"B3": (306, 136), "B2": (436, 174), "B4": (165, 180), "B1": (358, 287),
            "C2": (496, 308), "C3": (102, 326), "C1": (523, 367), "C4": (75, 385),
            "A1": (361, 486), "A4": (483, 547), "A2": (155, 590), "A3": (330, 635)}
LABEL_GAP = 40      # px (render coords) between the helmet and the Posterior/Anterior labels
GROUP_COLOR = {"A": "#006400", "B": "#00008B", "C": "#8B0000"}     # = A1/B1/C1 trace colours in panel A


def draw_panel_b_vector(ax):
    """Text-free render + all annotations drawn as vector text, coloured by sensor group."""
    im = Image.open(RENDER_NO_TEXT).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    x0, y0, x1, y1 = CROP_NO_TEXT
    img = np.asarray(bg.convert("RGB").crop(CROP_NO_TEXT))
    ax.imshow(img, interpolation="none", extent=(x0, x1, y1, y0))
    ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_axis_off()
    for s, (x, y) in LABEL_XY.items():
        ax.text(x, y, s, color=GROUP_COLOR[s[0]], fontsize=FONT_PT, fontweight="bold", ha="center", va="center",
                zorder=4, bbox=dict(facecolor="white", edgecolor="none", pad=0.4, alpha=0.75))
    ax.text(478, 497, "Craniotomy", color="#2e8b2e", fontsize=FONT_PT, style="italic", ha="left", va="center")
    ax.annotate("Sensor hub", xy=(352, 596), xytext=(440, 624), fontsize=FONT_PT, color="#222222",
                ha="left", va="center",
                arrowprops=dict(arrowstyle="-|>", color="#222222", lw=0.8, shrinkA=0, shrinkB=2))
    ax.text((x0 + x1) / 2, y0 - LABEL_GAP, "Posterior", ha="center", va="bottom", fontsize=FONT_PT, color="#333333")
    ax.text((x0 + x1) / 2, y1 + LABEL_GAP, "Anterior", ha="center", va="top", fontsize=FONT_PT, color="#333333")


def frame(fig, x0, y0, x1, y1, letter, title=""):
    """Rounded frame around a panel + its letter in the frame's top-left corner (all aligned)."""
    from matplotlib.patches import FancyBboxPatch
    fig.patches.append(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=0.008",
                                      transform=fig.transFigure, fill=False, edgecolor=FRAME_COLOR, lw=0.8))
    fig.text(x0 + 0.012, y1 - 0.01, letter, fontsize=FONT_PT, fontweight="bold", color=LETTER_COLOR, va="top", ha="left")
    if title:                                  # same baseline as the letter
        fig.text(x0 + 0.026, y1 - 0.01, title, fontsize=FONT_PT, fontweight="bold", color="#333333", va="top", ha="left")


def panel_label(fig, ax, letter, dx=-0.06, dy=1.02):
    ax.text(dx, dy, letter, transform=ax.transAxes, fontsize=FONT_PT, fontweight="bold", va="bottom", ha="left")


def _save(fig, base):
    for ext in ("png", "tiff"):
        kw = {"dpi": DPI}
        if ext == "tiff":
            kw["pil_kwargs"] = {"compression": "tiff_lzw"}
        fig.savefig(f"{base}.{ext}", **kw)
    plt.close(fig)


DPI = 600


def export_panels(rid, df, seg, st, n):
    """Panels A, B and C as separate images (no frame/letter), each >= 2100 px wide."""
    fA = plt.figure(figsize=(180 * MM, 95 * MM))
    axA = fA.add_axes([0.075, 0.12, 0.85, 0.74])
    A.draw_trace(axA, df, seg, legend_top=True)
    _save(fA, os.path.join(OUT_DIR, f"Figure5a_panel_{rid}"))

    fB = plt.figure(figsize=(92 * MM, 102 * MM))          # 92 mm @ 600 dpi = 2173 px
    axB = fB.add_axes([0.03, 0.08, 0.94, 0.84])
    draw_panel_b_vector(axB)
    _save(fB, os.path.join(OUT_DIR, "Figure5b_panel"))

    fC = plt.figure(figsize=(180 * MM, 105 * MM))
    axC = fC.add_axes([0.075, 0.07, 0.85, 0.74])
    C.LEGEND_TITLE = True
    C.draw_bars(axC, st, n)
    C.LEGEND_TITLE = False
    _save(fC, os.path.join(OUT_DIR, "Figure5c_panel"))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    fig = plt.figure(figsize=(W * MM, H * MM))

    # ---- A: trace --------------------------------------------------------
    rid, row, df, seg = A.load_representative(RUN_ID)
    n = len(load_manifest())
    TOP, MID, SPLIT = 0.99, 0.545, 0.715       # frame geometry (figure fractions)
    frame(fig, 0.01, MID + 0.01, SPLIT - 0.005, TOP, "a", f"Representative force trace (Fitting {fitting_number(load_manifest(), rid)})")
    frame(fig, SPLIT + 0.005, MID + 0.01, 0.99, TOP, "b", "Sensor locations")
    frame(fig, 0.01, 0.01, 0.99, MID, "c", f"Contact force at clinical time points (mean ± SD, n = {n})")
    axA = fig.add_axes([0.075, 0.61, 0.565, 0.30])
    A.draw_trace(axA, df, seg, legend_top=True)

    # ---- B: sensor locations --------------------------------------------
    axB = fig.add_axes([0.722, 0.60, 0.262, 0.30])
    draw_panel_b_vector(axB)

    # ---- C: bars ---------------------------------------------------------
    man = load_manifest()
    st = summarise(series_stats(man, A.RAW_DIR))
    C.LEGEND_TITLE = False
    axC = fig.add_axes([0.085, 0.045, 0.83, 0.40])
    C.draw_bars(axC, st, len(man))

    export_panels(rid, df, seg, st, len(man))
    base = os.path.join(OUT_DIR, f"Figure5_composite_{rid}")
    for ext in ("png", "tiff"):
        kw = {"dpi": 600}
        if ext == "tiff":
            kw["pil_kwargs"] = {"compression": "tiff_lzw"}
        fig.savefig(f"{base}.{ext}", **kw)
    plt.close(fig)
    print("saved", base)


if __name__ == "__main__":
    main()
