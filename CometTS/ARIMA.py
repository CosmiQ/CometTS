import matplotlib.dates as mdates
from tqdm import tqdm as tqdm
import datetime
import numpy as np
import pandas as pd
import seaborn as sns
import argparse
import os
sns.set(color_codes=True)
# Functions for a seasonal auto-regressive integrated moving average analysis
# using CometTS on a time series of satellite imagery.


def timeseries_trend(gdf3, CMA_Val=3, CutoffDate="2017/08/31", Uncertainty=2):
    """Internal function for ARIMA analysis

    Arguments
    ---------
    gdf3 : `class:geopandas.geodataframe`
        A geodataframe, converted from the specific path to the csv that was
        output from running CometTS with all detailed statistics for
        each polygon of interest.
    CMA_Val : int
        How large of a centered moving average value to calculate when running
        ARIMA across the entire dataset.  Should be an odd number. Defaults to 3.
    CutoffDate : str
        A string date value. Default is 2017/08/15. Format YYYY/MM/DD. Split
        data into a before and after event, i.e. a Hurricane.
        If no event simply set as last date in dataset, or a middle date.
        Ensure you have at least 14 observations in your of time series
        to pull out an historical trend"
    Uncertainty : int
        Default is 2. Multiplier for the mean absolute error from the ARIMA
        forecast, for shorter time series a greater uncertainty value is
        likely required so anomalies are not overly flagged.  For long time
        series set equal to 1. User discretion advised.

    Returns
    -------
    gdf3 : `class:geopandas.geodataframe`
        A geodataframe, converted from the specific path to the csv that was
        output from running CometTS with all detailed statistics for
        each polygon of interest with appended ARIMA analysis that can be saved
        and used for plotting.
    """
    x = gdf3['date']
    # Split data into a before and after event, i.e. a Hurricane.
    # If no event simply set as last date in dataset, or a middle date.
    CutoffDate = datetime.datetime.strptime(CutoffDate, '%Y/%m/%d').date()
    # Do some date conversion
    xcutoff = mdates.date2num(CutoffDate)
    xdate = x.astype('O')
    xdate = mdates.datestr2num(xdate)
    gdf3['xdate'] = xdate
    # Presently geared toward monthly trends only, could split this into days.
    gdf3['Month'] = pd.DatetimeIndex(gdf3['date']).month
    # Create a new GDF for before the event
    gdf4 = gdf3.loc[gdf3['xdate'] <= xcutoff]
    gdf3 = gdf3.sort_values(['date'])
    gdf4 = gdf4.sort_values(['date'])
    # print(gdf4)
    # print(gdf3)
    # Start ARIMA
    y = gdf4['mean']
    gdf4['CMA'] = y.rolling(window=CMA_Val, center=True).mean()
    gdf4['Div'] = gdf4['mean'] / gdf4['CMA']
    # print(gdf4['Div'])
    f = gdf4.groupby(['Month'])['Div'].mean()
    f = pd.DataFrame({'Month': f.index, 'SeasonalTrend': f.values})
    gdf4 = gdf4.merge(f, on='Month')
    gdf3 = gdf3.merge(f, on='Month')
    # Seasonal ARIMA
    gdf4['Deseasonalized'] = gdf4['mean'] / gdf4['SeasonalTrend']
    y = gdf4['Deseasonalized']
    z = gdf4['xdate']
    gdf3 = gdf3.sort_values(['date'])
    idx = np.isfinite(z) & np.isfinite(y)
    if not any(idx) is False:
        # Apply ARIMA to the oringial GDF
        p2 = np.poly1d(np.polyfit(z[idx], y[idx], 1))
        gdf3['Trend'] = p2(gdf3['xdate'])
        gdf3['SeasonalForecast'] = gdf3['SeasonalTrend'] * gdf3['Trend']
        gdf4['Trend'] = p2(gdf4['xdate'])
        gdf4['SeasonalForecast'] = gdf4['SeasonalTrend'] * gdf4['Trend']
        Error = Uncertainty * np.nanmean(abs(gdf4['SeasonalForecast'] - gdf4['mean']))
        gdf3['SeasonalError_Pos'] = gdf3['SeasonalForecast'] + Error
        gdf3['SeasonalError_Neg'] = gdf3['SeasonalForecast'] - Error
        Neg_Anom = gdf3['mean'] < gdf3['SeasonalError_Neg']
        Pos_Anom = gdf3['mean'] > gdf3['SeasonalError_Pos']
        gdf5 = gdf3.where(Neg_Anom | Pos_Anom)
        gdf3['Anomaly'] = gdf5['mean']
        # print(gdf3['Anomaly'])

        # print(gdf3['Anomaly'])
        return gdf3
    else:
        return gdf3


