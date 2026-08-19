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

export async function prepareInstruction(
  instructionFile: File,
  measurementsFile: File,
): Promise<PrepareInstructionResponse> {
  const formData = new FormData();

  formData.append("instruction_file", instructionFile);
  formData.append("measurements", measurementsFile);

  const response = await fetch("/backend/reports/prepare-instruction", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      error?.detail ?? "Nie udało się przygotować instrukcji.",
    );
  }

  return response.json();
}

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

  const response = await fetch("/backend/reports/analyze", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      error?.detail ?? "Nie udało się wygenerować sprawozdania.",
    );
  }

  return response.json();
}

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

  charts?: {
    figure_id: number;
    x: string;
    y: string;
  }[];

  report_text?: Record<string, unknown>;

  metadata?: Record<string, unknown>;
};

export async function getReport(
  reportId: string,
): Promise<ReportState> {
  const response = await fetch(`/backend/reports/${reportId}`);

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      error?.detail ?? "Nie udało się pobrać sprawozdania.",
    );
  }

  return response.json();
}