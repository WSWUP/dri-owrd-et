#--------------------------------
# Name:    ee_monthly_huc_evap_zonal_stats.py
# Desc:    Export monthly evaporation summaries
#           for HUC8/HUC12 watershed boundaries
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
This tool computes zonal statsistics for the WBD HUC8/HUC12 watershed 
boundary dataset and exports the tables.

It exports monthly small pond evaporation summaries as CSV tables
for the historical study period 1985-2024 (Nov-Oct)

"""

pp = pprint.PrettyPrinter(indent=4)


def main(ini_path=None):
    """ Earth Engine monthly zonal stats

    Parameters
    ----------
    ini_path : str

    """

    logging.info('\nEarth Engine monthly zonal stats for field boundaries')

    # Read config file
    ini = inputs.read(ini_path)
    inputs.parse_section(ini, section='INPUTS')
    inputs.parse_section(ini, section='ZONAL_STATS')

    # Initialize Earth Engine API key
    logging.info('\nInitializing Earth Engine')
    
    # high volume endpoint
    ee.Initialize(project=ini['INPUTS']['gcloud_project_id'])

    # HUC code to use for small pond evaporation summaries
    huc_code = ini['INPUTS']['huc_level']
    huc_c = huc_code.replace('HUC', '')

    # flag to export data for an individual HUC (True) or the entire HUC boundary dataset for Oregon (False)
    single_huc_flag = ini['INPUTS']['test_flag']

    # table export location in the cloud (cloud_storage or google_drive)
    out_location = ini['ZONAL_STATS']['export_location']

    # google drive folder name (default oregon_exports)
    gdrive_folder_name = ini['ZONAL_STATS']['gdrive_folder']

    # google cloud storage bucket name
    bucket = ini['ZONAL_STATS']['gcloud_bucket']

    # google cloud storage path within the bucket
    bucket_path = ini['ZONAL_STATS']['gcloud_bucket_path']

    # ag ET gridMET cells to use as a mask
    et_cells = ee.FeatureCollection('users/bminor/Oregon/or_et_cells')
    
    # mask image for gridMET data
    et_cells_mask = ee.Image.constant(1).clip(et_cells).mask()
    
    # HUC boundaries filtered to gridMET ag ET cells
    if single_huc_flag:
        hucs = (
            ee.FeatureCollection(f"USGS/WBD/2017/HUC{huc_c.zfill(2)}")
                .filterBounds(et_cells)
                .limit(1)
        )
    else:
        hucs = (
            ee.FeatureCollection(f"USGS/WBD/2017/HUC{huc_c.zfill(2)}")
                .filterBounds(et_cells)
        )

    def removGeom(ftr):
        """removes the geometry column from the field/feature
    
        Args:
            ftr: earth engine feature
    
        Returns:
            earth engine feature without geometry attributes
        """
        
        return ftr.setGeometry(None)
    
    # monthly bias corr ETo
    eto_b_coll_monthly = (
        ee.ImageCollection('projects/openet/assets/reference_et/conus/gridmet/monthly/v1')
            .select(['eto'], ['EToB'])
            .filter(ee.Filter.date('1984-11-01', '2025-11-01'))
    )
    
    # image projection info
    projection = eto_b_coll_monthly.first().projection()
    json = ee.Dictionary(ee.Algorithms.Describe(projection))
    ee_crs = ee.List(json.get('crs'))
    ee_transform = ee.List(json.get('transform'))
    
    # daily non bias corr ETo
    eto_n_coll_daily = (
        ee.ImageCollection("IDAHO_EPSCOR/GRIDMET")
            .select(['eto'], ['EToN'])
            .filter(ee.Filter.date('1984-11-01', '2025-11-01'))
    )
    
    # start and end dates of the project
    Date_Start = ee.Date('1984-11-01')
    Date_End = ee.Date('2025-10-01') # inclusive
    
    # Create list of dates for time series
    n_months = Date_End.difference(Date_Start,'month').round()
    dates = ee.List.sequence(0, n_months, 1)
    def makeDates(n):
        return Date_Start.advance(n, 'month')
    dates = dates.map(makeDates)
    
    def monthColl(dat):
        """converts gridMET daily ETo image to monthly ETo image and calculates evaporation (1.05 * ETo)
    
        Args:
            dat: earth engine date
    
        Returns:
            earth engine evaporation and ETo image with updated properties
        
        """
    
        # get earth engine date object and format as strings
        dat_obj = ee.Date(dat)
        dat_mo = dat_obj.get('month')
        dat_yr = dat_obj.get('year')
        dat_str = dat_obj.format('yyyy-MM-dd')
        dat_str2 = dat_obj.format('yyyyMM')
    
        # filter the daily ETo image collection to the month
        eto_n_imgs = (
            eto_n_coll_daily
                .filter(ee.Filter.calendarRange(dat_yr, dat_yr, 'year'))
                .filter(ee.Filter.calendarRange(dat_mo, dat_mo, 'month'))
        )
    
        # calculate the monthly non bias ETo total in inches
        eto_n_img = eto_n_imgs.sum().divide(25.4)
    
        # monthly bias corr ETo
        eto_b_img = (
            eto_b_coll_monthly
                .filter(ee.Filter.calendarRange(dat_yr, dat_yr, 'year'))
                .filter(ee.Filter.calendarRange(dat_mo, dat_mo, 'month'))
                .first()
                .divide(25.4)
        )
        
        # joined img and add evaporation estimate bands
        img = (
            eto_b_img
                .addBands(eto_n_img)
                .addBands(eto_b_img.multiply(1.05))
                .addBands(eto_n_img.multiply(1.05))
                .rename(['EToB', 'EToN', 'EvpB', 'EvpN'])
        )
    
        return img.set({
            'date': dat_str,
            'system:index': dat_str2,
            'system:time_start': ee.Date(dat_str).millis()
        })
    
    # calculate monthly ETo and evaporation
    joined = ee.ImageCollection(dates.map(monthColl))
    
    # convert the image collection to an image with numerous bands
    joined_bnds = joined.toBands()
    
    # getInfo call to get the list of band names as a python list
    joined_bnds_list = joined_bnds.bandNames().getInfo()
    
    # zonal stats computation
    huc_stats_out = (
        joined_bnds
            .updateMask(et_cells_mask)
            .reduceRegions(
                collection=hucs.select([f'huc{huc_c}'], [f'{huc_code}_code']),
                reducer=ee.Reducer.mean(),
                # scale=4638.312116386398,
                crs=ee_crs,
                crsTransform=ee_transform,
                tileScale=1 # changing the tileScale from the default 1 can help w/ memory limit errors on larger data extractions
            )
            .map(removGeom)
    )
        
    
    # Export tasks
    if out_location == 'google_drive':
    
        out_table_huc_monthly = ee.batch.Export.table.toDrive(**{
            'collection': ee.FeatureCollection(huc_stats_out),
            'description':f'OR_{huc_code}_Summary_Export_monthly_small_pond_evap',
            'fileNamePrefix': f'or_gridmet_huc{huc_c}_summaries_monthly_eto_small_pond_evap_inches',
            'folder': gdrive_folder_name,
            'fileFormat': 'CSV',
            'selectors': [f'{huc_code}_code', f'{huc_code}_name'] + joined_bnds_list,
        })
    
    
    elif out_location == 'cloud_storage':
        
        # Export a CSV file to Cloud Storage.
        out_table_huc_monthly = ee.batch.Export.table.toCloudStorage(**{
            'collection': ee.FeatureCollection(huc_stats_out),
            'description':f'OR_{huc_code}_Summary_Export_monthly_small_pond_evap',
            'bucket': bucket,
            'fileNamePrefix': f'{bucket_path}/or_gridmet_huc{huc_c}_summaries_monthly_eto_small_pond_evap_inches',
            'fileFormat': 'CSV',
            'selectors': [f'{huc_code}_code', f'{huc_code}_name'] + joined_bnds_list,
        })
    
    else:
        print('wrong export location setting, please check the parameter')
    
    out_table_huc_monthly.start()
    print('task started for exporting huc-level monthly small pond evap summaries')    

    
def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='Earth Engine HUC-Level Monthly Evaporation Zonal Stats Table Export',
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