const trimTrailingSlash = (url: string) => url.replace(/\/+$/, "");

export const env = {
  apiBaseUrl: trimTrailingSlash(
    import.meta.env.VITE_API_BASE_URL ?? "http://localhost:5000/api",
  ),
  appName: import.meta.env.VITE_APP_NAME ?? "Hela360",
  appVersion: import.meta.env.VITE_APP_VERSION ?? "1.0.0",
};