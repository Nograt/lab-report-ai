"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  getProfile,
  saveProfile,
  type UserProfile,
} from "@/lib/api/profile";

const emptyProfile: UserProfile = {
  first_name: "",
  last_name: "",
  university: "",
  faculty: "",
  field_of_study: "",
  semester: "",
  group: "",
  academic_year: "",
};

export default function ProfilePage() {
  const [profile, setProfile] =
    useState<UserProfile>(emptyProfile);

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  const [saved, setSaved] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadProfile() {
      try {
        setLoading(true);
        setError(null);

        const result = await getProfile();

        if (result) {
          setProfile(result);
        }
      } catch (error) {
        setError(
          error instanceof Error
            ? error.message
            : "Nie udało się pobrać profilu.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadProfile();
  }, []);

  function updateField(
    field: keyof UserProfile,
    value: string,
  ) {
    setSaved(false);

    setProfile((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function handleSave() {
    try {
      setSaving(true);
      setSaved(false);
      setError(null);

      const result = await saveProfile(
        profile,
      );

      setProfile(result);
      setSaved(true);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Nie udało się zapisać profilu.",
      );
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <main className="min-h-[calc(100vh-4rem)]">
        <section className="mx-auto max-w-5xl px-6 py-16">
          <p className="text-sm text-neutral-500">
            Ładowanie profilu...
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-[calc(100vh-4rem)]">
      <section className="mx-auto max-w-5xl px-6 py-16">
        <div>
          <p className="font-mono text-xs font-medium uppercase tracking-[0.18em] text-orange-600">
            Ustawienia / Profil
          </p>

          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-neutral-950">
            Profil
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-neutral-500">
            Dane używane automatycznie w generowanych sprawozdaniach.
          </p>
        </div>

        {error && (
          <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-700">
              {error}
            </p>
          </div>
        )}

        {saved && (
          <div className="mt-6 rounded-xl border border-green-200 bg-green-50 p-4">
            <p className="text-sm text-green-700">
              Profil został zapisany.
            </p>
          </div>
        )}

        <div className="mt-8 overflow-hidden rounded-xl border border-neutral-200 bg-white">
          <div className="border-b border-neutral-200 px-6 py-5">
            <p className="font-mono text-xs text-neutral-400">
              DANE OSOBOWE
            </p>
          </div>

          <div className="grid gap-6 p-6 md:grid-cols-2">
            <Field
              label="Imię"
              value={profile.first_name}
              onChange={(value) =>
                updateField(
                  "first_name",
                  value,
                )
              }
            />

            <Field
              label="Nazwisko"
              value={profile.last_name}
              onChange={(value) =>
                updateField(
                  "last_name",
                  value,
                )
              }
            />
          </div>
        </div>

        <div className="mt-6 overflow-hidden rounded-xl border border-neutral-200 bg-white">
          <div className="border-b border-neutral-200 px-6 py-5">
            <p className="font-mono text-xs text-neutral-400">
              UCZELNIA
            </p>
          </div>

          <div className="grid gap-6 p-6 md:grid-cols-2">
            <Field
              label="Uczelnia"
              value={profile.university}
              onChange={(value) =>
                updateField(
                  "university",
                  value,
                )
              }
            />

            <Field
              label="Wydział"
              value={profile.faculty}
              onChange={(value) =>
                updateField(
                  "faculty",
                  value,
                )
              }
            />

            <Field
              label="Kierunek"
              value={profile.field_of_study}
              onChange={(value) =>
                updateField(
                  "field_of_study",
                  value,
                )
              }
            />

            <Field
              label="Semestr"
              value={profile.semester}
              onChange={(value) =>
                updateField(
                  "semester",
                  value,
                )
              }
            />

            <Field
              label="Grupa"
              value={profile.group}
              onChange={(value) =>
                updateField(
                  "group",
                  value,
                )
              }
            />

            <Field
              label="Rok akademicki"
              value={profile.academic_year}
              onChange={(value) =>
                updateField(
                  "academic_year",
                  value,
                )
              }
              placeholder="2026/2027"
            />
          </div>
        </div>

        <div className="mt-8 flex justify-end">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="rounded-lg bg-orange-500 px-5 py-3 text-sm font-medium text-white hover:bg-orange-600 disabled:cursor-not-allowed disabled:bg-neutral-200 disabled:text-neutral-400"
          >
            {saving
              ? "Zapisywanie..."
              : "Zapisz profil"}
          </button>
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