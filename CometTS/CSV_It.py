import os
import glob
import pandas as pd
import geopandas as gpd
from tqdm import tqdm as tqdm
from fnmatch import fnmatch
from CometTS.CometTS import get_extent
import argparse

def CSV_It(
        input_dir="./VIIRS_Sample",
        TSdata="S*rade9.tif",
        Observations="",
        Mask="",
        DateLoc="10:18",
        BandNum=""):
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

###############################################################################
def main():

    ### Construct argument parser
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
    gdf_out = CSV_It(input_dir=args.input_dir, TSdata=args.TSdata, Observations=args.Observations,
                     Mask=args.Mask, DateLoc=args.DateLoc, BandNum=args.BandNum)
    output = os.path.join(args.output_dir, 'Raster_List.csv')
    gdf_out.to_csv(output)


###############################################################################

if __name__ == "__main__":
    main()
