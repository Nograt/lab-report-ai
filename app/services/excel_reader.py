from dataclasses import dataclass
import pandas as pd
from typing import BinaryIO
from app.schemas.measurement import MeasurementTableInfo

@dataclass
class MeasurementTableData:
    table_id: int
    title: str | None
    sheet_name: str
    dataframe: pd.DataFrame
    units: dict[str, str | None]
    
    
def create_measurement_table_infos(
    tables: list[MeasurementTableData],
) -> list[MeasurementTableInfo]:

    return [
        MeasurementTableInfo(
            table_id=table.table_id,
            title=table.title,
            sheet_name=table.sheet_name,
            columns=table.dataframe.columns.tolist(),
            units=table.units,
        )
        for table in tables
    ]

def parse_column(column: str) -> tuple[str, str | None]:
    column = str(column)

    if "[" in column and "]" in column:
        name = column.split("[")[0].strip()
        unit = column.split("[")[1].split("]")[0].strip()

        return name, unit

    return column.strip(), None

KNOWN_UNITS = {
    "V",
    "mV",
    "kV",

    "A",
    "mA",
    "µA",
    "uA",

    "W",
    "mW",
    "kW",
    "MW",

    "VA",
    "var",
    "kvar",

    "Ω",
    "kΩ",
    "MΩ",
    "ohm",

    "N",
    "mN",

    "Nm",
    "N·m",
    "N*m",
    "mNm",

    "Hz",
    "kHz",
    "MHz",

    "s",
    "ms",
    "min",

    "rpm",
    "obr/min",
    "obr./min",
    "1/min",

    "rad/s",

    "%",
    "°C",

    "m",
    "cm",
    "mm",

    "m/s",
    "m/s²",
}


def normalize_unit(value) -> str | None:
    """
    Zamienia wartość komórki z jednostką na string lub None.

    Przykłady:
    V       -> "V"
    obr/min -> "obr/min"
    -       -> None
    NaN     -> None
    """

    if pd.isna(value):
        return None

    value = str(value).strip()

    if value in {"", "-", "—", "–"}:
        return None

    return value


def is_unit_value(value) -> bool:
    """
    Sprawdza, czy komórka wygląda jak jednostka.
    """

    if pd.isna(value):
        return True

    value = str(value).strip()

    if value in {"", "-", "—", "–"}:
        return True

    return value in KNOWN_UNITS


def has_unit_row(df: pd.DataFrame) -> bool:

    if df.empty:
        return False

    first_row = df.iloc[0]

    values = [
        value
        for value in first_row.tolist()
        if not pd.isna(value)
    ]

    if not values:
        return False

    unit_count = sum(
        is_unit_value(value)
        for value in values
    )

    ratio = unit_count / len(values)

    return ratio >= 0.6


def convert_numeric_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.copy()

    for column in df.columns:

        original_non_null = df[column].notna().sum()

        converted = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        converted_non_null = converted.notna().sum()

        if converted_non_null == original_non_null:
            df[column] = converted

    return df



def read_measurement_tables(
    file: str | BinaryIO,
) -> list[MeasurementTableData]:

    if hasattr(file, "seek"):
        file.seek(0)

    excel_file = pd.ExcelFile(file)

    measurement_tables: list[MeasurementTableData] = []

    next_table_id = 1

    for sheet_name in excel_file.sheet_names:

        df = pd.read_excel(
            excel_file,
            sheet_name=sheet_name,
            decimal=",",
        )

        df = df.dropna(
            axis=0,
            how="all",
        )

        df = df.dropna(
            axis=1,
            how="all",
        )

        if df.empty:
            continue


        normalized_columns: list[str] = []
        units: dict[str, str | None] = {}

        for column in df.columns:

            name, unit = parse_column(
                str(column)
            )

            normalized_columns.append(name)
            units[name] = unit

        df.columns = normalized_columns


        if has_unit_row(df):

            unit_row = df.iloc[0]

            for column in df.columns:

                if units[column] is not None:
                    continue

                units[column] = normalize_unit(
                    unit_row[column]
                )

    
            df = df.iloc[1:].reset_index(
                drop=True
            )

        else:
            df = df.reset_index(
                drop=True
            )

        df = convert_numeric_columns(df)

        measurement_tables.append(
            MeasurementTableData(
                table_id=next_table_id,
                title=sheet_name,
                sheet_name=sheet_name,
                dataframe=df,
                units=units,
            )
        )

        next_table_id += 1

    if not measurement_tables:
        raise ValueError(
            "Excel file does not contain any measurement tables."
        )

    return measurement_tables





def get_chart_data(df: pd.DataFrame, x_column: str, y_column: str)-> tuple[pd.Series, pd.Series]:
    
    if x_column not in df.columns:
        raise ValueError(f"Unable to find {x_column} in DataFrame columns: {df.columns}")
    
    if y_column not in df.columns:
            raise ValueError(f"Unable to find {y_column} in DataFrame columns: {df.columns}")
        
    try:
        x = pd.to_numeric(df[x_column], errors="raise")
        y = pd.to_numeric(df[y_column], errors="raise")

    except ValueError:
        raise ValueError(
            f"Kolumny {x_column} lub {y_column} "
            "zawierają wartości, które nie są liczbami."
        )
        
    return (x,y)

def get_measurement_table(
    tables: list[MeasurementTableData],
    table_id: int,
) -> MeasurementTableData:

    for table in tables:
        if table.table_id == table_id:
            return table

    raise ValueError(
        f"Measurement table with table_id={table_id} does not exist."
    )
  
def read_meansurements(
    file: str | BinaryIO,
) -> tuple[pd.DataFrame, dict[str, str | None]]:

    tables = read_measurement_tables(file)

    first_table = tables[0]

    return (
        first_table.dataframe.copy(),
        first_table.units.copy(),
    )
    
    
def read_completed_measurement_tables(
    file: str | BinaryIO,
    metadata: list[dict],
) -> list[MeasurementTableData]:

    if hasattr(file, "seek"):
        file.seek(0)

    excel_file = pd.ExcelFile(file)

    tables: list[MeasurementTableData] = []

    for table_metadata in metadata:

        table_id = table_metadata["table_id"]
        sheet_name = table_metadata["sheet_name"]

        if sheet_name not in excel_file.sheet_names:
            raise ValueError(
                f"Sheet '{sheet_name}' for table_id={table_id} "
                "does not exist in completed measurements workbook."
            )

        df = pd.read_excel(
            excel_file,
            sheet_name=sheet_name,
        )

        df = df.dropna(
            axis=0,
            how="all",
        )

        df = df.dropna(
            axis=1,
            how="all",
        )

        df = convert_numeric_columns(df)

        expected_columns = table_metadata.get(
            "columns",
            [],
        )

        if expected_columns:
            missing_columns = [
                column
                for column in expected_columns
                if column not in df.columns
            ]

            if missing_columns:
                raise ValueError(
                    f"Completed table_id={table_id} is missing columns: "
                    f"{missing_columns}"
                )

        tables.append(
            MeasurementTableData(
                table_id=table_id,
                title=table_metadata.get("title"),
                sheet_name=sheet_name,
                dataframe=df,
                units=table_metadata.get(
                    "units",
                    {},
                ),
            )
        )

    return tables   