# deep-population-data

A collection of scripts and notebooks used to process GIS data for the deeppop project. The main goal here is to disaggregate US Census data onto a raster that is aligned with other raster data sources - satellite imagery, night light imagery, etc. - so that we can easily target the Census data with machine learning models.

US Census data is provided at several administrative levels (see here for the hierarchy of these levels: https://www2.census.gov/geo/pdfs/reference/geodiagram.pdf). The smallest (i.e. highest resolution) of these administrative levels are Census Blocks, which are at the scale of a few buildings. In this repository we show how to disagregate population counts using the Census Tract definitions, however the same steps could be used at any administrative level.

The steps for disaggregating population data over a raster grid for a given year are as follows:

1. Download and merge the Census Tract boundary information for the given year for all states in the contiguous US. 
2. Use a tool such as the American Fact Finder (https://factfinder.census.gov/faces/nav/jsf/pages/index.xhtml) or Social Explorer (https://www.socialexplorer.com/) to download population counts for the given year (total counts will be in Summary File 1).
    - Join the population counts with the shapefiles prepared in step 1.
3. Calculate the area of intersection between each raster cell in the given grid and the Census Tracts that it overlaps with.
4. Iterate over the Census Tracts and split their population proportionally by area over the raster cells that intersect with them.

## Downloading Satellite Data

Steps:

0. Register for a Google Earth Engine account and install the Earth Engine API python library (https://developers.google.com/earth-engine/python_install_manual).
1. Run `Earth Engine Authentication.ipynb` once to authenticate your local computer to use the Google Earth Engine API.
2. Customize and run the `Download from Earth Engine.ipynb` notebook to setup tasks on Google Earth Engine that export square patches of Landsat imagery as GeoTIFFs to your Google Drive account (ensure that you have sufficient space on your Google Drive account, for reference, the current Landsat 8 download uses ~450GB).
3. Download the GeoTIFFs from your Google Drive account (a batch download tool such as https://github.com/odeke-em/drive might be helpfulif you have performed a large export).
