#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
# pylint: skip-file
#
# Copyright © 2017 Caleb Robinson <calebrob6@gmail.com>
#
# Distributed under terms of the MIT license.
'''
Responsible for creating the `*_intersection_map.p` intermediate data files used in the disaggregation step.

Inputs:
- `input_fn` path to an administrative area shapefile (e.g. our merged Census tract shapefile)
- `input_key` the name of the column of `input_fn` to use as a primary key
- the "lloyd_hires_usa_data/mastergrid_countryarea_1km.tif" file (or similar) is expected to exist and is used as the grid definition
  - Has a CRS, `height`, and `width`
  - The CRS **must** be the same as `input_fn`

Outputs:
- `output_fn` path to write the resulting "intersection_map.p" data structure to

The intersection_map.p data structure is a (height x width) list where an entry intersection_map[i][j] is a dictionary that lists all the shapes from
`input_fn` that intersect the [i,j]th grid cell in the grid definition raster. Specifically each key in intersection_map[i][j] is a primary_key from the
`input_key` column of `input_fn`, and the assosciated value is the area of intersection between the shape and grid cell.

NOTE: this is generally an expensive operation as the number of shapes in `input_fn` is > 100k for the Census Tract shapefiles. This computation has beem
parallelized and uses an spatial tree for faster intersection calculations.

NOTE: **The `input_fn` should have the same CRS as the grid definition raster**

Example commands:
- python create_shapefile_raster_intersection_file_parallel.py --input_fn boundary_shapefiles/census_tracts/tl_2010_all_tract00_epsg4326.shp --input_key CTIDFP00 --output_fn derived_data/tract00_intersection_map.p
- python create_shapefile_raster_intersection_file_parallel.py --input_fn boundary_shapefiles/census_tracts/tl_2010_all_tract10_epsg4326.shp --input_key GEOID10 --output_fn derived_data/tract10_intersection_map.p
- python create_shapefile_raster_intersection_file_parallel.py --input_fn boundary_shapefiles/counties/tl_2010_us_county00_trimmed_epsg4326.shp --input_key CNTYIDFP00 --output_fn derived_data/county00_intersection_map.p
- python create_shapefile_raster_intersection_file_parallel.py --input_fn boundary_shapefiles/counties/tl_2010_us_county10_trimmed_epsg4326.shp --input_key GEOID10 --output_fn derived_data/county10_intersection_map.p
'''
import sys
import os
import time
import argparse
import datetime


import rasterio
import fiona
import rtree
from shapely.geometry import shape, Polygon
import pickle

import multiprocessing

def initializer(q, fn, index_fn):
    global index, features, affine, count # not sure if these are needed

    print("Loading worker process...")

    features, affine = pickle.load(open(fn, "rb"))
    index = rtree.index.Index(index_fn)
    count = 0

    print index.get_bounds()

    print("Finished initializing PID:", os.getpid())
    q.get()
    q.task_done()


def work(arg):
    global index, features, affine, count # not sure if these are needed
    x,y = arg

    if count % 100000==0:
        print(os.getpid(), count)

    cell_data = {}
        
    left, top = (x,y) * affine
    right, bottom = (x+1, y+1) * affine

    bounds = (left,bottom,right,top)

    intersections = list(index.intersection(bounds))

    if len(intersections) > 0:            
        grid_poly = Polygon([[left, top], [right, top], [right, bottom], [left, bottom]])
        grid_area = grid_poly.area
        
        for fid in intersections:
            feature_properties, tract_poly = features[fid]                    
            intersection_area = tract_poly.intersection(grid_poly).area
            #if intersection_area > 0:
            cell_data[fid] = (intersection_area / grid_area)
    else:
        # No intersection found
        pass

    count += 1
    return cell_data


