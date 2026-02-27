#--------------------------------
# Name:    1_file_concatenation.py
# Desc:    Concatenate all individual field
#           summaries for a given year
# Python:  3.11
#--------------------------------

import argparse
import logging
import pprint
import sys
from pathlib import Path
import os
import pandas as pd

dri_owrd_et_path = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(os.path.realpath(__file__)))))
sys.path.insert(0, os.path.join(dri_owrd_et_path, 'dri_owrd_et'))
sys.path.insert(0, dri_owrd_et_path)
import dri_owrd_et.inputs as inputs
import dri_owrd_et.utils as utils

"""
This tool concatenates all individual field summary files (static, dynamic/annual, and monthly).

All individual files are joined together using the unique ID for the field boundary dataset,
with a single file export for each year.

"""

pp = pprint.PrettyPrinter(indent=4)


def main(ini_path=None):
    """ CSV file concatenation for all field summary tables

    Parameters
    ----------
    ini_path : str

    """

    logging.info('\nConcatenating all field-level summary tables')

    # Read config file
    ini = inputs.read(ini_path)
    inputs.parse_section(ini, section='INPUTS')

    # Initialize Earth Engine API key
    logging.info('\nPost Processing Field Level Data')

    # root directory where this code repository is located on the local file system
    root_path = ini['INPUTS']['root_directory']
    
    # unique ID column/attribute for the field boundary dataset
    unique_id = ini['INPUTS']['unique_field_id']
    
    # start and end years
    start_yr = ini['INPUTS']['start_year']
    end_yr = ini['INPUTS']['end_year']
    
    # flag to export data for an individual field (True) or the entire field boundary dataset (False)
    single_field_flag = ini['INPUTS']['test_flag']

    # start/end dates for the statewide et project through 2024
    study_start = '1984-11-01'
    study_end = '2024-11-01' # exclusive
    
    # dictionary containg variables (keys) and output variable names/dataset source assetIDs (values) that are used
    dataset_dict = {
        'et': ['ETa', 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_0_pre2000', 'OpenET/ENSEMBLE/CONUS/GRIDMET/MONTHLY/v2_0'],
        'et_reference': ['ET_Reference', 'projects/openet/assets/reference_et/conus/gridmet/monthly/v1'],
        'et_fraction': ['ET_Fraction', 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_0_pre2000', 'OpenET/ENSEMBLE/CONUS/GRIDMET/MONTHLY/v2_0', 'projects/openet/assets/reference_et/conus/gridmet/monthly/v1'],
        'ppt': ['PPT', 'IDAHO_EPSCOR/GRIDMET'],
        # 'count': ['MODEL_COUNT', 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_0_pre2000', 'OpenET/ENSEMBLE/CONUS/GRIDMET/MONTHLY/v2_0']
    }
    
    ###################################################################
    
    # table path containing all earth engine export files created from the ee_zonal_stats.ipynb
    table_path = os.path.join(root_path, 'tables', 'ee_exports')
    
    # shapefile location
    shp_path = os.path.join(root_path, 'shapefiles')
    
    # output location
    out_path = os.path.join(table_path_main, 'post_processing', '2_for_et_demands_join')
    
    # list of years to process based on start/end year
    year_list = list(range(start_yr, end_yr+1))
    
    ###################################################################
    
    
    ### static attributes
    # huc attributes
    df_huc = pd.read_csv(os.path.join(table_path, 'or_field_summaries_huc_attributes.csv'), index_col='OPENET_ID')
    
    # annual crop type and gridmet ID attributes 
    df_c_pre = pd.read_csv(os.path.join(table_path, 'crop_type_codes_and_gridmet_cells.csv'), index_col='OPENET_ID')
    
    # irrigation system type, irrigation source type, efficiencies, and OWRD admin boundary attributes
    try:
        gdf_typ = gpd.read_file(os.path.join(shp_path, 'Oregon_Hyd_Area_Ag_Boundaries_20241016.shp'), columns=['OPENET_ID', 'ITYPE', 'srctype', 'IRR_EFF']).set_index('OPENET_ID')
        gdf_typ.drop(columns='geometry', inplace=True)
    except Exception as e:
        print('field boundary shapefile not found, please unzip the file so the shapefile can be read')
    
    # fill blank srctypes and efficiencies with 0's
    gdf_typ.loc[gdf_typ['srctype'].isnull(), 'srctype'] = 0
    gdf_typ.loc[gdf_typ['IRR_EFF'].isnull(), 'IRR_EFF'] = 0
    
    # cuenca region attributes
    df_cue = pd.read_csv(os.path.join(table_path, 'cuenca_regions.csv'), index_col='OPENET_ID')
    df_cue = df_cue.fillna(0)
    
    # owrd administrative basin attributes
    df_owrd = pd.read_csv(os.path.join(table_path, 'owrd_admin_bound.csv'), index_col='OPENET_ID')
    
    # bad geometries (slivers) identified and need to be removed
    df_bad = pd.read_csv(os.path.join(table_path, 'bad_geometry_list.csv'), index_col='OPENET_ID')
    bad_list = list(df_bad.index)
    
    # only process a single field if test_flag is True
    if test_flag:
        print('processing a single field: ORx_62521')
        df_huc = df_huc.loc[df_huc.index == 'ORx_62521']
        df_c_pre = df_c_pre.loc[df_c_pre.index == 'ORx_62521']
        gdf_typ = gdf_typ.loc[gdf_typ.index == 'ORx_62521']
        df_cue = df_cue.loc[df_cue.index == 'ORx_62521']
    else:
        print('processing all fields')
    
    
    # loop through each year
    for year in year_list:
    
        try:
            # ET dataframe
            df_et = pd.read_csv(os.path.join(table_path, f'or_field_summaries_water_year_shift_1mo_{year}_et.csv'), index_col='OPENET_ID')
        
            # ET Fraction dataframe
            df_etf = pd.read_csv(os.path.join(table_path, f'or_field_summaries_water_year_shift_1mo_{year}_et_fraction.csv'), index_col='OPENET_ID')
        
            # create columns for missing monthly ET flags
            # for col in df_etf.columns:
            #     df_etf[col+"_missing"] = df_etf[col].isnull()
                
            # ET Reference dataframe
            df_eto = pd.read_csv(os.path.join(table_path, f'or_field_summaries_water_year_shift_1mo_{year}_et_reference.csv'), index_col='OPENET_ID')
        
            # Crop Type and gridmet ID dataframe
            df_c = df_c_pre[[f'CROP_{year}', 'GRIDMET_ID']]
        
            # precip dataframe
            df_ppt = pd.read_csv(os.path.join(table_path, f'or_field_summaries_water_year_shift_1mo_{year}_ppt.csv'), index_col='OPENET_ID') 
                
            # IrrMapper Irrigated dataframe
            df_irr = pd.read_csv(os.path.join(table_path, f'or_field_summaries_{year}_irrmapper_irrigated.csv'), index_col='OPENET_ID')
            df_irr[f'%_IRRIGATED_{str(year)[2:]}'] = (df_irr['ACRES_IRRIGATED'] / df_irr['ACRES_ALL']) * 100
            df_irr = df_irr[[f'%_IRRIGATED_{str(year)[2:]}']]
        
            # IrrMapper Wetland dataframe
            df_wtl = pd.read_csv(os.path.join(table_path, f'or_field_summaries_{year}_irrmapper_wetland.csv'), index_col='OPENET_ID')
            df_wtl[f'%_WETLAND_{str(year)[2:]}'] = (df_wtl['ACRES_WETLAND'] / df_wtl['ACRES_ALL']) * 100
            df_wtl = df_wtl[[f'%_WETLAND_{str(year)[2:]}']]
        
            # EToF irrigation status dataframe
            df_etof_irr_status = pd.read_csv(os.path.join(table_path, f'or_field_summaries_{year}_etof_irr_status.csv'), index_col='OPENET_ID')
            
        except Exception as e:
            print(e)
    
        # unclassified field nans need to be filled with code 5 for filtering (they are assumed irrigated since they are usually small polygons for single home lawns)
        df_etof_irr_status[f'ETOF_IRR_STATUS_{str(year)[2:]}_MODE'] =  df_etof_irr_status[f'ETOF_IRR_STATUS_{str(year)[2:]}_MODE'].fillna(5)
        df_etof_irr_status[[f'ETOF_IRR_STATUS_{str(year)[2:]}_MODE']]
    
        # concatenate dataframes on columns using index (unique ID) to match fields
        df = pd.concat([df_huc, df_cue, df_owrd, gdf_typ, df_c, df_irr, df_wtl, df_etof_irr_status, df_et, df_etf, df_eto, df_ppt], axis=1)
    
        # filter out bad geometries
        df = df.loc[~df.index.isin(bad_list)]
    
        # create irrigation status column based on the following criteria
        # 1. IrrMapper % Irrigated > 40%
        # 2. IrrMapper % Irrigated <= 40% AND IrrMapper % Wetland > 40% AND non-zero irrigation source type AND EToF Classification is 2, 3, or 5 (irrigated, shorted, unclassified/assumed irrigated)
        # first initialize the new irrigation status column with 0s
        df[f'IRR_STATUS_{year}'] = 0
        df.loc[(df[f'%_IRRIGATED_{str(year)[2:]}'] > 40) | ((df[f'%_IRRIGATED_{str(year)[2:]}'] <= 40) & (df[f'%_WETLAND_{str(year)[2:]}'] > 40) & (df['srctype'] != 0) & (df[f'ETOF_IRR_STATUS_{str(year)[2:]}_MODE'].isin([2,3,5]))), f'IRR_STATUS_{year}'] = 1 
        
        # reset the index
        df = df.reset_index()
    
        # export joined dataframe for pairing with ET Demands
        df.to_csv(os.path.join(out_path, f'or_field_summaries_water_year_shift_1mo_{year}_pre_et_demands.csv'), index=False)
            
        print(f'exported dataframe for {year}')
    

def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='Earth Engine Field-Level Monthly ET Zonal Stats Table Export',
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