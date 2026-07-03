/** Provides consistent display and API error formatting helpers. */

export function formatDate(value?: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function collectMessages(value: unknown, prefix = ""): string[] {
  if (typeof value === "string") return [prefix ? `${prefix}: ${value}` : value];
  if (Array.isArray(value)) return value.flatMap((item) => collectMessages(item, prefix));
  if (value && typeof value === "object") {
    return Object.entries(value as Record<string, unknown>).flatMap(([key, item]) => {
      const label = key === "non_field_errors" || key === "detail"
        ? prefix
        : [prefix, key.replaceAll("_", " ")].filter(Boolean).join(" · ");
      return collectMessages(item, label);
    });
  }
  return [];
}

export function getErrorMessage(error: unknown) {
  if (typeof error === "object" && error && "data" in error) {
    const data = (error as { data?: { message?: string; errors?: unknown } }).data;
    const details = collectMessages(data?.errors);
    if (details.length) return details.slice(0, 4).join(" | ");
    if (data?.message) return data.message;
  }
  if (error instanceof Error && error.message) return error.message;
  return "The operation could not be completed.";
}
