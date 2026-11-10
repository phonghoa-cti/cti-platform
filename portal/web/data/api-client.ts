import { parseDraft, supportedTlp, type Draft, type Tlp } from "@/data/draft-adapter";

export type ReviewStatus = "pending" | "approved" | "rejected";
export type DecisionRequest =
  | { decision: "approve"; expected_version: number }
  | { decision: "reject"; expected_version: number; reason: string };
export type SelectionSaveRequest = { expected_version: number; selected_indices: number[] };

export interface DraftSummary {
  id: number; created_at: string; status: "pending"; source: { name: string; sha256: string };
  language: "vi" | "en"; tlp: Tlp; item_count: number; injection_warning: boolean;
  review_status: "pending"; review_version: number; selection_version: number;
}
export interface DraftPage { items: DraftSummary[]; next_before_id: number | null }
export interface DraftReviewState {
  status: ReviewStatus; version: number; created_by_subject: string | null;
  decided_by_subject: string | null; decided_at: string | null; reason: string | null;
}
export interface SelectionView {
  review_version: number; selection_version: number; selected_indices: number[]; selected_sha256: string;
  saved_by_subject: string | null; saved_at: string | null; changed: boolean;
  ai_extracted_count: number; ai_eligible_count: number; human_deselected_count: number; selection_save_count: number;
}
export interface DraftDetail extends Draft { review: DraftReviewState; selection: SelectionView }
export interface DecisionResponse {
  draft_id: number; status: "approved" | "rejected"; version: number; decided_by_subject: string;
  decided_at: string; reason: string | null; selection_version: number; selected_indices: number[]; selected_sha256: string;
}

type Fetcher = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
export interface DraftApi {
  list(beforeId?: number, signal?: AbortSignal): Promise<DraftPage>;
  detail(id: number, signal?: AbortSignal): Promise<DraftDetail>;
  saveSelection(id: number, request: SelectionSaveRequest): Promise<SelectionView>;
  decide(id: number, request: DecisionRequest, selection: SelectionView): Promise<DecisionResponse>;
}

export class ApiClientError extends Error {
  constructor(public readonly kind: "http" | "network" | "service", public readonly status?: number) {
    super(kind); this.name = "ApiClientError";
  }
}

