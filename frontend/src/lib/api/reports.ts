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