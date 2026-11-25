import { AssetDataError } from "@/data/assets";

export { AssetDataError } from "@/data/assets";

export type TechnologyItem = {
  id: number;
  vendor: string;
  product: string;
  softwareVersion: string;
  note: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  version: number;
};

export type TechnologyInput = {
  vendor: string;
  product: string;
  softwareVersion: string;
  note: string;
};

export type TechnologyUpdateInput = TechnologyInput & { expectedVersion: number };

export interface TechnologyProvider {
  list(): Promise<TechnologyItem[]>;
  create(input: TechnologyInput): Promise<TechnologyItem>;
  update(id: number, input: TechnologyUpdateInput): Promise<TechnologyItem>;
  remove(id: number, expectedVersion: number): Promise<void>;
}

const sampleSeed: TechnologyItem[] = [{
  id: 101,
  vendor: "Fortinet",
  product: "FortiOS",
  softwareVersion: "7.2.1",
  note: "VPN gateway mẫu — dữ liệu tổng hợp",
  createdBy: "sample-it",
  createdAt: "2026-11-11T00:00:00Z",
  updatedAt: "2026-11-11T00:00:00Z",
  version: 1,
}];

// This intentionally models only the finite ASCII sample. Backend casefold is authoritative.
function sampleIdentity(input: TechnologyInput) {
  return `${input.vendor.trim().toLowerCase()}\u0000${input.product.trim().toLowerCase()}\u0000${input.softwareVersion.trim()}`;
}

export function createSampleTechnologyProvider(): TechnologyProvider {
  const items = structuredClone(sampleSeed);
  let nextId = 102;
  const now = () => new Date().toISOString();
  return {
    async list() {
      return structuredClone(items);
    },
    async create(input) {
      if (items.some((item) => sampleIdentity({ ...item }) === sampleIdentity(input))) {
        throw new AssetDataError("conflict");
      }
      const at = now();
      const item: TechnologyItem = {
        id: nextId++,
        vendor: input.vendor.trim(),
        product: input.product.trim(),
        softwareVersion: input.softwareVersion.trim(),
        note: input.note,
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
      if (items.some((item, candidate) => candidate !== index && sampleIdentity({ ...item }) === sampleIdentity(input))) {
        throw new AssetDataError("conflict");
      }
      const item: TechnologyItem = {
        ...items[index],
        vendor: input.vendor.trim(),
        product: input.product.trim(),
        softwareVersion: input.softwareVersion.trim(),
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
