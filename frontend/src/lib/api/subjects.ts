export type Subject = {
  id: string;
  name: string;
  instructor_name: string;
  department?: string | null;
  laboratory?: string | null;
};

export async function getSubjects(): Promise<Subject[]> {
  const response = await fetch("/backend/subjects");

  if (!response.ok) {
    throw new Error("Nie udało się pobrać listy przedmiotów.");
  }

  return response.json();
}