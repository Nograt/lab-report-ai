"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ChartFigureEditor } from "@/components/reports/ChartFigureEditor";
import { ChartEditor } from "@/components/reports/ChartEditor";

import {
  getReport,
  getReportData,
  updateReportCharts,
  type ReportChart,
  type ReportDataResponse,
  type ReportState,
} from "@/lib/api/reports";

import { MeasurementTable } from "@/components/reports/MeasurementTable";

export default function ReportPage() {
  type ReportTab = "overview" | "data" | "charts" | "text" | "images";

  const [activeTab, setActiveTab] = useState<ReportTab>("overview");

  const [reportData, setReportData] = useState<ReportDataResponse | null>(null);

  const [dataLoading, setDataLoading] = useState(false);

  const [dataError, setDataError] = useState<string | null>(null);

  const params = useParams<{ reportId: string }>();

  const [report, setReport] = useState<ReportState | null>(null);

  const [isLoading, setIsLoading] = useState(true);

  const [error, setError] = useState<string | null>(null);

  const [editableCharts, setEditableCharts] = useState<ReportChart[]>([]);

  const [chartsSaving, setChartsSaving] = useState(false);

  const [chartsError, setChartsError] = useState<string | null>(null);

  const [chartsSaved, setChartsSaved] = useState(false);

  async function loadReportData() {
    if (reportData) {
      return;
    }

    try {
      setDataLoading(true);
      setDataError(null);

      const result = await getReportData(params.reportId);

      setReportData(result);
    } catch (error) {
      if (error instanceof Error) {
        setDataError(error.message);
      } else {
        setDataError("Wystąpił nieoczekiwany błąd.");
      }
    } finally {
      setDataLoading(false);
    }
  }

  function handleTabChange(tab: ReportTab) {
    setActiveTab(tab);

    if (tab === "data") {
      loadReportData();
    }
  }

  function handleChartChange(index: number, updatedChart: ReportChart) {
    setChartsSaved(false);

    setEditableCharts((current) =>
      current.map((chart, currentIndex) =>
        currentIndex === index ? updatedChart : chart,
      ),
    );
  }

  async function handleSaveCharts() {
    try {
      setChartsSaving(true);
      setChartsError(null);
      setChartsSaved(false);

      const result = await updateReportCharts(params.reportId, editableCharts);

      setEditableCharts(result.charts);

      setReport((current) =>
        current
          ? {
              ...current,
              charts: result.charts,
            }
          : current,
      );

      setChartsSaved(true);
    } catch (error) {
      if (error instanceof Error) {
        setChartsError(error.message);
      } else {
        setChartsError("Wystąpił nieoczekiwany błąd.");
      }
    } finally {
      setChartsSaving(false);
    }
  }
  useEffect(() => {
    async function loadReport() {
      try {
        setIsLoading(true);
        setError(null);

        const result = await getReport(params.reportId);

        setReport(result);
        setEditableCharts(result.charts ?? []);
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

    loadReport();
  }, [params.reportId]);


const groupedCharts = Object.values(
  editableCharts.reduce<
    Record<
      number,
      {
        chart: ReportChart;
        index: number;
      }[]
    >
  >((groups, chart, index) => {
    if (!groups[chart.figure_id]) {
      groups[chart.figure_id] = [];
    }

    groups[chart.figure_id].push({
      chart,
      index,
    });

    return groups;
  }, {}),
);


  if (isLoading) {
    return (
      <main className="min-h-[calc(100vh-4rem)]">
        <section className="mx-auto max-w-7xl px-6 py-16">
          <p className="text-sm text-neutral-500">Ładowanie sprawozdania...</p>
        </section>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-[calc(100vh-4rem)]">
        <section className="mx-auto max-w-7xl px-6 py-16">
          <div className="rounded-xl border border-red-200 bg-red-50 p-6">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </section>
      </main>
    );
  }

  if (!report) {
    return null;
  }

  return (
    <main className="min-h-[calc(100vh-4rem)]">
      <section className="mx-auto max-w-7xl px-6 py-16">
        <div className="flex flex-col gap-8 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="font-mono text-xs font-medium uppercase tracking-[0.18em] text-orange-600">
              Raport / Gotowy
            </div>

            <h1 className="mt-4 max-w-4xl text-4xl font-semibold tracking-tight text-neutral-950">
              {report.specification?.report_title ?? "Sprawozdanie"}
            </h1>

            <p className="mt-3 font-mono text-xs text-neutral-400">
              ID / {params.reportId}
            </p>
          </div>

          <a
            href={`/backend/reports/${params.reportId}/docx`}
            className="inline-flex w-fit rounded-lg bg-orange-500 px-5 py-3 text-sm font-medium text-white hover:bg-orange-600"
          >
            Pobierz DOCX
          </a>
        </div>

        <div className="mt-12 border-b border-neutral-200">
          <nav className="flex gap-6 overflow-x-auto">
            {[
              ["overview", "Przegląd"],
              ["data", "Dane"],
              ["charts", "Wykresy"],
              ["text", "Treść"],
              ["images", "Zdjęcia"],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => handleTabChange(value as ReportTab)}
                className={`
                whitespace-nowrap border-b-2 px-1 pb-3 text-sm font-medium
                ${
                  activeTab === value
                    ? "border-orange-500 text-orange-600"
                    : "border-transparent text-neutral-500 hover:text-neutral-900"
                }
              `}
              >
                {label}
              </button>
            ))}
          </nav>
        </div>

        {activeTab === "overview" && (
          <>
            <div className="mt-12 grid gap-6 md:grid-cols-3">
              <div className="rounded-xl border border-neutral-200 bg-white p-6">
                <p className="font-mono text-xs text-neutral-400">TABELE</p>

                <p className="mt-3 text-3xl font-semibold text-neutral-950">
                  {report.measurement_tables?.length ?? 0}
                </p>
              </div>

              <div className="rounded-xl border border-neutral-200 bg-white p-6">
                <p className="font-mono text-xs text-neutral-400">WYKRESY</p>

                <p className="mt-3 text-3xl font-semibold text-neutral-950">
                  {report.charts?.length ?? 0}
                </p>
              </div>

              <div className="rounded-xl border border-neutral-200 bg-white p-6">
                <p className="font-mono text-xs text-neutral-400">SEKCJE</p>

                <p className="mt-3 text-3xl font-semibold text-neutral-950">
                  {report.specification?.sections?.length ?? 0}
                </p>
              </div>
            </div>

            <div className="mt-12">
              <h2 className="text-xl font-semibold text-neutral-950">
                Sekcje sprawozdania
              </h2>

              <div className="mt-6 space-y-4">
                {report.specification?.sections?.map((section) => (
                  <div
                    key={section.section_id}
                    className="rounded-xl border border-neutral-200 bg-white p-6"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="font-mono text-xs text-neutral-400">
                          SEKCJA / {section.section_id}
                        </p>

                        <h3 className="mt-2 font-medium text-neutral-950">
                          {section.title}
                        </h3>
                      </div>

                      <div className="text-right text-xs text-neutral-500">
                        <p>Tabela {section.table_id}</p>

                        <p className="mt-1">
                          {section.chart_figure_ids.length} wykresów
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {activeTab === "data" && (
          <div className="mt-10">
            <div>
              <p className="font-mono text-xs font-medium uppercase tracking-[0.18em] text-orange-600">
                Dane / Pomiary
              </p>

              <h2 className="mt-3 text-2xl font-semibold tracking-tight text-neutral-950">
                Dane pomiarowe
              </h2>

              <p className="mt-2 text-sm leading-6 text-neutral-500">
                Podgląd tabel pomiarowych po wykonaniu obliczeń.
              </p>
            </div>

            {dataLoading && (
              <div className="mt-8 rounded-xl border border-neutral-200 bg-white p-6">
                <p className="text-sm text-neutral-500">Pobieranie danych...</p>
              </div>
            )}

            {dataError && (
              <div className="mt-8 rounded-xl border border-red-200 bg-red-50 p-6">
                <p className="text-sm text-red-700">{dataError}</p>
              </div>
            )}

            {reportData && (
              <div className="mt-8 space-y-8">
                {reportData.tables.map((table) => (
                  <MeasurementTable key={table.table_id} table={table} />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "charts" && (
          <div className="mt-10">
            <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="font-mono text-xs font-medium uppercase tracking-[0.18em] text-orange-600">
                  Wykresy / Konfiguracja
                </p>

                <h2 className="mt-3 text-2xl font-semibold tracking-tight text-neutral-950">
                  Wykresy
                </h2>

                <p className="mt-2 max-w-2xl text-sm leading-6 text-neutral-500">
                  Zmień zmienne na osiach, skalę oraz sposób prezentacji danych.
                </p>
              </div>

              <button
                type="button"
                onClick={handleSaveCharts}
                disabled={chartsSaving}
                className="
          w-fit rounded-lg px-5 py-3 text-sm font-medium
          disabled:cursor-not-allowed
          disabled:bg-neutral-200
          disabled:text-neutral-400
          enabled:bg-orange-500
          enabled:text-white
          enabled:hover:bg-orange-600
        "
              >
                {chartsSaving ? "Zapisywanie..." : "Zapisz wykresy"}
              </button>
            </div>

            {chartsError && (
              <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4">
                <p className="text-sm text-red-700">{chartsError}</p>
              </div>
            )}

            {chartsSaved && (
              <div className="mt-6 rounded-xl border border-green-200 bg-green-50 p-4">
                <p className="text-sm text-green-700">
                  Wykresy zostały zapisane i wygenerowane ponownie.
                </p>
              </div>
            )}

            <div className="mt-8 space-y-6">
              {editableCharts.length === 0 ? (
                <div className="rounded-xl border border-neutral-200 bg-white p-8">
                  <p className="text-sm text-neutral-500">
                    To sprawozdanie nie zawiera wykresów.
                  </p>
                </div>
              ) : (
                groupedCharts.map((figureCharts) => (
  <ChartFigureEditor
    key={figureCharts[0].chart.figure_id}
    figureId={figureCharts[0].chart.figure_id}
    charts={figureCharts}
    tables={report.measurement_tables ?? []}
    onChange={handleChartChange}
  />
))
              )}
            </div>
          </div>
        )}

        {activeTab === "text" && (
          <div className="mt-10">
            <div>
              <p className="font-mono text-xs font-medium uppercase tracking-[0.18em] text-orange-600">
                Raport / Treść
              </p>

              <h2 className="mt-3 text-2xl font-semibold tracking-tight text-neutral-950">
                Treść sprawozdania
              </h2>

              <p className="mt-2 text-sm leading-6 text-neutral-500">
                Podgląd wygenerowanych opisów, analiz i wniosków.
              </p>
            </div>

            <div className="mt-8 rounded-xl border border-neutral-200 bg-white p-8">
              <p className="text-sm text-neutral-500">
                W kolejnym kroku wyświetlimy tutaj dane z report_text.
              </p>
            </div>
          </div>
        )}

        {activeTab === "images" && (
          <div className="mt-10">
            <div>
              <p className="font-mono text-xs font-medium uppercase tracking-[0.18em] text-orange-600">
                Stanowisko / Zdjęcia
              </p>

              <h2 className="mt-3 text-2xl font-semibold tracking-tight text-neutral-950">
                Zdjęcia stanowiska
              </h2>

              <p className="mt-2 text-sm leading-6 text-neutral-500">
                Dodawaj schematy i fotografie oraz przypisuj je do sekcji
                raportu.
              </p>
            </div>

            <div className="mt-8 rounded-xl border border-neutral-200 bg-white p-8">
              <p className="text-sm text-neutral-500">
                Upload zdjęć podłączymy do istniejącego endpointu setup-images.
              </p>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
