import { describe, expect, it } from "vitest";
import { parseDraft, parseDraftQueue } from "@/data/draft-adapter";
import regular from "@/data/fixtures/01-regular.json";

describe("draft adapter", () => {
  it("rejects a malformed stored draft instead of treating it as an empty queue", () => {
    expect(() => parseDraft({ ...regular, id: 0 })).toThrow(/id/i);
    expect(() => parseDraft({ ...regular, items: "not-an-array" })).toThrow(/items/i);
  });

  it("accepts an explicitly empty queue", () => {
    expect(parseDraftQueue([])).toEqual([]);
  });

  it("rejects duplicate IDs so selecting a row is deterministic", () => {
    expect(() => parseDraftQueue([regular, regular])).toThrow(/id/i);
  });
});
