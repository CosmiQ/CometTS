import os
import glob
import gdal
import rasterio
from rasterstats import zonal_stats
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely.wkt
import matplotlib.pyplot as plt
from tqdm import tqdm as tqdm
import matplotlib.dates as mdates
from scipy.signal import gaussian
from scipy.ndimage import filters
import argparse


def Process_imagery(Path_dir, zonalpoly, NoDataValue, mask_value, maskit=True, Path_out=""):
    print(zonalpoly)
    gdf = gpd.read_file(zonalpoly)
    if maskit:
        mask_value = str(mask_value)
        mask_value = mask_value.split(",")
    # Get the zonal stats
    NoDataValue = int(NoDataValue)
    gdf2 = Do_Zonal_Stats(Path_dir, gdf, NoDataValue, mask_value, maskit)
    # Get number of observations
    gdf3 = Get_Num_Obs(Path_dir, gdf, NoDataValue, mask_value, maskit)
    for date in gdf2.iterrows():
        if 'median' in gdf3.columns:
            gdf2['observations'] = gdf3['median']

    # Save CSV
    print("Producing csv output...")
    z_simple = zonalpoly.split('/')
    z_simple = z_simple[-1].split('.')
    z_simple = z_simple[0]
    if Path_out == "":
        Path_out = os.path.dirname(os.path.abspath(Path_dir))

    output = os.path.join(Path_out, z_simple + '_FullStats.csv')
    print("CSV statistics saved here: ", output)
    gdf2.to_csv(output)
    for item in gdf2['ID'].unique():
        gdf3 = gdf2[(gdf2.ID == item)]
        output = os.path.join(
            Path_out,
            z_simple +
            '_Stats_ID_' +
            str(item) +
            '.csv')
        gdf3.to_csv(output)

    return gdf2


# Mask your data
def Mask_it(rasterin, mask, geom, NoDataValue, mask_value):
    geom = geom.bounds
    geom = [geom[0], geom[3], geom[2], geom[1]]
    MRO = gdal.Translate("temp1.vrt", rasterin, projWin=geom).ReadAsArray()
    MR2 = gdal.Translate("temp2.vrt", mask, projWin=geom).ReadAsArray()
    r = rasterio.open("temp1.vrt")
    affineO = r.transform
    del r
    for item in mask_value:
        MRO[np.where(MR2 == int(item))] = NoDataValue
    return MRO, affineO


