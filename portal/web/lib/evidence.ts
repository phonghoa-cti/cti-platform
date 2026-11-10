import type { EvidenceSpan } from "@/data/draft-adapter";

export function sliceCodePoints(text: string, start: number, end: number): string {
  return Array.from(text).slice(start, end).join("");
}

export function getEvidenceSegments(text: string, span: EvidenceSpan) {
  const points = Array.from(text);
  return {
    before: points.slice(0, span[0]).join(""),
    match: points.slice(span[0], span[1]).join(""),
    after: points.slice(span[1]).join(""),
  };
}

export function defangIoc(value: string): string {
  return value
    .replace(/^https:/i, "hxxps:")
    .replace(/^http:/i, "hxxp:")
    .replaceAll(".", "[.]");
}