def run_arima(CometTSOutputCSV="/San_Juan_FullStats.csv", outname="/FullStats_timeseries_trend.csv", CMA_Val=3, CutoffDate="2017/12/31", Uncertainty=2):
    """Run an autoregressive integrated moving average analysis. And flag anomalies
    in the time series.

    Arguments
    ---------
    CometTSOutputCSV : str
        The specific path to the csv that was output from running CometTS with
        all detailed statistics for each polygon of interest.
    outname : str
        The output name and path for a csv documenting your ARIMA analysis.
    CMA_Val : int
        How large of a centered moving average value to calculate when running
        ARIMA across the entire dataset.  Should be an odd number. Defaults to 3.
    CutoffDate : str
        A string date value. Default is 2017/08/15. Format YYYY/MM/DD. Split
        data into a before and after event, i.e. a Hurricane.
        If no event simply set as last date in dataset, or a middle date.
        Ensure you have at least 14 observations in your of time series
        to pull out an historical trend"
    Uncertainty : int
        Default is 2. Multiplier for the mean absolute error from the ARIMA
        forecast, for shorter time series a greater uncertainty value is
        likely required so anomalies are not overly flagged.  For long time
        series set equal to 1. User discretion advised.

    Returns
    -------
    All statistics are output in csv format to the outname.
    """

    print("Calculating...")
    C = 0
    main_gdf = pd.read_csv(CometTSOutputCSV)
    for item in tqdm(main_gdf['ID'].unique()):
        C += 1
        gdf3 = main_gdf[(main_gdf.ID == item)]
        gdf3 = gdf3.sort_values(['date'])
        gdf3 = timeseries_trend(gdf3, CMA_Val=CMA_Val, CutoffDate=CutoffDate, Uncertainty=Uncertainty)
        gdf3 = gdf3.sort_values(['date'])
        if 'SeasonalForecast' in gdf3.columns:
            if C == 1:
                gdf_holder = gdf3
            else:
                gdf_holder = gdf_holder.append(gdf3)

    gdf_holder.to_csv(outname)

###############################################################################


def main():

    # Construct argument parser
    parser = argparse.ArgumentParser()
    directory = os.path.join(os.path.abspath(os.path.dirname(__file__)), "CometTS/VIIRS_Sample")
    List = os.path.join(directory, 'San_Juan_FullStats.csv')
    ARIMA = os.path.join(directory, 'San_Juan_ARIMA_Output.csv')

    # general settings
    parser.add_argument('--CometTSOutputCSV', type=str, default=List,
                        help="Enter CSV output from CometTS script, as input for ARIMA, default: " + List)
    parser.add_argument('--ARIMA_CSV', type=str, default=ARIMA,
                        help="Enter ARIMA CSV output name: " + ARIMA)
    parser.add_argument('--CMA_Val', type=int, default=3,
                        help="Default is 3. Centered Moving Average Value for ARIMA, set to an odd number >=3")
    parser.add_argument('--CutoffDate', type=str, default="2017/08/15",
                        help="Default is 2017/08/15. Format YYYY/MM/DD. Split data into a before and after event, i.e. a Hurricane. If no event simply set as last date in dataset, or a middle date. Ensure you have at least 14 observations of data to pull out an historical trend")
    parser.add_argument('--Uncertainty', type=int, default=2,
                        help="Default is 2. Multiplier for the mean absolute error from the ARIMA forecast, for shorter time series a greater uncertainty value is likely required so anomalies are not overly flagged.  For long time series set equal to 1. User discretion advised.")
    args = parser.parse_args()

    run_arima(args.CometTSOutputCSV, args.ARIMA_CSV, args.CMA_Val, args.CutoffDate, args.Uncertainty)
    print("Run ARIMA_Plotting.ipynb to generate visualizations from output CSV")


###############################################################################

if __name__ == "__main__":
    main()
