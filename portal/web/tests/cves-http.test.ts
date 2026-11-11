import { describe, expect, it, vi } from "vitest";
import {
  createCvesHttpProvider,
  parseCveResponse,
} from "@/data/cves-http";
import detailFixture from "@/tests/fixtures/w03-detail.json";
import summaryFixture from "@/tests/fixtures/w03-summary.json";
import { createSampleCveProvider } from "@/data/cves";

const detailItem = {
  cve_id: "CVE-2026-1001",
  title: "FortiOS synthetic advisory <script>alert(1)</script>",
  kev: true,
  kev_due_date: "2026-12-01",
  kev_as_of: "2026-11-01",
  epss_score: 0,
  epss_percentile: 0,
  epss_as_of: "2026-11-01",
  cvss_base_score: 9.8,
  cvss_version: "3.1",
  published_at: "2026-10-01T12:00:00Z",
  advisory_url: "https://example.invalid/advisories/CVE-2026-1001",
  matches: [{
    technology_id: 41,
    vendor: "Fortinet",
    product: "FortiOS",
    software_version: "7.2.1",
    match_reason: "vendor_product_exact_casefold",
    version_assessment: "not_performed",
  }],
  priority: 1,
};

const detail = {
  view: "detail",
  items: [detailItem],
  summary: { matched_cves: 1, kev_cves: 1 },
  page: { next_cursor: "opaque-cursor", limit: 10 },
  source: {
    kind: "synthetic",
    dataset_id: `sha256:${"a".repeat(64)}`,
    source_as_of: "2026-11-01T00:00:00Z",
    retrieved_at: "2026-11-01T01:00:00.123456Z",
  },
  notice: "Liên quan theo tên sản phẩm; cần kiểm tra phiên bản/phạm vi bị ảnh hưởng trước khi vá.",
};

const summary = {
  ...detail,
  view: "summary",
  items: [{
    cve_id: "CVE-2026-1001",
    title: "FortiOS synthetic advisory",
    kev: true,
    epss_score: 0,
    cvss_base_score: null,
    priority: 1,
    match_count: 1,
  }],
};

function json(value: unknown, status = 200, headers: HeadersInit = {}) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

function error(status: number, code: string) {
  return json({ error: { code, message: "safe message" } }, status);
}

describe("W03 CVE strict parser", () => {
  it("parses exact detail and preserves score zero separately from null", () => {
    const parsed = parseCveResponse(detailFixture);
    expect(parsed.view).toBe("detail");
    if (parsed.view !== "detail") throw new Error("wrong view");
    expect(parsed.items[0].epssScore).toBe(0);
    expect(parsed.items[0].matches[0].softwareVersion).toBe("7.2.1");
  });

  it("parses summary without detail-only fields", () => {
    const parsed = parseCveResponse(summaryFixture);
    expect(parsed.view).toBe("summary");
    expect(parsed.items[0]).toEqual(expect.objectContaining({ matchCount: 1, cvssBaseScore: null }));
    expect(parsed.items[0]).not.toHaveProperty("matches");
    expect(parsed.items[0]).not.toHaveProperty("advisoryUrl");
  });

  it.each([
    { ...detail, extra: true },
    { ...detail, view: "full" },
    { ...detail, items: [{ ...detailItem, hidden: "x" }] },
    { ...detail, items: [{ ...detailItem, epss_score: Number.NaN }] },
    { ...detail, items: [{ ...detailItem, epss_score: true }] },
    { ...detail, items: [{ ...detailItem, cvss_base_score: 11 }] },
    { ...detail, items: [{ ...detailItem, kev: false, kev_due_date: "2026-12-01" }] },
    { ...detail, items: [{ ...detailItem, epss_score: null, epss_percentile: 0 }] },
    { ...detail, items: [{ ...detailItem, advisory_url: "http://example.invalid/x" }] },
    { ...detail, items: [{ ...detailItem, published_at: "2026-02-30T00:00:00Z" }] },
    { ...detail, page: { next_cursor: "é", limit: 10 } },
    { ...detail, source: { ...detail.source, dataset_id: `sha256:${"A".repeat(64)}` } },
    { ...summary, items: [{ ...summary.items[0], matches: [] }] },
  ])("rejects malformed, extra, non-finite, inconsistent, or hidden-field wire", (value) => {
    expect(() => parseCveResponse(value)).toThrow();
  });
});

