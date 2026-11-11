import type {
  LookupDataSource,
  LookupIocType,
  LookupLevel,
  LookupResponse,
  LookupScoreParts,
  LookupTlp,
} from "@/data/ioc-lookup";

type Fetcher = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
type HttpIocType = Exclude<LookupIocType, "hash">;

export type IocLookupHttpResponse = {
  ioc: { type: HttpIocType; value: string; display: string };
  state: "found" | "not_found" | "allowlisted";
  found: boolean;
  allowlisted: boolean;
  score: {
    value: number;
    level: LookupLevel;
    reason: string;
    parts: LookupScoreParts | null;
  } | null;
  sources: {
    name: string;
    first_seen: string;
    last_seen: string;
    tlp: LookupTlp;
  }[];
  related: { techniques: string[]; malware: string[]; actors: string[] };
  asset_match: { matched: boolean; assets: string[] };
  tlp: LookupTlp | null;
};

const MAX_BODY_BYTES = 1024 * 1024;
const TIMEOUT_MS = 10_000;
const IOC_TYPES = ["ipv4", "ipv6", "domain", "url", "email", "md5", "sha1", "sha256"] as const;
const TLPS = ["TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"] as const;
const LEVELS = ["low", "medium", "high"] as const;

class InvalidLookupResponse extends Error {}

function object(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new InvalidLookupResponse();
  return value as Record<string, unknown>;
}

function exact(value: Record<string, unknown>, keys: readonly string[]) {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index])) {
    throw new InvalidLookupResponse();
  }
}

function codePointLength(value: string) {
  return Array.from(value).length;
}

function text(value: unknown, minimum: number, maximum: number): string {
  if (typeof value !== "string") throw new InvalidLookupResponse();
  const length = codePointLength(value);
  if (length < minimum || length > maximum) throw new InvalidLookupResponse();
  return value;
}

function enumValue<const T extends readonly string[]>(value: unknown, allowed: T): T[number] {
  if (typeof value !== "string" || !allowed.includes(value)) throw new InvalidLookupResponse();
  return value as T[number];
}

function strictInteger(value: unknown, minimum: number, maximum: number): number {
  if (typeof value !== "number" || !Number.isFinite(value) || !Number.isSafeInteger(value)
    || value < minimum || value > maximum) throw new InvalidLookupResponse();
  return value;
}

function finiteNumber(value: unknown, minimum: number, maximum: number): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < minimum || value > maximum) {
    throw new InvalidLookupResponse();
  }
  return value;
}

function boolean(value: unknown): boolean {
  if (typeof value !== "boolean") throw new InvalidLookupResponse();
  return value;
}

function stringList(value: unknown): string[] {
  if (!Array.isArray(value) || value.length > 100) throw new InvalidLookupResponse();
  return value.map((item) => text(item, 1, 128));
}

function utcTimestamp(value: unknown): string {
  const timestamp = text(value, 1, 128);
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?Z$/.exec(timestamp);
  if (!match) throw new InvalidLookupResponse();
  const date = new Date(timestamp);
  const parts = match.slice(1, 7).map(Number);
  if (!Number.isFinite(date.getTime())
    || date.getUTCFullYear() !== parts[0]
    || date.getUTCMonth() + 1 !== parts[1]
    || date.getUTCDate() !== parts[2]
    || date.getUTCHours() !== parts[3]
    || date.getUTCMinutes() !== parts[4]
    || date.getUTCSeconds() !== parts[5]) throw new InvalidLookupResponse();
  return timestamp;
}

function parseIoc(value: unknown): IocLookupHttpResponse["ioc"] {
  const raw = object(value);
  exact(raw, ["type", "value", "display"]);
  return {
    type: enumValue(raw.type, IOC_TYPES),
    value: text(raw.value, 1, 2048),
    display: text(raw.display, 1, 4096),
  };
}

