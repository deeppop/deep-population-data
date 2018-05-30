#!/bin/bash

wget --accept 7z --mirror --page-requisites --adjust-extension --convert-links --backup-converted --no-parent -i lloyd_hires_global_data_paper_links.txt

mv www.worldpop.org.uk/data/lloyd_hires_global_data_paper/data/1km_mosaics/ lloyd_hires_global_data
mv lloyd_hires_global_data/mastergrid_chirps-v2.0/* lloyd_hires_global_data/
mv lloyd_hires_global_data/mastergrid_nightlightsv4_92-13/* lloyd_hires_global_data/

cd lloyd_hires_global_data/
7z x "*.7z"
cd ..

rm -rf www.worldpop.org.uk/