import sys
import os
import glob
import gdal
import rasterstats
import rasterio
from rasterstats import zonal_stats
import numpy as np
import pandas as pd
import geopandas as gpd
import fiona
from shapely.geometry import shape
import shapely.wkt
import string
import matplotlib.pyplot as plt
import seaborn as sns; sns.set(color_codes=True)
import datetime
from ipywidgets import interact, interactive, fixed, interact_manual
from IPython.display import Javascript, display, clear_output
import ipywidgets as widgets
from tqdm import tqdm_notebook as tqdm
import matplotlib.dates as mdates
from scipy.signal import gaussian
from scipy.ndimage import filters
from affine import Affine
from fnmatch import fnmatch


def Process_imagery(Path_dir, zonalpoly,NoDataValue,maskit=True):
    print zonalpoly
    gdf=gpd.read_file(zonalpoly)
    count=0
    
    #Get the zonal stats
    NoDataValue=int(NoDataValue)
    gdf2=Do_Zonal_Stats(Path_dir,gdf,NoDataValue,maskit)
    #os.chdir(Path_dir)
    
    #Get number of observations
    gdf3=Get_Num_Obs(Path_dir,gdf,NoDataValue,maskit)
    for date in gdf2.iterrows():
        if 'median' in gdf3.columns:
            gdf2['observations']=gdf3['median']
            
    #Save CSV
    print "Producing csv output..."
    z_simple=zonalpoly.split('/')
    z_simple=z_simple[-1].split('.')
    z_simple=z_simple[0]
    Path_out=os.path.dirname(os.path.abspath(Path_dir))
    
    output=os.path.join(Path_out, z_simple + '_FullStats.csv')
    print "CSV statistics saved here: ",output
    gdf2.to_csv(output)
    for item in gdf2['ID'].unique():
        gdf3=gdf2[(gdf2.ID == item)]
        output=os.path.join(Path_out,z_simple + '_Stats_ID_' + str(item)+'.csv')
        gdf3.to_csv(output)
        
    return gdf2

#Mask your data, this assumes the nodatavalue=0, edit the line below to change this.
def Mask_it(rasterin,mask,geom,NoDataValue,mask_value=0):
    geom=geom.bounds
    geom=[geom[0],geom[3],geom[2],geom[1]]
    MRO=gdal.Translate("temp1.vrt",rasterin,projWin=geom).ReadAsArray()
    MR2=gdal.Translate("temp2.vrt",mask,projWin=geom).ReadAsArray()
    r = rasterio.open("temp1.vrt")
    affineO=r.affine
    del r
    #if more nodata values are required simply add another line or two to this:
    #MRO[np.where((MR2 == 2))] = -9999
    MRO[np.where((MR2 == mask_value))] = NoDataValue
    return MRO, affineO

def Do_Zonal_Stats(Path_dir,gdf,NoDataValue,maskit=True):
    data=pd.read_csv(Path_dir)
    data=data.sort_values(['date'])
    zonelist=[]
    print "Processing..."
    for idx,row in tqdm(data.iterrows(), total=data.shape[0]):
        if row['TS_Data'] == 1:
            raster=row['File']
            count=0
            date=row['date']
            for idx, feature in gdf.iterrows():
                count+=1
                if maskit==True:
                    MR,affine=Mask_it(raster,row['Mask'],feature['geometry'],NoDataValue)
                    statout=zonal_stats(feature["geometry"],MR,stats="min max median mean std percentile_25 percentile_75 count",nodata=NoDataValue,affine=affine)
                if maskit==False:
                    statout=zonal_stats(feature["geometry"],raster,stats="min max median mean std percentile_25 percentile_75 count",nodata=NoDataValue)

                statout[0]['geometry']=feature['geometry']
                statout[0]['ID']=count
                statout[0]['date']=pd.to_datetime(date,infer_datetime_format=True)
                statout[0]['image']=raster
                zonelist.append(statout[0])
    gdf2=gpd.GeoDataFrame(zonelist)
    return gdf2
    
def Get_Num_Obs(Path_dir,gdf,NoDataValue,maskit=True):
    data=pd.read_csv(Path_dir)
    data=data.sort_values(['date'])
    zonelist=[]
    print "Getting number of observations..."
    for idx,row in tqdm(data.iterrows(), total=data.shape[0]):
        if row['obs'] == 1:
            raster=row['File']
            count=0
            date=row['date']
            for idx, feature in gdf.iterrows():
                count+=1
                MR=raster
                if maskit==True:
                    MR,affine=Mask_it(raster,row['Mask'],feature['geometry'],NoDataValue)
                    statout=zonal_stats(feature["geometry"],MR,stats="median",nodata=NoDataValue,affine=affine)
                    
                if maskit==False:
                    statout=zonal_stats(feature["geometry"],raster,stats="median",nodata=NoDataValue)

                #statout=zonal_stats(feature["geometry"],MR,stats="median")
                statout[0]['ID']=count
                statout[0]['date']=pd.to_datetime(date,infer_datetime_format=True)
                zonelist.append(statout[0])
                    
    gdf3=gpd.GeoDataFrame(zonelist)
    return gdf3


        
