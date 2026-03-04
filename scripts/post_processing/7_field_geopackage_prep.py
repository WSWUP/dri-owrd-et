#--------------------------------
# Name:    7_field_geopackage_prep.py
# Desc:    convert field summary CSV files into a geopackage
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
Convert individual field summary CSVs into a geopackge

"""

pp = pprint.PrettyPrinter(indent=4)


def main(ini_path=None):
    """ Field Geopackage preparation

    Parameters
    ----------
    ini_path : str

    """

    logging.info('\nField-Level Geopackage preparation (Step 7)')

    # Read config file
    ini = inputs.read(ini_path)
    inputs.parse_section(ini, section='INPUTS')

    # root directory where this code repository is located on the local file system
    root_path = ini['INPUTS']['root_directory']

    # field boundary shapefile name
    shapefile_name = ini['INPUTS']['field_boundary_shapefile_name']
    shapefile_sub = shapefile_name.split('.')[0]
    
    # unique ID column/attribute for the field boundary dataset
    unique_id = ini['INPUTS']['unique_field_id']
    
    # start and end years
    start_yr = ini['INPUTS']['start_year']
    end_yr = ini['INPUTS']['end_year']
    
    # table path
    table_path = os.path.join(root_path, 'tables', 'post_processing')
    
    in_path = os.path.join(table_path, '5_field_geodatabase')
    
    out_path = os.path.join(table_path, '7_field_geopackage')
    
    # list of years based on start/end parameters
    year_list = list(range(start_yr, end_yr+1))
    
    # shapefile location
    shp_path = os.path.join(root_path, 'shapefiles')
    
    def add_multiple_gdf_to_gpkg(gdf_dict, output_gpkg_path, chunk_size: int=20000):
        """
        Adds multiple GeoDataFrames to a GeoPackage as separate layers.
    
        Args:
            gdf_dict (dict): A dictionary where keys are layer names and values are GeoDataFrames.
            output_path (str): The path to the output GeoPackage file.
            chunk_size (int): The size of the dataframe chunk/subset (i.e., row-wise chunk)

            updates geopackage in place
        """
        for layer_name, gdf in gdf_dict.items():
    
            for i in range(0, len(gdf), chunk_size):
    
                chunk = gdf[i : i + chunk_size]
                
                gdf_chunk = gpd.GeoDataFrame(chunk, geometry='geometry')
                
                if i == 0:
                    gdf_chunk.to_file(output_gpkg_path, layer=layer_name, driver='GPKG')
                else:
                    gdf_chunk.to_file(output_gpkg_path, layer=layer_name, driver='GPKG', mode='a')
    
    # field boundary attributes
    field_attr_vars = [
        unique_id, 'SOURCECODE', 'MGRS_TILE', 'Acres', 'CLAY_WTA_L', 'CLAY_WTA_H', 'Ksat_WTA_L', 
        'Ksat_WTA_H', 'SAND_WTA_L', 'SAND_WTA_H', 'AWC_WTA_L', 'AWC_WTA_H', 'API_ID', 'geometry'
    ]
    
    # static table attributes
    static_vars = [
        'ACRES_FTR_GEOM', 'GRIDMET_ID', 'HUC8', 'HUC8_name', 'HUC12', 
        'HUC12_name', 'IRR_EFF', 'ITYPE', 'OWRD', 'Region', 'srctype', 'geometry'
    ]
    # static attribute dataframe column selection function
    static_var_sel = lambda x: unique_id in x  or 'ACRES_FTR_GEOM' in x or 'GRIDMET_ID' in x or 'HUC8' in x or 'HUC8_name' in x or 'HUC12' in x or \
                               'HUC12_name' in x or 'IRR_EFF' in x or 'ITYPE' in x or 'OWRD' in x or 'Region' in x or 'srctype' in x
    
    # timeseries attributes
    timeseries_vars = [
        'per_IRRIGATED','per_WETLAND','CROP','ETD','ETOF_IRR_STATUS', 'IRR_STATUS',
        'AW','EFF_VOLUME','EFF_VOLUMEadj','ET_Fraction','ET_Reference',
        'ET_VOLUME','ETa','ETDa','ETDa_VOLUME','ETO_VOLUME','IRR_CU_VOLUME',
        'IRR_CU_VOLUMEadj','NIWR','NIWR_VOLUME','P_eft','P_rz','PPT',
        'PPT_VOLUME','WS_C'
    ]
    
    # timeseries attribute dataframe column selection function
    timeseries_var_sel = lambda x: unique_id in x or '%_IRRIGATED' in x or '%_WETLAND' in x or 'CROP' in x or 'ETD' in x or 'IRR_STATUS' in x or 'AW' in x or \
                                   'EFF_VOLUME' in x or 'EFF_VOLUMEadj' in x or 'ET_Fraction' in x  or 'ET_Reference' in x or 'ET_VOLUME' in x or \
                                   'ETa' in x or 'ETDa' in x or 'ETDa_VOLUME' in x or 'ETO_VOLUME' in x or 'IRR_CU_VOLUME' in x or 'IRR_CU_VOLUMEadj' in x or \
                                   'NIWR' in x or 'NIWR_VOLUME' in x or 'P_eft' in x or 'P_rz' in x or 'PPT' in x or 'PPT_VOLUME' in x or 'WS_C' in x
    
    # output geopackage path
    output_gpkg = os.path.join(out_path, 'or_field_geopackage.gpkg')
    
    if os.path.isfile(output_gpkg):
        os.remove(output_gpkg)
    
    # field boundary dataframe with geometries
    field_gdf_pre = gpd.read_file(os.path.join(shp_path, shapefile_name), columns=field_attr_vars).set_index(unique_id)
    
    # static attribute dataframe is pulled from the first year that is specified
    try:
        static_df = pd.read_csv(os.path.join(in_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{start_yr}_final.csv'), index_col=unique_id, 
                                usecols=static_var_sel)
    except Exception as e:
        print(e)
        
    static_df.rename(columns={f'ACRES_FTR_GEOM_{str(start_yr)[2:]}': 'ACRES_FTR_GEOM'}, inplace=True)
    
    # join the static attributes to the field boundaries for its own layer in the geopackage
    field_gdf = field_gdf_pre.merge(static_df, on=unique_id)
    
    gdf_dict = {
        shapefile_sub: field_gdf,
    }
    
    field_gdf_sub = field_gdf[static_vars]
    
    
    for year in year_list:
    
        try:
            # timeseries dataframe for the current year in the loop
            select_year_df = pd.read_csv(os.path.join(in_path, f'or_openet_etdemands_monthly_water_year_shift_1mo_{year}_final.csv'), dtype={unique_id: str}, index_col=unique_id, 
                                         usecols=timeseries_var_sel)
        except Exception as e:
            print(e)
    
        # rename columns starting with %
        select_year_df.rename(columns={f'%_IRRIGATED_{str(year)[2:]}': f'per_IRRIGATED_{str(year)[2:]}', f'%_WETLAND_{str(year)[2:]}': f'per_WETLAND_{str(year)[2:]}'}, inplace=True)
    
        for timeseries_var in timeseries_vars:
    
            if timeseries_var not in gdf_dict:
                # print(f'{timeseries_var} not in datafframe, adding now')
    
                # add the static dataframe to the dictionary so that timeseries variables can be added
                gdf_dict[timeseries_var] = field_gdf_sub
    
            # list of timeseries columns for the current variable in loop
            if timeseries_var == 'IRR_STATUS':
                filtered_cols = [col for col in select_year_df.columns if (timeseries_var in col and 'ETOF' not in col)]
            elif timeseries_var == 'ETD':
                filtered_cols = [col for col in select_year_df.columns if (timeseries_var in col and 'ETDa' not in col)]
            elif (timeseries_var == 'ETDa' or timeseries_var == 'NIWR' or timeseries_var == 'PPT'):
                filtered_cols = [col for col in select_year_df.columns if (timeseries_var in col and '_in' in col)]
            elif (timeseries_var == 'EFF_VOLUME') or (timeseries_var == 'IRR_CU_VOLUME'):
                filtered_cols = [col for col in select_year_df.columns if (timeseries_var in col and 'adj' not in col)]
            else:
                filtered_cols = [col for col in select_year_df.columns if timeseries_var in col]
            
            # filtered timeseries dataframe for the current variable
            select_year_df_var = select_year_df[filtered_cols]
    
            # concatenate the timeseries dataframe to the existing one that was created for the current variable in loop
            gdf_dict[timeseries_var] = gdf_dict[timeseries_var].merge(select_year_df_var, on=unique_id)
    
    # Add the GeoDataFrames to the GeoPackage
    add_multiple_gdf_to_gpkg(gdf_dict, output_gpkg)
    print('finished building field-level irrigation/water use geopackage')

    
def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='Field-Level Geopackage Preparation (Step 7)',
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