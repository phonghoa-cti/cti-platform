import regular from "./fixtures/01-regular.json";
import warning from "./fixtures/02-warning-allowlist-rejected.json";
import empty from "./fixtures/03-empty.json";

export type EvidenceSpan = [number, number];

export interface DraftItem {
  kind: string;
  type: string;
  value: string;
  span: EvidenceSpan | null;
  evidence: string;
  keep: boolean;
  warning: string | null;
  status: string;
}

export interface DraftFinding {
  paragraph: number;
  rule: string;
  excerpt: string;
}

export interface Draft {
  id: number;
  created_at: string;
  schema_version: "1.0";
  status: "pending";
  source: { name: string; sha256: string };
  language: "vi" | "en";
  tlp: string;
  text: string;
  items: DraftItem[];
  injection_warning: boolean;
  findings: DraftFinding[];
  model: string;
  cost_tokens: number;
}

export const supportedTlp = ["TLP:CLEAR", "TLP:GREEN", "TLP:AMBER", "TLP:AMBER+STRICT", "TLP:RED"] as const;
export type Tlp = (typeof supportedTlp)[number];

function record(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${field} phải là object`);
  }
  return value as Record<string, unknown>;
}

function exactKeys(value: Record<string, unknown>, expected: readonly string[], field: string) {
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (actual.length !== wanted.length || actual.some((key, index) => key !== wanted[index])) {
    throw new Error(`${field} có trường không đúng hợp đồng`);
  }
}

function string(value: unknown, field: string, allowEmpty = false): string {
  if (typeof value !== "string" || (!allowEmpty && value.length === 0)) {
    throw new Error(`${field} phải là chuỗi${allowEmpty ? "" : " không rỗng"}`);
  }
  return value;
}

function integer(value: unknown, field: string, minimum = 0): number {
  if (!Number.isSafeInteger(value) || (value as number) < minimum) {
    throw new Error(`${field} phải là số nguyên >= ${minimum}`);
  }
  return value as number;
}

function parseSpan(value: unknown, field: string): EvidenceSpan | null {
  if (value === null) return null;
  if (!Array.isArray(value) || value.length !== 2) throw new Error(`${field} không hợp lệ`);
  const start = integer(value[0], `${field}[0]`);
  const end = integer(value[1], `${field}[1]`);
  if (end < start) throw new Error(`${field} không hợp lệ`);
  return [start, end];
}

function parseItem(value: unknown, index: number): DraftItem {
  const item = record(value, `items[${index}]`);
  exactKeys(item, ["kind", "type", "value", "span", "evidence", "keep", "warning", "status"], `items[${index}]`);
  if (typeof item.keep !== "boolean") throw new Error(`items[${index}].keep phải là boolean`);
  const warning = item.warning === null ? null : string(item.warning, `items[${index}].warning`, true);
  const status = string(item.status, `items[${index}].status`);
  if (!(["ok", "allowlist", "bia"] as string[]).includes(status)) {
    throw new Error(`items[${index}].status không được hỗ trợ`);
  }
  const kind = string(item.kind, `items[${index}].kind`);
  if (item.keep && kind !== "ioc") throw new Error(`items[${index}].kind không được hỗ trợ`);
  return {
    kind,
    type: string(item.type, `items[${index}].type`),
    value: string(item.value, `items[${index}].value`, true),
    span: parseSpan(item.span, `items[${index}].span`),
    evidence: string(item.evidence, `items[${index}].evidence`, true),
    keep: item.keep,
    warning,
    status,
  };
}

function parseFinding(value: unknown, index: number): DraftFinding {
  const finding = record(value, `findings[${index}]`);
  exactKeys(finding, ["paragraph", "rule", "excerpt"], `findings[${index}]`);
  return {
    paragraph: integer(finding.paragraph, `findings[${index}].paragraph`, 1),
    rule: string(finding.rule, `findings[${index}].rule`),
    excerpt: string(finding.excerpt, `findings[${index}].excerpt`, true),
  };
}

export function parseDraft(value: unknown): Draft {
  const draft = record(value, "draft");
  exactKeys(draft, ["id", "created_at", "schema_version", "status", "source", "language", "tlp", "text", "items", "injection_warning", "findings", "model", "cost_tokens"], "draft");
  const source = record(draft.source, "source");
  exactKeys(source, ["name", "sha256"], "source");
  if (!Array.isArray(draft.items)) throw new Error("items phải là mảng");
  if (!Array.isArray(draft.findings)) throw new Error("findings phải là mảng");
  if (typeof draft.injection_warning !== "boolean") throw new Error("injection_warning phải là boolean");

  const id = integer(draft.id, "id", 1);
  const language = string(draft.language, "language");
  if (language !== "vi" && language !== "en") throw new Error("language không được hỗ trợ");
  if (draft.schema_version !== "1.0") throw new Error("schema_version không được hỗ trợ");
  if (draft.status !== "pending") throw new Error("status không được hỗ trợ");
  const sha256 = string(source.sha256, "source.sha256");
  if (!/^[a-f0-9]{64}$/.test(sha256)) throw new Error("source.sha256 không hợp lệ");

  return {
    id,
    created_at: string(draft.created_at, "created_at"),
    schema_version: "1.0",
    status: "pending",
    source: { name: string(source.name, "source.name"), sha256 },
    language,
    tlp: (() => {
      const tlp = string(draft.tlp, "tlp");
      if (!(supportedTlp as readonly string[]).includes(tlp)) throw new Error("tlp không được hỗ trợ");
      return tlp;
    })(),
    text: string(draft.text, "text", true),
    items: draft.items.map(parseItem),
    injection_warning: draft.injection_warning,
    findings: draft.findings.map(parseFinding),
    model: string(draft.model, "model"),
    cost_tokens: integer(draft.cost_tokens, "cost_tokens"),
  };
}

export function parseDraftQueue(values: unknown[]): Draft[] {
  const drafts = values.map(parseDraft);
  const ids = new Set<number>();
  for (const draft of drafts) {
    if (ids.has(draft.id)) throw new Error(`id ${draft.id} bị trùng`);
    ids.add(draft.id);
  }
  return drafts.sort((a, b) => b.id - a.id);
}

export async function loadFixtureDrafts(): Promise<Draft[]> {
  return parseDraftQueue([regular, warning, empty]);
}
