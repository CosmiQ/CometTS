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


### Functions for an auto-regressive integrated moving average analysis using CometTS on a time series of satellite imagery.


def run_plot_TS(main_gdf, figsize = (12,6), y_val_alpha = 1, scatter_alpha = 1, 
             error_alpha = 0.2, y_label = "Brightness", x_label = "Date", title_label= "Brightness over time - Census Tract 9509, Yabucoa Municipio" 
             , outname="/Outname.csv",figname = '', custom_x_axis = True, show_grid = True, show_legend = True, min_count=0.5,ymin=0,ymax=5000):
    print "Plotting..." 
    C=0
    for item in main_gdf['ID'].unique():
        C+=1
        plt.style.use('fivethirtyeight')
        fig, ax = plt.subplots(figsize=figsize)
        gdf3=main_gdf[(main_gdf.ID == item)]
        title= title_label
        gdf3=gdf3.sort_values(['date'])
        gdf3=TS_Trend(gdf3,CMA_Val=5,CutoffDate="2017/08/31")
        gdf3=gdf3.sort_values(['date'])
        x = gdf3['date']
        xdate= x.astype('O')
        xdate=mdates.date2num(xdate)
        y  = gdf3['mean']
        if 'SeasonalForecast' in gdf3.columns:
            if C==1:
                gdf_holder=gdf3
            else:
                gdf_holder=gdf_holder.append(gdf3)
            T= gdf3['SeasonalForecast']
            if 'observations' in gdf3.columns:
                count= gdf3['observations']
            err_plus = gdf3['mean'] + gdf3['std']
            err_minus = gdf3['mean'] - gdf3['std']
            #Set the min_count value as a value from 0 to 1 (0 to 100%)
            #ax.set_ylim([ymin,ymax])

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
                
                
            if len(xdate)==len(gdf3['Trend']):
                # plot regression line, if desired
                idx = np.isfinite(xdate) & np.isfinite(y)
                p2 = np.poly1d(np.polyfit(xdate[idx], y[idx], 1))
                ax.plot(xdate, gdf3['Trend'], '-',label="Linear Forecast", color='#00C5B0', alpha=y_val_alpha)

                #plot running mean regression line
                #RM=(y.rolling(window=6,center=True, min_periods=2).median())
                #ax.plot(xdate, RM, '-',label="Moving Median", alpha=y_val_alpha)

                #Seasonal Forecast
                T=interpolate_gaps(T, limit=3)
                ax.plot(xdate, T, '-',label="Seasonal Forecast", alpha=1, color='#FF8700')

                # scatter points-median top, mean bottom
                ax.scatter(xdate, y, label="Mean", s=50, color='black', alpha=scatter_alpha)
                #ax.scatter(xdate, y2, label="Mean", s=50, color='red',alpha=scatter_alpha,marker='x')


                # if desired, plot error band
                plt.fill_between(xdate, err_plus, err_minus, alpha=error_alpha, color='black', label="Standard Deviation")

                ax.set_ylabel(y_label)
                ax.set_xlabel(x_label)
                if 'observations' in gdf3.columns:
                    ax.scatter(xdate, count, label="# of obs", s=50, color='#330DD0',alpha=y_val_alpha,marker='d')

                ax.yaxis.set_tick_params(labelsize=12)
                if custom_x_axis:
                    xticklabel_pad = 0.1
                    years = mdates.YearLocator()   # every year
                    months = mdates.MonthLocator()  # every month
                    yearsFmt = mdates.DateFormatter('%Y')


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
    output=outname
    gdf_holder.to_csv(output)             
            
            
        
def TS_Trend(gdf3,CMA_Val=5,CutoffDate="2017/08/31"):
    x = gdf3['date']
    CutoffDate=datetime.datetime.strptime(CutoffDate, '%Y/%m/%d').date()
    xcutoff=mdates.date2num(CutoffDate)
    xdate= x.astype('O')
    xdate=mdates.date2num(xdate)
    gdf3['xdate']=xdate
    gdf3['Month']=pd.DatetimeIndex(gdf3['date']).month
    gdf4=gdf3.loc[gdf3['xdate'] <= xcutoff]
    gdf3=gdf3.sort_values(['date'])
    gdf4=gdf4.sort_values(['date'])
    y=gdf4['mean']
    gdf4['CMA'] = y.rolling(window=CMA_Val,center=True).mean()
    gdf4['Div']=gdf4['mean']/gdf4['CMA']
    
    f=gdf4.groupby(['Month'])['Div'].mean()
    f=pd.DataFrame({'Month':f.index, 'SeasonalTrend':f.values})
    gdf4=gdf4.merge(f,on='Month')
    gdf3=gdf3.merge(f,on='Month')
    gdf4['Deseasonalized']=gdf4['mean']/gdf4['SeasonalTrend']
    y = gdf4['Deseasonalized']
    z = gdf4['xdate']
    gdf3=gdf3.sort_values(['date'])
    idx = np.isfinite(z) & np.isfinite(y)
    if not any(idx) == False:
        p2 = np.poly1d(np.polyfit(z[idx], y[idx], 1))
        gdf3['Trend']=p2(gdf3['xdate'])
        gdf3['SeasonalForecast']=gdf3['SeasonalTrend'] * gdf3['Trend']
        return gdf3
    else:
        return gdf3
    
def calc_TS_Trends(main_gdf,outname="/FullStats_TS_Trend.csv"):
    print "Calculating..." 
    C=0
    for item in tqdm(main_gdf['ID'].unique()):
        C+=1
        gdf3=main_gdf[(main_gdf.ID == item)]
        gdf3=gdf3.sort_values(['date'])
        gdf3=TS_Trend(gdf3,CMA_Val=5,CutoffDate="2017/08/31")
        gdf3=gdf3.sort_values(['date'])
        if 'SeasonalForecast' in gdf3.columns:
            if C==1:
                gdf_holder=gdf3
            else:
                gdf_holder=gdf_holder.append(gdf3)
            
    output=outname
    gdf_holder.to_csv(output) 