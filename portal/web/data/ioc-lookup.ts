export type LookupLevel = "low" | "medium" | "high";
export type LookupTlp = "TLP:CLEAR" | "TLP:GREEN" | "TLP:AMBER" | "TLP:AMBER+STRICT" | "TLP:RED";
export type LookupIocType = "ipv4" | "ipv6" | "domain" | "url" | "email" | "md5" | "sha1" | "sha256" | "hash";
export type LookupScoreParts = { reliability: number; confirmation: number; freshness: number; asset: number };

export type LookupResult = {
  state: "result";
  input: string;
  ioc: { type: LookupIocType; value: string; display: string };
  found: boolean;
  allowlisted: boolean;
  score: { value: number; level: LookupLevel; reason: string; parts?: LookupScoreParts | null } | null;
  sources: { name: string; firstSeen: string; lastSeen?: string; tlp?: LookupTlp }[];
  related: { techniques: string[]; malware: string[]; actors: string[] };
  enrichment: { country?: string; asn?: string; detections?: string };
  assetMatch?: { matched: boolean; assets: string[] };
  tlp: LookupTlp;
};

export type LookupResponse = LookupResult | {
  state: "not-found" | "invalid" | "private-ip" | "unavailable" | "forbidden" | "authentication-required";
};

export interface LookupDataSource {
  lookup(value: string): Promise<LookupResponse>;
}

const fixtures: Readonly<Record<string, LookupResult>> = {
  "hxxp://Evil[.]COM/a": {
    state: "result",
    input: "hxxp://Evil[.]COM/a",
    ioc: { type: "url", value: "http://evil.com/a", display: "hxxp://evil[.]com/a" },
    found: true,
    allowlisted: false,
    score: { value: 78, level: "high", reason: "Ba nguồn tổng hợp xác nhận IOC trong khoảng thời gian gần đây." },
    sources: [
      { name: "Nguồn CTI tổng hợp A", firstSeen: "2026-10-20T08:00:00+07:00" },
      { name: "Nguồn CTI tổng hợp B", firstSeen: "2026-10-21T09:30:00+07:00" },
      { name: "Báo cáo tổng hợp nội bộ", firstSeen: "2026-10-22T13:15:00+07:00" },
    ],
    related: { techniques: ["T1566.001"], malware: ["Họ mã độc mẫu"], actors: [] },
    enrichment: { country: "NL", asn: "AS64500", detections: "12/90" },
    tlp: "TLP:GREEN",
  },
  "allowlisted.example": {
    state: "result",
    input: "allowlisted.example",
    ioc: { type: "domain", value: "allowlisted.example", display: "allowlisted[.]example" },
    found: true,
    allowlisted: true,
    score: { value: 0, level: "low", reason: "Fixture xác định đây là hạ tầng hợp pháp trong allowlist." },
    sources: [],
    related: { techniques: [], malware: [], actors: [] },
    enrichment: {},
    tlp: "TLP:CLEAR",
  },
};

export const sampleLookupSource: LookupDataSource = {
  async lookup(value) {
    if (value.length === 0 || value.trim().length === 0) return { state: "invalid" };
    return Object.hasOwn(fixtures, value) ? fixtures[value] : { state: "not-found" };
  },
};
