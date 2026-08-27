/**
 * Generate a browser-compatible client identifier.
 *
 * crypto.randomUUID() is unavailable in some browsers when Hela360 is
 * accessed through a plain HTTP LAN address. This helper provides a safe
 * application-wide fallback for temporary client identifiers,
 * correlation IDs and idempotency keys.
 */
export function createClientId(): string {
  const cryptoApi = globalThis.crypto;

  if (
    cryptoApi &&
    typeof cryptoApi.randomUUID === "function"
  ) {
    return cryptoApi.randomUUID();
  }

  if (
    cryptoApi &&
    typeof cryptoApi.getRandomValues === "function"
  ) {
    const bytes = new Uint8Array(16);

    cryptoApi.getRandomValues(bytes);

    bytes[6] =
      ((bytes[6] ?? 0) & 0x0f) | 0x40;

    bytes[8] =
      ((bytes[8] ?? 0) & 0x3f) | 0x80;

    const hex = Array.from(
      bytes,
      (byte) =>
        byte.toString(16).padStart(2, "0"),
    ).join("");

    return [
      hex.slice(0, 8),
      hex.slice(8, 12),
      hex.slice(12, 16),
      hex.slice(16, 20),
      hex.slice(20),
    ].join("-");
  }

  return [
    Date.now().toString(36),
    Math.random().toString(36).slice(2),
    Math.random().toString(36).slice(2),
  ].join("-");
}

export default createClientId;
