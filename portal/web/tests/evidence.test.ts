import { describe, expect, it } from "vitest";
import regular from "@/data/fixtures/01-regular.json";
import { getEvidenceSegments, sliceCodePoints } from "@/lib/evidence";

describe("Unicode evidence", () => {
  it("uses code-point offsets so an emoji before the IOC does not shift the quote", () => {
    const [start, end] = regular.items[0].span;
    expect(sliceCodePoints(regular.text, start, end)).toBe(regular.items[0].evidence);
    expect(getEvidenceSegments(regular.text, [start, end]).match).toBe(
      "😀 Báo cáo tiếng Việt: ghi nhận kết nối tới evil[.]example.",
    );
  });
});
