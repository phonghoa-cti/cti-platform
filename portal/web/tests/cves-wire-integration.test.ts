import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { createCvesHttpProvider, parseCveResponse } from "@/data/cves-http";

const WIRE_NAMES = [
  "detail.json",
  "empty.json",
  "near-cap.json",
  "over-cap.json",
  "snapshot-changed.json",
  "summary.json",
  "unavailable.json",
  "w03-forbidden.json",
  "w03-missing-token.json",
] as const;
const defaultWireRoot = path.join(path.dirname(fileURLToPath(import.meta.url)), "fixtures", "w03-integration");
const wireRoot = path.resolve(process.env.W03_WIRE_DIR ?? defaultWireRoot);

function loadWires(root: string) {
  if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) {
    throw new Error(`[W03 wire preflight] fixture directory not found: ${root}`);
  }
  return new Map(WIRE_NAMES.map((name) => {
    const fixturePath = path.join(root, name);
    let raw: string;
    try {
      raw = fs.readFileSync(fixturePath, "utf8");
    } catch {
      throw new Error(`[W03 wire preflight] fixture missing or unreadable: ${fixturePath}`);
    }
    try {
      return [name, { raw, value: JSON.parse(raw) as unknown }] as const;
    } catch {
      throw new Error(`[W03 wire preflight] fixture is not valid JSON: ${fixturePath}`);
    }
  }));
}

const wires = loadWires(wireRoot);

function wire(name: string): unknown {
  return wires.get(name as typeof WIRE_NAMES[number])!.value;
}

function wireProvider(name: typeof WIRE_NAMES[number], status: number, includeLength = false) {
  const body = wires.get(name)!.raw;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (includeLength) headers["Content-Length"] = String(Buffer.byteLength(body));
  return createCvesHttpProvider({
    fetcher: async () => new Response(body, { status, headers }),
  });
}

const query = { kev: false, technologyId: null, q: "", limit: 5, cursor: null } as const;

describe("real W03 API wire compatibility", () => {
  it("parses real detail, summary and empty responses", () => {
    const detail = parseCveResponse(wire("detail.json"));
    const summary = parseCveResponse(wire("summary.json"));
    const empty = parseCveResponse(wire("empty.json"));
    expect(detail.view).toBe("detail");
    expect(detail.items).toHaveLength(5);
    expect(summary.view).toBe("summary");
    expect(summary.items).toHaveLength(5);
    expect(empty.items).toEqual([]);
  });

  it.each([false, true])("reads the near-cap API response through the HTTP provider (length=%s)", async (length) => {
    const nearCap = await wireProvider("near-cap.json", 200, length).list(query);
    expect(nearCap.view).toBe("detail");
    expect(nearCap.items.length).toBeGreaterThan(0);
    expect(Buffer.byteLength(wires.get("near-cap.json")!.raw)).toBeGreaterThan(700_000);
  });

  it.each([false, true])("rejects a response over 1 MiB through the HTTP provider (length=%s)", async (length) => {
    const body = JSON.stringify({ padding: "x".repeat(1024 * 1024) });
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (length) headers["Content-Length"] = String(Buffer.byteLength(body));
    const provider = createCvesHttpProvider({ fetcher: async () => new Response(body, { status: 200, headers }) });
    await expect(provider.list(query)).rejects.toMatchObject({ kind: "unavailable" });
  });

  it.each([
    ["snapshot-changed.json", 409, "snapshot-changed"],
    ["unavailable.json", 503, "unavailable"],
    ["over-cap.json", 503, "unavailable"],
    ["w03-missing-token.json", 401, "authentication-required"],
    ["w03-forbidden.json", 403, "forbidden"],
  ] as const)("maps real API error %s", async (name, status, kind) => {
    await expect(wireProvider(name, status).list(query))
      .rejects.toMatchObject({ kind });
  });
});