#run plotting
def interpolate_gaps(values, limit=None):
    """
    Fill gaps using linear interpolation, optionally only fill gaps up to a
    size of `limit`.
    """
    values = np.asarray(values)
    i = np.arange(values.size)
    valid = np.isfinite(values)
    filled = np.interp(i, i[valid], values[valid])

    if limit is not None:
        invalid = ~valid
        for n in range(1, limit+1):
            invalid[:-n] &= invalid[n:]
        filled[invalid] = np.nan

    return filled

def run_plot(main_gdf, figsize = (12,6), y_val_alpha = 1, scatter_alpha = 1, 
             error_alpha = 0.2, y_label = "Brightness", x_label = "Date", title_label= "Brightness over time - ID: " 
             ,figname = '', custom_x_axis = True, show_grid = True, show_legend = True, min_count=0.5):
    print "Plotting..." 
    for item in main_gdf['ID'].unique():
        plt.style.use('fivethirtyeight')
        fig, ax = plt.subplots(figsize=figsize)
        gdf3=main_gdf[(main_gdf.ID == item)]
        title= title_label + str(item)
        gdf3=gdf3.sort_values(['date'])
        x = gdf3['date']
        xdate= x.astype('O')
        xdate=mdates.date2num(xdate)
        y  = gdf3['median']
        if 'observations' in gdf3.columns:
            count= gdf3['observations']
        err_plus = gdf3['percentile_75']
        err_minus = gdf3['percentile_25']
        #Set the min_count value as a value from 0 to 1 (0 to 100%)
        #This will filter out observations where over n% of a polygon is masked out
        if min_count > 0:
            z = gdf3['count']
            zmax=gdf3['count'].max()
            z=z/zmax
            xdate = xdate[z >= min_count]
            y = y[z >= min_count]
            if 'observations' in gdf3.columns:
                count=count[z>= min_count]
            err_plus = err_plus[z >= min_count]
            err_minus = err_minus[z >= min_count]
            
        
    
        
        #y2 = gdf3['mean']


        # plot regression line, if desired
        idx = np.isfinite(xdate) & np.isfinite(y)
        p2 = np.poly1d(np.polyfit(xdate[idx], y[idx], 1))
        ax.plot(xdate, p2(xdate), '-',label="Linear Regression", color='#00C5B0', alpha=y_val_alpha)

        #plot running mean regression line
        RM=(y.rolling(window=6,center=True, min_periods=2).median())
        #ax.plot(xdate, RM, '-',label="Moving Median", alpha=y_val_alpha)

        #Gaussian smoothed plot
        b = gaussian(6, 2)
        ga = filters.convolve1d(y, b/b.sum(),mode="reflect")
        ga=interpolate_gaps(ga, limit=3)
        ax.plot(xdate, ga, '-',label="Gaussian Smoothed", alpha=1, color='#FF8700')

        # scatter points-median top, mean bottom
        ax.scatter(xdate, y, label="Median", s=50, color='black', alpha=scatter_alpha)
        #ax.scatter(xdate, y2, label="Mean", s=50, color='red',alpha=scatter_alpha,marker='x')
            

        # if desired, plot error band
        plt.fill_between(xdate, err_plus, err_minus, alpha=error_alpha, color='black', label="25th to 75th %")

        ax.set_ylabel(y_label)
        ax.set_xlabel(x_label)
        if 'observations' in gdf3.columns:
            ax.scatter(xdate, count, label="# of obs", s=50, color='#330DD0',alpha=y_val_alpha,marker='d')

        ax.yaxis.set_tick_params(labelsize=12)
        if custom_x_axis:
            xticklabel_pad = 0.1
            years = mdates.YearLocator()   # every year
            months = mdates.MonthLocator()  # every month
            yearsFmt = mdates.DateFormatter('%Y-%m')
            

            ax.xaxis.set_major_locator(years)
            ax.xaxis.set_major_formatter(yearsFmt)
            ax.xaxis.set_minor_locator(months)
            
            plt.rc('xtick', labelsize=12)
            
            #ax.set_xticks(xdate)
            #ax.set_xticklabels(x, rotation=50, fontsize=10)
            #ax.tick_params(axis='x', which='major', pad=xticklabel_pad)
            
            #ax.xaxis.set_major_formatter(dateformat)
            #ax.set_xlim(datetime.date(settings.plot['x_min'], 1, 1),datetime.date(settings.plot['x_max'], 12, 31))

        if show_grid:
            ax.grid(b=True, which='minor', color='black', alpha=0.75, linestyle=':')


        if show_legend:
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles, labels, ncol=1, loc='center right', 
               bbox_to_anchor=[1.1, 0.5], 
               columnspacing=1.0, labelspacing=0.0,
               handletextpad=0.0, handlelength=1.5,
               fancybox=True, shadow=True,
               fontsize='x-small')   

        ax.set_title(title)
        plt.tight_layout()
        plt.show()

        # save with figname
        if len(figname) > 0:
            plt.savefig(figname, dpi=dpi)
            
