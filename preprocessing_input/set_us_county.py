import argparse
import logging
import os
# import pprint

from osgeo import ogr, osr


def main(tgt_path, field_name='GEOID'):
    """Add MGRS tile field to an existing shapefile

    Parameters
    ----------
    tgt_path : str
        File path of the target shapefile.
    field_name : str
        MGRS tile field name (the default is "GEOID").

    """
    logging.info('Setting county property')


    # Hardcoding MGRS GeoJSON file name and folder (for now)
    # GeoJSON built from MGRS shapefile using following command:
    #   ogr2ogr MGRS_100kmSQ_ID_conus.geojson MGRS_100kmSQ_ID_conus.shp
    #   -preserve_fid -lco RFC7946=YES
    county_geojson = os.path.join(os.getcwd(), 'tl_2021_us_county.geojson')
    county_field_name = 'GEOID'



    # Get the extent of the target shapefile (to spatially filter the MGRS tiles)
    logging.info('\nReading target shapefile extent')
    logging.info('  {}'.format(tgt_path))

    tgt_ds = ogr.Open(tgt_path, 0)
    tgt_lyr = tgt_ds.GetLayer()
    tgt_osr = tgt_lyr.GetSpatialRef()

    # Build an extent geometry that can be projected/transformed below
    tgt_extent = tgt_lyr.GetExtent()
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(tgt_extent[0], tgt_extent[2])
    ring.AddPoint(tgt_extent[1], tgt_extent[2])
    ring.AddPoint(tgt_extent[1], tgt_extent[3])
    ring.AddPoint(tgt_extent[0], tgt_extent[3])
    ring.CloseRings()
    tgt_extent = ogr.Geometry(ogr.wkbPolygon)
    tgt_extent.AddGeometry(ring)
    logging.debug('  Extent: {}'.format(tgt_extent))
    logging.debug('  {}'.format(tgt_osr))
    tgt_ds = None



    logging.info('\nReading County data')
    logging.info('  {}'.format(county_geojson))
    county_ds = ogr.Open(county_geojson, 0)
    county_lyr = county_ds.GetLayer()
    county_osr = county_lyr.GetSpatialRef()

    # Project the input extent to the MGRS projection
    county_tx = osr.CoordinateTransformation(tgt_osr, county_osr)
    tgt_extent.Transform(county_tx)
    logging.debug('  Extent: {}'.format(tgt_extent))

    # Filter the MGRS to the input extent
    county_lyr.SetSpatialFilter(tgt_extent)

    # Save the county geometry to a dictionary by county ID
    county_dict = {}
    for county_ftr in county_lyr:
        county_id = county_ftr.GetField(county_field_name)
        county_dict[county_id] = county_ftr.GetGeometryRef().Clone()
    county_ds = None



    logging.info('\nWriting county ID to shapefile')
    tgt_ds = ogr.Open(tgt_path, 1)
    tgt_lyr = tgt_ds.GetLayer()
    tgt_defn = tgt_lyr.GetLayerDefn()

    # Get the current fields in the shapefile
    tgt_fields = [
        tgt_defn.GetFieldDefn(n).name
        for n in range(tgt_defn.GetFieldCount())
    ]
    logging.debug('  Current Fields: {}'.format(', '.join(tgt_fields)))

    # Add the MGRS tile field if it doesn't exist
    if field_name not in tgt_fields:
        logging.info('  Creating {} field'.format(field_name))
        field = ogr.FieldDefn(field_name, ogr.OFTString)
        field.SetWidth(5)
        tgt_lyr.CreateField(field)
    else:
        pass
        # TODO: Add logic to see if the existing field is the correct type

    # Loop through input features and find an MGRS tile that intersects the
    #   centroid of the feature.
    # TODO: Add support for identifying "majority" tile instead of using centroid
    for tgt_ftr in tgt_lyr:
        logging.debug('  FID: {}'.format(tgt_ftr.GetFID()))
        tgt_geom = tgt_ftr.GetGeometryRef()
        # Compute centroid then project to MGRS spatial reference
        tgt_pnt = tgt_geom.Clone().Centroid()
        tgt_pnt.Transform(county_tx)
        # logging.debug('    {}'.format(tgt_pnt))
        for county_id, county_geom in county_dict.items():
            if tgt_pnt.Intersects(county_geom):
                # logging.debug('    {}'.format(county_id))
                tgt_ftr.SetField(field_name, county_id)
        tgt_lyr.SetFeature(tgt_ftr)
    logging.info('  Complete')

    tgt_ds = None


def valid_shp(s):
    # TODO: Add check to see if shapefile is valid or opens?
    if not s.lower().endswith('shp'):
        raise argparse.ArgumentTypeError('file must have a ".shp" extensions')
    else:
        return s

def valid_gpkg(s):
    # TODO: Add check to see if shapefile is valid or opens?
    if not s.lower().endswith('gpkg'):
        raise argparse.ArgumentTypeError('file must have a ".gpkg" extensions')
    else:
        return s

def valid_data(s):
    # TODO: Add check to see if shapefile is valid or opens?
    if not s.lower().endswith('gpkg') or s.lower().endswith('shp'):
        raise argparse.ArgumentTypeError('file must have ".shp" or ".gpkg" extensions')
    else:
        return s


def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='Add County tile field to an existing shapefile',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # parser.add_argument(
    #     'tgt', metavar='SHP', type=valid_shp, help='Target shapefile')
    parser.add_argument(
        'tgt', metavar='SHP', type=valid_shp, help='Target shapefile')
    parser.add_argument(
        '--field', default='FIPS', type=str, help='County FIPS code field name')
    parser.add_argument(
        '-d', '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action='store_const', dest='loglevel')
    args = parser.parse_args()

    # Convert target shapefile to an absolute path
    if args.tgt and os.path.isfile(os.path.abspath(args.tgt)):
        args.tgt = os.path.abspath(args.tgt)

    return args


if __name__ == '__main__':
    args = arg_parse()
    logging.basicConfig(level=args.loglevel, format='%(message)s')
    main(tgt_path=args.tgt, field_name=args.field)
