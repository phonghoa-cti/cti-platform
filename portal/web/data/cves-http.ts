import {
  CveDataError,
  type CveDetailItem,
  type CveDetailResponse,
  type CveErrorKind,
  type CveMatch,
  type CveProvider,
  type CveResponse,
  type CveSource,
  type CveSummaryItem,
  type CveSummaryResponse,
} from "@/data/cves";

type Fetcher = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
const MAX_BODY_BYTES = 1024 * 1024;
const TIMEOUT_MS = 10_000;
const CONTROL = /[\p{Cc}\p{Cf}\p{Cs}]/u;
const NOTICE = "Liên quan theo tên sản phẩm; cần kiểm tra phiên bản/phạm vi bị ảnh hưởng trước khi vá.";

class InvalidCveResponse extends Error {}

function object(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new InvalidCveResponse();
  return value as Record<string, unknown>;
}

function exact(value: Record<string, unknown>, keys: readonly string[]) {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index])) {
    throw new InvalidCveResponse();
  }
}

function text(value: unknown, minimum: number, maximum: number, controls = false) {
  if (typeof value !== "string") throw new InvalidCveResponse();
  const length = Array.from(value).length;
  if (length < minimum || length > maximum || (controls && CONTROL.test(value))) throw new InvalidCveResponse();
  return value;
}

function integer(value: unknown, minimum = 1, maximum = Number.MAX_SAFE_INTEGER) {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < minimum || value > maximum) {
    throw new InvalidCveResponse();
  }
  return value;
}

function finite(value: unknown, maximum: number) {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > maximum) throw new InvalidCveResponse();
  return value;
}

function nullableFinite(value: unknown, maximum: number) {
  return value === null ? null : finite(value, maximum);
}

function date(value: unknown) {
  const parsed = text(value, 10, 10);
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(parsed);
  if (!match) throw new InvalidCveResponse();
  const [year, month, day] = match.slice(1).map(Number);
  const actual = new Date(Date.UTC(year, month - 1, day));
  if (actual.getUTCFullYear() !== year || actual.getUTCMonth() !== month - 1 || actual.getUTCDate() !== day) {
    throw new InvalidCveResponse();
  }
  return parsed;
}

function timestamp(value: unknown) {
  const parsed = text(value, 20, 27);
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?Z$/.exec(parsed);
  if (!match) throw new InvalidCveResponse();
  const parts = match.slice(1, 7).map(Number);
  const actual = new Date(parsed);
  if (!Number.isFinite(actual.getTime())
    || actual.getUTCFullYear() !== parts[0]
    || actual.getUTCMonth() + 1 !== parts[1]
    || actual.getUTCDate() !== parts[2]
    || actual.getUTCHours() !== parts[3]
    || actual.getUTCMinutes() !== parts[4]
    || actual.getUTCSeconds() !== parts[5]) throw new InvalidCveResponse();
  return parsed;
}

function cveId(value: unknown) {
  const parsed = text(value, 13, 64);
  if (!/^CVE-[0-9]{4}-[0-9]{4,}$/.test(parsed)) throw new InvalidCveResponse();
  return parsed;
}

function title(value: unknown) {
  const parsed = text(value, 1, 300, true);
  if (parsed !== parsed.trim()) throw new InvalidCveResponse();
  return parsed;
}

function technologyText(value: unknown, maximum: number) {
  const parsed = text(value, 1, maximum, true);
  if (parsed !== parsed.trim()) throw new InvalidCveResponse();
  return parsed;
}

function advisory(value: unknown) {
  if (value === null) return null;
  const parsed = text(value, 1, 2048, true);
  let url: URL;
  try { url = new URL(parsed); } catch { throw new InvalidCveResponse(); }
  if (url.protocol !== "https:" || url.username || url.password || !url.hostname) throw new InvalidCveResponse();
  return parsed;
}

function match(value: unknown): CveMatch {
  const raw = object(value);
  exact(raw, ["technology_id", "vendor", "product", "software_version", "match_reason", "version_assessment"]);
  if (raw.match_reason !== "vendor_product_exact_casefold" || raw.version_assessment !== "not_performed") {
    throw new InvalidCveResponse();
  }
  return {
    technologyId: integer(raw.technology_id),
    vendor: technologyText(raw.vendor, 128),
    product: technologyText(raw.product, 256),
    softwareVersion: technologyText(raw.software_version, 128),
    matchReason: raw.match_reason,
    versionAssessment: raw.version_assessment,
  };
}

