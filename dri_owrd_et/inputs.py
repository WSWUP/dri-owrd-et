#--------------------------------
# Name:         inputs.py
# Purpose:      Common INI reading/parsing functions
# Python:       3.6
#--------------------------------

from builtins import input
import datetime
import logging
import os
import sys

import configparser

import dri_owrd_et.utils as utils


def read(ini_path):
    logging.debug('\nReading Input File')
    # Open config file
    config = configparser.ConfigParser()
    try:
        config.read(ini_path)
    except Exception as e:
        logging.error('\nERROR: Input file could not be read, '
                      'is not an input file, or does not exist\n'
                      '  ini_path = {}\n{}\n'.format(ini_path, e))
        sys.exit()

    # Force conversion of unicode to strings
    ini = dict()
    for section in config.keys():
        ini[str(section)] = {}
        for k, v in config[section].items():
            ini[str(section)][str(k)] = v
    return ini


def parse_section(ini, section):
    logging.debug('Checking {} section'.format(section))
    if section not in ini.keys():
        logging.error(
            '\nERROR: Input file does not have an {} section'.format(section))
        sys.exit()

    if section == 'INPUTS':
        parse_inputs(ini)
    elif section == 'ZONAL_STATS':
        parse_zonal_stats(ini)


def get_param(ini, section, input_name, output_name, get_type,
              default='MANDATORY'):
    """Get INI parameters by type and set default values

    Args:
        ini (dict): Nested dictionary of INI file keys/values
        section (str): Section name
        input_name (str): Parameter name in INI file
        output_name (str): Parameter name in code
        get_type (): Python type
        default (): Default value to use if parameter was not set.
            Defaults to "MANDATORY".
            "MANDATORY" will cause script to exit if key does not exist.
    """

    try:
        if get_type is bool:
            ini[section][output_name] = (
                ini[section][input_name].lower() == 'true')
            # ini[section][output_name] = distutils.util.strtobool(
            #     ini[section][input_name])
            # ini[section][output_name] = ini.getboolean(section, input_name)
            # ini[section][output_name] = ini[section].getboolean(input_name)
        elif get_type is int:
            ini[section][output_name] = int(ini[section][input_name])
        elif get_type is float:
            ini[section][output_name] = float(ini[section][input_name])
        elif get_type is list:
            ini[section][output_name] = str(ini[section][input_name])
            # Parsing strings to list is handled in each section separately
            # ini[section][output_name] = [
            #     x.strip()
            #     for x in str(ini[section][input_name]).split(',')]
        else:
            ini[section][output_name] = str(ini[section][input_name])
            # Convert 'None' (strings) to None
            if ini[section][output_name].lower() in ['none', '']:
                ini[section][output_name] = None
    except (KeyError, configparser.NoOptionError):
        if default == 'MANDATORY':
            logging.error(
                '\nERROR: {} was not set in the INI, exiting\n'.format(
                    input_name))
            sys.exit()
        else:
            ini[section][input_name] = default
            ini[section][output_name] = default
            logging.debug('  Setting {} = {}'.format(
                input_name, ini[section][output_name]))
    except ValueError:
        logging.error('\nERROR: Invalid value for "{}"'.format(
            input_name))
        sys.exit()
    except Exception as e:
        logging.error('\nERROR: Unhandled error\n  {}'.format(e))
        sys.exit()

    # If the parameter is renamed, remove the old name/parameter
    if input_name != output_name:
        del ini[section][input_name]


