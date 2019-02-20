import os
from CometTS import CSV_It, Do_Zonal_Stats, get_extent, Get_Num_Obs, Process_imagery, Mask_it
import geopandas as gpd
import pandas as pd

"""Pytest evaluations.  These only test the single band processing,
Landsat expansion pack will not include pytesting, if something breaks in this case please open an issueself.
ARIMA testing will be added after expanding functionality.
No plotting testing included, do your own damn plotting if you have a problem."""



class TestEvalBase(object):
    data_dir = os.path.join(os.path.abspath(os.getcwd()),"VIIRS_Sample")
    def test_CSV_It(self):
        """Test instantiation of CSV_It.  Will also test get_extent"""
        base_instance = CSV_It(data_dir)
        gdf = pd.read_csv(os.path.join(data_dir),"Test_Raster_List.csv"))
        # assert base_instance.ground_truth_sindex.bounds == gdf.sindex.bounds
        assert base_instance.equals(gdf)
        # assert base_instance.ground_truth_GDF.equals(base_instance.ground_truth_GDF_Edit)

    def test_Process_imagery(self):
        """Test instantiation of Process_imagery.
        This test will hit all core functions including Do_Zonal_Stats, Get_Num_Obs, and Mask_it"""
        base_instance = Process_imagery(os.path.join(data_dir),"Test_Raster_List.csv"), os.path.join(data_dir),"San_Juan.shp"), 0)
        gdf = pd.read_csv(os.path.join(data_dir),"Test_San_Juan_FullStats.csv"))
        # assert base_instance.ground_truth_sindex.bounds == gdf.sindex.bounds
        # assert base_instance.equals(gpd.GeoDataFrame([]))
        assert base_instance.equals(gdf)
        # assert base_instance.ground_truth_GDF.equals(base_instance.ground_truth_GDF_Edit)
