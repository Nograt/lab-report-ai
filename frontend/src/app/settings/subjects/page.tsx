"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  createSubject,
  deleteSubject,
  getSubjects,
  updateSubject,
  type Subject,
} from "@/lib/api/subjects";

type SubjectForm = {
  name: string;
  instructor_name: string;
  department: string;
  laboratory: string;
};

const emptyForm: SubjectForm = {
  name: "",
  instructor_name: "",
  department: "",
  laboratory: "",
};

export default function SubjectsPage() {
  const [subjects, setSubjects] =
    useState<Subject[]>([]);

  const [form, setForm] =
    useState<SubjectForm>(emptyForm);

  const [editingId, setEditingId] =
    useState<string | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadSubjects() {
      try {
        setLoading(true);
        setError(null);

        const result = await getSubjects();

        setSubjects(result);
      } catch (error) {
        setError(
          error instanceof Error
            ? error.message
            : "Nie udało się pobrać przedmiotów.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadSubjects();
  }, []);

  function updateField(
    field: keyof SubjectForm,
    value: string,
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function handleEdit(
    subject: Subject,
  ) {
    setEditingId(subject.id);

    setForm({
      name: subject.name,
      instructor_name:
        subject.instructor_name,
      department:
        subject.department ?? "",
      laboratory:
        subject.laboratory ?? "",
    });

    setError(null);
  }

  function handleCancelEdit() {
    setEditingId(null);
    setForm(emptyForm);
    setError(null);
  }

  async function handleSave() {
    if (
      !form.name.trim() ||
      !form.instructor_name.trim()
    ) {
      setError(
        "Nazwa przedmiotu i prowadzący są wymagane.",
      );

      return;
    }

    try {
      setSaving(true);
      setError(null);

      const payload = {
        name: form.name.trim(),
        instructor_name:
          form.instructor_name.trim(),
        department:
          form.department.trim() || null,
        laboratory:
          form.laboratory.trim() || null,
      };

      if (editingId) {
        const updated =
          await updateSubject(
            editingId,
            payload,
          );

        setSubjects((current) =>
          current.map((subject) =>
            subject.id === editingId
              ? updated
              : subject,
          ),
        );
      } else {
        const created =
          await createSubject(
            payload,
          );

        setSubjects((current) => [
          ...current,
          created,
        ]);
      }

      setEditingId(null);
      setForm(emptyForm);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Nie udało się zapisać przedmiotu.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(
    subjectId: string,
  ) {
    try {
      setError(null);

      await deleteSubject(subjectId);

      setSubjects((current) =>
        current.filter(
          (subject) =>
            subject.id !== subjectId,
        ),
      );

      if (editingId === subjectId) {
        handleCancelEdit();
      }
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Nie udało się usunąć przedmiotu.",
      );
    }
  }

  if (loading) {
    return (
      <main className="min-h-[calc(100vh-4rem)]">
        <section className="mx-auto max-w-6xl px-6 py-16">
          <p className="text-sm text-neutral-500">
            Ładowanie przedmiotów...
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-[calc(100vh-4rem)]">
      <section className="mx-auto max-w-6xl px-6 py-16">
        <div>
          <p className="font-mono text-xs font-medium uppercase tracking-[0.18em] text-orange-600">
            Ustawienia / Przedmioty
          </p>

          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-neutral-950">
            Przedmioty
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-neutral-500">
            Zarządzaj przedmiotami używanymi podczas tworzenia sprawozdań.
          </p>
        </div>

        {error && (
          <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-700">
              {error}
            </p>
          </div>
        )}

        <div className="mt-8 rounded-xl border border-neutral-200 bg-white p-6">
          <p className="font-mono text-xs text-neutral-400">
            {editingId
              ? "EDYCJA PRZEDMIOTU"
              : "NOWY PRZEDMIOT"}
          </p>

          <div className="mt-6 grid gap-6 md:grid-cols-2">
            <div className="space-y-6">
              <Field
                label="Nazwa przedmiotu"
                value={form.name}
                onChange={(value) =>
                  updateField(
                    "name",
                    value,
                  )
                }
                placeholder="np. Maszyny elektryczne"
              />

              <Field
                label="Nazwa laboratorium"
                value={form.laboratory}
                onChange={(value) =>
                  updateField(
                    "laboratory",
                    value,
                  )
                }
                placeholder="np. Laboratorium Maszyn Elektrycznych"
              />
            </div>

            <div className="space-y-6">
              <Field
                label="Prowadzący"
                value={form.instructor_name}
                onChange={(value) =>
                  updateField(
                    "instructor_name",
                    value,
                  )
                }
                placeholder="np. dr inż. Jan Kowalski"
              />

              <Field
                label="Katedra"
                value={form.department}
                onChange={(value) =>
                  updateField(
                    "department",
                    value,
                  )
                }
                placeholder="np. Katedra Napędów i Maszyn Elektrycznych"
              />
            </div>
          </div>

          <div className="mt-6 flex gap-3">
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="rounded-lg bg-orange-500 px-5 py-3 text-sm font-medium text-white hover:bg-orange-600 disabled:cursor-not-allowed disabled:bg-neutral-200 disabled:text-neutral-400"
            >
              {saving
                ? "Zapisywanie..."
                : editingId
                  ? "Zapisz zmiany"
                  : "Dodaj przedmiot"}
            </button>

            {editingId && (
              <button
                type="button"
                onClick={handleCancelEdit}
                className="rounded-lg border border-neutral-200 px-5 py-3 text-sm font-medium text-neutral-700 hover:bg-neutral-50"
              >
                Anuluj
              </button>
            )}
          </div>
        </div>

        <div className="mt-10">
          <h2 className="text-lg font-semibold text-neutral-950">
            Twoje przedmioty
          </h2>

          {subjects.length === 0 ? (
            <div className="mt-4 rounded-xl border border-neutral-200 bg-white p-8">
              <p className="text-sm text-neutral-500">
                Nie dodano jeszcze żadnych przedmiotów.
              </p>
            </div>
          ) : (
            <div className="mt-4 space-y-4">
              {subjects.map((subject) => (
                <div
                  key={subject.id}
                  className="rounded-xl border border-neutral-200 bg-white p-6"
                >
                  <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="font-mono text-xs text-neutral-400">
                        PRZEDMIOT
                      </p>

                      <h3 className="mt-2 text-lg font-medium text-neutral-950">
                        {subject.name}
                      </h3>

                      {subject.laboratory && (
                        <p className="mt-1 text-sm text-neutral-500">
                          {subject.laboratory}
                        </p>
                      )}

                      <p className="mt-3 text-sm text-neutral-700">
                        {subject.instructor_name}
                      </p>

                      {subject.department && (
                        <p className="mt-1 text-sm text-neutral-500">
                          {subject.department}
                        </p>
                      )}
                    </div>

                    <div className="flex gap-3">
                      <button
                        type="button"
                        onClick={() =>
                          handleEdit(subject)
                        }
                        className="text-sm font-medium text-neutral-600 hover:text-neutral-950"
                      >
                        Edytuj
                      </button>

                      <button
                        type="button"
                        onClick={() =>
                          handleDelete(
                            subject.id,
                          )
                        }
                        className="text-sm font-medium text-red-600 hover:text-red-700"
                      >
                        Usuń
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

type FieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
};

function Field({
  label,
  value,
  onChange,
  placeholder,
}: FieldProps) {
  return (
    <div>
      <label className="text-sm font-medium text-neutral-900">
        {label}
      </label>

      <input
        type="text"
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        placeholder={placeholder}
        className="mt-2 w-full rounded-lg border border-neutral-200 px-3 py-2.5 text-sm outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
      />
    </div>
  );
}