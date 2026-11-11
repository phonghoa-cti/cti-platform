import {
  AssetDataError,
  type TechnologyInput,
  type TechnologyItem,
  type TechnologyProvider,
  type TechnologyUpdateInput,
} from "@/data/technologies";
import type { AssetErrorKind } from "@/data/assets";

type Fetcher = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
type WireTechnology = {
  id: number;
  vendor: string;
  product: string;
  software_version: string;
  note: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  version: number;
};

const MAX_BODY_BYTES = 1024 * 1024;
const TIMEOUT_MS = 10_000;

class InvalidTechnologyResponse extends Error {}

function object(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new InvalidTechnologyResponse();
  return value as Record<string, unknown>;
}

function exact(value: Record<string, unknown>, keys: readonly string[]) {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index])) {
    throw new InvalidTechnologyResponse();
  }
}

function text(value: unknown, minimum: number, maximum: number, nonBlank = false) {
  if (typeof value !== "string") throw new InvalidTechnologyResponse();
  const length = Array.from(value).length;
  if (length < minimum || length > maximum || (nonBlank && !value.trim())) throw new InvalidTechnologyResponse();
  return value;
}

function technologyText(value: unknown, maximum: number) {
  const parsed = text(value, 1, maximum);
  if (parsed !== parsed.trim() || /[\p{Cc}\p{Cf}\p{Cs}]/u.test(parsed)) throw new InvalidTechnologyResponse();
  return parsed;
}

function integer(value: unknown) {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 1) throw new InvalidTechnologyResponse();
  return value;
}

function timestamp(value: unknown) {
  const parsed = text(value, 1, 128);
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?Z$/.exec(parsed);
  if (!match) throw new InvalidTechnologyResponse();
  const date = new Date(parsed);
  const parts = match.slice(1, 7).map(Number);
  if (!Number.isFinite(date.getTime())
    || date.getUTCFullYear() !== parts[0]
    || date.getUTCMonth() + 1 !== parts[1]
    || date.getUTCDate() !== parts[2]
    || date.getUTCHours() !== parts[3]
    || date.getUTCMinutes() !== parts[4]
    || date.getUTCSeconds() !== parts[5]) throw new InvalidTechnologyResponse();
  return parsed;
}

export function parseTechnologyItem(value: unknown): WireTechnology {
  const raw = object(value);
  exact(raw, ["id", "vendor", "product", "software_version", "note", "created_by", "created_at", "updated_at", "version"]);
  return {
    id: integer(raw.id),
    vendor: technologyText(raw.vendor, 128),
    product: technologyText(raw.product, 256),
    software_version: technologyText(raw.software_version, 128),
    note: text(raw.note, 0, 500),
    created_by: text(raw.created_by, 1, 512, true),
    created_at: timestamp(raw.created_at),
    updated_at: timestamp(raw.updated_at),
    version: integer(raw.version),
  };
}

export function parseTechnologyList(value: unknown): WireTechnology[] {
  const raw = object(value);
  exact(raw, ["items"]);
  if (!Array.isArray(raw.items) || raw.items.length > 1000) throw new InvalidTechnologyResponse();
  return raw.items.map(parseTechnologyItem);
}

function toTechnology(value: WireTechnology): TechnologyItem {
  return {
    id: value.id,
    vendor: value.vendor,
    product: value.product,
    softwareVersion: value.software_version,
    note: value.note,
    createdBy: value.created_by,
    createdAt: value.created_at,
    updatedAt: value.updated_at,
    version: value.version,
  };
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
    throw new InvalidTechnologyResponse();
  }
  const declared = response.headers.get("Content-Length");
  if (declared !== null && (!/^\d+$/.test(declared) || Number(declared) > MAX_BODY_BYTES)) {
    await response.body?.cancel().catch(() => undefined);
    throw new InvalidTechnologyResponse();
  }
  if (!response.body) throw new InvalidTechnologyResponse();
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
      if (bytes > MAX_BODY_BYTES) throw new InvalidTechnologyResponse();
      body += decoder.decode(chunk.value, { stream: true });
    }
  } finally {
    if (!complete) await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
  try {
    return JSON.parse(body) as unknown;
  } catch {
    throw new InvalidTechnologyResponse();
  }
}

function parseError(value: unknown) {
  const envelope = object(value);
  exact(envelope, ["error"]);
  const error = object(envelope.error);
  exact(error, ["code", "message"]);
  return { code: text(error.code, 1, 64), message: text(error.message, 1, 160) };
}

function knownError(status: number, code: string): AssetErrorKind | null {
  if (status === 401 && code === "authentication_required") return "authentication-required";
  if (status === 403 && code === "forbidden") return "forbidden";
  if (status === 404 && code === "technology_not_found") return "not-found";
  if (status === 409 && (code === "technology_exists" || code === "technology_conflict")) return "conflict";
  if ((status === 413 && code === "request_too_large")
    || (status === 415 && code === "unsupported_media_type")
    || (status === 422 && code === "invalid_technology")) return "invalid";
  if (status === 503 && code === "assets_unavailable") return "unavailable";
  return null;
}

function body(input: TechnologyInput | TechnologyUpdateInput) {
  const value = {
    vendor: input.vendor,
    product: input.product,
    software_version: input.softwareVersion,
    note: input.note,
  } as Record<string, unknown>;
  if ("expectedVersion" in input) value.expected_version = input.expectedVersion;
  return JSON.stringify(value);
}

export function createTechnologiesHttpProvider({
  fetcher = globalThis.fetch.bind(globalThis),
}: { fetcher?: Fetcher } = {}): TechnologyProvider {
  async function request<T>({
    url, method, input, successStatus, parse, mutation,
  }: {
    url: string;
    method: "GET" | "POST" | "PUT" | "DELETE";
    input?: TechnologyInput | TechnologyUpdateInput;
    successStatus: number;
    parse?: (value: unknown) => T;
    mutation: boolean;
  }): Promise<T> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
    try {
      const response = await fetcher(url, {
        method,
        credentials: "same-origin",
        cache: "no-store",
        redirect: "error",
        headers: input ? { Accept: "application/json", "Content-Type": "application/json" } : { Accept: "application/json" },
        body: input ? body(input) : undefined,
        signal: controller.signal,
      });
      if (response.status === successStatus) {
        if (!parse) return undefined as T;
        return parse(await readJson(response, controller.signal));
      }
      const parsed = parseError(await readJson(response, controller.signal));
      throw new AssetDataError(knownError(response.status, parsed.code) ?? (mutation ? "unknown-mutation" : "unavailable"));
    } catch (error) {
      if (error instanceof AssetDataError) throw error;
      throw new AssetDataError(mutation ? "unknown-mutation" : "unavailable");
    } finally {
      clearTimeout(timeout);
    }
  }

  return {
    async list() {
      const values = await request({
        url: "/api/assets/technologies", method: "GET", successStatus: 200, parse: parseTechnologyList, mutation: false,
      });
      return values.map(toTechnology);
    },
    async create(input) {
      return toTechnology(await request({
        url: "/api/assets/technologies", method: "POST", input, successStatus: 201, parse: parseTechnologyItem, mutation: true,
      }));
    },
    async update(id, input) {
      return toTechnology(await request({
        url: `/api/assets/technologies/${id}`, method: "PUT", input, successStatus: 200, parse: parseTechnologyItem, mutation: true,
      }));
    },
    async remove(id, expectedVersion) {
      await request({
        url: `/api/assets/technologies/${id}?expected_version=${expectedVersion}`,
        method: "DELETE",
        successStatus: 204,
        mutation: true,
      });
    },
  };
}
