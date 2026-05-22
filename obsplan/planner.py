"""Core observation planning routines.

The public functions in this module are intentionally independent from
``argparse`` so they can be reused from scripts, notebooks, tests, or the CLI.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
import logging
from pathlib import Path
from typing import Sequence

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from astropy import units as u
from astropy.coordinates import AltAz, Angle, EarthLocation, SkyCoord
from astropy.table import Table
from astropy.time import Time


DEFAULT_DATA_PACKAGE = "obsplan.data"
LOGGER = logging.getLogger(__name__)
SOURCE_COLUMNS = {"coordinate", "unit", "name"}
TELESCOPE_COLUMNS = {"name", "lat", "lon", "height"}


@dataclass(frozen=True)
class ObservationPlan:
    """Resolved observing setup used by plotting and future analysis tools."""

    location: EarthLocation
    start_time: Time
    length_hours: float
    target_coordinates: list[SkyCoord]
    target_names: list[str]
    calibrator_coordinates: list[SkyCoord]
    calibrator_names: list[str]

    @property
    def end_time(self) -> Time:
        """End time of the requested observing block."""

        return self.start_time + self.length_hours * u.hour


def package_data_path(filename: str) -> Path:
    """Return the installed path for one of obsplan's bundled CSV files."""

    return Path(str(files(DEFAULT_DATA_PACKAGE).joinpath(filename)))


def read_table(path: str | Path) -> Table:
    """Read a CSV table and add a clearer error when the file is unavailable."""

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Could not find CSV file: {path}")
    LOGGER.debug("Reading table: %s", path)
    return Table.read(path, format="csv")


def validate_columns(table: Table, required_columns: set[str], table_name: str) -> None:
    """Raise a clear error if a user-editable CSV is missing required columns."""

    missing = required_columns.difference(table.colnames)
    if missing:
        missing_list = ", ".join(sorted(missing))
        required_list = ", ".join(sorted(required_columns))
        raise ValueError(
            f"{table_name} is missing required column(s): {missing_list}. "
            f"Required columns: {required_list}"
        )


def load_telescope(site: str, telescope_file: str | Path | None = None) -> EarthLocation:
    """Resolve a telescope location from astropy's site registry or a CSV file.

    The telescope CSV must contain ``name``, ``lat``, ``lon``, and ``height``
    columns. Latitude and longitude are interpreted as degrees unless they are
    sexagesimal strings supported by ``astropy.coordinates.Angle``. Custom CSV
    entries are checked first so local observatory definitions can override or
    supplement astropy's site registry.
    """

    site_key = site.strip().lower()
    LOGGER.debug("Resolving telescope site: %s", site_key)
    table_path = telescope_file or package_data_path("telescope.csv")
    site_table = read_table(table_path)
    validate_columns(site_table, TELESCOPE_COLUMNS, str(table_path))
    names = [str(name).lower() for name in site_table["name"]]
    if site_key in names:
        row = site_table[names.index(site_key)]
        LOGGER.debug("Using custom telescope definition from %s", table_path)
        return EarthLocation(
            lat=Angle(str(row["lat"]), unit=u.degree),
            lon=Angle(str(row["lon"]), unit=u.degree),
            height=float(row["height"]) * u.m,
        )

    astropy_sites = {name.lower(): name for name in EarthLocation.get_site_names()}
    if site_key in astropy_sites:
        LOGGER.debug("Using astropy site registry for %s", site)
        return EarthLocation.of_site(astropy_sites[site_key])

    known = ", ".join(str(name) for name in site_table["name"])
    raise ValueError(f"Unknown telescope '{site}'. Known custom telescopes: {known}")


def parse_coordinate(coordinate: str, unit: str) -> SkyCoord:
    """Parse a source coordinate from a supported CSV or CLI representation."""

    unit_key = unit.strip().lower()
    if unit_key == "hms":
        units = (u.hourangle, u.deg)
    elif unit_key == "deg":
        units = (u.deg, u.deg)
    else:
        raise ValueError("Source coordinate unit must be 'hms' or 'deg'")
    return SkyCoord(coordinate, unit=units, frame="icrs")


def format_coordinate_hmsdms(coordinate: SkyCoord) -> str:
    """Format a coordinate as compact HMS/DMS strings."""

    ra = coordinate.ra.to_string(unit=u.hourangle, sep="", precision=0, pad=True)
    dec = coordinate.dec.to_string(unit=u.deg, sep="", precision=0, alwayssign=True, pad=True)
    return f"{ra}{dec}"


def format_coordinate_degrees(coordinate: SkyCoord) -> str:
    """Format a coordinate as decimal-degree RA and Dec."""

    return f"{coordinate.ra.deg:.6f} {coordinate.dec.deg:+.6f}"


def format_target_label(index: int, coordinate: SkyCoord) -> str:
    """Create a compact J2000-style label for command-line targets."""

    return f"s{index}: J{format_coordinate_hmsdms(coordinate)}"


def format_coordinate_summary(name: str, coordinate: SkyCoord) -> str:
    """Create a log-friendly coordinate summary in HMS/DMS and degrees."""

    hmsdms = format_coordinate_hmsdms(coordinate)
    degrees = format_coordinate_degrees(coordinate)
    if f"J{hmsdms}" in name:
        return f"{name} ({degrees} deg)"
    return f"{name}: J{hmsdms} ({degrees} deg)"


