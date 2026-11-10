"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { DraftReview } from "@/components/draft-review";
import { ApiClientError, draftApi, type DecisionRequest, type DraftApi, type DraftDetail, type DraftSummary } from "@/data/api-client";
import { loadFixtureDrafts, type Draft } from "@/data/draft-adapter";
import en from "@/messages/en.json";
import vi from "@/messages/vi.json";

type Locale = "vi" | "en";
type Loader = () => Promise<Draft[]>;
type Mode = "api" | "sample";
type ErrorArea = "queue" | "detail" | "decision";

function safeErrorMessage(error: unknown, area: ErrorArea, locale: Locale) {
  const status = error instanceof ApiClientError ? error.status : undefined;
  const dictionary = locale === "vi" ? {
    queue: "Không tải được hàng đợi. Hãy thử lại.", detail: "Không tải được chi tiết bản nháp. Hãy thử lại.",
    login: "Cần phiên đăng nhập hợp lệ để xem và quyết định bản nháp.", forbidden: "Tài khoản không có quyền thực hiện quyết định này.",
    missing: "Bản nháp không còn khả dụng. Hãy tải lại hàng đợi.", conflict: "Dữ liệu đã thay đổi. Hãy tải lại trước khi quyết định lần nữa.",
    invalid: "Kiểm tra thông tin nhập trước khi gửi lại.", service: "Dịch vụ duyệt chưa sẵn sàng. Hãy thử lại thủ công.",
  } : {
    queue: "The review queue could not be loaded. Try again.", detail: "The draft detail could not be loaded. Try again.",
    login: "A valid signed-in session is required to view and decide drafts.", forbidden: "This account does not have permission to make this decision.",
    missing: "The draft is no longer available. Reload the queue.", conflict: "The data changed. Reload before deciding again.",
    invalid: "Check the entered information before sending again.", service: "The review service is unavailable. Retry manually.",
  };
  if (status === 401) return dictionary.login;
  if (status === 403) return dictionary.forbidden;
  if (status === 404) return dictionary.missing;
  if (status === 409) return dictionary.conflict;
  if (status === 422) return dictionary.invalid;
  if (area === "queue") return dictionary.queue;
  if (area === "detail") return dictionary.detail;
  return dictionary.service;
}

function sampleSummary(draft: Draft): DraftSummary {
  return { id: draft.id, created_at: draft.created_at, status: "pending", source: draft.source, language: draft.language,
    tlp: draft.tlp as DraftSummary["tlp"], item_count: draft.items.length, injection_warning: draft.injection_warning,
    review_status: "pending", review_version: 0 };
}