def parse_inputs(ini, section='INPUTS'):
    # MANDATORY PARAMETERS
    # section, input_name, output_name, description, get_type
    param_list = [
        ['root_directory', 'root_directory', str],
        ['gcloud_project_id', 'gcloud_project_id', str],
        ['field_boundary_asset_id', 'field_boundary_asset_id', str],
        ['unique_field_id', 'unique_field_id', str],
        ['huc_level', 'huc_level', str],
        ['start_year', 'start_year', int],
        ['end_year', 'end_year', int],
        ['start_year_climo', 'start_year_climo', int],
        ['end_year_climo', 'end_year_climo', int],
    ]
    for input_name, output_name, get_type in param_list:
        get_param(ini, section, input_name, output_name, get_type)


    if not os.path.isdir(os.path.dirname(ini[section]['root_directory'])):
        logging.error(
            '\nERROR: The root directory/path does not exist, exiting\n'
            '  {}'.format(os.path.dirname(ini[section]['root_directory'])))
        sys.exit()
        
    # Google Cloud project ID
    if ini[section]['gcloud_project_id']:
        ini[section]['gcloud_project_id'] = ini[section]['gcloud_project_id']
    
    if ini[section]['field_boundary_asset_id']:
        ini[section]['field_boundary_asset_id'] = ini[section]['field_boundary_asset_id']

    if ini[section]['unique_field_id']:
        ini[section]['unique_field_id'] = ini[section]['unique_field_id']

    # monthly data variable to extract
    if ini[section]['huc_level']:
        options = ['HUC8', 'HUC12']
        ini[section]['huc_level'] = ini[section]['huc_level']
        if ini[section]['huc_level'] not in options:
            logging.error(
                '\nERROR: Invalid HUC-level specified: {}\n'
                '  Must be: {}'.format(
                    ini[section]['huc_level'], ', '.join(options)))
            sys.exit()
    
    if ini[section]['start_year']:
        ini[section]['start_year'] = ini[section]['start_year']

    if ini[section]['end_year']:
        ini[section]['end_year'] = ini[section]['end_year']

    if ini[section]['start_year_climo']:
        ini[section]['start_year_climo'] = ini[section]['start_year_climo']

    if ini[section]['end_year_climo']:
        ini[section]['end_year_climo'] = ini[section]['end_year_climo']

    # OPTIONAL PARAMETERS
    # param_section, input_name, output_name, get_type, default
    param_list = [
        ['test_flag', 'test_flag', bool, True],
    ]
    for input_name, output_name, get_type, default in param_list:
        get_param(ini, section, input_name, output_name, get_type, default)
        

def parse_zonal_stats(ini, section='ZONAL_STATS'):
    """"""
    # Get the list of Landsat products to compute
    # DEADBEEF - What should the default Landsat products be?
    param_list = [
        ['monthly_variable', 'monthly_variable', str],
        ['export_location', 'export_location', str],
    ]
    for input_name, output_name, get_type in param_list:
        get_param(ini, section, input_name, output_name, get_type)

    
    # monthly data variable to extract
    if ini[section]['monthly_variable']:
        options = ['et', 'et_reference', 'et_fraction', 'ppt']
        ini[section]['monthly_variable'] = ini[section]['monthly_variable']
        if ini[section]['monthly_variable'] not in options:
            logging.error(
                '\nERROR: Invalid data variable: {}\n'
                '  Must be: {}'.format(
                    ini[section]['monthly_variable'], ', '.join(options)))
            sys.exit()
    
    # export location
    if ini[section]['export_location']:
        options = ['cloud_storage', 'google_drive']
        ini[section]['export_location'] = ini[section]['export_location']
        if ini[section]['export_location'] not in options:
            logging.error(
                '\nERROR: Invalid export location: {}\n'
                '  Must be: {}'.format(
                    ini[section]['export_location'], ', '.join(options)))
            sys.exit()


    # OPTIONAL PARAMETERS
    # param_section, input_name, output_name, get_type, default
    param_list = [
        ['gdrive_folder', 'gdrive_folder', str, 'oregon_exports'],
        ['gcloud_bucket', 'gcloud_bucket', str, 'openet'],
        ['gcloud_bucket_path', 'gcloud_bucket_path', str, 'intercomparison/output_main/Oregon_Statewide_2023/field_summaries/historical'],
    ]
    for input_name, output_name, get_type, default in param_list:
        get_param(ini, section, input_name, output_name, get_type, default)
