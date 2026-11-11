import { describe, expect, it, vi } from "vitest";
import {
  createTechnologiesHttpProvider,
  parseTechnologyItem,
  parseTechnologyList,
} from "@/data/technologies-http";

const wire = {
  id: 41,
  vendor: "Fortinet",
  product: "FortiOS",
  software_version: "7.2.1",
  note: "VPN gateway mẫu",
  created_by: "synthetic-it",
  created_at: "2026-11-11T16:00:00Z",
  updated_at: "2026-11-11T16:00:00.123Z",
  version: 1,
};

function json(value: unknown, status = 200, headers: HeadersInit = {}) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

function error(status: number, code: string) {
  return json({ error: { code, message: "safe public message" } }, status);
}

describe("W04 technology HTTP parser", () => {
  it("accepts the exact TechnologyView and maps software_version separately", () => {
    expect(parseTechnologyItem(wire)).toEqual(wire);
    expect(parseTechnologyList({ items: [wire] })).toEqual([wire]);
  });

  it.each([
    [{ ...wire, version_id: 1 }],
    [{ ...wire, id: "41" }],
    [{ ...wire, version: 1.5 }],
    [{ ...wire, id: true }],
    [{ ...wire, id: Number.MAX_SAFE_INTEGER + 1 }],
    [{ ...wire, created_at: "2026-11-11T16:00:00+07:00" }],
    [{ ...wire, created_at: "2026-02-30T16:00:00Z" }],
  ])("rejects extra keys, unsafe integers, and non-Z timestamps", (value) => {
    expect(() => parseTechnologyItem(value)).toThrow();
  });

  it("counts Unicode code points for all field bounds", () => {
    expect(() => parseTechnologyItem({ ...wire, vendor: "😀".repeat(128) })).not.toThrow();
    expect(() => parseTechnologyItem({ ...wire, vendor: "😀".repeat(129) })).toThrow();
    expect(() => parseTechnologyItem({ ...wire, product: "p".repeat(257) })).toThrow();
    expect(() => parseTechnologyItem({ ...wire, software_version: "v".repeat(129) })).toThrow();
    expect(() => parseTechnologyItem({ ...wire, note: "n".repeat(501) })).toThrow();
    expect(() => parseTechnologyItem({ ...wire, created_by: "😀".repeat(512) })).not.toThrow();
    expect(() => parseTechnologyItem({ ...wire, created_by: "😀".repeat(513) })).toThrow();
    expect(() => parseTechnologyItem({ ...wire, created_by: "   " })).toThrow();
  });

  it.each([
    [{ ...wire, vendor: " Fortinet" }],
    [{ ...wire, product: "FortiOS " }],
    [{ ...wire, software_version: "\u200b7.2.1" }],
    [{ ...wire, vendor: "line\nbreak" }],
    [{ ...wire, product: "   " }],
  ])("rejects untrimmed, control, format, and blank technology fields", (value) => {
    expect(() => parseTechnologyItem(value)).toThrow();
  });

  it("rejects oversized lists", () => {
    expect(() => parseTechnologyList({ items: Array.from({ length: 1001 }, () => wire) })).toThrow();
  });
});

