import { afterEach, describe, expect, it, vi } from "vitest";
import { getSystemStatus } from "./system-status";

afterEach(() => vi.unstubAllGlobals());

describe("getSystemStatus", () => {
  it.each([
    [200, { database: "available" }, "online"],
    [503, { database: "unavailable" }, "database-unavailable"],
    [503, { error: "Gateway error" }, "api-unavailable"],
    [200, { database: "unknown" }, "api-unavailable"],
  ])("interpreta la respuesta HTTP %s con %j", async (status, body, expected) => {
    const fetchMock = vi.fn().mockResolvedValue(Response.json(body, { status }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(getSystemStatus()).resolves.toBe(expected);
    expect(fetchMock).toHaveBeenCalledWith("/api/health", expect.any(Object));
  });

  it("indica cuando la API no responde", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Network error")));

    await expect(getSystemStatus()).resolves.toBe("api-unavailable");
  });
});
