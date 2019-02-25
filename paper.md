---
title: 'Comet Time Series (CometTS) Visualizer'
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

We have developed a tool that we call Comet Time Series (CometTS) that facilitates analysis and visualization of a time series of satellite imagery in order to enable population estimation research, land use change detection, or natural disaster monitoring using a range of data types. ``CometTS`` provides a partially automated approach for analyzing a time series of satellite imagery in any user defined area of interest. The tool calculates relevant statistical quantities (e.g., measures of central tendency and variation), and visualizes their changes over time (Figure 1 and Figure 2). We believe this work is novel, as presently we are not aware of any such open-source tools to evaluate and leverage a time series of satellite or potentially airborne imagery from user drawn polygons. Furthermore, this tool makes time series satellite imagery more accessible to the data science community and removes a GIS tool as a requirement for working with these data. The tool requires only a web browser, Python®, and dependent packages to function. Other time series tools like TSTools[@Holden:2017] are powerful but require a GIS interface and can only be used to analyze individual pixels rather than larger areas of interest.

![Figure 1](https://raw.githubusercontent.com/CosmiQ/CometTS/master/ExamplePlots/Workflow.png)


![Figure 2](https://raw.githubusercontent.com/CosmiQ/CometTS/master/ExamplePlots/Niamey.png)


The tool ingests two key components: (1) time series of overhead imagery and (2) the user drawn polygon to designate the area of interest. Beyond what is possible with a single satellite image, time series imagery enables the investigation of patterns and sequences of the spectral responses and how they change over time.

``CometTS`` then produces a tabular and visual depiction of relevant statistics of spectral responses for every pixel contained within the polygon that delimits the area of interest. This operation is repeated for every image within the time series. The user can determine the statistic(s) of most relevance for his/her analytic needs. The output is customizable by the user to produce any type or range of statistics needed. For our assessment and demonstration, we choose standard statistics to illustrate trends and uncertainty, including median, lower quartile (25th percentile), upper quartile (75th percentile), linear regression, and a Gaussian signal filter.  Users also have the option to supply “mask” images that are sometimes distributed with satellite imagery or that can be created. These masks can be used to remove areas that contain cloud cover, cloud shadow, snow, or other anomalies that can interfere with analysis of data (Figure 3).  The source code for ``CometTS`` has been archived to Zenodo with the linked DOI: [@Shermeyer:2018]

![Figure 3](https://raw.githubusercontent.com/CosmiQ/CometTS/master/ExamplePlots/CloudMask.png)



# Acknowledgements

We acknowledge contributions from Dylan George, Dave Lindenbaum, Ryan Lewis, and Adam Van Etten.

# References

