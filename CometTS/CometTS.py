import os
import gdal
import rasterio
from rasterstats import zonal_stats
import numpy as np
import pandas as pd
import geopandas as gpd
from tqdm import tqdm as tqdm
import argparse


def run_comet(directory_csv, zonalpoly, NoDataValue, mask_value, maskit=True, Path_out=""):
    """Run CometTS.  Analyze your timeseries of raster data for your polygon(s) of interest.

    Arguments
    ---------
    directory_csv : str
        The specific path to the csv documenting your raster data and
        directory structure created with CometTS.csv_it.
    zonalpoly : str
        The specific path to the polygon (geojson or shapefile or other vector)
        that contains your areas of interest for analysis.
    NoDataValue : int
        The value of blank space where no actual data resides in an image. For
        example Landsat surface reflenctance imagery has a value of -9999 where
        no observations exist. Suggest a value of -1 for NPP VIIRS.  If your
        imagery does not have a NoDataValue set == -1.
    mask_value : int(s)
        The value of a cloud or other anomaly mask (ex: Clouds/Cloud Shadow=1).
         Multiple values can be used and be split by commas (i.e. 1,2,99) if no
          masking is required, leave blank.
    maskit : bool
        Should cloud or anomalies be masked? Defaults to yes (``True``). If true
        the function will use the mask_value(s) passed to automatically remove
        any anomalies from the time series of imagery.
    Path_out :str
        The output path for detailed statistics of each polygon analyzed for the
        entire time series of imagery.  All stats will be stored in csv format.
        Defaults to the same path as directory_csv.

    Returns
    -------
    gdf2 : a :class:`geopandas.geodataframe` that conains all statstics for all
    ploygons and all imagery in the time series. Additonally all statistics for
    each individual polygon will be output in csv format to the Path_out directory.
    """

    print(zonalpoly)
    gdf = gpd.read_file(zonalpoly)
    if maskit:
        mask_value = str(mask_value)
        mask_value = mask_value.split(",")
    # Get the zonal stats
    NoDataValue = int(NoDataValue)
    gdf2 = calculate_zonal_stats(directory_csv, gdf, NoDataValue, mask_value, maskit)
    # Get number of observations
    gdf3 = get_num_obs(directory_csv, gdf, NoDataValue, mask_value, maskit)
    for date in gdf2.iterrows():
        if 'median' in gdf3.columns:
            gdf2['observations'] = gdf3['median']

    # Save CSV
    print("Producing csv output...")
    z_simple = zonalpoly.split('/')
    z_simple = z_simple[-1].split('.')
    z_simple = z_simple[0]
    if Path_out == "":
        Path_out = os.path.dirname(os.path.abspath(directory_csv))

    output = os.path.join(Path_out, z_simple + '_FullStats.csv')
    print("CSV statistics saved here: ", output)
    gdf2.to_csv(output)
    for item in gdf2['ID'].unique():
        gdf3 = gdf2[(gdf2.ID == item)]
        output = os.path.join(
            Path_out, z_simple + '_Stats_ID_' + str(item) + '.csv')
        gdf3.to_csv(output)

    return gdf2


# Mask your data
def mask_imagery(rasterin, mask, geom, NoDataValue, mask_value):
    """Mask your satellite imagery.

    Arguments
    ---------
    rasterin : str
        The specific path to a raster image that you want to mask.
    mask : str
        The specific path to a mask image that specifies where anomalies area
        that should be masked.
    geom : geometery????
        A polygon geometry, as in a single area of interest for where you will
        be doing timeseries analysis.  This is used to only read in a portion of
        the full raster instead of the full image.  This improves computational
        performance.
    NoDataValue : int
        The value of blank space where no actual data resides in an image. For
        example Landsat surface reflenctance imagery has a value of -9999 where
        no observations exist. Suggest a value of -1 for NPP VIIRS.  If your
        imagery does not have a NoDataValue set == -1.
    mask_value : int(s)
        The value of a cloud or other anomaly mask (ex: Clouds/Cloud Shadow=1).
         Multiple values can be used and be split by commas (i.e. 1,2,99) if no
          masking is required, leave blank.

    Returns
    -------
    MRO : a :class:`numpy.array` (masked raster object (MRO)). This is an array
    containing the original data that has been anomaly masked using the mask image.

    affineO : a :class:`rastrio.affine????` an object that contains the specific
    location of the polygon of interest, indexed to the time series imagery.
    This is used to only read in a portion of the full raster instead of the
     full image in the future.  This improves computational performance.
    """

    geom = geom.bounds
    #geom = [geom[0], geom[3], geom[2], geom[1]]
    MRO = gdal.Translate("temp1.vrt", rasterin, projWin=geom).ReadAsArray()
    MR2 = gdal.Translate("temp2.vrt", mask, projWin=geom).ReadAsArray()
    r = rasterio.open("temp1.vrt")
    affineO = r.transform
    del r
    for item in mask_value:
        MRO[np.where(MR2 == int(item))] = NoDataValue
    return MRO, affineO


