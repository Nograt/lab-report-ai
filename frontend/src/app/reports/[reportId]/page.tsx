"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ChartFigureEditor } from "@/components/reports/ChartFigureEditor";
import {
  deleteSetupImage,
  getReport,
  getReportData,
  updateReportCharts,
  updateReportText,
  updateSetupImageSections,
  uploadSetupImage,
  type ReportChart,
  type ReportDataResponse,
  type ReportState,
  type ReportText,
  type SetupImage,
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

  const [chartImageVersion, setChartImageVersion] =
  useState(0);
  const [editableText, setEditableText] =
  useState<ReportText | null>(null);

const [textSaving, setTextSaving] =
  useState(false);

const [textSaved, setTextSaved] =
  useState(false);

const [textError, setTextError] =
  useState<string | null>(null);

  const [schematics, setSchematics] =
    useState<SetupImage[]>([]);

  const [
    sectionSetupImages,
    setSectionSetupImages,
  ] = useState<Record<string, string>>({});

  const [schematicFile, setSchematicFile] =
    useState<File | null>(null);

  const [schematicCaption, setSchematicCaption] =
    useState("");

  const [
    schematicSections,
    setSchematicSections,
  ] = useState<number[]>([]);

  const [
    schematicUploading,
    setSchematicUploading,
  ] = useState(false);

  const [schematicError, setSchematicError] =
    useState<string | null>(null);

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
      setChartImageVersion((current) => current + 1);

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
        setEditableText(result.report_text ?? null);
        setEditableCharts(result.charts ?? []);
        setSchematics(result.setup_images ?? []);
        setSectionSetupImages(
          result.section_setup_images ?? {},
        );
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

  async function handleSaveText() {
  if (!editableText) {
    return;
  }

  try {
    setTextSaving(true);
    setTextSaved(false);
    setTextError(null);

    const result = await updateReportText(
      params.reportId,
      editableText,
    );

    setEditableText(result.report_text);

    setReport((current) =>
      current
        ? {
            ...current,
            report_text: result.report_text,
          }
        : current,
    );

    setTextSaved(true);
  } catch (error) {
    if (error instanceof Error) {
      setTextError(error.message);
    } else {
      setTextError(
        "Wystąpił nieoczekiwany błąd.",
      );
    }
  } finally {
    setTextSaving(false);
  }
}

  async function handleUploadSchematic() {
    if (
      !schematicFile ||
      schematicSections.length === 0
    ) {
      return;
    }

    try {
      setSchematicUploading(true);
      setSchematicError(null);

      const result = await uploadSetupImage(
        params.reportId,
        schematicFile,
        schematicSections,
        schematicCaption.trim() || undefined,
      );

      setSchematics((current) => [
        ...current,
        result.image,
      ]);

      setSectionSetupImages((current) => {
        const updated = { ...current };

        for (const sectionId of result.section_ids) {
          updated[String(sectionId)] =
            result.image.image_id;
        }

        return updated;
      });

      setSchematicFile(null);
      setSchematicCaption("");
      setSchematicSections([]);
    } catch (error) {
      setSchematicError(
        error instanceof Error
          ? error.message
          : "Wystąpił nieoczekiwany błąd.",
      );
    } finally {
      setSchematicUploading(false);
    }
  }

  async function handleDeleteSchematic(
    imageId: string,
  ) {
    try {
      setSchematicError(null);

      await deleteSetupImage(
        params.reportId,
        imageId,
      );

      setSchematics((current) =>
        current.filter(
          (image) =>
            image.image_id !== imageId,
        ),
      );

      setSectionSetupImages((current) => {
        const updated = { ...current };

        for (const [
          sectionId,
          assignedImageId,
        ] of Object.entries(updated)) {
          if (assignedImageId === imageId) {
            delete updated[sectionId];
          }
        }

        return updated;
      });
    } catch (error) {
      setSchematicError(
        error instanceof Error
          ? error.message
          : "Nie udało się usunąć schematu.",
      );
    }
  }

  function getSchematicSectionIds(
    imageId: string,
  ) {
    return Object.entries(
      sectionSetupImages,
    )
      .filter(
        ([, assignedImageId]) =>
          assignedImageId === imageId,
      )
      .map(([sectionId]) =>
        Number(sectionId),
      );
  }

  async function handleSchematicSectionToggle(
    imageId: string,
    sectionId: number,
  ) {
    const currentIds =
      getSchematicSectionIds(imageId);

    const nextIds = currentIds.includes(
      sectionId,
    )
      ? currentIds.filter(
          (id) => id !== sectionId,
        )
      : [...currentIds, sectionId];

    if (nextIds.length === 0) {
      return;
    }

    try {
      setSchematicError(null);

      await updateSetupImageSections(
        params.reportId,
        imageId,
        nextIds,
      );

      setSectionSetupImages((current) => {
        const updated = { ...current };

        for (const [
          key,
          assignedImageId,
        ] of Object.entries(updated)) {
          if (assignedImageId === imageId) {
            delete updated[key];
          }
        }

        for (const id of nextIds) {
          updated[String(id)] = imageId;
        }

        return updated;
      });
    } catch (error) {
      setSchematicError(
        error instanceof Error
          ? error.message
          : "Nie udało się zmienić przypisania.",
      );
    }
  }

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
              ["images", "Schematy"],
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
  reportId={params.reportId}
  figureId={
    figureCharts[0].chart.figure_id
  }
  imageVersion={chartImageVersion}
  charts={figureCharts}
  tables={
    report.measurement_tables ?? []
  }
  onChange={handleChartChange}
/>
))
              )}
            </div>
          </div>
        )}

       {activeTab === "text" && (
  <div className="mt-10">
    <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p className="font-mono text-xs font-medium uppercase tracking-[0.18em] text-orange-600">
          Raport / Treść
        </p>

        <h2 className="mt-3 text-2xl font-semibold tracking-tight text-neutral-950">
          Treść sprawozdania
        </h2>

        <p className="mt-2 text-sm leading-6 text-neutral-500">
          Edytuj wygenerowane opisy, analizy i wnioski.
        </p>
      </div>

      <button
        type="button"
        onClick={handleSaveText}
        disabled={textSaving || !editableText}
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
        {textSaving
          ? "Zapisywanie..."
          : "Zapisz treść"}
      </button>
    </div>

    {textError && (
      <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4">
        <p className="text-sm text-red-700">
          {textError}
        </p>
      </div>
    )}

    {textSaved && (
      <div className="mt-6 rounded-xl border border-green-200 bg-green-50 p-4">
        <p className="text-sm text-green-700">
          Treść została zapisana.
        </p>
      </div>
    )}

    {!editableText ? (
      <div className="mt-8 rounded-xl border border-neutral-200 bg-white p-8">
        <p className="text-sm text-neutral-500">
          Brak wygenerowanej treści raportu.
        </p>
      </div>
    ) : (
      <div className="mt-8 space-y-6">
        <section className="rounded-xl border border-neutral-200 bg-white p-6">
          <p className="font-mono text-xs text-neutral-400">
            CEL ĆWICZENIA
          </p>

          <textarea
            value={editableText.purpose}
            onChange={(event) =>
              setEditableText({
                ...editableText,
                purpose: event.target.value,
              })
            }
            rows={4}
            className="mt-4 w-full resize-y rounded-lg border border-neutral-200 px-4 py-3 text-sm leading-7 text-neutral-700 outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
          />
        </section>

        <section className="rounded-xl border border-neutral-200 bg-white p-6">
          <p className="font-mono text-xs text-neutral-400">
            OPIS STANOWISKA
          </p>

          <textarea
            value={editableText.setup_description}
            onChange={(event) =>
              setEditableText({
                ...editableText,
                setup_description:
                  event.target.value,
              })
            }
            rows={6}
            className="mt-4 w-full resize-y rounded-lg border border-neutral-200 px-4 py-3 text-sm leading-7 text-neutral-700 outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
          />
        </section>

        {editableText.theory !== null &&
          editableText.theory !== undefined && (
            <section className="rounded-xl border border-neutral-200 bg-white p-6">
              <p className="font-mono text-xs text-neutral-400">
                WSTĘP TEORETYCZNY
              </p>

              <textarea
                value={editableText.theory}
                onChange={(event) =>
                  setEditableText({
                    ...editableText,
                    theory: event.target.value,
                  })
                }
                rows={8}
                className="mt-4 w-full resize-y rounded-lg border border-neutral-200 px-4 py-3 text-sm leading-7 text-neutral-700 outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
              />
            </section>
          )}

        {editableText.sections.map(
          (sectionText, index) => {
            const section =
              report.specification?.sections?.find(
                (item) =>
                  item.section_id ===
                  sectionText.section_id,
              );

            return (
              <section
                key={sectionText.section_id}
                className="rounded-xl border border-neutral-200 bg-white"
              >
                <div className="border-b border-neutral-200 px-6 py-5">
                  <p className="font-mono text-xs text-neutral-400">
                    SEKCJA / {sectionText.section_id}
                  </p>

                  <h3 className="mt-2 text-lg font-medium text-neutral-950">
                    {section?.title ??
                      `Sekcja ${sectionText.section_id}`}
                  </h3>
                </div>

                <div className="space-y-6 p-6">
                  <div>
                    <p className="font-mono text-xs text-neutral-400">
                      OPIS
                    </p>

                    <textarea
                      value={sectionText.description}
                      onChange={(event) =>
                        setEditableText({
                          ...editableText,
                          sections:
                            editableText.sections.map(
                              (item, itemIndex) =>
                                itemIndex === index
                                  ? {
                                      ...item,
                                      description:
                                        event.target.value,
                                    }
                                  : item,
                            ),
                        })
                      }
                      rows={6}
                      className="mt-3 w-full resize-y rounded-lg border border-neutral-200 px-4 py-3 text-sm leading-7 text-neutral-700 outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
                    />
                  </div>

                  <div>
                    <p className="font-mono text-xs text-neutral-400">
                      ANALIZA
                    </p>

                    <textarea
                      value={sectionText.analysis}
                      onChange={(event) =>
                        setEditableText({
                          ...editableText,
                          sections:
                            editableText.sections.map(
                              (item, itemIndex) =>
                                itemIndex === index
                                  ? {
                                      ...item,
                                      analysis:
                                        event.target.value,
                                    }
                                  : item,
                            ),
                        })
                      }
                      rows={8}
                      className="mt-3 w-full resize-y rounded-lg border border-neutral-200 px-4 py-3 text-sm leading-7 text-neutral-700 outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
                    />
                  </div>
                </div>
              </section>
            );
          },
        )}

        <section className="rounded-xl border border-neutral-200 bg-white p-6">
          <p className="font-mono text-xs text-neutral-400">
            WNIOSKI
          </p>

          <textarea
            value={editableText.conclusions}
            onChange={(event) =>
              setEditableText({
                ...editableText,
                conclusions:
                  event.target.value,
              })
            }
            rows={8}
            className="mt-4 w-full resize-y rounded-lg border border-neutral-200 px-4 py-3 text-sm leading-7 text-neutral-700 outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
          />
        </section>
      </div>
    )}
  </div>
)}

        {activeTab === "images" && (
          <div className="mt-10">
            <div>
              <p className="font-mono text-xs font-medium uppercase tracking-[0.18em] text-orange-600">
                Raport / Schematy
              </p>

              <h2 className="mt-3 text-2xl font-semibold tracking-tight text-neutral-950">
                Schematy
              </h2>

              <p className="mt-2 text-sm leading-6 text-neutral-500">
                Dodaj schematy układów pomiarowych i przypisz je do sekcji sprawozdania.
              </p>
            </div>

            {schematicError && (
              <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4">
                <p className="text-sm text-red-700">
                  {schematicError}
                </p>
              </div>
            )}

            <div className="mt-8 rounded-xl border border-neutral-200 bg-white p-6">
              <p className="font-mono text-xs text-neutral-400">
                NOWY SCHEMAT
              </p>

              <div className="mt-6 grid gap-6 lg:grid-cols-2">
                <div>
                  <label className="text-sm font-medium text-neutral-900">
                    Plik
                  </label>

                  <input
                    type="file"
                    accept="image/*"
                    onChange={(event) =>
                      setSchematicFile(
                        event.target.files?.[0] ?? null,
                      )
                    }
                    className="mt-2 block w-full rounded-lg border border-neutral-200 px-3 py-2.5 text-sm"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium text-neutral-900">
                    Podpis
                  </label>

                  <input
                    value={schematicCaption}
                    onChange={(event) =>
                      setSchematicCaption(
                        event.target.value,
                      )
                    }
                    placeholder="Schemat układu pomiarowego"
                    className="mt-2 w-full rounded-lg border border-neutral-200 px-3 py-2.5 text-sm outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
                  />
                </div>
              </div>

              <div className="mt-6">
                <p className="text-sm font-medium text-neutral-900">
                  Sekcje
                </p>

                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  {report.specification?.sections?.map(
                    (section) => {
                      const selected =
                        schematicSections.includes(
                          section.section_id,
                        );

                      return (
                        <label
                          key={section.section_id}
                          className="flex cursor-pointer items-center gap-3 rounded-lg border border-neutral-200 px-4 py-3"
                        >
                          <input
                            type="checkbox"
                            checked={selected}
                            onChange={() =>
                              setSchematicSections(
                                (current) =>
                                  selected
                                    ? current.filter(
                                        (id) =>
                                          id !==
                                          section.section_id,
                                      )
                                    : [
                                        ...current,
                                        section.section_id,
                                      ],
                              )
                            }
                            className="accent-orange-500"
                          />

                          <div>
                            <p className="text-sm font-medium text-neutral-900">
                              {section.title}
                            </p>

                            <p className="mt-1 font-mono text-xs text-neutral-400">
                              SEKCJA / {section.section_id}
                            </p>
                          </div>
                        </label>
                      );
                    },
                  )}
                </div>
              </div>

              <button
                type="button"
                onClick={handleUploadSchematic}
                disabled={
                  schematicUploading ||
                  !schematicFile ||
                  schematicSections.length === 0
                }
                className="mt-6 rounded-lg px-5 py-3 text-sm font-medium disabled:cursor-not-allowed disabled:bg-neutral-200 disabled:text-neutral-400 enabled:bg-orange-500 enabled:text-white enabled:hover:bg-orange-600"
              >
                {schematicUploading
                  ? "Dodawanie..."
                  : "Dodaj schemat"}
              </button>
            </div>

            <div className="mt-10">
              <h3 className="text-lg font-semibold text-neutral-950">
                Dodane schematy
              </h3>

              {schematics.length === 0 ? (
                <div className="mt-4 rounded-xl border border-neutral-200 bg-white p-8">
                  <p className="text-sm text-neutral-500">
                    Nie dodano jeszcze żadnych schematów.
                  </p>
                </div>
              ) : (
                <div className="mt-4 grid gap-6 xl:grid-cols-2">
                  {schematics.map((image) => {
                    const assignedSections =
                      getSchematicSectionIds(
                        image.image_id,
                      );

                    return (
                      <div
                        key={image.image_id}
                        className="overflow-hidden rounded-xl border border-neutral-200 bg-white"
                      >
                        <div className="flex min-h-[300px] items-center justify-center bg-neutral-50 p-4">
                          <img
                            src={`/backend/reports/${params.reportId}/setup-images/${image.image_id}/image`}
                            alt={image.caption}
                            className="max-h-[420px] max-w-full object-contain"
                          />
                        </div>

                        <div className="border-t border-neutral-200 p-6">
                          <p className="font-mono text-xs text-neutral-400">
                            SCHEMAT
                          </p>

                          <h4 className="mt-2 font-medium text-neutral-950">
                            {image.caption}
                          </h4>

                          <div className="mt-5">
                            <p className="text-xs font-medium text-neutral-500">
                              PRZYPISANIE
                            </p>

                            <div className="mt-3 space-y-2">
                              {report.specification?.sections?.map(
                                (section) => (
                                  <label
                                    key={section.section_id}
                                    className="flex cursor-pointer items-center gap-2 text-sm text-neutral-700"
                                  >
                                    <input
                                      type="checkbox"
                                      checked={assignedSections.includes(
                                        section.section_id,
                                      )}
                                      onChange={() =>
                                        handleSchematicSectionToggle(
                                          image.image_id,
                                          section.section_id,
                                        )
                                      }
                                      className="accent-orange-500"
                                    />

                                    {section.title}
                                  </label>
                                ),
                              )}
                            </div>
                          </div>

                          <button
                            type="button"
                            onClick={() =>
                              handleDeleteSchematic(
                                image.image_id,
                              )
                            }
                            className="mt-6 text-sm font-medium text-red-600 hover:text-red-700"
                          >
                            Usuń schemat
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </section>
    </main>
  );
}