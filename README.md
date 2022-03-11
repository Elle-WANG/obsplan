# obsplan

It's an observation plan tool. Mainly focus on radio telescope. Will update optical telescope later. 

## Requirement

### Package requirement

* sys
* argparse
* numpy
* matplotlib
* astropy
* astroplan (necessary once finish future developement)

### Other files

#### Telescope

`telescope.csv` stored locations of telescopes which are not included in the astropy. You can check the astropy stored telescope names by EarthLocation.get_site_names(). 

If you want to add unknown/new telescope into the telescope csv file:
* available telescope: atca, parkes, mopra, gmrt... (lowercase name)
* lat and lon unit of degree
* height unit of meter

#### Target(s)

You can input the target coordinates via command line using `--target`. Alternatively you can write the source information into `source.csv`, format as 
* coordinates
* unit (deg or hms)
* name (use as plot label)

#### Calibrators

There is also a `calibrator.csv` to store the calibrator information. Same format as `source.csv`. 

Only 1934-638 and 0823-500 are available in current database (two standard calibrator for ATCA). Furthure development will be needed to actually select the proper calibrator. Currently it will plot all calibrators within the database. 

Those files should be in the same folder with `obslst.py`. You can also specify the file folder use `--telefile` (telescope csv) `--sourcefile` (target csv) `--calfile` (calibrator csv)


## Quick Usage

**Example 1:**

Input target coordinates, expect observing time in UTC, and expect observing length in hours. 
```
python obslst.py --target '05:23:48 -71:25:52' --time '2022-03-20 12:00:00' --length 12
```

You can also input two targets
```
python obslst.py --target '05:23:48 -71:25:52' '00:58:00 -23:54:49' --time '2022-03-20 12:00:00' --length 12
```


**Example 2:**

Read the target coordinates from `source.csv`. Will plot all sources listed in the csv file. 
```
python obslst.py --time '2022-03-20 12:00:00' --length 12
```







