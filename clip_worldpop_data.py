#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 Caleb Robinson <calebrob6@gmail.com>
#
# Distributed under terms of the MIT license.
import sys
import os
import time
import subprocess

def main():
    tic = float(time.time())
    
    if not os.path.isdir("lloyd_hires_usa_data/"):
        os.makedirs("lloyd_hires_usa_data/")

    for fn in os.listdir("lloyd_hires_global_data/"):
        
        if fn.endswith(".tif"):
               
            input_fn = "lloyd_hires_global_data/%s" % (fn)
            output_fn  = "lloyd_hires_usa_data/%s" % (fn)

            print("Running on: %s" % (input_fn))

            command = [
                "gdalwarp",
                "-te", "-125.225839", "23.998131", "-66.449895", "49.884358", # this is the same bounding box used in `Download from Earth Engine.ipynb
                "-t_srs", "epsg:4326",
                "-tr", "0.0083333333", "0.0083333333", # this sets the grid cells to be ~1km x 1km
                "-of", "GTiff",
                input_fn,
                output_fn
            ]
            subprocess.call(command)

    print("Finished in %0.4f seconds" % (time.time() - tic))

if __name__ == "__main__":
    main()