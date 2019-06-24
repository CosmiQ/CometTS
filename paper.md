---
title: 'Comet Time Series Visualizer: CometTS'
tags:
  - Python
  - Jupyter Notebook
  - Visualizer
  - Remote Sensing
  - Time Series Analysis
authors:
  - name: Jacob Shermeyer
    orcid: 0000-0002-8143-2790
    affiliation: "1"
affiliations:
 - name: CosmiQ Works, In-Q-Tel
   index: 1
date: 24 June 2019
bibliography: paper.bib
---

# Summary

We have developed a tool that we called Comet Time Series (``CometTS``) that enables workflows for the analysis and visualization of a time series of satellite imagery for the data science and geographic communities. The tool aims to enable population estimation research, land use change detection, or natural disaster monitoring using a range of data types.  ``CometTS`` calculates relevant statistical quantities (e.g., measures of central tendency and variation) and provides a visualization of their changes over time (Figure 1 and Figure 2). ``CometTS`` builds upon previously introduced tools like TSTools[@Holden:2017], TIMESAT[@Jonsson_Eklundh:2004], and SITS[@e-sensing/sits:2018] to provide a partially automated approach for analyzing a time series of satellite images.  ``CometTS`` adds new functionality to this domain, including analysis over arbitrarily sized regions of interest (ROI) and anomaly detection across a time series of imagery. Additionally, ``CometTS`` is coded in Python, and removes the GIS requirement that is typical for such analyses.

![Figure 1](https://raw.githubusercontent.com/CosmiQ/CometTS/master/ExamplePlots/Workflow.png)
**Fig. 1:** A four step process to analyze and visualize trends in a time series of overhead imagery.


![Figure 2](https://raw.githubusercontent.com/CosmiQ/CometTS/master/ExamplePlots/Niamey.png)
**Fig. 2:** An example output from CometTS showing variations in nighttime brighness in Niamey, Niger.  These seasonal trends can be correlated to season migration patterns in the city.

The tool ingests two key components: (1) time series of overhead imagery and (2) the ROI to designate the area of interest. Beyond what is possible with a single satellite image, time series imagery enables the investigation of patterns and sequences of the spectral responses and how they change over time. ``CometTS`` output includes user-specified statistics such as mean, median, and quartiles, and the package offers masking functionality to remove clouds and snow from the area of interest. The option for anomaly detection is also included, and CometTS leverages an Auto-Regressive Integrated Moving Average (ARIMA) analysis to quantify trends and test if observations are significantly different from observed historical trends.

Previously, ``CometTS`` has been employed to monitor electrical and infrastructure recovery in Puerto Rico following Hurricane Maria[@Shermeyer_PR:2018].  For this study, the tool was used to extract the change in average nighttime brightness for all census tracts within Puerto Rico and to infer the number of persons without power over time. Using the ARIMA analysis feature, an historical trend line was calucluated to  determine where brightness was expected to be if the hurricane had not hit. The difference between the actual observed brightness and the forecast brightness was then used to quantify electrical and infrastructure deficiencies and recovery over time.

![Figure 3](https://raw.githubusercontent.com/CosmiQ/CometTS/master/ExamplePlots/Puerto_Rico_ARIMA.png)

**Fig. 3:** A visualization of mean and one standard deviation of brightness over time in Census Tract 9509, in Yabucoa Municipio. The linear regression forecast and seasonal adjusted forecast are plotted in teal and orange respectively.


# Acknowledgements

We acknowledge contributions from Dylan George, Dave Lindenbaum, Ryan Lewis,  Adam Van Etten, Nick Weir, Zig Hampel Arias, 

# References

