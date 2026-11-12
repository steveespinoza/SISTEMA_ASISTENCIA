export type SystemStatus = "online" | "database-unavailable" | "api-unavailable";

export async function getSystemStatus(signal?: AbortSignal): Promise<SystemStatus> {
  try {
    const timeout = AbortSignal.timeout(6000);
    const response = await fetch("/api/health", {
      signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
      cache: "no-store",
    });
    const data: unknown = await response.json();

    if (typeof data === "object" && data !== null && "database" in data) {
      if (response.ok && data.database === "available") {
        return "online";
      }
      if (response.status === 503 && data.database === "unavailable") {
        return "database-unavailable";
      }
    }
  } catch {
    return "api-unavailable";
  }

  return "api-unavailable";
}