def load_sources(source_file: str | Path) -> tuple[list[SkyCoord], list[str]]:
    """Load named sources from a CSV file.

    The CSV must contain ``coordinate``, ``unit``, and ``name`` columns. The
    unit column accepts ``hms`` for hour-angle RA plus degree Dec, or ``deg`` for
    decimal-degree RA and Dec.
    """

    source_table = read_table(source_file)
    validate_columns(source_table, SOURCE_COLUMNS, str(source_file))
    LOGGER.debug("Loading sources from %s", source_file)
    coordinates: list[SkyCoord] = []
    names: list[str] = []

    for row in source_table:
        coordinates.append(parse_coordinate(str(row["coordinate"]), str(row["unit"])))
        names.append(str(row["name"]))

    return coordinates, names


def parse_cli_targets(
    target_coordinates: Sequence[str],
    unit: str = "hms",
) -> tuple[list[SkyCoord], list[str]]:
    """Parse target coordinates supplied directly on the command line."""

    coordinates = [parse_coordinate(coordinate, unit) for coordinate in target_coordinates]
    names = [
        format_target_label(index, coordinate)
        for index, coordinate in enumerate(coordinates, start=1)
    ]
    return coordinates, names


def select_sources(
    coordinates: Sequence[SkyCoord],
    names: Sequence[str],
    selected_names: Sequence[str] | None,
    *,
    source_type: str,
) -> tuple[list[SkyCoord], list[str]]:
    """Return all sources or the named subset requested by the user."""

    if not selected_names or any(name.lower() == "all" for name in selected_names):
        LOGGER.debug("Selected all %ss", source_type)
        return list(coordinates), list(names)

    lookup = {name.lower(): index for index, name in enumerate(names)}
    missing = [name for name in selected_names if name.lower() not in lookup]
    if missing:
        available = ", ".join(names)
        raise ValueError(
            f"Unknown {source_type} {', '.join(missing)}. "
            f"Available {source_type}s: {available}"
        )

    indexes = [lookup[name.lower()] for name in selected_names]
    return [coordinates[index] for index in indexes], [names[index] for index in indexes]


def build_observation_plan(
    *,
    site: str = "atca",
    start_time: str = "2022-03-11 00:00:00",
    length_hours: float = 6.0,
    target_coordinates: Sequence[str] | None = None,
    target_unit: str = "hms",
    calibrator_names: Sequence[str] | None = None,
    telescope_file: str | Path | None = None,
    source_file: str | Path | None = None,
    calibrator_file: str | Path | None = None,
) -> ObservationPlan:
    """Resolve input files and CLI values into an observation plan."""

    if length_hours <= 0:
        raise ValueError("Observation length must be greater than zero hours")

    location = load_telescope(site, telescope_file)
    if target_coordinates:
        LOGGER.debug("Using %d target(s) from command line", len(target_coordinates))
        targets, target_names = parse_cli_targets(target_coordinates, target_unit)
    else:
        LOGGER.debug("Using target source file")
        targets, target_names = load_sources(source_file or package_data_path("source.csv"))

    calibrators, available_calibrator_names = load_sources(
        calibrator_file or package_data_path("calibrator.csv")
    )
    selected_calibrators, selected_calibrator_names = select_sources(
        calibrators,
        available_calibrator_names,
        calibrator_names,
        source_type="calibrator",
    )

    return ObservationPlan(
        location=location,
        start_time=Time(start_time, format="iso", location=location),
        length_hours=length_hours,
        target_coordinates=targets,
        target_names=target_names,
        calibrator_coordinates=selected_calibrators,
        calibrator_names=selected_calibrator_names,
    )


def observing_window_times(plan: ObservationPlan, padding_hours: float = 5.0) -> Time:
    """Create a time grid centered around the observing block for plotting."""

    return plan.start_time + np.arange(0.0, 24.0, 0.1) * u.hour - padding_hours * u.hour


def plot_elevation(
    plan: ObservationPlan,
    *,
    elevation_limit: float = 12.0,
    output_path: str | Path | None = None,
    show: bool = True,
):
    """Plot target and calibrator elevation over a 24-hour UTC window.

    Parameters
    ----------
    plan:
        Fully resolved observing setup.
    elevation_limit:
        Lower y-axis limit in degrees.
    output_path:
        Optional path for saving a PNG or other matplotlib-supported format.
    show:
        Whether to display the interactive matplotlib window.

    Returns
    -------
    matplotlib.figure.Figure
        The created figure, useful for tests or caller-side customization.
    """

    times = observing_window_times(plan)
    plot_times = times.datetime
    altaz_frame = AltAz(obstime=times, location=plan.location)

    fig, ax = plt.subplots(figsize=(9, 6))
    for coordinate, name in zip(plan.target_coordinates, plan.target_names):
        elevation = coordinate.transform_to(altaz_frame).alt
        ax.plot(plot_times, elevation.degree, label=name)

    for coordinate, name in zip(plan.calibrator_coordinates, plan.calibrator_names):
        elevation = coordinate.transform_to(altaz_frame).alt
        ax.plot(plot_times, elevation.degree, linestyle="--", label=name)

    ax.axvspan(plan.start_time.datetime, plan.end_time.datetime, alpha=0.25, color="pink")
    ax.set_ylim(bottom=elevation_limit)
    ax.set_ylabel("Elevation (deg)")
    ax.set_xlabel("Time (UTC)")
    ax.legend()

    date_form = mdates.DateFormatter("%d-%b-%Y/%H:%M")
    ax.xaxis.set_major_formatter(date_form)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
    fig.autofmt_xdate()

    ax_top = ax.twiny()
    ax_top.set_xlim(ax.get_xlim())
    ax_top.set_xticks(
        [
            mdates.date2num(plan.start_time.datetime),
            mdates.date2num(plan.end_time.datetime),
        ]
    )
    ax_top.xaxis.set_major_formatter(date_form)

    fig.tight_layout()
    if output_path:
        LOGGER.info("Saving elevation plot to %s", output_path)
        fig.savefig(output_path, dpi=150)
    if show:
        plt.show()
    return fig
