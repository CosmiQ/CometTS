import os
import glob
import pandas as pd
import geopandas as gpd
from tqdm import tqdm as tqdm
from fnmatch import fnmatch
from CometTS.CometTS import get_extent
import argparse


def csv_it(
        input_dir="./VIIRS_Sample",
        TSdata="S*rade9.tif",
        Observations="",
        Mask="",
        DateLoc="10:18",
        BandNum=""):
    """Document and index your time series of raster imagery, masks, and potentially
    observation data.

    Arguments
    ---------
    input_dir : str
        The specific path to the directory containing your raster data. Each image
        and ancillary data should be stored in uniquely named subdirs.
    TSdata : str
        A search term to identify which images the actual images to use for our
        time series analyis. Can and should include a wildcard flag such as *.
    Observations : str
        If working with monthly or other composite data, the number of observations
        per period of observation may be stored in a separate raster image.
        Passing a search term to identify which files are observation images.
        Can and should include a wildcard flag such as *.
    Mask : str
        Identiy which files are masks that remove anomalies from the imagery.
        Passing a search term to identify which files are mask images.
        Can and should include a wildcard flag such as *.
    DateLoc : str
        Should be in the format int:int. This is used to tell where the date
        information is stored in each filename string.  Typical python index
        format.
    BandNum : int or str
        If there are multiple bands in the dataset and you are only interested
        in a specific one that is stored in a filename, pass that string or value
        here.

    Returns
    -------
    gdf : a :class:`geopandas.geodataframe` that contains the fully documented
    directory structure of all of your timeseries data as well as any ancilary
    files of interest.  Also outputs a CSV documenting all of this.
    """
    # Ensuring the user entered everything properly
    input_dir = input_dir.strip()
    TSdata = TSdata.strip()
    Observations = Observations.strip()
    Mask = Mask.strip()
    DateLoc = DateLoc.strip()
    BandNum = BandNum.strip()

    if len(TSdata) > 0:
        print("Pattern:", TSdata)
    else:
        print("No pattern defined, this is a requirement")
        exit()

    if len(Observations) > 0:
        print("#Obs Pattern:", Observations)
    else:
        print("No Observation pattern entered")
    if len(DateLoc) > 0:
        print("Date Location in filename:", DateLoc)
    else:
        print("No date pattern entered, this is a requirement")
        exit()

    if len(BandNum) > 0:
        print("Band Location in filename:", BandNum)
    else:
        print("No band number location entered")

    if len(Mask) > 0:
        print("Mask band pattern:", Mask)
    else:
        print("No mask band entered")

    os.chdir(input_dir)
    # Identify all subdirs that contain our raster data
    input_subdirs = glob.glob('*/')
    print(len(input_subdirs))

    rasterList = []
    DateLoc = DateLoc.split(":")
    for directory in tqdm(input_subdirs):
        os.chdir(directory)
        # Find our primary rasters of interest
        FilePattern = glob.glob(TSdata)
        if len(Observations) > 0:
            Observations = [Observations]
            FilePattern = [x for x in FilePattern if not any(
                fnmatch(x, TSdata) for TSdata in Observations)]
            Observations = Observations[0]
        for raster in FilePattern:
            statout = [{}]
            statout[0]['File'] = input_dir + '/' + directory + '/' + raster
            rasterExtent = get_extent(raster)
            statout[0]['extent'] = rasterExtent
            date = raster[int(DateLoc[0]):int(DateLoc[1])]
            statout[0]['date'] = pd.to_datetime(
                date, infer_datetime_format=True)
            statout[0]['obs'] = 0
            statout[0]['TS_Data'] = 1
            if len(BandNum) > 0:
                BandNum = raster[int(BandNum[0]):int(BandNum[1])]
                statout[0]['band_num'] = BandNum
            if len(Mask) > 0:
                mask = glob.glob(Mask)[0]
                statout[0]['Mask'] = input_dir + '/' + directory + '/' + mask
            rasterList.append(statout[0])

        if len(Observations) > 0:
            FilePattern = glob.glob(Observations)
            for raster in FilePattern:
                statout = [{}]
                statout[0]['File'] = input_dir + '/' + directory + '/' + raster
                rasterExtent = get_extent(raster)
                statout[0]['extent'] = rasterExtent
                date = raster[int(DateLoc[0]):int(DateLoc[1])]
                statout[0]['date'] = pd.to_datetime(
                    date, infer_datetime_format=True)
                statout[0]['obs'] = 1
                statout[0]['TS_Data'] = 0
                if len(BandNum) > 0:
                    statout[0]['band_num'] = 0
                if len(Mask) > 0:
                    mask = glob.glob(Mask)[0]
                    statout[0]['Mask'] = input_dir + \
                        '/' + directory + '/' + mask
                rasterList.append(statout[0])

        os.chdir(input_dir)

    gdf = gpd.GeoDataFrame(rasterList)
    return gdf