def Do_Zonal_Stats(Path_dir, gdf, NoDataValue, mask_value, maskit=True):
    data = pd.read_csv(Path_dir)
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
                    MR, affine = Mask_it(
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


def Get_Num_Obs(Path_dir, gdf, NoDataValue, mask_value, maskit=True):
    data = pd.read_csv(Path_dir)
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
                    MR, affine = Mask_it(
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

                #statout=zonal_stats(feature["geometry"],MR, stats="median")
                statout[0]['ID'] = count
                statout[0]['date'] = pd.to_datetime(
                    date, infer_datetime_format=True)
                zonelist.append(statout[0])

    gdf3 = gpd.GeoDataFrame(zonelist)
    return gdf3


# run plotting
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
        for n in range(1, limit + 1):
            invalid[:-n] &= invalid[n:]
        filled[invalid] = np.nan

    return filled


def run_plot(
        main_gdf,
        figsize=(
            12,
            6),
    y_val_alpha=1,
    scatter_alpha=1,
    error_alpha=0.2,
    y_label="Brightness",
    x_label="Date",
    title_label="Brightness over time - ID: ",
    figname='',
    custom_x_axis=True,
    show_grid=True,
    show_legend=True,
    min_count=0.5,
    ymin=0,
    ymax=50,
        dynamic_max=False):
    print("Plotting...")
    for item in main_gdf['ID'].unique():
        plt.style.use('fivethirtyeight')
        fig, ax = plt.subplots(figsize=figsize)
        gdf3 = main_gdf[(main_gdf.ID == item)]
        title = title_label + str(item)
        gdf3 = gdf3.sort_values(['date'])
        x = gdf3['date']
        xdate = x.astype('O')
        xdate = mdates.date2num(xdate)
        y = gdf3['median']
        if dynamic_max:
            ymax = gdf3['median'].max() + (gdf3['median'].max() * 0.5)
        if 'observations' in gdf3.columns:
            count = gdf3['observations']
        err_plus = gdf3['percentile_75']
        err_minus = gdf3['percentile_25']
        # Set the min_count value as a value from 0 to 1 (0 to 100%)
        ax.set_ylim([ymin, ymax])

        # This will filter out observations where over n% of a polygon is
        # masked out
        if min_count > 0:
            z = gdf3['count']
            zmax = gdf3['count'].max()
            z = z / zmax
            xdate = xdate[z >= min_count]
            y = y[z >= min_count]
            if 'observations' in gdf3.columns:
                count = count[z >= min_count]
            err_plus = err_plus[z >= min_count]
            err_minus = err_minus[z >= min_count]

        # plot regression line, if desired
        idx = np.isfinite(xdate) & np.isfinite(y)
        p2 = np.poly1d(np.polyfit(xdate[idx], y[idx], 1))
        ax.plot(
            xdate,
            p2(xdate),
            '-',
            label="Linear Regression",
            color='#00C5B0',
            alpha=y_val_alpha)

        # plot running mean regression line
        # RM=(y.rolling(window=6, center=True, min_periods=2).median())
        # ax.plot(xdate, RM, '-',label="Moving Median", alpha=y_val_alpha)

        # Gaussian smoothed plot
        b = gaussian(6, 2)
        ga = filters.convolve1d(y, b / b.sum(), mode="reflect")
        ga = interpolate_gaps(ga, limit=3)
        ax.plot(
            xdate,
            ga,
            '-',
            label="Gaussian Smoothed",
            alpha=1,
            color='#FF8700')

        # scatter points-median top, mean bottom
        ax.scatter(
            xdate,
            y,
            label="Median",
            s=50,
            color='black',
            alpha=scatter_alpha)
        # ax.scatter(xdate, y2, label="Mean", s=50, color='red',alpha=scatter_alpha, marker='x')

        # if desired, plot error band
        plt.fill_between(
            xdate,
            err_plus,
            err_minus,
            alpha=error_alpha,
            color='black',
            label="25th to 75th %")

        ax.set_ylabel(y_label)
        ax.set_xlabel(x_label)
        if 'observations' in gdf3.columns:
            ax.scatter(
                xdate,
                count,
                label="# of obs",
                s=50,
                color='#330DD0',
                alpha=y_val_alpha,
                marker='d')

        ax.yaxis.set_tick_params(labelsize=12)
        if custom_x_axis:
            years = mdates.YearLocator()   # every year
            months = mdates.MonthLocator()  # every month
            yearsFmt = mdates.DateFormatter('%Y')

            ax.xaxis.set_major_locator(years)
            ax.xaxis.set_major_formatter(yearsFmt)
            ax.xaxis.set_minor_locator(months)

            plt.rc('xtick', labelsize=12)

            # ax.set_xticks(xdate)
            # ax.set_xticklabels(x, rotation=50, fontsize=10)
            # ax.tick_params(axis='x', which='major', pad=xticklabel_pad)

            # ax.xaxis.set_major_formatter(dateformat)
            # ax.set_xlim(datetime.date(settings.plot['x_min'], 1, 1),datetime.date(settings.plot['x_max'], 12, 31))

        if show_grid:
            ax.grid(
                b=True,
                which='minor',
                color='black',
                alpha=0.75,
                linestyle=':')

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
            plt.savefig(figname, dpi=500)


def run_dual_plot(
        main_gdf,
        gdf2,
        figsize=(
            12,
            6),
    y_val_alpha=1,
    scatter_alpha=1,
    error_alpha=0.2,
    y_label="Brightness",
    x_label="Date",
    title_label="Brightness over time - ID: ",
    figname='',
    custom_x_axis=True,
    show_grid=True,
    show_legend=True,
    min_count=0.5,
    ymin=0,
        ymax=5000):
    print("Plotting...")
    for item in main_gdf['ID'].unique() & gdf2['ID'].unique():
        plt.style.use('fivethirtyeight')
        fig, ax = plt.subplots(figsize=figsize)
        gdf3 = main_gdf[(main_gdf.ID == item)]
        gdf4 = gdf2[(gdf2.ID == item)]
        title = title_label + str(item)
        gdf3 = gdf3.sort_values(['date'])
        gdf4 = gdf4.sort_values(['date'])
        x = gdf3['date']
        xdate = x.astype('O')
        xdate = mdates.date2num(xdate)
        y = gdf3['median']
        y2 = gdf4['median']
        #print(y, y2)
        if 'observations' in gdf3.columns:
            count = gdf3['observations']
        err_plus = gdf3['percentile_75']
        err_minus = gdf3['percentile_25']
        if 'observations' in gdf4.columns:
            count2 = gdf4['observations']
        err_plus2 = gdf4['percentile_75']
        err_minus2 = gdf4['percentile_25']
        # Set the min_count value as a value from 0 to 1 (0 to 100%)
        ax.set_ylim([ymin, ymax])

        # This will filter out observations where over n% of a polygon is
        # masked out
        if min_count > 0:
            z = gdf3['count']
            zmax = gdf3['count'].max()
            z = z / zmax
            #xdate = xdate[z >= min_count]
            y = y[z >= min_count]
            if 'observations' in gdf3.columns:
                count = count[z >= min_count]
            err_plus = err_plus[z >= min_count]
            err_minus = err_minus[z >= min_count]

            z2 = gdf4['count']
            zmax2 = gdf4['count'].max()
            z2 = z2 / zmax2
            xdate = xdate[z >= min_count]
            y2 = y2[z2 >= min_count]
            if 'observations' in gdf4.columns:
                count2 = count2[z2 >= min_count]
            err_plus2 = err_plus2[z2 >= min_count]
            err_minus2 = err_minus2[z2 >= min_count]

        # plot running mean regression line
        # RM=(y.rolling(window=6, center=True, min_periods=2).median())
        # ax.plot(xdate, RM, '-',label="Moving Median", alpha=y_val_alpha)

        # Gaussian smoothed plot
        b = gaussian(6, 2)
        ga = filters.convolve1d(y, b / b.sum(), mode="reflect")
        ga = interpolate_gaps(ga, limit=3)
        ax.plot(
            xdate,
            ga,
            '-',
            label="Gaussian Smoothed",
            alpha=1,
            color='#d7191c')

        ga2 = filters.convolve1d(y2, b / b.sum(), mode="reflect")
        ga2 = interpolate_gaps(ga2, limit=3)
        ax.plot(
            xdate,
            ga2,
            '-',
            label="Gaussian Smoothed_2",
            alpha=1,
            color='#2b83ba')

        # scatter points-median top, mean bottom
        ax.scatter(
            xdate,
            y,
            label="Median",
            s=50,
            color='#d7191c',
            alpha=scatter_alpha,
            marker=".")
        ax.scatter(
            xdate,
            y2,
            label="Median_2",
            s=50,
            color='#2b83ba',
            alpha=scatter_alpha,
            marker=".")

        # plot regression line, if desired
        idx = np.isfinite(xdate) & np.isfinite(y)
        p2 = np.poly1d(np.polyfit(xdate[idx], y[idx], 1))
        ax.plot(
            xdate,
            p2(xdate),
            '-',
            label="Linear Regression",
            color='#E84448',
            alpha=y_val_alpha)

        idx = np.isfinite(xdate) & np.isfinite(y2)
        p3 = np.poly1d(np.polyfit(xdate[idx], y2[idx], 1))
        ax.plot(
            xdate,
            p3(xdate),
            '-',
            label="Linear Regression_2",
            color='#4B97C8',
            alpha=y_val_alpha)

        # if desired, plot error band
        # plt.fill_between(xdate, err_plus, err_minus, alpha=error_alpha, color='black', label="25th to 75th %")
        # plt.fill_between(xdate, err_plus2, err_minus2, alpha=error_alpha, color='black', label="25th to 75th %")

        ax.set_ylabel(y_label)
        ax.set_xlabel(x_label)

        ax.yaxis.set_tick_params(labelsize=12)
        if custom_x_axis:
            years = mdates.YearLocator()   # every year
            months = mdates.MonthLocator()  # every month
            yearsFmt = mdates.DateFormatter('%Y')

            ax.xaxis.set_major_locator(years)
            ax.xaxis.set_major_formatter(yearsFmt)
            ax.xaxis.set_minor_locator(months)

            plt.rc('xtick', labelsize=12)

            # ax.set_xticks(xdate)
            #ax.set_xticklabels(x, rotation=50, fontsize=10)
            #ax.tick_params(axis='x', which='major', pad=xticklabel_pad)

            # ax.xaxis.set_major_formatter(dateformat)
            #ax.set_xlim(datetime.date(settings.plot['x_min'], 1, 1),datetime.date(settings.plot['x_max'], 12, 31))

        if show_grid:
            ax.grid(
                b=True,
                which='minor',
                color='black',
                alpha=0.75,
                linestyle=':')

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
            plt.savefig(figname, dpi=500)


def run_tri_plot(
        main_gdf,
        gdf2,
        gdfx,
        figsize=(
            12,
            6),
    y_val_alpha=1,
    scatter_alpha=1,
    error_alpha=0.2,
    y_label="Brightness",
    x_label="Date",
    title_label="Brightness over time - ID: ",
    figname='',
    custom_x_axis=True,
    show_grid=True,
    show_legend=True,
    min_count=0.5,
    ymin=0,
        ymax=5000):
    print("Plotting...")
    for item in main_gdf['ID'].unique() & gdf2['ID'].unique():
        plt.style.use('fivethirtyeight')
        fig, ax = plt.subplots(figsize=figsize)
        gdf3 = main_gdf[(main_gdf.ID == item)]
        gdf4 = gdf2[(gdf2.ID == item)]
        gdf5 = gdfx[(gdfx.ID == item)]
        title = title_label + str(item)
        gdf3 = gdf3.sort_values(['date'])
        gdf4 = gdf4.sort_values(['date'])
        gdf5 = gdf5.sort_values(['date'])
        x = gdf3['date']
        xdate = x.astype('O')
        xdate = mdates.date2num(xdate)
        y = gdf3['median']
        y2 = gdf4['median']
        y3 = gdf5['median']
        #print(y, y2)
        if 'observations' in gdf3.columns:
            count = gdf3['observations']
        err_plus = gdf3['percentile_75']
        err_minus = gdf3['percentile_25']
        if 'observations' in gdf4.columns:
            count2 = gdf4['observations']
        err_plus2 = gdf4['percentile_75']
        err_minus2 = gdf4['percentile_25']

        if 'observations' in gdf5.columns:
            count3 = gdf5['observations']
        err_plus3 = gdf5['percentile_75']
        err_minus3 = gdf5['percentile_25']
        # Set the min_count value as a value from 0 to 1 (0 to 100%)
        ax.set_ylim([ymin, ymax])

        # This will filter out observations where over n% of a polygon is
        # masked out
        if min_count > 0:
            z = gdf3['count']
            zmax = gdf3['count'].max()
            z = z / zmax
            #xdate = xdate[z >= min_count]
            y = y[z >= min_count]
            if 'observations' in gdf3.columns:
                count = count[z >= min_count]
            err_plus = err_plus[z >= min_count]
            err_minus = err_minus[z >= min_count]

            z2 = gdf4['count']
            zmax2 = gdf4['count'].max()
            z2 = z2 / zmax2
            #xdate = xdate[z >= min_count]
            y2 = y2[z2 >= min_count]

            if 'observations' in gdf4.columns:
                count2 = count2[z2 >= min_count]
            err_plus2 = err_plus2[z2 >= min_count]
            err_minus2 = err_minus2[z2 >= min_count]

            z3 = gdf5['count']
            zmax3 = gdf5['count'].max()
            z3 = z3 / zmax3
            xdate = xdate[z >= min_count]
            y3 = y3[z3 >= min_count]

            if 'observations' in gdf5.columns:
                count3 = count3[z3 >= min_count]
            err_plus3 = err_plus3[z3 >= min_count]
            err_minus3 = err_minus3[z3 >= min_count]

        # plot running mean regression line
        # RM=(y.rolling(window=6, center=True, min_periods=2).median())
        # ax.plot(xdate, RM, '-',label="Moving Median", alpha=y_val_alpha)

        # Gaussian smoothed plot
        b = gaussian(6, 2)
        ga = filters.convolve1d(y, b / b.sum(), mode="reflect")
        ga = interpolate_gaps(ga, limit=3)
        ax.plot(
            xdate,
            ga,
            '-',
            label="Gaussian SWIR2",
            alpha=1,
            color='#d7191c')

        ga2 = filters.convolve1d(y2, b / b.sum(), mode="reflect")
        ga2 = interpolate_gaps(ga2, limit=3)
        ax.plot(
            xdate,
            ga2,
            '-',
            label="Gaussian Green",
            alpha=1,
            color='#44C73D')

        ga3 = filters.convolve1d(y3, b / b.sum(), mode="reflect")
        ga3 = interpolate_gaps(ga3, limit=3)
        ax.plot(
            xdate,
            ga3,
            '-',
            label="Gaussian NIR",
            alpha=1,
            color='#2b83ba')

        # scatter points-median top, mean bottom
        ax.scatter(
            xdate,
            y,
            label="Median SWIR2",
            s=50,
            color='#d7191c',
            alpha=scatter_alpha,
            marker=".")
        ax.scatter(
            xdate,
            y2,
            label="Median Green",
            s=50,
            color='#44C73D',
            alpha=scatter_alpha,
            marker=".")
        ax.scatter(
            xdate,
            y3,
            label="Median NIR",
            s=50,
            color='#2b83ba',
            alpha=scatter_alpha,
            marker=".")

        # plot regression line, if desired
        idx = np.isfinite(xdate) & np.isfinite(y)
        p2 = np.poly1d(np.polyfit(xdate[idx], y[idx], 1))
        ax.plot(
            xdate,
            p2(xdate),
            '-',
            label="Linear SWIR2",
            color='#E84448',
            alpha=y_val_alpha)

        idx = np.isfinite(xdate) & np.isfinite(y2)
        p3 = np.poly1d(np.polyfit(xdate[idx], y2[idx], 1))
        ax.plot(
            xdate,
            p3(xdate),
            '-',
            label="Linear Green",
            color='#65D75F',
            alpha=y_val_alpha)

        idx = np.isfinite(xdate) & np.isfinite(y3)
        p4 = np.poly1d(np.polyfit(xdate[idx], y3[idx], 1))
        ax.plot(
            xdate,
            p4(xdate),
            '-',
            label="Linear NIR",
            color='#4B97C8',
            alpha=y_val_alpha)

        # if desired, plot error band
        #plt.fill_between(xdate, err_plus, err_minus, alpha=error_alpha, color='black', label="25th to 75th %")
        #plt.fill_between(xdate, err_plus2, err_minus2, alpha=error_alpha, color='black', label="25th to 75th %")

        ax.set_ylabel(y_label)
        ax.set_xlabel(x_label)

        ax.yaxis.set_tick_params(labelsize=12)
        if custom_x_axis:
            years = mdates.YearLocator()   # every year
            months = mdates.MonthLocator()  # every month
            yearsFmt = mdates.DateFormatter('%Y')

            ax.xaxis.set_major_locator(years)
            ax.xaxis.set_major_formatter(yearsFmt)
            ax.xaxis.set_minor_locator(months)

            plt.rc('xtick', labelsize=12)

            # ax.set_xticks(xdate)
            #ax.set_xticklabels(x, rotation=50, fontsize=10)
            #ax.tick_params(axis='x', which='major', pad=xticklabel_pad)

            # ax.xaxis.set_major_formatter(dateformat)
            #ax.set_xlim(datetime.date(settings.plot['x_min'], 1, 1),datetime.date(settings.plot['x_max'], 12, 31))

        if show_grid:
            ax.grid(
                b=True,
                which='minor',
                color='black',
                alpha=0.75,
                linestyle=':')

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
            plt.savefig(figname, dpi=500)


def LS_CSV_It(
        input_dir,
        TSdata="L*.tif",
        Mask="",
        DateLoc="10:18",
        Band="BLUE"):
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


def get_extent(raster):
    raster = gdal.Open(raster)
    rastergeo = raster.GetGeoTransform()
    minx = rastergeo[0]
    maxy = rastergeo[3]
    maxx = minx + rastergeo[1] * raster.RasterXSize
    miny = maxy + rastergeo[5] * raster.RasterYSize
    rasterExtent = [minx, maxy, maxx, miny]
    return rasterExtent


# Run plotting from CSV output ONLY
def gen_plots(input_csv):
    df = pd.read_csv(input_csv)
    df = df.sort_values(['date'])
    geometry = df['geometry'].map(shapely.wkt.loads)
    crs = {'init': 'epsg:2263'}
    gdf = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
    gdf['date'] = pd.to_datetime(gdf['date'], infer_datetime_format=True)
    #run_plot(gdf, y_label="NDVI", title_label= "NDVI over time - ID: ")
    run_plot(gdf)


def gen_dual_plot(
        input_csv,
        input_csv2,
        title_label="Spectral Response Over Time - ID: "):
    CSVs = [input_csv, input_csv2]
    gdfs = ["gdf_1", "gdf_2"]
    count = 0
    for csv in CSVs:
        df = pd.read_csv(csv)
        df = df.sort_values(['date'])
        geometry = df['geometry'].map(shapely.wkt.loads)
        crs = {'init': 'epsg:2263'}
        gdfs[count] = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
        gdfs[count]['date'] = pd.to_datetime(
            gdfs[count]['date'], infer_datetime_format=True)
        count += 1
    run_dual_plot(
        gdfs[0],
        gdfs[1],
        title_label=title_label,
        show_grid=False,
        ymax=3000,
        y_label="Surface Reflectance x 10000")


def gen_tri_plot(
        input_csv,
        input_csv2,
        input_csv3,
        title_label="Spectral Response Over Time - ID: "):
    CSVs = [input_csv, input_csv2, input_csv3]
    gdfs = ["gdf_1", "gdf_2", "gdf_3"]
    count = 0
    for csv in CSVs:
        df = pd.read_csv(csv)
        df = df.sort_values(['date'])
        geometry = df['geometry'].map(shapely.wkt.loads)
        crs = {'init': 'epsg:2263'}
        gdfs[count] = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
        gdfs[count]['date'] = pd.to_datetime(
            gdfs[count]['date'], infer_datetime_format=True)
        count += 1

    run_tri_plot(
        gdfs[0],
        gdfs[1],
        gdfs[2],
        title_label=title_label,
        show_grid=False,
        ymax=5000,
        y_label="Surface Reflectance x 10000")

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

    Process_imagery(args.input_csv, args.zonalpoly, args.NoDataValue, args.mask_value, maskit=args.maskit, Path_out=args.Path_out)
    print("Run Plot_Results.ipynb to generate visualizations from output CSV")


###############################################################################

if __name__ == "__main__":
    main()
