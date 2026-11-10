"use client";

import { useEffect, useState } from "react";
import { DraftReview } from "@/components/draft-review";
import { loadFixtureDrafts, type Draft } from "@/data/draft-adapter";
import en from "@/messages/en.json";
import vi from "@/messages/vi.json";

type Locale = "vi" | "en";
type Loader = () => Promise<Draft[]>;

export function DraftReviewApp({ loadDrafts = loadFixtureDrafts }: { loadDrafts?: Loader }) {
  const [locale, setLocale] = useState<Locale>("vi");
  const [drafts, setDrafts] = useState<Draft[] | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const messages = locale === "vi" ? vi : en;

  useEffect(() => {
    let active = true;
    loadDrafts()
      .then((result) => {
        if (!active) return;
        setDrafts(result);
        setSelectedId(result[0]?.id ?? null);
      })
      .catch((caught: unknown) => {
        if (active) setError(caught instanceof Error ? caught.message : "unknown");
      });
    return () => { active = false; };
  }, [loadDrafts, attempt]);

  const retry = () => {
    setError(null);
    setDrafts(null);
    setAttempt((value) => value + 1);
  };

  const selected = drafts?.find((draft) => draft.id === selectedId) ?? null;

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label={messages.section}>
        <div className="brand-mark" aria-label={messages.product}>
          <span className="brand-glyph" aria-hidden="true">PH</span>
          <span>{messages.product}</span>
        </div>
        <p className="nav-group">{messages.section}</p>
        <div className="nav-active" aria-current="page">
          <span>{messages.navReview}</span>
          <span className="count-badge">{drafts?.length ?? "—"}</span>
        </div>
        <div className="sidebar-state">
          <strong>{messages.localPreview}</strong>
          <span>{messages.sourceState}</span>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <span>{messages.section} / {messages.navReview}</span>
          <div className="locale-switch" aria-label={messages.language}>
            <button type="button" aria-pressed={locale === "vi"} onClick={() => setLocale("vi")}>{messages.vietnamese}</button>
            <button type="button" aria-pressed={locale === "en"} onClick={() => setLocale("en")}>{messages.english}</button>
          </div>
        </header>

        <div className="page-content">
          <div className="page-heading">
            <div>
              <h1>{messages.pageTitle}</h1>
              <p>{messages.pageDescription}</p>
            </div>
            <div className="source-labels">
              <span className="tag sample-tag">{messages.sampleData}</span>
              <span>{messages.sourceState}</span>
            </div>
          </div>

          {drafts === null && !error && (
            <div className="state-panel" role="status" aria-live="polite">
              <span className="loading-bar" aria-hidden="true" />
              {messages.loading}
            </div>
          )}

          {error && (
            <div className="state-panel error-panel" role="alert">
              <strong>{messages.loadError}</strong>
              <code>{error}</code>
              <button type="button" onClick={retry}>{messages.retry}</button>
            </div>
          )}

          {drafts && drafts.length === 0 && <div className="state-panel">{messages.emptyQueue}</div>}

          {drafts && drafts.length > 0 && selected && (
            <div className="workspace-grid">
              <section className="panel queue-panel" aria-labelledby="queue-title">
                <header className="panel-header">
                  <h2 id="queue-title">{messages.queueTitle}</h2>
                  <span>{messages.queueContext}</span>
                </header>
                <div className="queue-list">
                  {drafts.map((draft) => (
                    <button
                      type="button"
                      key={draft.id}
                      className={`queue-row ${draft.id === selectedId ? "is-selected" : ""}`}
                      aria-pressed={draft.id === selectedId}
                      aria-label={`${messages.draftNumber} ${draft.id}: ${draft.source.name}`}
                      onClick={() => setSelectedId(draft.id)}
                    >
                      <span className="queue-id">#{draft.id}</span>
                      <span className="queue-source">{draft.source.name}</span>
                      <span className="queue-meta">{draft.items.length} {messages.items} · {draft.tlp}</span>
                      <span className={`queue-status ${draft.injection_warning ? "has-warning" : ""}`}>
                        {draft.injection_warning ? messages.injectionShort : messages.pending}
                      </span>
                    </button>
                  ))}
                </div>
              </section>
              <DraftReview key={selected.id} draft={selected} locale={locale} />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
