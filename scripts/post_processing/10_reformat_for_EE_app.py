#--------------------------------
# Name:    10_reformat_for_EE_app.py
# Desc:    reformat geodatabase data for 
#           the earth engine application
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
import polars as pl
import polars.selectors as cs
import numpy as np

dri_owrd_et_path = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(os.path.realpath(__file__)))))
sys.path.insert(0, os.path.join(dri_owrd_et_path, 'dri_owrd_et'))
sys.path.insert(0, dri_owrd_et_path)
import dri_owrd_et.inputs_post_processing as inputs
import dri_owrd_et.utils as utils

"""
Reformat the geodatabase for the Earth Engine application

"""

pp = pprint.PrettyPrinter(indent=4)


def main(ini_path=None):
    """ Geodatabase Reformatting for Earth Engine

    Parameters
    ----------
    ini_path : str

    """

    logging.info('\nField-Level Geopackage reformatting for Earth Engine (Step 10)')

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
        
    # -----------------------------------------------------------------------------------------------
    
    # table path
    in_path = os.path.join(root_path, 'tables', 'post_processing', '5_field_geodatabase')
    
    out_path = os.path.join(root_path, 'tables', 'post_processing', '10_reformat_for_EE_app')
    
    # list of variables included in the reformatted database
    var_names = ['ACRES_FTR_GEOM', 'CROP', 'ET_VOLUME', 'ETDa_VOLUME', 'ETO_VOLUME', 'PPT_VOLUME', 'EFF_VOLUMEadj', 'NIWR_VOLUME', 'CU_VOLUMEadj', 'AW']
    
    # irrigation status filtering substring
    irr_name = 'IRR_STATUS'
    
    # -----------------------------------------------------------------------------------------------

    # processing the data in blocks due to runtime/memory issues and limitations with table uploads in Earth Engine
    if end_yr - start_yr <= 9:
        year_blocks = {
            start_yr: end_yr,
        }      
    else: 
        year_blocks = {
            1985: 1994,
            1995: 2004,
            2005: 2014,
            2015: 2024,
        }
    
    for k, v in year_blocks.items():
    
        year_list = list(np.arange(k, v+1))
        
        # monthly time series
        data_mo = {
            unique_id: [],
            'Date': [],
            var_names[0].replace('_', ' '): [],
            'CDL': [],
            'IRR STATUS FLAG': [],
            'IRR EFFICIENCY': [],
            'ITYPE': [],
            'srctype': [],
            var_names[2].replace('_', ' ')+' (acft)': [],
            'ETC VOLUME (acft)': [],
            var_names[4].replace('_', ' ')+' (acft)': [],
            var_names[5].replace('_', ' ')+' (acft)': [],
            'PRZ VOLUME (acft)': [],
            var_names[7].replace('_', ' ')+' (acft)': [],
            'CU VOLUME (acft)': [],
            var_names[9]+' VOLUME (acft)': [],
            var_names[2].split('_')[0]+' RATE (inches)': [],
            'ETC RATE (inches)': [],
            var_names[4].split('_')[0]+' RATE (inches)': [],
            var_names[5].split('_')[0]+' RATE (inches)': [],
            'PRZ RATE (inches)': [],
            var_names[7].split('_')[0]+' RATE (inches)': [],
            'CU RATE (inches)': [],
            var_names[9].split('_')[0]+' RATE (inches)': [],
            'timestep': [],
        }
        schema_mo = {
            unique_id: pl.Utf8,
            'Date': pl.Utf8,
            var_names[0].replace('_', ' '): pl.Float64,
            'CDL': pl.Int32,
            'IRR STATUS FLAG': pl.Int32,
            'IRR EFFICIENCY': pl.Float64,
            'ITYPE': pl.Int32,
            'srctype': pl.Int32,
            var_names[2].replace('_', ' ')+' (acft)': pl.Float64,
            'ETC VOLUME (acft)': pl.Float64,
            var_names[4].replace('_', ' ')+' (acft)': pl.Float64,
            var_names[5].replace('_', ' ')+' (acft)': pl.Float64,
            'PRZ VOLUME (acft)': pl.Float64,
            var_names[7].replace('_', ' ')+' (acft)': pl.Float64,
            'CU VOLUME (acft)': pl.Float64,
            var_names[9]+' VOLUME (acft)': pl.Float64,
            var_names[2].split('_')[0]+' RATE (inches)': pl.Float64,
            'ETC RATE (inches)': pl.Float64,
            var_names[4].split('_')[0]+' RATE (inches)': pl.Float64,
            var_names[5].split('_')[0]+' RATE (inches)': pl.Float64,
            'PRZ RATE (inches)': pl.Float64,
            var_names[7].split('_')[0]+' RATE (inches)': pl.Float64,
            'CU RATE (inches)': pl.Float64,
            var_names[9].split('_')[0]+' RATE (inches)': pl.Float64,
            'timestep': pl.Utf8,
        }
        
        # annual time series
        data_an = {
            unique_id: [],
            'Date': [],
            'Year': [],
            var_names[0].replace('_', ' '): [],
            'CDL': [],
            'IRR STATUS FLAG': [],
            'IRR EFFICIENCY': [],
            'ITYPE': [],
            'srctype': [],
            var_names[2].replace('_', ' ')+' (acft)': [],
            'ETC VOLUME (acft)': [],
            var_names[4].replace('_', ' ')+' (acft)': [],
            var_names[5].replace('_', ' ')+' (acft)': [],
            'PRZ VOLUME (acft)': [],
            var_names[7].replace('_', ' ')+' (acft)': [],
            'CU VOLUME (acft)': [],
            var_names[9]+' VOLUME (acft)': [],
            var_names[2].split('_')[0]+' RATE (inches)': [],
            'ETC RATE (inches)': [],
            var_names[4].split('_')[0]+' RATE (inches)': [],
            var_names[5].split('_')[0]+' RATE (inches)': [],
            'PRZ RATE (inches)': [],
            var_names[7].split('_')[0]+' RATE (inches)': [],
            'CU RATE (inches)': [],
            var_names[9].split('_')[0]+' RATE (inches)': [],
            'timestep': [],
        }
        schema_an = {
            unique_id: pl.Utf8,
            'Date': pl.Utf8,
            'Year': pl.Utf8,
            var_names[0].replace('_', ' '): pl.Float64,
            'CDL': pl.Int32,
            'IRR STATUS FLAG': pl.Int32,
            'IRR EFFICIENCY': pl.Float64,
            'ITYPE': pl.Int32,
            'srctype': pl.Int32,
            var_names[2].replace('_', ' ')+' (acft)': pl.Float64,
            'ETC VOLUME (acft)': pl.Float64,
            var_names[4].replace('_', ' ')+' (acft)': pl.Float64,
            var_names[5].replace('_', ' ')+' (acft)': pl.Float64,
            'PRZ VOLUME (acft)': pl.Float64,
            var_names[7].replace('_', ' ')+' (acft)': pl.Float64,
            'CU VOLUME (acft)': pl.Float64,
            var_names[9]+' VOLUME (acft)': pl.Float64,
            var_names[2].split('_')[0]+' RATE (inches)': pl.Float64,
            'ETC RATE (inches)': pl.Float64,
            var_names[4].split('_')[0]+' RATE (inches)': pl.Float64,
            var_names[5].split('_')[0]+' RATE (inches)': pl.Float64,
            'PRZ RATE (inches)': pl.Float64,
            var_names[7].split('_')[0]+' RATE (inches)': pl.Float64,
            'CU RATE (inches)': pl.Float64,
            var_names[9].split('_')[0]+' RATE (inches)': pl.Float64,
            'timestep': pl.Utf8,
        }
        
        df_ts_mo = pl.DataFrame(data=data_mo, schema=schema_mo)
        df_ts_an = pl.DataFrame(data=data_an, schema=schema_an)
        
        for yr in year_list:
            file = f'or_openet_etdemands_monthly_water_year_shift_1mo_{yr}_final.csv'
            path = os.path.join(in_path, file)
        
            # empty monthly and annual dataframes
            df_cmo = pl.DataFrame([])
            df_can = pl.DataFrame([])
            
            # read field-levedataframe
            try:
                df = (
                    pl.scan_csv(path)
                        .collect(engine='auto')
                        .select(pl.all().sort_by(unique_id))
                        .drop(f'ETOF_IRR_STATUS_{str(yr)[2:]}_MODE')
                )
            except Exception as e:
                print(e)
        
            ### MONTHLY
            # dataframe column renaming to month value
            df_t = (
                df
                    .select(pl.col(f"^.*({unique_id}|ET_VOLUME).*$"))
                    .rename({
                        f'ET_VOLUME_11_{str(yr-1)[2:]}_acft': str(yr-1)+'-11-01',
                        f'ET_VOLUME_12_{str(yr-1)[2:]}_acft': str(yr-1)+'-12-01',
                        f'ET_VOLUME_01_{str(yr)[2:]}_acft': str(yr)+'-01-01',
                        f'ET_VOLUME_02_{str(yr)[2:]}_acft': str(yr)+'-02-01',
                        f'ET_VOLUME_03_{str(yr)[2:]}_acft': str(yr)+'-03-01',
                        f'ET_VOLUME_04_{str(yr)[2:]}_acft': str(yr)+'-04-01',
                        f'ET_VOLUME_05_{str(yr)[2:]}_acft': str(yr)+'-05-01',
                        f'ET_VOLUME_06_{str(yr)[2:]}_acft': str(yr)+'-06-01',
                        f'ET_VOLUME_07_{str(yr)[2:]}_acft': str(yr)+'-07-01',
                        f'ET_VOLUME_08_{str(yr)[2:]}_acft': str(yr)+'-08-01',
                        f'ET_VOLUME_09_{str(yr)[2:]}_acft': str(yr)+'-09-01',
                        f'ET_VOLUME_10_{str(yr)[2:]}_acft': str(yr)+'-10-01',
                    })
            )
            # dates value dataframe
            df_dates = (df_t.unpivot(index=unique_id, variable_name='Date', value_name='Val')
                .select(pl.all().sort_by(unique_id))
                .drop('Val')
            )  
        
            # acreage dataframe duplicated 12 times to match monthly time series lengths
            df_ac_mo = (df.unpivot(index=unique_id, on=cs.contains(var_names[0]), value_name=var_names[0].replace('_',' '))
                .select(pl.all().repeat_by(12).flatten())
                .select(pl.all().sort_by(unique_id))
                .drop('variable')
            )
            # CDL dataframe duplicated 12 times to match monthly time series lengths
            df_cdl_mo = (df.unpivot(index=unique_id, on=cs.contains(var_names[1]), value_name='CDL')
                .select(pl.all().repeat_by(12).flatten())
                .select(pl.all().sort_by(unique_id))
                .drop('variable')
            )
            # irrigation status dataframe duplicated 12 times to match monthly time series lengths
            df_irr_mo = (df.unpivot(index=unique_id, on=cs.contains(irr_name), value_name=irr_name.replace('_', ' '))
                .select(pl.all().repeat_by(12).flatten())
                .select(pl.all().sort_by(unique_id))
                .drop('variable')
            )
            # irrigation status dataframe duplicated 12 times to match monthly time series lengths
            df_ire_mo = (df.unpivot(index=unique_id, on=cs.contains('IRR_EFF'), value_name='IRR EFFICIENCY')
                .select(pl.all().repeat_by(12).flatten())
                .select(pl.all().sort_by(unique_id))
                .drop('variable')
            )
            # irrigation status dataframe duplicated 12 times to match monthly time series lengths
            df_irt_mo = (df.unpivot(index=unique_id, on=cs.contains('ITYPE'), value_name='ITYPE')
                .select(pl.all().repeat_by(12).flatten())
                .select(pl.all().sort_by(unique_id))
                .drop('variable')
            )
            # irrigation status dataframe duplicated 12 times to match monthly time series lengths
            df_src_mo = (df.unpivot(index=unique_id, on=cs.contains('srctype'), value_name='srctype')
                .select(pl.all().repeat_by(12).flatten())
                .select(pl.all().sort_by(unique_id))
                .drop('variable')
            )
            # monthly ET
            df_et_mo = (df.unpivot(index=unique_id, on=cs.contains(var_names[2]), value_name=var_names[2].replace('_', ' ')+' (acft)')
                .select(pl.all().sort_by(unique_id))
            )
            # monthly ETc
            df_etc_mo = (df.unpivot(index=unique_id, on=cs.contains(var_names[3]), value_name='ETC VOLUME (acft)')
                .select(pl.all().sort_by(unique_id))
            )
            # monthly ETo
            df_eto_mo = (df.unpivot(index=unique_id, on=cs.contains(var_names[4]), value_name=var_names[4].replace('_', ' ')+' (acft)')
                .select(pl.all().sort_by(unique_id))
            )
            # monthly PPT
            df_ppt_mo = (df.unpivot(index=unique_id, on=cs.contains(var_names[5]), value_name=var_names[5].replace('_', ' ')+' (acft)')
                .select(pl.all().sort_by(unique_id))
            )
            # monthly Prz
            df_eff_mo = (df.unpivot(index=unique_id, on=cs.contains(var_names[6]), value_name='PRZ VOLUME (acft)')
                .select(pl.all().sort_by(unique_id))
            )
            # monthly NIWR
            df_niwr_mo = (df.unpivot(index=unique_id, on=cs.contains(var_names[7]), value_name=var_names[7].replace('_', ' ')+' (acft)')
                .select(pl.all().sort_by(unique_id))
            )
            # monthly CU
            df_cu_mo = (df.unpivot(index=unique_id, on=cs.contains(var_names[8]), value_name='CU VOLUME (acft)')
                .select(pl.all().sort_by(unique_id))
            )
            # monthly CUnet
            df_aw_mo = (df.unpivot(index=unique_id, on=cs.contains(var_names[9]), value_name=var_names[9]+' VOLUME (acft)')
                .select(pl.all().sort_by(unique_id))
            )
        
            # single year timeseries (irrigated fields only)
            df_cmo = (
                df_cmo
                    .with_columns(
                        df_dates[unique_id].alias(unique_id),
                        df_dates['Date'].cast(pl.Utf8).alias('Date'),
                        df_ac_mo[var_names[0].replace('_',' ')].alias(var_names[0].replace('_',' ')),
                        df_cdl_mo['CDL'].cast(pl.Int32).alias('CDL'),
                        df_irr_mo[irr_name.replace('_',' ')].cast(pl.Int32).alias('IRR STATUS FLAG'),
                        df_ire_mo['IRR EFFICIENCY'].alias('IRR EFFICIENCY'),
                        df_irt_mo['ITYPE'].cast(pl.Int32).alias('ITYPE'),
                        df_src_mo['srctype'].cast(pl.Int32).alias('srctype'),
                        df_et_mo[var_names[2].replace('_',' ')+' (acft)'].alias(var_names[2].replace('_',' ')+' (acft)'),
                        df_etc_mo['ETC VOLUME (acft)'].alias('ETC VOLUME (acft)'),
                        df_eto_mo[var_names[4].replace('_',' ')+' (acft)'].alias(var_names[4].replace('_',' ')+' (acft)'),
                        df_ppt_mo[var_names[5].replace('_',' ')+' (acft)'].alias(var_names[5].replace('_',' ')+' (acft)'),
                        df_eff_mo['PRZ VOLUME (acft)'].alias('PRZ VOLUME (acft)'),
                        df_niwr_mo[var_names[7].replace('_',' ')+' (acft)'].alias(var_names[7].replace('_',' ')+' (acft)'),
                        df_cu_mo['CU VOLUME (acft)'].alias('CU VOLUME (acft)'),
                        df_aw_mo[var_names[9]+' VOLUME (acft)'].alias(var_names[9]+' VOLUME (acft)'),
                    )
            )
        
        
            # add irrigation status flag column based on classification values and calculate rates from volume columns
            df_cmo_s = (
                df_cmo
                    .with_columns(
                        (pl.col(var_names[2].replace('_',' ')+' (acft)') / pl.col(var_names[0].replace('_',' ')) * 12).alias(var_names[2 ].split('_')[0]+' RATE (inches)'),
                        (pl.col('ETC VOLUME (acft)') / pl.col(var_names[0].replace('_',' ')) * 12).alias('ETC RATE (inches)'),
                        (pl.col(var_names[4].replace('_',' ')+' (acft)') / pl.col(var_names[0].replace('_',' ')) * 12).alias(var_names[4].split('_')[0]+' RATE (inches)'),
                        (pl.col(var_names[5].replace('_',' ')+' (acft)') / pl.col(var_names[0].replace('_',' ')) * 12).alias(var_names[5].split('_')[0]+' RATE (inches)'),
                        (pl.col('PRZ VOLUME (acft)') / pl.col(var_names[0].replace('_',' ')) * 12).alias('PRZ RATE (inches)'),
                        (pl.col(var_names[7].replace('_',' ')+' (acft)') / pl.col(var_names[0].replace('_',' ')) * 12).alias(var_names[7].split('_')[0]+' RATE (inches)'),
                        (pl.col('CU VOLUME (acft)') / pl.col(var_names[0].replace('_',' ')) * 12).alias('CU RATE (inches)'),
                        (pl.col(var_names[9]+' VOLUME (acft)') / pl.col(var_names[0].replace('_',' ')) * 12).alias(var_names[9]+' RATE (inches)'),
                    )
            )
        
            # overwrite CU values when fields are not classified as irrigated for the given year
            df_cmo_f = (
                df_cmo_s
                    .with_columns(
                        pl.when(pl.col('IRR STATUS FLAG') == 0).then(0).otherwise(pl.col('CU VOLUME (acft)')).alias('CU VOLUME (acft)'),
                        pl.when(pl.col('IRR STATUS FLAG') == 0).then(0).otherwise(pl.col(var_names[9]+' VOLUME (acft)')).alias(var_names[9]+' VOLUME (acft)'),
                        pl.when(pl.col('IRR STATUS FLAG') == 0).then(0).otherwise(pl.col('CU RATE (inches)')).alias('CU RATE (inches)'),
                        pl.when(pl.col('IRR STATUS FLAG') == 0).then(0).otherwise(pl.col(var_names[9]+' RATE (inches)')).alias(var_names[9]+' RATE (inches)'),
                        pl.lit('monthly').alias('timestep'),
                    )
            )
        
            # round float columns
            df_cmo_fround = (
                df_cmo_f
                    .with_columns(
                        pl.col(pl.Float64).round(3)
                    )
            )
        
            # add the year's time series to the final dataframe
            data_mo_c = [df_ts_mo, df_cmo_fround]
            df_ts_mo = pl.concat(data_mo_c, how='vertical')
        
        
            ### ANNUAL
            df_ac_an = (
                df
                    .select(pl.col(f"^.*({unique_id}|ACRES_FTR_GEOM).*$"))
                    .rename({
                        f'ACRES_FTR_GEOM_{str(yr)[2:]}': var_names[0].replace('_',' '),
                    })
            )
            df_cdl_an = (
                df
                    .select(pl.col(f"^.*({unique_id}|CROP).*$"))
                    .rename({
                        f'CROP_{yr}': 'CDL',
                    })
            )
        
            df_irr_an = (
                df
                    .select(pl.col(f"^.*({unique_id}|IRR_STATUS).*$"))
                    .rename({
                        f'IRR_STATUS_{yr}': 'IRR STATUS FLAG',
                    })
            )
        
            df_ire_an = (
                df
                    .select(pl.col(f"^.*({unique_id}|IRR_EFF).*$"))
                    .rename({
                        'IRR_EFF': 'IRR EFFICIENCY',
                    })
            )
        
            df_ity_an = (
                df.select(pl.col(f"^.*({unique_id}|ITYPE).*$"))
            )
        
            df_src_an = (
                df.select(pl.col(f"^.*({unique_id}|srctype).*$"))
            )
        
        
            # add annual sum columns
            df = df.with_columns(
                df.select(pl.col("^.*(ET_VOLUME).*$")).sum_horizontal().alias(f'ET_{str(yr)[2:]}_acft'),
                df.select(pl.col("^.*(ETDa_VOLUME).*$")).sum_horizontal().alias(f'ETC_{str(yr)[2:]}_acft'),
                df.select(pl.col("^.*(ETO_VOLUME).*$")).sum_horizontal().alias(f'ETO_{str(yr)[2:]}_acft'),
                df.select(pl.col("^.*(PPT_VOLUME).*$")).sum_horizontal().alias(f'PPT_{str(yr)[2:]}_acft'),
                df.select(pl.col("^.*(EFF_VOLUMEadj).*$")).sum_horizontal().alias(f'PRZ_{str(yr)[2:]}_acft'),
                df.select(pl.col("^.*(NIWR_VOLUME).*$")).sum_horizontal().alias(f'NIWR_{str(yr)[2:]}_acft'),
                df.select(pl.col("^.*(IRR_CU_VOLUMEadj).*$")).sum_horizontal().alias(f'CU_{str(yr)[2:]}_acft'),
                df.select(pl.col("^.*(AW).*$")).sum_horizontal().alias(f'AW_{str(yr)[2:]}_acft'),
            )
            
            
            df_can = (
                df_can
                    .with_columns(
                        df[unique_id].alias(unique_id),
                        pl.lit(f'{yr-1}-11-01').cast(pl.Utf8).alias('Date'),
                        pl.lit(yr).cast(pl.Utf8).alias('Year'),
                        df_ac_an[var_names[0].replace('_',' ')].alias(var_names[0].replace('_',' ')),
                        df_cdl_an['CDL'].cast(pl.Int32).alias('CDL'),
                        df_irr_an['IRR STATUS FLAG'].cast(pl.Int32).alias('IRR STATUS FLAG'),
                        df_ire_an['IRR EFFICIENCY'].alias('IRR EFFICIENCY'),
                        df_ity_an['ITYPE'].cast(pl.Int32).alias('ITYPE'),
                        df_src_an['srctype'].cast(pl.Int32).alias('srctype'),
                        df[f"{var_names[2].split('_')[0]}_{str(yr)[2:]}_acft"].alias(var_names[2].split('_')[0]+' VOLUME (acft)'),
                        df[f"ETC_{str(yr)[2:]}_acft"].alias('ETC VOLUME (acft)'),
                        df[f"{var_names[4].split('_')[0]}_{str(yr)[2:]}_acft"].alias(var_names[4].split('_')[0]+' VOLUME (acft)'),
                        df[f"{var_names[5].split('_')[0]}_{str(yr)[2:]}_acft"].alias(var_names[5].split('_')[0]+' VOLUME (acft)'),
                        df[f"PRZ_{str(yr)[2:]}_acft"].alias('PRZ VOLUME (acft)'),
                        df[f"{var_names[7].split('_')[0]}_{str(yr)[2:]}_acft"].alias(var_names[7].split('_')[0]+' VOLUME (acft)'),
                        df[f"CU_{str(yr)[2:]}_acft"].alias('CU VOLUME (acft)'),
                        df[f"{var_names[9]}_{str(yr)[2:]}_acft"].alias(var_names[9]+' VOLUME (acft)'),
                    )
            )
        
            # add irrigation status flag column based on classification values and calculate rates from volume columns
            df_can_s = (
                df_can
                    .with_columns(
                        (pl.col(var_names[2].replace('_',' ')+' (acft)') / pl.col(var_names[0].replace('_',' ')) * 12).alias(var_names[2].split('_')[0]+' RATE (inches)'),
                        (pl.col('ETC VOLUME (acft)') / pl.col(var_names[0].replace('_',' ')) * 12).alias('ETC RATE (inches)'),
                        (pl.col(var_names[4].replace('_',' ')+' (acft)') / pl.col(var_names[0].replace('_',' ')) * 12).alias(var_names[4].split('_')[0]+' RATE (inches)'),
                        (pl.col(var_names[5].replace('_',' ')+' (acft)') / pl.col(var_names[0].replace('_',' ')) * 12).alias(var_names[5].split('_')[0]+' RATE (inches)'),
                        (pl.col('PRZ VOLUME (acft)') / pl.col(var_names[0].replace('_',' ')) * 12).alias('PRZ RATE (inches)'),
                        (pl.col(var_names[7].replace('_',' ')+' (acft)') / pl.col(var_names[0].replace('_',' ')) * 12).alias(var_names[7].split('_')[0]+' RATE (inches)'),
                        (pl.col('CU VOLUME (acft)') / pl.col(var_names[0].replace('_',' ')) * 12).alias('CU RATE (inches)'),
                        (pl.col(var_names[9]+' VOLUME (acft)') / pl.col(var_names[0].replace('_',' ')) * 12).alias(var_names[9]+' RATE (inches)'),
                    )
            )
        
            # overwrite CU values when fields are not classified as irrigated for the given year
            df_can_f = (
                df_can_s
                    .with_columns(
                        pl.when(pl.col('IRR STATUS FLAG') == 0).then(0).otherwise(pl.col('CU VOLUME (acft)')).alias('CU VOLUME (acft)'),
                        pl.when(pl.col('IRR STATUS FLAG') == 0).then(0).otherwise(pl.col(var_names[9]+' VOLUME (acft)')).alias(var_names[9]+' VOLUME (acft)'),
                        pl.when(pl.col('IRR STATUS FLAG') == 0).then(0).otherwise(pl.col('CU RATE (inches)')).alias('CU RATE (inches)'),
                        pl.when(pl.col('IRR STATUS FLAG') == 0).then(0).otherwise(pl.col(var_names[9]+' RATE (inches)')).alias(var_names[9]+' RATE (inches)'),
                        pl.lit('annual').alias('timestep'),
                    )
            )
        
            # round float columns
            df_can_fround = (
                df_can_f
                    .with_columns(
                        pl.col(pl.Float64).round(3)
                    )
            )
        
            # add the year's time series to the final dataframe
            data_an_c = [df_ts_an, df_can_fround]
            df_ts_an = pl.concat(data_an_c, how='vertical')
        
        # sort values
        df_ts_mo = df_ts_mo.select(pl.all().sort_by([unique_id, 'Date']))
        df_ts_an = df_ts_an.select(pl.all().sort_by([unique_id, 'Date']))
        
        df_ts_mo = df_ts_mo.rename({'ACRES FTR GEOM': 'ACRES'})
        df_ts_an = df_ts_an.rename({'ACRES FTR GEOM': 'ACRES'})
        
        # export monthly and annual timeseries
        df_ts_mo.write_csv(os.path.join(out_path, f'oregon_field_monthly_summary_{year_list[0]}_{year_list[-1]}.csv'), separator=',')
        df_ts_an.write_csv(os.path.join(out_path, f'oregon_field_annual_summary_{year_list[0]}_{year_list[-1]}.csv'), separator=',')
        
        print(f'finished exporting reformatted data for {year_list[0]}-{year_list[-1]}')

    if end_yr - start_yr <= 9:
        filename_a1 = f'oregon_field_annual_summary_{start_yr}_{end_yr}.csv'
            
        df_ts_an_mpre = (
            pl.scan_csv(os.path.join(out_path, filename_a1))
                .collect(engine='auto')
                .select(pl.all())
        )
        
        
    else:
        # input filenames for the annual timeseries files
        filename_a1 = 'oregon_field_annual_summary_1985_1994.csv'
        filename_a2 = 'oregon_field_annual_summary_1995_2004.csv'
        filename_a3 = 'oregon_field_annual_summary_2005_2014.csv'
        filename_a4 = 'oregon_field_annual_summary_2015_2024.csv'
        
        try:
            df_a1 = (
                pl.scan_csv(os.path.join(out_path, filename_a1))
                    .collect(engine='auto')
                    .select(pl.all())
            )
            df_a2 = (
                pl.scan_csv(os.path.join(out_path, filename_a2))
                    .collect(engine='auto')
                    .select(pl.all())
            )
            df_a3 = (
                pl.scan_csv(os.path.join(out_path, filename_a3))
                    .collect(engine='auto')
                    .select(pl.all())
            )
            df_a4 = (
                pl.scan_csv(os.path.join(out_path, filename_a4))
                    .collect(engine='auto')
                    .select(pl.all())
            )
        except Exception as e:
            print(e)
        
        # concatenate the four dataframes vertically and re-sort
        df_ts_an_mpre = pl.concat([df_a1, df_a2, df_a3, df_a4], how='vertical')
        
    df_ts_an_m = df_ts_an_mpre.select(pl.all().sort_by(['OPENET_ID','Date']))
    
    # calculate a mean annual dataframe to export grouped by DRI_ID, but first replace 0's with nans before calculating means
    df_mean_an_pre = (
        df_ts_an_m
            .with_columns(
                pl.col(pl.Float64).replace(0, np.nan)
            )
    )
    
    # prep stat settings for all columns, CDL needs to use a mode statistic
    mode_cols = ['CDL']
    
    # mean annual dataframe
    df_mean_an = (
        df_mean_an_pre
            .group_by('OPENET_ID', maintain_order=True)
            .agg([pl.col('CDL').mode().first().alias('CDL')]
                +
                 [pl.col('IRR STATUS FLAG').mean().cast(pl.Int32).alias('IRR STATUS FLAG')]
                +
                 [pl.col(pl.Float64).exclude(mode_cols).mean()])
            .with_columns(
                (pl.col('ET RATE (inches)') / pl.col('PPT RATE (inches)')).alias('ET_to_PPT_ratio'),
                (pl.col('PRZ RATE (inches)') / pl.col('PPT RATE (inches)')).alias('PRZ_to_PPT_ratio'),
                pl.col(pl.Float64).round(3),
            )
            .fill_nan(0)
    )
    
    # export annual dataframe
    df_ts_an_m.write_csv(os.path.join(out_path, 'oregon_field_annual_summary.csv'), separator=',')
    df_mean_an.write_csv(os.path.join(out_path, 'oregon_field_mean_annual_summary.csv'), separator=',')

    print('saved mean annual summary table')
        
    
def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='Field-Level Geopackage Reformatting for Earth Engine (Step 10)',
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