def calculate_zonal_stats(directory_csv, gdf, NoDataValue, mask_value, maskit=True):
    """Calculate various statistics for each poylgon for a time series of imagery.

    Arguments
    ---------
    directory_csv : str
        The specific path to the csv documenting your raster data and
        directory structure created with CometTS.csv_it.
    gdf : a :class:`geopandas.geodataframe` that conains all of the polygons/
        areas of interest. This is typically converted from zonalpoly in the
        run_comet function.
    NoDataValue : int
        The value of blank space where no actual data resides in an image. For
        example Landsat surface reflenctance imagery has a value of -9999 where
        no observations exist. Suggest a value of -1 for NPP VIIRS.  If your
        imagery does not have a NoDataValue set == -1.
    mask_value : int(s)
        The value of a cloud or other anomaly mask (ex: Clouds/Cloud Shadow=1).
         Multiple values can be used and be split by commas (i.e. 1,2,99) if no
          masking is required, leave blank.
    maskit : bool
        Should cloud or anomalies be masked? Defaults to yes (``True``). If true
        the function will use the mask_value(s) passed to automatically remove
        any anomalies from the time series of imagery.

    Returns
    -------
    gdf2 : a :class:`geopandas.geodataframe` that conains all statstics for all
    ploygons and all imagery in the time series. Additonally all statistics for
    each individual polygon will be output in csv format to the Path_out directory.
    """
    data = pd.read_csv(directory_csv)
    data = data.sort_values(['date'])
    zonelist = []
    print("Processing...")
    for idx, row in tqdm(data.iterrows(), total=data.shape[0]):
        if row['TS_Data'] == 1:
            raster = row['File']
            count = 0
            date = row['date']
            for idx, feature in gdf.iterrows():
                count += 1
                if maskit:
                    MR, affine = mask_imagery(
                        raster, row['Mask'], feature['geometry'], NoDataValue, mask_value)
                    statout = zonal_stats(
                        feature["geometry"],
                        MR,
                        stats="min max median mean std percentile_25 percentile_75 count",
                        nodata=NoDataValue,
                        affine=affine)
                if maskit is False:
                    statout = zonal_stats(
                        feature["geometry"],
                        raster,
                        stats="min max median mean std percentile_25 percentile_75 count",
                        nodata=NoDataValue)

                statout[0]['geometry'] = feature['geometry']
                statout[0]['ID'] = count
                statout[0]['date'] = pd.to_datetime(
                    date, infer_datetime_format=True)
                statout[0]['image'] = raster
                zonelist.append(statout[0])
    gdf2 = gpd.GeoDataFrame(zonelist)
    return gdf2


