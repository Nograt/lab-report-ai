export type Subject = {
  id: string;
  name: string;
  instructor_name: string;
  department?: string | null;
  laboratory?: string | null;
};

export type CreateSubjectInput = {
  name: string;
  instructor_name: string;
  department?: string | null;
  laboratory?: string | null;
};

export type UpdateSubjectInput = {
  name?: string;
  instructor_name?: string;
  department?: string | null;
  laboratory?: string | null;
};

export async function getSubjects(): Promise<Subject[]> {
  const response = await fetch("/backend/subjects");

  if (!response.ok) {
    throw new Error(
      "Nie udało się pobrać przedmiotów.",
    );
  }

  return response.json();
}

export async function createSubject(
  input: CreateSubjectInput,
): Promise<Subject> {
  const response = await fetch(
    "/backend/subjects",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    },
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      typeof error?.detail === "string"
        ? error.detail
        : "Nie udało się dodać przedmiotu.",
    );
  }

  return response.json();
}

export async function updateSubject(
  subjectId: string,
  input: UpdateSubjectInput,
): Promise<Subject> {
  const response = await fetch(
    `/backend/subjects/${subjectId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    },
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      typeof error?.detail === "string"
        ? error.detail
        : "Nie udało się zaktualizować przedmiotu.",
    );
  }

  return response.json();
}

export async function deleteSubject(
  subjectId: string,
): Promise<void> {
  const response = await fetch(
    `/backend/subjects/${subjectId}`,
    {
      method: "DELETE",
    },
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      typeof error?.detail === "string"
        ? error.detail
        : "Nie udało się usunąć przedmiotu.",
    );
  }
}