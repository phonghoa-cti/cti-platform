import { describe, expect, it, vi } from "vitest";
import {
  ApiClientError,
  createDraftApi,
  parseDecisionV1,
  parseDraftDetailV1,
  parseDraftPageV1,
  parseSelectionView,
} from "@/data/api-client";
import regular from "@/data/fixtures/01-regular.json";

const hash = "a".repeat(64);
const review = {
  status: "pending",
  version: 4,
  created_by_subject: "author-sub",
  decided_by_subject: null,
  decided_at: null,
  reason: null,
};
const selection = {
  review_version: 4,
  selection_version: 4,
  selected_indices: [0],
  selected_sha256: hash,
  saved_by_subject: "analyst-sub",
  saved_at: "2026-11-11T01:00:00+00:00",
  changed: false,
  ai_extracted_count: regular.items.length,
  ai_eligible_count: 1,
  human_deselected_count: 0,
  selection_save_count: 1,
};
const detail = { ...regular, review, selection };
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
  review_version: 4,
  selection_version: 4,
};

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

describe("W05 v1 selection contract", () => {
  it("parses exact list/detail/selection and keeps read selections above the save limit", () => {
    expect(parseDraftPageV1({ items: [summary], next_before_id: null }).items[0].selection_version).toBe(4);
    expect(parseDraftDetailV1(detail).selection.selected_indices).toEqual([0]);
    expect(parseSelectionView({ ...selection, selected_indices: Array.from({ length: 1025 }, (_, index) => index), ai_eligible_count: 1025 }).selected_indices).toHaveLength(1025);
  });

  it.each([
    ["extra selection key", { ...selection, extra: true }, parseSelectionView],
    ["boolean version", { ...selection, review_version: true }, parseSelectionView],
    ["unsafe version", { ...selection, selection_version: Number.MAX_SAFE_INTEGER + 1 }, parseSelectionView],
    ["duplicate index", { ...selection, selected_indices: [0, 0] }, parseSelectionView],
    ["unsorted indices", { ...selection, selected_indices: [1, 0] }, parseSelectionView],
    ["bad hash", { ...selection, selected_sha256: "ABC" }, parseSelectionView],
    ["noneligible detail index", { ...detail, selection: { ...selection, selected_indices: [1] } }, parseDraftDetailV1],
    ["review version mismatch", { ...detail, selection: { ...selection, review_version: 3 } }, parseDraftDetailV1],
  ])("rejects %s", (_name, value, parser) => {
    expect(() => parser(value)).toThrow(ApiClientError);
  });

  it("uses v1 routes and sends an exact sorted save body", async () => {
    const saved = { ...selection, review_version: 5, selection_version: 5, selected_indices: [], human_deselected_count: 1, changed: true };
    const fetcher = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ items: [summary], next_before_id: null }))
      .mockResolvedValueOnce(jsonResponse(detail))
      .mockResolvedValueOnce(jsonResponse(saved));
    const api = createDraftApi(fetcher);

    await api.list();
    await api.detail(regular.id);
    await api.saveSelection(regular.id, { expected_version: 4, selected_indices: [] });

    expect(fetcher).toHaveBeenNthCalledWith(1, "/api/v1/drafts?limit=20", expect.objectContaining({ credentials: "same-origin", cache: "no-store" }));
    expect(fetcher).toHaveBeenNthCalledWith(2, `/api/v1/drafts/${regular.id}`, expect.any(Object));
    expect(fetcher).toHaveBeenNthCalledWith(3, `/api/v1/drafts/${regular.id}/selection`, {
      method: "POST",
      credentials: "same-origin",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ expected_version: 4, selected_indices: [] }),
    });
  });

  it("rejects save input over 1024 before fetch but accepts exactly 1024", async () => {
    const fetcher = vi.fn().mockResolvedValue(jsonResponse({ ...selection, selected_indices: Array.from({ length: 1024 }, (_, index) => index), ai_eligible_count: 1024 }));
    const api = createDraftApi(fetcher);
    await api.saveSelection(regular.id, { expected_version: 4, selected_indices: Array.from({ length: 1024 }, (_, index) => index) });
    expect(() => api.saveSelection(regular.id, { expected_version: 4, selected_indices: Array.from({ length: 1025 }, (_, index) => index) })).toThrow(ApiClientError);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("validates a decision against the pinned draft, version, status and saved snapshot", async () => {
    const response = {
      draft_id: regular.id,
      status: "approved",
      version: 5,
      decided_by_subject: "analyst-sub",
      decided_at: "2026-11-11T01:02:03+00:00",
      reason: null,
      selection_version: 4,
      selected_indices: [0],
      selected_sha256: hash,
    };
    expect(parseDecisionV1(response, regular.id, { decision: "approve", expected_version: 4 }, selection)).toEqual(response);
    expect(() => parseDecisionV1({ ...response, draft_id: 99 }, regular.id, { decision: "approve", expected_version: 4 }, selection)).toThrow();
    expect(() => parseDecisionV1({ ...response, selected_indices: [] }, regular.id, { decision: "approve", expected_version: 4 }, selection)).toThrow();
    expect(() => parseDecisionV1({ ...response, version: Number.MAX_SAFE_INTEGER }, regular.id, { decision: "approve", expected_version: Number.MAX_SAFE_INTEGER }, selection)).toThrow();
  });

  it("treats network, 5xx, malformed and mismatched POST results as unsafe client errors", async () => {
    const cases = [
      vi.fn().mockRejectedValue(new Error("network secret")),
      vi.fn().mockResolvedValue(jsonResponse({ error: {} }, 503)),
      vi.fn().mockResolvedValue(new Response("not json", { status: 200 })),
      vi.fn().mockResolvedValue(jsonResponse({ ...selection, selected_indices: [1] })),
    ];
    for (const fetcher of cases) {
      await expect(createDraftApi(fetcher).saveSelection(regular.id, { expected_version: 4, selected_indices: [0] })).rejects.toBeInstanceOf(ApiClientError);
    }
  });
});
