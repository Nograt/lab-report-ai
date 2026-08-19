"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import {
  getReport,
  type ReportState,
} from "@/lib/api/reports";

export default function ReportPage() {
  const params = useParams<{ reportId: string }>();

  const [report, setReport] =
    useState<ReportState | null>(null);

  const [isLoading, setIsLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadReport() {
      try {
        setIsLoading(true);
        setError(null);

        const result = await getReport(
          params.reportId,
        );

        setReport(result);
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

  if (isLoading) {
    return (
      <main className="min-h-[calc(100vh-4rem)]">
        <section className="mx-auto max-w-7xl px-6 py-16">
          <p className="text-sm text-neutral-500">
            Ładowanie sprawozdania...
          </p>
        </section>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-[calc(100vh-4rem)]">
        <section className="mx-auto max-w-7xl px-6 py-16">
          <div className="rounded-xl border border-red-200 bg-red-50 p-6">
            <p className="text-sm text-red-700">
              {error}
            </p>
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

            <h1 className="mt-4 text-4xl font-semibold tracking-tight text-neutral-950">
              {report.specification?.report_title
                ?? "Sprawozdanie"}
            </h1>

            <p className="mt-3 font-mono text-xs text-neutral-400">
              ID / {params.reportId}
            </p>
          </div>

          <a
            href={`/backend/reports/${params.reportId}/docx`}
            className="inline-flex rounded-lg bg-orange-500 px-5 py-3 text-sm font-medium text-white hover:bg-orange-600"
          >
            Pobierz DOCX
          </a>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          <div className="rounded-xl border border-neutral-200 bg-white p-6">
            <p className="font-mono text-xs text-neutral-400">
              TABELE
            </p>

            <p className="mt-3 text-3xl font-semibold text-neutral-950">
              {report.measurement_tables?.length ?? 0}
            </p>
          </div>

          <div className="rounded-xl border border-neutral-200 bg-white p-6">
            <p className="font-mono text-xs text-neutral-400">
              WYKRESY
            </p>

            <p className="mt-3 text-3xl font-semibold text-neutral-950">
              {report.charts?.length ?? 0}
            </p>
          </div>

          <div className="rounded-xl border border-neutral-200 bg-white p-6">
            <p className="font-mono text-xs text-neutral-400">
              SEKCJE
            </p>

            <p className="mt-3 text-3xl font-semibold text-neutral-950">
              {report.specification?.sections?.length ?? 0}
            </p>
          </div>
        </div>

        <div className="mt-12">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-neutral-950">
              Sekcje sprawozdania
            </h2>
          </div>

          <div className="mt-6 space-y-4">
            {report.specification?.sections?.map(
              (section) => (
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
                      <p>
                        Tabela {section.table_id}
                      </p>

                      <p className="mt-1">
                        {section.chart_figure_ids.length} wykresów
                      </p>
                    </div>
                  </div>
                </div>
              ),
              
            )}
          </div>
        </div>
      </section>
    </main>
  );
}