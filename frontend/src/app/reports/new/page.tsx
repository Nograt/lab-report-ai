"use client";
import { ParameterField } from "@/components/reports/ParameterField";
import { FileUploadCard } from "@/components/reports/FileUploadCard";
import { useEffect, useState } from "react";

import { getSubjects } from "@/lib/api/subjects";
import type { Subject } from "@/lib/api/subjects";
import type {
  MissingParameter,
  PrepareInstructionResponse,
} from "@/lib/api/reports";

import { useRouter } from "next/navigation";

import { analyzeReport, prepareInstruction } from "@/lib/api/reports";

export default function NewReportPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [instructionFile, setInstructionFile] = useState<File | null>(null);

  const [measurementsFile, setMeasurementsFile] = useState<File | null>(null);

  const canContinue = instructionFile !== null && measurementsFile !== null;

  const [step, setStep] = useState<1 | 2 | 3>(1);

  const [preparedInstruction, setPreparedInstruction] =
    useState<PrepareInstructionResponse | null>(null);

  const [parameterValues, setParameterValues] = useState<
    Record<string, string>
  >({});

  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [subjectsLoading, setSubjectsLoading] = useState(false);

  const [subjectId, setSubjectId] = useState("");
  const [executionDate, setExecutionDate] = useState("");
  const [team, setTeam] = useState("");
  const [members, setMembers] = useState("");

  useEffect(() => {
    async function loadSubjects() {
      try {
        setSubjectsLoading(true);

        const result = await getSubjects();

        setSubjects(result);
      } catch (error) {
        console.error(error);
      } finally {
        setSubjectsLoading(false);
      }
    }

    loadSubjects();
  }, []);

  const allParametersFilled =
    preparedInstruction?.missing_parameters.every(
      (parameter) => parameterValues[parameter.symbol]?.trim() !== "",
    ) ?? true;

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

  const router = useRouter();

  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  function normalizeNumber(value: string) {
  return value.trim().replace(",", ".");
}
  async function handleGenerateReport() {
    if (
      !preparedInstruction ||
      !measurementsFile ||
      !subjectId ||
      !executionDate
    ) {
      return;
    }

    try {
      setIsGenerating(true);
      setGenerationError(null);

      const parameters =
  preparedInstruction.missing_parameters.map((parameter) => ({
    name: parameter.name,
    symbol: parameter.symbol,
    value: normalizeNumber(
      parameterValues[parameter.symbol],
    ),
  }));

      const result = await analyzeReport({
        instruction: preparedInstruction.instruction,
        measurementsFile,

        subjectId,
        executionDate,

        team: team.trim() || undefined,
        members: members.trim() || undefined,

        parameters,
      });

      router.push(`/reports/${result.report_id}`);
    } catch (error) {
      if (error instanceof Error) {
        setGenerationError(error.message);
      } else {
        setGenerationError("Wystąpił nieoczekiwany błąd.");
      }
    } finally {
      setIsGenerating(false);
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
              disabled={!allParametersFilled}
              onClick={() => setStep(3)}
              className="rounded-lg px-5 py-3 text-sm font-mediumdisabled:cursor-not-alloweddisabled:bg-neutral-200disabled:text-neutral-400 enabled:bg-orange-500 enabled:text-white enabled:hover:bg-orange-600 "
            >
              Dalej
            </button>
          </div>
        </section>
      </main>
    );
  }

  if (step === 3 && preparedInstruction) {
    return (
      <main className="min-h-[calc(100vh-4rem)]">
        <section className="mx-auto max-w-4xl px-6 py-16">
          <div>
            <div className="font-mono text-xs font-medium uppercase tracking-[0.18em] text-orange-600">
              03 / Dane
            </div>

            <h1 className="mt-4 text-4xl font-semibold tracking-tight text-neutral-950">
              Dane sprawozdania
            </h1>

            <p className="mt-4 text-lg leading-8 text-neutral-600">
              Uzupełnij informacje, które znajdą się w dokumencie końcowym.
            </p>
          </div>

          <div className="mt-10 rounded-xl border border-neutral-200 bg-white p-6">
            <div className="grid gap-6 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className="text-sm font-medium text-neutral-900">
                  Przedmiot
                </label>

                <select
                  value={subjectId}
                  onChange={(event) => setSubjectId(event.target.value)}
                  disabled={subjectsLoading}
                  className="
                  mt-2 w-full rounded-lg border border-neutral-300
                  bg-white px-3 py-2.5 text-sm
                  outline-none
                  focus:border-orange-400
                  focus:ring-2
                  focus:ring-orange-100
                "
                >
                  <option value="">
                    {subjectsLoading ? "Pobieranie..." : "Wybierz przedmiot"}
                  </option>

                  {subjects.map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {subject.name} — {subject.instructor_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-sm font-medium text-neutral-900">
                  Data wykonania
                </label>

                <input
                  type="date"
                  value={executionDate}
                  onChange={(event) => setExecutionDate(event.target.value)}
                  className="
                  mt-2 w-full rounded-lg border border-neutral-300
                  bg-white px-3 py-2.5 text-sm
                  outline-none
                  focus:border-orange-400
                  focus:ring-2
                  focus:ring-orange-100
                "
                />
              </div>

              <div>
                <label className="text-sm font-medium text-neutral-900">
                  Zespół
                </label>

                <input
                  type="text"
                  value={team}
                  onChange={(event) => setTeam(event.target.value)}
                  placeholder="np. Zespół 3"
                  className="
                  mt-2 w-full rounded-lg border border-neutral-300
                  bg-white px-3 py-2.5 text-sm
                  outline-none
                  focus:border-orange-400
                  focus:ring-2
                  focus:ring-orange-100
                "
                />
              </div>

              <div className="sm:col-span-2">
                <label className="text-sm font-medium text-neutral-900">
                  Członkowie zespołu
                </label>

                <input
                  type="text"
                  value={members}
                  onChange={(event) => setMembers(event.target.value)}
                  placeholder="Jan Kowalski, Anna Nowak"
                  className="
                  mt-2 w-full rounded-lg border border-neutral-300
                  bg-white px-3 py-2.5 text-sm
                  outline-none
                  focus:border-orange-400
                  focus:ring-2
                  focus:ring-orange-100
                "
                />

                <p className="mt-2 text-xs text-neutral-500">
                  Oddziel osoby przecinkami. Jeśli zostawisz pole puste, backend
                  użyje danych z profilu.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-8 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setStep(2)}
              className="rounded-lg border border-neutral-300 bg-white px-5 py-3 text-sm font-medium text-neutral-700 hover:bg-neutral-50"
            >
              Wstecz
            </button>

            <button
              type="button"
              disabled={!subjectId || !executionDate || isGenerating}
              onClick={handleGenerateReport}
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
              {isGenerating ? "Generowanie..." : "Generuj sprawozdanie"}
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
