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

dri_owrd_et_path = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(os.path.realpath(__file__)))))
sys.path.insert(0, os.path.join(dri_owrd_et_path, 'dri_owrd_et'))
sys.path.insert(0, dri_owrd_et_path)
import dri_owrd_et.inputs as inputs
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

    logging.info('\nGap-filling months of missing EToF')

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

    # ET Demands effective precip variable name
    eff_ppt_var = 'P_rz'
    
    # table path
    table_path_main = os.path.join(root_path, 'tables')
    table_path = os.path.join(table_path_main, 'post_processing')
    table_path_ee = os.path.join(table_path_main, 'ee_exports')
    
    # input path
    in_path = os.path.join(table_path, '3_pre_gap_filled')
    
    # output path
    out_path = os.path.join(table_path, '4_gap_filled')
    
    # list of years and list of years abbreviations
    yr_list = list(range(start_yr, end_yr+1))
    yr_abr_list = [int(str(yr)[2:]) for yr in yr_list]
    
    # EToF Climatology  dataframe to gap-fill if multiple adjacent-months missing (also first and last values)
    try:
        if (yr_list[0] == 1985 and yr_list[-1] == 1991):
            df_c = pd.read_csv(os.path.join(table_path_ee, f'or_field_summaries_water_year_shift_1mo_1984_{yr_list[-1]}_et_fraction_climo.csv'), index_col=unique_id)
        elif (yr_list[0] == 2016 and yr_list[-1] == 2022):
            df_c = pd.read_csv(os.path.join(table_path_ee, f'or_field_summaries_water_year_shift_1mo_{yr_list[0]}_2021_et_fraction_climo.csv'), index_col=unique_id)
        elif (yr_list[0] == 2016 and yr_list[-1] == 2023):
            df_c = pd.read_csv(os.path.join(table_path_ee, f'or_field_summaries_water_year_shift_1mo_{yr_list[0]}_2021_et_fraction_climo.csv'), index_col=unique_id)
        elif (yr_list[0] == 2016 and yr_list[-1] == 2024):
            df_c = pd.read_csv(os.path.join(table_path_ee, f'or_field_summaries_water_year_shift_1mo_{yr_list[0]}_2021_et_fraction_climo.csv'), index_col=unique_id)
        else:
            df_c = pd.read_csv(os.path.join(table_path_ee, f'or_field_summaries_water_year_shift_1mo_{yr_list[0]}_{yr_list[-1]}_et_fraction_climo.csv'), index_col=unique_id)
    
        # rename columns for climo file
        df_c.columns = ['ETc_Fraction_11','ETc_Fraction_12','ETc_Fraction_01','ETc_Fraction_02','ETc_Fraction_03','ETc_Fraction_04','ETc_Fraction_05','ETc_Fraction_06',
                        'ETc_Fraction_07','ETc_Fraction_08','ETc_Fraction_09','ETc_Fraction_10']
    
        # read all years into dataframes in order to concatenate and gap fill properly
        
        if (yr_list[0] == 1985 and yr_list[-1] == 1991):
            df1 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_1985_pre_gapfill.csv'), index_col=unique_id)
            df1 = df1.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[0]:02d}'})
            df2 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_1986_pre_gapfill.csv'), index_col=unique_id)
            df2 = df2.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[1]:02d}'})
            df3 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_1987_pre_gapfill.csv'), index_col=unique_id)
            df3 = df3.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[2]:02d}'})
            df4 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_1988_pre_gapfill.csv'), index_col=unique_id)
            df4 = df4.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[3]:02d}'})
            df5 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_1989_pre_gapfill.csv'), index_col=unique_id)
            df5 = df5.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[4]:02d}'})
            df6 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_1990_pre_gapfill.csv'), index_col=unique_id)
            df6 = df6.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[5]:02d}'})
            df7 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_1991_pre_gapfill.csv'), index_col=unique_id)
            df7 = df7.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[6]:02d}'})
        
            df = pd.concat([df_c, df1, df2, df3, df4, df5, df6, df7], axis=1)
        elif (yr_list[0] == 2016 and yr_list[-1] == 2022):
            df1 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2016_pre_gapfill.csv'), index_col=unique_id)
            df1 = df1.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[0]:02d}'})
            df2 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2017_pre_gapfill.csv'), index_col=unique_id)
            df2 = df2.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[1]:02d}'})
            df3 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2018_pre_gapfill.csv'), index_col=unique_id)
            df3 = df3.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[2]:02d}'})
            df4 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2019_pre_gapfill.csv'), index_col=unique_id)
            df4 = df4.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[3]:02d}'})
            df5 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2020_pre_gapfill.csv'), index_col=unique_id)
            df5 = df5.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[4]:02d}'})
            df6 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2021_pre_gapfill.csv'), index_col=unique_id)
            df6 = df6.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[5]:02d}'})
            df7 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2022_pre_gapfill.csv'), index_col=unique_id)
            df7 = df7.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[6]:02d}'})
        
            df = pd.concat([df_c, df1, df2, df3, df4, df5, df6, df7], axis=1)
        elif (yr_list[0] == 2016 and yr_list[-1] == 2023):
            df1 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2016_pre_gapfill.csv'), index_col=unique_id)
            df1 = df1.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[0]:02d}'})
            df2 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2017_pre_gapfill.csv'), index_col=unique_id)
            df2 = df2.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[1]:02d}'})
            df3 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2018_pre_gapfill.csv'), index_col=unique_id)
            df3 = df3.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[2]:02d}'})
            df4 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2019_pre_gapfill.csv'), index_col=unique_id)
            df4 = df4.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[3]:02d}'})
            df5 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2020_pre_gapfill.csv'), index_col=unique_id)
            df5 = df5.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[4]:02d}'})
            df6 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2021_pre_gapfill.csv'), index_col=unique_id)
            df6 = df6.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[5]:02d}'})
            df7 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2022_pre_gapfill.csv'), index_col=unique_id)
            df7 = df7.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[6]:02d}'})
            df8 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2023_pre_gapfill.csv'), index_col=unique_id)
            df8 = df8.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[7]:02d}'})
        
            df = pd.concat([df_c, df1, df2, df3, df4, df5, df6, df7, df8], axis=1)
        elif (yr_list[0] == 2016 and yr_list[-1] == 2024):
            df1 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2016_pre_gapfill.csv'), index_col=unique_id)
            df1 = df1.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[0]:02d}'})
            df2 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2017_pre_gapfill.csv'), index_col=unique_id)
            df2 = df2.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[1]:02d}'})
            df3 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2018_pre_gapfill.csv'), index_col=unique_id)
            df3 = df3.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[2]:02d}'})
            df4 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2019_pre_gapfill.csv'), index_col=unique_id)
            df4 = df4.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[3]:02d}'})
            df5 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2020_pre_gapfill.csv'), index_col=unique_id)
            df5 = df5.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[4]:02d}'})
            df6 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2021_pre_gapfill.csv'), index_col=unique_id)
            df6 = df6.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[5]:02d}'})
            df7 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2022_pre_gapfill.csv'), index_col=unique_id)
            df7 = df7.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[6]:02d}'})
            df8 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2023_pre_gapfill.csv'), index_col=unique_id)
            df8 = df8.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[7]:02d}'})
            df9 = pd.read_csv(os.path.join(in_path, 'or_openet_etdemands_monthly_water_year_shift_1mo_2024_pre_gapfill.csv'), index_col=unique_id)
            df9 = df9.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[8]:02d}'})
        
            df = pd.concat([df_c, df1, df2, df3, df4, df5, df6, df7, df8, df9], axis=1)
        else:
            df1 = pd.read_csv(os.path.join(in_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[0]}_pre_gapfill.csv'), index_col=unique_id)
            df1 = df1.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[0]:02d}'})
            df2 = pd.read_csv(os.path.join(in_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[1]}_pre_gapfill.csv'), index_col=unique_id)
            df2 = df2.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[1]:02d}'})
            df3 = pd.read_csv(os.path.join(in_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[2]}_pre_gapfill.csv'), index_col=unique_id)
            df3 = df3.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[2]:02d}'})
            df4 = pd.read_csv(os.path.join(in_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[3]}_pre_gapfill.csv'), index_col=unique_id)
            df4 = df4.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[3]:02d}'})
            df5 = pd.read_csv(os.path.join(in_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[4]}_pre_gapfill.csv'), index_col=unique_id)
            df5 = df5.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[4]:02d}'})
            df6 = pd.read_csv(os.path.join(in_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[5]}_pre_gapfill.csv'), index_col=unique_id)
            df6 = df6.rename(columns={'ACRES_FTR_GEOM': f'ACRES_FTR_GEOM_{yr_abr_list[5]:02d}'})
    
    except Exception as e:
        print(e)
        
        df = pd.concat([df_c, df1, df2, df3, df4, df5, df6], axis=1)
    
    # Last month of period needs to be filled with climo before linear interpolation (first month does not since interp doesn't catch it)
    df[f'ET_Fraction_10_{yr_abr_list[-1]:02d}'] = df[f'ET_Fraction_10_{yr_abr_list[-1]:02d}'].fillna(df['ETc_Fraction_10'])
    
    # linearly interpolate isolated monthly nans/gaps 
    # df_t = df.loc[:,df.columns.str.contains('ET_Fraction')]
    # df.loc[:,df.columns.str.contains('ET_Fraction')] = df.loc[:,df.columns.str.contains('ET_Fraction')].interpolate(method='linear',limit=1,limit_area='inside',axis=1)
    
    # linearly interpolate isolated monthly nans/gaps only, not consecutive nans
    fval = (df.loc[:, df.columns.str.contains('ET_Fraction')].shift(1, axis=1).add(df.loc[:, df.columns.str.contains('ET_Fraction')].shift(-1, axis=1)) / 2)
    df.loc[:, df.columns.str.contains('ET_Fraction')] = df.loc[:, df.columns.str.contains('ET_Fraction')].fillna(value=fval, axis=1)
    
    # fill non-isolated (i.e., consecutive/adjacent) monthly nans/gaps with the climo values explicitly
    for yr in yr_abr_list:
        print(f'gap filling {yr}')
    
        # fill the rest of the nans (consecutive nans) with the climatologies
        # the year 2000 has to have this special condition for subtracting 1 from 0 (2000 actual year value)
        if yr == 0:
            df['ET_Fraction_11_99'] = df['ET_Fraction_11_99'].fillna(df['ETc_Fraction_11'])
            df['ET_Fraction_12_99'] = df['ET_Fraction_12_99'].fillna(df['ETc_Fraction_12'])
        else:
            df[f'ET_Fraction_11_{yr-1:02d}'] = df[f'ET_Fraction_11_{yr-1:02d}'].fillna(df['ETc_Fraction_11'])
            df[f'ET_Fraction_12_{yr-1:02d}'] = df[f'ET_Fraction_12_{yr-1:02d}'].fillna(df['ETc_Fraction_12'])
        df[f'ET_Fraction_01_{yr:02d}'] = df[f'ET_Fraction_01_{yr:02d}'].fillna(df['ETc_Fraction_01'])
        df[f'ET_Fraction_02_{yr:02d}'] = df[f'ET_Fraction_02_{yr:02d}'].fillna(df['ETc_Fraction_02'])
        df[f'ET_Fraction_03_{yr:02d}'] = df[f'ET_Fraction_03_{yr:02d}'].fillna(df['ETc_Fraction_03'])
        df[f'ET_Fraction_04_{yr:02d}'] = df[f'ET_Fraction_04_{yr:02d}'].fillna(df['ETc_Fraction_04'])
        df[f'ET_Fraction_05_{yr:02d}'] = df[f'ET_Fraction_05_{yr:02d}'].fillna(df['ETc_Fraction_05'])
        df[f'ET_Fraction_06_{yr:02d}'] = df[f'ET_Fraction_06_{yr:02d}'].fillna(df['ETc_Fraction_06'])
        df[f'ET_Fraction_07_{yr:02d}'] = df[f'ET_Fraction_07_{yr:02d}'].fillna(df['ETc_Fraction_07'])
        df[f'ET_Fraction_08_{yr:02d}'] = df[f'ET_Fraction_08_{yr:02d}'].fillna(df['ETc_Fraction_08'])
        df[f'ET_Fraction_09_{yr:02d}'] = df[f'ET_Fraction_09_{yr:02d}'].fillna(df['ETc_Fraction_09'])
        df[f'ET_Fraction_10_{yr:02d}'] = df[f'ET_Fraction_10_{yr:02d}'].fillna(df['ETc_Fraction_10'])
    
        # some fields' EToF climos for Dec 1984 were missing so need to interpolate those months after above gap-filling
        if yr == 85:
            df.loc[:,df.columns.str.contains('ET_Fraction')] = df.loc[:,df.columns.str.contains('ET_Fraction')].interpolate(method='linear', axis=1)        
    
        # fill nans in actual et with the gap-filled et fraction * et reference
        if yr == 0:
            df[f'ETa_11_99'] = df[f'ETa_11_99'].fillna(df[f'ET_Fraction_11_99'] * df[f'ET_Reference_11_99'])
            df[f'ETa_12_99'] = df[f'ETa_12_99'].fillna(df[f'ET_Fraction_12_99'] * df[f'ET_Reference_12_99'])
        else:  
            df[f'ETa_11_{yr-1:02d}'] = df[f'ETa_11_{yr-1:02d}'].fillna(df[f'ET_Fraction_11_{yr-1:02d}'] * df[f'ET_Reference_11_{yr-1:02d}'])
            df[f'ETa_12_{yr-1:02d}'] = df[f'ETa_12_{yr-1:02d}'].fillna(df[f'ET_Fraction_12_{yr-1:02d}'] * df[f'ET_Reference_12_{yr-1:02d}'])
        df[f'ETa_01_{yr:02d}'] = df[f'ETa_01_{yr:02d}'].fillna(df[f'ET_Fraction_01_{yr:02d}'] * df[f'ET_Reference_01_{yr:02d}'])
        df[f'ETa_02_{yr:02d}'] = df[f'ETa_02_{yr:02d}'].fillna(df[f'ET_Fraction_02_{yr:02d}'] * df[f'ET_Reference_02_{yr:02d}'])
        df[f'ETa_03_{yr:02d}'] = df[f'ETa_03_{yr:02d}'].fillna(df[f'ET_Fraction_03_{yr:02d}'] * df[f'ET_Reference_03_{yr:02d}'])
        df[f'ETa_04_{yr:02d}'] = df[f'ETa_04_{yr:02d}'].fillna(df[f'ET_Fraction_04_{yr:02d}'] * df[f'ET_Reference_04_{yr:02d}'])
        df[f'ETa_05_{yr:02d}'] = df[f'ETa_05_{yr:02d}'].fillna(df[f'ET_Fraction_05_{yr:02d}'] * df[f'ET_Reference_05_{yr:02d}'])
        df[f'ETa_06_{yr:02d}'] = df[f'ETa_06_{yr:02d}'].fillna(df[f'ET_Fraction_06_{yr:02d}'] * df[f'ET_Reference_06_{yr:02d}'])
        df[f'ETa_07_{yr:02d}'] = df[f'ETa_07_{yr:02d}'].fillna(df[f'ET_Fraction_07_{yr:02d}'] * df[f'ET_Reference_07_{yr:02d}'])
        df[f'ETa_08_{yr:02d}'] = df[f'ETa_08_{yr:02d}'].fillna(df[f'ET_Fraction_08_{yr:02d}'] * df[f'ET_Reference_08_{yr:02d}'])
        df[f'ETa_09_{yr:02d}'] = df[f'ETa_09_{yr:02d}'].fillna(df[f'ET_Fraction_09_{yr:02d}'] * df[f'ET_Reference_09_{yr:02d}'])
        df[f'ETa_10_{yr:02d}'] = df[f'ETa_10_{yr:02d}'].fillna(df[f'ET_Fraction_10_{yr:02d}'] * df[f'ET_Reference_10_{yr:02d}'])
        
        # convert units from mm to inches 
        if yr == 0:
            df[f'ETa_11_99_in'] = df[f'ETa_11_99'] / 25.4
            df[f'ETa_12_99_in'] = df[f'ETa_12_99'] / 25.4
        else:
            df[f'ETa_11_{yr-1:02d}_in'] = df[f'ETa_11_{yr-1:02d}'] / 25.4
            df[f'ETa_12_{yr-1:02d}_in'] = df[f'ETa_12_{yr-1:02d}'] / 25.4
        df[f'ETa_01_{yr:02d}_in'] = df[f'ETa_01_{yr:02d}'] / 25.4
        df[f'ETa_02_{yr:02d}_in'] = df[f'ETa_02_{yr:02d}'] / 25.4
        df[f'ETa_03_{yr:02d}_in'] = df[f'ETa_03_{yr:02d}'] / 25.4
        df[f'ETa_04_{yr:02d}_in'] = df[f'ETa_04_{yr:02d}'] / 25.4
        df[f'ETa_05_{yr:02d}_in'] = df[f'ETa_05_{yr:02d}'] / 25.4
        df[f'ETa_06_{yr:02d}_in'] = df[f'ETa_06_{yr:02d}'] / 25.4
        df[f'ETa_07_{yr:02d}_in'] = df[f'ETa_07_{yr:02d}'] / 25.4
        df[f'ETa_08_{yr:02d}_in'] = df[f'ETa_08_{yr:02d}'] / 25.4
        df[f'ETa_09_{yr:02d}_in'] = df[f'ETa_09_{yr:02d}'] / 25.4
        df[f'ETa_10_{yr:02d}_in'] = df[f'ETa_10_{yr:02d}'] / 25.4
        
        # convert units from mm to inches 
        if yr == 0:
            df[f'ETDa_11_99_in'] = df[f'ETDa_11_99'] / 25.4
            df[f'ETDa_12_99_in'] = df[f'ETDa_12_99'] / 25.4
        else:
            df[f'ETDa_11_{yr-1:02d}_in'] = df[f'ETDa_11_{yr-1:02d}'] / 25.4
            df[f'ETDa_12_{yr-1:02d}_in'] = df[f'ETDa_12_{yr-1:02d}'] / 25.4
        df[f'ETDa_01_{yr:02d}_in'] = df[f'ETDa_01_{yr:02d}'] / 25.4
        df[f'ETDa_02_{yr:02d}_in'] = df[f'ETDa_02_{yr:02d}'] / 25.4
        df[f'ETDa_03_{yr:02d}_in'] = df[f'ETDa_03_{yr:02d}'] / 25.4
        df[f'ETDa_04_{yr:02d}_in'] = df[f'ETDa_04_{yr:02d}'] / 25.4
        df[f'ETDa_05_{yr:02d}_in'] = df[f'ETDa_05_{yr:02d}'] / 25.4
        df[f'ETDa_06_{yr:02d}_in'] = df[f'ETDa_06_{yr:02d}'] / 25.4
        df[f'ETDa_07_{yr:02d}_in'] = df[f'ETDa_07_{yr:02d}'] / 25.4
        df[f'ETDa_08_{yr:02d}_in'] = df[f'ETDa_08_{yr:02d}'] / 25.4
        df[f'ETDa_09_{yr:02d}_in'] = df[f'ETDa_09_{yr:02d}'] / 25.4
        df[f'ETDa_10_{yr:02d}_in'] = df[f'ETDa_10_{yr:02d}'] / 25.4
    
        if yr == 0:
            df[f'ET_Reference_11_99_in'] = df[f'ET_Reference_11_99'] / 25.4
            df[f'ET_Reference_12_99_in'] = df[f'ET_Reference_12_99'] / 25.4
        else:
            df[f'ET_Reference_11_{yr-1:02d}_in'] = df[f'ET_Reference_11_{yr-1:02d}'] / 25.4
            df[f'ET_Reference_12_{yr-1:02d}_in'] = df[f'ET_Reference_12_{yr-1:02d}'] / 25.4
        df[f'ET_Reference_01_{yr:02d}_in'] = df[f'ET_Reference_01_{yr:02d}'] / 25.4
        df[f'ET_Reference_02_{yr:02d}_in'] = df[f'ET_Reference_02_{yr:02d}'] / 25.4
        df[f'ET_Reference_03_{yr:02d}_in'] = df[f'ET_Reference_03_{yr:02d}'] / 25.4
        df[f'ET_Reference_04_{yr:02d}_in'] = df[f'ET_Reference_04_{yr:02d}'] / 25.4
        df[f'ET_Reference_05_{yr:02d}_in'] = df[f'ET_Reference_05_{yr:02d}'] / 25.4
        df[f'ET_Reference_06_{yr:02d}_in'] = df[f'ET_Reference_06_{yr:02d}'] / 25.4
        df[f'ET_Reference_07_{yr:02d}_in'] = df[f'ET_Reference_07_{yr:02d}'] / 25.4
        df[f'ET_Reference_08_{yr:02d}_in'] = df[f'ET_Reference_08_{yr:02d}'] / 25.4
        df[f'ET_Reference_09_{yr:02d}_in'] = df[f'ET_Reference_09_{yr:02d}'] / 25.4
        df[f'ET_Reference_10_{yr:02d}_in'] = df[f'ET_Reference_10_{yr:02d}'] / 25.4
        
        if yr == 0:
            df[f'PPT_11_99_in'] = df[f'PPT_11_99'] / 25.4
            df[f'PPT_12_99_in'] = df[f'PPT_12_99'] / 25.4
        else:
            df[f'PPT_11_{yr-1:02d}_in'] = df[f'PPT_11_{yr-1:02d}'] / 25.4
            df[f'PPT_12_{yr-1:02d}_in'] = df[f'PPT_12_{yr-1:02d}'] / 25.4
        df[f'PPT_01_{yr:02d}_in'] = df[f'PPT_01_{yr:02d}'] / 25.4
        df[f'PPT_02_{yr:02d}_in'] = df[f'PPT_02_{yr:02d}'] / 25.4
        df[f'PPT_03_{yr:02d}_in'] = df[f'PPT_03_{yr:02d}'] / 25.4
        df[f'PPT_04_{yr:02d}_in'] = df[f'PPT_04_{yr:02d}'] / 25.4
        df[f'PPT_05_{yr:02d}_in'] = df[f'PPT_05_{yr:02d}'] / 25.4
        df[f'PPT_06_{yr:02d}_in'] = df[f'PPT_06_{yr:02d}'] / 25.4
        df[f'PPT_07_{yr:02d}_in'] = df[f'PPT_07_{yr:02d}'] / 25.4
        df[f'PPT_08_{yr:02d}_in'] = df[f'PPT_08_{yr:02d}'] / 25.4
        df[f'PPT_09_{yr:02d}_in'] = df[f'PPT_09_{yr:02d}'] / 25.4
        df[f'PPT_10_{yr:02d}_in'] = df[f'PPT_10_{yr:02d}'] / 25.4
        
        # if yr == 0:
        #     df[f'P_eft_11_99_in'] = df[f'P_eft_11_99'] / 25.4
        #     df[f'P_eft_12_99_in'] = df[f'P_eft_12_99'] / 25.4    
        # else:
        #     df[f'P_eft_11_{yr-1:02d}_in'] = df[f'P_eft_11_{yr-1:02d}'] / 25.4
        #     df[f'P_eft_12_{yr-1:02d}_in'] = df[f'P_eft_12_{yr-1:02d}'] / 25.4
        # df[f'P_eft_01_{yr:02d}_in'] = df[f'P_eft_01_{yr:02d}'] / 25.4
        # df[f'P_eft_02_{yr:02d}_in'] = df[f'P_eft_02_{yr:02d}'] / 25.4
        # df[f'P_eft_03_{yr:02d}_in'] = df[f'P_eft_03_{yr:02d}'] / 25.4
        # df[f'P_eft_04_{yr:02d}_in'] = df[f'P_eft_04_{yr:02d}'] / 25.4
        # df[f'P_eft_05_{yr:02d}_in'] = df[f'P_eft_05_{yr:02d}'] / 25.4
        # df[f'P_eft_06_{yr:02d}_in'] = df[f'P_eft_06_{yr:02d}'] / 25.4
        # df[f'P_eft_07_{yr:02d}_in'] = df[f'P_eft_07_{yr:02d}'] / 25.4
        # df[f'P_eft_08_{yr:02d}_in'] = df[f'P_eft_08_{yr:02d}'] / 25.4
        # df[f'P_eft_09_{yr:02d}_in'] = df[f'P_eft_09_{yr:02d}'] / 25.4
        # df[f'P_eft_10_{yr:02d}_in'] = df[f'P_eft_10_{yr:02d}'] / 25.4
    
        if yr == 0:
            df[f'P_rz_11_99_in'] = df[f'P_rz_11_99'] / 25.4
            df[f'P_rz_12_99_in'] = df[f'P_rz_12_99'] / 25.4  
        else:
            df[f'P_rz_11_{yr-1:02d}_in'] = df[f'P_rz_11_{yr-1:02d}'] / 25.4
            df[f'P_rz_12_{yr-1:02d}_in'] = df[f'P_rz_12_{yr-1:02d}'] / 25.4
        df[f'P_rz_01_{yr:02d}_in'] = df[f'P_rz_01_{yr:02d}'] / 25.4
        df[f'P_rz_02_{yr:02d}_in'] = df[f'P_rz_02_{yr:02d}'] / 25.4
        df[f'P_rz_03_{yr:02d}_in'] = df[f'P_rz_03_{yr:02d}'] / 25.4
        df[f'P_rz_04_{yr:02d}_in'] = df[f'P_rz_04_{yr:02d}'] / 25.4
        df[f'P_rz_05_{yr:02d}_in'] = df[f'P_rz_05_{yr:02d}'] / 25.4
        df[f'P_rz_06_{yr:02d}_in'] = df[f'P_rz_06_{yr:02d}'] / 25.4
        df[f'P_rz_07_{yr:02d}_in'] = df[f'P_rz_07_{yr:02d}'] / 25.4
        df[f'P_rz_08_{yr:02d}_in'] = df[f'P_rz_08_{yr:02d}'] / 25.4
        df[f'P_rz_09_{yr:02d}_in'] = df[f'P_rz_09_{yr:02d}'] / 25.4
        df[f'P_rz_10_{yr:02d}_in'] = df[f'P_rz_10_{yr:02d}'] / 25.4
    
        if yr == 0:
            df[f'NIWR_11_99_in'] = (df[f'NIWR_11_99'] / 25.4)
            df[f'NIWR_12_99_in'] = (df[f'NIWR_12_99'] / 25.4)
        else:
            df[f'NIWR_11_{yr-1:02d}_in'] = (df[f'NIWR_11_{yr-1:02d}'] / 25.4)
            df[f'NIWR_12_{yr-1:02d}_in'] = (df[f'NIWR_12_{yr-1:02d}'] / 25.4)
        df[f'NIWR_01_{yr:02d}_in'] = (df[f'NIWR_01_{yr:02d}'] / 25.4)
        df[f'NIWR_02_{yr:02d}_in'] = (df[f'NIWR_02_{yr:02d}'] / 25.4)
        df[f'NIWR_03_{yr:02d}_in'] = (df[f'NIWR_03_{yr:02d}'] / 25.4)
        df[f'NIWR_04_{yr:02d}_in'] = (df[f'NIWR_04_{yr:02d}'] / 25.4)
        df[f'NIWR_05_{yr:02d}_in'] = (df[f'NIWR_05_{yr:02d}'] / 25.4)
        df[f'NIWR_06_{yr:02d}_in'] = (df[f'NIWR_06_{yr:02d}'] / 25.4)
        df[f'NIWR_07_{yr:02d}_in'] = (df[f'NIWR_07_{yr:02d}'] / 25.4)
        df[f'NIWR_08_{yr:02d}_in'] = (df[f'NIWR_08_{yr:02d}'] / 25.4)
        df[f'NIWR_09_{yr:02d}_in'] = (df[f'NIWR_09_{yr:02d}'] / 25.4)
        df[f'NIWR_10_{yr:02d}_in'] = (df[f'NIWR_10_{yr:02d}'] / 25.4)
        
        # calculate volumes of each monthly value for all variables
        if yr == 0:
            df[f'ET_VOLUME_11_99_acft'] = (df[f'ETa_11_99_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
            df[f'ET_VOLUME_12_99_acft'] = (df[f'ETa_12_99_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']        
        else:
            df[f'ET_VOLUME_11_{yr-1:02d}_acft'] = (df[f'ETa_11_{yr-1:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
            df[f'ET_VOLUME_12_{yr-1:02d}_acft'] = (df[f'ETa_12_{yr-1:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ET_VOLUME_01_{yr:02d}_acft'] = (df[f'ETa_01_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ET_VOLUME_02_{yr:02d}_acft'] = (df[f'ETa_02_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ET_VOLUME_03_{yr:02d}_acft'] = (df[f'ETa_03_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ET_VOLUME_04_{yr:02d}_acft'] = (df[f'ETa_04_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ET_VOLUME_05_{yr:02d}_acft'] = (df[f'ETa_05_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ET_VOLUME_06_{yr:02d}_acft'] = (df[f'ETa_06_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ET_VOLUME_07_{yr:02d}_acft'] = (df[f'ETa_07_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ET_VOLUME_08_{yr:02d}_acft'] = (df[f'ETa_08_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ET_VOLUME_09_{yr:02d}_acft'] = (df[f'ETa_09_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ET_VOLUME_10_{yr:02d}_acft'] = (df[f'ETa_10_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        
        # calculate volumes of each monthly value for all variables
        if yr == 0:
            df[f'ETDa_VOLUME_11_99_acft'] = (df[f'ETDa_11_99_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
            df[f'ETDa_VOLUME_12_99_acft'] = (df[f'ETDa_12_99_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        else:
            df[f'ETDa_VOLUME_11_{yr-1:02d}_acft'] = (df[f'ETDa_11_{yr-1:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
            df[f'ETDa_VOLUME_12_{yr-1:02d}_acft'] = (df[f'ETDa_12_{yr-1:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETDa_VOLUME_01_{yr:02d}_acft'] = (df[f'ETDa_01_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETDa_VOLUME_02_{yr:02d}_acft'] = (df[f'ETDa_02_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETDa_VOLUME_03_{yr:02d}_acft'] = (df[f'ETDa_03_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETDa_VOLUME_04_{yr:02d}_acft'] = (df[f'ETDa_04_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETDa_VOLUME_05_{yr:02d}_acft'] = (df[f'ETDa_05_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETDa_VOLUME_06_{yr:02d}_acft'] = (df[f'ETDa_06_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETDa_VOLUME_07_{yr:02d}_acft'] = (df[f'ETDa_07_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETDa_VOLUME_08_{yr:02d}_acft'] = (df[f'ETDa_08_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETDa_VOLUME_09_{yr:02d}_acft'] = (df[f'ETDa_09_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETDa_VOLUME_10_{yr:02d}_acft'] = (df[f'ETDa_10_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
    
        if yr == 0:
            df[f'ETO_VOLUME_11_99_acft'] = (df[f'ET_Reference_11_99_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
            df[f'ETO_VOLUME_12_99_acft'] = (df[f'ET_Reference_12_99_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        else:
            df[f'ETO_VOLUME_11_{yr-1:02d}_acft'] = (df[f'ET_Reference_11_{yr-1:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
            df[f'ETO_VOLUME_12_{yr-1:02d}_acft'] = (df[f'ET_Reference_12_{yr-1:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETO_VOLUME_01_{yr:02d}_acft'] = (df[f'ET_Reference_01_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETO_VOLUME_02_{yr:02d}_acft'] = (df[f'ET_Reference_02_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETO_VOLUME_03_{yr:02d}_acft'] = (df[f'ET_Reference_03_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETO_VOLUME_04_{yr:02d}_acft'] = (df[f'ET_Reference_04_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETO_VOLUME_05_{yr:02d}_acft'] = (df[f'ET_Reference_05_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETO_VOLUME_06_{yr:02d}_acft'] = (df[f'ET_Reference_06_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETO_VOLUME_07_{yr:02d}_acft'] = (df[f'ET_Reference_07_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETO_VOLUME_08_{yr:02d}_acft'] = (df[f'ET_Reference_08_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETO_VOLUME_09_{yr:02d}_acft'] = (df[f'ET_Reference_09_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'ETO_VOLUME_10_{yr:02d}_acft'] = (df[f'ET_Reference_10_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
     
        if yr == 0:
            df[f'PPT_VOLUME_11_99_acft'] = (df[f'PPT_11_99_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
            df[f'PPT_VOLUME_12_99_acft'] = (df[f'PPT_12_99_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']    
        else:
            df[f'PPT_VOLUME_11_{yr-1:02d}_acft'] = (df[f'PPT_11_{yr-1:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
            df[f'PPT_VOLUME_12_{yr-1:02d}_acft'] = (df[f'PPT_12_{yr-1:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'PPT_VOLUME_01_{yr:02d}_acft'] = (df[f'PPT_01_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'PPT_VOLUME_02_{yr:02d}_acft'] = (df[f'PPT_02_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'PPT_VOLUME_03_{yr:02d}_acft'] = (df[f'PPT_03_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'PPT_VOLUME_04_{yr:02d}_acft'] = (df[f'PPT_04_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'PPT_VOLUME_05_{yr:02d}_acft'] = (df[f'PPT_05_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'PPT_VOLUME_06_{yr:02d}_acft'] = (df[f'PPT_06_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'PPT_VOLUME_07_{yr:02d}_acft'] = (df[f'PPT_07_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'PPT_VOLUME_08_{yr:02d}_acft'] = (df[f'PPT_08_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'PPT_VOLUME_09_{yr:02d}_acft'] = (df[f'PPT_09_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'PPT_VOLUME_10_{yr:02d}_acft'] = (df[f'PPT_10_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
    
        if yr == 0:
            df[f'EFF_VOLUME_11_99_acft'] = (df[f'{eff_ppt_var}_11_99_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
            df[f'EFF_VOLUME_12_99_acft'] = (df[f'{eff_ppt_var}_12_99_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']    
        else:
            df[f'EFF_VOLUME_11_{yr-1:02d}_acft'] = (df[f'{eff_ppt_var}_11_{yr-1:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
            df[f'EFF_VOLUME_12_{yr-1:02d}_acft'] = (df[f'{eff_ppt_var}_12_{yr-1:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'EFF_VOLUME_01_{yr:02d}_acft'] = (df[f'{eff_ppt_var}_01_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'EFF_VOLUME_02_{yr:02d}_acft'] = (df[f'{eff_ppt_var}_02_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'EFF_VOLUME_03_{yr:02d}_acft'] = (df[f'{eff_ppt_var}_03_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'EFF_VOLUME_04_{yr:02d}_acft'] = (df[f'{eff_ppt_var}_04_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'EFF_VOLUME_05_{yr:02d}_acft'] = (df[f'{eff_ppt_var}_05_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'EFF_VOLUME_06_{yr:02d}_acft'] = (df[f'{eff_ppt_var}_06_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'EFF_VOLUME_07_{yr:02d}_acft'] = (df[f'{eff_ppt_var}_07_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'EFF_VOLUME_08_{yr:02d}_acft'] = (df[f'{eff_ppt_var}_08_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'EFF_VOLUME_09_{yr:02d}_acft'] = (df[f'{eff_ppt_var}_09_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
        df[f'EFF_VOLUME_10_{yr:02d}_acft'] = (df[f'{eff_ppt_var}_10_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}']
    
        # cap the effective ppt from ET Demands to the max (total precip) from the field averaged gridMET ppt
        # if yr == 0:
        #     df.loc[df[f'EFF_VOLUME_11_99_acft'] > df[f'PPT_VOLUME_11_99_acft'], f'EFF_VOLUME_11_99_acft'] = df[f'PPT_VOLUME_11_99_acft']
        #     df.loc[df[f'EFF_VOLUME_12_99_acft'] > df[f'PPT_VOLUME_11_99_acft'], f'EFF_VOLUME_11_99_acft'] = df[f'PPT_VOLUME_11_99_acft']    
        # else:
        #     df.loc[df[f'EFF_VOLUME_11_{yr-1:02d}_acft'] > df[f'PPT_VOLUME_11_{yr-1:02d}_acft'], f'EFF_VOLUME_11_{yr-1:02d}_acft'] = df[f'PPT_VOLUME_11_{yr-1:02d}_acft']
        #     df.loc[df[f'EFF_VOLUME_12_{yr-1:02d}_acft'] > df[f'PPT_VOLUME_11_{yr-1:02d}_acft'], f'EFF_VOLUME_11_{yr-1:02d}_acft'] = df[f'PPT_VOLUME_11_{yr-1:02d}_acft']
        # df.loc[df[f'EFF_VOLUME_01_{yr:02d}_acft'] > df[f'PPT_VOLUME_01_{yr:02d}_acft'], f'EFF_VOLUME_01_{yr:02d}_acft'] = df[f'PPT_VOLUME_01_{yr:02d}_acft']
        # df.loc[df[f'EFF_VOLUME_02_{yr:02d}_acft'] > df[f'PPT_VOLUME_02_{yr:02d}_acft'], f'EFF_VOLUME_02_{yr:02d}_acft'] = df[f'PPT_VOLUME_02_{yr:02d}_acft']
        # df.loc[df[f'EFF_VOLUME_03_{yr:02d}_acft'] > df[f'PPT_VOLUME_03_{yr:02d}_acft'], f'EFF_VOLUME_03_{yr:02d}_acft'] = df[f'PPT_VOLUME_03_{yr:02d}_acft']
        # df.loc[df[f'EFF_VOLUME_04_{yr:02d}_acft'] > df[f'PPT_VOLUME_04_{yr:02d}_acft'], f'EFF_VOLUME_04_{yr:02d}_acft'] = df[f'PPT_VOLUME_04_{yr:02d}_acft']
        # df.loc[df[f'EFF_VOLUME_05_{yr:02d}_acft'] > df[f'PPT_VOLUME_05_{yr:02d}_acft'], f'EFF_VOLUME_05_{yr:02d}_acft'] = df[f'PPT_VOLUME_05_{yr:02d}_acft']
        # df.loc[df[f'EFF_VOLUME_06_{yr:02d}_acft'] > df[f'PPT_VOLUME_06_{yr:02d}_acft'], f'EFF_VOLUME_06_{yr:02d}_acft'] = df[f'PPT_VOLUME_06_{yr:02d}_acft']
        # df.loc[df[f'EFF_VOLUME_07_{yr:02d}_acft'] > df[f'PPT_VOLUME_07_{yr:02d}_acft'], f'EFF_VOLUME_07_{yr:02d}_acft'] = df[f'PPT_VOLUME_07_{yr:02d}_acft']
        # df.loc[df[f'EFF_VOLUME_08_{yr:02d}_acft'] > df[f'PPT_VOLUME_08_{yr:02d}_acft'], f'EFF_VOLUME_08_{yr:02d}_acft'] = df[f'PPT_VOLUME_08_{yr:02d}_acft']
        # df.loc[df[f'EFF_VOLUME_09_{yr:02d}_acft'] > df[f'PPT_VOLUME_09_{yr:02d}_acft'], f'EFF_VOLUME_09_{yr:02d}_acft'] = df[f'PPT_VOLUME_09_{yr:02d}_acft']
        # df.loc[df[f'EFF_VOLUME_10_{yr:02d}_acft'] > df[f'PPT_VOLUME_10_{yr:02d}_acft'], f'EFF_VOLUME_10_{yr:02d}_acft'] = df[f'PPT_VOLUME_10_{yr:02d}_acft']
        
        # calculate the consumptive use by subtracting effective ppt from actual et
        if yr == 0:
            df[f'IRR_CU_VOLUME_11_99_acft'] = df[f'ET_VOLUME_11_99_acft'] - df[f'EFF_VOLUME_11_99_acft']
            df[f'IRR_CU_VOLUME_12_99_acft'] = df[f'ET_VOLUME_12_99_acft'] - df[f'EFF_VOLUME_12_99_acft']        
        else:
            df[f'IRR_CU_VOLUME_11_{yr-1:02d}_acft'] = df[f'ET_VOLUME_11_{yr-1:02d}_acft'] - df[f'EFF_VOLUME_11_{yr-1:02d}_acft']
            df[f'IRR_CU_VOLUME_12_{yr-1:02d}_acft'] = df[f'ET_VOLUME_12_{yr-1:02d}_acft'] - df[f'EFF_VOLUME_12_{yr-1:02d}_acft']
        df[f'IRR_CU_VOLUME_01_{yr:02d}_acft'] = df[f'ET_VOLUME_01_{yr:02d}_acft'] - df[f'EFF_VOLUME_01_{yr:02d}_acft']
        df[f'IRR_CU_VOLUME_02_{yr:02d}_acft'] = df[f'ET_VOLUME_02_{yr:02d}_acft'] - df[f'EFF_VOLUME_02_{yr:02d}_acft']
        df[f'IRR_CU_VOLUME_03_{yr:02d}_acft'] = df[f'ET_VOLUME_03_{yr:02d}_acft'] - df[f'EFF_VOLUME_03_{yr:02d}_acft']
        df[f'IRR_CU_VOLUME_04_{yr:02d}_acft'] = df[f'ET_VOLUME_04_{yr:02d}_acft'] - df[f'EFF_VOLUME_04_{yr:02d}_acft']
        df[f'IRR_CU_VOLUME_05_{yr:02d}_acft'] = df[f'ET_VOLUME_05_{yr:02d}_acft'] - df[f'EFF_VOLUME_05_{yr:02d}_acft']
        df[f'IRR_CU_VOLUME_06_{yr:02d}_acft'] = df[f'ET_VOLUME_06_{yr:02d}_acft'] - df[f'EFF_VOLUME_06_{yr:02d}_acft']
        df[f'IRR_CU_VOLUME_07_{yr:02d}_acft'] = df[f'ET_VOLUME_07_{yr:02d}_acft'] - df[f'EFF_VOLUME_07_{yr:02d}_acft']
        df[f'IRR_CU_VOLUME_08_{yr:02d}_acft'] = df[f'ET_VOLUME_08_{yr:02d}_acft'] - df[f'EFF_VOLUME_08_{yr:02d}_acft']
        df[f'IRR_CU_VOLUME_09_{yr:02d}_acft'] = df[f'ET_VOLUME_09_{yr:02d}_acft'] - df[f'EFF_VOLUME_09_{yr:02d}_acft']
        df[f'IRR_CU_VOLUME_10_{yr:02d}_acft'] = df[f'ET_VOLUME_10_{yr:02d}_acft'] - df[f'EFF_VOLUME_10_{yr:02d}_acft']
    
        if yr == 0:
            df[f'NIWR_VOLUME_11_99_acft'] = ((df[f'NIWR_11_99_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}'])
            df[f'NIWR_VOLUME_12_99_acft'] = ((df[f'NIWR_12_99_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}'])   
        else:
            df[f'NIWR_VOLUME_11_{yr-1:02d}_acft'] = ((df[f'NIWR_11_{yr-1:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}'])
            df[f'NIWR_VOLUME_12_{yr-1:02d}_acft'] = ((df[f'NIWR_12_{yr-1:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}'])
        df[f'NIWR_VOLUME_01_{yr:02d}_acft'] = ((df[f'NIWR_01_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}'])
        df[f'NIWR_VOLUME_02_{yr:02d}_acft'] = ((df[f'NIWR_02_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}'])
        df[f'NIWR_VOLUME_03_{yr:02d}_acft'] = ((df[f'NIWR_03_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}'])
        df[f'NIWR_VOLUME_04_{yr:02d}_acft'] = ((df[f'NIWR_04_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}'])
        df[f'NIWR_VOLUME_05_{yr:02d}_acft'] = ((df[f'NIWR_05_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}'])
        df[f'NIWR_VOLUME_06_{yr:02d}_acft'] = ((df[f'NIWR_06_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}'])
        df[f'NIWR_VOLUME_07_{yr:02d}_acft'] = ((df[f'NIWR_07_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}'])
        df[f'NIWR_VOLUME_08_{yr:02d}_acft'] = ((df[f'NIWR_08_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}'])
        df[f'NIWR_VOLUME_09_{yr:02d}_acft'] = ((df[f'NIWR_09_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}'])
        df[f'NIWR_VOLUME_10_{yr:02d}_acft'] = ((df[f'NIWR_10_{yr:02d}_in'] / 12) * df[f'ACRES_FTR_GEOM_{yr:02d}'])   
        
        
    # regular expression to find columns containing the list of substrings below 
    reg1 = '|'.join([f'GEOM_{yr_abr_list[0]:02d}','HUC','OWRD','Region','ITYPE','IRR_EFF','srctype','GRIDMET',f'IRR_STATUS_{yr_list[0]}',f'ACRES_FTR_GEOM_{yr_abr_list[0]:02d}',f'IRRIGATED_{yr_abr_list[0]:02d}',f'WETLAND_{yr_abr_list[0]:02d}',f'{yr_abr_list[0]:02d}_MODE',f'ETD_{yr_abr_list[0]:02d}',
                     f'ET_Fraction_11_{yr_abr_list[0]-1:02d}',f'ET_Fraction_12_{yr_abr_list[0]-1:02d}',f'ET_Fraction_01_{yr_abr_list[0]:02d}',f'ET_Fraction_02_{yr_abr_list[0]:02d}',
                     f'ET_Fraction_03_{yr_abr_list[0]:02d}',f'ET_Fraction_04_{yr_abr_list[0]:02d}',f'ET_Fraction_05_{yr_abr_list[0]:02d}',f'ET_Fraction_06_{yr_abr_list[0]:02d}',
                     f'ET_Fraction_07_{yr_abr_list[0]:02d}',f'ET_Fraction_08_{yr_abr_list[0]:02d}',f'ET_Fraction_09_{yr_abr_list[0]:02d}',f'ET_Fraction_10_{yr_abr_list[0]:02d}',
                     f'11_{yr_abr_list[0]-1:02d}_in',f'12_{yr_abr_list[0]-1:02d}_in',f'01_{yr_abr_list[0]:02d}_in',f'02_{yr_abr_list[0]:02d}_in',f'03_{yr_abr_list[0]:02d}_in',
                     f'04_{yr_abr_list[0]:02d}_in',f'05_{yr_abr_list[0]:02d}_in',f'06_{yr_abr_list[0]:02d}_in',f'07_{yr_abr_list[0]:02d}_in',f'08_{yr_abr_list[0]:02d}_in',
                     f'09_{yr_abr_list[0]:02d}_in',f'10_{yr_abr_list[0]:02d}_in',f'11_{yr_abr_list[0]-1:02d}_acft',f'12_{yr_abr_list[0]-1:02d}_acft',f'01_{yr_abr_list[0]:02d}_acft',
                     f'02_{yr_abr_list[0]:02d}_acft',f'03_{yr_abr_list[0]:02d}_acft',f'04_{yr_abr_list[0]:02d}_acft',f'05_{yr_abr_list[0]:02d}_acft',
                     f'06_{yr_abr_list[0]:02d}_acft',f'07_{yr_abr_list[0]:02d}_acft',f'08_{yr_abr_list[0]:02d}_acft',f'09_{yr_abr_list[0]:02d}_acft',f'10_{yr_abr_list[0]:02d}_acft',f'{yr_list[0]}'])
    reg2 = '|'.join([f'GEOM_{yr_abr_list[1]:02d}','HUC','OWRD','Region','ITYPE','IRR_EFF','srctype','GRIDMET',f'IRR_STATUS_{yr_list[1]}',f'ACRES_FTR_GEOM_{yr_abr_list[1]:02d}',f'IRRIGATED_{yr_abr_list[1]:02d}',f'WETLAND_{yr_abr_list[1]:02d}',f'{yr_abr_list[1]:02d}_MODE',f'ETD_{yr_abr_list[1]:02d}',
                     f'ET_Fraction_11_{yr_abr_list[1]-1:02d}',f'ET_Fraction_12_{yr_abr_list[1]-1:02d}',f'ET_Fraction_01_{yr_abr_list[1]:02d}',f'ET_Fraction_02_{yr_abr_list[1]:02d}',
                     f'ET_Fraction_03_{yr_abr_list[1]:02d}',f'ET_Fraction_04_{yr_abr_list[1]:02d}',f'ET_Fraction_05_{yr_abr_list[1]:02d}',f'ET_Fraction_06_{yr_abr_list[1]:02d}',
                     f'ET_Fraction_07_{yr_abr_list[1]:02d}',f'ET_Fraction_08_{yr_abr_list[1]:02d}',f'ET_Fraction_09_{yr_abr_list[1]:02d}',f'ET_Fraction_10_{yr_abr_list[1]:02d}',
                     f'11_{yr_abr_list[1]-1:02d}_in',f'12_{yr_abr_list[1]-1:02d}_in',f'01_{yr_abr_list[1]:02d}_in',f'02_{yr_abr_list[1]:02d}_in',f'03_{yr_abr_list[1]:02d}_in',f'04_{yr_abr_list[1]:02d}_in',f'05_{yr_abr_list[1]:02d}_in',
                     f'06_{yr_abr_list[1]:02d}_in',f'07_{yr_abr_list[1]:02d}_in',f'08_{yr_abr_list[1]:02d}_in',f'09_{yr_abr_list[1]:02d}_in',f'10_{yr_abr_list[1]:02d}_in',f'11_{yr_abr_list[1]-1:02d}_acft',f'12_{yr_abr_list[1]-1:02d}_acft',
                     f'01_{yr_abr_list[1]:02d}_acft',f'02_{yr_abr_list[1]:02d}_acft',f'03_{yr_abr_list[1]:02d}_acft',f'04_{yr_abr_list[1]:02d}_acft',f'05_{yr_abr_list[1]:02d}_acft',
                     f'06_{yr_abr_list[1]:02d}_acft',f'07_{yr_abr_list[1]:02d}_acft',f'08_{yr_abr_list[1]:02d}_acft',f'09_{yr_abr_list[1]:02d}_acft',f'10_{yr_abr_list[1]:02d}_acft',f'{yr_list[1]}'])
    if 0 in yr_abr_list:
        reg3 = '|'.join([f'GEOM_{yr_abr_list[2]:02d}','HUC','OWRD','Region','ITYPE','IRR_EFF','srctype','GRIDMET',f'IRR_STATUS_{yr_list[2]}',f'ACRES_FTR_GEOM_{yr_abr_list[2]:02d}',f'IRRIGATED_{yr_abr_list[2]:02d}',f'WETLAND_{yr_abr_list[2]:02d}',f'{yr_abr_list[2]:02d}_MODE',f'ETD_{yr_abr_list[2]:02d}',
                         'ET_Fraction_11_99','ET_Fraction_12_99',f'ET_Fraction_01_{yr_abr_list[2]:02d}',f'ET_Fraction_02_{yr_abr_list[2]:02d}',
                         f'ET_Fraction_03_{yr_abr_list[2]:02d}',f'ET_Fraction_04_{yr_abr_list[2]:02d}',f'ET_Fraction_05_{yr_abr_list[2]:02d}',f'ET_Fraction_06_{yr_abr_list[2]:02d}',
                         f'ET_Fraction_07_{yr_abr_list[2]:02d}',f'ET_Fraction_08_{yr_abr_list[2]:02d}',f'ET_Fraction_09_{yr_abr_list[2]:02d}',f'ET_Fraction_10_{yr_abr_list[2]:02d}',
                         '11_99_in','12_99_in',f'01_{yr_abr_list[2]:02d}_in',f'02_{yr_abr_list[2]:02d}_in',f'03_{yr_abr_list[2]:02d}_in',f'04_{yr_abr_list[2]:02d}_in',f'05_{yr_abr_list[2]:02d}_in',
                         f'06_{yr_abr_list[2]:02d}_in',f'07_{yr_abr_list[2]:02d}_in',f'08_{yr_abr_list[2]:02d}_in',f'09_{yr_abr_list[2]:02d}_in',f'10_{yr_abr_list[2]:02d}_in','11_99_acft','12_99_acft',
                         f'01_{yr_abr_list[2]:02d}_acft',f'02_{yr_abr_list[2]:02d}_acft',f'03_{yr_abr_list[2]:02d}_acft',f'04_{yr_abr_list[2]:02d}_acft',f'05_{yr_abr_list[2]:02d}_acft',
                         f'06_{yr_abr_list[2]:02d}_acft',f'07_{yr_abr_list[2]:02d}_acft',f'08_{yr_abr_list[2]:02d}_acft',f'09_{yr_abr_list[2]:02d}_acft',f'10_{yr_abr_list[2]:02d}_acft',f'{yr_list[2]}'])
    else:
        reg3 = '|'.join([f'GEOM_{yr_abr_list[2]:02d}','HUC','OWRD','Region','ITYPE','IRR_EFF','srctype','GRIDMET',f'IRR_STATUS_{yr_list[2]}',f'ACRES_FTR_GEOM_{yr_abr_list[2]:02d}',f'IRRIGATED_{yr_abr_list[2]:02d}',f'WETLAND_{yr_abr_list[2]:02d}',f'{yr_abr_list[2]:02d}_MODE',f'ETD_{yr_abr_list[2]:02d}',
                         f'ET_Fraction_11_{yr_abr_list[2]-1:02d}',f'ET_Fraction_12_{yr_abr_list[2]-1:02d}',f'ET_Fraction_01_{yr_abr_list[2]:02d}',f'ET_Fraction_02_{yr_abr_list[2]:02d}',
                         f'ET_Fraction_03_{yr_abr_list[2]:02d}',f'ET_Fraction_04_{yr_abr_list[2]:02d}',f'ET_Fraction_05_{yr_abr_list[2]:02d}',f'ET_Fraction_06_{yr_abr_list[2]:02d}',
                         f'ET_Fraction_07_{yr_abr_list[2]:02d}',f'ET_Fraction_08_{yr_abr_list[2]:02d}',f'ET_Fraction_09_{yr_abr_list[2]:02d}',f'ET_Fraction_10_{yr_abr_list[2]:02d}',
                         f'11_{yr_abr_list[2]-1:02d}_in',f'12_{yr_abr_list[2]-1:02d}_in',f'01_{yr_abr_list[2]:02d}_in',f'02_{yr_abr_list[2]:02d}_in',f'03_{yr_abr_list[2]:02d}_in',f'04_{yr_abr_list[2]:02d}_in',f'05_{yr_abr_list[2]:02d}_in',
                         f'06_{yr_abr_list[2]:02d}_in',f'07_{yr_abr_list[2]:02d}_in',f'08_{yr_abr_list[2]:02d}_in',f'09_{yr_abr_list[2]:02d}_in',f'10_{yr_abr_list[2]:02d}_in',f'11_{yr_abr_list[2]-1:02d}_acft',f'12_{yr_abr_list[2]-1:02d}_acft',
                         f'01_{yr_abr_list[2]:02d}_acft',f'02_{yr_abr_list[2]:02d}_acft',f'03_{yr_abr_list[2]:02d}_acft',f'04_{yr_abr_list[2]:02d}_acft',f'05_{yr_abr_list[2]:02d}_acft',
                         f'06_{yr_abr_list[2]:02d}_acft',f'07_{yr_abr_list[2]:02d}_acft',f'08_{yr_abr_list[2]:02d}_acft',f'09_{yr_abr_list[2]:02d}_acft',f'10_{yr_abr_list[2]:02d}_acft',f'{yr_list[2]}'])
    reg4 = '|'.join([f'GEOM_{yr_abr_list[3]:02d}','HUC','OWRD','Region','ITYPE','IRR_EFF','srctype','GRIDMET',f'IRR_STATUS_{yr_list[3]}',f'ACRES_FTR_GEOM_{yr_abr_list[3]:02d}',f'IRRIGATED_{yr_abr_list[3]:02d}',f'WETLAND_{yr_abr_list[3]:02d}',f'{yr_abr_list[3]:02d}_MODE',f'ETD_{yr_abr_list[3]:02d}',
                     f'ET_Fraction_11_{yr_abr_list[3]-1:02d}',f'ET_Fraction_12_{yr_abr_list[3]-1:02d}',f'ET_Fraction_01_{yr_abr_list[3]:02d}',f'ET_Fraction_02_{yr_abr_list[3]:02d}',
                     f'ET_Fraction_03_{yr_abr_list[3]:02d}',f'ET_Fraction_04_{yr_abr_list[3]:02d}',f'ET_Fraction_05_{yr_abr_list[3]:02d}',f'ET_Fraction_06_{yr_abr_list[3]:02d}',
                     f'ET_Fraction_07_{yr_abr_list[3]:02d}',f'ET_Fraction_08_{yr_abr_list[3]:02d}',f'ET_Fraction_09_{yr_abr_list[3]:02d}',f'ET_Fraction_10_{yr_abr_list[3]:02d}',
                     f'11_{yr_abr_list[3]-1:02d}_in',f'12_{yr_abr_list[3]-1:02d}_in',f'01_{yr_abr_list[3]:02d}_in',f'02_{yr_abr_list[3]:02d}_in',f'03_{yr_abr_list[3]:02d}_in',f'04_{yr_abr_list[3]:02d}_in',f'05_{yr_abr_list[3]:02d}_in',
                     f'06_{yr_abr_list[3]:02d}_in',f'07_{yr_abr_list[3]:02d}_in',f'08_{yr_abr_list[3]:02d}_in',f'09_{yr_abr_list[3]:02d}_in',f'10_{yr_abr_list[3]:02d}_in',f'11_{yr_abr_list[3]-1:02d}_acft',f'12_{yr_abr_list[3]-1:02d}_acft',
                     f'01_{yr_abr_list[3]:02d}_acft',f'02_{yr_abr_list[3]:02d}_acft',f'03_{yr_abr_list[3]:02d}_acft',f'04_{yr_abr_list[3]:02d}_acft',f'05_{yr_abr_list[3]:02d}_acft',
                     f'06_{yr_abr_list[3]:02d}_acft',f'07_{yr_abr_list[3]:02d}_acft',f'08_{yr_abr_list[3]:02d}_acft',f'09_{yr_abr_list[3]:02d}_acft',f'10_{yr_abr_list[3]:02d}_acft',f'{yr_list[3]}'])
    reg5 = '|'.join([f'GEOM_{yr_abr_list[4]:02d}','HUC','OWRD','Region','ITYPE','IRR_EFF','srctype','GRIDMET',f'IRR_STATUS_{yr_list[4]}',f'ACRES_FTR_GEOM_{yr_abr_list[4]:02d}',f'IRRIGATED_{yr_abr_list[4]:02d}',f'WETLAND_{yr_abr_list[4]:02d}',f'{yr_abr_list[4]:02d}_MODE',f'ETD_{yr_abr_list[4]:02d}',
                     f'ET_Fraction_11_{yr_abr_list[4]-1:02d}',f'ET_Fraction_12_{yr_abr_list[4]-1:02d}',f'ET_Fraction_01_{yr_abr_list[4]:02d}',f'ET_Fraction_02_{yr_abr_list[4]:02d}',
                     f'ET_Fraction_03_{yr_abr_list[4]:02d}',f'ET_Fraction_04_{yr_abr_list[4]:02d}',f'ET_Fraction_05_{yr_abr_list[4]:02d}',f'ET_Fraction_06_{yr_abr_list[4]:02d}',
                     f'ET_Fraction_07_{yr_abr_list[4]:02d}',f'ET_Fraction_08_{yr_abr_list[4]:02d}',f'ET_Fraction_09_{yr_abr_list[4]:02d}',f'ET_Fraction_10_{yr_abr_list[4]:02d}',
                     f'11_{yr_abr_list[4]-1:02d}_in',f'12_{yr_abr_list[4]-1:02d}_in',f'01_{yr_abr_list[4]:02d}_in',f'02_{yr_abr_list[4]:02d}_in',f'03_{yr_abr_list[4]:02d}_in',f'04_{yr_abr_list[4]:02d}_in',f'05_{yr_abr_list[4]:02d}_in',
                     f'06_{yr_abr_list[4]:02d}_in',f'07_{yr_abr_list[4]:02d}_in',f'08_{yr_abr_list[4]:02d}_in',f'09_{yr_abr_list[4]:02d}_in',f'10_{yr_abr_list[4]:02d}_in',f'11_{yr_abr_list[4]-1:02d}_acft',f'12_{yr_abr_list[4]-1:02d}_acft',
                     f'01_{yr_abr_list[4]:02d}_acft',f'02_{yr_abr_list[4]:02d}_acft',f'03_{yr_abr_list[4]:02d}_acft',f'04_{yr_abr_list[4]:02d}_acft',f'05_{yr_abr_list[4]:02d}_acft',
                     f'06_{yr_abr_list[4]:02d}_acft',f'07_{yr_abr_list[4]:02d}_acft',f'08_{yr_abr_list[4]:02d}_acft',f'09_{yr_abr_list[4]:02d}_acft',f'10_{yr_abr_list[4]:02d}_acft',f'{yr_list[4]}'])
    reg6 = '|'.join([f'GEOM_{yr_abr_list[5]:02d}','HUC','OWRD','Region','ITYPE','IRR_EFF','srctype','GRIDMET',f'IRR_STATUS_{yr_list[5]}',f'ACRES_FTR_GEOM_{yr_abr_list[5]:02d}',f'IRRIGATED_{yr_abr_list[5]:02d}',f'WETLAND_{yr_abr_list[5]:02d}',f'{yr_abr_list[5]:02d}_MODE',f'ETD_{yr_abr_list[5]:02d}',
                     f'ET_Fraction_11_{yr_abr_list[5]-1:02d}',f'ET_Fraction_12_{yr_abr_list[5]-1:02d}',f'ET_Fraction_01_{yr_abr_list[5]:02d}',f'ET_Fraction_02_{yr_abr_list[5]:02d}',
                     f'ET_Fraction_03_{yr_abr_list[5]:02d}',f'ET_Fraction_04_{yr_abr_list[5]:02d}',f'ET_Fraction_05_{yr_abr_list[5]:02d}',f'ET_Fraction_06_{yr_abr_list[5]:02d}',
                     f'ET_Fraction_07_{yr_abr_list[5]:02d}',f'ET_Fraction_08_{yr_abr_list[5]:02d}',f'ET_Fraction_09_{yr_abr_list[5]:02d}',f'ET_Fraction_10_{yr_abr_list[5]:02d}',
                     f'11_{yr_abr_list[5]-1:02d}_in',f'12_{yr_abr_list[5]-1:02d}_in',f'01_{yr_abr_list[5]:02d}_in',f'02_{yr_abr_list[5]:02d}_in',f'03_{yr_abr_list[5]:02d}_in',f'04_{yr_abr_list[5]:02d}_in',f'05_{yr_abr_list[5]:02d}_in',
                     f'06_{yr_abr_list[5]:02d}_in',f'07_{yr_abr_list[5]:02d}_in',f'08_{yr_abr_list[5]:02d}_in',f'09_{yr_abr_list[5]:02d}_in',f'10_{yr_abr_list[5]:02d}_in',f'11_{yr_abr_list[5]-1:02d}_acft',f'12_{yr_abr_list[5]-1:02d}_acft',
                     f'01_{yr_abr_list[5]:02d}_acft',f'02_{yr_abr_list[5]:02d}_acft',f'03_{yr_abr_list[5]:02d}_acft',f'04_{yr_abr_list[5]:02d}_acft',f'05_{yr_abr_list[5]:02d}_acft',
                     f'06_{yr_abr_list[5]:02d}_acft',f'07_{yr_abr_list[5]:02d}_acft',f'08_{yr_abr_list[5]:02d}_acft',f'09_{yr_abr_list[5]:02d}_acft',f'10_{yr_abr_list[5]:02d}_acft',f'{yr_list[5]}'])
    if (yr_list[0] == 1985 and yr_list[-1] == 1991) or (yr_list[0] == 2016 and yr_list[-1] == 2022):
        reg7 = '|'.join([f'GEOM_{yr_abr_list[6]:02d}','HUC','OWRD','Region','ITYPE','IRR_EFF','srctype','GRIDMET',f'IRR_STATUS_{yr_list[6]}',f'ACRES_FTR_GEOM_{yr_abr_list[6]:02d}',f'IRRIGATED_{yr_abr_list[6]:02d}',f'WETLAND_{yr_abr_list[6]:02d}',f'{yr_abr_list[6]:02d}_MODE',f'ETD_{yr_abr_list[6]:02d}',
                         f'ET_Fraction_11_{yr_abr_list[6]-1:02d}',f'ET_Fraction_12_{yr_abr_list[6]-1:02d}',f'ET_Fraction_01_{yr_abr_list[6]:02d}',f'ET_Fraction_02_{yr_abr_list[6]:02d}',
                         f'ET_Fraction_03_{yr_abr_list[6]:02d}',f'ET_Fraction_04_{yr_abr_list[6]:02d}',f'ET_Fraction_05_{yr_abr_list[6]:02d}',f'ET_Fraction_06_{yr_abr_list[6]:02d}',
                         f'ET_Fraction_07_{yr_abr_list[6]:02d}',f'ET_Fraction_08_{yr_abr_list[6]:02d}',f'ET_Fraction_09_{yr_abr_list[6]:02d}',f'ET_Fraction_10_{yr_abr_list[6]:02d}',
                         f'11_{yr_abr_list[6]-1:02d}_in',f'12_{yr_abr_list[6]-1:02d}_in',f'01_{yr_abr_list[6]:02d}_in',f'02_{yr_abr_list[6]:02d}_in',f'03_{yr_abr_list[6]:02d}_in',f'04_{yr_abr_list[6]:02d}_in',f'05_{yr_abr_list[6]:02d}_in',
                         f'06_{yr_abr_list[6]:02d}_in',f'07_{yr_abr_list[6]:02d}_in',f'08_{yr_abr_list[6]:02d}_in',f'09_{yr_abr_list[6]:02d}_in',f'10_{yr_abr_list[6]:02d}_in',f'11_{yr_abr_list[6]-1:02d}_acft',f'12_{yr_abr_list[6]-1:02d}_acft',
                         f'01_{yr_abr_list[6]:02d}_acft',f'02_{yr_abr_list[6]:02d}_acft',f'03_{yr_abr_list[6]:02d}_acft',f'04_{yr_abr_list[6]:02d}_acft',f'05_{yr_abr_list[6]:02d}_acft',
                         f'06_{yr_abr_list[6]:02d}_acft',f'07_{yr_abr_list[6]:02d}_acft',f'08_{yr_abr_list[6]:02d}_acft',f'09_{yr_abr_list[6]:02d}_acft',f'10_{yr_abr_list[6]:02d}_acft',f'{yr_list[6]}'])
    elif (yr_list[0] == 2016 and yr_list[-1] == 2023):
        reg7 = '|'.join([f'GEOM_{yr_abr_list[6]:02d}','HUC','OWRD','Region','ITYPE','IRR_EFF','srctype','GRIDMET',f'IRR_STATUS_{yr_list[6]}',f'ACRES_FTR_GEOM_{yr_abr_list[6]:02d}',f'IRRIGATED_{yr_abr_list[6]:02d}',f'WETLAND_{yr_abr_list[6]:02d}',f'{yr_abr_list[6]:02d}_MODE',f'ETD_{yr_abr_list[6]:02d}',
                         f'ET_Fraction_11_{yr_abr_list[6]-1:02d}',f'ET_Fraction_12_{yr_abr_list[6]-1:02d}',f'ET_Fraction_01_{yr_abr_list[6]:02d}',f'ET_Fraction_02_{yr_abr_list[6]:02d}',
                         f'ET_Fraction_03_{yr_abr_list[6]:02d}',f'ET_Fraction_04_{yr_abr_list[6]:02d}',f'ET_Fraction_05_{yr_abr_list[6]:02d}',f'ET_Fraction_06_{yr_abr_list[6]:02d}',
                         f'ET_Fraction_07_{yr_abr_list[6]:02d}',f'ET_Fraction_08_{yr_abr_list[6]:02d}',f'ET_Fraction_09_{yr_abr_list[6]:02d}',f'ET_Fraction_10_{yr_abr_list[6]:02d}',
                         f'11_{yr_abr_list[6]-1:02d}_in',f'12_{yr_abr_list[6]-1:02d}_in',f'01_{yr_abr_list[6]:02d}_in',f'02_{yr_abr_list[6]:02d}_in',f'03_{yr_abr_list[6]:02d}_in',f'04_{yr_abr_list[6]:02d}_in',f'05_{yr_abr_list[6]:02d}_in',
                         f'06_{yr_abr_list[6]:02d}_in',f'07_{yr_abr_list[6]:02d}_in',f'08_{yr_abr_list[6]:02d}_in',f'09_{yr_abr_list[6]:02d}_in',f'10_{yr_abr_list[6]:02d}_in',f'11_{yr_abr_list[6]-1:02d}_acft',f'12_{yr_abr_list[6]-1:02d}_acft',
                         f'01_{yr_abr_list[6]:02d}_acft',f'02_{yr_abr_list[6]:02d}_acft',f'03_{yr_abr_list[6]:02d}_acft',f'04_{yr_abr_list[6]:02d}_acft',f'05_{yr_abr_list[6]:02d}_acft',
                         f'06_{yr_abr_list[6]:02d}_acft',f'07_{yr_abr_list[6]:02d}_acft',f'08_{yr_abr_list[6]:02d}_acft',f'09_{yr_abr_list[6]:02d}_acft',f'10_{yr_abr_list[6]:02d}_acft',f'{yr_list[6]}'])
        reg8 = '|'.join([f'GEOM_{yr_abr_list[7]:02d}','HUC','OWRD','Region','ITYPE','IRR_EFF','srctype','GRIDMET',f'IRR_STATUS_{yr_list[7]}',f'ACRES_FTR_GEOM_{yr_abr_list[7]:02d}',f'IRRIGATED_{yr_abr_list[7]:02d}',f'WETLAND_{yr_abr_list[7]:02d}',f'{yr_abr_list[7]:02d}_MODE',f'ETD_{yr_abr_list[7]:02d}',
                         f'ET_Fraction_11_{yr_abr_list[7]-1:02d}',f'ET_Fraction_12_{yr_abr_list[7]-1:02d}',f'ET_Fraction_01_{yr_abr_list[7]:02d}',f'ET_Fraction_02_{yr_abr_list[7]:02d}',
                         f'ET_Fraction_03_{yr_abr_list[7]:02d}',f'ET_Fraction_04_{yr_abr_list[7]:02d}',f'ET_Fraction_05_{yr_abr_list[7]:02d}',f'ET_Fraction_06_{yr_abr_list[7]:02d}',
                         f'ET_Fraction_07_{yr_abr_list[7]:02d}',f'ET_Fraction_08_{yr_abr_list[7]:02d}',f'ET_Fraction_09_{yr_abr_list[7]:02d}',f'ET_Fraction_10_{yr_abr_list[7]:02d}',
                         f'11_{yr_abr_list[7]-1:02d}_in',f'12_{yr_abr_list[7]-1:02d}_in',f'01_{yr_abr_list[7]:02d}_in',f'02_{yr_abr_list[7]:02d}_in',f'03_{yr_abr_list[7]:02d}_in',f'04_{yr_abr_list[7]:02d}_in',f'05_{yr_abr_list[7]:02d}_in',
                         f'06_{yr_abr_list[7]:02d}_in',f'07_{yr_abr_list[7]:02d}_in',f'08_{yr_abr_list[7]:02d}_in',f'09_{yr_abr_list[7]:02d}_in',f'10_{yr_abr_list[7]:02d}_in',f'11_{yr_abr_list[7]-1:02d}_acft',f'12_{yr_abr_list[7]-1:02d}_acft',
                         f'01_{yr_abr_list[7]:02d}_acft',f'02_{yr_abr_list[7]:02d}_acft',f'03_{yr_abr_list[7]:02d}_acft',f'04_{yr_abr_list[7]:02d}_acft',f'05_{yr_abr_list[7]:02d}_acft',
                         f'06_{yr_abr_list[7]:02d}_acft',f'07_{yr_abr_list[7]:02d}_acft',f'08_{yr_abr_list[7]:02d}_acft',f'09_{yr_abr_list[7]:02d}_acft',f'10_{yr_abr_list[7]:02d}_acft',f'{yr_list[7]}'])
    elif (yr_list[0] == 2016 and yr_list[-1] == 2024):
        reg7 = '|'.join([f'GEOM_{yr_abr_list[6]:02d}','HUC','OWRD','Region','ITYPE','IRR_EFF','srctype','GRIDMET',f'IRR_STATUS_{yr_list[6]}',f'ACRES_FTR_GEOM_{yr_abr_list[6]:02d}',f'IRRIGATED_{yr_abr_list[6]:02d}',f'WETLAND_{yr_abr_list[6]:02d}',f'{yr_abr_list[6]:02d}_MODE',f'ETD_{yr_abr_list[6]:02d}',
                         f'ET_Fraction_11_{yr_abr_list[6]-1:02d}',f'ET_Fraction_12_{yr_abr_list[6]-1:02d}',f'ET_Fraction_01_{yr_abr_list[6]:02d}',f'ET_Fraction_02_{yr_abr_list[6]:02d}',
                         f'ET_Fraction_03_{yr_abr_list[6]:02d}',f'ET_Fraction_04_{yr_abr_list[6]:02d}',f'ET_Fraction_05_{yr_abr_list[6]:02d}',f'ET_Fraction_06_{yr_abr_list[6]:02d}',
                         f'ET_Fraction_07_{yr_abr_list[6]:02d}',f'ET_Fraction_08_{yr_abr_list[6]:02d}',f'ET_Fraction_09_{yr_abr_list[6]:02d}',f'ET_Fraction_10_{yr_abr_list[6]:02d}',
                         f'11_{yr_abr_list[6]-1:02d}_in',f'12_{yr_abr_list[6]-1:02d}_in',f'01_{yr_abr_list[6]:02d}_in',f'02_{yr_abr_list[6]:02d}_in',f'03_{yr_abr_list[6]:02d}_in',f'04_{yr_abr_list[6]:02d}_in',f'05_{yr_abr_list[6]:02d}_in',
                         f'06_{yr_abr_list[6]:02d}_in',f'07_{yr_abr_list[6]:02d}_in',f'08_{yr_abr_list[6]:02d}_in',f'09_{yr_abr_list[6]:02d}_in',f'10_{yr_abr_list[6]:02d}_in',f'11_{yr_abr_list[6]-1:02d}_acft',f'12_{yr_abr_list[6]-1:02d}_acft',
                         f'01_{yr_abr_list[6]:02d}_acft',f'02_{yr_abr_list[6]:02d}_acft',f'03_{yr_abr_list[6]:02d}_acft',f'04_{yr_abr_list[6]:02d}_acft',f'05_{yr_abr_list[6]:02d}_acft',
                         f'06_{yr_abr_list[6]:02d}_acft',f'07_{yr_abr_list[6]:02d}_acft',f'08_{yr_abr_list[6]:02d}_acft',f'09_{yr_abr_list[6]:02d}_acft',f'10_{yr_abr_list[6]:02d}_acft',f'{yr_list[6]}'])
        reg8 = '|'.join([f'GEOM_{yr_abr_list[7]:02d}','HUC','OWRD','Region','ITYPE','IRR_EFF','srctype','GRIDMET',f'IRR_STATUS_{yr_list[7]}',f'ACRES_FTR_GEOM_{yr_abr_list[7]:02d}',f'IRRIGATED_{yr_abr_list[7]:02d}',f'WETLAND_{yr_abr_list[7]:02d}',f'{yr_abr_list[7]:02d}_MODE',f'ETD_{yr_abr_list[7]:02d}',
                         f'ET_Fraction_11_{yr_abr_list[7]-1:02d}',f'ET_Fraction_12_{yr_abr_list[7]-1:02d}',f'ET_Fraction_01_{yr_abr_list[7]:02d}',f'ET_Fraction_02_{yr_abr_list[7]:02d}',
                         f'ET_Fraction_03_{yr_abr_list[7]:02d}',f'ET_Fraction_04_{yr_abr_list[7]:02d}',f'ET_Fraction_05_{yr_abr_list[7]:02d}',f'ET_Fraction_06_{yr_abr_list[7]:02d}',
                         f'ET_Fraction_07_{yr_abr_list[7]:02d}',f'ET_Fraction_08_{yr_abr_list[7]:02d}',f'ET_Fraction_09_{yr_abr_list[7]:02d}',f'ET_Fraction_10_{yr_abr_list[7]:02d}',
                         f'11_{yr_abr_list[7]-1:02d}_in',f'12_{yr_abr_list[7]-1:02d}_in',f'01_{yr_abr_list[7]:02d}_in',f'02_{yr_abr_list[7]:02d}_in',f'03_{yr_abr_list[7]:02d}_in',f'04_{yr_abr_list[7]:02d}_in',f'05_{yr_abr_list[7]:02d}_in',
                         f'06_{yr_abr_list[7]:02d}_in',f'07_{yr_abr_list[7]:02d}_in',f'08_{yr_abr_list[7]:02d}_in',f'09_{yr_abr_list[7]:02d}_in',f'10_{yr_abr_list[7]:02d}_in',f'11_{yr_abr_list[7]-1:02d}_acft',f'12_{yr_abr_list[7]-1:02d}_acft',
                         f'01_{yr_abr_list[7]:02d}_acft',f'02_{yr_abr_list[7]:02d}_acft',f'03_{yr_abr_list[7]:02d}_acft',f'04_{yr_abr_list[7]:02d}_acft',f'05_{yr_abr_list[7]:02d}_acft',
                         f'06_{yr_abr_list[7]:02d}_acft',f'07_{yr_abr_list[7]:02d}_acft',f'08_{yr_abr_list[7]:02d}_acft',f'09_{yr_abr_list[7]:02d}_acft',f'10_{yr_abr_list[7]:02d}_acft',f'{yr_list[7]}'])
        reg9 = '|'.join([f'GEOM_{yr_abr_list[8]:02d}','HUC','OWRD','Region','ITYPE','IRR_EFF','srctype','GRIDMET',f'IRR_STATUS_{yr_list[8]}',f'ACRES_FTR_GEOM_{yr_abr_list[8]:02d}',f'IRRIGATED_{yr_abr_list[8]:02d}',f'WETLAND_{yr_abr_list[8]:02d}',f'{yr_abr_list[8]:02d}_MODE',f'ETD_{yr_abr_list[8]:02d}',
                         f'ET_Fraction_11_{yr_abr_list[8]-1:02d}',f'ET_Fraction_12_{yr_abr_list[8]-1:02d}',f'ET_Fraction_01_{yr_abr_list[8]:02d}',f'ET_Fraction_02_{yr_abr_list[8]:02d}',
                         f'ET_Fraction_03_{yr_abr_list[8]:02d}',f'ET_Fraction_04_{yr_abr_list[8]:02d}',f'ET_Fraction_05_{yr_abr_list[8]:02d}',f'ET_Fraction_06_{yr_abr_list[8]:02d}',
                         f'ET_Fraction_07_{yr_abr_list[8]:02d}',f'ET_Fraction_08_{yr_abr_list[8]:02d}',f'ET_Fraction_09_{yr_abr_list[8]:02d}',f'ET_Fraction_10_{yr_abr_list[8]:02d}',
                         f'11_{yr_abr_list[8]-1:02d}_in',f'12_{yr_abr_list[8]-1:02d}_in',f'01_{yr_abr_list[8]:02d}_in',f'02_{yr_abr_list[8]:02d}_in',f'03_{yr_abr_list[8]:02d}_in',f'04_{yr_abr_list[8]:02d}_in',f'05_{yr_abr_list[8]:02d}_in',
                         f'06_{yr_abr_list[8]:02d}_in',f'07_{yr_abr_list[8]:02d}_in',f'08_{yr_abr_list[8]:02d}_in',f'09_{yr_abr_list[8]:02d}_in',f'10_{yr_abr_list[8]:02d}_in',f'11_{yr_abr_list[8]-1:02d}_acft',f'12_{yr_abr_list[8]-1:02d}_acft',
                         f'01_{yr_abr_list[8]:02d}_acft',f'02_{yr_abr_list[8]:02d}_acft',f'03_{yr_abr_list[8]:02d}_acft',f'04_{yr_abr_list[8]:02d}_acft',f'05_{yr_abr_list[8]:02d}_acft',
                         f'06_{yr_abr_list[8]:02d}_acft',f'07_{yr_abr_list[8]:02d}_acft',f'08_{yr_abr_list[8]:02d}_acft',f'09_{yr_abr_list[8]:02d}_acft',f'10_{yr_abr_list[8]:02d}_acft',f'{yr_list[8]}'])
        
    # use regex matches to extract columsn for output files
    df1o = df.loc[:,df.columns.str.contains(reg1)]
    df2o = df.loc[:,df.columns.str.contains(reg2)]
    df3o = df.loc[:,df.columns.str.contains(reg3)]
    df4o = df.loc[:,df.columns.str.contains(reg4)]
    df5o = df.loc[:,df.columns.str.contains(reg5)]
    df6o = df.loc[:,df.columns.str.contains(reg6)]
    
    # remove duplicate columns (static attributes)
    df1o = df1o.loc[:,~df1o.columns.duplicated()].copy()
    df2o = df2o.loc[:,~df2o.columns.duplicated()].copy()
    df3o = df3o.loc[:,~df3o.columns.duplicated()].copy()
    df4o = df4o.loc[:,~df4o.columns.duplicated()].copy()
    df5o = df5o.loc[:,~df5o.columns.duplicated()].copy()
    df6o = df6o.loc[:,~df6o.columns.duplicated()].copy()
    
    df1o = df1o.reset_index()
    df2o = df2o.reset_index()
    df3o = df3o.reset_index()
    df4o = df4o.reset_index()
    df5o = df5o.reset_index()
    df6o = df6o.reset_index()
    
    # export files to CSV's
    df1o.to_csv(os.path.join(out_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[0]}_gap_filled.csv'), index=False)
    df2o.to_csv(os.path.join(out_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[1]}_gap_filled.csv'), index=False)
    df3o.to_csv(os.path.join(out_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[2]}_gap_filled.csv'), index=False)
    df4o.to_csv(os.path.join(out_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[3]}_gap_filled.csv'), index=False)
    df5o.to_csv(os.path.join(out_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[4]}_gap_filled.csv'), index=False)
    df6o.to_csv(os.path.join(out_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[5]}_gap_filled.csv'), index=False)
    
    # additional years of processing done for certain windows
    if (yr_list[0] == 1985 and yr_list[-1] == 1991) or (yr_list[0] == 2016 and yr_list[-1] == 2022):
        
        df7o = df.loc[:,df.columns.str.contains(reg7)]
        
        df7o = df7o.loc[:,~df7o.columns.duplicated()].copy()
        
        df7o = df7o.reset_index()
    
        df7o.to_csv(os.path.join(out_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[6]}_gap_filled.csv'), index=False)
    elif (yr_list[0] == 2016 and yr_list[-1] == 2023):
        df7o = df.loc[:,df.columns.str.contains(reg7)]
        df8o = df.loc[:,df.columns.str.contains(reg8)]
        
        df7o = df7o.loc[:,~df7o.columns.duplicated()].copy()
        df8o = df8o.loc[:,~df8o.columns.duplicated()].copy()
        
        df7o = df7o.reset_index()
        df8o = df8o.reset_index()
    
        df7o.to_csv(os.path.join(out_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[6]}_gap_filled.csv'), index=False)
        df8o.to_csv(os.path.join(out_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[7]}_gap_filled.csv'), index=False)
    elif (yr_list[0] == 2016 and yr_list[-1] == 2024):
        df7o = df.loc[:,df.columns.str.contains(reg7)]
        df8o = df.loc[:,df.columns.str.contains(reg8)]
        df9o = df.loc[:,df.columns.str.contains(reg9)]
        
        df7o = df7o.loc[:,~df7o.columns.duplicated()].copy()
        df8o = df8o.loc[:,~df8o.columns.duplicated()].copy()
        df9o = df9o.loc[:,~df9o.columns.duplicated()].copy()
        
        df7o = df7o.reset_index()
        df8o = df8o.reset_index()
        df9o = df9o.reset_index()
    
        df7o.to_csv(os.path.join(out_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[6]}_gap_filled.csv'), index=False)
        df8o.to_csv(os.path.join(out_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[7]}_gap_filled.csv'), index=False)
        df9o.to_csv(os.path.join(out_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr_list[8]}_gap_filled.csv'), index=False)
    
    print('exported all annual files')
    
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