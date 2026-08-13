#--------------------------------
# Name:    7_HUC_geopackage_prep.py
# Desc:    convert HUC summary CSV files into a geopackage
#           format
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
# Set pyogrio as the IO engine
gpd.options.io_engine = "pyogrio"

dri_owrd_et_path = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(os.path.realpath(__file__)))))
sys.path.insert(0, os.path.join(dri_owrd_et_path, 'dri_owrd_et'))
sys.path.insert(0, dri_owrd_et_path)
import dri_owrd_et.inputs_post_processing as inputs
import dri_owrd_et.utils as utils

"""
HUC geopackage preparation of HUC level irrigation water use volumes.

"""

pp = pprint.PrettyPrinter(indent=4)


def main(ini_path=None):
    """ HUC geopackage preparation (Step 7)

    Parameters
    ----------
    ini_path : str

    """

    logging.info('\nHUC Watershed Geopackage Preparation')

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
    
    #---------------------------------------------------------------
    
    # specify the HUC-levels to process (HUC8 and HUC12 only)
    huc_level_list = ['HUC8', 'HUC12']
    
    # filter by irrigation source type (all, groundwater, and surface_water only)
    # "all" does not do any filtering of irrigation source type and includes all irrigated fields
    src_type_list = ['all', 'groundwater', 'surface_water']
    
    #---------------------------------------------------------------
        
    # table path
    table_path_main = os.path.join(root_path, 'tables')
    table_path = os.path.join(table_path_main, 'post_processing')
    table_path_ee = os.path.join(table_path_main, 'ee_exports')
    
    in_path = os.path.join(table_path, '6_huc_geodatabase')
    
    out_path = os.path.join(table_path, '8_huc_geopackage')
    
    # shapefile location
    shp_path = os.path.join(root_path, 'shapefiles')
    
    
    def add_multiple_gdf_to_gpkg(gdf_dict, output_gpkg_path):
        """
        Adds multiple GeoDataFrames to a GeoPackage as separate layers.
    
        Args:
            gdf_dict (dict): A dictionary where keys are layer names and values are GeoDataFrames.
            output_path (str): The path to the output GeoPackage file.

            updates geopackage in place
        """
        for layer_name, gdf in gdf_dict.items():
    
            gdf.to_file(output_gpkg_path, layer=layer_name, driver='GPKG')
    
    
    # output geopackage path
    output_gpkg = os.path.join(out_path, f'or_huc_geopackage_{start_yr}_{end_yr}.gpkg')

    if os.path.isfile(output_gpkg):
        print('HUC-level geopackage already exists, overwriting now')
        os.remove(output_gpkg)
    
    # empty dictionary to fill with geodataframes
    gdf_dict = {}
    
    # loop through HUC8 and HUC12 aggregations
    for huc_level in huc_level_list:
    
        # read HUC shapefile into a geodataframe
        gdf = gpd.read_file(os.path.join(shp_path, f'Oregon_{huc_level}_Boundaries.shp')).set_index(f'{huc_level}_code')
        gdf.drop(columns=[f'{huc_level}_name'], inplace=True)
        
        # loop through each source type (all, groundwater, and surface_water)
        for src_type in src_type_list:

            filename = f'or_{huc_level.lower()}_openet_etdemands_water_year_shift_1mo_srctype_{src_type}.csv'

            if not os.path.isfile(os.path.join(in_path, filename)):
                print(f'no {huc_level} {src_type} irrigation source(s) type file, skipping')

            else:
                # read the HUC irrigation/water use stats table/CSV into a dataframe
                try:
                    df = pd.read_csv(os.path.join(in_path, filename), dtype={f'{huc_level}_code': str})
                except Exception as e:
                    print(e)
                
                df[f'{huc_level}_code'] = df[f'{huc_level}_code'].str.replace('.0', '', regex=False)
                
                # merge the HUC geometry geodataframe with the HUC stats table/CSV
                gdf_irr = gdf.merge(df, on=f'{huc_level}_code')
        
                # add geodataframe to the dictionary
                gdf_dict[f'or_openet_{huc_level.lower()}_irrigated_{src_type}'] = gdf_irr
    
        try:
            # read in the stats tables for small pond evaporation
            df_evap_monthly = pd.read_csv(os.path.join(table_path_ee, f'or_gridmet_{huc_level.lower()}_summaries_monthly_eto_small_pond_evap_inches.csv'), dtype={f'{huc_level}_code': str}, index_col=f'{huc_level}_code')
            df_evap_climo = pd.read_csv(os.path.join(table_path_ee, f'or_gridmet_{huc_level.lower()}_summaries_monthly_climo_eto_small_pond_evap_inches.csv'),  dtype={f'{huc_level}_code': str}, index_col=f'{huc_level}_code') 
        except Exception as e:
            print("HUC-level small pond evaporation summaries were not found, please check that they exist in the 'ee_exports' sub folder")
            
        # merge HUC geometry geodataframe with the small pond evaporation stats table
        gdf_monthly = gdf.merge(df_evap_monthly, on=f'{huc_level}_code')
        gdf_climo = gdf.merge(df_evap_climo, on=f'{huc_level}_code')
    
        # add geodataframes to the dictionary
        gdf_dict[f'or_gridmet_{huc_level.lower()}_monthly_eto_small_pond_evap_inches'] = gdf_monthly
        gdf_dict[f'or_gridmet_{huc_level.lower()}_monthly_climo_eto_small_pond_evap_inches'] = gdf_climo
    
    # Add the GeoDataFrames to the GeoPackage
    add_multiple_gdf_to_gpkg(gdf_dict, output_gpkg)
    print('finished building HUC-level irrigation/water use and small pond evaporation geopackage')

def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='HUC Watershed Geopackage Preparatation of HUC Level Volumes (Step 7)',
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