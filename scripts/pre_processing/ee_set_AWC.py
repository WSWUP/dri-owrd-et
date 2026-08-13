#--------------------------------
# Name:    ee_set_AWC.py
# Desc:    Summarize Available Water Capacity (OpenET ssurgo composite) for
#           field boundaries.
# Python:  3.11
#--------------------------------

import argparse
import logging
import ee
import datetime
import pprint
import sys
from pathlib import Path
import json
import os

dri_owrd_et_path = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(os.path.realpath(__file__)))))
sys.path.insert(0, os.path.join(dri_owrd_et_path, 'dri_owrd_et'))
sys.path.insert(0, dri_owrd_et_path)
import dri_owrd_et.inputs as inputs
import dri_owrd_et.utils as utils

"""
This tool spatiall joins HUC8/HUC12 geometries with field boundaries (centroid).

It exports static HUC8/HUC12 attributes in a CSV table.

"""

pp = pprint.PrettyPrinter(indent=4)


def main(ini_path=None):
    """ Earth Engine monthly zonal stats

    Parameters
    ----------
    ini_path : str

    """

    logging.info('\nEarth Engine spatially join HUC watersheds with field boundaries')

    # Read config file
    ini = inputs.read(ini_path)
    inputs.parse_section(ini, section='INPUTS')
    inputs.parse_section(ini, section='ZONAL_STATS')

    # Initialize Earth Engine API key
    logging.info('\nInitializing Earth Engine')
    
    # high volume endpoint
    ee.Initialize(project=ini['INPUTS']['gcloud_project_id'])

    # field boundary feature collection in earth engine
    fb_asset_id = ini['INPUTS']['field_boundary_asset_id']
    try:
        test_exist = ee.data.getAsset(fb_asset_id)
    except:
        logging.error(
            '\nERROR: field boundary earth engine asset not found, exiting\n'
            '  {}'.format(fb_asset_id))
        sys.exit()

    # unique ID column/attribute for the field boundary dataset
    unique_id = ini['INPUTS']['unique_field_id']

    # flag to export data for an individual field (True) or the entire field boundary dataset (False)
    single_field_flag = ini['INPUTS']['test_flag']
    
    # table export location in the cloud (cloud_storage or google_drive)
    out_location = ini['ZONAL_STATS']['export_location']

    # google drive folder name (default oregon_exports)
    gdrive_folder_name = ini['ZONAL_STATS']['gdrive_folder']

    # google cloud storage bucket name
    bucket = ini['ZONAL_STATS']['gcloud_bucket']

    # google cloud storage path within the bucket
    bucket_path = ini['ZONAL_STATS']['gcloud_bucket_path']
    
    # field boundary assetID on GEE
    if single_field_flag:
        field_bound = (
            ee.FeatureCollection(fb_asset_id)
                .select([unique_id])
                .limit(1)
        )
    else:
        field_bound = (
            ee.FeatureCollection(fb_asset_id)
                .select([unique_id])
        )
    
    # SSURGO AWC Composite that we filled 0 pixels with a 500m circle kernel focal mean calc (OpenET legacy asset)
    ssurgo_awc = ee.Image('projects/openet/soil/ssurgo_AWC_WTA_0to152cm_composite_base_fill').select(['b1'], ['AWC'])

    projection = ssurgo_awc.projection()
    ee_json = ee.Dictionary(ee.Algorithms.Describe(projection))
    ee_wkt = ee.String(ee_json.get('wkt'))
    ee_transform = ee.List(ee_json.get('transform'))
    
    # reduceRegions zonal stats 
    stats_out = (
        ssurgo_awc
            .reduceRegions(
                collection=field_bound,
                reducer=ee.Reducer.mean(),
                crs=ee_wkt,
                # scale=90,
                crsTransform=ee_transform,
            )
            .map(lambda x: x.set({'AWC': x.get('mean')}))
    )

    def fill_null_stats(ftr):
        """ use centroid and ee.Reducer.first() to fill fields that returned null on the first reduction above"""
    
        val = ftr.get('AWC')
    
        return (
            ee.Algorithms.If(
                ee.Algorithms.IsEqual(val, None),
                ftr.set(ssurgo_awc.reduceRegion(
                    reducer=ee.Reducer.first(),
                    geometry=ftr.geometry().centroid(),
                    crs=ee_wkt,
                    # scale=90,
                    crsTransform=ee_transform,
                    maxPixels=1e13,
                )),
                ftr
            )
        )
    
    stats_out_final = stats_out.map(fill_null_stats)

    # list of properties to export
    selector_list = [unique_id, 'AWC']
    
    # Export tasks
    if out_location == 'google_drive':
    
        # Export a CSV file to Google Drive.
        out_table_task = ee.batch.Export.table.toDrive(**{
            'collection': stats_out_final,
            'description': 'OR_Field_Bound_Summary_Export_AWC_attributes',
            'folder': gdrive_folder_name,
            'fileNamePrefix': 'or_field_summaries_awc_attributes',
            'fileFormat': 'CSV',
            'selectors': selector_list,
        })
    
    elif out_location == 'cloud_storage':
        
        # Export a CSV file to Cloud Storage.
        out_table_task = ee.batch.Export.table.toCloudStorage(**{
            'collection': stats_out_final,
            'description': 'OR_Field_Bound_Summary_Export_AWC_attributes',
            'bucket': bucket,
            'fileNamePrefix': f'{bucket_path}/or_field_summaries_awc_attributes',
            'fileFormat': 'CSV',
            'selectors': selector_list,
         })
    
    else:
        print('wrong export location setting, please check the parameter')
    
    # start the task
    out_table_task.start()
    
    # print the status of the task
    # print(out_table_task.status()["id"])
    
    print('task started for exporting field-level SSURGO AWC attributes')
    

def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='Earth Engine Field-Level SSURGO AWC Zonal Stats Table Export',
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