function commonItem(raw: Record<string, unknown>) {
  return {
    cveId: cveId(raw.cve_id),
    title: title(raw.title),
    kev: typeof raw.kev === "boolean" ? raw.kev : (() => { throw new InvalidCveResponse(); })(),
    epssScore: nullableFinite(raw.epss_score, 1),
    cvssBaseScore: nullableFinite(raw.cvss_base_score, 10),
    priority: integer(raw.priority),
  };
}

function detailItem(value: unknown): CveDetailItem {
  const raw = object(value);
  exact(raw, [
    "cve_id", "title", "kev", "kev_due_date", "kev_as_of", "epss_score", "epss_percentile", "epss_as_of",
    "cvss_base_score", "cvss_version", "published_at", "advisory_url", "matches", "priority",
  ]);
  const common = commonItem(raw);
  const kevDueDate = raw.kev_due_date === null ? null : date(raw.kev_due_date);
  if (!common.kev && kevDueDate !== null) throw new InvalidCveResponse();
  const epssPercentile = nullableFinite(raw.epss_percentile, 1);
  const epssAsOf = raw.epss_as_of === null ? null : date(raw.epss_as_of);
  if (common.epssScore === null ? epssPercentile !== null || epssAsOf !== null : epssAsOf === null) throw new InvalidCveResponse();
  const cvssVersion = raw.cvss_version === null ? null : raw.cvss_version;
  if (cvssVersion !== null && cvssVersion !== "3.1" && cvssVersion !== "4.0") throw new InvalidCveResponse();
  if ((common.cvssBaseScore === null) !== (cvssVersion === null)) throw new InvalidCveResponse();
  if (!Array.isArray(raw.matches) || raw.matches.length < 1 || raw.matches.length > 1000) throw new InvalidCveResponse();
  const matches = raw.matches.map(match);
  if (matches.some((entry, index) => index > 0 && entry.technologyId <= matches[index - 1].technologyId)) {
    throw new InvalidCveResponse();
  }
  return {
    ...common,
    kevDueDate,
    kevAsOf: date(raw.kev_as_of),
    epssPercentile,
    epssAsOf,
    cvssVersion,
    publishedAt: raw.published_at === null ? null : timestamp(raw.published_at),
    advisoryUrl: advisory(raw.advisory_url),
    matches,
  };
}

function summaryItem(value: unknown): CveSummaryItem {
  const raw = object(value);
  exact(raw, ["cve_id", "title", "kev", "epss_score", "cvss_base_score", "priority", "match_count"]);
  return { ...commonItem(raw), matchCount: integer(raw.match_count) };
}

function envelope(raw: Record<string, unknown>) {
  const summary = object(raw.summary);
  exact(summary, ["matched_cves", "kev_cves"]);
  const page = object(raw.page);
  exact(page, ["next_cursor", "limit"]);
  const cursor = page.next_cursor === null ? null : text(page.next_cursor, 1, 1024);
  if (cursor !== null && !/^[\x20-\x7e]+$/.test(cursor)) throw new InvalidCveResponse();
  const sourceRaw = object(raw.source);
  exact(sourceRaw, ["kind", "dataset_id", "source_as_of", "retrieved_at"]);
  if (sourceRaw.kind !== "synthetic") throw new InvalidCveResponse();
  const datasetId = text(sourceRaw.dataset_id, 71, 71);
  if (!/^sha256:[0-9a-f]{64}$/.test(datasetId)) throw new InvalidCveResponse();
  const source: CveSource = {
    kind: "synthetic",
    datasetId,
    sourceAsOf: timestamp(sourceRaw.source_as_of),
    retrievedAt: timestamp(sourceRaw.retrieved_at),
  };
  const notice = text(raw.notice, 1, 1000, true);
  if (notice !== NOTICE) throw new InvalidCveResponse();
  return {
    summary: { matchedCves: integer(summary.matched_cves, 0), kevCves: integer(summary.kev_cves, 0) },
    page: { nextCursor: cursor, limit: integer(page.limit, 1, 100) },
    source,
    notice,
  };
}

function uniqueCves<T extends { cveId: string }>(items: T[]) {
  if (new Set(items.map((item) => item.cveId)).size !== items.length) throw new InvalidCveResponse();
  return items;
}

