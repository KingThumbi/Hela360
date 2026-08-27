const trimTrailingSlash = (
  url: string,
): string =>
  url.replace(/\/+$/, "");

const optionalEnvironmentValue = (
  value: string | undefined,
): string | null => {
  const normalized = value?.trim();

  return normalized
    ? normalized
    : null;
};

export const env = {
  apiBaseUrl: trimTrailingSlash(
    import.meta.env.VITE_API_BASE_URL ??
      "http://localhost:5000/api",
  ),

  appName:
    import.meta.env.VITE_APP_NAME ??
    "Hela360",

  appVersion:
    import.meta.env.VITE_APP_VERSION ??
    "1.0.0",

  defaultTenantId:
    optionalEnvironmentValue(
      import.meta.env.VITE_DEFAULT_TENANT_ID,
    ),
} as const;