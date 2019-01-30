This readme has instructions of working through sampling street points from the road network and then crawling google street view api for street view images of the sampled points.

1- The first step is to sample points where we would like to get street view images.
python sampling.py -s data_1/BostonBspClassesFiltered.shp -p data_1/tabular/BostonPOI.csv  -v
As a proof of concept, the code currently samples 10 points.

This will output a file named "sample.csv"

2- The second step is to feed the file "sample.csv" to the GoogleScrapper.py code which will scrape images from the API.
Note: the GoogleScrapper.py code requires the google API KEY to be entered for it to run. Note that Google doesn't provide the google street view imagery free of cost, please review the cost sheet of Google API usage.

Sample crawled images are stored in the folder BostonStreets.


git filter-branch --force --index-filter \
  'git rm -r --cached --ignore-unmatch data/*' \
  --prune-empty --tag-name-filter cat -- --all
