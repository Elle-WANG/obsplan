"""Command line interface for obsplan."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Create the command line parser."""

    parser = argparse.ArgumentParser(
        prog="obsplan",
        description="Plan source and calibrator elevation for an observing block.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--site", default="atca", help="telescope/site name")
    parser.add_argument(
        "--target",
        nargs="+",
        help=(
            "target coordinates, for example '05:23:48 -71:25:52'. "
            "If omitted, targets are read from --sourcefile."
        ),
    )
    parser.add_argument(
        "--target-unit",
        choices=["hms", "deg"],
        default="hms",
        help="coordinate unit for targets supplied with --target",
    )
    parser.add_argument(
        "--cal",
        nargs="+",
        default=["1934-638", "0823-500"],
        help="calibrator names to plot, or 'all' to plot every calibrator",
    )
    parser.add_argument(
        "--time",
        default="2022-03-11 00:00:00",
        help="observing start time in UTC, formatted as 'YYYY-MM-DD HH:MM:SS'",
    )
    parser.add_argument(
        "--length",
        type=float,
        default=6.0,
        help="planned observing length in hours",
    )
    parser.add_argument(
        "--elimit",
        type=float,
        default=12.0,
        help="minimum elevation to show in degrees; Parkes often uses 30 deg",
    )
    parser.add_argument(
        "--oname",
        default="elevation",
        help="output filename stem when --save-png is used",
    )
    parser.add_argument("--save-png", action="store_true", help="save the plot as a PNG")
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="build/save the plot without opening a window",
    )
    parser.add_argument(
        "--telefile",
        type=Path,
        help="CSV file containing extra telescope locations",
    )
    parser.add_argument(
        "--sourcefile",
        type=Path,
        help="CSV file containing target sources",
    )
    parser.add_argument(
        "--calfile",
        type=Path,
        help="CSV file containing calibrator sources",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show debug logging",
    )
    return parser


def configure_logging(verbose: bool = False) -> None:
    """Configure command line logging."""

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
    logging.getLogger("obsplan").setLevel(logging.DEBUG if verbose else logging.INFO)


def main(argv: list[str] | None = None) -> int:
    """Run the obsplan command line application."""

    args = build_parser().parse_args(argv)
    configure_logging(args.verbose)

    from obsplan.planner import (
        build_observation_plan,
        format_coordinate_summary,
        plot_elevation,
    )

    try:
        plan = build_observation_plan(
            site=args.site,
            start_time=args.time,
            length_hours=args.length,
            target_coordinates=args.target,
            target_unit=args.target_unit,
            calibrator_names=args.cal,
            telescope_file=args.telefile,
            source_file=args.sourcefile,
            calibrator_file=args.calfile,
        )
    except (FileNotFoundError, ValueError) as exc:
        LOGGER.error("%s", exc)
        return 2

    output_path = f"{args.oname}.png" if args.save_png else None

    LOGGER.info("Planning observation using telescope: %s", args.site)
    for name, coordinate in zip(plan.target_names, plan.target_coordinates):
        LOGGER.info("Target source: %s", format_coordinate_summary(name, coordinate))
    LOGGER.info("Calibrators: %s", ", ".join(plan.calibrator_names))
    LOGGER.info("Observing window UTC: %s to %s", plan.start_time.iso, plan.end_time.iso)
    LOGGER.info("Observation length: %.2f hours", plan.length_hours)
    LOGGER.info("Output path: %s", output_path or "not saving")

    plot_elevation(
        plan,
        elevation_limit=args.elimit,
        output_path=output_path,
        show=not args.no_show,
    )
    return 0
