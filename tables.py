"""
Tables and in-text values reported in the manuscript.

Writes to outputs/:
  sensor_forces.csv       per sensor and volume step (incl. 900 mL and the final 704 mL hold):
                          mean, SD, min, max across fittings in gf and N, and CV (%)
  regional_shares_by_run.csv
                          per run and volume: summed force of each anatomical group as a
                          percentage of the summed force of all 12 sensors
  regional_shares.csv     mean, min and max of those shares across fittings
  peak_force.csv          highest single-site sample up to and including the 860 mL hold
and prints a short summary.
    python tables.py
"""
import os

import pandas as pd

from pipeline import (GRAM_PER_NEWTON, GROUPS, GROUP_NAMES, OUT_DIR, SENSORS, fitting_number,
                      load_manifest, load_run_by_id, segments, series_stats, summarise)

VOLUME_ORDER = ["704", "732", "843", "860", "900", "704_end"]
NO_CONTACT_GF = 0.5      # means below this are reported as no measurable contact


def sensor_table(long):
    st = summarise(long)
    st["cv_pct"] = (st.sd_gf / st.mean_gf * 100).where(st.mean_gf >= NO_CONTACT_GF)
    st["volume"] = pd.Categorical(st.volume, VOLUME_ORDER, ordered=True)
    st["sensor"] = pd.Categorical(st.sensor, SENSORS, ordered=True)
    return st.sort_values(["volume", "sensor"]).reset_index(drop=True)


def regional_shares(long):
    wide = long.pivot_table(index=["run_id", "volume"], columns="sensor", values="gf")
    total = wide[SENSORS].sum(axis=1)
    by_run = pd.DataFrame({GROUP_NAMES[g]: wide[s].sum(axis=1) / total * 100 for g, s in GROUPS.items()})
    by_run = by_run[total > 0].reset_index()
    summary = (by_run.melt(id_vars=["run_id", "volume"], var_name="group", value_name="share_pct")
               .groupby(["volume", "group"])["share_pct"].agg(["mean", "min", "max"]).reset_index())
    return by_run, summary


def peak_force(man):
    """Highest single sample of any sensor before the 900 mL extension starts."""
    rows = []
    for rid in man.run_id:
        df = load_run_by_id(man, rid)
        seg = segments(df)
        t_ext = seg.loc[seg.label == "860-900", "t0"].min()
        pre = df[df.t_s < t_ext]
        i = pre.gf.idxmax()
        rows.append({"run_id": rid, "sensor": pre.at[i, "short_id"], "volume": pre.at[i, "volume"],
                     "peak_gf": pre.at[i, "gf"], "peak_N": pre.at[i, "gf"] / GRAM_PER_NEWTON})
    return pd.DataFrame(rows)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    man = load_manifest()
    long = series_stats(man)

    st = sensor_table(long)
    st.to_csv(os.path.join(OUT_DIR, "sensor_forces.csv"), index=False)
    by_run, shares = regional_shares(long)
    by_run.to_csv(os.path.join(OUT_DIR, "regional_shares_by_run.csv"), index=False)
    shares.to_csv(os.path.join(OUT_DIR, "regional_shares.csv"), index=False)
    pk = peak_force(man)
    pk.to_csv(os.path.join(OUT_DIR, "peak_force.csv"), index=False)

    print(f"n = {len(man)} fittings: " + ", ".join(f"Fitting {f} = {r}" for f, r in zip(man.fitting, man.run_id)) + "\n")
    for vol in ["704", "732", "843", "860", "900"]:
        s = st[(st.volume == vol) & (st.mean_gf >= NO_CONTACT_GF)]
        print(f"{vol} mL: " + "; ".join(f"{r.sensor} {r.mean_gf:.1f} ± {r.sd_gf:.1f} gf" for r in s.itertuples()))
    print("\nRegional share of summed sensor force (%; mean [min-max]):")
    for vol in ["704", "843", "860"]:
        s = shares[shares.volume == vol]
        print(f"  {vol} mL: " + "; ".join(f"{r.group} {r.mean:.0f} [{r.min:.0f}-{r.max:.0f}]" for r in s.itertuples()))
    top = pk.loc[pk.peak_gf.idxmax()]
    print(f"\nHighest single-site force up to 860 mL: {top.peak_gf:.0f} gf ({top.peak_N:.2f} N), "
          f"{top.sensor}, Fitting {fitting_number(man, top.run_id)} ({top.run_id})")
    print(f"Outputs written to {OUT_DIR}")


if __name__ == "__main__":
    main()
