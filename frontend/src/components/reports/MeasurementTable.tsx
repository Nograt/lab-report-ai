import type { ReportDataTable } from "@/lib/api/reports";

type MeasurementTableProps = {
  table: ReportDataTable;
};

export function MeasurementTable({
  table,
}: MeasurementTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white">
      <div className="border-b border-neutral-200 px-6 py-5">
        <p className="font-mono text-xs text-neutral-400">
          TABELA / {table.table_id}
        </p>

        <h2 className="mt-2 font-medium text-neutral-950">
          {table.title ?? `Tabela ${table.table_id}`}
        </h2>

        <p className="mt-1 text-xs text-neutral-500">
          Arkusz: {table.sheet_name}
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-neutral-200 bg-neutral-50">
              {table.columns.map((column) => (
                <th
                  key={column}
                  className="whitespace-nowrap px-4 py-3 text-left font-medium text-neutral-700"
                >
                  <div>{column}</div>

                  {table.units[column] && (
                    <div className="mt-1 font-mono text-[10px] font-normal text-neutral-400">
                      [{table.units[column]}]
                    </div>
                  )}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {table.rows.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className="border-b border-neutral-100 last:border-b-0"
              >
                {table.columns.map((column) => (
                  <td
                    key={column}
                    className="whitespace-nowrap px-4 py-3 text-neutral-700"
                  >
                    {row[column] === null ||
                    row[column] === undefined
                      ? "—"
                      : String(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}