# obsplan

`obsplan` is a small observation planning tool for radio astronomy. It plots the
elevation of science targets and calibrators over a UTC observing window, using
`astropy` for coordinate and site calculations.

The project can be used directly from this repository with `python obslst.py`,
or installed as a package to expose the `obsplan` command.

## Features

- Plot target and calibrator elevation for a selected telescope/site.
- Read targets, calibrators, and custom telescope locations from CSV files.
- Accept one or more target coordinates directly from the command line.
- Select calibrators by name with `--cal`, or plot all calibrators with
  `--cal all`.
- Save plots to PNG for proposals, logs, or observation notes.

## Installation

Create and activate a virtual environment, then install the project:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

For development and tests:

```bash
python -m pip install -e ".[dev]"
pytest
```

If you only want the runtime dependencies without installing the package:

```bash
python -m pip install -r requirements.txt
```

## Quick Usage

Plot a target from the command line:

```bash
obsplan --target "05:23:48 -71:25:52" --time "2022-03-20 12:00:00" --length 12
```

Command-line targets default to `hms`, meaning hour-angle RA plus degree Dec.
Use `--target-unit deg` for decimal-degree RA and Dec:

```bash
obsplan --target "80.9 21.3" --target-unit deg
```

Plot multiple command-line targets:

```bash
obsplan \
  --target "05:23:48 -71:25:52" "00:58:00 -23:54:49" \
  --time "2022-03-20 12:00:00" \
  --length 12
```

Read targets from `source.csv` and save the output plot:

```bash
obsplan --sourcefile source.csv --time "2022-03-20 12:00:00" --length 12 --save-png
```

Show debug logging while running:

```bash
obsplan --target "05:23:48 -71:25:52" --no-show --verbose
```

The legacy script entry point still works:

```bash
python obslst.py --target "05:23:48 -71:25:52"
```

## CSV Formats

### Telescope File

The telescope file stores sites that are not available through
`astropy.coordinates.EarthLocation.get_site_names()`.

Required columns:

- `name`: lowercase site name, such as `atca`, `parkes`, `mopra`, or `gmrt`
- `lat`: latitude in degrees or sexagesimal degree format
- `lon`: longitude in degrees
- `height`: height in meters

Example:

```csv
name,lat,lon,height
atca,-30 18 46.385,149.5501388,236.87
```

### Source and Calibrator Files

Target and calibrator files use the same format.

Required columns:

- `coordinate`: RA/Dec coordinate pair
- `unit`: `hms` for hour-angle RA plus degree Dec, or `deg` for decimal degrees
- `name`: plot label and calibrator selection name

Example:

```csv
coordinate,unit,name
19:39:25.026 -63:42:45.63,hms,1934-638
```

By default, an installed package uses bundled example data. Pass `--telefile`,
`--sourcefile`, or `--calfile` to use local files instead.

## Python API

```python
from obsplan import build_observation_plan, plot_elevation

plan = build_observation_plan(
    site="atca",
    start_time="2022-03-20 12:00:00",
    length_hours=12,
    target_coordinates=["05:23:48 -71:25:52"],
    calibrator_names=["1934-638"],
)

plot_elevation(plan, output_path="elevation.png", show=False)
```

## Roadmap

- Add LST, azimuth, and parallactic angle plots.
- Add optical planning support, including twilight and Sun altitude.
- Improve calibrator selection with angular separation and flux metadata.