export function DraftReviewApp({ mode = "api", api = draftApi, loadDrafts = loadFixtureDrafts }: { mode?: Mode; api?: DraftApi; loadDrafts?: Loader }) {
  const [locale, setLocale] = useState<Locale>("vi");
  const [queue, setQueue] = useState<DraftSummary[] | null>(null);
  const [nextBeforeId, setNextBeforeId] = useState<number | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<DraftDetail | Draft | null>(null);
  const [sampleDetails, setSampleDetails] = useState<Draft[]>([]);
  const [queueError, setQueueError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const [decisionRefreshError, setDecisionRefreshError] = useState<string | null>(null);
  const [decisionSuccess, setDecisionSuccess] = useState<"approved" | "rejected" | null>(null);
  const [queueAttempt, setQueueAttempt] = useState(0);
  const [detailAttempt, setDetailAttempt] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const [sending, setSending] = useState(false);
  const [refreshingDecision, setRefreshingDecision] = useState(false);
  const [decisionBlocked, setDecisionBlocked] = useState(false);
  const decisionLock = useRef(false);
  const submittedVersionRef = useRef<string | null>(null);
  const selectedIdRef = useRef<number | null>(null);
  const recordedDecisionRef = useRef<{ id: number; status: "approved" | "rejected" } | null>(null);
  const messages = locale === "vi" ? vi : en;

  const loadQueue = useCallback(async (reset: boolean) => {
    if (mode === "sample") {
      const drafts = await loadDrafts();
      setSampleDetails(drafts);
      setQueue(drafts.map(sampleSummary)); setNextBeforeId(null);
      setSelectedId((current) => {
        const next = current ?? drafts[0]?.id ?? null;
        selectedIdRef.current = next;
        return next;
      });
      setDetail((current) => current ?? drafts[0] ?? null);
      return;
    }
    const page = await api.list();
    setQueue(page.items); setNextBeforeId(page.next_before_id);
    if (reset) setSelectedId((current) => {
      const next = current ?? page.items[0]?.id ?? null;
      selectedIdRef.current = next;
      return next;
    });
  }, [api, loadDrafts, mode]);

  useEffect(() => {
    let active = true;
    void Promise.resolve().then(() => loadQueue(true)).catch((error: unknown) => {
      if (active) setQueueError(safeErrorMessage(error, "queue", locale));
    });
    return () => { active = false; };
    // Locale changes translate existing state and must not issue another request.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadQueue, queueAttempt]);

  useEffect(() => {
    if (mode === "sample" || selectedId === null) return;
    const controller = new AbortController();
    let active = true;
    api.detail(selectedId, controller.signal)
      .then((result) => { if (active) setDetail(result); })
      .catch((error: unknown) => {
        if (active && !(error instanceof DOMException && error.name === "AbortError")) setDetailError(safeErrorMessage(error, "detail", locale));
      });
    return () => { active = false; controller.abort(); };
  // Locale changes translate controls without refetching CTI data.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api, detailAttempt, mode, selectedId]);

  const retryQueue = () => {
    selectedIdRef.current = null;
    submittedVersionRef.current = null;
    recordedDecisionRef.current = null;
    setQueue(null); setQueueError(null); setSelectedId(null); setDetail(null); setDetailError(null);
    setDecisionError(null); setDecisionRefreshError(null); setDecisionSuccess(null); setDecisionBlocked(false);
    setQueueAttempt((value) => value + 1);
  };
  const selectDraft = (id: number) => {
    if (decisionLock.current) return;
    if (selectedIdRef.current === id) return;
    selectedIdRef.current = id;
    submittedVersionRef.current = null;
    recordedDecisionRef.current = null;
    setDetail(null); setDetailError(null); setDecisionError(null); setDecisionRefreshError(null); setDecisionSuccess(null); setDecisionBlocked(false);
    setSelectedId(id);
    if (mode === "sample") setDetail(sampleDetails.find((draft) => draft.id === id) ?? null);
  };
  const retryDetail = () => {
    submittedVersionRef.current = null;
    recordedDecisionRef.current = null;
    setDetail(null); setDetailError(null); setDecisionError(null); setDecisionRefreshError(null); setDecisionSuccess(null); setDecisionBlocked(false);
    setDetailAttempt((value) => value + 1);
  };

  const loadMore = async () => {
    if (mode !== "api" || nextBeforeId === null || loadingMore) return;
    setLoadingMore(true); setQueueError(null);
    try {
      const page = await api.list(nextBeforeId);
      setQueue((current) => [...(current ?? []), ...page.items]); setNextBeforeId(page.next_before_id);
    } catch (error) { setQueueError(safeErrorMessage(error, "queue", locale)); }
    finally { setLoadingMore(false); }
  };

  const refreshDecisionState = async (draftId: number) => {
    const [freshDetail, freshPage] = await Promise.all([api.detail(draftId), api.list()]);
    setQueue(freshPage.items); setNextBeforeId(freshPage.next_before_id);
    if (selectedIdRef.current === draftId) setDetail(freshDetail);
  };

  const retryDecisionRefresh = async () => {
    const recorded = recordedDecisionRef.current;
    if (!recorded || refreshingDecision || decisionLock.current) return;
    decisionLock.current = true;
    setRefreshingDecision(true); setDecisionRefreshError(null);
    try {
      await refreshDecisionState(recorded.id);
    } catch {
      setDecisionRefreshError(messages.decisionRefreshFailed);
    } finally {
      decisionLock.current = false;
      setRefreshingDecision(false);
    }
  };

  const decide = async (request: DecisionRequest) => {
    if (mode !== "api" || !detail || !("review" in detail) || detail.review.status !== "pending" || decisionLock.current) return;
    const decisionDraftId = detail.id;
    const submittedVersion = `${decisionDraftId}:${detail.review.version}`;
    if (submittedVersionRef.current === submittedVersion) return;
    submittedVersionRef.current = submittedVersion;
    decisionLock.current = true; setSending(true); setDecisionError(null); setDecisionRefreshError(null); setDecisionSuccess(null);
    let result: Awaited<ReturnType<DraftApi["decide"]>>;
    try {
      result = await api.decide(decisionDraftId, request);
      if (result.draft_id !== decisionDraftId) throw new ApiClientError("service");
      if (selectedIdRef.current === decisionDraftId) {
        setDecisionSuccess(result.status);
      }
    } catch (error) {
      submittedVersionRef.current = null;
      setDecisionError(safeErrorMessage(error, "decision", locale));
      if (error instanceof ApiClientError && error.status === 409) setDecisionBlocked(true);
      decisionLock.current = false; setSending(false);
      return;
    }

    recordedDecisionRef.current = { id: decisionDraftId, status: result.status };
    try {
      await refreshDecisionState(decisionDraftId);
    } catch {
      setDecisionRefreshError(messages.decisionRefreshFailed);
    } finally {
      decisionLock.current = false; setSending(false);
    }
  };

  return <div className="app-shell">
    <aside className="sidebar" aria-label={messages.section}>
      <div className="brand-mark" aria-label={messages.product}><span className="brand-glyph" aria-hidden="true">PH</span><span>{messages.product}</span></div>
      <p className="nav-group">{messages.section}</p>
      <div className="nav-active" aria-current="page"><span>{messages.navReview}</span><span className="count-badge">{queue?.length ?? "—"}</span></div>
      <div className="sidebar-state"><strong>{mode === "sample" ? messages.localPreview : messages.liveApi}</strong><span>{mode === "sample" ? messages.sourceState : messages.apiSourceState}</span></div>
    </aside>
    <main className="main-content">
      <header className="topbar"><span>{messages.section} / {messages.navReview}</span><div className="locale-switch" aria-label={messages.language}>
        <button type="button" aria-pressed={locale === "vi"} onClick={() => setLocale("vi")}>{messages.vietnamese}</button>
        <button type="button" aria-pressed={locale === "en"} onClick={() => setLocale("en")}>{messages.english}</button>
      </div></header>
      <div className="page-content">
        <div className="page-heading"><div><h1>{messages.pageTitle}</h1><p>{mode === "sample" ? messages.pageDescription : messages.apiPageDescription}</p></div><div className="source-labels">
          <span className={`tag ${mode === "sample" ? "sample-tag" : "api-tag"}`}>{mode === "sample" ? messages.sampleData : messages.liveData}</span>
          <span>{mode === "sample" ? messages.sourceState : messages.apiSourceState}</span>
        </div></div>
        {queue === null && !queueError && <div className="state-panel" role="status" aria-live="polite"><span className="loading-bar" aria-hidden="true" />{messages.loading}</div>}
        {queueError && <div className="state-panel error-panel" role="alert"><strong>{queueError}</strong><button type="button" onClick={retryQueue}>{messages.retry}</button></div>}
        {queue && queue.length === 0 && !(decisionSuccess && detail) && <div className="state-panel">{mode === "sample" ? messages.emptyQueue : messages.emptyApiQueue}</div>}
        {queue && (queue.length > 0 || (decisionSuccess && detail)) && <div className="workspace-grid">
          <section className="panel queue-panel" aria-labelledby="queue-title">
            <header className="panel-header"><h2 id="queue-title">{messages.queueTitle}</h2><span>{queue.length} {messages.loadedDrafts}</span></header>
            <div className="queue-list">{queue.map((draft) => <button type="button" key={draft.id} disabled={sending || refreshingDecision} className={`queue-row ${draft.id === selectedId ? "is-selected" : ""}`} aria-pressed={draft.id === selectedId} aria-label={`${messages.draftNumber} ${draft.id}: ${draft.source.name}`} onClick={() => selectDraft(draft.id)}>
              <span className="queue-id">#{draft.id}</span><span className="queue-source">{draft.source.name}</span><span className="queue-meta">{draft.item_count} {messages.items} · {draft.tlp}</span>
              <span className={`queue-status ${draft.injection_warning ? "has-warning" : ""}`}>{draft.injection_warning ? messages.injectionShort : messages.pending}</span>
            </button>)}</div>
            {nextBeforeId !== null && <button className="load-more" type="button" disabled={loadingMore || sending || refreshingDecision} onClick={() => void loadMore()}>{loadingMore ? messages.loadingMore : messages.loadMore}</button>}
          </section>
          <div className="detail-state">
            {mode === "api" && selectedId !== null && !detail && !detailError && <div className="state-panel" role="status" aria-live="polite">{messages.detailLoading}</div>}
            {detailError && <div className="state-panel error-panel" role="alert"><strong>{detailError}</strong><button type="button" onClick={retryDetail}>{messages.retry}</button></div>}
            {detail && <DraftReview draft={detail} locale={locale} mode={mode} sending={sending} decisionBlocked={decisionBlocked} decisionError={decisionError} decisionRefreshError={decisionRefreshError} decisionSuccess={decisionSuccess} refreshingDecision={refreshingDecision} onDecide={decide} onReload={retryDetail} onRefreshDecision={retryDecisionRefresh} />}
          </div>
        </div>}
      </div>
    </main>
  </div>;
}
