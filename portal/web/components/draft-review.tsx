"use client";

import { useEffect, useRef, useState } from "react";
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

export function DraftReview({ draft, locale }: { draft: Draft; locale: Locale }) {
  const messages: Messages = locale === "vi" ? vi : en;
  const [activeItem, setActiveItem] = useState<number | null>(null);
  const [kept, setKept] = useState(() => draft.items.map((item) => item.keep));
  const [copiedItem, setCopiedItem] = useState<number | null>(null);
  const [copyErrorItem, setCopyErrorItem] = useState<number | null>(null);
  const evidenceRef = useRef<HTMLElement>(null);
  const activeSpan = activeItem === null ? null : draft.items[activeItem]?.span;

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
        <div><dt>{messages.draftStatus}</dt><dd><span className="tag tag-neutral">{messages.pending}</span></dd></div>
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
            <span>{messages.itemsContext}</span>
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

      <footer className="approval-boundary">
        <div>
          <p>{messages.approvalUnavailable}</p>
          <span>{messages.approvalHelp}</span>
        </div>
        <button type="button" disabled aria-label={messages.approvalUnavailable}>{messages.approvalUnavailable}</button>
      </footer>
    </div>
  );
}
