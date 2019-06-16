import os
from CometTS.CometTS import run_comet
from CometTS.CSV_It import csv_it
from CometTS.ARIMA import run_arima
import pandas as pd

"""Pytest evaluations.  These only test the single band processing,
Landsat expansion pack will not include pytesting, if something breaks in this case please open an issueself.
ARIMA testing will be added after expanding functionality.
No plotting testing included."""
data_dir = os.path.dirname(__file__)
os.chdir(data_dir)
os.chdir("..")
data_dir = os.path.join(os.getcwd(), "VIIRS_Sample")
print(data_dir)


class TestEvalBase(object):
    def test_csv_it(self):
        """Test instantiation of csv_it.  Will also test get_extent"""
        base_instance = csv_it(input_dir=data_dir, TSdata="S*rade9*.tif", Observations="S*cvg*.tif", Mask="S*cvg*.tif", DateLoc="10:18", BandNum="")
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
        pd.testing.assert_frame_equal(base_instance.reset_index(drop=True), gdf.reset_index(drop=True))

    def test_run_comet(self):
        print(data_dir)
        """Test instantiation of run_comet.
        This test will hit all core functions including calculate_zonal_stats, get_num_obs, and mask_imagery"""
        base_instance = run_comet(os.path.join(data_dir, "Test_Raster_List2.csv"), os.path.join(data_dir, "San_Juan.shp"), -1, 0, maskit=True)
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
        pd.testing.assert_frame_equal(base_instance.reset_index(drop=True), gdf.reset_index(drop=True))

    def test_ARIMA(self):
        """Test instantiation of ARIMA Functions."""
        run_arima(os.path.join(data_dir, "Test_San_Juan_FullStats2.csv"), os.path.join(data_dir, "Test_San_Juan_ARIMA_Output2.csv"), 3, "2017/08/15", 2)
        base_instance = pd.read_csv(os.path.join(data_dir, "Test_San_Juan_ARIMA_Output2.csv"))
        gdf = pd.read_csv(os.path.join(data_dir, "Test_San_Juan_ARIMA_Output.csv"))
        gdf = gdf.sort_values(by=['date'])
        base_instance = base_instance.sort_values(by=['date'])
        base_instance = base_instance[['date', 'SeasonalForecast']]
        gdf = gdf[['date', 'SeasonalForecast']]
        print(gdf['SeasonalForecast'])
        print(base_instance['SeasonalForecast'])
        pd.testing.assert_frame_equal(base_instance.reset_index(drop=True), gdf.reset_index(drop=True))
