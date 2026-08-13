#--------------------------------
# Name:    4_soil_moisture_carry_forward.py
# Desc:    Carry forward surplus soil moisture (i.e., ET < Prz) 
#           for all fields/months and recompute consumptive use
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
import numpy as np
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

dri_owrd_et_path = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(os.path.realpath(__file__)))))
sys.path.insert(0, os.path.join(dri_owrd_et_path, 'dri_owrd_et'))
sys.path.insert(0, dri_owrd_et_path)
import dri_owrd_et.inputs_post_processing as inputs
import dri_owrd_et.utils as utils

"""
Carry forward excess soil moisture (i.e., when ET < Prz) into the 
next month for all fields and months. Recommend running from the 
start of the study period all the way to the end of the study 
period if all individual files have been prepared 
in the previous step (i.e., 1985-2025).

"""

pp = pprint.PrettyPrinter(indent=4)


def main(ini_path=None):
    """ Soil Moisture Carry Forward

    Parameters
    ----------
    ini_path : str

    """

    logging.info('\nField-Level Soil Moisture Carry Forward Routine')

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

    # table path
    table_path_main = os.path.join(root_path, 'tables')
    table_path = os.path.join(table_path_main, 'post_processing')
    table_path_ee = os.path.join(table_path_main, 'ee_exports')
    supp_path = os.path.join(table_path_main, 'supplemental')
    
    in_path = os.path.join(table_path, '4_gap_filled')
    
    out_path = os.path.join(table_path, '5_field_geodatabase')
    
    # list of years based on start/end year parameters
    year_list = list(range(start_yr, end_yr+1))
    if not year_list[0] == 1985:
        logging.error(
            '\nERROR: Soil Moisture Carry Forward should begin at the study period start (i.e., 1985)')
        sys.exit()
    
    def compute_month(df, mo, cal_year, ws_prev):
    
        mo_str = f"{mo:02d}"
        yr_str = str(cal_year)[2:]
    
        irr_col = f'IRR_CU_VOLUME_{mo_str}_{yr_str}_acft'
        et_col  = f'ET_VOLUME_{mo_str}_{yr_str}_acft'
    
        ws_col      = f'WS_{mo_str}_{yr_str}_acft'
        ws_c_col    = f'WS_C_{mo_str}_{yr_str}_acft'
        irr_adj_col = f'IRR_CU_VOLUMEadj_{mo_str}_{yr_str}_acft'
        eff_col     = f'EFF_VOLUMEadj_{mo_str}_{yr_str}_acft'
        aw_col      = f'AW_{mo_str}_{yr_str}_acft'
        
        dperc_col = f'DPerc_add_{mo_str}_{yr_str}_acft'
        
        # Monthly deficit only (negative values)
        df[ws_col] = df[irr_col].clip(upper=0)

        # -------------------------------------------------------
        # AVAILABLE STORED SOIL WATER
        # -------------------------------------------------------
    
        # Convert negative storage to positive available water
        storage_available = np.abs(ws_prev)
    
        # Water demand remaining after soil-water contribution
        df[irr_adj_col] = np.maximum(
            df[irr_col] - storage_available,
            0
        )
        
        # -------------------------------------------------------
        # UPDATE SOIL STORAGE
        # -------------------------------------------------------
    
        # Raw updated storage:
        # previous storage + current month surplus
        ws_raw = (ws_prev + df[irr_col]).clip(upper=0)
    
        # Storage cap (negative internally)
        ws_cap = -df['PAW_acft']
    
        # Excess beyond storage capacity
        df[dperc_col] = (ws_cap - ws_raw).clip(lower=0)
    
        # Final capped soil storage
        df[ws_c_col] = np.maximum(ws_raw, ws_cap)
    
        # -------------------------------------------------------
        # ADJUSTED EFFECTIVE PRECIP
        # -------------------------------------------------------
    
        df[eff_col] = df[et_col] - df[irr_adj_col]
    
        # -------------------------------------------------------
        # APPLIED WATER
        # -------------------------------------------------------
    
        df[aw_col] = np.where(
            df['IRR_EFF'] > 0,
            df[irr_adj_col] / df['IRR_EFF'],
            np.nan
        ).clip(min=0)
    
        # -------------------------------------------------------
        # RETURN STORAGE STATE FOR NEXT MONTH
        # -------------------------------------------------------
            
        return df[ws_c_col]
    
    def soil_moisture_carry_forward(
        in_path,
        out_path,
        year_list,
        unique_id
    ):
    
        water_year_months = [11,12,1,2,3,4,5,6,7,8,9,10]
        ws_carry = None
    
        for i, wy in enumerate(year_list):

            filename = f'or_openet_etdemands_monthly_water_year_shift_1mo_{wy}_gap_filled.csv.gz'
            
            in_file  = os.path.join(in_path,  filename)
    
            df = pd.read_csv(in_file, index_col=unique_id)

            # temporary addition for sensitivity testing
            df_awc = pd.read_csv(os.path.join(table_path_ee, 'or_field_summaries_awc_attributes.csv'), index_col=unique_id)
            # List of bad geometries to remove
            df_bad = pd.read_csv(os.path.join(supp_path, "bad_geometry_list.csv"), index_col=unique_id)
            bad_list = list(df_bad.index)
            df_awc = df_awc.loc[~df_awc.index.isin(bad_list)]
            
            df = pd.concat([df, df_awc], axis=1)
            # Create field-specific cap for surplus soil moisture carried forward when ET < PRZ (assuming 1.5m ~ 5ft rooting depth) - Plant Available Water (PAW)
            rooting_depth_m = 2
            df['rooting_depth_ft'] = rooting_depth_m * 3.281
            df['PAW_ft'] = df['AWC'] * df['rooting_depth_ft']
            df['PAW_acft'] = df['PAW_ft'] * df[f'ACRES_FTR_GEOM_{str(wy)[2:]}']

            out_file = os.path.join(out_path, filename.replace('gap_filled', "final"))
            
            if i == 0:
                ws_carry = pd.Series(0, index=df.index)
    
            for mo in water_year_months:
                cal_year = wy - 1 if mo in [11,12] else wy
                ws_carry = compute_month(df, mo, cal_year, ws_carry)
    
            # -------------------------------------------------------
            # CLEANUP BEFORE EXPORT
            # -------------------------------------------------------
    
            # 1 Drop WS_ columns but keep WS_C_
            ws_only_cols = [
                c for c in df.columns
                if c.startswith("WS_") and not c.startswith("WS_C_")
            ]
            df.drop(columns=ws_only_cols, inplace=True)
    
            # 2️ Flip sign on WS_C_ columns (make deficits positive)
            ws_c_cols = [c for c in df.columns if c.startswith("WS_C_")]
            df[ws_c_cols] = df[ws_c_cols] * -1
    
            # Fill remaining NaNs
            df.fillna(0, inplace=True)
    
            df.reset_index(inplace=True)

            # if not os.path.isfile(out_file):
            # df.to_csv(out_file, index=False)
            df.to_csv(out_file, index=False, compression='gzip')
    
            print(f"Exported WY{wy}")
    
    soil_moisture_carry_forward(
        in_path=in_path,
        out_path=out_path,
        year_list=year_list,
        unique_id=unique_id
    )

    
def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='Field-Level Soil Moisture Carry Forward (Step 4)',
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