describe("W03 CVE HTTP provider", () => {
  it("sends one GET with no-store and exact filters including opaque cursor", async () => {
    const fetcher = vi.fn().mockResolvedValue(json(detail));
    const provider = createCvesHttpProvider({ fetcher });
    await provider.list({ kev: true, technologyId: 41, q: "CVE-2026", limit: 10, cursor: "opaque-cursor" });
    expect(fetcher).toHaveBeenCalledTimes(1);
    const [url, init] = fetcher.mock.calls[0];
    expect(url).toBe("/api/cves?kev=true&asset_id=41&q=CVE-2026&limit=10&cursor=opaque-cursor");
    expect(init).toMatchObject({ method: "GET", cache: "no-store", credentials: "same-origin", redirect: "error" });
    expect(init.body).toBeUndefined();
  });

  it.each([
    [401, "authentication_required", "authentication-required"],
    [403, "forbidden", "forbidden"],
    [404, "technology_not_found", "not-found"],
    [422, "invalid_cve_query", "invalid"],
    [409, "cve_snapshot_changed", "snapshot-changed"],
    [503, "cves_unavailable", "unavailable"],
  ] as const)("maps only exact %s/%s errors", async (status, code, kind) => {
    const provider = createCvesHttpProvider({ fetcher: vi.fn().mockResolvedValue(error(status, code)) });
    await expect(provider.list({ kev: true, technologyId: null, q: "", limit: 10, cursor: null }))
      .rejects.toMatchObject({ kind });
  });

  it("maps wrong status/code, network, malformed, and over-1MiB responses to unavailable", async () => {
    for (const response of [
      error(500, "cve_snapshot_changed"),
      new Response("{", { status: 200, headers: { "Content-Type": "application/json" } }),
      json(detail, 200, { "Content-Length": String(1024 * 1024 + 1) }),
      new Response(JSON.stringify(detail), { status: 200, headers: { "Content-Type": "text/plain" } }),
    ]) {
      const provider = createCvesHttpProvider({ fetcher: vi.fn().mockResolvedValue(response) });
      await expect(provider.list({ kev: true, technologyId: null, q: "", limit: 10, cursor: null }))
        .rejects.toMatchObject({ kind: "unavailable" });
    }
    const provider = createCvesHttpProvider({ fetcher: vi.fn().mockRejectedValue(new TypeError("network")) });
    await expect(provider.list({ kev: true, technologyId: null, q: "", limit: 10, cursor: null }))
      .rejects.toMatchObject({ kind: "unavailable" });
  });

  it("rejects a streamed body over 1 MiB and never retries", async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response("x".repeat(1024 * 1024 + 1), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }));
    const provider = createCvesHttpProvider({ fetcher });
    await expect(provider.list({ kev: false, technologyId: null, q: "", limit: 10, cursor: null }))
      .rejects.toMatchObject({ kind: "unavailable" });
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});

describe("W03 sample CVE provider", () => {
  it("provides at least 12 clearly synthetic CVEs for deterministic pagination", async () => {
    const result = await createSampleCveProvider().list({ kev: false, technologyId: null, q: "", limit: 100, cursor: null });
    expect(result.view).toBe("detail");
    expect(result.items).toHaveLength(12);
    expect(result.source.kind).toBe("synthetic");
    expect(result.items.every((item) => item.title.includes("tổng hợp"))).toBe(true);
  });

  it("keeps sample priorities continuous after a fixture filter", async () => {
    const result = await createSampleCveProvider().list({ kev: false, technologyId: 101, q: "", limit: 10, cursor: null });
    expect(result.items.map((item) => item.priority)).toEqual([1, 2, 3, 4]);
  });
});
