from types import SimpleNamespace

import pandas as pd
import pytest

from app.services.chart_generator import (
    generate_chart,
    match_column_name,
)
from app.services.excel_reader import MeasurementTableData


def measurement_table(
    table_id: int,
    dataframe: pd.DataFrame,
    units: dict[str, str | None],
) -> MeasurementTableData:
    return MeasurementTableData(
        table_id=table_id,
        title=f"Table {table_id}",
        sheet_name=f"Sheet{table_id}",
        dataframe=dataframe,
        units=units,
    )


def chart(
    figure_id: int,
    table_id: int,
    x: str,
    y: str,
    *,
    filter_column: str | None = None,
    filter_value=None,
    label: str | None = None,
    connect_points: bool = True,
    x_scale: str = "linear",
    y_scale: str = "linear",
    show_grid: bool = True,
    show_legend: bool = True,
):
    return SimpleNamespace(
        figure_id=figure_id,
        table_id=table_id,
        x=x,
        y=y,
        filter_column=filter_column,
        filter_value=filter_value,
        label=label,
        connect_points=connect_points,
        x_scale=x_scale,
        y_scale=y_scale,
        show_grid=show_grid,
        show_legend=show_legend,
    )


def test_match_column_name_exact_match():
    df = pd.DataFrame(
        {
            "Voltage": [10, 20],
        }
    )

    result = match_column_name(
        "Voltage",
        df,
    )

    assert result == "Voltage"


def test_match_column_name_case_insensitive():
    df = pd.DataFrame(
        {
            "Voltage": [10, 20],
        }
    )

    result = match_column_name(
        "voltage",
        df,
    )

    assert result == "Voltage"


def test_match_column_name_unknown_column_raises_error():
    df = pd.DataFrame(
        {
            "Voltage": [10, 20],
        }
    )

    with pytest.raises(
        ValueError,
        match="Unable to find column",
    ):
        match_column_name(
            "Current",
            df,
        )


def test_generates_single_chart(tmp_path):
    table = measurement_table(
        table_id=1,
        dataframe=pd.DataFrame(
            {
                "U": [100, 150, 200],
                "I": [1.0, 1.5, 2.0],
            }
        ),
        units={
            "U": "V",
            "I": "A",
        },
    )

    charts = [
        chart(
            figure_id=1,
            table_id=1,
            x="U",
            y="I",
        )
    ]

    files = generate_chart(
        tables=[table],
        charts=charts,
        output_dir=tmp_path,
    )

    assert len(files) == 1

    file = files[0]

    assert file.name == "figure_1.png"
    assert file.exists()
    assert file.stat().st_size > 0


def test_multiple_series_with_same_figure_id_create_one_file(
    tmp_path,
):
    table = measurement_table(
        table_id=1,
        dataframe=pd.DataFrame(
            {
                "P": [100, 200, 300],
                "I": [1.0, 2.0, 3.0],
                "n": [1500, 1450, 1400],
            }
        ),
        units={
            "P": "W",
            "I": "A",
            "n": "rpm",
        },
    )

    charts = [
        chart(
            figure_id=1,
            table_id=1,
            x="P",
            y="I",
        ),
        chart(
            figure_id=1,
            table_id=1,
            x="P",
            y="n",
        ),
    ]

    files = generate_chart(
        tables=[table],
        charts=charts,
        output_dir=tmp_path,
    )

    assert len(files) == 1

    assert (
        tmp_path
        / "figure_1.png"
    ).exists()


def test_same_figure_requires_common_x_axis(
    tmp_path,
):
    table = measurement_table(
        table_id=1,
        dataframe=pd.DataFrame(
            {
                "P": [100, 200],
                "U": [100, 200],
                "I": [1, 2],
                "n": [1500, 1400],
            }
        ),
        units={},
    )

    charts = [
        chart(
            figure_id=1,
            table_id=1,
            x="P",
            y="I",
        ),
        chart(
            figure_id=1,
            table_id=1,
            x="U",
            y="n",
        ),
    ]

    with pytest.raises(
        ValueError,
        match="common x-axis",
    ):
        generate_chart(
            tables=[table],
            charts=charts,
            output_dir=tmp_path,
        )


def test_numeric_filter_generates_chart(
    tmp_path,
):
    table = measurement_table(
        table_id=1,
        dataframe=pd.DataFrame(
            {
                "U": [100, 150, 100, 150],
                "n": [1000, 1100, 1200, 1300],
                "Ts": [0.5, 0.5, 1.0, 1.0],
            }
        ),
        units={
            "U": "V",
            "n": "rpm",
            "Ts": None,
        },
    )

    charts = [
        chart(
            figure_id=1,
            table_id=1,
            x="U",
            y="n",
            filter_column="Ts",
            filter_value=0.5,
            label="Ts = 0.5",
        )
    ]

    files = generate_chart(
        tables=[table],
        charts=charts,
        output_dir=tmp_path,
    )

    assert len(files) == 1
    assert files[0].exists()


def test_filter_without_matching_rows_raises_error(
    tmp_path,
):
    table = measurement_table(
        table_id=1,
        dataframe=pd.DataFrame(
            {
                "U": [100, 150],
                "n": [1000, 1100],
                "Ts": [0.5, 0.5],
            }
        ),
        units={},
    )

    charts = [
        chart(
            figure_id=1,
            table_id=1,
            x="U",
            y="n",
            filter_column="Ts",
            filter_value=999,
        )
    ]

    with pytest.raises(
        ValueError,
        match="No valid data for chart",
    ):
        generate_chart(
            tables=[table],
            charts=charts,
            output_dir=tmp_path,
        )


def test_missing_filter_value_raises_error(
    tmp_path,
):
    table = measurement_table(
        table_id=1,
        dataframe=pd.DataFrame(
            {
                "U": [100, 150],
                "n": [1000, 1100],
                "Ts": [0.5, 1.0],
            }
        ),
        units={},
    )

    charts = [
        chart(
            figure_id=1,
            table_id=1,
            x="U",
            y="n",
            filter_column="Ts",
            filter_value=None,
        )
    ]

    with pytest.raises(
        ValueError,
        match="filter_value is missing",
    ):
        generate_chart(
            tables=[table],
            charts=charts,
            output_dir=tmp_path,
        )


def test_logarithmic_y_scale_rejects_non_positive_values(
    tmp_path,
):
    table = measurement_table(
        table_id=1,
        dataframe=pd.DataFrame(
            {
                "U": [100, 200, 300],
                "I": [1.0, 0.0, 3.0],
            }
        ),
        units={},
    )

    charts = [
        chart(
            figure_id=1,
            table_id=1,
            x="U",
            y="I",
            y_scale="log",
        )
    ]

    with pytest.raises(
        ValueError,
        match="Cannot use logarithmic scale",
    ):
        generate_chart(
            tables=[table],
            charts=charts,
            output_dir=tmp_path,
        )