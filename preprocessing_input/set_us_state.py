import geopandas as gpd
from shapely.geometry import Point

# Load your input shapefile (features covering the US)
features = gpd.read_file("path_to_your_features_shapefile.shp")

# Load reference U.S. states shapefile
us_states = gpd.read_file("path_to_us_states_shapefile.shp")

# Ensure both shapefiles have the same CRS (Coordinate Reference System)
features = features.to_crs(us_states.crs)

# Function to get state based on feature centroid
def get_state_from_centroid(centroid, states_gdf):
    for idx, state in states_gdf.iterrows():
        if state['geometry'].contains(centroid):
            return state['NAME']  # Assuming 'NAME' is the state name column in the states shapefile
    return None

# Create a new column 'state' in the features GeoDataFrame
features['state'] = features['geometry'].centroid.apply(lambda x: get_state_from_centroid(x, us_states))

# Save the updated shapefile
features.to_file("path_to_output_shapefile.shp", driver='ESRI Shapefile')
