import os
from CometTS.CometTS import Process_imagery
from CometTS.CSV_It import CSV_It
from CometTS.ARIMA import calc_TS_Trends
import pandas as pd

"""Pytest evaluations.  These only test the single band processing,
Landsat expansion pack will not include pytesting, if something breaks in this case please open an issueself.
ARIMA testing will be added after expanding functionality.
No plotting testing included, do your own damn plotting if you have a problem."""
data_dir = os.path.dirname(__file__)
os.chdir(data_dir)
os.chdir("..")
data_dir = os.path.join(os.getcwd(), "VIIRS_Sample")
print(data_dir)


class TestEvalBase(object):
    def test_CSV_It(self):
        # data_dir = os.path.join(os.getcwd(), "VIIRS_Sample")
        """Test instantiation of CSV_It.  Will also test get_extent"""
        base_instance = CSV_It(input_dir=data_dir, TSdata="S*rade9*.tif", Observations="S*cvg*.tif", Mask="S*cvg*.tif", DateLoc="10:18", BandNum="")
        output = os.path.join(data_dir, 'Test_Raster_List2.csv')
        base_instance.to_csv(output)
        base_instance = pd.read_csv(os.path.join(data_dir, "Test_Raster_List2.csv"))
        gdf = pd.read_csv(os.path.join(data_dir, "Test_Raster_List.csv"))
        gdf = gdf.sort_values(by=['date'])
        base_instance = base_instance.sort_values(by=['date'])
        base_instance = base_instance[['date', 'extent']]
        gdf = gdf[['date', 'extent']]
        print(gdf['extent'])
        print(base_instance['extent'])

        # base_instance.set_index('date')
        # gdf.set_index('date')
        # gdf = gdf.loc[:, ~gdf.columns.str.match('Unnamed')]
        # base_instance = base_instance.loc[:, ~base_instance.columns.str.match('Unnamed')]
        # assert base_instance.ground_truth_sindex.bounds == gdf.sindex.bounds
        # assert base_instance.equals(gpd.GeoDataFrame([]))
        pd.testing.assert_frame_equal(base_instance.reset_index(drop=True), gdf.reset_index(drop=True))
        # assert gdf['extent'].equals(base_instance['extent'])

    def test_Process_imagery(self):
        # data_dir = os.path.join(os.getcwd(), "VIIRS_Sample")
        print(data_dir)
        """Test instantiation of Process_imagery.
        This test will hit all core functions including Do_Zonal_Stats, Get_Num_Obs, and Mask_it"""
        base_instance = Process_imagery(os.path.join(data_dir, "Test_Raster_List2.csv"), os.path.join(data_dir, "San_Juan.shp"), -1, 0, maskit=True)
        output = os.path.join(data_dir, 'Test_San_Juan_FullStats2.csv')
        base_instance.to_csv(output)
        base_instance = pd.read_csv(os.path.join(data_dir, "Test_San_Juan_FullStats2.csv"))
        gdf = pd.read_csv(os.path.join(data_dir, "Test_San_Juan_FullStats.csv"))
        gdf = gdf.sort_values(by=['date'])
        base_instance = base_instance.sort_values(by=['date'])
        base_instance = base_instance[['date', 'mean']]
        gdf = gdf[['date', 'mean']]
        print(gdf['mean'])
        print(base_instance['mean'])
        # base_instance.set_index('date')
        # gdf.set_index('date')

        # gdf = gdf.loc[:, ~gdf.columns.str.match('Unnamed')]
        # base_instance = base_instance.loc[:, ~base_instance.columns.str.match('Unnamed')]
        # assert base_instance.ground_truth_sindex.bounds == gdf.sindex.bounds
        # assert base_instance.equals(gpd.GeoDataFrame([]))
        pd.testing.assert_frame_equal(base_instance.reset_index(drop=True), gdf.reset_index(drop=True))
        # assert gdf['mean'].equals(base_instance['mean'])

    def test_ARIMA(self):
        # data_dir = os.path.join(os.getcwd(), "VIIRS_Sample")
        """Test instantiation of ARIMA Functions."""
        calc_TS_Trends(os.path.join(data_dir, "Test_San_Juan_FullStats2.csv"), os.path.join(data_dir, "Test_San_Juan_ARIMA_Output2.csv"), 3, "2017/08/15", 2)
        #output = os.path.join(data_dir, 'Test_San_Juan_FullStats2.csv')
        #base_instance.to_csv(output)
        base_instance = pd.read_csv(os.path.join(data_dir, "Test_San_Juan_ARIMA_Output2.csv"))
        gdf = pd.read_csv(os.path.join(data_dir, "Test_San_Juan_ARIMA_Output.csv"))
        gdf = gdf.sort_values(by=['date'])
        base_instance = base_instance.sort_values(by=['date'])
        base_instance = base_instance[['date', 'SeasonalForecast']]
        gdf = gdf[['date', 'SeasonalForecast']]
        print(gdf['SeasonalForecast'])
        print(base_instance['SeasonalForecast'])
        # base_instance.set_index('date')
        # gdf.set_index('date')
        # gdf = gdf.loc[:, ~gdf.columns.str.match('Unnamed')]
        # base_instance = base_instance.loc[:, ~base_instance.columns.str.match('Unnamed')]
        # assert base_instance.ground_truth_sindex.bounds == gdf.sindex.bounds
        # assert base_instance.equals(gpd.GeoDataFrame([]))
        pd.testing.assert_frame_equal(base_instance.reset_index(drop=True), gdf.reset_index(drop=True))
        # assert gdf['SeasonalForecast'].equals(base_instance['SeasonalForecast'])



"""

        gdf = pd.read_csv(os.path.join(data_dir, "Test_San_Juan_ARIMA_Output.csv"))
        # assert base_instance.ground_truth_sindex.bounds == gdf.sindex.bounds
        # assert base_instance.equals(gpd.GeoDataFrame([]))
        base_instance = pd.read_csv(os.path.join(data_dir, "San_Juan_ARIMA_Output.csv"))
        #bah = pd.testing.assert_frame_equal(base_instance,gdf)
        print(base_instance.index)
        print(gdf.index)
        #print(bah)
        # assert base_instance.ground_truth_GDF.equals(base_instance.ground_truth_GDF_Edit)"""
