#--------------------------------
# Name:    2_et_demands_join.py
# Desc:    Join monthly ET Demands ETc and Prz
#           to field summaries
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

dri_owrd_et_path = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(os.path.realpath(__file__)))))
sys.path.insert(0, os.path.join(dri_owrd_et_path, 'dri_owrd_et'))
sys.path.insert(0, dri_owrd_et_path)
import dri_owrd_et.inputs as inputs
import dri_owrd_et.utils as utils

"""
This tool joins ET Demands Potential Crop ET (ETc) and Effective Precipitation (Prz) to 
field summaries.

Data is joined by matching the field's crop type (CDL) and gridMET cell with the ET Demands
simulation.

"""

pp = pprint.PrettyPrinter(indent=4)


def main(ini_path=None):
    """ CSV joining between ET Demands and the field summaries based on crop type and gridMET cell

    Parameters
    ----------
    ini_path : str

    """

    logging.info('\nConcatenating all field-level summary tables')

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
    
    # flag to export data for an individual field (True) or the entire field boundary dataset (False)
    single_field_flag = ini['INPUTS']['test_flag']

    # table path
    table_path = os.path.join(root_path, 'tables', 'post_processing')
    
    # CDL - ET Demands crosswalk file
    in_path = os.path.join(table_path, '2_for_et_demands_join')
    
    # ET Demands monthly data path
    etd_path = os.path.join(in_path, 'et_demands')
    
    # output path
    out_path = os.path.join(table_path, '3_pre_gap_filled')
    
    # list of years based on start/end parameters
    year_list = list(range(start_yr, end_yr+1))
    
    # ET Demands variables
    variable_map = {
        "ETDa": "ETact",
        # "P_eft": "P_eft",
        "P_rz": "P_rz",
        "NIWR": "NIWR",
    }
    
    # vectorized crosswalk
    cross_df = pd.read_csv(
        os.path.join(in_path, "OR_unique_cdl_etdemands_crosswalk_model_setup_1979_2024.csv")
    )
    
    cross_df["etd_no"] = (
        cross_df["etd_no"]
        .astype(str)
        .str.split(",")
        .str[0]
        .astype(int)
    )
    
    cross_dict = dict(zip(cross_df.cdl_no, cross_df.etd_no))
    
    # ET Demands loader
    def load_etd(grid_id, crop_code, year):
        csv_path = os.path.join(etd_path, f"{grid_id}_crop_{crop_code}.csv")
        pq_path = csv_path.replace(".csv", ".parquet")
    
        def read_csv_known_good():
            try:
                df = pd.read_csv(
                    csv_path,
                    header=1,
                    index_col="Date",
                    parse_dates=True,a
                )
                return df.reset_index()
            except Exception:
                pass
    
            raise ValueError(f"Failed to read ET Demands file: {csv_path}")
    
        # --- read parquet safely
        if os.path.exists(pq_path):
            try:
                df = pd.read_parquet(pq_path)
    
                # schema validation
                if not {"Date", "Year", "Month"}.issubset(df.columns):
                    raise ValueError("Invalid parquet schema")
    
            except Exception:
                print(f"Rebuilding parquet for {os.path.basename(csv_path)}")
                df = read_csv_known_good()
                df["Year"] = df["Date"].dt.year
                df["Month"] = df["Date"].dt.month
                df.to_parquet(pq_path, index=False)
    
        else:
            df = read_csv_known_good()
            df["Year"] = df["Date"].dt.year
            df["Month"] = df["Date"].dt.month
            df.to_parquet(pq_path, index=False)
    
        # --- filter years and months
        df = df[
        ((df['Date'].dt.year == year - 1) & (df['Date'].dt.month >= 11)) |
        ((df['Date'].dt.year == year) & (df['Date'].dt.month <= 10))
    ]
    
        # --- attach identifiers
        df["GRIDMET_ID"] = int(grid_id)
        df["ETD_CROP"] = str(crop_code).zfill(2)
    
        return df
    
    
    for year in year_list:
        t0 = perf_counter()
        print(f"\nProcessing {year}")
    
        # --- Load field table
        df_fields = pd.read_csv(
            os.path.join(
                in_path,
                 f'or_field_summaries_water_year_shift_1mo_{year}_pre_et_demands.csv',
            ),
            index_col=unique_id,
        )
    
        # --- Map CDL → ETD crop
        df_fields["ETD_CROP"] = (
            df_fields[f"CDL_{year}"]
            .round()
            .map(cross_dict)
            .astype("Int64")
            .astype(str)
            .str.zfill(2)
        )
    
        df_fields["ETD_CROP_STR"] = df_fields["ETD_CROP"].astype(str).str.zfill(2)
        df_fields[f"ETD_{str(year)[2:]}"] = df_fields["ETD_CROP_STR"]
    
        # --- Unique ET Demands files
        combos = (
            df_fields
            .dropna(subset=["ETD_CROP"])
            [["GRIDMET_ID", "ETD_CROP_STR"]]
            .drop_duplicates()
            .itertuples(index=False)
        )
    
        combos = list(combos)
        print(f"Unique ETD files: {len(combos)}")
    
        # parallel ET Demands ingestion
        etd_tables = Parallel(n_jobs=-1)(
            delayed(load_etd)(int(g), c, year)
            for g, c in tqdm(combos, desc="Loading ET Demands")
        )
    
        etd_all = pd.concat(etd_tables, ignore_index=True)
    
        # reshape ET Demands
        etd_long = (
            etd_all
            .melt(
                id_vars=["GRIDMET_ID", "ETD_CROP", "Year", "Month"],
                value_vars=list(variable_map.values()),
                var_name="variable",
                value_name="value",
            )
        )
    
        etd_long["var"] = etd_long["variable"].map(
            {v: k for k, v in variable_map.items()}
        )
    
        etd_long["col"] = (
            etd_long["var"]
            + "_"
            + etd_long["Month"].astype(str).str.zfill(2)
            + "_"
            + etd_long["Year"].astype(str).str[2:]
        )
    
        etd_wide = (
            etd_long
            .pivot_table(
                index=["GRIDMET_ID", "ETD_CROP"],
                columns="col",
                values="value",
                aggfunc="first",
            )
            .reset_index()
        )
    
        # single merge
        df_fields = df_fields.reset_index().merge(
            etd_wide,
            how="left",
            on=["GRIDMET_ID", "ETD_CROP"],
        )
    
        variable_list = ['ETDa', 'P_rz', 'NIWR']
        prev_year_months = [11, 12]
        curr_year_months = list(range(1, 11))
        
        # All columns that were added from ET Demands merge
        etd_cols = [c for c in df_fields.columns if any(c.startswith(v + "_") for v in variable_list)]
    
        # Build the desired order for the ETD columns
        etd_cols_ordered = []
        for var in variable_list:
            for m in prev_year_months:
                col_name = f"{var}_{str(m).zfill(2)}_{str(year-1)[2:]}"
                if col_name in etd_cols:
                    etd_cols_ordered.append(col_name)
            for m in curr_year_months:
                col_name = f"{var}_{str(m).zfill(2)}_{str(year)[2:]}"
                if col_name in etd_cols:
                    etd_cols_ordered.append(col_name)
        
        # Original columns without ETD columns
        original_cols = [c for c in df_fields.columns if c not in etd_cols]
        
        # Final column order: original first, ETD columns reordered last
        final_cols = original_cols + etd_cols_ordered
        df_fields = df_fields[final_cols]
    
        # remove string column
        df_fields = df_fields.drop(columns=['ETD_CROP','ETD_CROP_STR'])
        
        # export and benchmark
        out_file = f'or_openet_etdemands_monthly_water_year_shift_1mo_{year}_pre_gapfill.csv'
    
        df_fields.to_csv(os.path.join(out_path, out_file), index=False)
    
        t1 = perf_counter()
        print(f"Finished {year} in {t1 - t0:0.1f} seconds")

    
def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='ET Demands to Field Summary Crop Type/Grid Cell Join (Step 2)',
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