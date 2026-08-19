"use client";
import { prepareInstruction } from "@/lib/api/reports";
import { useState } from "react";
import { ParameterField } from "@/components/reports/ParameterField";
import { FileUploadCard } from "@/components/reports/FileUploadCard";

import type {
  MissingParameter,
  PrepareInstructionResponse,
} from "@/lib/api/reports";

export default function NewReportPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [instructionFile, setInstructionFile] = useState<File | null>(null);

  const [measurementsFile, setMeasurementsFile] = useState<File | null>(null);

  const canContinue = instructionFile !== null && measurementsFile !== null;

  const [step, setStep] = useState<1 | 2>(1);

  const [preparedInstruction, setPreparedInstruction] =
    useState<PrepareInstructionResponse | null>(null);

  const [parameterValues, setParameterValues] = useState<
    Record<string, string>
  >({});

  async function handleContinue() {
    if (!instructionFile || !measurementsFile) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const result = await prepareInstruction(
        instructionFile,
        measurementsFile,
      );

      setPreparedInstruction(result);

      const initialValues = Object.fromEntries(
        result.missing_parameters.map((parameter) => [parameter.symbol, ""]),
      );

      setParameterValues(initialValues);
      setStep(2);
    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError("Wystąpił nieoczekiwany błąd.");
      }
    } finally {
      setIsLoading(false);
    }
  }
  if (step === 2 && preparedInstruction) {
    return (
      <main className="min-h-[calc(100vh-4rem)]">
        <section className="mx-auto max-w-4xl px-6 py-16">
          <div>
            <div className="font-mono text-xs font-medium uppercase tracking-[0.18em] text-orange-600">
              02 / Parametry
            </div>

            <h1 className="mt-4 text-4xl font-semibold tracking-tight text-neutral-950">
              Uzupełnij brakujące dane
            </h1>

            <p className="mt-4 text-lg leading-8 text-neutral-600">
              Instrukcja została przeanalizowana. Uzupełnij parametry, których
              nie udało się jednoznacznie odczytać.
            </p>
          </div>

          <div className="mt-10 space-y-4">
            {preparedInstruction.missing_parameters.length === 0 ? (
              <div className="rounded-xl border border-neutral-200 bg-white p-6">
                <p className="text-sm text-neutral-600">
                  Nie znaleziono brakujących parametrów.
                </p>
              </div>
            ) : (
              preparedInstruction.missing_parameters.map((parameter) => (
                <ParameterField
                  key={parameter.symbol}
                  parameter={parameter}
                  value={parameterValues[parameter.symbol] ?? ""}
                  onChange={(value) =>
                    setParameterValues((current) => ({
                      ...current,
                      [parameter.symbol]: value,
                    }))
                  }
                />
              ))
            )}
          </div>

          <div className="mt-8 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="rounded-lg border border-neutral-300 bg-white px-5 py-3 text-sm font-medium text-neutral-700 hover:bg-neutral-50"
            >
              Wstecz
            </button>

            <button
              type="button"
              className="rounded-lg bg-orange-500 px-5 py-3 text-sm font-medium text-white hover:bg-orange-600"
            >
              Dalej
            </button>
          </div>
        </section>
      </main>
    );
  }
  return (
    <main className="min-h-[calc(100vh-4rem)]">
      <section className="mx-auto max-w-7xl px-6 py-16">
        <div className="max-w-3xl">
          <div className="font-mono text-xs font-medium uppercase tracking-[0.18em] text-orange-600">
            01 / Pliki
          </div>

          <h1 className="mt-4 text-4xl font-semibold tracking-tight text-neutral-950">
            Nowe sprawozdanie
          </h1>

          <p className="mt-4 text-lg leading-8 text-neutral-600">
            Dodaj instrukcję laboratoryjną oraz arkusz z wynikami pomiarów.
          </p>
        </div>

        <div className="mt-12 grid gap-6 lg:grid-cols-2">
          <FileUploadCard
            label="INSTRUKCJA / PDF"
            title="Instrukcja laboratoryjna"
            description="Dodaj plik PDF zawierający instrukcję do ćwiczenia."
            accept=".pdf,application/pdf"
            file={instructionFile}
            onChange={setInstructionFile}
          />

          <FileUploadCard
            label="POMIARY / XLSX"
            title="Dane pomiarowe"
            description="Dodaj arkusz Excel zawierający wyniki pomiarów."
            accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            file={measurementsFile}
            onChange={setMeasurementsFile}
          />
        </div>

        <div className="mt-8 flex justify-end">
          <button
            type="button"
            disabled={!canContinue || isLoading}
            onClick={handleContinue}
            className="
    rounded-lg px-5 py-3 text-sm font-medium
    disabled:cursor-not-allowed
    disabled:bg-neutral-200
    disabled:text-neutral-400
    enabled:bg-orange-500
    enabled:text-white
    enabled:hover:bg-orange-600
  "
          >
            {isLoading ? "Analizowanie..." : "Dalej"}
          </button>

          {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
        </div>
      </section>
    </main>
  );
}