def ls_csv_it(
        input_dir,
        TSdata="L*.tif",
        Mask="",
        DateLoc="10:18",
        Band="BLUE"):
    """Document and index your time series of raster imagery, and masks. Used
    specifically for Landsat imagery.

    Arguments
    ---------
    input_dir : str
        The specific path to the directory containing your raster data. Each image
        and ancillary data should be stored in uniquely named subdirs.
    TSdata : str
        A search term to identify which images the actual images to use for our
        time series analyis. Can and should include a wildcard flag such as *.
    Mask : str
        Identiy which files are masks that remove anomalies from the imagery.
        Passing a search term to identify which files are mask images.
        Can and should include a wildcard flag such as *.
    DateLoc : str
        Should be in the format int:int. This is used to tell where the date
        information is stored in each filename string.  Typical python index
        format.
    Band : str
        Which band of interest you are intersted in plotting.  If interested in
        plotting multiple bands at once, this function must be run interatively.
        Options are: COASTAL, BLUE, GREEN, RED, NIR, SWIR1, SWIR2

    Returns
    -------
    gdf : a :class:`geopandas.geodataframe` that contains the fully documented
    directory structure of all of your timeseries data as well as any ancilary
    files of interest.  Also outputs a CSV documenting all of this.
    """
    # Ensuring the user entered everything properly
    input_dir = input_dir.strip()
    TSdata = TSdata.strip()
    Mask = Mask.strip()
    DateLoc = DateLoc.strip()
    Band = Band.strip()

    if len(TSdata) > 0:
        print("Pattern:", TSdata)
    else:
        print("No pattern defined, this is a requirement")
        exit()
    if len(DateLoc) > 0:
        print("Date Location in filename:", DateLoc)
    else:
        print("No date pattern entered, this is a requirement")
        exit()

    if len(Band) > 0:
        print("Band of interest:", Band)
        if Band == "COASTAL":
            TSdata = ["LC08*band1.tif"]
        if Band == "BLUE":
            TSdata = ['LE07*band1.tif', 'LT05*band1.tif', 'LC08*band2.tif']
        if Band == "GREEN":
            TSdata = ['LE07*band2.tif', 'LT05*band2.tif', 'LC08*band3.tif']
        if Band == "RED":
            TSdata = ['LE07*band3.tif', 'LT05*band3.tif', 'LC08*band4.tif']
        if Band == "NIR":
            TSdata = ['LE07*band4.tif', 'LT05*band4.tif', 'LC08*band5.tif']
        if Band == "SWIR1":
            TSdata = ['LE07*band5.tif', 'LT05*band5.tif', 'LC08*band6.tif']
        if Band == "SWIR2":
            TSdata = ['LE07*band7.tif', 'LT05*band7.tif', 'LC08*band7.tif']
    else:
        print("No band entered, this is recommended for Landsat, unless you are working with an index like NDVI")
        print("Options are: COASTAL, BLUE, GREEN, RED, NIR, SWIR1, SWIR2")
        TSdata = [TSdata]

    if len(Mask) > 0:
        print("Mask band pattern:", Mask)
    else:
        print("No mask band entered")

    os.chdir(input_dir)
    # Identify all subdirs that contain our raster data
    input_subdirs = glob.glob('*/')
    print(len(input_subdirs))

    rasterList = []
    DateLoc = DateLoc.split(":")

    for directory in tqdm(input_subdirs):
        os.chdir(directory)
        # Find our primary rasters of interest
        FilePattern = []
        for item in TSdata:
            FilePattern.extend(glob.glob(item))
        for raster in FilePattern:
            statout = [{}]
            statout[0]['File'] = input_dir + '/' + directory + '/' + raster
            rasterExtent = get_extent(raster)
            statout[0]['extent'] = rasterExtent
            date = raster[int(DateLoc[0]):int(DateLoc[1])]
            statout[0]['date'] = pd.to_datetime(
                date, infer_datetime_format=True)
            statout[0]['obs'] = 0
            statout[0]['TS_Data'] = 1
            if len(Mask) > 0:
                mask = glob.glob(Mask)[0]
                statout[0]['Mask'] = input_dir + '/' + directory + '/' + mask
            rasterList.append(statout[0])

        os.chdir(input_dir)

    gdf = gpd.GeoDataFrame(rasterList)
    return gdf


###############################################################################
def main():

    # Construct argument parser
    parser = argparse.ArgumentParser()
    directory = os.path.join(os.path.abspath(os.path.dirname(__file__)), "VIIRS_Sample")

    # general settings
    parser.add_argument('--input_dir', type=str, default=directory,
                        help="input directory for time series data, default: " + directory)
    parser.add_argument('--TSdata', type=str, default='S*rade9*.tif',
                        help="The naming pattern for your time-series data, if not necessary, just set as *")
    parser.add_argument('--Observations', type=str, default='S*cvg*.tif',
                        help="The number of observations that were aggregated per date-somewhat useful is working with monthly composite data")
    parser.add_argument('--Mask', type=str, default='S*cvg*.tif',
                        help="The naming pattern for your masked data, if you have a seperate mask band. If not set the same as TSData")
    parser.add_argument('--DateLoc', type=str, default='10:18',
                        help="The location of the date within your filename.  This will be extracted using regex techniques. ")
    parser.add_argument('--BandNum', type=str, default='',
                        help="The location of the band number or name in your file.  This will be extracted using regex techniques. ")
    parser.add_argument('--output_dir', type=str, default=directory,
                        help="Default is same as input_dir. ")

    args = parser.parse_args()
    gdf_out = csv_it(input_dir=args.input_dir, TSdata=args.TSdata, Observations=args.Observations,
                     Mask=args.Mask, DateLoc=args.DateLoc, BandNum=args.BandNum)
    output = os.path.join(args.output_dir, 'Raster_List.csv')
    gdf_out.to_csv(output)


###############################################################################

if __name__ == "__main__":
    main()
