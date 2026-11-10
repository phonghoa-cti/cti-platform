"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { DraftReview, type SelectionPhase } from "@/components/draft-review";
import { ApiClientError, draftApi, type DecisionRequest, type DraftApi, type DraftDetail, type DraftSummary, type SelectionView } from "@/data/api-client";
import { loadFixtureDrafts, type Draft } from "@/data/draft-adapter";
import en from "@/messages/en.json";
import vi from "@/messages/vi.json";

type Locale = "vi" | "en";
type Loader = () => Promise<Draft[]>;
type Mode = "api" | "sample";

function sameIndices(left: readonly number[], right: readonly number[]) {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}
function safeReadError(area: "queue" | "detail", locale: Locale) {
  if (locale === "vi") return area === "queue" ? "Không tải được hàng đợi. Hãy thử lại." : "Không tải được chi tiết bản nháp. Hãy thử lại.";
  return area === "queue" ? "The review queue could not be loaded. Try again." : "The draft detail could not be loaded. Try again.";
}
function knownHttp(error: unknown) {
  return error instanceof ApiClientError && error.kind === "http" && [401, 403, 404, 409, 413, 415, 422].includes(error.status ?? 0);
}
function writeError(error: unknown, locale: Locale, operation: "save" | "decision") {
  const status = error instanceof ApiClientError ? error.status : undefined;
  const viText: Record<number, string> = {
    401: "Cần phiên đăng nhập hợp lệ để ghi thay đổi.", 403: "Tài khoản không có quyền thực hiện thao tác này.",
    404: "Bản nháp không còn khả dụng. Hãy bỏ thay đổi cục bộ và tải lại hàng đợi.",
    409: "Dữ liệu đã thay đổi. Hãy tải lại trước khi lưu hoặc quyết định.",
    413: "Yêu cầu lưu quá lớn. Hãy giảm lựa chọn rồi gửi thao tác mới.",
    415: "Yêu cầu không đúng định dạng mà dịch vụ hỗ trợ.",
    422: "Lựa chọn không còn hợp lệ. Hãy tải lại trạng thái.",
  };
  const enText: Record<number, string> = {
    401: "A valid signed-in session is required to write changes.", 403: "This account cannot perform this action.",
    404: "The draft is no longer available. Discard local changes and reload the queue.",
    409: "The data changed. Reload before saving or deciding.",
    413: "The save request is too large. Reduce the selection and start a new action.",
    415: "The request format is not supported by the service.",
    422: "The selection is no longer valid. Reload the state.",
  };
  if (status && (locale === "vi" ? viText[status] : enText[status])) return (locale === "vi" ? viText : enText)[status];
  if (operation === "save") return locale === "vi"
    ? "Chưa xác định lựa chọn đã được lưu. Không gửi lại; hãy tải lại trạng thái."
    : "It is unknown whether the selection was saved. Do not resend it; reload the state.";
  return locale === "vi"
    ? "Chưa xác định quyết định đã được ghi. Không gửi lại; hãy tải lại trạng thái."
    : "It is unknown whether the decision was recorded. Do not resend it; reload the state.";
}
function sampleSummary(draft: Draft): DraftSummary {
  return { id: draft.id, created_at: draft.created_at, status: "pending", source: draft.source, language: draft.language,
    tlp: draft.tlp as DraftSummary["tlp"], item_count: draft.items.length, injection_warning: draft.injection_warning,
    review_status: "pending", review_version: 0, selection_version: 0 };
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
  const [queueAttempt, setQueueAttempt] = useState(0);
  const [detailAttempt, setDetailAttempt] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const [savedSelection, setSavedSelection] = useState<SelectionView | null>(null);
  const [editingIndices, setEditingIndices] = useState<number[]>([]);
  const [phase, setPhase] = useState<SelectionPhase>("idle");
  const [selectionError, setSelectionError] = useState<string | null>(null);
  const [selectionNotice, setSelectionNotice] = useState<string | null>(null);
  const [decisionSuccess, setDecisionSuccess] = useState<"approved" | "rejected" | null>(null);
  const operationLock = useRef(false);
  const selectedIdRef = useRef<number | null>(null);
  const generationRef = useRef(0);
  const messages = locale === "vi" ? vi : en;
  const dirty = useMemo(() => !!savedSelection && !sameIndices(savedSelection.selected_indices, editingIndices), [editingIndices, savedSelection]);
  const navigationLocked = dirty || phase !== "idle";

  const resetActionState = () => {
    setSavedSelection(null); setEditingIndices([]); setPhase("idle"); setSelectionError(null); setSelectionNotice(null); setDecisionSuccess(null);
  };
  const applyDetail = (result: DraftDetail) => {
    setDetail(result); setSavedSelection(result.selection); setEditingIndices([...result.selection.selected_indices]);
  };
  const loadQueue = useCallback(async () => {
    if (mode === "sample") {
      const drafts = await loadDrafts(); setSampleDetails(drafts); setQueue(drafts.map(sampleSummary)); setNextBeforeId(null);
      const first = drafts[0]?.id ?? null; selectedIdRef.current = first; setSelectedId(first); setDetail(drafts[0] ?? null); return;
    }
    const page = await api.list(); setQueue(page.items); setNextBeforeId(page.next_before_id);
    const first = page.items[0]?.id ?? null; selectedIdRef.current = first; setSelectedId(first);
  }, [api, loadDrafts, mode]);

  useEffect(() => {
    let active = true; void Promise.resolve().then(loadQueue).catch(() => { if (active) setQueueError(safeReadError("queue", locale)); });
    return () => { active = false; };
    // Locale switches translate current state and do not refetch CTI data.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadQueue, queueAttempt]);

  useEffect(() => {
    if (mode === "sample" || selectedId === null) return;
    const controller = new AbortController(); const generation = ++generationRef.current; let active = true;
    api.detail(selectedId, controller.signal).then((result) => {
      if (active && selectedIdRef.current === selectedId && generationRef.current === generation) applyDetail(result);
    }).catch((error: unknown) => {
      if (active && !(error instanceof DOMException && error.name === "AbortError")) setDetailError(safeReadError("detail", locale));
    });
    return () => { active = false; controller.abort(); };
    // Locale switches translate controls without refetching CTI data.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api, detailAttempt, mode, selectedId]);

  const retryQueue = () => { setQueue(null); setQueueError(null); setDetail(null); selectedIdRef.current = null; setSelectedId(null); resetActionState(); setQueueAttempt((value) => value + 1); };
  const selectDraft = (id: number) => {
    if (navigationLocked || selectedIdRef.current === id) return;
    generationRef.current += 1; selectedIdRef.current = id; setSelectedId(id); setDetail(null); setDetailError(null); resetActionState();
    if (mode === "sample") setDetail(sampleDetails.find((draft) => draft.id === id) ?? null);
  };
  const retryDetail = () => { if (navigationLocked) return; setDetail(null); setDetailError(null); resetActionState(); setDetailAttempt((value) => value + 1); };
  const loadMore = async () => {
    if (mode !== "api" || nextBeforeId === null || loadingMore || navigationLocked) return;
    setLoadingMore(true); setQueueError(null);
    try { const page = await api.list(nextBeforeId); setQueue((current) => [...(current ?? []), ...page.items]); setNextBeforeId(page.next_before_id); }
    catch { setQueueError(safeReadError("queue", locale)); } finally { setLoadingMore(false); }
  };

  const toggleSelection = (index: number) => {
    if (phase !== "idle" || !detail || !("selection" in detail) || detail.review.status !== "pending") return;
    const item = detail.items[index]; if (!item || item.kind !== "ioc" || !item.keep || item.status !== "ok") return;
    setSelectionError(null); setSelectionNotice(null);
    setEditingIndices((current) => current.includes(index) ? current.filter((value) => value !== index) : current.length >= 1024 ? current : [...current, index].sort((a, b) => a - b));
  };
  const discardSelection = () => { if (phase === "idle" && savedSelection) { setEditingIndices([...savedSelection.selected_indices]); setSelectionError(null); setSelectionNotice(null); } };

  const refreshAfterWrite = async (draftId: number, minimumSelectionVersion: number) => {
    const [freshDetail, freshPage] = await Promise.all([api.detail(draftId), api.list()]);
    if (freshDetail.id !== draftId || freshDetail.selection.selection_version < minimumSelectionVersion) throw new ApiClientError("service");
    if (selectedIdRef.current === draftId) applyDetail(freshDetail);
    setQueue(freshPage.items); setNextBeforeId(freshPage.next_before_id);
  };

  const saveSelection = async () => {
    if (mode !== "api" || operationLock.current || phase !== "idle" || !dirty || !savedSelection || !detail || !("selection" in detail) || editingIndices.length > 1024) return;
    const draftId = detail.id; const generation = generationRef.current; const request = { expected_version: savedSelection.review_version, selected_indices: [...editingIndices] };
    operationLock.current = true; setPhase("saving"); setSelectionError(null); setSelectionNotice(null);
    try {
      const result = await api.saveSelection(draftId, request);
      const increment = result.changed ? 1 : 0;
      if (selectedIdRef.current !== draftId || generationRef.current !== generation || !sameIndices(result.selected_indices, request.selected_indices) || result.review_version !== request.expected_version + increment || result.selection_version !== request.expected_version + increment) throw new ApiClientError("service");
      setSavedSelection(result); setEditingIndices([...result.selected_indices]);
      setDetail((current) => current && "selection" in current && current.id === draftId ? { ...current, selection: result, review: { ...current.review, version: result.review_version } } : current);
      setSelectionNotice(result.changed ? messages.selectionSaved : messages.selectionNoop); setPhase("refreshing-save");
      try { await refreshAfterWrite(draftId, result.selection_version); setPhase("idle"); }
      catch { setPhase("save-refresh-failed"); setSelectionError(messages.selectionRefreshFailed); }
    } catch (error) {
      setSelectionError(writeError(error, locale, "save"));
      setPhase(knownHttp(error) ? ([404, 409, 422].includes((error as ApiClientError).status ?? 0) ? "reload-required" : "idle") : "save-unknown");
    } finally { operationLock.current = false; }
  };

  const validateDecision = (result: Awaited<ReturnType<DraftApi["decide"]>>, request: DecisionRequest, selection: SelectionView, draftId: number) => {
    const expectedStatus = request.decision === "approve" ? "approved" : "rejected";
    const expectedReason = request.decision === "approve" ? null : request.reason.trim();
    return result.draft_id === draftId && result.status === expectedStatus && result.reason === expectedReason && request.expected_version < Number.MAX_SAFE_INTEGER && result.version === request.expected_version + 1 && result.selection_version === selection.selection_version && result.selected_sha256 === selection.selected_sha256 && sameIndices(result.selected_indices, selection.selected_indices);
  };
  const decide = async (request: DecisionRequest) => {
    if (mode !== "api" || operationLock.current || phase !== "idle" || dirty || !savedSelection || !detail || !("selection" in detail) || detail.review.status !== "pending") return;
    if (request.decision === "approve" && savedSelection.selected_indices.length === 0) return;
    const draftId = detail.id; const pinned = savedSelection; const body: DecisionRequest = request.decision === "approve" ? { decision: "approve", expected_version: pinned.review_version } : { decision: "reject", expected_version: pinned.review_version, reason: request.reason.trim() };
    operationLock.current = true; setPhase("deciding"); setSelectionError(null); setSelectionNotice(null);
    try {
      const result = await api.decide(draftId, body, pinned);
      if (!validateDecision(result, body, pinned, draftId)) throw new ApiClientError("service");
      setDecisionSuccess(result.status); setDetail((current) => current && "selection" in current && current.id === draftId ? { ...current, review: { ...current.review, status: result.status, version: result.version, decided_by_subject: result.decided_by_subject, decided_at: result.decided_at, reason: result.reason } } : current);
      try { await refreshAfterWrite(draftId, pinned.selection_version); setPhase("idle"); }
      catch { setPhase("decision-refresh-failed"); setSelectionError(messages.decisionRefreshFailed); }
    } catch (error) {
      setSelectionError(writeError(error, locale, "decision"));
      setPhase(knownHttp(error) ? ([404, 409, 422].includes((error as ApiClientError).status ?? 0) ? "reload-required" : "idle") : "decision-unknown");
    } finally { operationLock.current = false; }
  };

  const recover = async () => {
    if (mode !== "api" || operationLock.current || selectedIdRef.current === null) return;
    const draftId = selectedIdRef.current; operationLock.current = true; setSelectionError(null);
    try {
      const [freshDetail, freshPage] = await Promise.all([api.detail(draftId), api.list()]);
      if (freshDetail.id !== draftId) throw new ApiClientError("service");
      applyDetail(freshDetail); setQueue(freshPage.items); setNextBeforeId(freshPage.next_before_id); setPhase("idle"); setSelectionNotice(null);
    } catch { setSelectionError(safeReadError("detail", locale)); }
    finally { operationLock.current = false; }
  };

  return <div className="app-shell">
    <aside className="sidebar" aria-label={messages.section}><div className="brand-mark" aria-label={messages.product}><span className="brand-glyph" aria-hidden="true">PH</span><span>{messages.product}</span></div><p className="nav-group">{messages.section}</p><div className="nav-active" aria-current="page"><span>{messages.navReview}</span><span className="count-badge">{queue?.length ?? "—"}</span></div><div className="sidebar-state"><strong>{mode === "sample" ? messages.localPreview : messages.liveApi}</strong><span>{mode === "sample" ? messages.sourceState : messages.apiSourceState}</span></div></aside>
    <main className="main-content"><header className="topbar"><span>{messages.section} / {messages.navReview}</span><div className="locale-switch" aria-label={messages.language}><button type="button" aria-pressed={locale === "vi"} onClick={() => setLocale("vi")}>{messages.vietnamese}</button><button type="button" aria-pressed={locale === "en"} onClick={() => setLocale("en")}>{messages.english}</button></div></header>
      <div className="page-content"><div className="page-heading"><div><h1>{messages.pageTitle}</h1><p>{mode === "sample" ? messages.pageDescription : messages.apiPageDescription}</p></div><div className="source-labels"><span className={`tag ${mode === "sample" ? "sample-tag" : "api-tag"}`}>{mode === "sample" ? messages.sampleData : messages.liveData}</span><span>{mode === "sample" ? messages.sourceState : messages.apiSourceState}</span></div></div>
        {queue === null && !queueError && <div className="state-panel" role="status" aria-live="polite"><span className="loading-bar" aria-hidden="true" />{messages.loading}</div>}
        {queueError && <div className="state-panel error-panel" role="alert"><strong>{queueError}</strong><button type="button" onClick={retryQueue}>{messages.retry}</button></div>}
        {queue && queue.length === 0 && !(decisionSuccess && detail) && <div className="state-panel">{mode === "sample" ? messages.emptyQueue : messages.emptyApiQueue}</div>}
        {queue && (queue.length > 0 || (decisionSuccess && detail)) && <div className="workspace-grid"><section className="panel queue-panel" aria-labelledby="queue-title"><header className="panel-header"><h2 id="queue-title">{messages.queueTitle}</h2><span>{queue.length} {messages.loadedDrafts}</span></header><div className="queue-list">{queue.map((draft) => <button type="button" key={draft.id} disabled={navigationLocked} className={`queue-row ${draft.id === selectedId ? "is-selected" : ""}`} aria-pressed={draft.id === selectedId} aria-label={`${messages.draftNumber} ${draft.id}: ${draft.source.name}`} onClick={() => selectDraft(draft.id)}><span className="queue-id">#{draft.id}</span><span className="queue-source">{draft.source.name}</span><span className="queue-meta">{draft.item_count} {messages.items} · {draft.tlp}</span><span className={`queue-status ${draft.injection_warning ? "has-warning" : ""}`}>{draft.injection_warning ? messages.injectionShort : messages.pending}</span></button>)}</div>{nextBeforeId !== null && <button className="load-more" type="button" disabled={loadingMore || navigationLocked} onClick={() => void loadMore()}>{loadingMore ? messages.loadingMore : messages.loadMore}</button>}</section>
          <div className="detail-state">{mode === "api" && selectedId !== null && !detail && !detailError && <div className="state-panel" role="status" aria-live="polite">{messages.detailLoading}</div>}{detailError && <div className="state-panel error-panel" role="alert"><strong>{detailError}</strong><button type="button" onClick={retryDetail}>{messages.retry}</button></div>}{detail && <DraftReview key={detail.id} draft={detail} locale={locale} mode={mode} selection={savedSelection ?? undefined} editingIndices={editingIndices} selectionPhase={phase} selectionError={selectionError} selectionNotice={selectionNotice} decisionSuccess={decisionSuccess} onToggleSelection={toggleSelection} onSaveSelection={saveSelection} onDiscardSelection={discardSelection} onRecover={recover} onDecide={decide} />}</div>
        </div>}
      </div>
    </main>
  </div>;
}
