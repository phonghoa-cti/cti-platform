export type CveErrorKind =
  | "authentication-required"
  | "forbidden"
  | "not-found"
  | "invalid"
  | "snapshot-changed"
  | "unavailable";

export class CveDataError extends Error {
  constructor(public readonly kind: CveErrorKind) {
    super(kind);
    this.name = "CveDataError";
  }
}

export type CveQuery = {
  kev: boolean;
  technologyId: number | null;
  q: string;
  limit: number;
  cursor: string | null;
};

export type CveSource = {
  kind: "synthetic";
  datasetId: string;
  sourceAsOf: string;
  retrievedAt: string;
};

export type CveMatch = {
  technologyId: number;
  vendor: string;
  product: string;
  softwareVersion: string;
  matchReason: "vendor_product_exact_casefold";
  versionAssessment: "not_performed";
};

export type CveDetailItem = {
  cveId: string;
  title: string;
  kev: boolean;
  kevDueDate: string | null;
  kevAsOf: string;
  epssScore: number | null;
  epssPercentile: number | null;
  epssAsOf: string | null;
  cvssBaseScore: number | null;
  cvssVersion: "3.1" | "4.0" | null;
  publishedAt: string | null;
  advisoryUrl: string | null;
  matches: CveMatch[];
  priority: number;
};

export type CveSummaryItem = {
  cveId: string;
  title: string;
  kev: boolean;
  epssScore: number | null;
  cvssBaseScore: number | null;
  priority: number;
  matchCount: number;
};

type CveEnvelope = {
  summary: { matchedCves: number; kevCves: number };
  page: { nextCursor: string | null; limit: number };
  source: CveSource;
  notice: string;
};

export type CveDetailResponse = CveEnvelope & { view: "detail"; items: CveDetailItem[] };
export type CveSummaryResponse = CveEnvelope & { view: "summary"; items: CveSummaryItem[] };
export type CveResponse = CveDetailResponse | CveSummaryResponse;

export interface CveProvider {
  list(query: CveQuery): Promise<CveResponse>;
}

const notice = "Liên quan theo tên sản phẩm; cần kiểm tra phiên bản/phạm vi bị ảnh hưởng trước khi vá.";
const source: CveSource = {
  kind: "synthetic",
  datasetId: `sha256:${"1".repeat(64)}`,
  sourceAsOf: "2026-11-01T00:00:00Z",
  retrievedAt: "2026-11-01T01:00:00Z",
};

const sampleProducts = [
  ["Fortinet", "FortiOS", "7.2.1"],
  ["Microsoft", "Exchange Server", "2019 CU14"],
  ["VMware", "vCenter Server", "8.0 U2"],
] as const;

const sampleItems: CveDetailItem[] = Array.from({ length: 12 }, (_, index) => {
  const [vendor, product, softwareVersion] = sampleProducts[index % sampleProducts.length];
  const number = String(index + 1).padStart(4, "0");
  const kev = index < 7;
  return {
    cveId: `CVE-2026-${number}`,
    title: `${product}: bản ghi lỗ hổng tổng hợp ${index + 1}`,
    kev,
    kevDueDate: kev && index % 2 === 0 ? `2026-12-${String(index + 1).padStart(2, "0")}` : null,
    kevAsOf: "2026-11-01",
    epssScore: index === 10 ? null : Math.max(0, 0.92 - index * 0.07),
    epssPercentile: index === 10 ? null : Math.max(0, 0.98 - index * 0.05),
    epssAsOf: index === 10 ? null : "2026-11-01",
    cvssBaseScore: index === 11 ? null : Math.max(0, 9.8 - index * 0.4),
    cvssVersion: index === 11 ? null : "3.1",
    publishedAt: `2026-10-${String(index + 1).padStart(2, "0")}T08:00:00Z`,
    advisoryUrl: `https://example.invalid/advisories/CVE-2026-${number}`,
    matches: [{
      technologyId: 101 + (index % sampleProducts.length),
      vendor,
      product,
      softwareVersion,
      matchReason: "vendor_product_exact_casefold",
      versionAssessment: "not_performed",
    }],
    priority: index + 1,
  };
});

export function createSampleCveProvider(): CveProvider {
  return {
    async list(query) {
      let filtered = sampleItems.filter((item) => !query.kev || item.kev);
      if (query.technologyId !== null) {
        filtered = filtered.filter((item) => item.matches.some((match) => match.technologyId === query.technologyId));
      }
      const needle = query.q.trim().toLocaleLowerCase("en-US");
      if (needle) filtered = filtered.filter((item) => `${item.cveId}\n${item.title}`.toLocaleLowerCase("en-US").includes(needle));
      filtered = filtered.map((item, index) => ({ ...item, priority: index + 1 }));
      const offset = query.cursor?.startsWith("sample:") ? Number(query.cursor.slice(7)) : 0;
      const items = filtered.slice(offset, offset + query.limit);
      const next = offset + query.limit < filtered.length ? `sample:${offset + query.limit}` : null;
      return structuredClone({
        view: "detail" as const,
        items,
        summary: { matchedCves: filtered.length, kevCves: filtered.filter((item) => item.kev).length },
        page: { nextCursor: next, limit: query.limit },
        source,
        notice,
      });
    },
  };
}
