import { afterEach, describe, expect, it, vi } from "vitest";
import {
  AssetDataError,
  createAssetsHttpDataSource,
  parseAssetItem,
  parseAssetList,
} from "@/data/assets-http";
import assetsUnavailableFixture from "@/data/fixtures/w04-fixture-error-assets-unavailable.json";

const domain = {
  id: 1,
  type: "domain",
  value: "congty.vn",
  note: "Cổng thư điện tử",
  created_by: "it-user",
  created_at: "2026-11-11T00:00:00Z",
  updated_at: "2026-11-11T00:00:00Z",
  version: 1,
} as const;

function json(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

afterEach(() => vi.useRealTimers());

describe("strict W04 assets HTTP parser", () => {
  it("accepts one exact asset and list envelope", () => {
    expect(parseAssetItem(structuredClone(domain))).toEqual(domain);
    expect(parseAssetList({ items: [structuredClone(domain)] })).toEqual([domain]);
  });

  it.each([
    ["extra item field", { ...domain, canonical_value: domain.value }],
    ["unsafe integer id", { ...domain, id: Number.MAX_SAFE_INTEGER + 1 }],
    ["bad type", { ...domain, type: "technology" }],
    ["empty value", { ...domain, value: "" }],
    ["overlong note", { ...domain, note: "x".repeat(501) }],
    ["invalid timestamp", { ...domain, updated_at: "yesterday" }],
    ["nonexistent UTC date", { ...domain, updated_at: "2026-02-30T00:00:00Z" }],
    ["zero version", { ...domain, version: 0 }],
  ])("rejects %s", (_name, value) => {
    expect(() => parseAssetItem(value)).toThrow();
  });

  it("rejects extra list envelope keys", () => {
    expect(() => parseAssetList({ items: [], total: 0 })).toThrow();
  });
});

describe("W04 same-origin assets adapter", () => {
  it("lists the selected type with one same-origin GET and no identity header", async () => {
    const fetcher = vi.fn().mockResolvedValue(json({ items: [domain] }));
    const result = await createAssetsHttpDataSource({ fetcher }).list("domain");

    expect(result).toEqual([{
      id: 1,
      type: "domain",
      value: "congty.vn",
      note: "Cổng thư điện tử",
      createdBy: "it-user",
      createdAt: "2026-11-11T00:00:00Z",
      updatedAt: "2026-11-11T00:00:00Z",
      version: 1,
    }]);
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(fetcher).toHaveBeenCalledWith("/api/assets?type=domain", expect.objectContaining({
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
      redirect: "error",
      headers: { Accept: "application/json" },
    }));
  });

  it("creates once with the exact JSON body and does not add auth or role", async () => {
    const fetcher = vi.fn().mockResolvedValue(json(domain, 201));
    await createAssetsHttpDataSource({ fetcher }).create({
      type: "domain",
      value: "congty.vn",
      note: "Cổng thư điện tử",
    });

    expect(fetcher).toHaveBeenCalledTimes(1);
    const [url, init] = fetcher.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/assets");
    expect(init.method).toBe("POST");
    expect(init.headers).toEqual({ Accept: "application/json", "Content-Type": "application/json" });
    expect(JSON.parse(init.body as string)).toEqual({ type: "domain", value: "congty.vn", note: "Cổng thư điện tử" });
  });

  it("updates and deletes with the server version contract", async () => {
    const updated = { ...domain, value: "portal.congty.vn", version: 2 };
    const fetcher = vi.fn()
      .mockResolvedValueOnce(json(updated))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    const source = createAssetsHttpDataSource({ fetcher });

    await expect(source.update(1, {
      type: "domain", value: "portal.congty.vn", note: "", expectedVersion: 1,
    })).resolves.toEqual({
      id: 1,
      type: "domain",
      value: "portal.congty.vn",
      note: "Cổng thư điện tử",
      createdBy: "it-user",
      createdAt: "2026-11-11T00:00:00Z",
      updatedAt: "2026-11-11T00:00:00Z",
      version: 2,
    });
    await expect(source.remove(1, 2)).resolves.toBeUndefined();

    expect(fetcher.mock.calls[0][0]).toBe("/api/assets/1");
    expect(JSON.parse(fetcher.mock.calls[0][1].body)).toEqual({
      type: "domain", value: "portal.congty.vn", note: "", expected_version: 1,
    });
    expect(fetcher.mock.calls[1][0]).toBe("/api/assets/1?expected_version=2");
    expect(fetcher.mock.calls[1][1].method).toBe("DELETE");
  });

  it.each([
    [401, "authentication_required", "authentication-required"],
    [403, "forbidden", "forbidden"],
    [409, "asset_exists", "conflict"],
    [409, "asset_conflict", "conflict"],
    [422, "invalid_asset", "invalid"],
    [503, "assets_unavailable", "unavailable"],
  ] as const)("maps HTTP %i %s to %s", async (status, code, kind) => {
    const fetcher = vi.fn().mockResolvedValue(json({ error: { code, message: "Không hiển thị raw" } }, status));
    await expect(createAssetsHttpDataSource({ fetcher }).create({ type: "domain", value: "x.vn", note: "" }))
      .rejects.toMatchObject({ name: "AssetDataError", kind });
  });

  it("classifies a lost mutation response as unknown and never replays it", async () => {
    const fetcher = vi.fn().mockRejectedValue(new TypeError("connection reset"));
    const source = createAssetsHttpDataSource({ fetcher });

    await expect(source.create({ type: "domain", value: "congty.vn", note: "" }))
      .rejects.toEqual(new AssetDataError("unknown-mutation"));
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("maps a rejected GET to unavailable without retry", async () => {
    const fetcher = vi.fn().mockRejectedValue(new TypeError("offline"));
    await expect(createAssetsHttpDataSource({ fetcher }).list("domain"))
      .rejects.toEqual(new AssetDataError("unavailable"));
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("maps the hash-checked backend unavailable fixture without exposing its message", async () => {
    const fetcher = vi.fn().mockResolvedValue(json(assetsUnavailableFixture, 503));
    await expect(createAssetsHttpDataSource({ fetcher }).list("domain"))
      .rejects.toEqual(new AssetDataError("unavailable"));
  });

  it("keeps the timeout over fetch and clears its timer", async () => {
    vi.useFakeTimers();
    const fetcher = vi.fn((_input: RequestInfo | URL, init?: RequestInit) => new Promise<Response>((_resolve, reject) => {
      init?.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")), { once: true });
    }));
    const pending = createAssetsHttpDataSource({ fetcher }).list("domain");
    const rejection = expect(pending).rejects.toEqual(new AssetDataError("unavailable"));
    await vi.advanceTimersByTimeAsync(10_000);

    await rejection;
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(vi.getTimerCount()).toBe(0);
  });

  it("keeps the timeout over body reading and cancels a stalled reader", async () => {
    vi.useFakeTimers();
    const cancel = vi.fn();
    const stream = new ReadableStream<Uint8Array>({
      pull() { return new Promise<void>(() => undefined); },
      cancel,
    });
    const pending = createAssetsHttpDataSource({
      fetcher: vi.fn().mockResolvedValue(new Response(stream, { headers: { "Content-Type": "application/json" } })),
    }).list("domain");
    const rejection = expect(pending).rejects.toEqual(new AssetDataError("unavailable"));
    await vi.advanceTimersByTimeAsync(10_000);

    await rejection;
    expect(cancel).toHaveBeenCalledTimes(1);
    expect(vi.getTimerCount()).toBe(0);
  });

  it("cancels a response body once it exceeds 1 MiB", async () => {
    const cancel = vi.fn();
    const stream = new ReadableStream<Uint8Array>({
      start(controller) { controller.enqueue(new Uint8Array(1024 * 1024 + 1)); },
      cancel,
    });
    const source = createAssetsHttpDataSource({
      fetcher: vi.fn().mockResolvedValue(new Response(stream, { headers: { "Content-Type": "application/json" } })),
    });

    await expect(source.list("domain")).rejects.toEqual(new AssetDataError("unavailable"));
    expect(cancel).toHaveBeenCalledTimes(1);
  });
});
