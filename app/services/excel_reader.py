import pandas as pd


def parse_column(column: str) -> tuple[str, str | None]:
    column = str(column)

    if "[" in column and "]" in column:
        name = column.split("[")[0].strip()
        unit = column.split("[")[1].split("]")[0].strip()

        return name, unit

    return column.strip(), None



def read_meansurements(file_path: str)-> tuple[pd.DataFrame, dict[str, str|None]]:
    try:
        df = pd.read_excel(file_path,decimal=",")
    except Exception as error:
        raise Exception(f"Problem with loading data: {error}")
    
    units = {}
    new_columns = []
    
    for column in df.columns:
        name,unit = parse_column(column)
        
        new_columns.append(name)
        units[name] = unit
        
    df.columns = new_columns
    
    return df, units
        


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
  
