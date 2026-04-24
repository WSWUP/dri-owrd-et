#--------------------------------
# Name:    5_HUC_aggregations.py
# Desc:    HUC watershed aggregations of field level irrigation 
#           water use volumes
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
import dri_owrd_et.inputs_post_processing as inputs
import dri_owrd_et.utils as utils

"""
HUC watershed aggregations of field level irrigation water use volumes.

"""

pp = pprint.PrettyPrinter(indent=4)


def main(ini_path=None):
    """ HUC watershed aggregations

    Parameters
    ----------
    ini_path : str

    """

    logging.info('\nHUC8/HUC12 watershed aggregations of field-level volumes (Step 5)')

    # Read config file
    ini = inputs.read(ini_path)
    inputs.parse_section(ini, section='INPUTS')

    # root directory where this code repository is located on the local file system
    root_path = ini['INPUTS']['root_directory']
    
    # unique ID column/attribute for the field boundary dataset
    unique_id = ini['INPUTS']['unique_field_id']

    # HUC level to aggregate the field summary volumes by (HUC8 or HUC12)
    huc_code = ini['INPUTS']['huc_level']
    
    # start and end years
    start_yr = ini['INPUTS']['start_year']
    end_yr = ini['INPUTS']['end_year']

    # table path
    table_path = os.path.join(root_path, 'tables', 'post_processing')
    
    in_path = os.path.join(table_path, '5_field_geodatabase')
    
    out_path = os.path.join(table_path, '6_huc_geodatabase')
    
    # list of years based on start/end year parameters
    year_list = list(range(start_yr, end_yr+1))
    
    # irrmapper irrigated filter (>40 % of the field-area is considered irrigated)
    irr_val = 40
    
    # irrmapper wetland filter
    wetland_val = 40
    

    for src_type in ['all', 'groundwater', 'surface_water']:

        # empty dataframe to concatenate individual years of data to
        df_out = pd.DataFrame([])
            
        # empty huc code/name dictionary to build for filling in missing names in the output (b/c for some hucs, certain years didn't have irrigated fields)
        huc_dict = {}
        
        for yr in year_list:
        
            try:
                # read file into a dataframe
                df_1 = pd.read_csv(os.path.join(in_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr}_final.csv.gz'))
            except Exception as e:
                print(e)
    
            # update the huc dictionary with the codes/names
            huc_dict_sub = df_1[[huc_code, f'{huc_code}_name']].drop_duplicates(huc_code).set_index(huc_code)[f'{huc_code}_name'].to_dict()
            huc_dict.update(huc_dict_sub)
            
            # filter fields using IrrMapper irrigated > 40% OR (IrrMapper irrigated < 40% & IrrMapper wetland > 40% & srctype non zero & EToF not equal to 1)
            # df_1 = df_1.loc[(df_1[f'%_IRRIGATED_{str(yr)[2:]}'] > irr_val) | ((df_1[f'%_IRRIGATED_{str(yr)[2:]}'] <= irr_val) & (df_1[f'%_WETLAND_{str(yr)[2:]}'] > wetland_val) & (df_1['srctype'] != 0) & (df_1[f'ETOF_IRR_STATUS_{str(yr)[2:]}_MODE'].isin([2,3,5])))]
            # new addition just uses the irrigation status attribute that was added in 2025, based on the above conditionals
            df_1 = df_1.loc[df_1[f'IRR_STATUS_{yr}'] == 1]
            
            # irrigation source type filtering
            if src_type == 'groundwater':
                df_1 = df_1.loc[df_1['srctype'].isin([1, 3])]
                
            elif src_type == 'surface_water':
                df_1 = df_1.loc[df_1['srctype'].isin([2, 3])]
    
            
            df_1[f'ACRES_{str(yr)[2:]}'] = df_1[f'ACRES_FTR_GEOM_{str(yr)[2:]}']
            
            # sum monthly column values to get annual totals for each field/row
            df_1[f'ET_v_{str(yr)[2:]}'] = df_1.loc[:, df_1.columns.str.contains('ET_VOLUME')].sum(axis=1)
            df_1[f'ETc_v_{str(yr)[2:]}'] = df_1.loc[:, df_1.columns.str.contains('ETDa_VOLUME')].sum(axis=1)
            df_1[f'ETo_v_{str(yr)[2:]}'] = df_1.loc[:, df_1.columns.str.contains('ETO_VOLUME')].sum(axis=1)
            df_1[f'PPT_v_{str(yr)[2:]}'] = df_1.loc[:, df_1.columns.str.contains('PPT_VOLUME')].sum(axis=1)
            df_1[f'EFF_v_{str(yr)[2:]}'] = df_1.loc[:, df_1.columns.str.contains('EFF_VOLUMEadj')].sum(axis=1)
            df_1[f'NIWR_v_{str(yr)[2:]}'] = df_1.loc[:, df_1.columns.str.contains('NIWR_VOLUME')].sum(axis=1)
            df_1[f'CU_v_{str(yr)[2:]}'] = df_1.loc[:, df_1.columns.str.contains('IRR_CU_VOLUMEadj')].sum(axis=1)
            df_1[f'AW_v_{str(yr)[2:]}'] = df_1.loc[:, df_1.columns.str.contains('AW_')].sum(axis=1)
        
            # locate mix source type fields and threshold the ET, EFF, CU and AW to be half to split surface/groundwater
            if (src_type == 'groundwater' or src_type == 'surface_water'):
                df_1.loc[df_1['srctype'] == 3, f'ET_v_{str(yr)[2:]}'] = df_1[f'ET_v_{str(yr)[2:]}'] * 0.5
                df_1.loc[df_1['srctype'] == 3, f'ETc_v_{str(yr)[2:]}'] = df_1[f'ETc_v_{str(yr)[2:]}'] * 0.5
                df_1.loc[df_1['srctype'] == 3, f'ETo_v_{str(yr)[2:]}'] = df_1[f'ETo_v_{str(yr)[2:]}'] * 0.5
                df_1.loc[df_1['srctype'] == 3, f'PPT_v_{str(yr)[2:]}'] = df_1[f'PPT_v_{str(yr)[2:]}'] * 0.5
                df_1.loc[df_1['srctype'] == 3, f'EFF_v_{str(yr)[2:]}'] = df_1[f'EFF_v_{str(yr)[2:]}'] * 0.5
                df_1.loc[df_1['srctype'] == 3, f'NIWR_v_{str(yr)[2:]}'] = df_1[f'NIWR_v_{str(yr)[2:]}'] * 0.5
                df_1.loc[df_1['srctype'] == 3, f'CU_v_{str(yr)[2:]}'] = df_1[f'CU_v_{str(yr)[2:]}'] * 0.5
                df_1.loc[df_1['srctype'] == 3, f'AW_v_{str(yr)[2:]}'] = df_1[f'AW_v_{str(yr)[2:]}'] * 0.5
        
            # groupby each huc or region and sum up the volumes
            df_1_group1 = df_1[[f'ACRES_{str(yr)[2:]}', f'ET_v_{str(yr)[2:]}', f'ETc_v_{str(yr)[2:]}', f'ETo_v_{str(yr)[2:]}', f'PPT_v_{str(yr)[2:]}', f'EFF_v_{str(yr)[2:]}',
                                f'NIWR_v_{str(yr)[2:]}', f'CU_v_{str(yr)[2:]}', f'AW_v_{str(yr)[2:]}', huc_code]].groupby(huc_code).sum()

            # area-weighted average rates
            df_1_group1[f'ET_r_{str(yr)[2:]}'] = df_1_group1[f'ET_v_{str(yr)[2:]}'] / df_1_group1[f'ACRES_{str(yr)[2:]}']
            df_1_group1[f'ETc_r_{str(yr)[2:]}'] = df_1_group1[f'ETc_v_{str(yr)[2:]}'] / df_1_group1[f'ACRES_{str(yr)[2:]}']
            df_1_group1[f'ETo_r_{str(yr)[2:]}'] = df_1_group1[f'ETo_v_{str(yr)[2:]}'] / df_1_group1[f'ACRES_{str(yr)[2:]}']
            df_1_group1[f'PPT_r_{str(yr)[2:]}'] = df_1_group1[f'PPT_v_{str(yr)[2:]}'] / df_1_group1[f'ACRES_{str(yr)[2:]}']
            df_1_group1[f'EFF_r_{str(yr)[2:]}'] = df_1_group1[f'EFF_v_{str(yr)[2:]}'] / df_1_group1[f'ACRES_{str(yr)[2:]}']
            df_1_group1[f'NIWR_r_{str(yr)[2:]}'] = df_1_group1[f'NIWR_v_{str(yr)[2:]}'] / df_1_group1[f'ACRES_{str(yr)[2:]}']
            df_1_group1[f'CU_r_{str(yr)[2:]}'] = df_1_group1[f'CU_v_{str(yr)[2:]}'] / df_1_group1[f'ACRES_{str(yr)[2:]}']   
            df_1_group1[f'AW_r_{str(yr)[2:]}'] = df_1_group1[f'AW_v_{str(yr)[2:]}'] / df_1_group1[f'ACRES_{str(yr)[2:]}']
        
            # concatenate individual years to the output dataframe
            df_1_group2 = df_1[[f'{huc_code}_name', huc_code]].groupby(huc_code).first()
        
            df = pd.concat([df_1_group2, df_1_group1], axis=1)
        
            data = [df_out, df]
            df_out = pd.concat(data, axis=1)
            df_out = df_out.loc[:, ~df_out.columns.duplicated()].copy()

        if len(df_out) == 0:
            logging.info(f"\nNo '{src_type}' source types for the field(s) being processed, skipping")

        else:
            df_out = df_out.loc[:, ~df_out.columns.duplicated()].copy()
            df_out = df_out.reset_index()
    
            df_out = df_out.set_index([huc_code, f'{huc_code}_name'])
            df_out = df_out.reset_index()
        
            df_out[f'{huc_code}_name'] = df_out[f'{huc_code}_name'].fillna(df_out[huc_code].map(huc_dict))
            
            df_out.rename(columns={huc_code: f'{huc_code}_code'}, inplace=True)
                
            # long-term average of the area-weighted average Nov-Oct rates and volumes
            # df_out.replace("", np.nan, inplace=True)
            df_out['ET_v'] = df_out.loc[:, df_out.columns.str.contains('ET_v')].mean(axis=1)
            df_out['ET_r'] = df_out.loc[:, df_out.columns.str.contains('ET_r')].mean(axis=1)
            df_out['ETc_v'] = df_out.loc[:, df_out.columns.str.contains('ETc_v')].mean(axis=1)
            df_out['ETc_r'] = df_out.loc[:, df_out.columns.str.contains('ETc_r')].mean(axis=1)
            df_out['ETo_v'] = df_out.loc[:, df_out.columns.str.contains('ETo_v')].mean(axis=1)
            df_out['ETo_r'] = df_out.loc[:, df_out.columns.str.contains('ETo_r')].mean(axis=1)
            df_out['PPT_v'] = df_out.loc[:, df_out.columns.str.contains('PPT_v')].mean(axis=1)
            df_out['PPT_r'] = df_out.loc[:, df_out.columns.str.contains('PPT_r')].mean(axis=1)
            df_out['EFF_v'] = df_out.loc[:, df_out.columns.str.contains('EFF_v')].mean(axis=1)
            df_out['EFF_r'] = df_out.loc[:, df_out.columns.str.contains('EFF_r')].mean(axis=1)
            df_out['NIWR_v'] = df_out.loc[:, df_out.columns.str.contains('NIWR_v')].mean(axis=1)
            df_out['NIWR_r'] = df_out.loc[:, df_out.columns.str.contains('NIWR_r')].mean(axis=1)
            df_out['CUirr_v'] = df_out.loc[:, df_out.columns.str.contains('CU_v')].mean(axis=1)
            df_out['CUirr_r'] = df_out.loc[:, df_out.columns.str.contains('CU_r')].mean(axis=1)    
            df_out['AW_v'] = df_out.loc[:, df_out.columns.str.contains('AW_v')].mean(axis=1)
            df_out['AW_r'] = df_out.loc[:, df_out.columns.str.contains('AW_r')].mean(axis=1)   

            df_out = df_out.fillna(0)
            
            df_out.to_csv(os.path.join(out_path, fr'or_{huc_code.lower()}_openet_etdemands_water_year_shift_1mo_srctype_{src_type}.csv'), index=False)
            logging.info(f'\nexported {huc_code.lower()} {src_type} source(s) table')


def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='HUC Watershed Aggregations of Field Level Volumes (Step 5)',
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