export function parseCveResponse(value: unknown): CveResponse {
  const raw = object(value);
  exact(raw, ["view", "items", "summary", "page", "source", "notice"]);
  if (!Array.isArray(raw.items) || raw.items.length > 100) throw new InvalidCveResponse();
  const common = envelope(raw);
  if (raw.view === "detail") {
    return { view: "detail", items: uniqueCves(raw.items.map(detailItem)), ...common } satisfies CveDetailResponse;
  }
  if (raw.view === "summary") {
    return { view: "summary", items: uniqueCves(raw.items.map(summaryItem)), ...common } satisfies CveSummaryResponse;
  }
  throw new InvalidCveResponse();
}

async function readChunk(reader: ReadableStreamDefaultReader<Uint8Array>, signal: AbortSignal) {
  if (signal.aborted) throw new DOMException("aborted", "AbortError");
  return new Promise<ReadableStreamReadResult<Uint8Array>>((resolve, reject) => {
    const abort = () => reject(new DOMException("aborted", "AbortError"));
    signal.addEventListener("abort", abort, { once: true });
    reader.read().then(resolve, reject).finally(() => signal.removeEventListener("abort", abort));
  });
}

async function readJson(response: Response, signal: AbortSignal): Promise<unknown> {
  const contentType = response.headers.get("Content-Type")?.toLowerCase() ?? "";
  if (!/^application\/json(?:\s*;|$)/.test(contentType)) {
    await response.body?.cancel().catch(() => undefined);
    throw new InvalidCveResponse();
  }
  const declared = response.headers.get("Content-Length");
  if (declared !== null && (!/^\d+$/.test(declared) || Number(declared) > MAX_BODY_BYTES)) {
    await response.body?.cancel().catch(() => undefined);
    throw new InvalidCveResponse();
  }
  if (!response.body) throw new InvalidCveResponse();
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: true });
  let bytes = 0;
  let complete = false;
  let body = "";
  try {
    while (true) {
      const chunk = await readChunk(reader, signal);
      if (chunk.done) {
        complete = true;
        body += decoder.decode();
        break;
      }
      bytes += chunk.value.byteLength;
      if (bytes > MAX_BODY_BYTES) throw new InvalidCveResponse();
      body += decoder.decode(chunk.value, { stream: true });
    }
  } finally {
    if (!complete) await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
  try { return JSON.parse(body) as unknown; } catch { throw new InvalidCveResponse(); }
}

function parseError(value: unknown) {
  const envelope = object(value);
  exact(envelope, ["error"]);
  const error = object(envelope.error);
  exact(error, ["code", "message"]);
  return { code: text(error.code, 1, 64), message: text(error.message, 1, 160) };
}

function knownError(status: number, code: string): CveErrorKind | null {
  if (status === 401 && code === "authentication_required") return "authentication-required";
  if (status === 403 && code === "forbidden") return "forbidden";
  if (status === 404 && code === "technology_not_found") return "not-found";
  if (status === 422 && code === "invalid_cve_query") return "invalid";
  if (status === 409 && code === "cve_snapshot_changed") return "snapshot-changed";
  if (status === 503 && code === "cves_unavailable") return "unavailable";
  return null;
}

export function createCvesHttpProvider({ fetcher = globalThis.fetch.bind(globalThis) }: { fetcher?: Fetcher } = {}): CveProvider {
  return {
    async list(query) {
      const parameters = new URLSearchParams();
      if (query.kev) parameters.set("kev", "true");
      if (query.technologyId !== null) parameters.set("asset_id", String(query.technologyId));
      if (query.q) parameters.set("q", query.q);
      parameters.set("limit", String(query.limit));
      if (query.cursor !== null) parameters.set("cursor", query.cursor);
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
      try {
        const response = await fetcher(`/api/cves?${parameters.toString()}`, {
          method: "GET",
          credentials: "same-origin",
          cache: "no-store",
          redirect: "error",
          headers: { Accept: "application/json" },
          signal: controller.signal,
        });
        const value = await readJson(response, controller.signal);
        if (response.status === 200) return parseCveResponse(value);
        const error = parseError(value);
        throw new CveDataError(knownError(response.status, error.code) ?? "unavailable");
      } catch (error) {
        if (error instanceof CveDataError) throw error;
        throw new CveDataError("unavailable");
      } finally {
        clearTimeout(timeout);
      }
    },
  };
}