def CSV_It(input_dir, TSdata="S*rade9.tif",Observations="", Mask="",DateLoc="10:18",BandNum=""):
    #Ensuring the user entered everything properly
    input_dir=input_dir.strip()
    TSdata=TSdata.strip()
    Observations=Observations.strip()
    Mask=Mask.strip()
    DateLoc=DateLoc.strip()
    BandNum=BandNum.strip()
    
    if len(TSdata) > 0:
        print "Pattern:", TSdata
    else:
        print "No pattern defined, this is a requirement"
        exit()
        
    if len(Observations) > 0:
        print "#Obs Pattern:",Observations
    else:
        print "No Observation pattern entered"        
    if len(DateLoc) > 0:    
        print "Date Location in filename:", DateLoc
    else:
        print "No date pattern entered, this is a requirement"
        exit()
        
    if len(BandNum) > 0:
        print "Band Location in filename:", BandNum
    else:
        print "No band number location entered"
        
        
    if len(Mask) > 0:
        print "Mask band pattern:", Mask
    else:
        print "No mask band entered"
        
    os.chdir(input_dir)    
    #Identify all subdirs that contain our raster data
    input_subdirs= glob.glob('*/')
    print len(input_subdirs)
    
    rasterList=[]
    DateLoc=DateLoc.split(":")
    for directory in tqdm(input_subdirs):
        os.chdir(directory)
        #Find our primary rasters of interest
        FilePattern=glob.glob(TSdata)
        if len(Observations) > 0:
                Observations=[Observations]
                FilePattern=[x for x in FilePattern if not any(fnmatch(x, TSdata) for TSdata in Observations)]
                Observations=Observations[0]
        for raster in FilePattern:
            statout=[{}]
            statout[0]['File']=input_dir+'/'+directory+'/'+raster
            rasterExtent=get_extent(raster)
            statout[0]['extent']=rasterExtent
            date=raster[int(DateLoc[0]):int(DateLoc[1])]              
            statout[0]['date']=pd.to_datetime(date,infer_datetime_format=True)
            statout[0]['obs']=0
            statout[0]['TS_Data']=1
            if len(BandNum) > 0:
                BandNum=raster[int(BandNum[0]):int(BandNum[1])]
                statout[0]['band_num']=b
            if len(Mask) > 0:
                mask=glob.glob(Mask)[0]
                statout[0]['Mask']=input_dir+'/'+directory+'/'+mask
            rasterList.append(statout[0])

                
        if len(Observations) > 0:        
            FilePattern=glob.glob(Observations)
            for raster in FilePattern:
                statout=[{}]
                statout[0]['File']=input_dir+'/'+directory+'/'+raster
                rasterExtent=get_extent(raster)
                statout[0]['extent']=rasterExtent
                date=raster[int(DateLoc[0]):int(DateLoc[1])]
                statout[0]['date']=pd.to_datetime(date,infer_datetime_format=True)
                statout[0]['obs']=1
                statout[0]['TS_Data']=0
                if len(BandNum) > 0:
                    statout[0]['band_num']=0
                if len(Mask) > 0:
                    mask=glob.glob(Mask)[0]
                    statout[0]['Mask']=input_dir+'/'+directory+'/'+mask
                rasterList.append(statout[0])


                
        os.chdir(input_dir)
            
    
    gdf=gpd.GeoDataFrame(rasterList)
    return gdf
            

def get_extent(raster):
    raster = gdal.Open(raster)
    rastergeo=raster.GetGeoTransform()
    minx = rastergeo[0]
    maxy = rastergeo[3]
    maxx = minx + rastergeo[1] * raster.RasterXSize
    miny = maxy + rastergeo[5] * raster.RasterYSize
    rasterExtent= [minx, maxy, maxx, miny] 
    return rasterExtent


### Run plotting from CSV output ONLY
def gen_plots(input_csv):
    df = pd.read_csv(input_csv)
    df=df.sort_values(['date'])
    geometry = df['geometry'].map(shapely.wkt.loads)
    crs = {'init': 'epsg:2263'}
    gdf = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
    gdf['date']=pd.to_datetime(gdf['date'],infer_datetime_format=True)
    #run_plot(gdf, y_label="NDVI", title_label= "NDVI over time - ID: ")
    run_plot(gdf)