import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { createCvesHttpProvider, parseCveResponse } from "@/data/cves-http";

const wireRoot = process.env.W03_WIRE_DIR;

function wire(name: string): unknown {
  if (!wireRoot) throw new Error("W03_WIRE_DIR is required");
  return JSON.parse(fs.readFileSync(path.join(wireRoot, name), "utf8")) as unknown;
}

function errorProvider(name: string, status: number) {
  return createCvesHttpProvider({
    fetcher: async () => new Response(JSON.stringify(wire(name)), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  });
}

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

  it("parses the real API response nearest the 1 MiB cap without truncation", () => {
    const nearCap = parseCveResponse(wire("near-cap.json"));
    expect(nearCap.view).toBe("detail");
    expect(nearCap.items.length).toBeGreaterThan(0);
    expect(JSON.stringify(wire("near-cap.json")).length).toBeGreaterThan(700_000);
  });

  it.each([
    ["snapshot-changed.json", 409, "snapshot-changed"],
    ["unavailable.json", 503, "unavailable"],
    ["over-cap.json", 503, "unavailable"],
    ["w03-missing-token.json", 401, "authentication-required"],
    ["w03-forbidden.json", 403, "forbidden"],
  ] as const)("maps real API error %s", async (name, status, kind) => {
    await expect(errorProvider(name, status).list({ kev: false, technologyId: null, q: "", limit: 5, cursor: null }))
      .rejects.toMatchObject({ kind });
  });
});
