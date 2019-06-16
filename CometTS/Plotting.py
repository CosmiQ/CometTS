import numpy as np
import pandas as pd
import geopandas as gpd
import shapely.wkt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.signal import gaussian
from scipy.ndimage import filters

"""This file contains multiple plotting functions.  Specific docstrings not
provided but these are simple wrappers around matplotlib.  Simple adjustments to
what you pass to each function should enable easy modification of output plots.
"""


def interpolate_gaps(values, limit=None):
    """When there are gaps in the data they sometimes cannot be plotted properly.
    This funciton interpolates these gaps using a linear interpolation to enable
    plotting.

    Arguments
    ---------
    values : a :class:`numpy.array`
        The data that we want to remove the gaps within.

    limit : int
        The maximum amount of times to interpolate. i.e. if there is a large
        gap in the data due to a lack of obserbations, how much should we
         interpolate?  Defaults to None.

    Returns
    -------
    filled : a :class:`numpy.array`
        An array where any gaps in the data are removed via linear interpolation.
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

        # This will filter out observations where over n% of a polygon is masked out
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


def run_plot_arima(
        ARIMA_GDF,
        figsize=(12, 6),
        y_val_alpha=1,
        scatter_alpha=1,
        error_alpha=0.2,
        y_label="Brightness",
        x_label="Date",
        title_label="ARIMA_Trend",
        figname='',
        custom_x_axis=True,
        show_grid=True,
        show_legend=True,
        min_count=0.5,
        ymin=0,
        ymax=5000):
    print("Plotting...")
    C = 0
    # ARIMA GDF is the output GDF from timeseries_trend function
    for item in ARIMA_GDF['ID'].unique():
        C += 1
        plt.style.use('fivethirtyeight')
        fig, ax = plt.subplots(figsize=figsize)
        gdf3 = ARIMA_GDF[(ARIMA_GDF.ID == item)]
        title = title_label
        gdf3 = gdf3.sort_values(['date'])
        x = gdf3['date']
        xdate = x.astype('O')
        xdate = mdates.date2num(xdate)
        y = gdf3['mean']
        anomaly = gdf3['Anomaly']
        if 'SeasonalForecast' in gdf3.columns:
            if C == 1:
                gdf_holder = gdf3
            else:
                gdf_holder = gdf_holder.append(gdf3)
            T = gdf3['SeasonalForecast']
            if 'observations' in gdf3.columns:
                count = gdf3['observations']
            err_plus = gdf3['SeasonalError_Pos']
            err_minus = gdf3['SeasonalError_Neg']
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

            if len(xdate) == len(gdf3['Trend']):
                ax.plot(
                    xdate,
                    gdf3['Trend'],
                    '-',
                    label="Linear Forecast",
                    color='#00C5B0',
                    alpha=y_val_alpha)
                # Seasonal Forecast
                T = interpolate_gaps(T, limit=3)
                ax.plot(
                    xdate,
                    T,
                    '-',
                    label="Seasonal Forecast",
                    alpha=1,
                    color='#FF8700')

                # scatter points-median top, mean bottom
                ax.scatter(
                    xdate,
                    y,
                    label="Mean",
                    s=50,
                    color='black',
                    alpha=scatter_alpha)
                ax.scatter(
                    xdate,
                    anomaly,
                    label="Anomalies",
                    s=50,
                    color='red',
                    alpha=scatter_alpha)
                plt.fill_between(
                    xdate,
                    err_plus,
                    err_minus,
                    alpha=error_alpha,
                    color='black',
                    label="Forecast MAE")

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
        if 'observations' in gdf3.columns:
            count = gdf3['observations']
        err_plus = gdf3['percentile_75']
        err_minus = gdf3['percentile_25']
        if 'observations' in gdf4.columns:
            count2 = gdf4['observations']
        err_plus2 = gdf4['percentile_75']
        err_minus2 = gdf4['percentile_25']
        ax.set_ylim([ymin, ymax])

        if min_count > 0:
            z = gdf3['count']
            zmax = gdf3['count'].max()
            z = z / zmax
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
        ax.set_ylim([ymin, ymax])

        if min_count > 0:
            z = gdf3['count']
            zmax = gdf3['count'].max()
            z = z / zmax
            y = y[z >= min_count]
            if 'observations' in gdf3.columns:
                count = count[z >= min_count]
            err_plus = err_plus[z >= min_count]
            err_minus = err_minus[z >= min_count]

            z2 = gdf4['count']
            zmax2 = gdf4['count'].max()
            z2 = z2 / zmax2
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


def gen_plots(input_csv):
    # Run plotting from CSV output ONLY
    df = pd.read_csv(input_csv)
    df = df.sort_values(['date'])
    geometry = df['geometry'].map(shapely.wkt.loads)
    crs = {'init': 'epsg:2263'}
    gdf = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
    gdf['date'] = pd.to_datetime(gdf['date'], infer_datetime_format=True)
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