function parseParts(value: unknown): LookupScoreParts | null {
  if (value === null) return null;
  const raw = object(value);
  exact(raw, ["reliability", "confirmation", "freshness", "asset"]);
  const asset = finiteNumber(raw.asset, 1, 1.3);
  if (asset !== 1 && asset !== 1.3) throw new InvalidLookupResponse();
  return {
    reliability: finiteNumber(raw.reliability, 0, 1),
    confirmation: finiteNumber(raw.confirmation, 0, 1),
    freshness: finiteNumber(raw.freshness, 0, 1),
    asset,
  };
}

function parseScore(value: unknown): NonNullable<IocLookupHttpResponse["score"]> | null {
  if (value === null) return null;
  const raw = object(value);
  exact(raw, ["value", "level", "reason", "parts"]);
  const scoreValue = strictInteger(raw.value, 0, 100);
  const level = enumValue(raw.level, LEVELS);
  const expectedLevel: LookupLevel = scoreValue < 40 ? "low" : scoreValue < 70 ? "medium" : "high";
  if (level !== expectedLevel) throw new InvalidLookupResponse();
  return {
    value: scoreValue,
    level,
    reason: text(raw.reason, 1, 512),
    parts: parseParts(raw.parts),
  };
}

function parseSources(value: unknown): IocLookupHttpResponse["sources"] {
  if (!Array.isArray(value) || value.length > 100) throw new InvalidLookupResponse();
  return value.map((entry) => {
    const raw = object(entry);
    exact(raw, ["name", "first_seen", "last_seen", "tlp"]);
    const firstSeen = utcTimestamp(raw.first_seen);
    const lastSeen = utcTimestamp(raw.last_seen);
    if (Date.parse(firstSeen) > Date.parse(lastSeen)) throw new InvalidLookupResponse();
    return {
      name: text(raw.name, 1, 128),
      first_seen: firstSeen,
      last_seen: lastSeen,
      tlp: enumValue(raw.tlp, TLPS),
    };
  });
}

function parseRelated(value: unknown): IocLookupHttpResponse["related"] {
  const raw = object(value);
  exact(raw, ["techniques", "malware", "actors"]);
  return {
    techniques: stringList(raw.techniques),
    malware: stringList(raw.malware),
    actors: stringList(raw.actors),
  };
}

function parseAssetMatch(value: unknown): IocLookupHttpResponse["asset_match"] {
  const raw = object(value);
  exact(raw, ["matched", "assets"]);
  const assets = stringList(raw.assets);
  const matched = boolean(raw.matched);
  if (matched !== (assets.length > 0)) throw new InvalidLookupResponse();
  return { matched, assets };
}

function isEmptyRelated(value: IocLookupHttpResponse["related"]) {
  return value.techniques.length === 0 && value.malware.length === 0 && value.actors.length === 0;
}

export function parseIocLookupResponse(value: unknown): IocLookupHttpResponse {
  const raw = object(value);
  exact(raw, ["ioc", "state", "found", "allowlisted", "score", "sources", "related", "asset_match", "tlp"]);
  const result: IocLookupHttpResponse = {
    ioc: parseIoc(raw.ioc),
    state: enumValue(raw.state, ["found", "not_found", "allowlisted"] as const),
    found: boolean(raw.found),
    allowlisted: boolean(raw.allowlisted),
    score: parseScore(raw.score),
    sources: parseSources(raw.sources),
    related: parseRelated(raw.related),
    asset_match: parseAssetMatch(raw.asset_match),
    tlp: raw.tlp === null ? null : enumValue(raw.tlp, TLPS),
  };

  if (result.state === "found") {
    if (!result.found || result.allowlisted || !result.score || !result.score.parts
      || result.sources.length === 0 || result.tlp === null) throw new InvalidLookupResponse();
  } else if (result.state === "allowlisted") {
    if (result.found || !result.allowlisted || !result.score || result.score.value !== 0
      || result.score.level !== "low" || result.score.parts !== null || result.sources.length !== 0
      || !isEmptyRelated(result.related) || result.asset_match.matched || result.asset_match.assets.length !== 0
      || result.tlp !== "TLP:CLEAR") throw new InvalidLookupResponse();
  } else if (result.found || result.allowlisted || result.score !== null || result.sources.length !== 0
    || !isEmptyRelated(result.related) || result.asset_match.matched || result.asset_match.assets.length !== 0
    || result.tlp !== null) throw new InvalidLookupResponse();

  return result;
}

