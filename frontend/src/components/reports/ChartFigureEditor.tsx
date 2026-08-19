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

     reportId: string;
    imageVersion: number;
};

export function ChartFigureEditor({
  reportId,
  figureId,
  imageVersion,
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
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-mono text-xs text-neutral-400">
            WYKRES / {figureId}
          </p>

          {charts.length > 1 && (
            <h3 className="mt-2 text-lg font-medium text-neutral-950">
              {charts.length} serie danych
            </h3>
          )}
        </div>

        <div className="font-mono text-xs text-neutral-400">
          TABELA / {firstChart.table_id}
        </div>
      </div>
    </div>

    <div className="grid gap-6 bg-neutral-50/50 p-4 sm:p-6 xl:grid-cols-[minmax(0,1fr)_minmax(420px,0.8fr)]">
      <div>
        <div className="sticky top-24">
          <p className="mb-3 font-mono text-xs text-neutral-400">
            PODGLĄD
          </p>

          <div className="overflow-hidden rounded-lg border border-neutral-200 bg-white">
            <div className="flex min-h-[420px] items-center justify-center p-4">
              <img
                src={`/backend/reports/${reportId}/charts/${figureId}/image?version=${imageVersion}`}
                alt={`Wykres ${figureId}`}
                className="max-h-[560px] max-w-full object-contain"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <p className="font-mono text-xs text-neutral-400">
          USTAWIENIA
        </p>

        {charts.map(
          ({ chart, index }, seriesIndex) => (
            <div
              key={`${chart.figure_id}-${index}`}
              className="overflow-hidden rounded-lg border border-neutral-200 bg-white"
            >
              <div className="border-b border-neutral-100 px-5 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-mono text-xs text-neutral-400">
                      SERIA / {seriesIndex + 1}
                    </p>

                    <p className="mt-1 text-sm font-medium text-neutral-900">
                      {chart.label ||
                        `${chart.y} = f(${chart.x})`}
                    </p>
                  </div>

                  <div className="font-mono text-[11px] text-neutral-400">
                    {chart.x} → {chart.y}
                  </div>
                </div>
              </div>

              <ChartEditor
                chart={chart}
                tables={tables}
                onChange={(updatedChart) =>
                  onChange(index, updatedChart)
                }
              />
            </div>
          ),
        )}
      </div>
    </div>
  </div>
);
}