export type MissingParameter = {
  name: string;
  symbol: string;
  unit?: string | null;
  description?: string | null;
};

export type PrepareInstructionResponse = {
  instruction: string;
  missing_parameters: MissingParameter[];
};

export type ReportSectionText = {
  section_id: number;
  description: string;
  analysis: string;
};

export type ReportText = {
  purpose: string;
  setup_description: string;
  theory?: string | null;
  sections: ReportSectionText[];
  conclusions: string;
};

export type ReportChart = {
  figure_id: number;
  table_id: number;
  x: string;
  y: string;
  filter_column?: string | null;
  filter_value?: number | string | null;
  label?: string | null;
  connect_points: boolean;
  x_scale: "linear" | "log";
  y_scale: "linear" | "log";
  show_grid: boolean;
  show_legend: boolean;
};

export type SetupImage = {
  image_id: string;
  filename: string;
  caption: string;
};

export type AnalyzeReportInput = {
  instruction: string;
  measurementsFile: File;
  subjectId: string;
  executionDate: string;
  team?: string;
  members?: string;
  parameters: {
    name: string;
    symbol: string;
    value: string;
  }[];
};

export type AnalyzeReportResponse = {
  report_id: string;
};

export type ReportState = {
  report_id: string;
  specification?: {
    report_title?: string | null;
    sections?: {
      section_id: number;
      title: string;
      table_id: number;
      chart_figure_ids: number[];
    }[];
  };
  measurement_tables?: {
    table_id: number;
    title: string | null;
    sheet_name: string;
    columns: string[];
    units: Record<string, string>;
    rows: number;
  }[];
  charts?: ReportChart[];
  report_text?: ReportText;
  metadata?: Record<string, unknown>;
  setup_images?: SetupImage[];
  section_setup_images?: Record<string, string>;
};

export type ReportDataTable = {
  table_id: number;
  title: string | null;
  sheet_name: string;
  columns: string[];
  units: Record<string, string>;
  rows: Record<string, unknown>[];
};

export type ReportDataResponse = {
  report_id: string;
  tables: ReportDataTable[];
};

export type UpdateChartsResponse = {
  report_id: string;
  charts: ReportChart[];
  generated_charts: number;
};

export type UploadSetupImageResponse = {
  report_id: string;
  image: SetupImage;
  section_ids: number[];
};

export async function prepareInstruction(
  instructionFile: File,
  measurementsFile: File,
): Promise<PrepareInstructionResponse> {
  const formData = new FormData();

  formData.append("instruction_file", instructionFile);
  formData.append("measurements", measurementsFile);

  const response = await fetch(
    "/backend/reports/prepare-instruction",
    {
      method: "POST",
      body: formData,
    },
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      error?.detail ?? "Nie udało się przygotować instrukcji.",
    );
  }

  return response.json();
}

export async function analyzeReport(
  input: AnalyzeReportInput,
): Promise<AnalyzeReportResponse> {
  const formData = new FormData();

  formData.append("instruction", input.instruction);
  formData.append("measurements", input.measurementsFile);
  formData.append("subject_id", input.subjectId);
  formData.append("execution_date", input.executionDate);

  if (input.team) {
    formData.append("team", input.team);
  }

  if (input.members) {
    formData.append("members", input.members);
  }

  if (input.parameters.length > 0) {
    formData.append(
      "parameters",
      JSON.stringify(input.parameters),
    );
  }

  const response = await fetch(
    "/backend/reports/analyze",
    {
      method: "POST",
      body: formData,
    },
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      typeof error?.detail === "string"
        ? error.detail
        : "Nie udało się wygenerować sprawozdania.",
    );
  }

  return response.json();
}

export async function getReport(
  reportId: string,
): Promise<ReportState> {
  const response = await fetch(
    `/backend/reports/${reportId}`,
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      error?.detail ?? "Nie udało się pobrać sprawozdania.",
    );
  }

  return response.json();
}

export async function getReportData(
  reportId: string,
): Promise<ReportDataResponse> {
  const response = await fetch(
    `/backend/reports/${reportId}/data`,
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      error?.detail ?? "Nie udało się pobrać danych pomiarowych.",
    );
  }

  return response.json();
}

export async function updateReportCharts(
  reportId: string,
  charts: ReportChart[],
): Promise<UpdateChartsResponse> {
  const response = await fetch(
    `/backend/reports/${reportId}/charts`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        charts,
      }),
    },
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      typeof error?.detail === "string"
        ? error.detail
        : "Nie udało się zaktualizować wykresów.",
    );
  }

  return response.json();
}

export async function updateReportText(
  reportId: string,
  reportText: ReportText,
): Promise<{
  report_id: string;
  report_text: ReportText;
}> {
  const response = await fetch(
    `/backend/reports/${reportId}/text`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(reportText),
    },
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      typeof error?.detail === "string"
        ? error.detail
        : "Nie udało się zapisać treści raportu.",
    );
  }

  return response.json();
}

export async function uploadSetupImage(
  reportId: string,
  image: File,
  sectionIds: number[],
  caption?: string,
): Promise<UploadSetupImageResponse> {
  const formData = new FormData();

  formData.append("image", image);
  formData.append(
    "section_ids",
    sectionIds.join(","),
  );

  if (caption) {
    formData.append("caption", caption);
  }

  const response = await fetch(
    `/backend/reports/${reportId}/setup-images`,
    {
      method: "POST",
      body: formData,
    },
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      typeof error?.detail === "string"
        ? error.detail
        : "Nie udało się dodać schematu.",
    );
  }

  return response.json();
}

export async function updateSetupImageSections(
  reportId: string,
  imageId: string,
  sectionIds: number[],
): Promise<void> {
  const response = await fetch(
    `/backend/reports/${reportId}/setup-images/${imageId}/sections`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        section_ids: sectionIds,
      }),
    },
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      typeof error?.detail === "string"
        ? error.detail
        : "Nie udało się zmienić przypisania.",
    );
  }
}

export async function deleteSetupImage(
  reportId: string,
  imageId: string,
): Promise<void> {
  const response = await fetch(
    `/backend/reports/${reportId}/setup-images/${imageId}`,
    {
      method: "DELETE",
    },
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      typeof error?.detail === "string"
        ? error.detail
        : "Nie udało się usunąć schematu.",
    );
  }
}