async function readChunk(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  signal: AbortSignal,
): Promise<ReadableStreamReadResult<Uint8Array>> {
  if (signal.aborted) throw new DOMException("aborted", "AbortError");
  return new Promise((resolve, reject) => {
    const abort = () => reject(new DOMException("aborted", "AbortError"));
    signal.addEventListener("abort", abort, { once: true });
    reader.read().then(resolve, reject).finally(() => signal.removeEventListener("abort", abort));
  });
}

async function readJson(response: Response, signal: AbortSignal): Promise<unknown> {
  const contentType = response.headers.get("Content-Type")?.toLowerCase() ?? "";
  if (!/^application\/json(?:\s*;|$)/.test(contentType)) {
    await response.body?.cancel().catch(() => undefined);
    throw new InvalidLookupResponse();
  }
  const contentLength = response.headers.get("Content-Length");
  if (contentLength !== null && (!/^\d+$/.test(contentLength) || Number(contentLength) > MAX_BODY_BYTES)) {
    await response.body?.cancel().catch(() => undefined);
    throw new InvalidLookupResponse();
  }
  if (!response.body) throw new InvalidLookupResponse();

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: true });
  let complete = false;
  let bytes = 0;
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
      if (bytes > MAX_BODY_BYTES) throw new InvalidLookupResponse();
      body += decoder.decode(chunk.value, { stream: true });
    }
  } finally {
    if (!complete) await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
  try {
    return JSON.parse(body) as unknown;
  } catch {
    throw new InvalidLookupResponse();
  }
}

function parseError(value: unknown) {
  const envelope = object(value);
  exact(envelope, ["error"]);
  const error = object(envelope.error);
  exact(error, ["code", "message"]);
  return { code: text(error.code, 1, 64), message: text(error.message, 1, 160) };
}

function mapHttpError(status: number, code: string): LookupResponse {
  if (status === 401 && code === "authentication_required") return { state: "authentication-required" };
  if (status === 403 && code === "forbidden") return { state: "forbidden" };
  if (status === 422 && code === "invalid_ioc") return { state: "invalid" };
  if (status === 422 && code === "private_ip") return { state: "private-ip" };
  return { state: "unavailable" };
}

function mapSuccess(value: IocLookupHttpResponse, input: string): LookupResponse {
  if (value.state === "not_found") return { state: "not-found" };
  return {
    state: "result",
    input,
    ioc: value.ioc,
    found: value.found,
    allowlisted: value.allowlisted,
    score: value.score,
    sources: value.sources.map((source) => ({
      name: source.name,
      firstSeen: source.first_seen,
      lastSeen: source.last_seen,
      tlp: source.tlp,
    })),
    related: value.related,
    enrichment: {},
    assetMatch: value.asset_match,
    tlp: value.tlp as LookupTlp,
  };
}

export function createIocHttpDataSource({
  fetcher = globalThis.fetch.bind(globalThis),
}: { fetcher?: Fetcher } = {}): LookupDataSource {
  return {
    async lookup(value) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
      try {
        const query = new URLSearchParams({ value });
        const response = await fetcher(`/api/ioc?${query.toString()}`, {
          method: "GET",
          credentials: "same-origin",
          cache: "no-store",
          redirect: "error",
          headers: { Accept: "application/json" },
          signal: controller.signal,
        });
        const body = await readJson(response, controller.signal);
        if (!response.ok) {
          const error = parseError(body);
          return mapHttpError(response.status, error.code);
        }
        return mapSuccess(parseIocLookupResponse(body), value);
      } catch {
        return { state: "unavailable" };
      } finally {
        clearTimeout(timeout);
      }
    },
  };
}
