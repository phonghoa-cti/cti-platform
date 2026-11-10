"use client";

import { useEffect, useRef, useState } from "react";
import type { DecisionRequest, DraftDetail } from "@/data/api-client";
import type { Draft } from "@/data/draft-adapter";
import { defangIoc, getEvidenceSegments } from "@/lib/evidence";
import en from "@/messages/en.json";
import vi from "@/messages/vi.json";

type Locale = "vi" | "en";
type Messages = typeof vi;

function statusLabel(status: string, messages: Messages) {
  if (status === "ok") return messages.statusOk;
  if (status === "allowlist") return messages.statusAllowlist;
  return messages.statusRejected;
}

function reviewLabel(status: "pending" | "approved" | "rejected", messages: Messages) {
  if (status === "approved") return messages.reviewApproved;
  if (status === "rejected") return messages.reviewRejected;
  return messages.reviewPending;
}

export function DraftReview({ draft, locale, mode = "sample", sending = false, decisionBlocked = false, decisionError = null, decisionSuccess = null, onDecide, onReload }: {
  draft: Draft | DraftDetail;
  locale: Locale;
  mode?: "api" | "sample";
  sending?: boolean;
  decisionBlocked?: boolean;
  decisionError?: string | null;
  decisionSuccess?: "approved" | "rejected" | null;
  onDecide?: (request: DecisionRequest) => Promise<void>;
  onReload?: () => void;
}) {
  const messages: Messages = locale === "vi" ? vi : en;
  const [activeItem, setActiveItem] = useState<number | null>(null);
  const [kept, setKept] = useState(() => draft.items.map((item) => item.keep));
  const [copiedItem, setCopiedItem] = useState<number | null>(null);
  const [copyErrorItem, setCopyErrorItem] = useState<number | null>(null);
  const [reason, setReason] = useState("");
  const [reasonError, setReasonError] = useState(false);
  const evidenceRef = useRef<HTMLElement>(null);
  const activeSpan = activeItem === null ? null : draft.items[activeItem]?.span;
  const review = "review" in draft ? draft.review : null;
  const canDecide = mode === "api" && review?.status === "pending" && !sending && !decisionBlocked;

  useEffect(() => {
    if (activeSpan) evidenceRef.current?.focus();
  }, [activeItem, activeSpan]);

  const copyIoc = async (value: string, index: number) => {
    setCopiedItem(null);
    setCopyErrorItem(null);

    if (!navigator.clipboard?.writeText) {
      setCopyErrorItem(index);
      return;
    }

    try {
      await navigator.clipboard.writeText(value);
      setCopiedItem(index);
    } catch {
      setCopyErrorItem(index);
    }
  };

  const sourceBody = () => {
    if (!draft.text) return <p className="empty-state">{messages.emptyText}</p>;
    if (!activeSpan) return <p className="source-copy">{draft.text}</p>;
    const segments = getEvidenceSegments(draft.text, activeSpan);
    return (
      <p className="source-copy">
        {segments.before}
        <mark ref={evidenceRef} tabIndex={-1} className="evidence-highlight">
          {segments.match}
        </mark>
        {segments.after}
      </p>
    );
  };

  return (
    <div className="draft-detail">
      <dl className="metadata-strip">
        <div><dt>{messages.sourceName}</dt><dd>{draft.source.name}</dd></div>
        <div><dt>{messages.tlp}</dt><dd><span className="tag tag-warning">{draft.tlp}</span></dd></div>
        <div><dt>{messages.documentLanguage}</dt><dd>{draft.language.toUpperCase()}</dd></div>
        <div><dt>{messages.model}</dt><dd className="mono">{draft.model}</dd></div>
        <div><dt>{messages.createdAt}</dt><dd className="mono">{new Date(draft.created_at).toLocaleString(locale === "vi" ? "vi-VN" : "en-GB", { timeZone: "Asia/Ho_Chi_Minh" })}</dd></div>
        <div><dt>{messages.draftStatus}</dt><dd><span className="tag tag-neutral">{review ? reviewLabel(review.status, messages) : messages.pending}</span></dd></div>
        <div className="metadata-hash"><dt>{messages.sha256}</dt><dd className="mono">{draft.source.sha256}</dd></div>
        <div><dt>{messages.cost}</dt><dd className="mono">{draft.cost_tokens}</dd></div>
      </dl>

      {draft.injection_warning && (
        <section className="injection-alert" role="alert" aria-labelledby="injection-title">
          <div>
            <h2 id="injection-title">{messages.injectionTitle}</h2>
            <p>{messages.injectionBody}</p>
          </div>
          <ul>
            {draft.findings.map((finding, index) => (
              <li key={`${finding.rule}-${index}`}>
                <span className="mono">{finding.rule}</span> · {messages.findingParagraph} {finding.paragraph}: {finding.excerpt}
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="review-grid">
        <section className="panel source-panel" aria-labelledby="source-title">
          <header className="panel-header">
            <h2 id="source-title">{messages.sourceTitle}</h2>
            <span>{messages.sourceReadOnly}</span>
          </header>
          <div className="source-content">{sourceBody()}</div>
        </section>

        <section className="panel items-panel" aria-labelledby="items-title">
          <header className="panel-header">
            <h2 id="items-title">{messages.itemsTitle}</h2>
            <span>{mode === "api" ? messages.itemsReadOnly : messages.itemsContext}</span>
          </header>
          {draft.items.length === 0 ? (
            <p className="empty-state">{messages.emptyItems}</p>
          ) : (
            <div className="item-list">
              {draft.items.map((item, index) => (
                <article className={`ioc-item status-${item.status}`} key={`${item.type}-${item.value}-${index}`}>
                  <div className="ioc-heading">
                    <label className="keep-control">
                      <input
                        type="checkbox"
                        checked={kept[index]}
                        disabled={mode === "api"}
                        onChange={(event) => setKept((current) => current.map((value, itemIndex) => itemIndex === index ? event.target.checked : value))}
                      />
                      <span>{messages.keepSuggestion}: {kept[index] ? messages.selected : messages.notSelected}</span>
                    </label>
                    <span className={`tag item-status status-${item.status}`}>{statusLabel(item.status, messages)}</span>
                  </div>
                  <div className="ioc-main">
                    <span className="ioc-type">{item.type}</span>
                    <code>{defangIoc(item.value)}</code>
                  </div>
                  {item.warning && <p className="item-warning"><strong>{messages.warning}:</strong> {item.warning}</p>}
                  <div className="item-actions">
                    {item.span ? (
                      <button type="button" className="text-button" onClick={() => setActiveItem(index)}>
                        {messages.focusEvidence}
                      </button>
                    ) : (
                      <span className="no-evidence">{messages.noEvidence}</span>
                    )}
                    <button type="button" className="text-button" onClick={() => void copyIoc(item.value, index)}>
                      {copiedItem === index ? messages.copied : messages.copyOriginal}
                    </button>
                  </div>
                  {copyErrorItem === index && <p role="alert">{messages.copyError}</p>}
                  {copiedItem === index && (
                    <p role="status" aria-label={messages.copied}>{messages.copied}</p>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>
      </div>

      {mode === "sample" ? <footer className="approval-boundary">
        <div><p>{messages.approvalUnavailable}</p><span>{messages.approvalHelp}</span></div>
        <button type="button" disabled aria-label={messages.approvalUnavailable}>{messages.approvalUnavailable}</button>
      </footer> : <footer className="approval-boundary decision-boundary">
        <div className="decision-copy"><p>{messages.localDecisionTitle}</p><span>{messages.localDecisionHelp}</span></div>
        <label className="reason-field"><span>{messages.rejectReason}</span><textarea aria-label={messages.rejectReason} value={reason} disabled={!canDecide} onChange={(event) => { setReason(event.target.value); setReasonError(false); }} /></label>
        <div className="decision-actions">
          <button type="button" disabled={!canDecide} onClick={() => void onDecide?.({ decision: "approve", expected_version: review?.version ?? 0 })}>{sending ? messages.sendingDecision : messages.approveDraft}</button>
          <button className="reject-button" type="button" disabled={!canDecide} onClick={() => {
            const trimmed = reason.trim();
            if (!trimmed) { setReasonError(true); return; }
            void onDecide?.({ decision: "reject", expected_version: review?.version ?? 0, reason: trimmed });
          }}>{sending ? messages.sendingDecision : messages.rejectDraft}</button>
        </div>
        {reasonError && <p className="decision-message error-text" role="alert">{messages.rejectReasonRequired}</p>}
        {decisionError && <p className="decision-message error-text" role="alert">{decisionError}</p>}
        {decisionBlocked && <button className="decision-reload" type="button" onClick={onReload}>{messages.reloadDetail}</button>}
        {decisionSuccess && <p className="decision-message success-text" role="status" aria-live="polite">{decisionSuccess === "approved" ? messages.approvedLocally : messages.rejectedLocally}</p>}
      </footer>}
    </div>
  );
}
