import pytest
from astropy import units as u
from astropy.coordinates import Angle
from astropy.table import Table

from obsplan.planner import (
    build_observation_plan,
    format_coordinate_degrees,
    format_coordinate_hmsdms,
    load_sources,
    load_telescope,
    package_data_path,
    plot_elevation,
    parse_cli_targets,
    read_table,
    select_sources,
    validate_columns,
)


def row_by_name(table, name):
    names = [str(row_name).lower() for row_name in table["name"]]
    return table[names.index(name.lower())]


def test_packaged_calibrators_include_standard_atca_sources():
    coordinates, names = load_sources(package_data_path("calibrator.csv"))
    by_name = dict(zip(names, coordinates))

    assert "1934-638" in by_name
    assert "0823-500" in by_name
    assert by_name["1934-638"].ra.deg == pytest.approx(294.854275, abs=1e-5)
    assert by_name["1934-638"].dec.deg == pytest.approx(-63.712675, abs=1e-5)
    assert by_name["0823-500"].ra.deg == pytest.approx(126.361954, abs=1e-5)
    assert by_name["0823-500"].dec.deg == pytest.approx(-50.177358, abs=1e-5)


def test_packaged_telescope_file_includes_expected_custom_sites():
    telescope_table = read_table(package_data_path("telescope.csv"))
    atca = row_by_name(telescope_table, "atca")
    parkes = row_by_name(telescope_table, "parkes")

    assert Angle(str(atca["lat"]), unit=u.degree).deg == pytest.approx(-30.3128847)
    assert Angle(str(atca["lon"]), unit=u.degree).deg == pytest.approx(149.5501388)
    assert float(atca["height"]) == pytest.approx(236.87)

    assert Angle(str(parkes["lat"]), unit=u.degree).deg == pytest.approx(-32.9984064)
    assert Angle(str(parkes["lon"]), unit=u.degree).deg == pytest.approx(148.2635101)
    assert float(parkes["height"]) == pytest.approx(410.80)


def test_load_custom_telescope_returns_expected_location():
    location = load_telescope("atca", package_data_path("telescope.csv"))

    assert location.height.to_value(u.m) == pytest.approx(236.87)


def test_packaged_sources_use_supported_units():
    source_table = read_table(package_data_path("source.csv"))
    supported_units = {"hms", "deg"}

    assert all(str(unit).lower() in supported_units for unit in source_table["unit"])


def test_select_sources_filters_by_name():
    coordinates, names = load_sources(package_data_path("calibrator.csv"))

    selected_coordinates, selected_names = select_sources(
        coordinates,
        names,
        ["0823-500"],
        source_type="calibrator",
    )

    assert len(selected_coordinates) == 1
    assert selected_names == ["0823-500"]


def test_cli_targets_default_to_hms_and_can_use_degrees():
    hms_coordinates, _ = parse_cli_targets(["05:23:48 -71:25:52"])
    deg_coordinates, _ = parse_cli_targets(["80.9 21.3"], unit="deg")

    assert hms_coordinates[0].ra.deg == pytest.approx(80.95)
    assert hms_coordinates[0].dec.deg == pytest.approx(-71.431111, abs=1e-5)
    assert deg_coordinates[0].ra.deg == pytest.approx(80.9)
    assert deg_coordinates[0].dec.deg == pytest.approx(21.3)
    assert format_coordinate_hmsdms(hms_coordinates[0]) == "052348-712552"
    assert format_coordinate_degrees(deg_coordinates[0]) == "80.900000 +21.300000"


def test_build_plan_from_cli_targets():
    plan = build_observation_plan(
        target_coordinates=["05:23:48 -71:25:52"],
        calibrator_names=["1934-638"],
    )

    assert plan.target_names == ["s1: J052348-712552"]
    assert plan.calibrator_names == ["1934-638"]
    assert plan.length_hours == 6.0


def test_plot_uses_target_coordinate_labels_without_limit_line():
    plan = build_observation_plan(
        target_coordinates=["05:23:48 -71:25:52"],
        calibrator_names=["1934-638"],
    )

    figure = plot_elevation(plan, show=False)
    axes = figure.axes[0]
    _, labels = axes.get_legend_handles_labels()

    assert "s1: J052348-712552" in labels


def test_validate_columns_reports_missing_user_csv_columns():
    table = Table({"coordinate": ["05:23:48 -71:25:52"], "name": ["target"]})

    with pytest.raises(ValueError, match="missing required column"):
        validate_columns(table, {"coordinate", "unit", "name"}, "source.csv")