def do_args(arg_list, name):
    parser = argparse.ArgumentParser(description=name)

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debugging", default=False)
    parser.add_argument("--input_fn", action="store", dest="input_fn", type=str, help="Input shapefile name", required=True)
    parser.add_argument("--input_key", action="store", dest="input_key", type=str, help="The property to use as a primary key from the input shapefile", required=True)
    parser.add_argument("--output_fn", action="store", dest="output_fn", type=str, help="Output file name", required=True)

    return parser.parse_args(arg_list)

#---------------------------------------------------------------------------------------------------
def main():
    prog_name = sys.argv[0]
    args = do_args(sys.argv[1:], prog_name)

    verbose = args.verbose
    input_fn = args.input_fn
    input_key = args.input_key
    output_fn = args.output_fn

    print("Starting %s at %s" % (prog_name, str(datetime.datetime.now())))
    start_time = float(time.time())

    if not os.path.isfile(input_fn):
        print("Input does not exist, exiting")
        return

    output_base = os.path.dirname(output_fn)
    if output_base != "" and not os.path.exists(output_base):
        print("Output directory does not exist, making output dirs: %s" % (output_base))
        os.makedirs(output_base)


    #---------------------------------------------------------
    # Create rtree instance
    #---------------------------------------------------------
    tic = float(time.time())

    index = rtree.index.Index("tmp_index.idx")
    features = {}
    count = 0

    f = fiona.open(input_fn, "r")
    for feature in f:            
        if count % 10000 == 0:
            print("Loaded %d shapes..." % (count))
            
        fid = int(feature["properties"][input_key])
        geom = shape(feature["geometry"])
        index.insert(fid, geom.bounds)
        
        if fid not in features:
            features[fid] = (feature["properties"], geom)
        else:
            print("ERROR %d" % (fid))
            
        count += 1
    f.close()
    print(index.get_bounds())
    index.close()

    print("Finished creating rtree in %0.4f seconds" % (time.time() - tic))


    #---------------------------------------------------------
    # Load raster definition
    #---------------------------------------------------------
    print("Starting to load cells")
    tic = float(time.time())

    # load any of the raster files that we clipped as our reference grid
    f = rasterio.open("lloyd_hires_usa_data/mastergrid_countryarea_1km.tif", "r")
    affine = f.affine
    height, width = f.read().squeeze().shape
    f.close()

    print("Intersecting versus grid of cells with shape (%d, %d)" % (height, width))
    print("Finished loading cells in %0.4f seconds" % (time.time() - tic))


    #---------------------------------------------------------
    # Perform intersections and save results
    #---------------------------------------------------------
    print("Starting intersection calculation")
    tic = float(time.time())


    pickle.dump([features, affine], open("tmp.p", "wb"), protocol=pickle.HIGHEST_PROTOCOL)
    num_processes = 64
    q = multiprocessing.JoinableQueue()
    for i in range(num_processes):
        q.put(i)
    pool = multiprocessing.Pool(num_processes, initializer=initializer, initargs=(q, "tmp.p", "tmp_index.idx"))
    q.join()
    os.remove("tmp.p")
    os.remove("tmp_index.idx.dat")
    os.remove("tmp_index.idx.idx")

    args = []
    for y in xrange(height):
        for x in xrange(width):
            args.append((x,y))

    results = pool.map(work, args)
    pool.close()
    pool.join()


    i = 0
    intersection_map = []
    for y in xrange(height):
        row = []
        for x in xrange(width):
            row.append(results[i])
            i += 1
        intersection_map.append(row)

    print("Finished intersection calculation in %0.4f seconds" % (time.time() - tic))


    #---------------------------------------------------------
    # Write output
    #---------------------------------------------------------
    print("Writing output file")
    tic = float(time.time())

    pickle.dump(intersection_map, open(output_fn, "wb"), protocol=pickle.HIGHEST_PROTOCOL)

    print("Finished writing output in %0.4f seconds" % (time.time() - tic))
    print("Finished in %0.4f seconds" % (time.time() - start_time))


if __name__ == "__main__":
    main()