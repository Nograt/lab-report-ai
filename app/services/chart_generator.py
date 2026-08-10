import matplotlib.pyplot as plt
from collections import defaultdict
from app.services.excel_reader import read_meansurements, get_chart_data
from app.services.instruction_parser import parse_report_instruction
from matplotlib.ticker import MaxNLocator
from app.schemas.chart import ChartSpecification


def create_chart_specifications(ai_specifications):
    charts = []
    
    for ai_chart in ai_specifications.charts:
        chart = ChartSpecification(figure_id=ai_chart.figure_id, x=ai_chart.x,y=ai_chart.y)
        charts.append(chart)
        
    return charts

def generate_chart(df, units, charts):
    
    grouped_charts = defaultdict(list)
    
    for chart in charts:
        grouped_charts[chart.figure_id].append(chart)
        
    for figure_id, charts in grouped_charts.items():
        
    # wspólny X bierzemy z pierwszej charakterystyki
        shared_x = charts[0].x

        for chart in charts:
            if chart.x != shared_x:
                raise ValueError(
                    f"Figure {figure_id} wymaga wspólnej osi X, "
                    f"ale znaleziono {shared_x} oraz {chart.x}"
                )

        fig, ax = plt.subplots()
        
        
        ax.set_xscale(charts[0].x_scale)

        # robimy miejsce na dodatkowe osie po prawej
        if len(charts) > 1:
            fig.subplots_adjust(right=0.75)

        axes = [ax]

        # tworzymy dodatkowe osie Y
        for i in range(1, len(charts)):
            new_ax = ax.twinx()

            # druga oś jest normalnie po prawej,
            # każdą kolejną przesuwamy dalej
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
        
    plt.show()
