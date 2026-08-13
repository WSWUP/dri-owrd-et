#--------------------------------
# Name:    3_gap_fill.py
# Desc:    Gap fill months of missing EToF 
#           in the field summaries
# Python:  3.11
#--------------------------------

import argparse
import logging
import datetime
import pprint
import sys
from pathlib import Path
import json
import os
import pandas as pd
import re
from pandas.errors import SettingWithCopyWarning
import warnings
warnings.simplefilter(action='ignore', category=SettingWithCopyWarning)
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

dri_owrd_et_path = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(os.path.realpath(__file__)))))
sys.path.insert(0, os.path.join(dri_owrd_et_path, 'dri_owrd_et'))
sys.path.insert(0, dri_owrd_et_path)
import dri_owrd_et.inputs_post_processing as inputs
import dri_owrd_et.utils as utils

"""
Gap fills months of missing EToF data in the field boundary summaries using 
linear interpolation (1mo) and EToF climatologies (2+ mo).

"""

pp = pprint.PrettyPrinter(indent=4)


def main(ini_path=None):
    """ Gap filling of field-level monthly EToF

    Parameters
    ----------
    ini_path : str

    """

    logging.info('\nGap-filling months of missing EToF (Step 3)')

    # Read config file
    ini = inputs.read(ini_path)
    inputs.parse_section(ini, section='INPUTS')

    # root directory where this code repository is located on the local file system
    root_path = ini['INPUTS']['root_directory']
    
    # unique ID column/attribute for the field boundary dataset
    unique_id = ini['INPUTS']['unique_field_id']
    
    # start and end years
    start_yr = ini['INPUTS']['start_year']
    end_yr = ini['INPUTS']['end_year']

    # ET Demands effective precip variable name
    eff_ppt_var = 'P_rz'
    
    # table path
    table_path_main = os.path.join(root_path, 'tables')
    table_path = os.path.join(table_path_main, 'post_processing')
    table_path_ee = os.path.join(table_path_main, 'ee_exports')
    supp_path = os.path.join(root_path, "tables", "supplemental")

    # input path
    in_path = os.path.join(table_path, '3_pre_gap_filled')
    
    # output path
    out_path = os.path.join(table_path, '4_gap_filled')

    # List of bad geometries to remove
    df_bad = pd.read_csv(os.path.join(supp_path, "bad_geometry_list.csv"), index_col=unique_id)
    bad_list = list(df_bad.index)
        
    # list of years and list of years abbreviations
    yr_list = list(range(start_yr, end_yr+1))
    yr_abr_list = [int(str(yr)[2:]) for yr in yr_list]
    
    mm_vars = ["ETa", "ETDa", "ET_Reference", "PPT", "P_rz", "NIWR"]
    
    # ---------------------------
    # HELPER: Water year month order
    # ---------------------------
    def water_year_months(year):
        yr = int(str(year)[2:])
        prev = int(str(year - 1)[2:])
        return [
            ("11", prev),
            ("12", prev),
            ("01", yr), ("02", yr), ("03", yr),
            ("04", yr), ("05", yr), ("06", yr),
            ("07", yr), ("08", yr), ("09", yr),
            ("10", yr),
        ]
    
    def load_climatology(table_path_ee, yr_list):
        if yr_list[0] >= 2016:
            climo_start, climo_end = 2016, 2021
        elif yr_list[0] == 1985:
            climo_start, climo_end = 1984, 1991
        else:
            climo_start, climo_end = yr_list[0], yr_list[-1]
    
        climo_file = os.path.join(
            table_path_ee,
            f"or_field_summaries_water_year_shift_1mo_{climo_start}_{climo_end}_et_fraction_climo.csv",
        )
    
        df_c = pd.read_csv(climo_file, index_col=unique_id)

        # filter out bad geometries
        df_c = df_c.loc[~df_c.index.isin(bad_list)]
        
        df_c.columns = [
            "ETc_Fraction_11", "ETc_Fraction_12",
            "ETc_Fraction_01", "ETc_Fraction_02", "ETc_Fraction_03",
            "ETc_Fraction_04", "ETc_Fraction_05", "ETc_Fraction_06",
            "ETc_Fraction_07", "ETc_Fraction_08", "ETc_Fraction_09",
            "ETc_Fraction_10",
        ]
    
        return df_c
    
    def load_year_data(in_path, year):
        yr_abr = int(str(year)[2:])
    
        file_path = os.path.join(
            in_path,
            f"or_openet_etdemands_monthly_water_year_shift_1mo_{year}_pre_gapfill.csv.gz",
        )
    
        df = pd.read_csv(file_path, index_col=unique_id)
    
        df = df.rename(columns={
            "ACRES_FTR_GEOM": f"ACRES_FTR_GEOM_{yr_abr:02d}"
        })
    
        return df
    
    def build_master_dataframe(table_path_ee, in_path, yr_list):
        df_c = load_climatology(table_path_ee, yr_list)
    
        dfs = [df_c]
        for yr in yr_list:
            dfs.append(load_year_data(in_path, yr))
    
        return pd.concat(dfs, axis=1)
    
    def fill_final_october(df, yr_list):
        last_yr = int(str(yr_list[-1])[2:])
        col = f"ET_Fraction_10_{last_yr:02d}"
    
        if col in df.columns:
            df[col] = df[col].fillna(df["ETc_Fraction_10"])
    
        return df
    
    def interpolate_single_month_gaps(df):
        frac_cols = df.filter(regex="ET_Fraction").columns
    
        interp_vals = (
            df[frac_cols].shift(1, axis=1)
            .add(df[frac_cols].shift(-1, axis=1))
            / 2
        )
    
        df[frac_cols] = df[frac_cols].fillna(interp_vals)
    
        return df
    
    def fill_with_climatology(df, yr_list):
    
        for yr in yr_list:
            for m, y in water_year_months(yr):
                frac_col = f"ET_Fraction_{m}_{y:02d}"
                climo_col = f"ETc_Fraction_{m}"
    
                if frac_col in df.columns:
                    df[frac_col] = df[frac_col].fillna(df[climo_col])
    
        return df

    def interpolate_month_gaps_climo_missing(df):
        frac_cols = df.filter(regex="ET_Fraction").columns

        interp_vals = df[frac_cols].interpolate(method='linear', axis=1)
    
        df[frac_cols] = df[frac_cols].fillna(interp_vals)
    
        return df
        
    def backfill_eta(df, yr_list):
    
        for yr in yr_list:
            for m, y in water_year_months(yr):
    
                eta = f"ETa_{m}_{y:02d}"
                frac = f"ET_Fraction_{m}_{y:02d}"
                eto = f"ET_Reference_{m}_{y:02d}"
    
                if eta in df.columns:
                    df[eta] = df[eta].fillna(df[frac] * df[eto])
    
        return df
    
    def convert_mm_to_inches(df, mm_vars):
    
        for col in df.columns:
            for v in mm_vars:
                if col.startswith(v + "_") and not col.endswith("_in"):
                    df[f"{col}_in"] = df[col] / 25.4
    
        return df
    
    def calculate_volumes(df, yr_list, eff_ppt_var):
    
        for yr in yr_list:
            yr_abr = int(str(yr)[2:])
            acres_col = f"ACRES_FTR_GEOM_{yr_abr:02d}"
    
            for m, y in water_year_months(yr):
    
                for var in ["ETa", "ETDa", "ET_Reference", "PPT", eff_ppt_var, 'IRR_CU', 'NIWR']:
    
                    depth_col = f"{var}_{m}_{y:02d}_in"
    
                    if depth_col in df.columns:
                        if var == 'ETa':
                            vol_col = f"ET_VOLUME_{m}_{y:02d}_acft"
                        elif var == 'ET_Reference':
                            vol_col = f"ETO_VOLUME_{m}_{y:02d}_acft"
                        elif var == eff_ppt_var:
                            vol_col = f"EFF_VOLUME_{m}_{y:02d}_acft"
                        else:
                            vol_col = f"{var}_VOLUME_{m}_{y:02d}_acft"
                        df[vol_col] = (df[depth_col] / 12) * df[acres_col]
                        
                    # IRR_CU is calculated from ET and EFF volumes after they are made
                    else:
                        vol_col = f"{var}_VOLUME_{m}_{y:02d}_acft"
                        df[vol_col] = df[f"ET_VOLUME_{m}_{y:02d}_acft"] - df[f"EFF_VOLUME_{m}_{y:02d}_acft"]
                        
    
        return df
    
    def run_pipeline(table_path_ee, in_path, yr_list):
    
        df = build_master_dataframe(table_path_ee, in_path, yr_list)
    
        df = fill_final_october(df, yr_list)
        df = interpolate_single_month_gaps(df)
        df = fill_with_climatology(df, yr_list)
        df = interpolate_month_gaps_climo_missing(df) # additional etof fillna b/c 1984-1991 climo values for fields were null
        df = backfill_eta(df, yr_list)
        df = convert_mm_to_inches(df, mm_vars)
        df = calculate_volumes(df, yr_list, eff_ppt_var)

        return df
    
    yr_list = list(range(start_yr, end_yr + 1))
    
    df_final = run_pipeline(
        table_path_ee=table_path_ee,
        in_path=in_path,
        yr_list=yr_list,
    )

    def parse_month_year(col):
    
        match = re.search(r'_(\d{2})_(\d{2})(?:_|$)', col)
        if not match:
            return None
    
        month = int(match.group(1))
        yy = int(match.group(2))
    
        # Convert 2-digit year correctly
        if yy >= 80:
            year = 1900 + yy
        else:
            year = 2000 + yy
    
        return month, year
        
    def parse_annual_year(col):
    
        # First try 4-digit year at end
        match4 = re.search(r'_(\d{4})$', col)
        if match4:
            return int(match4.group(1))
    
        # Then try 2-digit year before optional suffix
        match2 = re.search(r'_(\d{2})(?:_|$)', col)
        if match2:
            yy = int(match2.group(1))
    
            if yy >= 80:
                return 1900 + yy
            else:
                return 2000 + yy
    
        return None

    def columns_for_water_year(df, water_year):
    
        cols_keep = []
    
        for col in df.columns:
    
            # -------------------------------------------------
            #  Monthly columns
            # -------------------------------------------------
            parsed_month = parse_month_year(col)
    
            if parsed_month is not None:
                month, year = parsed_month
    
                # Keep only water-year months
                if (
                    (year == water_year - 1 and month in [11, 12]) or
                    (year == water_year and 1 <= month <= 10)
                ):
    
                    # Remove millimeter monthly columns
                    # (those that end exactly in _MM_YY)
                    if (re.search(r'_\d{2}_\d{2}$', col) and 'ET_Fraction' not in col):
                        continue
    
                    # ✅ Keep inch + acft versions
                    cols_keep.append(col)
    
                continue
    
            # -------------------------------------------------
            # Annual columns (2-digit or 4-digit year)
            # -------------------------------------------------
            annual_year = parse_annual_year(col)
    
            if annual_year is not None:
                if annual_year == water_year:
                    cols_keep.append(col)
                continue
    
            # -------------------------------------------------
            # Acreage column
            # -------------------------------------------------
            if col.startswith("ACRES_FTR_GEOM_"):
                if col.endswith(str(water_year)[-2:]):
                    cols_keep.append(col)
                continue
    
            # -------------------------------------------------
            # 4️⃣ Static columns (no year)
            # -------------------------------------------------
            cols_keep.append(col)
    
        return cols_keep

    def reorder_volume_columns(df, water_year):
        """Reorder volumetric columns by variable and water-year month order (Nov–Oct)"""
        
        # Water year month order: Nov-Dec previous year, Jan–Oct current year
        wy_months = [11, 12] + list(range(1, 11))
        
        # Identify volume columns
        vol_cols = [c for c in df.columns if "_VOLUME_" in c]
        
        # Parse variable and month from volume column names
        parsed = []
        for c in vol_cols:
            # Example format: ETa_VOLUME_11_85_acft
            m = re.search(r'^(.*)_VOLUME_(\d{2})_(\d{2})_acft$', c)
            if m:
                var = m.group(1)
                month = int(m.group(2))
                year = int("20" + m.group(3)) if int(m.group(3)) < 50 else int("19" + m.group(3))
                parsed.append((var, month, year, c))
        
        # Group by variable, then sort columns within each variable by water-year month order
        vol_sorted = []
        for var in sorted(set([p[0] for p in parsed])):  # maintain consistent variable order
            var_cols = [p for p in parsed if p[0] == var]
            # sort by water-year month order
            var_cols_sorted = sorted(
                var_cols,
                key=lambda x: wy_months.index(x[1]) if x[1] in wy_months else 99
            )
            vol_sorted.extend([x[3] for x in var_cols_sorted])
        
        # All other columns (non-volume)
        other_cols = [c for c in df.columns if c not in vol_sorted]
        
        return df[other_cols + vol_sorted]
        
    def split_and_save_by_water_year(df_final, yr_list, out_path):
    
        for wy in yr_list:
    
            cols_keep = columns_for_water_year(df_final, wy)
    
            df_wy = df_final[cols_keep].copy()

            df_wy = df_wy.loc[:, ~df_wy.columns.duplicated()].copy()
            
            df_wy = reorder_volume_columns(df_wy, wy)

            out_file = os.path.join(
                out_path,
                f"or_openet_etdemands_monthly_water_year_shift_1mo_{wy}_gap_filled.csv.gz"
            )
    
            # df_wy.to_csv(out_file)
            df_wy.to_csv(out_file, compression='gzip')
    
            logging.info(f"Saved water year {wy}")
    
    # ---------------------------------
    # Remove climatology columns and duplicate columns
    # ---------------------------------
    df_final = df_final.drop(
        columns=[c for c in df_final.columns if c.startswith("ETc_")],
        errors="ignore"
    )
    df_final = df_final.loc[:, ~df_final.columns.duplicated()]
    
    # ---------------------------------
    # Split and write individual water-year files
    # ---------------------------------
    split_and_save_by_water_year(
        df_final=df_final,
        yr_list=yr_list,
        out_path=out_path
    )

        
def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='EToF Gap Filling (Step 3)',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    parser.add_argument(
        '-i', '--ini', type=utils.arg_valid_file,
        help='Input file', metavar='FILE')
    
    parser.add_argument(
        '-d', '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action='store_const', dest='loglevel')
    
    args = parser.parse_args()

    if args.ini and os.path.isfile(os.path.abspath(args.ini)):
        args.ini = os.path.abspath(args.ini)
    else:
        args.ini = utils.get_ini_path(os.getcwd())
        
    return args


if __name__ == '__main__':
    
    args = arg_parse()

    logging.basicConfig(level=args.loglevel, format='%(message)s')
    logging.getLogger('googleapiclient').setLevel(logging.ERROR)
    logging.info('\n{}'.format('#' * 80))
    log_f = '{:<20s} {}'
    logging.info(log_f.format(
        'Start Time:', datetime.datetime.now().isoformat(' ')))
    logging.info(log_f.format('Current Directory:', os.getcwd()))
    logging.info(log_f.format('Script:', os.path.basename(sys.argv[0])))
    
    main(ini_path=args.ini)