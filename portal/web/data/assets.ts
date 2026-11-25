export type AssetType = "domain" | "ip_range";
export type AssetErrorKind =
  | "authentication-required"
  | "forbidden"
  | "unavailable"
  | "conflict"
  | "invalid"
  | "not-found"
  | "unknown-mutation";

export type AssetItem = {
  id: number;
  type: AssetType;
  value: string;
  note: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  version: number;
};

export type AssetInput = { type: AssetType; value: string; note: string };
export type AssetUpdateInput = AssetInput & { expectedVersion: number };

export class AssetDataError extends Error {
  constructor(readonly kind: AssetErrorKind) {
    super(kind);
    this.name = "AssetDataError";
  }
}

export interface AssetDataSource {
  list(type: AssetType): Promise<AssetItem[]>;
  create(input: AssetInput): Promise<AssetItem>;
  update(id: number, input: AssetUpdateInput): Promise<AssetItem>;
  remove(id: number, expectedVersion: number): Promise<void>;
}

const sampleSeed: AssetItem[] = [
  {
    id: 1,
    type: "domain",
    value: "congty-mau.vn",
    note: "Tên miền chính — dữ liệu tổng hợp",
    createdBy: "sample-it",
    createdAt: "2026-11-11T00:00:00Z",
    updatedAt: "2026-11-11T00:00:00Z",
    version: 1,
  },
  {
    id: 2,
    type: "ip_range",
    value: "203.0.113.0/24",
    note: "Dải tài liệu RFC 5737 — dữ liệu tổng hợp",
    createdBy: "sample-it",
    createdAt: "2026-11-11T00:00:00Z",
    updatedAt: "2026-11-11T00:00:00Z",
    version: 1,
  },
];

export function createSampleAssetsDataSource(): AssetDataSource {
  const items = structuredClone(sampleSeed);
  let nextId = 3;
  const now = () => new Date().toISOString();
  return {
    async list(type) {
      return structuredClone(items.filter((item) => item.type === type));
    },
    async create(input) {
      const at = now();
      const item: AssetItem = {
        id: nextId++,
        ...input,
        createdBy: "sample-it",
        createdAt: at,
        updatedAt: at,
        version: 1,
      };
      items.push(item);
      return structuredClone(item);
    },
    async update(id, input) {
      const index = items.findIndex((item) => item.id === id);
      if (index < 0) throw new AssetDataError("not-found");
      if (items[index].version !== input.expectedVersion) throw new AssetDataError("conflict");
      const item = {
        ...items[index],
        type: input.type,
        value: input.value,
        note: input.note,
        version: input.expectedVersion + 1,
        updatedAt: now(),
      };
      items[index] = item;
      return structuredClone(item);
    },
    async remove(id, expectedVersion) {
      const index = items.findIndex((item) => item.id === id);
      if (index < 0) throw new AssetDataError("not-found");
      if (items[index].version !== expectedVersion) throw new AssetDataError("conflict");
      items.splice(index, 1);
    },
  };
}
