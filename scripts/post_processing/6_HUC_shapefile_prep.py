#--------------------------------
# Name:    5_HUC_shapefile_prep.py
# Desc:    HUC shapefile preparation for the HUC geodatabase
#           irrigation water use data aggregated for watersheds
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
import geopandas as gpd

dri_owrd_et_path = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(os.path.realpath(__file__)))))
sys.path.insert(0, os.path.join(dri_owrd_et_path, 'dri_owrd_et'))
sys.path.insert(0, dri_owrd_et_path)
import dri_owrd_et.inputs_post_processing as inputs
import dri_owrd_et.utils as utils

"""
HUC watershed shapefile preparation for the HUC geodatabase

"""

pp = pprint.PrettyPrinter(indent=4)


def main(ini_path=None):
    """ HUC watershed shapefile preparation for the HUC geodatabase

    Parameters
    ----------
    ini_path : str

    """

    logging.info('\nHUC8/HUC12 shapefile preparation (Step 6)')

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

    # irrigation water source type for HUC aggregations of water use variables
    src_type = ini['INPUTS']['irrigation_source_type']

    # table path
    table_path = os.path.join(root_path, 'tables', 'post_processing')
    
    in_path = os.path.join(table_path, '6_huc_geodatabase')
    
    # output path same as input for this step
    out_path = os.path.join(table_path, '6_huc_geodatabase')
    
    # shapefile location
    shp_path = os.path.join(root_path, 'shapefiles')
    
    # read the HUC shapefile into a geodataframe
    gdf = gpd.read_file(os.path.join(shp_path, f'Oregon_{huc_code}_Boundaries.shp'))
    
    # HUC name will be pulled from the dataframe instead of geodataframe
    gdf.drop(columns=[f'{huc_code}_name'], inplace=True)
    
    # read the HUC irrigation/water use stats table/CSV into a dataframe
    try:
        df = pd.read_csv(os.path.join(in_path, f'or_{huc_code.lower()}_openet_etdemands_water_year_shift_1mo_srctype_{src_type}.csv'), dtype={f'{huc_code}_code': str})
    except Exception as e:
        print(e)
        
    if huc_code == 'HUC12':
        df['HUC12_code'] = df['HUC12_code'].str.replace('.0', '', regex=False)
    
    # merge the HUC geometry geodataframe with the HUC stats table/CSV
    gdf_irr = gdf.merge(df, on=f'{huc_code}_code')
    
    # export to shapefile
    gdf_irr.to_file(os.path.join(out_path, f'or_openet_{huc_level.lower()}_irrigated_{src_type}.shp'), driver='ESRI Shapefile')
    
    print(f'{huc_code} {src_type} irrigated shapefile exported ')
    

def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='HUC Watershed Shapefile Preparation (Step 5)',
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