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
import datetime
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

    logging.info('\nConcatenating all field-level summary tables (Step 1)')

    # Read config file
    ini = inputs.read(ini_path)
    inputs.parse_section(ini, section='INPUTS')

    # root directory where this code repository is located on the local file system
    root_path = ini['INPUTS']['root_directory']

    # field boundary shapefile name
    shapefile_name = ini['INPUTS']['field_boundary_shapefile_name']

    # unique ID column/attribute for the field boundary dataset
    unique_id = ini['INPUTS']['unique_field_id']
    
    # start and end years
    start_yr = ini['INPUTS']['start_year']
    end_yr = ini['INPUTS']['end_year']
    
    # flag to export data for an individual field (True) or the entire field boundary dataset (False)
    single_field_flag = ini['INPUTS']['test_flag']

    def concat_field_summaries(year_list, paths, unique_id, bad_list, df_huc, df_cue, df_owrd, gdf_typ, df_c_pre):
        """
        Concatenate all field summary tables for each water year.
    
        Parameters
        ----------
        year_list : list of int
            Water years to process
        paths : dict
            Dictionary of paths to CSVs
        unique_id : str
            Unique ID column for joining
        bad_list : list
            List of bad geometries to filter
        df_huc, df_cue, df_owrd, gdf_typ, df_c_pre : DataFrames
            Static attribute data
    
        Returns
        -------
        None (writes out per-year CSVs)
        """
    
        for year in year_list:
            yr_str = str(year)
            yr_abbr = yr_str[2:]
    
            # Build a list of DataFrames to concat
            dfs_to_concat = []
    
            # Static attributes
            dfs_to_concat.extend([df_huc, df_cue, df_owrd, gdf_typ, df_c_pre[[f'CROP_{year}', 'GRIDMET_ID']]])
    
            # Dynamic tables (ET, ET Fraction, ET Reference, PPT)
            dynamic_files = {
                'df_et': f'or_field_summaries_water_year_shift_1mo_{year}_et.csv',
                'df_etf': f'or_field_summaries_water_year_shift_1mo_{year}_et_fraction.csv',
                'df_eto': f'or_field_summaries_water_year_shift_1mo_{year}_et_reference.csv',
                'df_ppt': f'or_field_summaries_water_year_shift_1mo_{year}_ppt.csv'
            }
            for key, fname in dynamic_files.items():
                try:
                    dfs_to_concat.append(pd.read_csv(os.path.join(paths['table_path'], fname), index_col=unique_id))

                except FileNotFoundError:
                    print(f"Warning: {fname} not found.")
                    continue
                    
            # Irrigation / wetland
            df_irr = pd.read_csv(os.path.join(paths['table_path'], f'or_field_summaries_{year}_irrmapper_irrigated.csv'), index_col=unique_id)
            df_irr[f'%_IRRIGATED_{yr_abbr}'] = (df_irr['ACRES_IRRIGATED'] / df_irr['ACRES_ALL']) * 100
            dfs_to_concat.append(df_irr[[f'%_IRRIGATED_{yr_abbr}']])
    
            df_wtl = pd.read_csv(os.path.join(paths['table_path'], f'or_field_summaries_{year}_irrmapper_wetland.csv'), index_col=unique_id)
            df_wtl[f'%_WETLAND_{yr_abbr}'] = (df_wtl['ACRES_WETLAND'] / df_wtl['ACRES_ALL']) * 100
            dfs_to_concat.append(df_wtl[[f'%_WETLAND_{yr_abbr}']])
    
            df_etof = pd.read_csv(os.path.join(paths['table_path'], f'or_field_summaries_{year}_etof_irr_status.csv'), index_col=unique_id)
            df_etof[f'ETOF_IRR_STATUS_{yr_abbr}_MODE'] = df_etof[f'ETOF_IRR_STATUS_{yr_abbr}_MODE'].fillna(5)
            dfs_to_concat.append(df_etof[[f'ETOF_IRR_STATUS_{yr_abbr}_MODE']])
    
            # Concatenate all
            df_combined = pd.concat(dfs_to_concat, axis=1)
    
            # Filter bad geometries
            df_combined = df_combined.loc[~df_combined.index.isin(bad_list)]
    
            # Create irrigation status
            df_combined[f'IRR_STATUS_{year}'] = (
                (df_combined[f'%_IRRIGATED_{yr_abbr}'] > 40) |
                ((df_combined[f'%_IRRIGATED_{yr_abbr}'] <= 40) &
                 (df_combined[f'%_WETLAND_{yr_abbr}'] > 40) &
                 (df_combined['srctype'] != 0) &
                 (df_combined[f'ETOF_IRR_STATUS_{yr_abbr}_MODE'].isin([2,3,5])))
            ).astype(int)

            # remove duplicate columns
            df_combined = df_combined.loc[:, ~df_combined.columns.duplicated()].copy()
            
            # Reset index and save
            df_combined.reset_index().to_csv(
                os.path.join(paths['out_path'], f'or_field_summaries_water_year_shift_1mo_{year}_pre_et_demands.csv.gz'),
                index=False, compression='gzip'
            )
            print(f'Exported dataframe for {year}')
    
    # --- Configuration and paths ---
    table_path = os.path.join(root_path, "tables", "ee_exports")
    supp_path = os.path.join(root_path, "tables", "supplemental")
    shp_path = os.path.join(root_path, "shapefiles")
    out_path = os.path.join(root_path, "tables", "post_processing", "2_for_et_demands_join")
    
    paths = {
        "table_path": table_path,
        "supp_path": supp_path,
        "shp_path": shp_path,
        "out_path": out_path
    }
    
    year_list = list(range(start_yr, end_yr+1))
    
    # --- Load static attributes ---
    df_huc = pd.read_csv(os.path.join(table_path, 'or_field_summaries_huc_attributes.csv'), index_col=unique_id)
    df_cue = pd.read_csv(os.path.join(supp_path, 'cuenca_regions.csv'), index_col=unique_id).fillna(0)
    df_owrd = pd.read_csv(os.path.join(supp_path, 'owrd_admin_bound.csv'), index_col=unique_id)
    df_c_pre = pd.read_csv(os.path.join(supp_path, 'crop_type_codes_and_gridmet_cells.csv'), index_col=unique_id)
    
    # Irrigation types from shapefile
    gdf_typ = gpd.read_file(os.path.join(shp_path, shapefile_name), columns=[unique_id, "ITYPE", "srctype", "IRR_EFF"]).set_index(unique_id)
    gdf_typ.drop(columns='geometry', inplace=True)
    gdf_typ['srctype'] = gdf_typ['srctype'].fillna(0)
    gdf_typ['IRR_EFF'] = gdf_typ['IRR_EFF'].fillna(0)
    
    # List of bad geometries to remove
    df_bad = pd.read_csv(os.path.join(supp_path, "bad_geometry_list.csv"), index_col=unique_id)
    bad_list = list(df_bad.index)
    
    if single_field_flag:
        try:
            df_lookup = pd.read_csv(os.path.join(table_path, f'or_field_summaries_water_year_shift_1mo_{year_list[0]}_et.csv'), index_col=unique_id, nrows=1)
            oid = df_lookup.index[0]
        except Exception as e:
            print(e)
        
        print(f'processing a single field: {oid}')
        df_huc = df_huc.loc[df_huc.index == oid]
        df_c_pre = df_c_pre.loc[df_c_pre.index == oid]
        gdf_typ = gdf_typ.loc[gdf_typ.index == oid]
        df_cue = df_cue.loc[df_cue.index == oid]
        df_owrd = df_owrd.loc[df_owrd.index == oid]
    else:
        print('processing all fields')
    
    # --- Call the concatenation function ---
    concat_field_summaries(
        year_list=year_list,
        paths=paths,
        unique_id=unique_id,
        bad_list=bad_list,
        df_huc=df_huc,
        df_cue=df_cue,
        df_owrd=df_owrd,
        gdf_typ=gdf_typ,
        df_c_pre=df_c_pre
    )
    

def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='Field Summary Concatentation (Step 1)',
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