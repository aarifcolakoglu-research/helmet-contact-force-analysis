"""
Shared processing for Sensor Tracking Studio force logs.

Each log row carries the operator's volume label ("704", "704-732", "732", ...).
A run is split into contiguous label SEGMENTS:
  * a segment whose label has no "-" is a stable hold at that volume,
  * the FIRST segment is always the pre-loading 704 mL baseline,
  * the LAST segment (the return to 704 mL after unloading) is kept apart as "704_end".
For each run and sensor, the force at a volume is the mean of all samples in the
first stable segment carrying that label (Methods, force data processing).
"""
from __future__ import annotations

import logging
import os

import numpy as np
import pandas as pd

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "data", "raw")
MANIFEST = os.path.join(HERE, "data", "runs_manifest.csv")
OUT_DIR = os.path.join(HERE, "outputs")

GRAM_PER_NEWTON = 1000 / 9.80665          # 1 N = 101.9716 gf
SENSORS = ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4", "C1", "C2", "C3", "C4"]
GROUPS = {"A": SENSORS[0:4], "B": SENSORS[4:8], "C": SENSORS[8:12]}
GROUP_NAMES = {"A": "Frontal", "B": "Occipital", "C": "Spheno-temporal"}

# One typeface and one font size in every figure (journal requirement);
# emphasis is by weight or colour only.
FONT_PT = 6.5
STYLE = {
    "font.family": ["Arial", "Liberation Sans", "DejaVu Sans"],
    "font.size": FONT_PT, "axes.labelsize": FONT_PT, "axes.titlesize": FONT_PT,
    "xtick.labelsize": FONT_PT, "ytick.labelsize": FONT_PT, "legend.fontsize": FONT_PT,
    "legend.title_fontsize": FONT_PT, "figure.titlesize": FONT_PT,
    "axes.spines.top": False, "axes.linewidth": 0.8, "pdf.fonttype": 42, "svg.fonttype": "none",
}

# Volume steps of the protocol: label -> (volume-equivalent age in days, description)
VOLUME_STEPS = {
    "704": (77, "surgery day"),
    "732": (90, "Helmet 1 start"),
    "843": (160, "Helmet 1 end"),
    "860": (175, "extended end of Helmet 1 (CT)"),
    "900": (212, "extension (Supporting Information)"),
}
MAIN_VOLS = ["704", "732", "843", "860"]


def age_label(vol: str, two_line: bool = False) -> str:
    """Age first, volume in brackets, e.g. '77 d (704 mL)'."""
    d = VOLUME_STEPS[vol][0]
    return f"{d} d\n({vol} mL)" if two_line else f"{d} d ({vol} mL)"


def load_manifest(path: str = MANIFEST) -> pd.DataFrame:
    """The seven fittings analysed in the paper (Fittings 1-7), in chronological order."""
    m = pd.read_csv(path, dtype=str).fillna("")
    return m.reset_index(drop=True)


def fitting_number(manifest: pd.DataFrame, run_id: str) -> int:
    """Fitting number used in the paper (1-7), taken from the manifest."""
    return int(manifest.loc[manifest.run_id == run_id, "fitting"].iloc[0])


def load_run(path: str) -> pd.DataFrame:
    """Read one raw log and add time (s), force in gf and a segment id."""
    df = pd.read_csv(path, dtype={"volume": str})
    df["force_n"] = pd.to_numeric(df["force_n"], errors="coerce")
    df = df.dropna(subset=["force_n"]).reset_index(drop=True)
    t = pd.to_datetime(df["timestamp"], format="%H:%M:%S.%f")
    df["t_s"] = (t - t.iloc[0]).dt.total_seconds()
    df["gf"] = df["force_n"] * GRAM_PER_NEWTON
    df["segment"] = (df["volume"] != df["volume"].shift()).cumsum()
    return df


def load_run_by_id(manifest: pd.DataFrame, run_id: str, raw_dir: str = RAW_DIR) -> pd.DataFrame:
    row = manifest[manifest.run_id == run_id].iloc[0]
    return load_run(os.path.join(raw_dir, row["file"]))


def segments(df: pd.DataFrame) -> pd.DataFrame:
    """One row per contiguous label segment: label, start/end time, stable flag."""
    g = df.groupby("segment").agg(label=("volume", "first"), t0=("t_s", "first"), t1=("t_s", "last"))
    g["stable"] = ~g["label"].str.contains("-")
    return g


def stable_means(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Mean force (gf) per sensor for each stable volume; "704" = baseline, "704_end" = final hold."""
    seg = segments(df)
    out: dict[str, np.ndarray] = {}
    first, last = seg.index[0], seg.index[-1]
    for sid, row in seg[seg["stable"]].iterrows():
        key = row["label"]
        if sid == first:
            key = "704"
        elif sid == last:
            key = "704_end"
        if key in out:                      # keep the first occurrence of a label
            continue
        part = df[df["segment"] == sid]
        out[key] = part.groupby("short_id")["gf"].mean().reindex(SENSORS).fillna(0).values
    return out


def series_stats(manifest: pd.DataFrame, raw_dir: str = RAW_DIR) -> pd.DataFrame:
    """Long table: run_id, volume, sensor, gf."""
    rows = []
    for _, r in manifest.iterrows():
        means = stable_means(load_run(os.path.join(raw_dir, r["file"])))
        for vol, vec in means.items():
            for s, v in zip(SENSORS, vec):
                rows.append({"run_id": r["run_id"], "volume": vol, "sensor": s, "gf": v})
    return pd.DataFrame(rows)


def summarise(long: pd.DataFrame) -> pd.DataFrame:
    """Mean / sample SD (ddof = 1) / min / max across fittings per (volume, sensor), in gf and N."""
    g = (long.groupby(["volume", "sensor"])["gf"]
         .agg(mean_gf="mean", sd_gf="std", min_gf="min", max_gf="max", n="count").reset_index())
    g["sd_gf"] = g["sd_gf"].fillna(0)
    for c in ["mean", "sd", "min", "max"]:
        g[f"{c}_N"] = g[f"{c}_gf"] / GRAM_PER_NEWTON
    return g