function object(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new ApiClientError("service");
  return value as Record<string, unknown>;
}
function exact(value: Record<string, unknown>, keys: readonly string[]) {
  const actual = Object.keys(value).sort(); const expected = [...keys].sort();
  if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index])) throw new ApiClientError("service");
}
function text(value: unknown, nullable = false): string | null {
  if (nullable && value === null) return null;
  if (typeof value !== "string") throw new ApiClientError("service");
  return value;
}
function safeInteger(value: unknown, minimum = 0): number {
  if (!Number.isSafeInteger(value) || (value as number) < minimum) throw new ApiClientError("service");
  return value as number;
}
function enumValue<const T extends readonly string[]>(value: unknown, allowed: T): T[number] {
  if (typeof value !== "string" || !allowed.includes(value)) throw new ApiClientError("service");
  return value as T[number];
}
function source(value: unknown) {
  const parsed = object(value); exact(parsed, ["name", "sha256"]);
  const name = text(parsed.name); const sha256 = text(parsed.sha256);
  if (!name || !sha256 || !/^[a-f0-9]{64}$/.test(sha256)) throw new ApiClientError("service");
  return { name, sha256 };
}
function sortedUniqueIntegers(value: unknown): number[] {
  if (!Array.isArray(value)) throw new ApiClientError("service");
  const result = value.map((item) => safeInteger(item));
  if (result.some((item, index) => index > 0 && item <= result[index - 1])) throw new ApiClientError("service");
  return result;
}
function sameNumbers(left: readonly number[], right: readonly number[]) {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function parseSummaryV1(value: unknown): DraftSummary {
  const item = object(value);
  exact(item, ["id", "created_at", "status", "source", "language", "tlp", "item_count", "injection_warning", "review_status", "review_version", "selection_version"]);
  if (typeof item.injection_warning !== "boolean") throw new ApiClientError("service");
  const createdAt = text(item.created_at); if (!createdAt) throw new ApiClientError("service");
  const reviewVersion = safeInteger(item.review_version); const selectionVersion = safeInteger(item.selection_version);
  if (reviewVersion !== selectionVersion) throw new ApiClientError("service");
  return {
    id: safeInteger(item.id, 1), created_at: createdAt, status: enumValue(item.status, ["pending"] as const),
    source: source(item.source), language: enumValue(item.language, ["vi", "en"] as const), tlp: enumValue(item.tlp, supportedTlp),
    item_count: safeInteger(item.item_count), injection_warning: item.injection_warning,
    review_status: enumValue(item.review_status, ["pending"] as const), review_version: reviewVersion, selection_version: selectionVersion,
  };
}
export function parseDraftPageV1(value: unknown): DraftPage {
  const page = object(value); exact(page, ["items", "next_before_id"]);
  if (!Array.isArray(page.items)) throw new ApiClientError("service");
  const items = page.items.map(parseSummaryV1); const ids = new Set(items.map((item) => item.id));
  if (ids.size !== items.length) throw new ApiClientError("service");
  return { items, next_before_id: page.next_before_id === null ? null : safeInteger(page.next_before_id, 1) };
}

function parseReviewV1(value: unknown): DraftReviewState {
  const review = object(value); exact(review, ["status", "version", "created_by_subject", "decided_by_subject", "decided_at", "reason"]);
  return {
    status: enumValue(review.status, ["pending", "approved", "rejected"] as const), version: safeInteger(review.version),
    created_by_subject: text(review.created_by_subject, true), decided_by_subject: text(review.decided_by_subject, true),
    decided_at: text(review.decided_at, true), reason: text(review.reason, true),
  };
}
export function parseSelectionView(value: unknown): SelectionView {
  const raw = object(value);
  exact(raw, ["review_version", "selection_version", "selected_indices", "selected_sha256", "saved_by_subject", "saved_at", "changed", "ai_extracted_count", "ai_eligible_count", "human_deselected_count", "selection_save_count"]);
  if (typeof raw.changed !== "boolean") throw new ApiClientError("service");
  const selectedIndices = sortedUniqueIntegers(raw.selected_indices); const selectedSha = text(raw.selected_sha256);
  const aiEligible = safeInteger(raw.ai_eligible_count); const humanDeselected = safeInteger(raw.human_deselected_count);
  if (!selectedSha || !/^[a-f0-9]{64}$/.test(selectedSha) || humanDeselected + selectedIndices.length !== aiEligible) throw new ApiClientError("service");
  return {
    review_version: safeInteger(raw.review_version), selection_version: safeInteger(raw.selection_version),
    selected_indices: selectedIndices, selected_sha256: selectedSha,
    saved_by_subject: text(raw.saved_by_subject, true), saved_at: text(raw.saved_at, true), changed: raw.changed,
    ai_extracted_count: safeInteger(raw.ai_extracted_count), ai_eligible_count: aiEligible, human_deselected_count: humanDeselected,
    selection_save_count: safeInteger(raw.selection_save_count),
  };
}
export function parseDraftDetailV1(value: unknown): DraftDetail {
  const raw = object(value);
  exact(raw, ["id", "created_at", "schema_version", "status", "source", "language", "tlp", "text", "items", "injection_warning", "findings", "model", "cost_tokens", "review", "selection"]);
  try {
    const { review: reviewValue, selection: selectionValue, ...draftValue } = raw;
    const draft = parseDraft(draftValue); const review = parseReviewV1(reviewValue); const selection = parseSelectionView(selectionValue);
    const eligible = new Set(draft.items.map((item, index) => item.kind === "ioc" && item.keep && item.status === "ok" ? index : -1).filter((index) => index >= 0));
    const extracted = draft.items.filter((item) => item.kind === "ioc").length;
    if (selection.selected_indices.some((index) => index >= draft.items.length || !eligible.has(index))) throw new ApiClientError("service");
    if (selection.ai_extracted_count !== extracted || selection.ai_eligible_count !== eligible.size || selection.changed) throw new ApiClientError("service");
    if (selection.review_version !== review.version) throw new ApiClientError("service");
    const expectedReviewVersion = review.status === "pending" ? selection.selection_version : selection.selection_version + 1;
    if (!Number.isSafeInteger(expectedReviewVersion) || review.version !== expectedReviewVersion) throw new ApiClientError("service");
    return { ...draft, review, selection };
  } catch (error) {
    if (error instanceof ApiClientError) throw error;
    throw new ApiClientError("service");
  }
}

function validateSaveResponse(value: unknown, request: SelectionSaveRequest): SelectionView {
  const selection = parseSelectionView(value);
  if (!sameNumbers(selection.selected_indices, request.selected_indices)) throw new ApiClientError("service");
  const increment = selection.changed ? 1 : 0;
  if (request.expected_version > Number.MAX_SAFE_INTEGER - increment || selection.review_version !== request.expected_version + increment || selection.selection_version !== request.expected_version + increment) throw new ApiClientError("service");
  return selection;
}
export function parseDecisionV1(value: unknown, draftId: number, request: DecisionRequest, selection: SelectionView): DecisionResponse {
  const raw = object(value);
  exact(raw, ["draft_id", "status", "version", "decided_by_subject", "decided_at", "reason", "selection_version", "selected_indices", "selected_sha256"]);
  const response: DecisionResponse = {
    draft_id: safeInteger(raw.draft_id, 1), status: enumValue(raw.status, ["approved", "rejected"] as const), version: safeInteger(raw.version),
    decided_by_subject: text(raw.decided_by_subject) as string, decided_at: text(raw.decided_at) as string, reason: text(raw.reason, true),
    selection_version: safeInteger(raw.selection_version), selected_indices: sortedUniqueIntegers(raw.selected_indices), selected_sha256: text(raw.selected_sha256) as string,
  };
  const expectedStatus = request.decision === "approve" ? "approved" : "rejected";
  const expectedReason = request.decision === "approve" ? null : request.reason.trim();
  if (!response.decided_by_subject || !response.decided_at || !/^[a-f0-9]{64}$/.test(response.selected_sha256) || response.draft_id !== draftId || response.status !== expectedStatus || response.reason !== expectedReason || request.expected_version === Number.MAX_SAFE_INTEGER || response.version !== request.expected_version + 1 || response.selection_version !== selection.selection_version || response.selected_sha256 !== selection.selected_sha256 || !sameNumbers(response.selected_indices, selection.selected_indices)) throw new ApiClientError("service");
  return response;
}

async function requestJson<T>(fetcher: Fetcher, url: string, init: RequestInit, parser: (value: unknown) => T): Promise<T> {
  let response: Response;
  try { response = await fetcher(url, init); }
  catch (error) { if (error instanceof DOMException && error.name === "AbortError") throw error; throw new ApiClientError("network"); }
  if (!response.ok) {
    const knownCodes: Record<number, string> = {
      401: "authentication_required", 403: "forbidden", 404: "draft_not_found", 409: "draft_conflict",
      413: "request_too_large", 415: "unsupported_media_type", 422: "invalid_request",
    };
    try {
      const envelope = object(await response.json()); exact(envelope, ["error"]);
      const error = object(envelope.error); exact(error, ["code", "message"]);
      if (knownCodes[response.status] && text(error.code) === knownCodes[response.status] && text(error.message)) {
        throw new ApiClientError("http", response.status);
      }
    } catch (error) {
      if (error instanceof ApiClientError && error.kind === "http") throw error;
    }
    throw new ApiClientError("service");
  }
  try { return parser(await response.json()); }
  catch (error) { if (error instanceof ApiClientError) throw error; throw new ApiClientError("service"); }
}
function normalizeSelectionRequest(request: SelectionSaveRequest): SelectionSaveRequest {
  const expectedVersion = safeInteger(request.expected_version); const selectedIndices = sortedUniqueIntegers(request.selected_indices);
  if (selectedIndices.length > 1024) throw new ApiClientError("service");
  return { expected_version: expectedVersion, selected_indices: selectedIndices };
}
export function createDraftApi(fetcher: Fetcher = globalThis.fetch.bind(globalThis)): DraftApi {
  const common = { credentials: "same-origin" as const, cache: "no-store" as const };
  return {
    list(beforeId, signal) {
      const cursor = beforeId === undefined ? "" : `&before_id=${safeInteger(beforeId, 1)}`;
      return requestJson(fetcher, `/api/v1/drafts?limit=20${cursor}`, { ...common, signal }, parseDraftPageV1);
    },
    detail(id, signal) {
      const draftId = safeInteger(id, 1);
      return requestJson(fetcher, `/api/v1/drafts/${draftId}`, { ...common, signal }, (value) => {
        const parsed = parseDraftDetailV1(value);
        if (parsed.id !== draftId) throw new ApiClientError("service");
        return parsed;
      });
    },
    saveSelection(id, rawRequest) {
      const request = normalizeSelectionRequest(rawRequest);
      return requestJson(fetcher, `/api/v1/drafts/${safeInteger(id, 1)}/selection`, { method: "POST", ...common, headers: { "Content-Type": "application/json" }, body: JSON.stringify(request) }, (value) => validateSaveResponse(value, request));
    },
    decide(id, rawRequest, selection) {
      const expectedVersion = safeInteger(rawRequest.expected_version);
      const request: DecisionRequest = rawRequest.decision === "approve" ? { decision: "approve", expected_version: expectedVersion } : { decision: "reject", expected_version: expectedVersion, reason: rawRequest.reason.trim() };
      if (request.decision === "reject" && !request.reason) throw new ApiClientError("service");
      const draftId = safeInteger(id, 1);
      return requestJson(fetcher, `/api/v1/drafts/${draftId}/decision`, { method: "POST", ...common, headers: { "Content-Type": "application/json" }, body: JSON.stringify(request) }, (value) => parseDecisionV1(value, draftId, request, selection));
    },
  };
}

// Legacy parsers stay strict and separate so v1 payloads are never accepted accidentally.
export function parseDraftPage(value: unknown) {
  const page = object(value); exact(page, ["items", "next_before_id"]); if (!Array.isArray(page.items)) throw new ApiClientError("service");
  const items = page.items.map((entry) => {
    const item = object(entry);
    exact(item, ["id", "created_at", "status", "source", "language", "tlp", "item_count", "injection_warning", "review_status", "review_version"]);
    if (typeof item.injection_warning !== "boolean") throw new ApiClientError("service");
    const createdAt = text(item.created_at);
    if (!createdAt || safeInteger(item.review_version) !== 0) throw new ApiClientError("service");
    return {
      id: safeInteger(item.id, 1), created_at: createdAt, status: enumValue(item.status, ["pending"] as const),
      source: source(item.source), language: enumValue(item.language, ["vi", "en"] as const),
      tlp: enumValue(item.tlp, supportedTlp), item_count: safeInteger(item.item_count), injection_warning: item.injection_warning,
      review_status: enumValue(item.review_status, ["pending"] as const), review_version: 0 as const,
    };
  });
  if (new Set(items.map((item) => item.id)).size !== items.length) throw new ApiClientError("service");
  return { items, next_before_id: page.next_before_id === null ? null : safeInteger(page.next_before_id, 1) };
}
export function parseDraftDetail(value: unknown) {
  const raw = object(value); exact(raw, ["id", "created_at", "schema_version", "status", "source", "language", "tlp", "text", "items", "injection_warning", "findings", "model", "cost_tokens", "review"]);
  const { review, ...draft } = raw; const parsedReview = parseReviewV1(review); if (parsedReview.version > 1) throw new ApiClientError("service"); return { ...parseDraft(draft), review: parsedReview };
}
export function parseDecision(value: unknown) {
  const raw = object(value); exact(raw, ["draft_id", "status", "version", "decided_by_subject", "decided_at", "reason"]);
  const decidedBy = text(raw.decided_by_subject); const decidedAt = text(raw.decided_at);
  if (safeInteger(raw.version) !== 1 || !decidedBy || !decidedAt) throw new ApiClientError("service");
  return { draft_id: safeInteger(raw.draft_id, 1), status: enumValue(raw.status, ["approved", "rejected"] as const), version: 1, decided_by_subject: decidedBy, decided_at: decidedAt, reason: text(raw.reason, true) };
}

export const draftApi = createDraftApi();
