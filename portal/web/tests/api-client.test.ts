import { describe, expect, it, vi } from "vitest";
import {
  ApiClientError,
  createDraftApi,
  parseDecision,
  parseDraftDetail,
  parseDraftPage,
} from "@/data/api-client";
import regular from "@/data/fixtures/01-regular.json";

const review = {
  status: "pending",
  version: 0,
  created_by_subject: "author-sub",
  decided_by_subject: null,
  decided_at: null,
  reason: null,
};

const detail = { ...regular, review };
const summary = {
  id: regular.id,
  created_at: regular.created_at,
  status: "pending",
  source: regular.source,
  language: regular.language,
  tlp: regular.tlp,
  item_count: regular.items.length,
  injection_warning: regular.injection_warning,
  review_status: "pending",
  review_version: 0,
};
const selection = {
  review_version: 0,
  selection_version: 0,
  selected_indices: [0],
  selected_sha256: "a".repeat(64),
  saved_by_subject: null,
  saved_at: null,
  changed: false,
  ai_extracted_count: 1,
  ai_eligible_count: 1,
  human_deselected_count: 0,
  selection_save_count: 0,
};
const summaryV1 = { ...summary, selection_version: 0 };

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("W05 runtime parsers", () => {
  it("parses the exact summary, detail, and flat decision response shapes", () => {
    expect(parseDraftPage({ items: [summary], next_before_id: regular.id })).toEqual({
      items: [summary],
      next_before_id: regular.id,
    });
    expect(parseDraftDetail(detail).review).toEqual(review);
    expect(parseDecision({
      draft_id: regular.id,
      status: "approved",
      version: 1,
      decided_by_subject: "analyst-sub",
      decided_at: "2026-11-11T01:02:03+00:00",
      reason: null,
    })).toEqual(expect.objectContaining({ status: "approved", version: 1 }));
  });

  it("uses review status even though stored payload status remains pending", () => {
    expect(parseDraftDetail({
      ...detail,
      status: "pending",
      review: { ...review, status: "approved", version: 1, decided_by_subject: "analyst-sub", decided_at: "2026-11-11T01:02:03+00:00" },
    }).review.status).toBe("approved");
  });

  it.each([
    ["unsafe summary id", { items: [{ ...summary, id: Number.MAX_SAFE_INTEGER + 1 }], next_before_id: null }, parseDraftPage],
    ["unsafe cursor", { items: [summary], next_before_id: Number.MAX_SAFE_INTEGER + 1 }, parseDraftPage],
    ["unsafe detail id", { ...detail, id: Number.MAX_SAFE_INTEGER + 1 }, parseDraftDetail],
    ["wrong boolean", { items: [{ ...summary, injection_warning: 1 }], next_before_id: null }, parseDraftPage],
    ["wrong array", { ...detail, items: {} }, parseDraftDetail],
    ["wrong enum", { ...detail, tlp: "TLP:BLUE" }, parseDraftDetail],
    ["wrong nullability", { ...detail, review: { ...review, reason: 1 } }, parseDraftDetail],
  ])("rejects %s", (_name, value, parser) => {
    expect(() => parser(value)).toThrow();
  });

  it.each([
    ["empty created_at", { created_at: "" }],
    ["invalid status", { status: "approved" }],
    ["invalid language", { language: "fr" }],
    ["invalid TLP", { tlp: "INVALID" }],
    ["negative item_count", { item_count: -1 }],
    ["invalid review_status", { review_status: "approved" }],
  ])("keeps the legacy summary strict for %s", (_name, change) => {
    expect(() => parseDraftPage({ items: [{ ...summary, ...change }], next_before_id: null })).toThrow(ApiClientError);
  });

  it("keeps legacy duplicate IDs and empty decision actors invalid", () => {
    expect(() => parseDraftPage({ items: [summary, summary], next_before_id: null })).toThrow(ApiClientError);
    expect(() => parseDecision({ draft_id: 1, status: "approved", version: 1, decided_by_subject: "", decided_at: "2026-11-11T00:00:00Z", reason: null })).toThrow(ApiClientError);
  });
});

describe("same-origin draft API client", () => {
  it("paginates with limit 20 and before_id using same-origin no-store requests", async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ items: [summaryV1], next_before_id: 6 }))
      .mockResolvedValueOnce(jsonResponse({ items: [], next_before_id: null }));
    const api = createDraftApi(fetcher);

    await api.list();
    await api.list(6);

    expect(fetcher).toHaveBeenNthCalledWith(1, "/api/v1/drafts?limit=20", expect.objectContaining({ credentials: "same-origin", cache: "no-store" }));
    expect(fetcher).toHaveBeenNthCalledWith(2, "/api/v1/drafts?limit=20&before_id=6", expect.objectContaining({ credentials: "same-origin", cache: "no-store" }));
  });

  it("posts only the decision contract and expected detail version", async () => {
    const fetcher = vi.fn().mockResolvedValue(jsonResponse({
      draft_id: regular.id,
      status: "rejected",
      version: 1,
      decided_by_subject: "analyst-sub",
      decided_at: "2026-11-11T01:02:03+00:00",
      reason: "Không đủ bằng chứng",
      selection_version: 0,
      selected_indices: [0],
      selected_sha256: "a".repeat(64),
    }));

    await createDraftApi(fetcher).decide(regular.id, { decision: "reject", expected_version: 0, reason: "Không đủ bằng chứng" }, selection);

    expect(fetcher).toHaveBeenCalledWith(`/api/v1/drafts/${regular.id}/decision`, {
      method: "POST",
      credentials: "same-origin",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision: "reject", expected_version: 0, reason: "Không đủ bằng chứng" }),
    });
  });

  it.each([
    [401, "authentication_required"], [403, "forbidden"], [404, "draft_not_found"], [409, "draft_conflict"],
    [413, "request_too_large"], [415, "unsupported_media_type"], [422, "invalid_request"],
  ])("maps exact HTTP %s envelopes without exposing the server message", async (status, code) => {
    const api = createDraftApi(vi.fn().mockResolvedValue(jsonResponse({ error: { code, message: "SECRET raw backend" } }, status)));
    await expect(api.list()).rejects.toMatchObject({ status });
    await expect(api.list()).rejects.not.toThrow(/SECRET/);
  });

  it("treats 5xx and malformed error envelopes as unsafe service results", async () => {
    const unavailable = createDraftApi(vi.fn().mockResolvedValue(jsonResponse({ error: { code: "review_unavailable", message: "secret" } }, 503)));
    const malformed = createDraftApi(vi.fn().mockResolvedValue(jsonResponse({ error: { message: "secret" } }, 409)));
    await expect(unavailable.list()).rejects.toMatchObject({ kind: "service", status: undefined });
    await expect(malformed.list()).rejects.toMatchObject({ kind: "service", status: undefined });
  });

  it("maps network, non-JSON, and malformed 200 responses to safe client errors", async () => {
    const network = createDraftApi(vi.fn().mockRejectedValue(new Error("token=secret")));
    const nonJson = createDraftApi(vi.fn().mockResolvedValue(new Response("<html>secret</html>", { status: 200 })));
    const malformed = createDraftApi(vi.fn().mockResolvedValue(jsonResponse({ items: "wrong", next_before_id: null })));

    for (const request of [network.list(), nonJson.list(), malformed.list()]) {
      await expect(request).rejects.toBeInstanceOf(ApiClientError);
      await expect(request).rejects.not.toThrow(/secret|html/i);
    }
  });
});
