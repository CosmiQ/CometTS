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
date: 31 July 2018
bibliography: paper.bib
---

# Summary

We have developed a tool that we called Comet Time Series (``CometTS``) that facilitates analysis and visualization of a time series of satellite imagery. The tool aims to enable population estimation research, land use change detection, or natural disaster monitoring using a range of data types. ``CometTS`` provides a partially automated approach for analyzing a time series of satellite images in any user defined polygon identifying a an arbitrarily sized region of interest (ROI). The tool calculates relevant statistical quantities (e.g., measures of central tendency and variation) and provides a visualization of their changes over time (Figure 1 and Figure 2). We believe this work is novel, as presently we are not aware of any such open-source tools to evaluate and leverage a time series of satellite or potentially airborne imagery from an ROI. Furthermore, this tool makes time series satellite imagery more accessible to the data science community and removes a Geographic Information Systems (GIS) tool as a requirement for working with these data. The tool requires only a web browser, Python, and dependent packages to function. Other time series tools like TSTools[@Holden:2017] are powerful but require a GIS interface and are limited to an analysis of individual pixels rather than larger areas of interest.

![Figure 1](https://raw.githubusercontent.com/CosmiQ/CometTS/master/ExamplePlots/Workflow.png)
**Fig. 1:** A four step process to analyze and visualize trends in a time series of overhead imagery.


![Figure 2](https://raw.githubusercontent.com/CosmiQ/CometTS/master/ExamplePlots/Niamey.png)
**Fig. 2:** An example output from CometTS showing variations in nighttime brighness in Niamey, Niger.  These seasonal trends can be correlated to season migration patterns in the city.


The tool ingests two key components: (1) time series of overhead imagery and (2) the ROI to designate the area of interest. Beyond what is possible with a single satellite image, time series imagery enables the investigation of patterns and sequences of the spectral responses and how they change over time.

``CometTS`` produces a tabular and visual depiction of relevant statistics of spectral responses for every pixel contained within the ROI that delimits the area of interest. This operation is repeated for every image within the time series. The user can determine the statistic(s) most relevant for their analytic needs. The output is customizable by the user to produce any type or range of statistics needed. For our assessment and demonstration, we choose standard test statistics to illustrate trends and uncertainty, including median, lower quartile (25th percentile), upper quartile (75th percentile), linear regression, and a Gaussian signal filter.  Users also have the option to supply “mask” images that are sometimes distributed with satellite imagery or that can be created. These masks can be used to remove areas that contain cloud cover, cloud shadow, snow, or other anomalies that can interfere with analysis of data (Figure 3).  The source code for ``CometTS`` has been archived to Zenodo with the linked DOI: [@Shermeyer:2018]

![Figure 3](https://raw.githubusercontent.com/CosmiQ/CometTS/master/ExamplePlots/CloudMask.png)

**Fig. 3:** An example of masked clouds.  CometTS can handle masked data to ignore anomalies like cloud cover and cloud shadows.


# Acknowledgements

We acknowledge contributions from Dylan George, Dave Lindenbaum, Ryan Lewis, and Adam Van Etten.

# References

