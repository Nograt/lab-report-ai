import type { MissingParameter } from "@/lib/api/reports";

type ParameterFieldProps = {
  parameter: MissingParameter;
  value: string;
  onChange: (value: string) => void;
};

export function ParameterField({
  parameter,
  value,
  onChange,
}: ParameterFieldProps) {
  return (
    <div className="rounded-xl border border-neutral-200 bg-white p-6">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="font-medium text-neutral-950">
              {parameter.name}
            </h2>

            <span className="font-mono text-sm text-orange-600">
              {parameter.symbol}
            </span>
          </div>

          {parameter.description && (
            <p className="mt-2 text-sm leading-6 text-neutral-500">
              {parameter.description}
            </p>
          )}
        </div>

        <div className="flex items-center gap-3">
          <input
            type="text"
            value={value}
            onChange={(event) => onChange(event.target.value)}
            placeholder="Wartość"
            className="
              w-40 rounded-lg border border-neutral-300
              bg-white px-3 py-2.5 text-sm
              outline-none
              focus:border-orange-400
              focus:ring-2
              focus:ring-orange-100
            "
          />

          {parameter.unit && (
            <span className="min-w-10 font-mono text-sm text-neutral-500">
              {parameter.unit}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}