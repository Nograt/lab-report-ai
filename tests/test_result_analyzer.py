from types import SimpleNamespace

import pandas as pd
import pytest

from app.services.excel_reader import MeasurementTableData
from app.services.result_analyzer import (
    analyze_chart_relationship,
    analyze_section,
)


def measurement_table(
    table_id: int,
    dataframe: pd.DataFrame,
    units: dict[str, str | None] | None = None,
) -> MeasurementTableData:
    return MeasurementTableData(
        table_id=table_id,
        title=f"Table {table_id}",
        sheet_name=f"Sheet{table_id}",
        dataframe=dataframe,
        units=units or {},
    )


def chart(
    figure_id: int,
    table_id: int,
    x: str,
    y: str,
    *,
    filter_column: str | None = None,
    filter_value=None,
):
    return SimpleNamespace(
        figure_id=figure_id,
        table_id=table_id,
        x=x,
        y=y,
        filter_column=filter_column,
        filter_value=filter_value,
    )


def section(
    section_id: int,
    columns: list[str] | None = None,
):
    table = None

    if columns is not None:
        table = SimpleNamespace(
            columns=columns,
        )

    return SimpleNamespace(
        section_id=section_id,
        table=table,
    )


def test_analyzes_increasing_chart():
    df = pd.DataFrame(
        {
            "P": [100, 200, 300],
            "I": [1.0, 2.0, 3.0],
        }
    )

    result = analyze_chart_relationship(
        df=df,
        chart=chart(
            figure_id=1,
            table_id=1,
            x="P",
            y="I",
        ),
    )

    assert result.figure_id == 1
    assert result.x == "P"
    assert result.y == "I"

    assert result.x_min == 100
    assert result.x_max == 300

    assert result.y_min == 1.0
    assert result.y_max == 3.0

    assert result.y_at_min_x == 1.0
    assert result.y_at_max_x == 3.0

    assert result.overall_direction == "increasing"
    assert result.monotonic is True

    assert result.correlation == pytest.approx(1.0)


def test_analyzes_decreasing_chart():
    df = pd.DataFrame(
        {
            "P": [100, 200, 300],
            "n": [1500, 1450, 1400],
        }
    )

    result = analyze_chart_relationship(
        df=df,
        chart=chart(
            figure_id=1,
            table_id=1,
            x="P",
            y="n",
        ),
    )

    assert result.overall_direction == "decreasing"
    assert result.monotonic is True

    assert result.y_at_min_x == 1500
    assert result.y_at_max_x == 1400

    assert result.correlation == pytest.approx(-1.0)


def test_detects_non_monotonic_chart():
    df = pd.DataFrame(
        {
            "P": [100, 200, 300, 400],
            "eta": [
                0.50,
                0.70,
                0.80,
                0.75,
            ],
        }
    )

    result = analyze_chart_relationship(
        df=df,
        chart=chart(
            figure_id=1,
            table_id=1,
            x="P",
            y="eta",
        ),
    )

    assert result.monotonic is False

    # Pomimo lokalnego spadku ogólny trend
    # może nadal być rosnący.
    assert result.overall_direction == "increasing"

    assert result.y_min == 0.50
    assert result.y_max == 0.80


def test_constant_chart():
    df = pd.DataFrame(
        {
            "U": [100, 200, 300],
            "f": [50, 50, 50],
        }
    )

    result = analyze_chart_relationship(
        df=df,
        chart=chart(
            figure_id=1,
            table_id=1,
            x="U",
            y="f",
        ),
    )

    assert result.overall_direction == "constant"
    assert result.monotonic is True

    assert result.y_min == 50
    assert result.y_max == 50

    # Korelacja dla stałej zmiennej nie jest określona.
    assert result.correlation is None


def test_chart_data_is_sorted_by_x_before_analysis():
    df = pd.DataFrame(
        {
            "P": [
                300,
                100,
                200,
            ],
            "I": [
                3.0,
                1.0,
                2.0,
            ],
        }
    )

    result = analyze_chart_relationship(
        df=df,
        chart=chart(
            figure_id=1,
            table_id=1,
            x="P",
            y="I",
        ),
    )

    assert result.x_min == 100
    assert result.x_max == 300

    assert result.y_at_min_x == 1.0
    assert result.y_at_max_x == 3.0

    assert result.monotonic is True


