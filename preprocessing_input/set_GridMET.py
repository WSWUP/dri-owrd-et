import argparse
import logging
import os
# import pprint

from osgeo import ogr, osr


def main(tgt_path, field_name='GRIDMET_ID'):
    """Add HUC12 tile field to an existing shapefile

    Parameters
    ----------
    tgt_path : str
        File path of the target shapefile.
    field_name : str
        MGRS tile field name (the default is "GEOID").

    """
    logging.info('Setting HUC12 property')


    # Hardcoding MGRS GeoJSON file name and folder (for now)
    # GeoJSON built from HUC12 shapefile using following command:
    #   ogr2ogr MGRS_100kmSQ_ID_conus.geojson MGRS_100kmSQ_ID_conus.shp
    #   -preserve_fid -lco RFC7946=YES
    gridmet_geojson = os.path.join(os.getcwd(), 'gridmet_4km_dd_full.shp')
    gridmet_field_name = 'GRIDMET_ID'



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



    logging.info('\nReading gridMET data')
    logging.info('  {}'.format(gridmet_geojson))
    gridmet_ds = ogr.Open(gridmet_geojson, 0)
    gridmet_lyr = gridmet_ds.GetLayer()
    gridmet_osr = gridmet_lyr.GetSpatialRef()

    # Project the input extent to the MGRS projection
    gridmet_tx = osr.CoordinateTransformation(tgt_osr, gridmet_osr)
    tgt_extent.Transform(gridmet_tx)
    logging.debug('  Extent: {}'.format(tgt_extent))

    # Filter the MGRS to the input extent
    gridmet_lyr.SetSpatialFilter(tgt_extent)

    # Save the gridMET geometry to a dictionary by HUC12 ID
    gridmet_dict = {}
    for gridmet_ftr in gridmet_lyr:
        gridmet_id = gridmet_ftr.GetField(gridmet_field_name)
        gridmet_dict[gridmet_id] = gridmet_ftr.GetGeometryRef().Clone()
    gridmet_ds = None



    logging.info('\nWriting HUC12 ID to shapefile')
    tgt_ds = ogr.Open(tgt_path, 1)
    tgt_lyr = tgt_ds.GetLayer()
    tgt_defn = tgt_lyr.GetLayerDefn()

    # Get the current fields in the shapefile
    tgt_fields = [
        tgt_defn.GetFieldDefn(n).name
        for n in range(tgt_defn.GetFieldCount())
    ]
    logging.debug('  Current Fields: {}'.format(', '.join(tgt_fields)))

    # Add the gridMET tile field if it doesn't exist
    if field_name not in tgt_fields:
        logging.info('  Creating {} field'.format(field_name))
        field = ogr.FieldDefn(field_name, ogr.OFTString)
        field.SetWidth(12)
        tgt_lyr.CreateField(field)
    else:
        pass
        # TODO: Add logic to see if the existing field is the correct type

    # Loop through input features and find an HUC12 that intersects the
    #   centroid of the feature.
    # TODO: Add support for identifying "majority" tile instead of using centroid
    for tgt_ftr in tgt_lyr:
        logging.debug('  FID: {}'.format(tgt_ftr.GetFID()))
        try:
            tgt_geom = tgt_ftr.GetGeometryRef()
            # Compute centroid then project to MGRS spatial reference
            tgt_pnt = tgt_geom.Clone().Centroid()
            tgt_pnt.Transform(gridmet_tx)
            # logging.debug('    {}'.format(tgt_pnt))
            for gridmet_id, gridmet_geom in gridmet_dict.items():
                if tgt_pnt.Intersects(gridmet_geom):
                    # logging.debug('    {}'.format(gridmet_id))
                    tgt_ftr.SetField(field_name, gridmet_id)
            tgt_lyr.SetFeature(tgt_ftr)
        except:
            print("Error with FID: {}".format(tgt_ftr.GetFieldAsString('OPENET_ID')))
    logging.info('  Complete')

    tgt_ds = None


def valid_shp(s):
    # TODO: Add check to see if shapefile is valid or opens?
    if not s.lower().endswith('shp'):
        raise argparse.ArgumentTypeError('file must have a ".shp" extensions')
    else:
        return s

# def valid_gpkg(s):
#     # TODO: Add check to see if shapefile is valid or opens?
#     if not s.lower().endswith('gpkg'):
#         raise argparse.ArgumentTypeError('file must have a ".gpkg" extensions')
#     else:
#         return s

# def valid_data(s):
#     # TODO: Add check to see if shapefile is valid or opens?
#     if not s.lower().endswith('gpkg') or s.lower().endswith('shp'):
#         raise argparse.ArgumentTypeError('file must have ".shp" or ".gpkg" extensions')
#     else:
#         return s


def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='Add GRIDMET_ID tile field to an existing shapefile',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # parser.add_argument(
    #     'tgt', metavar='SHP', type=valid_shp, help='Target shapefile')
    parser.add_argument(
        'tgt', metavar='SHP', type=valid_shp, help='Target geopackage')
    parser.add_argument(
        '--field', default='GRIDMET_ID', type=int, help='GridMET cell field name')
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
