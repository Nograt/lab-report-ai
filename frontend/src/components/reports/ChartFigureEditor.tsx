import type {
  ReportChart,
  ReportState,
} from "@/lib/api/reports";

import { ChartEditor } from "@/components/reports/ChartEditor";

type ChartFigureEditorProps = {
  figureId: number;
  charts: {
    chart: ReportChart;
    index: number;
  }[];
  tables: NonNullable<ReportState["measurement_tables"]>;
  onChange: (
    index: number,
    chart: ReportChart,
  ) => void;
};

export function ChartFigureEditor({
  figureId,
  charts,
  tables,
  onChange,
}: ChartFigureEditorProps) {
  const firstChart = charts[0]?.chart;

  if (!firstChart) {
    return null;
  }

  return (
    <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white">
      <div className="border-b border-neutral-200 px-6 py-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="font-mono text-xs text-neutral-400">
              WYKRES / {figureId}
            </p>

            <h3 className="mt-2 text-lg font-medium text-neutral-950">
              {charts.length === 1
                ? ""
                : `${charts.length} serie danych`}
            </h3>
          </div>

          <div className="font-mono text-xs text-neutral-400">
            TABELA / {firstChart.table_id}
          </div>
        </div>
      </div>

      <div className="space-y-4 bg-neutral-50/50 p-4 sm:p-6">
        {charts.map(({ chart, index }, seriesIndex) => (
          <div
            key={`${chart.figure_id}-${index}`}
            className="rounded-lg border border-neutral-200 bg-white"
          >
            <div className="border-b border-neutral-100 px-5 py-4">
              <p className="font-mono text-xs text-neutral-400">
                SERIA / {seriesIndex + 1}
              </p>

              <p className="mt-1 text-sm font-medium text-neutral-900">
                {chart.label || `${chart.y} = f(${chart.x})`}
              </p>
            </div>

            <ChartEditor
              chart={chart}
              tables={tables}
              onChange={(updatedChart) =>
                onChange(index, updatedChart)
              }
            />
          </div>
        ))}
      </div>
    </div>
  );
}