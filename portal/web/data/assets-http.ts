import {
  AssetDataError,
  type AssetDataSource,
  type AssetErrorKind,
  type AssetInput,
  type AssetItem,
  type AssetType,
  type AssetUpdateInput,
} from "@/data/assets";

export { AssetDataError } from "@/data/assets";

type Fetcher = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
type WireAsset = {
  id: number;
  type: AssetType;
  value: string;
  note: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  version: number;
};

const MAX_BODY_BYTES = 1024 * 1024;
const TIMEOUT_MS = 10_000;
const MAX_SAFE_ID = Number.MAX_SAFE_INTEGER;

class InvalidAssetResponse extends Error {}

function object(value: unknown): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new InvalidAssetResponse();
  return value as Record<string, unknown>;
}

function exact(value: Record<string, unknown>, keys: readonly string[]) {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index])) {
    throw new InvalidAssetResponse();
  }
}

function text(value: unknown, minimum: number, maximum: number) {
  if (typeof value !== "string") throw new InvalidAssetResponse();
  const length = Array.from(value).length;
  if (length < minimum || length > maximum) throw new InvalidAssetResponse();
  return value;
}

function integer(value: unknown, minimum = 1, maximum = MAX_SAFE_ID) {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < minimum || value > maximum) {
    throw new InvalidAssetResponse();
  }
  return value;
}

function timestamp(value: unknown) {
  const parsed = text(value, 1, 128);
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?Z$/.exec(parsed);
  if (!match) throw new InvalidAssetResponse();
  const date = new Date(parsed);
  const parts = match.slice(1, 7).map(Number);
  if (!Number.isFinite(date.getTime())
    || date.getUTCFullYear() !== parts[0]
    || date.getUTCMonth() + 1 !== parts[1]
    || date.getUTCDate() !== parts[2]
    || date.getUTCHours() !== parts[3]
    || date.getUTCMinutes() !== parts[4]
    || date.getUTCSeconds() !== parts[5]) throw new InvalidAssetResponse();
  return parsed;
}

function assetType(value: unknown): AssetType {
  if (value !== "domain" && value !== "ip_range") throw new InvalidAssetResponse();
  return value;
}

export function parseAssetItem(value: unknown): WireAsset {
  const raw = object(value);
  exact(raw, ["id", "type", "value", "note", "created_by", "created_at", "updated_at", "version"]);
  return {
    id: integer(raw.id),
    type: assetType(raw.type),
    value: text(raw.value, 1, 253),
    note: text(raw.note, 0, 500),
    created_by: text(raw.created_by, 1, 512),
    created_at: timestamp(raw.created_at),
    updated_at: timestamp(raw.updated_at),
    version: integer(raw.version),
  };
}

export function parseAssetList(value: unknown): WireAsset[] {
  const raw = object(value);
  exact(raw, ["items"]);
  if (!Array.isArray(raw.items) || raw.items.length > 1000) throw new InvalidAssetResponse();
  return raw.items.map(parseAssetItem);
}

function toAsset(value: WireAsset): AssetItem {
  return {
    id: value.id,
    type: value.type,
    value: value.value,
    note: value.note,
    createdBy: value.created_by,
    createdAt: value.created_at,
    updatedAt: value.updated_at,
    version: value.version,
  };
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
    throw new InvalidAssetResponse();
  }
  const declared = response.headers.get("Content-Length");
  if (declared !== null && (!/^\d+$/.test(declared) || Number(declared) > MAX_BODY_BYTES)) {
    await response.body?.cancel().catch(() => undefined);
    throw new InvalidAssetResponse();
  }
  if (!response.body) throw new InvalidAssetResponse();
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
      if (bytes > MAX_BODY_BYTES) throw new InvalidAssetResponse();
      body += decoder.decode(chunk.value, { stream: true });
    }
  } finally {
    if (!complete) await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
  try {
    return JSON.parse(body) as unknown;
  } catch {
    throw new InvalidAssetResponse();
  }
}

function parseError(value: unknown) {
  const envelope = object(value);
  exact(envelope, ["error"]);
  const error = object(envelope.error);
  exact(error, ["code", "message"]);
  return { code: text(error.code, 1, 64), message: text(error.message, 1, 160) };
}

function knownErrorKind(status: number, code: string): AssetErrorKind | null {
  if (status === 401 && code === "authentication_required") return "authentication-required";
  if (status === 403 && code === "forbidden") return "forbidden";
  if (status === 409 && (code === "asset_exists" || code === "asset_conflict")) return "conflict";
  if (status === 404 && code === "asset_not_found") return "not-found";
  if (status === 422 && code === "invalid_asset") return "invalid";
  if (status === 503 && code === "assets_unavailable") return "unavailable";
  return null;
}

function body(input: AssetInput | AssetUpdateInput) {
  return JSON.stringify("expectedVersion" in input ? {
    type: input.type,
    value: input.value,
    note: input.note,
    expected_version: input.expectedVersion,
  } : input);
}

export function createAssetsHttpDataSource({
  fetcher = globalThis.fetch.bind(globalThis),
}: { fetcher?: Fetcher } = {}): AssetDataSource {
  async function request<T>({
    url,
    method,
    input,
    successStatus,
    parse,
    mutation,
  }: {
    url: string;
    method: "GET" | "POST" | "PUT" | "DELETE";
    input?: AssetInput | AssetUpdateInput;
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
        headers: input
          ? { Accept: "application/json", "Content-Type": "application/json" }
          : { Accept: "application/json" },
        body: input ? body(input) : undefined,
        signal: controller.signal,
      });
      if (response.status === successStatus) {
        if (!parse) return undefined as T;
        return parse(await readJson(response, controller.signal));
      }
      const error = parseError(await readJson(response, controller.signal));
      const knownKind = knownErrorKind(response.status, error.code);
      throw new AssetDataError(knownKind ?? (mutation ? "unknown-mutation" : "unavailable"));
    } catch (error) {
      if (error instanceof AssetDataError) throw error;
      throw new AssetDataError(mutation ? "unknown-mutation" : "unavailable");
    } finally {
      clearTimeout(timeout);
    }
  }

  return {
    async list(type) {
      const items = await request({
        url: `/api/assets?type=${type}`,
        method: "GET",
        successStatus: 200,
        parse: parseAssetList,
        mutation: false,
      });
      return items.map(toAsset);
    },
    async create(input) {
      const item = await request({
        url: "/api/assets", method: "POST", input, successStatus: 201, parse: parseAssetItem, mutation: true,
      });
      return toAsset(item);
    },
    async update(id, input) {
      const item = await request({
        url: `/api/assets/${id}`, method: "PUT", input, successStatus: 200, parse: parseAssetItem, mutation: true,
      });
      return toAsset(item);
    },
    async remove(id, expectedVersion) {
      await request({
        url: `/api/assets/${id}?expected_version=${expectedVersion}`,
        method: "DELETE",
        successStatus: 204,
        mutation: true,
      });
    },
  };
}
