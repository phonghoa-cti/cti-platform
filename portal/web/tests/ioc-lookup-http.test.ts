import { afterEach, describe, expect, it, vi } from "vitest";
import {
  createIocHttpDataSource,
  parseIocLookupResponse,
} from "@/data/ioc-lookup-http";
import allowlistedAssetFixture from "@/data/fixtures/w04-fixture-allowlisted-asset.json";
import notFoundAssetFixture from "@/data/fixtures/w04-fixture-not-found-url-asset.json";
import foundAssetFixture from "@/data/fixtures/w04-fixture-found-url-asset.json";
import assetsUnavailableFixture from "@/data/fixtures/w04-fixture-error-assets-unavailable.json";

const foundFixture = {
  ioc: { type: "domain", value: "evil.example", display: "evil[.]example" },
  state: "found",
  found: true,
  allowlisted: false,
  score: {
    value: 40,
    level: "medium",
    reason: "Nguồn tin cậy 0.80 × 1 nguồn xác nhận (0.50) × thấy lần cuối 0 ngày trước (1.00) = 40 điểm",
    parts: { reliability: 0.8, confirmation: 0.5, freshness: 1.0, asset: 1.0 },
  },
  sources: [{
    name: "Synthetic Alpha",
    first_seen: "2026-11-11T00:00:00Z",
    last_seen: "2026-11-11T00:00:00Z",
    tlp: "TLP:GREEN",
  }],
  related: { techniques: [], malware: [], actors: [] },
  asset_match: { matched: false, assets: [] },
  tlp: "TLP:GREEN",
} as const;

const allowlistedFixture = {
  ioc: { type: "ipv4", value: "8.8.8.8", display: "8[.]8[.]8[.]8" },
  state: "allowlisted",
  found: false,
  allowlisted: true,
  score: {
    value: 0,
    level: "low",
    reason: "IOC nằm trong allowlist (hạ tầng hợp pháp) nên điểm = 0.",
    parts: null,
  },
  sources: [],
  related: { techniques: [], malware: [], actors: [] },
  asset_match: { matched: false, assets: [] },
  tlp: "TLP:CLEAR",
} as const;

const notFoundFixture = {
  ioc: { type: "domain", value: "unknown.example", display: "unknown[.]example" },
  state: "not_found",
  found: false,
  allowlisted: false,
  score: null,
  sources: [],
  related: { techniques: [], malware: [], actors: [] },
  asset_match: { matched: false, assets: [] },
  tlp: null,
} as const;