def test_missing_x_column_raises_error():
    df = pd.DataFrame(
        {
            "I": [1.0, 2.0],
        }
    )

    with pytest.raises(
        ValueError,
        match="uses x column",
    ):
        analyze_chart_relationship(
            df=df,
            chart=chart(
                figure_id=1,
                table_id=1,
                x="U",
                y="I",
            ),
        )


def test_missing_y_column_raises_error():
    df = pd.DataFrame(
        {
            "U": [100, 200],
        }
    )

    with pytest.raises(
        ValueError,
        match="uses y column",
    ):
        analyze_chart_relationship(
            df=df,
            chart=chart(
                figure_id=1,
                table_id=1,
                x="U",
                y="I",
            ),
        )


def test_non_numeric_chart_data_raises_error():
    df = pd.DataFrame(
        {
            "U": [
                "abc",
                "xyz",
            ],
            "I": [
                "foo",
                "bar",
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="No valid data for chart",
    ):
        analyze_chart_relationship(
            df=df,
            chart=chart(
                figure_id=1,
                table_id=1,
                x="U",
                y="I",
            ),
        )


def test_analyze_section_calculates_column_statistics():
    df = pd.DataFrame(
        {
            "U": [
                100,
                200,
                300,
            ],
            "I": [
                1.0,
                2.0,
                3.0,
            ],
        }
    )

    table = measurement_table(
        table_id=1,
        dataframe=df,
        units={
            "U": "V",
            "I": "A",
        },
    )

    result = analyze_section(
        df=df,
        section=section(
            section_id=1,
            columns=[
                "U",
                "I",
            ],
        ),
        units=table.units,
        charts=[],
        tables=[table],
    )

    assert result.section_id == 1
    assert len(result.columns) == 2

    voltage_analysis = result.columns[0]

    assert voltage_analysis.column == "U"
    assert voltage_analysis.unit == "V"
    assert voltage_analysis.minimum == 100
    assert voltage_analysis.maximum == 300
    assert voltage_analysis.mean == 200
    assert voltage_analysis.first_value == 100
    assert voltage_analysis.last_value == 300


def test_analyze_section_applies_numeric_chart_filter():
    df = pd.DataFrame(
        {
            "U": [
                100,
                200,
                100,
                200,
            ],
            "n": [
                1000,
                1100,
                1300,
                1200,
            ],
            "Ts": [
                0.5,
                0.5,
                1.0,
                1.0,
            ],
        }
    )

    table = measurement_table(
        table_id=1,
        dataframe=df,
    )

    result = analyze_section(
        df=df,
        section=section(
            section_id=1,
        ),
        units={},
        charts=[
            chart(
                figure_id=1,
                table_id=1,
                x="U",
                y="n",
                filter_column="Ts",
                filter_value=0.5,
            )
        ],
        tables=[table],
    )

    assert len(result.charts) == 1

    chart_analysis = result.charts[0]

    assert chart_analysis.y_min == 1000
    assert chart_analysis.y_max == 1100

    assert (
        chart_analysis.overall_direction
        == "increasing"
    )

    assert chart_analysis.monotonic is True


def test_filter_column_must_exist():
    df = pd.DataFrame(
        {
            "U": [100, 200],
            "n": [1000, 1100],
        }
    )

    table = measurement_table(
        table_id=1,
        dataframe=df,
    )

    with pytest.raises(
        ValueError,
        match="uses filter column",
    ):
        analyze_section(
            df=df,
            section=section(
                section_id=1,
            ),
            units={},
            charts=[
                chart(
                    figure_id=1,
                    table_id=1,
                    x="U",
                    y="n",
                    filter_column="Ts",
                    filter_value=0.5,
                )
            ],
            tables=[table],
        )


def test_filter_column_requires_filter_value():
    df = pd.DataFrame(
        {
            "U": [100, 200],
            "n": [1000, 1100],
            "Ts": [0.5, 1.0],
        }
    )

    table = measurement_table(
        table_id=1,
        dataframe=df,
    )

    with pytest.raises(
        ValueError,
        match="filter_value is missing",
    ):
        analyze_section(
            df=df,
            section=section(
                section_id=1,
            ),
            units={},
            charts=[
                chart(
                    figure_id=1,
                    table_id=1,
                    x="U",
                    y="n",
                    filter_column="Ts",
                    filter_value=None,
                )
            ],
            tables=[table],
        )