describe("W04 technology HTTP provider", () => {
  it("sends exact request bodies and never retries mutations", async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(json(wire, 201))
      .mockResolvedValueOnce(json({ ...wire, version: 2 }, 200))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    const provider = createTechnologiesHttpProvider({ fetcher });

    await provider.create({ vendor: "Fortinet", product: "FortiOS", softwareVersion: "7.2.1", note: "x" });
    await provider.update(41, {
      vendor: "Fortinet", product: "FortiOS", softwareVersion: "7.2.2", note: "x", expectedVersion: 1,
    });
    await provider.remove(41, 2);

    expect(fetcher).toHaveBeenCalledTimes(3);
    expect(JSON.parse(String(fetcher.mock.calls[0][1]?.body))).toEqual({
      vendor: "Fortinet", product: "FortiOS", software_version: "7.2.1", note: "x",
    });
    expect(JSON.parse(String(fetcher.mock.calls[1][1]?.body))).toEqual({
      vendor: "Fortinet", product: "FortiOS", software_version: "7.2.2", note: "x", expected_version: 1,
    });
    expect(fetcher.mock.calls[2][0]).toBe("/api/assets/technologies/41?expected_version=2");
  });

  it.each([
    [401, "authentication_required", "authentication-required"],
    [403, "forbidden", "forbidden"],
    [404, "technology_not_found", "not-found"],
    [409, "technology_exists", "conflict"],
    [409, "technology_conflict", "conflict"],
    [413, "request_too_large", "invalid"],
    [415, "unsupported_media_type", "invalid"],
    [422, "invalid_technology", "invalid"],
    [503, "assets_unavailable", "unavailable"],
  ] as const)("maps only the exact %s/%s pair", async (status, code, kind) => {
    const provider = createTechnologiesHttpProvider({ fetcher: vi.fn().mockResolvedValue(error(status, code)) });
    await expect(provider.create({ vendor: "a", product: "b", softwareVersion: "c", note: "" }))
      .rejects.toMatchObject({ kind });
  });

  it("does not trust a known code with the wrong status", async () => {
    const provider = createTechnologiesHttpProvider({
      fetcher: vi.fn().mockResolvedValue(error(500, "technology_conflict")),
    });
    await expect(provider.update(41, {
      vendor: "a", product: "b", softwareVersion: "c", note: "", expectedVersion: 1,
    })).rejects.toMatchObject({ kind: "unknown-mutation" });
  });

  it.each([
    [new Response("{", { status: 200, headers: { "Content-Type": "application/json" } }), "unavailable"],
    [new Response("{}", { status: 200, headers: { "Content-Type": "text/plain" } }), "unavailable"],
    [json({ items: [wire] }, 200, { "Content-Length": String(1024 * 1024 + 1) }), "unavailable"],
    [error(502, "gateway_error"), "unavailable"],
  ] as const)("maps malformed, wrong content type, oversized, and unknown GET responses to unavailable", async (response, kind) => {
    const provider = createTechnologiesHttpProvider({ fetcher: vi.fn().mockResolvedValue(response) });
    await expect(provider.list()).rejects.toMatchObject({ kind });
  });

  it("rejects a streamed body that exceeds the byte cap without Content-Length", async () => {
    const response = new Response("x".repeat(1024 * 1024 + 1), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
    const provider = createTechnologiesHttpProvider({ fetcher: vi.fn().mockResolvedValue(response) });
    await expect(provider.list()).rejects.toMatchObject({ kind: "unavailable" });
  });

  it.each([
    new TypeError("network"),
    new DOMException("aborted", "AbortError"),
  ])("maps network and abort failures by request safety", async (failure) => {
    const list = createTechnologiesHttpProvider({ fetcher: vi.fn().mockRejectedValue(failure) });
    await expect(list.list()).rejects.toMatchObject({ kind: "unavailable" });
    const mutation = createTechnologiesHttpProvider({ fetcher: vi.fn().mockRejectedValue(failure) });
    await expect(mutation.create({ vendor: "a", product: "b", softwareVersion: "c", note: "" }))
      .rejects.toMatchObject({ kind: "unknown-mutation" });
  });

  it("maps a truncated or network-failed mutation to unknown and calls fetch once", async () => {
    const truncated = new Response("{", { status: 201, headers: { "Content-Type": "application/json" } });
    const fetcher = vi.fn().mockResolvedValue(truncated);
    const provider = createTechnologiesHttpProvider({ fetcher });
    await expect(provider.create({ vendor: "a", product: "b", softwareVersion: "c", note: "" }))
      .rejects.toMatchObject({ kind: "unknown-mutation" });
    expect(fetcher).toHaveBeenCalledTimes(1);

    const failedFetcher = vi.fn().mockRejectedValue(new TypeError("network"));
    const failedProvider = createTechnologiesHttpProvider({ fetcher: failedFetcher });
    await expect(failedProvider.remove(41, 1)).rejects.toMatchObject({ kind: "unknown-mutation" });
    expect(failedFetcher).toHaveBeenCalledTimes(1);
  });
});