function jsonResponse(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

function copy<T>(value: T): T {
  return structuredClone(value);
}

type MutableFoundFixture = Record<string, unknown> & {
  ioc: { type: string; value: string; display: string };
  state: string;
  found: boolean;
  allowlisted: boolean;
  score: {
    value: unknown;
    level: string;
    reason: string;
    parts: { reliability: number; confirmation: number; freshness: number; asset: number } | null;
  };
  sources: { name: string; first_seen: string; last_seen: string; tlp: string }[];
  related: { techniques: string[]; malware: string[]; actors: string[] };
  asset_match: { matched: boolean; assets: string[] };
  tlp: string | null;
};

function mutableFoundFixture(): MutableFoundFixture {
  return copy(foundFixture) as unknown as MutableFoundFixture;
}

afterEach(() => {
  vi.useRealTimers();
});

describe("strict W02 HTTP response parser", () => {
  it("accepts the three hash-checked W04 backend fixtures without dropping asset metadata", () => {
    expect(parseIocLookupResponse(copy(allowlistedAssetFixture)).asset_match).toEqual({ matched: true, assets: ["congty.vn"] });
    expect(parseIocLookupResponse(copy(notFoundAssetFixture)).asset_match).toEqual({ matched: true, assets: ["congty.vn"] });
    expect(parseIocLookupResponse(copy(foundAssetFixture)).asset_match).toEqual({ matched: true, assets: ["congty.vn"] });
  });

  it("keeps strict malformed-payload rejection for asset names", () => {
    const fixture = copy(foundAssetFixture) as typeof foundAssetFixture & { asset_match: { matched: boolean; assets: string[] } };
    fixture.asset_match.assets = ["x".repeat(254)];
    expect(() => parseIocLookupResponse(fixture)).toThrow();
    expect(() => parseIocLookupResponse({ ...foundAssetFixture, extra: true })).toThrow();
  });
  it("parses the three shared literal fixtures without dropping transport fields", () => {
    expect(parseIocLookupResponse(copy(foundFixture))).toEqual(foundFixture);
    expect(parseIocLookupResponse(copy(allowlistedFixture))).toEqual(allowlistedFixture);
    expect(parseIocLookupResponse(copy(notFoundFixture))).toEqual(notFoundFixture);
  });

  it.each(["ipv4", "ipv6", "domain", "url", "email", "md5", "sha1", "sha256"] as const)(
    "accepts the exact HTTP IOC type %s",
    (type) => {
      const value = mutableFoundFixture();
      value.ioc.type = type;
      expect(parseIocLookupResponse(value).ioc.type).toBe(type);
    },
  );

  it.each(["TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"] as const)(
    "accepts the exact TLP marking %s",
    (tlp) => {
      const value = mutableFoundFixture();
      value.tlp = tlp;
      value.sources[0].tlp = tlp;
      expect(parseIocLookupResponse(value).tlp).toBe(tlp);
    },
  );

  it("rejects an array instead of an object", () => {
    expect(() => parseIocLookupResponse([])).toThrow();
  });

  it.each([
    ["an extra top-level key", (value: MutableFoundFixture) => { value.extra = true; }],
    ["a null nested object", (value: MutableFoundFixture) => { value.related = null as unknown as MutableFoundFixture["related"]; }],
    ["the legacy generic hash type", (value: MutableFoundFixture) => { value.ioc.type = "hash"; }],
    ["a boolean integer", (value: MutableFoundFixture) => { value.score.value = true; }],
    ["a non-integer score", (value: MutableFoundFixture) => { value.score.value = 40.5; }],
    ["a non-finite part", (value: MutableFoundFixture) => { value.score.parts!.reliability = Number.NaN; }],
    ["an out-of-range part", (value: MutableFoundFixture) => { value.score.parts!.confirmation = 1.1; }],
    ["a mismatched score level", (value: MutableFoundFixture) => { value.score.level = "high"; }],
    ["an overlong IOC value by Unicode code point", (value: MutableFoundFixture) => { value.ioc.value = "🔥".repeat(2049); }],
    ["an empty found source list", (value: MutableFoundFixture) => { value.sources = []; }],
    ["a non-UTC source timestamp", (value: MutableFoundFixture) => { value.sources[0].first_seen = "2026-11-11T07:00:00+07:00"; }],
    ["a nonexistent calendar timestamp", (value: MutableFoundFixture) => { value.sources[0].first_seen = "2026-02-30T00:00:00Z"; }],
    ["first_seen after last_seen", (value: MutableFoundFixture) => { value.sources[0].first_seen = "2026-11-12T00:00:00Z"; }],
    ["an asset boolean inconsistent with its list", (value: MutableFoundFixture) => { value.asset_match.matched = true; }],
    ["found booleans inconsistent with state", (value: MutableFoundFixture) => { value.found = false; }],
    ["allowlisted data with related values", (value: MutableFoundFixture) => { value.state = "allowlisted"; value.found = false; value.allowlisted = true; value.score = copy(allowlistedFixture.score) as unknown as MutableFoundFixture["score"]; value.sources = []; value.related.techniques = ["T1566.001"]; value.tlp = "TLP:CLEAR"; }],
  ] as const)("rejects %s", (_name, mutate) => {
    const value = mutableFoundFixture();
    mutate(value);
    expect(() => parseIocLookupResponse(value)).toThrow();
  });
});

describe("W02 same-origin HTTP data source", () => {
  it("preserves asset_match when mapping allowlisted, not_found, and found states", async () => {
    const fixtures = [allowlistedAssetFixture, notFoundAssetFixture, foundAssetFixture];
    for (const fixture of fixtures) {
      const source = createIocHttpDataSource({ fetcher: vi.fn().mockResolvedValue(jsonResponse(fixture)) });
      const result = await source.lookup(fixture.ioc.value);
      expect(result).toMatchObject({ assetMatch: { matched: true, assets: ["congty.vn"] } });
    }
  });

  it("maps the hash-checked assets unavailable error without exposing its message", async () => {
    const source = createIocHttpDataSource({
      fetcher: vi.fn().mockResolvedValue(jsonResponse(assetsUnavailableFixture, 503)),
    });
    await expect(source.lookup("mail.congty.vn")).resolves.toEqual({ state: "unavailable" });
  });
  it.each([
    ["caller found", foundFixture, "result"],
    ["caller allowlist", allowlistedFixture, "result"],
    ["caller unknown", notFoundFixture, "not-found"],
  ] as const)("maps %s using the caller input", async (input, fixture, state) => {
    const dataSource = createIocHttpDataSource({ fetcher: vi.fn().mockResolvedValue(jsonResponse(fixture)) });
    const result = await dataSource.lookup(input);
    expect(result.state).toBe(state);
    if (result.state === "result") {
      expect(result.input).toBe(input);
      expect(result.enrichment).toEqual({});
      expect(result.sources[0]?.lastSeen).toBe(fixture === foundFixture ? "2026-11-11T00:00:00Z" : undefined);
      expect(result.assetMatch).toEqual({ matched: false, assets: [] });
    }
  });

  it("encodes &, # and Unicode in exactly one value query without identity headers", async () => {
    const fetcher = vi.fn().mockResolvedValue(jsonResponse(notFoundFixture));
    const input = "https://ví-dụ.example/a?x=1&y=#mục";
    await createIocHttpDataSource({ fetcher }).lookup(input);

    expect(fetcher).toHaveBeenCalledTimes(1);
    const [url, init] = fetcher.mock.calls[0] as [string, RequestInit];
    expect(url.startsWith("/api/ioc?")).toBe(true);
    const query = new URLSearchParams(url.slice(url.indexOf("?") + 1));
    expect([...query.keys()]).toEqual(["value"]);
    expect(query.getAll("value")).toEqual([input]);
    expect(init).toEqual(expect.objectContaining({
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
      redirect: "error",
      headers: { Accept: "application/json" },
    }));
    expect(Object.keys(init.headers as Record<string, string>)).toEqual(["Accept"]);
    expect(init.body).toBeUndefined();
  });

  it.each([
    [401, "authentication_required", "authentication-required"],
    [403, "forbidden", "forbidden"],
    [422, "invalid_ioc", "invalid"],
    [422, "private_ip", "private-ip"],
    [503, "lookup_unavailable", "unavailable"],
  ] as const)("maps HTTP %i %s to %s", async (status, code, state) => {
    const response = { error: { code, message: "Thông báo cố định" } };
    const source = createIocHttpDataSource({ fetcher: vi.fn().mockResolvedValue(jsonResponse(response, status)) });
    await expect(source.lookup("evil.example")).resolves.toEqual({ state });
  });

  it.each([
    [401, "forbidden"],
    [403, "authentication_required"],
    [422, "lookup_unavailable"],
    [503, "private_ip"],
    [404, "lookup_unavailable"],
  ] as const)("maps mismatched HTTP %i/%s to unavailable", async (status, code) => {
    const response = { error: { code, message: "do not render me" } };
    const source = createIocHttpDataSource({ fetcher: vi.fn().mockResolvedValue(jsonResponse(response, status)) });
    await expect(source.lookup("evil.example")).resolves.toEqual({ state: "unavailable" });
  });

  it("rejects a valid found fixture returned with non-contract success status 201", async () => {
    const source = createIocHttpDataSource({
      fetcher: vi.fn().mockResolvedValue(jsonResponse(foundFixture, 201)),
    });

    await expect(source.lookup("evil.example")).resolves.toEqual({ state: "unavailable" });
  });

  it.each([
    ["HTML success", new Response("<html>login</html>", { headers: { "Content-Type": "text/html" } })],
    ["invalid JSON", new Response("{", { headers: { "Content-Type": "application/json" } })],
    ["missing JSON content type", new Response(JSON.stringify(foundFixture))],
    ["extra error field", jsonResponse({ error: { code: "forbidden", message: "x", raw: "secret" } }, 403)],
  ])("does not expose %s as a result", async (_name, response) => {
    const source = createIocHttpDataSource({ fetcher: vi.fn().mockResolvedValue(response) });
    await expect(source.lookup("evil.example")).resolves.toEqual({ state: "unavailable" });
  });

  it("does not retry a rejected request or fall back to fixtures", async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error("offline"));
    await expect(createIocHttpDataSource({ fetcher }).lookup("hxxp://Evil[.]COM/a"))
      .resolves.toEqual({ state: "unavailable" });
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("aborts a pending fetch at 10 seconds and clears the timeout", async () => {
    vi.useFakeTimers();
    const fetcher = vi.fn((_input: RequestInfo | URL, init?: RequestInit) => new Promise<Response>((_resolve, reject) => {
      init?.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")), { once: true });
    }));
    const lookup = createIocHttpDataSource({ fetcher }).lookup("evil.example");
    await vi.advanceTimersByTimeAsync(10_000);

    await expect(lookup).resolves.toEqual({ state: "unavailable" });
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
    const lookup = createIocHttpDataSource({
      fetcher: vi.fn().mockResolvedValue(new Response(stream, { headers: { "Content-Type": "application/json" } })),
    }).lookup("evil.example");
    await vi.advanceTimersByTimeAsync(10_000);

    await expect(lookup).resolves.toEqual({ state: "unavailable" });
    expect(cancel).toHaveBeenCalledTimes(1);
    expect(vi.getTimerCount()).toBe(0);
  });

  it("cancels a body once it exceeds 1 MiB", async () => {
    const cancel = vi.fn();
    const stream = new ReadableStream<Uint8Array>({
      start(controller) { controller.enqueue(new Uint8Array(1024 * 1024 + 1)); },
      cancel,
    });
    const source = createIocHttpDataSource({
      fetcher: vi.fn().mockResolvedValue(new Response(stream, { headers: { "Content-Type": "application/json" } })),
    });

    await expect(source.lookup("evil.example")).resolves.toEqual({ state: "unavailable" });
    expect(cancel).toHaveBeenCalledTimes(1);
  });

  it("cancels an unread body rejected by its declared size", async () => {
    const cancel = vi.fn();
    const stream = new ReadableStream<Uint8Array>({ cancel });
    const response = new Response(stream, {
      headers: {
        "Content-Type": "application/json",
        "Content-Length": String(1024 * 1024 + 1),
      },
    });
    const source = createIocHttpDataSource({ fetcher: vi.fn().mockResolvedValue(response) });

    await expect(source.lookup("evil.example")).resolves.toEqual({ state: "unavailable" });
    expect(cancel).toHaveBeenCalledTimes(1);
  });
});
