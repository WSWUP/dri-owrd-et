#--------------------------------
# Name:    ee_monthly_field_zonal_stats.py
# Desc:    Export monthly ET, ETo, EToF, or PPT summaries
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

It exports monthly summaries of ET, ETo, EToF, or PPT as CSV tables,
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
    start_yr = ini['INPUTS']['start_year']
    end_yr = ini['INPUTS']['end_year']

    # monthly data variable to extract
    variable = ini['ZONAL_STATS']['monthly_variable']
    
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

    # start/end dates for the statewide et project through 2024
    study_start = '1984-11-01'
    study_end = '2025-11-01' # exclusive
    
    # dictionary containg variables (keys) and output variable names/dataset source assetIDs (values) that are used
    dataset_dict_v2_0 = {
        'et': ['ETa', 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_0_pre2000', 'OpenET/ENSEMBLE/CONUS/GRIDMET/MONTHLY/v2_0'],
        'et_reference': ['ET_Reference', 'projects/openet/assets/reference_et/conus/gridmet/monthly/v1'],
        'et_fraction': ['ET_Fraction', 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_0_pre2000', 'OpenET/ENSEMBLE/CONUS/GRIDMET/MONTHLY/v2_0', 'projects/openet/assets/reference_et/conus/gridmet/monthly/v1'],
        'ppt': ['PPT', 'IDAHO_EPSCOR/GRIDMET'],
        # 'count': ['MODEL_COUNT', 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_0_pre2000', 'OpenET/ENSEMBLE/CONUS/GRIDMET/MONTHLY/v2_0']
    }
    
    # 2025 updates uses 2.1 version
    dataset_dict_v2_1 = {
        'et': ['ETa', 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_0_pre2000', 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_1'], # 2025 updates uses 2.1 version
        'et_reference': ['ET_Reference', 'projects/openet/assets/reference_et/conus/gridmet/monthly/v1'],
        'et_fraction': ['ET_Fraction', 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_0_pre2000', 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_1', 'projects/openet/assets/reference_et/conus/gridmet/monthly/v1'], # 2025 updates uses the 2.1 version
        'ppt': ['PPT', 'IDAHO_EPSCOR/GRIDMET'],
        # 'count': ['MODEL_COUNT', 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_0_pre2000', 'OpenET/ENSEMBLE/CONUS/GRIDMET/MONTHLY/v2_0']
    }
    
    # list of years to process based on start/end year parameters
    potential_year_list = list(range(1985, 2026))
    if start_yr > end_yr:
        print('end year cannot be less than start_year, please check the parameters')
    if start_yr not in potential_year_list:
        print('start year is not within the 1985-2025 study period')
    if end_yr not in potential_year_list:
        print('end year is not within the 1985-2025 study period')
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
    
    # prep image collections
    if variable == 'et':
    
        # Nov 1984 - Sept 1999 ET collection v2.0
        monthly_coll_1_v2_0 = (
            ee.ImageCollection(dataset_dict_v2_0[variable][1])
                .select(['et_ensemble_mad'], [variable])
                .filter(ee.Filter.date(study_start, '1999-10-01'))
        )
    
        # Oct 1999 - Dec 2024 ET collection v2.0
        monthly_coll_2_v2_0 = (
            ee.ImageCollection(dataset_dict_v2_0[variable][2])
                .select(['et_ensemble_mad'], [variable])
                .filter(ee.Filter.date('1999-10-01', '2025-01-01'))
        )
        # 2025 updates have to be handled slightly different with v2.0 to v2.1 switch
        monthly_coll_1_v2_1 = (
            ee.ImageCollection(dataset_dict_v2_1[variable][2])
                .select(['et_ensemble_mad'], [variable])
                .filter(ee.Filter.date('2025-01-01', study_end))
        )
    
        # merge image collections
        final_coll = monthly_coll_1_v2_0.merge(monthly_coll_2_v2_0).merge(monthly_coll_1_v2_1)
    
    elif variable == 'et_reference':
    
        # gridMET ETo collections
        final_coll = (
            ee.ImageCollection(dataset_dict[variable][1])
                .select(['eto'], [variable])
                .filter(ee.Filter.date(study_start, study_end))
        )
    
    elif variable == 'et_fraction':
    
        # Nov 1984 - Sept 1999 ET collection v2.0
        monthly_coll_1_v2_0 = (
            ee.ImageCollection(dataset_dict_v2_0[variable][1])
                .select(['et_ensemble_mad'], [variable])
                .filter(ee.Filter.date(study_start, '1999-10-01'))
        )
    
        # Oct 1999 - Dec 2024 ET collection v2.0
        monthly_coll_2_v2_0 = (
            ee.ImageCollection(dataset_dict_v2_0[variable][2])
                .select(['et_ensemble_mad'], [variable])
                .filter(ee.Filter.date('1999-10-01', '2025-01-01'))
        )
        # 2025 updates have to be handled slightly different with v2.0 to v2.1 switch
        monthly_coll_1_v2_1 = (
            ee.ImageCollection(dataset_dict_v2_1[variable][2])
                .select(['et_ensemble_mad'], [variable])
                .filter(ee.Filter.date('2025-01-01', study_end))
        )
    
        # merge image collections
        monthly_coll = monthly_coll_1_v2_0.merge(monthly_coll_2_v2_0).merge(monthly_coll_1_v2_1)
    
        # gridMET ETo collection
        gridmet_coll = (
            ee.ImageCollection(dataset_dict[variable][3])
                .select(['eto'], ['et_reference'])
                .filter(ee.Filter.date(study_start, study_end))
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
    
    elif variable == 'ppt':
        
        # start and end dates of the OpenET data
        Date_Start = ee.Date(study_start)
        Date_End = ee.Date(study_end)
        
        # Create list of dates for time series
        n_months = Date_End.difference(Date_Start, 'month').round()
        dates = ee.List.sequence(0, n_months, 1)
        def makeDates(n):
            return Date_Start.advance(n, 'month')
        dates = dates.map(makeDates)
        
        # earth engine end date (exclusive)
        en_dt_exc = Date_End.advance(1, 'month').format('yyyy-MM-dd')
    
        # daily gridMET precip collection
        daily_coll = (
            ee.ImageCollection(dataset_dict[variable][1])
                .select(['pr'], [variable])
                .filter(ee.Filter.date(study_start, study_end))
        )
        
        def monthColl(dat):
            """converts daily precip images to monthly precip images by looping through each summation period
    
            Args:
                dat: earth engine date
    
            Returns:
                earth engine monthly gridMET precip image with updated properties
            
            """
        
            # get earth engine date object and format as strings
            dat_obj = ee.Date(dat)
            dat_mo = dat_obj.get('month')
            dat_yr = dat_obj.get('year')
            dat_str = dat_obj.format('yyyy-MM-dd')
        
            # filter the precip image collection to the date
            imgs = (
                daily_coll
                    .filter(ee.Filter.calendarRange(dat_yr, dat_yr, 'year'))
                    .filter(ee.Filter.calendarRange(dat_mo, dat_mo, 'month'))
            )
        
            # calculate the monthly total
            img = imgs.sum()
            return img.set({
                'date': dat_str,
                'system:time_start': ee.Date(dat_str).millis()
            })
            
        # map the function over the dates to create the monthly image collection
        final_coll = ee.ImageCollection(dates.map(monthColl))
    
    
    print(f'PROCESSING {year_list[0]} to {year_list[-1]}')
    # loop through each year that is being run
    for year in year_list:
    
        # filter collection to Nov-Oct months for the current year
        final_coll_sub = (
            final_coll
                .filter(ee.Filter.date(f'{year-1}-11-01', f'{year}-11-01'))
        )
    
        # monthly images
        if variable == 'et_fraction':
            var_nov = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(11, 11, 'month')).mean().rename([f'{variable}_11']))
            var_dec = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(12, 12, 'month')).mean().rename([f'{variable}_12']))
            var_jan = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(1, 1, 'month')).mean().rename([f'{variable}_01']))
            var_feb = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(2, 2, 'month')).mean().rename([f'{variable}_02']))
            var_mar = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(3, 3, 'month')).mean().rename([f'{variable}_03']))
            var_apr = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(4, 4, 'month')).mean().rename([f'{variable}_04']))
            var_may = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(5, 5, 'month')).mean().rename([f'{variable}_05']))
            var_jun = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(6, 6, 'month')).mean().rename([f'{variable}_06']))
            var_jul = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(7, 7, 'month')).mean().rename([f'{variable}_07']))
            var_aug = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(8, 8, 'month')).mean().rename([f'{variable}_08']))
            var_sep = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(9, 9, 'month')).mean().rename([f'{variable}_09']))
            var_oct = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(10, 10, 'month')).mean().rename([f'{variable}_10']))
        else:
            var_nov = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(11, 11, 'month')).sum().rename([f'{variable}_11']))
            var_dec = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(12, 12, 'month')).sum().rename([f'{variable}_12']))
            var_jan = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(1, 1, 'month')).sum().rename([f'{variable}_01']))
            var_feb = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(2, 2, 'month')).sum().rename([f'{variable}_02']))
            var_mar = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(3, 3, 'month')).sum().rename([f'{variable}_03']))
            var_apr = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(4, 4, 'month')).sum().rename([f'{variable}_04']))
            var_may = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(5, 5, 'month')).sum().rename([f'{variable}_05']))
            var_jun = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(6, 6, 'month')).sum().rename([f'{variable}_06']))
            var_jul = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(7, 7, 'month')).sum().rename([f'{variable}_07']))
            var_aug = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(8, 8, 'month')).sum().rename([f'{variable}_08']))
            var_sep = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(9, 9, 'month')).sum().rename([f'{variable}_09']))
            var_oct = ee.Image(final_coll_sub.filter(ee.Filter.calendarRange(10, 10, 'month')).sum().rename([f'{variable}_10']))
    
        # stack all bands
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
    
        def orgFeatColl(ftr):
            """adds formatted columns/properties to a feature using existing properties/values
    
            Args:
                ftr: earth engine feature
    
            Returns:
                earth engine feature with updated properties
            
            """
            
            return ftr.set({
                'ACRES_FTR_GEOM': ftr.get('ACRES_FTR_GEOM_EE'),
                f'{dataset_dict[variable][0]}_11_{str(year-1)[2:]}': ftr.get(f'{variable}_11'),
                f'{dataset_dict[variable][0]}_12_{str(year-1)[2:]}': ftr.get(f'{variable}_12'),
                f'{dataset_dict[variable][0]}_01_{str(year)[2:]}': ftr.get(f'{variable}_01'),
                f'{dataset_dict[variable][0]}_02_{str(year)[2:]}': ftr.get(f'{variable}_02'),
                f'{dataset_dict[variable][0]}_03_{str(year)[2:]}': ftr.get(f'{variable}_03'),
                f'{dataset_dict[variable][0]}_04_{str(year)[2:]}': ftr.get(f'{variable}_04'),
                f'{dataset_dict[variable][0]}_05_{str(year)[2:]}': ftr.get(f'{variable}_05'),
                f'{dataset_dict[variable][0]}_06_{str(year)[2:]}': ftr.get(f'{variable}_06'),
                f'{dataset_dict[variable][0]}_07_{str(year)[2:]}': ftr.get(f'{variable}_07'),
                f'{dataset_dict[variable][0]}_08_{str(year)[2:]}': ftr.get(f'{variable}_08'),
                f'{dataset_dict[variable][0]}_09_{str(year)[2:]}': ftr.get(f'{variable}_09'),
                f'{dataset_dict[variable][0]}_10_{str(year)[2:]}': ftr.get(f'{variable}_10'),
            })
    
        # map the function to format 
        stats_out_form  = ee.FeatureCollection(stats_out.map(orgFeatColl))
    
        # list of properties to export
        if variable == 'et':
            selector_list = [unique_id, 'ACRES_FTR_GEOM',
                              f'{dataset_dict[variable][0]}_11_{str(year-1)[2:]}', f'{dataset_dict[variable][0]}_12_{str(year-1)[2:]}', f'{dataset_dict[variable][0]}_01_{str(year)[2:]}',
                              f'{dataset_dict[variable][0]}_02_{str(year)[2:]}', f'{dataset_dict[variable][0]}_03_{str(year)[2:]}', f'{dataset_dict[variable][0]}_04_{str(year)[2:]}',
                              f'{dataset_dict[variable][0]}_05_{str(year)[2:]}', f'{dataset_dict[variable][0]}_06_{str(year)[2:]}', f'{dataset_dict[variable][0]}_07_{str(year)[2:]}',
                              f'{dataset_dict[variable][0]}_08_{str(year)[2:]}', f'{dataset_dict[variable][0]}_09_{str(year)[2:]}', f'{dataset_dict[variable][0]}_10_{str(year)[2:]}',
                            ]
        else:
            selector_list = [unique_id,
                              f'{dataset_dict[variable][0]}_11_{str(year-1)[2:]}', f'{dataset_dict[variable][0]}_12_{str(year-1)[2:]}', f'{dataset_dict[variable][0]}_01_{str(year)[2:]}',
                              f'{dataset_dict[variable][0]}_02_{str(year)[2:]}', f'{dataset_dict[variable][0]}_03_{str(year)[2:]}', f'{dataset_dict[variable][0]}_04_{str(year)[2:]}',
                              f'{dataset_dict[variable][0]}_05_{str(year)[2:]}', f'{dataset_dict[variable][0]}_06_{str(year)[2:]}', f'{dataset_dict[variable][0]}_07_{str(year)[2:]}',
                              f'{dataset_dict[variable][0]}_08_{str(year)[2:]}', f'{dataset_dict[variable][0]}_09_{str(year)[2:]}', f'{dataset_dict[variable][0]}_10_{str(year)[2:]}',
                            ]
        
        # Export tasks
        if out_location == 'google_drive':
    
            # Export a CSV file to Google Drive.
            out_table_task = ee.batch.Export.table.toDrive(**{
                'collection': stats_out_form,
                'description': f'OR_Field_Bound_Summary_Export_{variable}_{year}',
                'fileNamePrefix': f'or_field_summaries_water_year_shift_1mo_{year}_{variable}',
                'folder': gdrive_folder_name,
                'fileFormat': 'CSV',
                'selectors': selector_list,
            })
    
        elif out_location == 'cloud_storage':
            
            # Export a CSV file to Cloud Storage.
            out_table_task = ee.batch.Export.table.toCloudStorage(**{
                'collection': stats_out_form,
                'description': f'OR_Field_Bound_Summary_Export_{variable}_{year}',
                'bucket': bucket,
                'fileNamePrefix': f'{bucket_path}/or_field_summaries_water_year_shift_1mo_{year}_{variable}',
                'fileFormat': 'CSV',
                'selectors': selector_list,
             })
    
        else:
            print('wrong export location setting, please check the parameter')
            continue
    
        # start the task
        out_table_task.start()
    
        # print the status of the task
        # print(out_table_task.status()["id"])
        
        print(f'task started for {variable} {year}')
    

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