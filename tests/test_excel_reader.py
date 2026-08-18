from io import BytesIO

import pandas as pd
import pytest

from app.services.excel_reader import (
    create_measurement_table_infos,
    read_measurement_tables,
)


def create_excel(
    sheets: dict[str, pd.DataFrame],
) -> BytesIO:
    file = BytesIO()

    with pd.ExcelWriter(
        file,
        engine="openpyxl",
    ) as writer:
        for sheet_name, dataframe in sheets.items():
            dataframe.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False,
            )

    file.seek(0)

    return file


def test_reads_single_measurement_table():
    excel = create_excel(
        {
            "Bieg jałowy": pd.DataFrame(
                {
                    "U [V]": [100, 200],
                    "I [A]": [1.0, 2.0],
                }
            )
        }
    )

    tables = read_measurement_tables(excel)

    assert len(tables) == 1

    table = tables[0]

    assert table.table_id == 1
    assert table.title == "Bieg jałowy"
    assert table.sheet_name == "Bieg jałowy"

    assert table.dataframe.columns.tolist() == [
        "U",
        "I",
    ]

    assert table.units == {
        "U": "V",
        "I": "A",
    }


def test_reads_multiple_excel_sheets():
    excel = create_excel(
        {
            "Bieg jałowy": pd.DataFrame(
                {
                    "U [V]": [100, 200],
                    "I [A]": [1.0, 2.0],
                }
            ),
            "Obciążenie": pd.DataFrame(
                {
                    "P [W]": [100, 200],
                    "n [rpm]": [1450, 1400],
                }
            ),
        }
    )

    tables = read_measurement_tables(excel)

    assert len(tables) == 2

    assert tables[0].table_id == 1
    assert tables[0].sheet_name == "Bieg jałowy"

    assert tables[1].table_id == 2
    assert tables[1].sheet_name == "Obciążenie"


def test_reads_units_from_first_row():
    dataframe = pd.DataFrame(
        {
            "U": ["V", 100, 200],
            "I": ["A", 1.0, 2.0],
            "P": ["W", 100, 400],
        }
    )

    excel = create_excel(
        {
            "Pomiary": dataframe,
        }
    )

    tables = read_measurement_tables(excel)

    table = tables[0]

    assert table.units == {
        "U": "V",
        "I": "A",
        "P": "W",
    }

    assert len(table.dataframe) == 2

    assert table.dataframe["U"].tolist() == [
        100,
        200,
    ]


def test_preserves_named_empty_result_column():
    dataframe = pd.DataFrame(
        {
            "U [V]": [100, 200],
            "I [A]": [1.0, 2.0],
            "P [W]": [None, None],
        }
    )

    excel = create_excel(
        {
            "Pomiary": dataframe,
        }
    )

    tables = read_measurement_tables(excel)

    table = tables[0]

    assert table.dataframe.columns.tolist() == [
        "U",
        "I",
        "P",
    ]

    assert table.dataframe["P"].isna().all()


def test_removes_empty_unnamed_column():
    dataframe = pd.DataFrame(
        {
            "U [V]": [100, 200],
            "Unnamed: 3": [None, None],
            "I [A]": [1.0, 2.0],
        }
    )

    excel = create_excel(
        {
            "Pomiary": dataframe,
        }
    )

    tables = read_measurement_tables(excel)

    table = tables[0]

    assert table.dataframe.columns.tolist() == [
        "U",
        "I",
    ]


def test_measurement_table_info_detects_populated_columns():
    dataframe = pd.DataFrame(
        {
            "U [V]": [100, 200],
            "I [A]": [1.0, 2.0],
            "P [W]": [None, None],
        }
    )

    excel = create_excel(
        {
            "Pomiary": dataframe,
        }
    )

    tables = read_measurement_tables(excel)

    infos = create_measurement_table_infos(
        tables
    )

    assert len(infos) == 1

    info = infos[0]

    assert info.column_has_values == {
        "U": True,
        "I": True,
        "P": False,
    }


def test_empty_workbook_raises_error():
    excel = create_excel(
        {
            "Pusty": pd.DataFrame(),
        }
    )

    with pytest.raises(
        ValueError,
        match="does not contain any measurement tables",
    ):
        read_measurement_tables(excel)