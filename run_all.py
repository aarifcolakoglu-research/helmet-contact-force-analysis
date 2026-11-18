"""Reproduce every output of this repository: python run_all.py

Writes to outputs/: the force tables (tables.py), Figure 5 and its panels, Figures S9-S11
(calibration; with the cubic coefficients printed for comparison with Table S4) and
Figure S12 (all seven fittings).
"""
import fig5_compose
import fig5c_bar
import figS9_S11_calibration
import figS12_all_fittings
import tables

if __name__ == "__main__":
    tables.main()
    fig5c_bar.main()            # also writes fig5c_values.csv (values behind Figure 5c)
    fig5_compose.main()
    figS9_S11_calibration.main()
    figS12_all_fittings.main()
