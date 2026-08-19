export type UserProfile = {
  first_name: string;
  last_name: string;
  university: string;
  faculty: string;
  field_of_study: string;
  semester: string;
  group: string;
  academic_year: string;
};

export async function getProfile(): Promise<UserProfile | null> {
  const response = await fetch("/backend/profile");

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(
      "Nie udało się pobrać profilu.",
    );
  }

  return response.json();
}

export async function saveProfile(
  profile: UserProfile,
): Promise<UserProfile> {
  const response = await fetch(
    "/backend/profile",
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(profile),
    },
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      typeof error?.detail === "string"
        ? error.detail
        : "Nie udało się zapisać profilu.",
    );
  }

  return response.json();
}