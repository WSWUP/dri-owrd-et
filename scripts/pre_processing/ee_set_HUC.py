#--------------------------------
# Name:    ee_set_HUC.py
# Desc:    Export HUC8 and HUC12 attributes for
#           field boundaries using centroid (spatial join)
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

    def addProp(ftr):
        """sets the field geometry centroid as a property on each field/feature
    
        Args:
            img: earth engine image
    
        Returns:
            img: earth engine image with updated properties
        
        """
        return ftr.set({
            'centroid': ftr.geometry().centroid(),
        })
    
    # field boundary assetID on GEE
    if single_field_flag:
        field_bound_pre = (
            ee.FeatureCollection(fb_asset_id)
                .select([unique_id])
                .limit(1)
        )
    else:
        field_bound_pre = (
            ee.FeatureCollection(fb_asset_id)
                .select([unique_id])
        )
        
    # map the centroid function over the field boundary feature collection
    field_bound = field_bound_pre.map(addProp)
    
    # HUC feature collections
    huc8 = (
        ee.FeatureCollection("USGS/WBD/2017/HUC08")
            .select(['name', 'huc8'], ['huc8_name', 'huc8_code'])
    )
    
    huc12 = (
        ee.FeatureCollection("USGS/WBD/2017/HUC12")
            .select(['name', 'huc12'], ['huc12_name', 'huc12_code'])
    )
    
    # Define a spatial filter as geometries that intersect, using the field centroid
    spatialFilter = ee.Filter.intersects(
        leftField='centroid',
        rightField='.geo',
        maxError=10
    )
    
    # Define a save all joins for hucs
    saveHucJoin8 = ee.Join.saveAll(
      matchesKey='HUC8r'
    )
    
    saveHucJoin12 = ee.Join.saveAll(
      matchesKey='HUC12r'
    )
    
    ### Process one join at a time
    # Apply the join.
    field_bound_huc1 = saveHucJoin8.apply(field_bound, huc8, spatialFilter)
    
    # adding id property of HUC feature to root feature
    def hucProp8(ftr):
        hucid = ee.Feature(ee.List(ftr.get("HUC8r")).get(0)).get('huc8_code')
        hucna = ee.Feature(ee.List(ftr.get('HUC8r')).get(0)).get('huc8_name')
        return ftr.set({
            'HUC8': hucid,
            'HUC8_name': hucna,
            'HUC8r': None
        })
    
    field_bound_out_huc1 = field_bound_huc1.map(hucProp8)
    
    
    # Apply the join.
    field_bound_huc2 = saveHucJoin12.apply(field_bound_out_huc1, huc12, spatialFilter)
    
    # adding id property of HUC feature to root feature
    def hucProp12(ftr):
        hucid = ee.Feature(ee.List(ftr.get("HUC12r")).get(0)).get('huc12_code')
        hucna = ee.Feature(ee.List(ftr.get('HUC12r')).get(0)).get('huc12_name')
        return ftr.set({
            'HUC12': hucid,
            'HUC12_name': hucna,
            'HUC12r': None
        })
    
    field_bound_out = field_bound_huc2.map(hucProp12)
    
    
    # list of properties to export
    selector_list = ['OPENET_ID', 'HUC8_name', 'HUC8', 'HUC12_name','HUC12']
    
    # Export tasks
    if out_location == 'google_drive':
    
        # Export a CSV file to Google Drive.
        out_table_task = ee.batch.Export.table.toDrive(**{
            'collection': field_bound_out,
            'description': 'OR_Field_Bound_Summary_Export_HUC_attributes',
            'folder': gdrive_folder_name,
            'fileNamePrefix': 'or_field_summaries_huc_attributes',
            'fileFormat': 'CSV',
            'selectors': selector_list,
        })
    
    elif out_location == 'cloud_storage':
        
        # Export a CSV file to Cloud Storage.
        out_table_task = ee.batch.Export.table.toCloudStorage(**{
            'collection': field_bound_out,
            'description': 'OR_Field_Bound_Summary_Export_HUC_attributes',
            'bucket': bucket,
            'fileNamePrefix': f'{bucket_path}/or_field_summaries_huc_attributes',
            'fileFormat': 'CSV',
            'selectors': selector_list,
         })
    
    else:
        print('wrong export location setting, please check the parameter')
    
    # start the task
    out_table_task.start()
    
    # print the status of the task
    # print(out_table_task.status()["id"])
    
    print('task started for exporting field-level HUC8/HUC12 attributes')
    

def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='Earth Engine HUC - Field Spatial Join Table Export',
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