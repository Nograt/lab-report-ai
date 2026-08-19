"use client";

import { ChangeEvent } from "react";

type FileUploadCardProps = {
  label: string;
  title: string;
  description: string;
  accept: string;
  file: File | null;
  onChange: (file: File | null) => void;
};

export function FileUploadCard({
  label,
  title,
  description,
  accept,
  file,
  onChange,
}: FileUploadCardProps) {
  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0] ?? null;
    onChange(selectedFile);
  }

  return (
    <div className="rounded-xl border border-neutral-200 bg-white p-6">
      <p className="font-mono text-xs text-neutral-400">
        {label}
      </p>

      <h2 className="mt-3 text-lg font-medium text-neutral-950">
        {title}
      </h2>

      <p className="mt-2 text-sm leading-6 text-neutral-500">
        {description}
      </p>

      <div className="mt-6">
        {file ? (
          <div className="flex items-center justify-between rounded-lg border border-orange-200 bg-orange-50 px-4 py-4">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-neutral-900">
                {file.name}
              </p>

              <p className="mt-1 text-xs text-neutral-500">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>

            <button
              type="button"
              onClick={() => onChange(null)}
              className="ml-4 text-sm font-medium text-orange-600 hover:text-orange-700"
            >
              Usuń
            </button>
          </div>
        ) : (
          <label className="flex cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-neutral-300 px-6 py-12 text-center hover:border-orange-300 hover:bg-orange-50/40">
            <div className="flex size-10 items-center justify-center rounded-lg bg-neutral-100 text-neutral-600">
              ↑
            </div>

            <p className="mt-4 text-sm font-medium text-neutral-900">
              Wybierz plik
            </p>

            <p className="mt-1 text-xs text-neutral-500">
              albo przeciągnij go tutaj
            </p>

            <input
              type="file"
              accept={accept}
              onChange={handleChange}
              className="hidden"
            />
          </label>
        )}
      </div>
    </div>
  );
}