import { parseDraft, supportedTlp, type Draft, type Tlp } from "@/data/draft-adapter";

export type ReviewStatus = "pending" | "approved" | "rejected";

export interface DraftSummary {
  id: number;
  created_at: string;
  status: "pending";
  source: { name: string; sha256: string };
  language: "vi" | "en";
  tlp: Tlp;
  item_count: number;
  injection_warning: boolean;
  review_status: "pending";
  review_version: 0;
}

export interface DraftPage {
  items: DraftSummary[];
  next_before_id: number | null;
}

export interface DraftReviewState {
  status: ReviewStatus;
  version: number;
  created_by_subject: string | null;
  decided_by_subject: string | null;
  decided_at: string | null;
  reason: string | null;
}

export interface DraftDetail extends Draft {
  review: DraftReviewState;
}

export interface DecisionResponse {
  draft_id: number;
  status: "approved" | "rejected";
  version: 1;
  decided_by_subject: string;
  decided_at: string;
  reason: string | null;
}

export type DecisionRequest =
  | { decision: "approve"; expected_version: number }
  | { decision: "reject"; expected_version: number; reason: string };

type Fetcher = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

export interface DraftApi {
  list(beforeId?: number, signal?: AbortSignal): Promise<DraftPage>;
  detail(id: number, signal?: AbortSignal): Promise<DraftDetail>;
  decide(id: number, request: DecisionRequest): Promise<DecisionResponse>;
}

export class ApiClientError extends Error {
  constructor(public readonly kind: "http" | "network" | "service", public readonly status?: number) {
    super(kind);
    this.name = "ApiClientError";
  }
}

function object(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new ApiClientError("service");
  return value as Record<string, unknown>;
}

function exact(value: Record<string, unknown>, keys: readonly string[]) {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index])) {
    throw new ApiClientError("service");
  }
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
  const parsed = object(value);
  exact(parsed, ["name", "sha256"]);
  const name = text(parsed.name);
  const sha256 = text(parsed.sha256);
  if (!name || !sha256 || !/^[a-f0-9]{64}$/.test(sha256)) throw new ApiClientError("service");
  return { name, sha256 };
}

function parseSummary(value: unknown): DraftSummary {
  const item = object(value);
  exact(item, ["id", "created_at", "status", "source", "language", "tlp", "item_count", "injection_warning", "review_status", "review_version"]);
  if (typeof item.injection_warning !== "boolean") throw new ApiClientError("service");
  const createdAt = text(item.created_at);
  if (!createdAt) throw new ApiClientError("service");
  return {
    id: safeInteger(item.id, 1),
    created_at: createdAt,
    status: enumValue(item.status, ["pending"] as const),
    source: source(item.source),
    language: enumValue(item.language, ["vi", "en"] as const),
    tlp: enumValue(item.tlp, supportedTlp),
    item_count: safeInteger(item.item_count),
    injection_warning: item.injection_warning,
    review_status: enumValue(item.review_status, ["pending"] as const),
    review_version: safeInteger(item.review_version) === 0 ? 0 : (() => { throw new ApiClientError("service"); })(),
  };
}

export function parseDraftPage(value: unknown): DraftPage {
  const page = object(value);
  exact(page, ["items", "next_before_id"]);
  if (!Array.isArray(page.items)) throw new ApiClientError("service");
  const items = page.items.map(parseSummary);
  const ids = new Set(items.map((item) => item.id));
  if (ids.size !== items.length) throw new ApiClientError("service");
  return { items, next_before_id: page.next_before_id === null ? null : safeInteger(page.next_before_id, 1) };
}

function parseReview(value: unknown): DraftReviewState {
  const review = object(value);
  exact(review, ["status", "version", "created_by_subject", "decided_by_subject", "decided_at", "reason"]);
  const version = safeInteger(review.version);
  if (version > 1) throw new ApiClientError("service");
  return {
    status: enumValue(review.status, ["pending", "approved", "rejected"] as const),
    version,
    created_by_subject: text(review.created_by_subject, true),
    decided_by_subject: text(review.decided_by_subject, true),
    decided_at: text(review.decided_at, true),
    reason: text(review.reason, true),
  };
}

export function parseDraftDetail(value: unknown): DraftDetail {
  const raw = object(value);
  exact(raw, ["id", "created_at", "schema_version", "status", "source", "language", "tlp", "text", "items", "injection_warning", "findings", "model", "cost_tokens", "review"]);
  try {
    const { review, ...draft } = raw;
    return { ...parseDraft(draft), review: parseReview(review) };
  } catch (error) {
    if (error instanceof ApiClientError) throw error;
    throw new ApiClientError("service");
  }
}

export function parseDecision(value: unknown): DecisionResponse {
  const decision = object(value);
  exact(decision, ["draft_id", "status", "version", "decided_by_subject", "decided_at", "reason"]);
  const version = safeInteger(decision.version);
  const decidedBy = text(decision.decided_by_subject);
  const decidedAt = text(decision.decided_at);
  if (version !== 1 || !decidedBy || !decidedAt) throw new ApiClientError("service");
  return {
    draft_id: safeInteger(decision.draft_id, 1),
    status: enumValue(decision.status, ["approved", "rejected"] as const),
    version: 1,
    decided_by_subject: decidedBy,
    decided_at: decidedAt,
    reason: text(decision.reason, true),
  };
}

async function requestJson(fetcher: Fetcher, url: string, init: RequestInit, parser: (value: unknown) => unknown) {
  let response: Response;
  try {
    response = await fetcher(url, init);
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiClientError("network");
  }
  if (!response.ok) throw new ApiClientError("http", response.status);
  try {
    return parser(await response.json());
  } catch (error) {
    if (error instanceof ApiClientError) throw error;
    throw new ApiClientError("service");
  }
}

export function createDraftApi(fetcher: Fetcher = globalThis.fetch.bind(globalThis)): DraftApi {
  const common = { credentials: "same-origin" as const, cache: "no-store" as const };
  return {
    list(beforeId, signal) {
      const cursor = beforeId === undefined ? "" : `&before_id=${safeInteger(beforeId, 1)}`;
      return requestJson(fetcher, `/api/drafts?limit=20${cursor}`, { ...common, signal }, parseDraftPage) as Promise<DraftPage>;
    },
    detail(id, signal) {
      return requestJson(fetcher, `/api/drafts/${safeInteger(id, 1)}`, { ...common, signal }, parseDraftDetail) as Promise<DraftDetail>;
    },
    decide(id, request) {
      const expectedVersion = safeInteger(request.expected_version);
      const body: DecisionRequest = request.decision === "approve"
        ? { decision: "approve", expected_version: expectedVersion }
        : { decision: "reject", expected_version: expectedVersion, reason: request.reason.trim() };
      if (body.decision === "reject" && !body.reason) throw new ApiClientError("service");
      return requestJson(fetcher, `/api/drafts/${safeInteger(id, 1)}/decision`, {
        method: "POST",
        ...common,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }, parseDecision) as Promise<DecisionResponse>;
    },
  };
}

export const draftApi = createDraftApi();
