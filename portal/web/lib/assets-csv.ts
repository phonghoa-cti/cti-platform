import type { AssetItem } from "@/data/assets";
import type { TechnologyItem } from "@/data/technologies";

// Excel interprets formula prefixes even in a quoted CSV field. Also protect
// whitespace/control-prefixed formulas and full-width variants.
export function csvCell(value: string): string {
  const unsafe = /^[\s\p{Cc}\p{Cf}]*[=+\-@＝＋－＠]/u.test(value) || /^[\t\r\n]/.test(value);
  const safe = unsafe ? "'" + value : value;
  return '"' + safe.replaceAll('"', '""') + '"';
}

export function assetsCsv(assets: readonly AssetItem[], technologies: readonly TechnologyItem[]): string {
  const rows = [
    ["type", "value", "vendor", "product", "software_version", "note"],
    ...assets.map((item) => [item.type, item.value, "", "", "", item.note]),
    ...technologies.map((item) => ["technology", "", item.vendor, item.product, item.softwareVersion, item.note]),
  ];
  return "\uFEFF" + rows.map((row) => row.map(csvCell).join(",")).join("\r\n") + "\r\n";
}

export function downloadCsv(csv: string, filename: string): void {
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  try {
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
  } finally {
    link.remove();
    // Allow the browser to consume the object URL before releasing it.
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}
