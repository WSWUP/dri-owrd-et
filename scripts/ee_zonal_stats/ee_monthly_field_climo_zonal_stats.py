#--------------------------------
# Name:    ee_monthly_field_climo_zonal_stats.py
# Desc:    Export monthly EToF climatology summaries
#           for field boundaries
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
This tool computes zonal statsistics for a field boundary dataset
and exports the tables.

It exports monthly summaries of EToF climatologies for fixed year 
windows/blocks (e.g., 1984-1991; 1992-1997) as CSV tables,
keeping individual data variables in separate files for a given
year (12 months of data per file, nov-oct shifted water year months).

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
    
    # start and end years
    start_yr = ini['INPUTS']['start_year_climo']
    if start_yr == 1984:
        end_yr = 1991
    elif start_yr == 1992:
        end_yr = 1997
    elif start_yr == 1998:
        end_yr = 2003
    elif start_yr == 2004:
        end_yr = 2009
    elif start_yr == 2010:
        end_yr = 2015
    elif start_yr == 2016:
        end_yr = 2021
    else:
        end_yr = ini['INPUTS']['end_year_climo']
        logging.error(
                        '\nERROR: Invalid start year specified for the climatology window options (1984-1991; 1992-1997; 1998-2003; 2004-2009; 2010-2015; 2016-2021): {}\n'
                        '  Must be: 1984, 1992, 1998, 2004, 2010, or 2016')
        sys.exit()

    # monthly data variable to extract
    variable = 'et_fraction_climo'
    
    # flag to export data for an individual field (True) or the entire field boundary dataset (False)
    single_field_flag = ini['ZONAL_STATS']['test_flag']

    # table export location in the cloud (cloud_storage or google_drive)
    out_location = ini['ZONAL_STATS']['export_location']

    # google drive folder name (default oregon_exports)
    gdrive_folder_name = ini['ZONAL_STATS']['gdrive_folder']

    # google cloud storage bucket name
    bucket = ini['ZONAL_STATS']['gcloud_bucket']

    # google cloud storage path within the bucket
    bucket_path = ini['ZONAL_STATS']['gcloud_bucket_path']


    # dictionary containg variables (keys) and output variable names/dataset source assetIDs (values) that are used
    dataset_dict = {
        'et_fraction_climo': ['ET_Fraction', 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_0_pre2000', 'OpenET/ENSEMBLE/CONUS/GRIDMET/MONTHLY/v2_0', 'projects/openet/assets/reference_et/conus/gridmet/monthly/v1'],
    }
    
    
    # list of years to process based on start/end year parameters
    potential_year_list = list(range(1984, 2022))
    if start_yr > end_yr:
        print('end_year cannot be less than start_year, please check the parameters')
    if start_yr not in potential_year_list:
        print('start_year is not within the 1984-2021 climatology years')
    if end_yr not in potential_year_list:
        print('end_year is not within the 1984-2021 climatology years')
    year_list = list(range(start_yr, end_yr+1))

    # general functions
    def calcArea(ftr):
        """calculates the field geometry area in units of acres (sq. m to acres) and sets the value as a property on the field/feature
    
        Args:
            ftr: earth engine feature
    
        Returns:
            ftr: earth engine feature with updated properties
        """
        
        return ftr.set({
            'ACRES_FTR_GEOM_EE': ftr.geometry().area().divide(4047),
        })

    def addDates(img):
        """sets the image date (start of the month) as a property on each field/feature
    
        Args:
            img: earth engine image
    
        Returns:
            img: earth engine image with updated properties
        """
        
        img_date = ee.Date(img.get('system:time_start'))
        return img.set('date', img_date.format('yyyy-MM-dd'))

    # simple join function for images
    def joinFunc(img):
        """joins a primary and secondary image together using concatenation (combining images/bands)
    
        Args:
            img: earth engine image
    
        Returns:
            combined earth engine image
        """
        
        return ee.Image.cat(img.get('primary'), img.get('secondary'))

    def calcETF(img):
        """calculates the fraction of reference ET (EToF) by dividing the OpenET ensemble ETa by the gridMET ETo
    
        Args:
            img: earth engine image
    
        Returns:
            earth engine image with additional band
        """
        
        img = img.addBands(img.select('et').divide(img.select('et_reference'))).rename(['et', 'et_reference', 'et_fraction'])
        return img.select(['et_fraction'])

    def removGeom(ftr):
        """removes the geometry column from the field/feature
    
        Args:
            ftr: earth engine feature
    
        Returns:
            earth engine feature without geometry attributes
        """
        
        return ftr.setGeometry(None)
    
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
        
    # map the area function over the field boundary feature collection
    field_bound = field_bound_pre.map(calcArea)
    

    # Nov 1984 - Sept 1999 ET collection
    monthly_coll_1 = (
        ee.ImageCollection(dataset_dict[variable][1])
            .select(['et_ensemble_mad'], ['et'])
            .filter(ee.Filter.date('1984-03-01', '1999-10-01'))
            .map(addDates)
    )

    # Oct 1999 - Sept 2022 ET collection
    monthly_coll_2 = (
        ee.ImageCollection(dataset_dict[variable][2])
            .select(['et_ensemble_mad'], ['et'])
            .filter(ee.Filter.date('1999-10-01', '2021-11-01'))
            .map(addDates)
    )

    # merge image collections
    monthly_coll = monthly_coll_1.merge(monthly_coll_2)

    # gridMET ETo collection
    gridmet_coll = (
        ee.ImageCollection(dataset_dict[variable][3])
            .select(['eto'], ['et_reference'])
            .filter(ee.Filter.date('1984-03-01', '2021-11-01'))
            .map(addDates)
    )

    # GEE filter using date properties    
    filter_c = ee.Filter.equals(leftField='date', rightField='date')

    # inner join keeps matches only
    innJoin = ee.Join.inner()

    # apply the inner join with the filter
    innerApp = ee.ImageCollection(innJoin.apply(monthly_coll, gridmet_coll, filter_c))

    # Combine the images into a single image which contains all bands from all of the images
    # also calculate EToF
    final_coll = (
        innerApp
            .map(joinFunc)
            .map(calcETF)
    )

    # filter to the climatology window that was defined by the start/end years
    final_coll_window = (
        final_coll
            .filter(ee.Filter.date(f'{start_yr-1}-11-01', f'{end_yr}-11-01'))
    )
    
    var_nov = ee.Image(final_coll_window.filter(ee.Filter.calendarRange(11, 11, 'month')).mean().rename([f'{variable}_11']))
    var_dec = ee.Image(final_coll_window.filter(ee.Filter.calendarRange(12, 12, 'month')).mean().rename([f'{variable}_12']))
    var_jan = ee.Image(final_coll_window.filter(ee.Filter.calendarRange(1, 1, 'month')).mean().rename([f'{variable}_01']))
    var_feb = ee.Image(final_coll_window.filter(ee.Filter.calendarRange(2, 2, 'month')).mean().rename([f'{variable}_02']))
    var_mar = ee.Image(final_coll_window.filter(ee.Filter.calendarRange(3, 3, 'month')).mean().rename([f'{variable}_03']))
    var_apr = ee.Image(final_coll_window.filter(ee.Filter.calendarRange(4, 4, 'month')).mean().rename([f'{variable}_04']))
    var_may = ee.Image(final_coll_window.filter(ee.Filter.calendarRange(5, 5, 'month')).mean().rename([f'{variable}_05']))
    var_jun = ee.Image(final_coll_window.filter(ee.Filter.calendarRange(6, 6, 'month')).mean().rename([f'{variable}_06']))
    var_jul = ee.Image(final_coll_window.filter(ee.Filter.calendarRange(7, 7, 'month')).mean().rename([f'{variable}_07']))
    var_aug = ee.Image(final_coll_window.filter(ee.Filter.calendarRange(8, 8, 'month')).mean().rename([f'{variable}_08']))
    var_sep = ee.Image(final_coll_window.filter(ee.Filter.calendarRange(9, 9, 'month')).mean().rename([f'{variable}_09']))
    var_oct = ee.Image(final_coll_window.filter(ee.Filter.calendarRange(10, 10, 'month')).mean().rename([f'{variable}_10']))
    
    # add all bands
    all_bnds = (
        var_nov.addBands(var_dec).addBands(var_jan).addBands(var_feb).addBands(var_mar)
            .addBands(var_apr).addBands(var_may).addBands(var_jun).addBands(var_jul)
            .addBands(var_aug).addBands(var_sep).addBands(var_oct)
    )
    
    # zonal stats computation (reduceRegions, spatial mean, composite dataframe output)
    stats_out = (
        all_bnds
            .reduceRegions(
                collection=field_bound,
                reducer=ee.Reducer.mean(),
                scale=30,
                tileScale=16
            )
            .map(removGeom)
    )
    
    # format the output
    def orgFeatColl(ftr):
        """adds formatted columns/properties to a feature using existing properties/values
    
        Args:
            ftr: earth engine feature
    
        Returns:
            earth engine feature with updated properties
        
        """
        
        return ftr.set({
            'ACRES_FTR_GEOM': ftr.get('ACRES_FTR_GEOM_EE'),
            f'{dataset_dict[variable][0]}_11': ftr.get(f'{variable}_11'),
            f'{dataset_dict[variable][0]}_12': ftr.get(f'{variable}_12'),
            f'{dataset_dict[variable][0]}_01': ftr.get(f'{variable}_01'),
            f'{dataset_dict[variable][0]}_02': ftr.get(f'{variable}_02'),
            f'{dataset_dict[variable][0]}_03': ftr.get(f'{variable}_03'),
            f'{dataset_dict[variable][0]}_04': ftr.get(f'{variable}_04'),
            f'{dataset_dict[variable][0]}_05': ftr.get(f'{variable}_05'),
            f'{dataset_dict[variable][0]}_06': ftr.get(f'{variable}_06'),
            f'{dataset_dict[variable][0]}_07': ftr.get(f'{variable}_07'),
            f'{dataset_dict[variable][0]}_08': ftr.get(f'{variable}_08'),
            f'{dataset_dict[variable][0]}_09': ftr.get(f'{variable}_09'),
            f'{dataset_dict[variable][0]}_10': ftr.get(f'{variable}_10'),
    
        })
    
    # map the function to format 
    stats_out_form  = ee.FeatureCollection(stats_out.map(orgFeatColl))
    
    # list of properties to export
    selector_list = ['OPENET_ID',
                      f'{dataset_dict[variable][0]}_11', f'{dataset_dict[variable][0]}_12', f'{dataset_dict[variable][0]}_01',
                      f'{dataset_dict[variable][0]}_02', f'{dataset_dict[variable][0]}_03', f'{dataset_dict[variable][0]}_04',
                      f'{dataset_dict[variable][0]}_05', f'{dataset_dict[variable][0]}_06', f'{dataset_dict[variable][0]}_07',
                      f'{dataset_dict[variable][0]}_08', f'{dataset_dict[variable][0]}_09', f'{dataset_dict[variable][0]}_10',
                    ]
    
    # Export tasks
    if out_location == 'google_drive':
    
        # Export a CSV file to Google Drive.
        out_table_task = ee.batch.Export.table.toDrive(**{
            'collection': stats_out_form,
            'description': f'OR_Field_Bound_Summary_Export_{variable}_{start_yr}_{end_yr}',
            'fileNamePrefix': f'or_field_summaries_water_year_shift_1mo_{start_yr}_{end_yr}_{variable}',
            'folder': gdrive_folder_name,
            'fileFormat': 'CSV',
            'selectors': selector_list,
        })
    
    elif out_location == 'cloud_storage':
        
        # Export a CSV file to Cloud Storage.
        out_table_task = ee.batch.Export.table.toCloudStorage(**{
            'collection': stats_out_form,
            'description': f'OR_Field_Bound_Summary_Export_{variable}_{start_yr}_{end_yr}',
            'bucket': bucket,
            'fileNamePrefix': f'{bucket_path}/or_field_summaries_water_year_shift_1mo_{start_yr}_{end_yr}_{variable}',
            'fileFormat': 'CSV',
            'selectors': selector_list,
         })
    
    else:
        print('wrong export location setting, please check the parameter')
    
    # start the task
    out_table_task.start()
    
    # print the status of the task
    # print(out_table_task.status()["id"])
    
    print(f'task started for {variable} {start_yr} - {end_yr}')


def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='Earth Engine Field-Level Monthly EToF Climatology Zonal Stats Table Export',
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
    