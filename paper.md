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

We have developed a tool that we called Comet Time Series (``CometTS``) that enables workflows for the analysis and visualization of a time series of satellite imagery for the data science and geographic communities. The tool aims to enable population estimation research, land use change detection, or natural disaster monitoring using a range of data types.  ``CometTS`` calculates relevant statistical quantities (e.g., measures of central tendency and variation) and provides a visualization of their changes over time (Figure 1 and Figure 2). 

Our package builds upon previously introduced tools like ``TSTools``[@Holden:2017], ``TIMESAT``[@Jonsson_Eklundh:2004], and ``Satellite Image Time Series Analysis (SITS)``[@e-sensing/sits:2018] to provide a partially automated approach for analyzing a time series of satellite images.  ``CometTS`` adds new functionality to the overhead time series analysis and visualization domain in a few ways:  Specifically, ``CometTS`` output includes user-specified statistics such as mean, median, and quartiles, across arbitrarily sized regions of interest (ROI) and includes masking functionality to remove clouds and snow from the area of interest. Furthermore, the option for anomaly detection is also included, and CometTS leverages an Auto-Regressive Integrated Moving Average (ARIMA) analysis to quantify trends and test if observations are significantly different from observed historical trends.  Finally, ``CometTS`` is coded in Python, and removes the GIS requirement that is typical for such analyses.

![Figure 1](https://raw.githubusercontent.com/CosmiQ/CometTS/master/ExamplePlots/Workflow.png)
**Fig. 1:** A four step process to analyze and visualize trends in a time series of overhead imagery.


![Figure 2](https://raw.githubusercontent.com/CosmiQ/CometTS/master/ExamplePlots/Niamey.png)
**Fig. 2:** An example output from CometTS showing variations in nighttime brighness in Niamey, Niger.  These seasonal trends can be correlated to season migration patterns in the city.


Previously ``CometTS`` has been employed to monitor electrical and infrastructure recovery in Puerto Rico following Hurricane Maria[@Shermeyer_PR:2018].  For this study, the tool was used to extract the change in average nighttime brightness for all census tracts within Puerto Rico and to infer the number of persons without power over time. Using the ARIMA analysis functionality, an historical trend line was calucluated to  determine where brightness was expected to be if the hurricane had not hit. The difference between the actual observed brightness and the forecast brightness was then used to quantify electrical and infrastructure deficiencies and recovery over time. Multiple opportunities exist to employ CometTS for impactful work in the future. There are a number of useful primary applications including: (1) population dynamics; (2) land-use change; and (3) investigating seasonal or climatic conditions such as drought. These primary applications generate outputs that have been demonstrated as useful inputs to gain better understanding of changes in other topics such as climate, poverty, food security, biodiversity, political conflict, and civil instability. 

The source code for CometTS has been archived to Zenodo with the linked DOI: [@Shermeyer:2018]

![Figure 3](https://raw.githubusercontent.com/CosmiQ/CometTS/master/ExamplePlots/Puerto_Rico_ARIMA.png)

**Fig. 3:** A visualization of mean and one standard deviation of brightness over time in Census Tract 9509, in Yabucoa Municipio, Puerto Rico. The linear regression forecast and seasonal adjusted forecast are plotted in teal and orange respectively. Differences of observed vs. expected brightness can be visualized and quantified.


# Acknowledgements

We acknowledge contributions from Dylan George, Dave Lindenbaum, Ryan Lewis, Adam Van Etten, Nick Weir, Zig Hampel Arias, Rob Sare, & Jack McNelis.

# References

