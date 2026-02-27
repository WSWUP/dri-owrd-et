#--------------------------------
# Name:    ee_annual_field_zonal_stats.py
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
    single_field_flag = ini['ZONAL_STATS']['test_flag']

    # table export location in the cloud (cloud_storage or google_drive)
    out_location = ini['ZONAL_STATS']['export_location']

    # google drive folder name (default oregon_exports)
    gdrive_folder_name = ini['ZONAL_STATS']['gdrive_folder']

    # google cloud storage bucket name
    bucket = ini['ZONAL_STATS']['gcloud_bucket']

    # google cloud storage path within the bucket
    bucket_path = ini['ZONAL_STATS']['gcloud_bucket_path']

    # start/end dates for the statewide et project
    study_start = '1984-11-01'
    study_end = '2024-11-01' # exclusive
    
    # dictionary containg variables (keys) and pixel class values/output variable names/dataset source assetIDs (values) that are used
    dataset_dict = {
        'crop_type': ['CROP', 'USDA/NASS/CDL'],
        'irrmapper_irrigated': [0, 'IRRIGATED', 'projects/ee-dgketchum/assets/IrrMapper/IrrMapperComp'],
        'irrmapper_wetland': [3, 'WETLAND', 'projects/ee-dgketchum/assets/IrrMapper/IrrMapperComp'],
        'etof_irr_status': ['ETOF_IRR_STATUS_MODE', 'projects/openet/assets/ensemble/conus/gridmet/monthly/v2_0_pre2000', 'OpenET/ENSEMBLE/CONUS/GRIDMET/MONTHLY/v2_0', 'projects/openet/assets/reference_et/conus/gridmet/monthly/v1'],
    }
    
    
    # full list of years within the study period
    potential_year_list = list(range(1985, 2025))
    
    if start_yr > end_yr:
        print('end_year cannot be less than start_year, please check the parameters')
    if start_yr not in potential_year_list:
        print('start_year is not within the 1985-2024 study period')
    if end_yr not in potential_year_list:
        print('end_year is not within the 1985-2024 study period')
    
    # list of years to process based on start/end year parameters
    year_list = list(range(start_yr, end_yr+1))
    
    
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
    
    print(f'PROCESSING {year_list[0]} to {year_list[-1]}')
    for year in year_list:
        
        # prep image collections
        if (variable == 'irrmapper_irrigated' or variable == 'irrmapper_wetland'):
            
            # IrrMapper Irrigated class image for the current year
            irr = (
                ee.ImageCollection(dataset_dict[variable][2])
                    .filter(ee.Filter.calendarRange(year, year, 'year'))
                    .select('classification')
                    .max()
                    .rename([dataset_dict[variable][1]])
            )
    
            # pixel values of 0 is irrigated class, 3 is wetland class; first build a mask of those values
            mask = irr.eq(dataset_dict[variable][0])
    
            # mask the image to irrigated pixels only
            irrmapper_mask = irr.updateMask(mask).remap([dataset_dict[variable][0]], [1])
    
            # Nov 1984 - Sept 1999 ET collection
            monthly_coll_1 = (
                ee.ImageCollection(dataset_dict['etof_irr_status'][1])
                    .select(['et_ensemble_mad'], ['et'])
                    .filter(ee.Filter.date(study_start, '1999-10-01'))
            )
        
            # Oct 1999 - Sept 2024 ET collection
            monthly_coll_2 = (
                ee.ImageCollection(dataset_dict['etof_irr_status'][2])
                    .select(['et_ensemble_mad'], ['et'])
                    .filter(ee.Filter.date('1999-10-01', study_end))
            )
        
            # merge image collections
            final_coll = monthly_coll_1.merge(monthly_coll_2)
    
            # make an annual image from monthly
            eta_an = (
                ee.Image(
                    final_coll
                        .select('et')
                        .filter(ee.Filter.calendarRange(year, year, 'year'))
                        .sum()
                )
                .rename(['eta_an'])
            )
    
            # make an annual image from monthly but masked to irrigated pixels only
            eta_an_masked = (
                ee.Image(
                    final_coll
                        .select('et')
                        .filter(ee.Filter.calendarRange(year, year, 'year'))
                        .sum()
                )
                .updateMask(irrmapper_mask)
                .rename(['eta_an'])
            )
        
            # Image for computing area (ACRES_FTR_GEOM) of all pixels within field boundary
            area_all_img = (
                eta_an
                    .divide(eta_an)
                    .multiply(ee.Image.pixelArea())
                    .rename(['ACRES_ALL_PIXELS'])
                    .divide(4047) 
            )
        
            # Image for computing area (ACRES_FTR_GEOM) of irrigated/wetland pixels within field boundary (uses the irr_mask image as a mask)
            area_masked_img = (
                eta_an_masked
                    .divide(eta_an_masked)
                    .multiply(ee.Image.pixelArea())
                    .rename([f'ACRES_{dataset_dict[variable][1]}_PIXELS'])
                    .divide(4047)
            )
        
            # stack bands  
            all_bnds = area_all_img.addBands(area_masked_img)
    
            # zonal stats computation (reduceRegions, spatial sum, composite dataframe output)
            stats_out = (
                all_bnds
                    .reduceRegions(
                        collection=field_bound,
                        reducer=ee.Reducer.sum(),
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
                    'ACRES_ALL': ftr.get('ACRES_ALL_PIXELS'),
                    f'ACRES_{dataset_dict[variable][1]}': ftr.get(f'ACRES_{dataset_dict[variable][1]}_PIXELS'),
                })
        
            # map the function to organize 
            stats_out_form = ee.FeatureCollection(stats_out.map(orgFeatColl))
    
            # list of properties to export
            selector_list = [unique_id, 'ACRES_ALL', f'ACRES_{dataset_dict[variable][1]}']
    
        
        elif variable == 'etof_irr_status':
    
            # Identify months to run
            start_month = "05"
            end_month = "10"
            
            # Shorted slope months
            short_start_month = "06"
            short_end_month = "09"
            
            # Define EToF threshold
            etof_threshold = 0.5
            etof_short_threshold = -0.05
    
            stats_out = ee.FeatureCollection([])
            
            # Nov 1984 - Sept 1999 ET collection
            monthly_coll_1 = (
                ee.ImageCollection(dataset_dict[variable][1])
                    .select(['et_ensemble_mad'], ['et'])
                    .filter(ee.Filter.date(study_start, '1999-10-01'))
                    .map(addDates)
            )
            
            # Oct 1999 - Sept 2022 ET collection
            monthly_coll_2 = (
                ee.ImageCollection(dataset_dict[variable][2])
                    .select(['et_ensemble_mad'], ['et'])
                    .filter(ee.Filter.date('1999-10-01', study_end))
                    .map(addDates)
            )
            
            # merge image collections
            monthly_coll = monthly_coll_1.merge(monthly_coll_2)
        
        
            # -------------------------------- Build monthly EToF collection -----------------------------
            
        
            # Set start and end dates and create months sequence to iterate over
            # Run for 2016-2021
            start_date = ee.Date(str(year) + '-' + start_month + '-01') # set analysis start date
            end_date = ee.Date(str(year) + '-' + end_month + '-01') # set analysis end date
            count_months = ee.Number(end_date.difference(start_date, 'month')).round()
            month_list = ee.List.sequence(0, count_months)
        
    
            def createMonthlyEtof(i):
                """creates a monthly fraction of reference ET (EToF) image
    
                Args:
                    i: month integer (1-12)
    
                Returns:
                    earth engine monthly fraction of reference ET (EToF) image with updated properties
                
                
                """
        
                # Calculate the offset from start_date and create eng
                ini = start_date.advance(i, 'month')
                end = ini.advance(1, 'month')
        
                # Get first image from collection
                first_img = (
                    ee.Image(monthly_coll
                        .filterDate(ini, end)
                        .select(['et'])
                        .first())
                )
        
                # Filter and reduce the eeMETRIC Collection to median monthly composite
                et = (
                    monthly_coll
                        .filterDate(ini, end)
                        .select(['et'])
                        .median()
                )
        
                # Filter and get first ETo image 
                eto = ee.ImageCollection(dataset_dict[variable][3]).filterDate(ini,end).select(['eto']).first()
        
                # Calculate EToF for the month
                etof = ee.Image(et).divide(eto).rename('etof')
        
                return ee.Image(ee.Image(etof).copyProperties(first_img, ['system:index', 'system:time_start', 'start_date', 'end_date']))
        
            # Map EToF function over images
            month_etof_ic = ee.ImageCollection(month_list.map(createMonthlyEtof))
        
            # ------------------------------- Apply EToF threshold ----------------------------------------
        
        
            # Apply function to get binary ETOF monthly image collection of EToF >0.5
            def createMonthlyBinaryEtof(i):
                """creates a binary fraction of EToF using the specified threshold 
    
                Args:
                    i: earth engine image
    
                Returns:
                    earth engine binary image based on the specified EToF threshold
                
                
                """
                return(i.gte(etof_threshold).set(i.toDictionary()).set('system:time_start', i.get('system:time_start')))
        
            # Map binary EToF function over images
            month_etof_ic_bi = ee.ImageCollection(month_etof_ic).map(createMonthlyBinaryEtof)
        
        
            # --------------------- Assign labels based on monthly EToF time-series -----------------------
        
            # Label categories and definitions
            # 1: Not Irrigated: EToF < 0.5 for most of all growing season months (4 or greater months).
            # 2: Irrigated: EToF > 0.5 May-October (3+ months)
            # 3: Shorted: Doesn't meet criteria for Irrigated or Not Irrigated AND EToF slope of < -0.05
            # 4: Other: Max extent lands not classified using this schema
        
            # Generate irrigated and not irrigated classes based on ruleset described above
            irrigated_i = month_etof_ic_bi.sum().gte(3)
            notirrigated_i = month_etof_ic_bi.sum().lte(2)
        
            
            def slopePrep(img):
                """creates a month integer image to use for determining shorted pixels for the growing season
    
                Args:
                    img: earth engine image
    
                Returns:
                    earth engine image with updated month band
                
                """
                img = ee.Image(img)
                month = ee.Number.parse(ee.String(img.get('start_date')).slice(5, 7))
                img_month = ee.Image(month).rename('month').toInt()
                return img.addBands(img_month)
    
            # Generate shorted class by masking irrigated and not irrigated pixels and applying sens slope reducer and threshold
            month_etof_slope = (
                month_etof_ic
                    .filterDate(str(year) + '-' + short_start_month + '-01', str(year) + '-' + short_end_month + '-30')
                    .map(slopePrep)
                    .select('month', 'etof')
                    .reduce(ee.Reducer.sensSlope())
                    .select('slope')
            )
        
            shorted_i = irrigated_i.updateMask(month_etof_slope.lt(etof_short_threshold))
        
            # Generate other by masking all classified pixels
            other_i = month_etof_ic.first().neq(-100).updateMask(irrigated_i.Not()).updateMask(notirrigated_i.Not()).updateMask(shorted_i.Not()) 
            
            class_ls = ee.ImageCollection([notirrigated_i.multiply(1).toByte().selfMask(),
                                                 irrigated_i.multiply(2).toByte().selfMask(),
                                                 shorted_i.multiply(3).toByte().selfMask(),
                                                 other_i.multiply(4).toByte().selfMask()]).select([0], ['class'])
            
        
            # image used to compute mode of values for each field
            irr_all_c = class_ls.mosaic().rename(['irr_status_all_c'])
            
            irr_1_m = irr_all_c.eq(1)
            irr_2_m = irr_all_c.eq(2)
            irr_3_m = irr_all_c.eq(3)
            irr_4_m = irr_all_c.eq(4)
        
            irr_1_c = irr_all_c.updateMask(irr_1_m).rename(['irr_status_1'])
            irr_2_c = irr_all_c.updateMask(irr_2_m).rename(['irr_status_2'])
            irr_3_c = irr_all_c.updateMask(irr_3_m).rename(['irr_status_3'])
            irr_4_c = irr_all_c.updateMask(irr_4_m).rename(['irr_status_4'])
    
            # stack all bands
            all_bnds = irr_all_c.addBands(irr_1_c).addBands(irr_2_c).addBands(irr_3_c).addBands(irr_4_c)
    
    
            # images already masked to max irr extent raster so no need to add the updateMask here again
            stats_out = (
                all_bnds
                    .reduceRegions(
                        collection=field_bound,
                        reducer=(
                            ee.Reducer.mode().unweighted()
                                .combine(ee.Reducer.count().unweighted(), 'irr_status_1_', False)
                                .combine(ee.Reducer.count().unweighted(), 'irr_status_2_', False)
                                .combine(ee.Reducer.count().unweighted(), 'irr_status_3_', False)
                                .combine(ee.Reducer.count().unweighted(), 'irr_status_4_', False)
                        ),
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
                    f'ETOF_IRR_STATUS_{str(year)[2:]}_MODE': ftr.get('mode'),
                    f'1_NOT_IRRIGATED_{str(year)[2:]}_COUNT': ftr.get('irr_status_1_count'),
                    f'2_IRRIGATED_{str(year)[2:]}_COUNT': ftr.get('irr_status_2_count'),
                    f'3_SHORTED_{str(year)[2:]}_COUNT': ftr.get('irr_status_3_count'),
                    f'4_OTHER_{str(year)[2:]}_COUNT': ftr.get('irr_status_4_count'),
                })
    
    
            # map the function to format 
            stats_out_form  = ee.FeatureCollection(stats_out.map(orgFeatColl))
    
            # list of properties to export
            selector_list = [unique_id,f'ETOF_IRR_STATUS_{str(year)[2:]}_MODE',
                             f'1_NOT_IRRIGATED_{str(year)[2:]}_COUNT', f'2_IRRIGATED_{str(year)[2:]}_COUNT',
                             f'3_SHORTED_{str(year)[2:]}_COUNT', f'4_OTHER_{str(year)[2:]}_COUNT']
        
        
        elif variable == 'crop_type':
    
            # CDL image collection
            cdl_coll = (
                ee.ImageCollection(dataset_dict[variable][1])
                    .select(['cropland'])
            )
            
            if year < 2007:
                print('CDL data not available for the study area prior to 2008, please change the selected start year')
                continue
                
            elif year == 2007:
    
                # mosaic 2007a and 2007b images
                mos_img = (                
                    cdl_coll
                        .filter(ee.Filter.calendarRange(year, year, 'year'))
                        .mosaic()
                )
    
                # CDl image with no 0 pixel values
                cdl_img = mos_img.updateMask(mos_img.neq(0))
                
            else:
    
                # CDL image before 0 pixels are masked
                fir_img = (
                    cdl_coll
                        .filter(ee.Filter.calendarRange(year, year, 'year'))
                        .first()
                )
                
                # cdl image with no 0 pixel values
                cdl_img = fir_img.updateMask(fir_img.neq(0))
    
            # zonal stats computation (reduceRegions, spatial mode, composite dataframe output)
            stats_out = (
                cdl_img
                    .reduceRegions(
                        collection=field_bound,
                        reducer=ee.Reducer.mode(),
                        scale=30,
                        tileScale=16
                    )
                    .map(removGeom)
            )
    
    
            def orgFeatColl(ftr):
                """adds formatted columns/properties to a feature using existing properties/values and converts float values to integers
            
                Args:
                    ftr: earth engine feature
            
                Returns:
                    earth engine feature with updated properties
                
                """
    
                # get the mode property from the stats
                v = ftr.get('mode') # may be null (e.g., NV fields in 2007?)
                
                # check for null values before attempting to convert feature properties (float) to integers
                v_int = ee.Algorithms.If(
                    ee.Algorithms.IsEqual(v, None), # null check
                    None,
                    ee.Number(v).round().toInt()
                )
                
                return ftr.set({
                    f'{dataset_dict[variable][0]}_{year}': v_int,
                })
        
            stats_out_form = ee.FeatureCollection(stats_out.map(orgFeatColl))
            
            
            selector_list = [unique_id, f'{dataset_dict[variable][0]}_{year}']
        
        # Export tasks
        if out_location == 'google_drive':
    
            # Export a CSV file to Google Drive.
            out_table_task = ee.batch.Export.table.toDrive(**{
                'collection': stats_out_form,
                'description': f'OR_Field_Bound_Summary_Export_{variable}_{year}',
                'fileNamePrefix': f'or_field_summaries_{year}_{variable}',
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
                'fileNamePrefix': f'{bucket_path}/or_field_summaries_{year}_{variable}',
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
        description='Earth Engine Field-Level Annual Zonal Stats Table Export',
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