def get_num_obs(directory_csv, gdf, NoDataValue, mask_value, maskit=True):
    """When working with monthly composite data it may be necessary to calculate
    the number of observations per pixel per month.  For example the VIIRS
    monthly data offers such files.  This function will enable future plotting of
    the number of observations that a satellite collect each month before the
    monthly composite data is aggregated together.

    Arguments
    ---------
    directory_csv : str
        The specific path to the csv documenting your raster data and
        directory structure created with CometTS.csv_it.
    gdf : a :class:`geopandas.geodataframe` that conains all of the polygons/
        areas of interest. This is typically converted from zonalpoly in the
        run_comet function.
    NoDataValue : int
        The value of blank space where no actual data resides in an image. For
        example Landsat surface reflenctance imagery has a value of -9999 where
        no observations exist. Suggest a value of -1 for NPP VIIRS.  If your
        imagery does not have a NoDataValue set == -1.
    mask_value : int(s)
        The value of a cloud or other anomaly mask (ex: Clouds/Cloud Shadow=1).
         Multiple values can be used and be split by commas (i.e. 1,2,99) if no
          masking is required, leave blank.
    maskit : bool
        Should cloud or anomalies be masked? Defaults to yes (``True``). If true
        the function will use the mask_value(s) passed to automatically remove
        any anomalies from the time series of imagery.

    Returns
    -------
    gdf3 : a :class:`geopandas.geodataframe` that conains all statstics for all
    ploygons and all imagery in the time series. Additonally all statistics for
    each individual polygon will be output in csv format to the Path_out directory.
    Specifically contains the number of observations per month in the "Median"
    column.
    """
    data = pd.read_csv(directory_csv)
    data = data.sort_values(['date'])
    zonelist = []
    print("Getting number of observations...")
    for idx, row in tqdm(data.iterrows(), total=data.shape[0]):
        if row['obs'] == 1:
            raster = row['File']
            count = 0
            date = row['date']
            for idx, feature in gdf.iterrows():
                count += 1
                MR = raster
                if maskit:
                    MR, affine = mask_imagery(
                        raster, row['Mask'], feature['geometry'], NoDataValue, mask_value)
                    statout = zonal_stats(
                        feature["geometry"],
                        MR,
                        stats="median",
                        nodata=NoDataValue,
                        affine=affine)

                if not maskit:
                    statout = zonal_stats(
                        feature["geometry"],
                        raster,
                        stats="median",
                        nodata=NoDataValue)

                statout[0]['ID'] = count
                statout[0]['date'] = pd.to_datetime(
                    date, infer_datetime_format=True)
                zonelist.append(statout[0])

    gdf3 = gpd.GeoDataFrame(zonelist)
    return gdf3


def get_extent(raster):
    """Get the extent of a raster image.

    Arguments
    ---------
    raster : str
        The specific path to a raster of interest.

    Returns
    -------
    rasterExtent : list
    A list that contains the extent of a raster in [minx, maxy, maxx, miny] format.
    """
    raster = gdal.Open(raster)
    rastergeo = raster.GetGeoTransform()
    minx = rastergeo[0]
    maxy = rastergeo[3]
    maxx = minx + rastergeo[1] * raster.RasterXSize
    miny = maxy + rastergeo[5] * raster.RasterYSize
    rasterExtent = [minx, maxy, maxx, miny]
    return rasterExtent

###############################################################################


def main():

    # Construct argument parser
    parser = argparse.ArgumentParser()
    directory = os.path.join(os.path.abspath(os.path.dirname(__file__)), "VIIRS_Sample")
    List = os.path.join(directory, 'Raster_List.csv')
    Poly = os.path.join(directory, 'San_Juan.shp')

    # general settings
    parser.add_argument('--input_csv', type=str, default=List,
                        help="Enter csv to data - default: " + List)
    parser.add_argument('--zonalpoly', type=str, default=Poly,
                        help="Enter full path to vector polygon - default: " + Poly)
    parser.add_argument('--NoDataValue', type=str, default=-1,
                        help="Default is -1. Enter NoData Value for null space in imagery(ex: Landsat typically -9999, VIIRS Monthly Composites -1)")
    parser.add_argument('--mask_value', type=str, default=0,
                        help="Default is 0. Enter mask pixel value(s).  (ex: Clouds/Cloud Shadow=1), If multiple values seperate with a comma (i.e. 1,2,99) if no masking is required, leave blank")
    parser.add_argument('--maskit', type=bool, default=True,
                        help="Turn masking functionality on or off, default is true.  Set to false to turn off.")
    parser.add_argument('--Path_out', type=str, default="",
                        help="Add an output path for CSVs.  Default is the same directory as the input_csv")

    args = parser.parse_args()

    run_comet(args.input_csv, args.zonalpoly, args.NoDataValue, args.mask_value, maskit=args.maskit, Path_out=args.Path_out)
    print("Run Plot_Results.ipynb to generate visualizations from output CSV")


###############################################################################

if __name__ == "__main__":
    main()
