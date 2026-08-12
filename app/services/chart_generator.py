import matplotlib.pyplot as plt
from collections import defaultdict
from app.services.excel_reader import (
    MeasurementTableData,
    get_measurement_table,
    get_chart_data
)
from app.services.instruction_parser import parse_report_instruction
from matplotlib.ticker import MaxNLocator
from app.schemas.chart import ChartSpecification
from pathlib import Path
from app.schemas.report import ReportSpecification

def create_multi_table_chart_specifications(
    specification: ReportSpecification,
    tables: list[MeasurementTableData],
) -> list[ChartSpecification]:

    charts: list[ChartSpecification] = []

    used_figure_ids: set[int] = set()

    for section in specification.sections:

        table = get_measurement_table(
            tables=tables,
            table_id=section.table_id,
        )

        available_columns = set(
            table.dataframe.columns
        )

        section_chart_ids = set(
            section.chart_figure_ids
        )

        for parsed_chart in specification.charts:

            if parsed_chart.figure_id not in section_chart_ids:
                continue

            if parsed_chart.figure_id in used_figure_ids:
                raise ValueError(
                    f"Chart figure_id={parsed_chart.figure_id} "
                    "is assigned to more than one report section."
                )

            if parsed_chart.x not in available_columns:
                raise ValueError(
                    f"Chart figure_id={parsed_chart.figure_id} "
                    f"uses x column '{parsed_chart.x}', "
                    f"but table_id={table.table_id} "
                    f"contains columns: "
                    f"{table.dataframe.columns.tolist()}"
                )

            if parsed_chart.y not in available_columns:
                raise ValueError(
                    f"Chart figure_id={parsed_chart.figure_id} "
                    f"uses y column '{parsed_chart.y}', "
                    f"but table_id={table.table_id} "
                    f"contains columns: "
                    f"{table.dataframe.columns.tolist()}"
                )

            charts.append(
                ChartSpecification(
                    figure_id=parsed_chart.figure_id,
                    x=parsed_chart.x,
                    y=parsed_chart.y,
                )
            )

            used_figure_ids.add(
                parsed_chart.figure_id
            )

    expected_figure_ids = {
        chart.figure_id
        for chart in specification.charts
    }

    missing_figure_ids = (
        expected_figure_ids - used_figure_ids
    )

    if missing_figure_ids:
        raise ValueError(
            "Some charts are not assigned to any report section: "
            f"{sorted(missing_figure_ids)}"
        )

    return charts


def create_chart_specifications(ai_specifications, df):
    charts = []

    for ai_chart in ai_specifications.charts:
        x = match_column_name(
            ai_chart.x,
            df
        )

        y = match_column_name(
            ai_chart.y,
            df
        )

        chart = ChartSpecification(
            figure_id=ai_chart.figure_id,
            x=x,
            y=y,
        )

        charts.append(chart)

    return charts
        

def match_column_name(column_name:str, df) -> str:
    if column_name in df:
        return column_name
    
    matches = [
        col for col in df.columns if col.lower() == column_name.lower()
    ]
    
    if len(matches) == 1:
        return matches[0]
    
    raise ValueError(
        f"Unable to find column '{column_name}'. "
        f"Available columns: {df.columns.tolist()}")
    

def generate_chart(df, units, charts, output_dir: Path):
    
    grouped_charts = defaultdict(list)
    
    output_dir.mkdir(parents=True,exist_ok=True)
    
    generated_files = []
    
    for chart in charts:
        grouped_charts[chart.figure_id].append(chart)
        
    for figure_id, charts in grouped_charts.items():
        
        shared_x = charts[0].x

        for chart in charts:
            if chart.x != shared_x:
                raise ValueError(
                    f"Figure {figure_id} wymaga wspólnej osi X, "
                    f"ale znaleziono {shared_x} oraz {chart.x}"
                )

        fig, ax = plt.subplots()
        
        
        ax.set_xscale(charts[0].x_scale)

        if len(charts) > 1:
            fig.subplots_adjust(right=0.75)

        axes = [ax]

        for i in range(1, len(charts)):
            new_ax = ax.twinx()

            if i > 1:
                new_ax.spines.right.set_position(
                    ("axes", 1 + 0.2 * (i - 1))
                )

            axes.append(new_ax)

        lines = []
        
        title =  ""
        
        colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

        for index, (chart, current_ax) in enumerate(zip(charts, axes)):

            x, y = get_chart_data(
                    df,
                    chart.x,
                    chart.y
                )
            
            if chart.y_scale == "log" and (y <= 0).any():
                raise ValueError(f"Nie można użyć skali logarytmicznej dla {chart.y}, ponieważ występują wartości <= 0.")
            
            current_ax.set_yscale(chart.y_scale)
            
            if len(title) == 0:
                title += chart.y
            else:
                title += f", {chart.y}"
            
            color = colors[index % len(colors)]
            if chart.connect_points:
                line, = current_ax.plot(x,y,marker="o",color=color,label=f"{chart.y}({chart.x})")
            else:
                line = current_ax.scatter(x,y,color=color,label=f"{chart.y}({chart.x})")
            
            if chart.y_scale == "linear" and y.min() >= 0:
                locator = MaxNLocator(nbins=6)

                ticks = locator.tick_values(0, y.max())
                max_tick = ticks[-1]

                current_ax.set_ylim(0, max_tick)
                current_ax.set_yticks(ticks)


            y_unit = units.get(chart.y)

            if y_unit is None:
                y_label = f"{chart.y} [-]"
            else:
                y_label = f"{chart.y} [{y_unit}]"

            current_ax.set_ylabel(y_label, color=color)
            current_ax.tick_params(
                    axis="y",
                    colors=color
                )

            lines.append(line)

        
        if "," in title:
            ax.set_title(f"Charakterystyki {title} w funkcji {shared_x} ")
        else:
            ax.set_title(f"Charakterystyka {title} w funkcji {shared_x} ")

    
        if chart.show_grid:
            ax.grid()
            
        
        if chart.show_legend:
            ax.legend(
                handles=lines
            )
        
        x_unit = units.get(shared_x)
        
        if x_unit is None:
            ax.set_xlabel(f"{shared_x} [-]")
        else:
            ax.set_xlabel(f"{shared_x} [{x_unit}]")
            
        file_path = output_dir / f"figure_{figure_id}.png"
        
        fig.savefig(file_path,dpi=150,bbox_inches="tight")
        
        plt.close(fig)
        
        generated_files.append(file_path)
        
    return generated_files

def generate_multi_table_charts(
    specification: ReportSpecification,
    tables: list[MeasurementTableData],
    charts: list[ChartSpecification],
    output_dir: Path,
) -> list[Path]:

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated_files: list[Path] = []

    for section in specification.sections:

        table = get_measurement_table(
            tables=tables,
            table_id=section.table_id,
        )

        section_charts = [
            chart
            for chart in charts
            if chart.figure_id
            in section.chart_figure_ids
        ]

        if not section_charts:
            continue

        files = generate_chart(
            df=table.dataframe,
            units=table.units,
            charts=section_charts,
            output_dir=output_dir,
        )

        generated_files.extend(files)

    return generated_files
        
        

