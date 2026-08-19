import type {
  ReportChart,
  ReportState,
} from "@/lib/api/reports";

type ChartEditorProps = {
  chart: ReportChart;
  tables: NonNullable<ReportState["measurement_tables"]>;
  onChange: (chart: ReportChart) => void;
};

export function ChartEditor({
  chart,
  tables,
  onChange,
}: ChartEditorProps) {
  const table = tables.find(
    (table) => table.table_id === chart.table_id,
  );

  const columns = table?.columns ?? [];

  function update<K extends keyof ReportChart>(
    key: K,
    value: ReportChart[K],
  ) {
    onChange({
      ...chart,
      [key]: value,
    });
  }

  return (
    <div>

      <div className="grid gap-6 p-6 md:grid-cols-2">
        {/* X */}
        <div>
          <label className="text-sm font-medium text-neutral-900">
            Oś X
          </label>

          <select
            value={chart.x}
            onChange={(event) =>
              update("x", event.target.value)
            }
            className="
              mt-2 w-full rounded-lg border border-neutral-300
              bg-white px-3 py-2.5 text-sm
              outline-none
              focus:border-orange-400
              focus:ring-2 focus:ring-orange-100
            "
          >
            {columns.map((column) => (
              <option key={column} value={column}>
                {column}
              </option>
            ))}
          </select>
        </div>

        {/* Y */}
        <div>
          <label className="text-sm font-medium text-neutral-900">
            Oś Y
          </label>

          <select
            value={chart.y}
            onChange={(event) =>
              update("y", event.target.value)
            }
            className="
              mt-2 w-full rounded-lg border border-neutral-300
              bg-white px-3 py-2.5 text-sm
              outline-none
              focus:border-orange-400
              focus:ring-2 focus:ring-orange-100
            "
          >
            {columns.map((column) => (
              <option key={column} value={column}>
                {column}
              </option>
            ))}
          </select>
        </div>

        {/* X scale */}
        <div>
          <label className="text-sm font-medium text-neutral-900">
            Skala X
          </label>

          <select
            value={chart.x_scale}
            onChange={(event) =>
              update(
                "x_scale",
                event.target.value as "linear" | "log",
              )
            }
            className="
              mt-2 w-full rounded-lg border border-neutral-300
              bg-white px-3 py-2.5 text-sm
              outline-none
              focus:border-orange-400
              focus:ring-2 focus:ring-orange-100
            "
          >
            <option value="linear">Liniowa</option>
            <option value="log">Logarytmiczna</option>
          </select>
        </div>

        {/* Y scale */}
        <div>
          <label className="text-sm font-medium text-neutral-900">
            Skala Y
          </label>

          <select
            value={chart.y_scale}
            onChange={(event) =>
              update(
                "y_scale",
                event.target.value as "linear" | "log",
              )
            }
            className="
              mt-2 w-full rounded-lg border border-neutral-300
              bg-white px-3 py-2.5 text-sm
              outline-none
              focus:border-orange-400
              focus:ring-2 focus:ring-orange-100
            "
          >
            <option value="linear">Liniowa</option>
            <option value="log">Logarytmiczna</option>
          </select>
        </div>
      </div>

      {/* Opcje */}
      <div className="flex flex-wrap gap-6 border-t border-neutral-200 px-6 py-5">
        <label className="flex cursor-pointer items-center gap-2 text-sm text-neutral-700">
          <input
            type="checkbox"
            checked={chart.connect_points}
            onChange={(event) =>
              update(
                "connect_points",
                event.target.checked,
              )
            }
            className="accent-orange-500"
          />

          Łącz punkty
        </label>

        <label className="flex cursor-pointer items-center gap-2 text-sm text-neutral-700">
          <input
            type="checkbox"
            checked={chart.show_grid}
            onChange={(event) =>
              update(
                "show_grid",
                event.target.checked,
              )
            }
            className="accent-orange-500"
          />

          Siatka
        </label>

        <label className="flex cursor-pointer items-center gap-2 text-sm text-neutral-700">
          <input
            type="checkbox"
            checked={chart.show_legend}
            onChange={(event) =>
              update(
                "show_legend",
                event.target.checked,
              )
            }
            className="accent-orange-500"
          />

          Legenda
        </label>
      </div>
    </div>
  );
}