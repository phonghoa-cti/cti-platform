"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CveDataError, createSampleCveProvider, type CveProvider, type CveResponse } from "@/data/cves";
import { createCvesHttpProvider } from "@/data/cves-http";
import found from "@/data/fixtures/w04-fixture-found-url-asset.json";
import allowlisted from "@/data/fixtures/w04-fixture-allowlisted-asset.json";

type Locale = "vi" | "en";
type LoadState = { kind: "loading" } | { kind: "error"; reason: string } | { kind: "ready"; data: CveResponse };

const messages = {
  vi: {
    title: "Tổng quan", navigation: "Giám sát", risk: "Rủi ro", operations: "Vận hành",
    cves: "Lỗ hổng", assets: "Tài sản", ioc: "Điều tra IOC", drafts: "Hàng chờ duyệt",
    refresh: "Làm mới", switchSample: "Xem trang mẫu", switchApi: "Về trang API",
    sample: "Dữ liệu mẫu — chỉ các bản ghi giả lập sẵn có; không đại diện tình hình hôm nay.",
    api: "API cục bộ — nguồn CVE hiện là dữ liệu giả lập; không tự chuyển sang mẫu nếu có lỗi.",
    threat: "Mức đe dọa hôm nay", unknown: "Chưa xác định",
    threatReason: "Chưa có đủ nguồn IOC theo thời gian và trạng thái xử lý để tính mức đe dọa.",
    kpiIoc: "IOC mới · 24 giờ", kpiMatch: "IOC khớp tài sản", kpiKev: "CVE KEV liên quan", kpiWazuh: "Cảnh báo Wazuh · 7 ngày",
    noSource: "Chưa có nguồn dữ liệu", fixtureCount: "Chỉ trong fixture tra cứu, không phải tổng số doanh nghiệp.",
    kevNote: "Khớp tên sản phẩm, chưa xác nhận phiên bản bị ảnh hưởng.",
    alerts: "Cảnh báo mới / việc cần chú ý", alertsNote: "Chưa có nguồn cảnh báo theo thời gian. Các mục bên dưới là ứng viên ưu tiên từ CVE và IOC; không phải sự cố đã xác nhận.",
    priorities: "CVE ưu tiên", matches: "IOC khớp tài sản", latest: "Tối đa 5 CVE theo thứ tự ưu tiên API",
    emptyCve: "Không có CVE liên quan trong dữ liệu trả về.", noIoc: "Không có IOC khớp trong fixture.",
    loading: "Đang tải dữ liệu CVE…", error: "Không tải được dữ liệu CVE",
    forbidden: "Không có quyền xem.", auth: "Cần đăng nhập.", unavailable: "Nguồn tạm thời không sẵn sàng.",
    trend: "Xu hướng IOC · 30 ngày", techniques: "Kỹ thuật ATT&CK · 7 ngày", malware: "Mã độc / nhóm · 7 ngày",
    sources: "Tình trạng nguồn dữ liệu", cveSource: "CVE / KEV", iocSource: "IOC / OpenCTI", wazuhSource: "Wazuh",
    synthetic: "Giả lập", ready: "Đã đọc", failure: "Lỗi", sourceDate: "Mốc dữ liệu", score: "Điểm", priority: "Ưu tiên",
    detail: "Xem lỗ hổng", lookup: "Mở điều tra IOC", kevCandidate: "Kiểm tra CVE trong KEV", iocCandidate: "Kiểm tra IOC khớp tài sản", noCandidates: "Chưa có ứng viên từ dữ liệu hiện có.",
  },
  en: {
    title: "Overview", navigation: "Monitoring", risk: "Risk", operations: "Operations",
    cves: "Vulnerabilities", assets: "Assets", ioc: "IOC lookup", drafts: "Review queue",
    refresh: "Refresh", switchSample: "View sample", switchApi: "Back to API view",
    sample: "Sample data — existing synthetic records only; not today's actual situation.",
    api: "Local API — CVE source is currently synthetic; errors never fall back to sample data.",
    threat: "Today's threat level", unknown: "Undetermined",
    threatReason: "Time-window IOC data and remediation status are not available to calculate threat level.",
    kpiIoc: "New IOCs · 24 hours", kpiMatch: "Asset-matched IOCs", kpiKev: "Related KEV CVEs", kpiWazuh: "Wazuh alerts · 7 days",
    noSource: "Data source not available", fixtureCount: "Lookup fixtures only, not an organization-wide total.",
    kevNote: "Product-name match, affected version not confirmed.",
    alerts: "New alerts / items to review", alertsNote: "No time-based alert source. Items below are CVE and IOC review candidates, not confirmed incidents.",
    priorities: "Priority CVEs", matches: "Asset-matched IOCs", latest: "Up to 5 CVEs in API priority order",
    emptyCve: "No related CVEs in the returned data.", noIoc: "No matched IOC in the fixture.",
    loading: "Loading CVE data…", error: "Could not load CVE data",
    forbidden: "Access denied.", auth: "Sign-in required.", unavailable: "Source temporarily unavailable.",
    trend: "IOC trends · 30 days", techniques: "ATT&CK techniques · 7 days", malware: "Malware / groups · 7 days",
    sources: "Data source health", cveSource: "CVE / KEV", iocSource: "IOC / OpenCTI", wazuhSource: "Wazuh",
    synthetic: "Synthetic", ready: "Read successfully", failure: "Error", sourceDate: "Data as of", score: "Score", priority: "Priority",
    detail: "View vulnerabilities", lookup: "Open IOC lookup", kevCandidate: "Review KEV CVE", iocCandidate: "Review asset-matched IOC", noCandidates: "No review candidates in available data.",
  },
} as const;

// Existing W04 fixtures: exclude legitimate allowlisted and not-found entries.
const sampleMatches = [found, allowlisted].filter((item) => item.found && !item.allowlisted && item.asset_match.matched);
const query = { kev: false, technologyId: null, q: "", limit: 10, cursor: null } as const;

export function OverviewApp({ mode, provider }: { mode: "sample" | "api"; provider: CveProvider }) {
  const [locale, setLocale] = useState<Locale>("vi");
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [revision, setRevision] = useState(0);
  const m = messages[locale];
  const sample = mode === "sample";
  const route = (path: string) => sample ? path + "/mau" : path;

  useEffect(() => {
    let active = true;
    provider.list(query).then(
      (data) => { if (active) setState({ kind: "ready", data }); },
      (error: unknown) => { if (active) setState({ kind: "error", reason: error instanceof CveDataError ? error.kind : "unavailable" }); },
    );
    return () => { active = false; };
  }, [provider, revision]);

  const data = state.kind === "ready" ? state.data : null;
  const priorities = data ? [...data.items].sort((a, b) => a.priority - b.priority).slice(0, 5) : [];
  // Chỉ là ứng viên kiểm tra từ bản ghi hiện có, không gán thời điểm cảnh báo hay trạng thái xử lý.
  const candidates = [
    ...priorities.filter((item) => item.kev).slice(0, sample ? Math.max(0, 5 - sampleMatches.length) : 5).map((item) => ({
      key: item.cveId, label: m.kevCandidate, value: item.cveId, href: route("/lo-hong"),
    })),
    ...(sample ? sampleMatches.map((item) => ({
      key: item.ioc.display, label: m.iocCandidate, value: item.ioc.display, href: route("/tra-cuu"),
    })) : []),
  ].slice(0, 5);
  const cveValue = data ? data.summary.kevCves.toLocaleString(locale) : "—";
  const statusText = state.kind === "loading" ? m.loading : state.kind === "error" ? m.failure : m.ready;
  const errorDetail = state.kind === "error" && state.reason === "authentication-required" ? m.auth
    : state.kind === "error" && state.reason === "forbidden" ? m.forbidden : m.unavailable;

  return <div className="app-shell">
    <aside className="sidebar" aria-label={m.navigation}>
      <div className="brand-mark"><span className="brand-glyph" aria-hidden="true">PH</span>Phong Hỏa</div>
      <p className="nav-group">{m.navigation}</p>
      <div className="nav-active" aria-current="page">{m.title}</div>
      <Link className="nav-link" href={route("/tra-cuu")}>{m.ioc}</Link>
      <p className="nav-group">{m.risk}</p>
      <Link className="nav-link" href={route("/lo-hong")}>{m.cves}</Link>
      <Link className="nav-link" href={route("/tai-san")}>{m.assets}</Link>
      <p className="nav-group">{m.operations}</p>
      <Link className="nav-link" href={route("/duyet")}>{m.drafts}</Link>
    </aside>
    <main className="main-content overview">
      <header className="topbar overview-topbar">
        <span>{m.navigation} / {m.title}</span>
        <div className="locale-switch" aria-label={locale === "vi" ? "Ngôn ngữ" : "Language"}>
          <button type="button" aria-pressed={locale === "vi"} onClick={() => setLocale("vi")}>Tiếng Việt</button>
          <button type="button" aria-pressed={locale === "en"} onClick={() => setLocale("en")}>English</button>
        </div>
      </header>
      <div className="overview-content">
        <div className="overview-heading">
          <h1>{m.title}</h1>
          <div className="overview-actions">
            <Link href={sample ? "/tong-quan" : "/tong-quan/mau"}>{sample ? m.switchApi : m.switchSample}</Link>
            <button type="button" className="assets-app__secondary" disabled={state.kind === "loading"} onClick={() => {
              setState({ kind: "loading" });
              setRevision((value) => value + 1);
            }}>{m.refresh}</button>
          </div>
        </div>
        <p className="overview-disclaimer">{sample ? m.sample : m.api}</p>
        <section className="overview-panel">
          <h2>{m.threat}</h2><p><strong className="overview-tag">{m.unknown}</strong> {m.threatReason}</p>
        </section>
        <div className="overview-kpis">
          <section className="overview-panel"><h2>{m.kpiIoc}</h2><strong className="overview-value mono">—</strong><p>{m.noSource}</p></section>
          <section className="overview-panel"><h2>{m.kpiMatch}</h2><strong className="overview-value mono">{sample ? sampleMatches.length : "—"}</strong><p>{sample ? m.fixtureCount : m.noSource}</p><Link href={route("/tra-cuu")}>{m.lookup}</Link></section>
          <section className="overview-panel"><h2>{m.kpiKev}</h2><strong className="overview-value mono">{cveValue}</strong><p>{data ? m.kevNote : statusText}</p><Link href={route("/lo-hong")}>{m.detail}</Link></section>
          <section className="overview-panel"><h2>{m.kpiWazuh}</h2><strong className="overview-value mono">—</strong><p>{m.noSource}</p></section>
        </div>
        <section className="overview-panel">
          <h2>{m.alerts}</h2><p>{m.alertsNote}</p>
          {candidates.length > 0 ? <ul className="overview-list">{candidates.map((item) => <li key={item.key}>
            <Link href={item.href}>{item.label} · <code>{item.value}</code></Link>
          </li>)}</ul> : <p>{data ? m.noCandidates : statusText}</p>}
        </section>
        <div className="overview-two">
          <section className="overview-panel">
            <h2>{m.priorities}</h2><p>{m.latest}</p>
            {state.kind === "loading" && <p role="status">{m.loading}</p>}
            {state.kind === "error" && <p role="alert">{m.error}: {errorDetail}</p>}
            {data && data.items.length === 0 && <p>{m.emptyCve}</p>}
            {data && data.items.length > 0 && <ul className="overview-list">
              {priorities.map((item) => <li key={item.cveId}>
                <div><Link href={route("/lo-hong")}><code>{item.cveId}</code></Link> {item.kev && <span className="overview-tag overview-kev">KEV</span>}</div>
                <span>{item.title}</span><small>{m.priority} <code>{item.priority}</code></small>
              </li>)}
            </ul>}
          </section>
          <section className="overview-panel" aria-labelledby="overview-matched-iocs">
            <h2 id="overview-matched-iocs">{m.matches}</h2>
            {!sample ? <p>{m.noSource}</p> : <>
              <p>{m.fixtureCount}</p>
              {sampleMatches.length === 0 ? <p>{m.noIoc}</p> : <ul className="overview-list">{sampleMatches.map((item) => <li key={item.ioc.display}>
                <code>{item.ioc.display}</code><span>{item.asset_match.assets.join(", ")}</span>
                <small>{m.score}: <code>{item.score.value}</code> · {item.tlp}</small>
              </li>)}</ul>}
            </>}
          </section>
        </div>
        <div className="overview-two">
          <section className="overview-panel"><h2>{m.trend}</h2><p>{m.noSource}</p></section>
          <section className="overview-panel"><h2>{m.techniques}</h2><p>{m.noSource}</p></section>
        </div>
        <section className="overview-panel"><h2>{m.malware}</h2><p>{m.noSource}</p></section>
        <section className="overview-panel">
          <h2>{m.sources}</h2>
          <ul className="overview-list">
            <li><strong>{m.cveSource}</strong><span>{statusText}{data ? " · " + m.synthetic : ""}</span>{data && <small>{m.sourceDate}: <code>{data.source.sourceAsOf}</code></small>}</li>
            <li><strong>{m.iocSource}</strong><span>{sample ? m.synthetic + " · " + m.fixtureCount : m.noSource}</span></li>
            <li><strong>{m.wazuhSource}</strong><span>{m.noSource}</span></li>
          </ul>
        </section>
      </div>
    </main>
  </div>;
}

export function OverviewClient({ mode }: { mode: "sample" | "api" }) {
  const [provider] = useState(() => mode === "sample" ? createSampleCveProvider() : createCvesHttpProvider());
  return <OverviewApp mode={mode} provider={provider} />;
}
