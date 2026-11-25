"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import type { AssetErrorKind } from "@/data/assets";
import {
  AssetDataError,
  type TechnologyItem,
  type TechnologyProvider,
} from "@/data/technologies";
import en from "@/messages/en.json";
import vi from "@/messages/vi.json";

type Locale = "vi" | "en";
type TechnologyForm = {
  mode: "create" | "edit";
  item?: TechnologyItem;
  vendor: string;
  product: string;
  softwareVersion: string;
  note: string;
};
type Notice = { kind: "error" | "success" | "committed-refresh" | "unknown"; message: string };
type LoadMode = "normal" | "background" | "mutation-refresh" | "committed-retry" | "unknown-reconcile";

function errorKind(error: unknown): AssetErrorKind {
  return error instanceof AssetDataError ? error.kind : "unavailable";
}

function invalidText(value: string, label: string, maximum: number, messages: typeof vi.w04Technology) {
  if (!value.trim()) return messages.validationRequired.replace("{field}", label);
  if (/[\p{Cc}\p{Cf}\p{Cs}]/u.test(value)) return messages.validationCharacters.replace("{field}", label);
  if (Array.from(value.trim()).length > maximum) {
    return messages.validationMaximum.replace("{field}", label).replace("{maximum}", String(maximum));
  }
  return null;
}

function validate(form: TechnologyForm, messages: typeof vi.w04Technology) {
  return invalidText(form.vendor, messages.vendor, 128, messages)
    ?? invalidText(form.product, messages.product, 256, messages)
    ?? invalidText(form.softwareVersion, messages.softwareVersion, 128, messages)
    ?? (Array.from(form.note).length > 500 ? messages.noteMaximum : null);
}

export function TechnologyPanel({
  provider,
  locale,
  active = true,
}: {
  provider: TechnologyProvider;
  locale: Locale;
  active?: boolean;
}) {
  const [items, setItems] = useState<TechnologyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<AssetErrorKind | null>(null);
  const [form, setForm] = useState<TechnologyForm | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<TechnologyItem | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const requestRef = useRef(0);
  const contextRef = useRef(0);
  const activeRef = useRef(active);
  const savingRef = useRef(saving);
  const noticeRef = useRef(notice);
  const wasActiveRef = useRef(active);
  const messages = locale === "vi" ? vi.w04Technology : en.w04Technology;
  const locked = saving || notice?.kind === "unknown";

  useEffect(() => {
    activeRef.current = active;
    savingRef.current = saving;
    noticeRef.current = notice;
  }, [active, notice, saving]);

  const load = useCallback(async (mode: LoadMode = "normal") => {
    const request = ++requestRef.current;
    setLoading(true);
    setLoadError(null);
    if (mode === "normal") setNotice(null);
    try {
      const next = await provider.list();
      if (request !== requestRef.current) return true;
      setItems(next);
      setLoading(false);
      if (mode === "committed-retry" || mode === "unknown-reconcile") setNotice(null);
      return true;
    } catch (error) {
      if (request !== requestRef.current) return false;
      setLoading(false);
      if (mode === "normal") setLoadError(errorKind(error));
      return false;
    }
  }, [provider]);

  useEffect(() => {
    const context = ++contextRef.current;
    queueMicrotask(() => {
      if (context !== contextRef.current) return;
      setItems([]);
      setLoading(true);
      setLoadError(null);
      setForm(null);
      setFormError(null);
      setSaving(false);
      setDeleteTarget(null);
      setNotice(null);
      void load();
    });
    return () => {
      requestRef.current += 1;
      contextRef.current += 1;
    };
  }, [load]);

  useEffect(() => {
    const becameActive = active && !wasActiveRef.current;
    wasActiveRef.current = active;
    if (!becameActive) return;
    queueMicrotask(() => {
      if (!activeRef.current) return;
      if (savingRef.current) {
        void load("background");
      } else if (noticeRef.current?.kind === "unknown") {
        void load("unknown-reconcile");
      }
    });
  }, [active, load]);

  const startCreate = () => {
    if (locked) return;
    setForm({ mode: "create", vendor: "", product: "", softwareVersion: "", note: "" });
    setFormError(null);
    setDeleteTarget(null);
    setNotice(null);
  };

  const startEdit = (item: TechnologyItem) => {
    if (locked) return;
    setForm({
      mode: "edit",
      item,
      vendor: item.vendor,
      product: item.product,
      softwareVersion: item.softwareVersion,
      note: item.note,
    });
    setFormError(null);
    setDeleteTarget(null);
    setNotice(null);
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!form || saving || locked) return;
    const invalid = validate(form, messages);
    if (invalid) {
      setFormError(invalid);
      return;
    }
    setSaving(true);
    const context = contextRef.current;
    setFormError(null);
    setNotice(null);
    const input = {
      vendor: form.vendor,
      product: form.product,
      softwareVersion: form.softwareVersion,
      note: form.note,
    };
    try {
      if (form.mode === "create") {
        await provider.create(input);
      } else {
        await provider.update(form.item!.id, { ...input, expectedVersion: form.item!.version });
      }
      if (context !== contextRef.current) return;
      setForm(null);
      setNotice({ kind: "success", message: messages.saved });
      const refreshed = await load("mutation-refresh");
      if (context !== contextRef.current) return;
      if (!refreshed) setNotice({ kind: "committed-refresh", message: messages.committedRefresh });
    } catch (error) {
      if (context !== contextRef.current) return;
      const kind = errorKind(error);
      if (kind === "conflict") {
        setFormError(messages.conflict);
      } else if (kind === "invalid") {
        setFormError(messages.invalidServer);
      } else if (kind === "unknown-mutation") {
        setForm(null);
        setNotice({ kind: "unknown", message: messages.unknownMutation });
      } else {
        setFormError(messages.errors[kind] ?? messages.errors.unavailable);
      }
    } finally {
      if (context === contextRef.current) setSaving(false);
    }
  };

  const remove = async () => {
    if (!deleteTarget || saving || locked) return;
    setSaving(true);
    const context = contextRef.current;
    setNotice(null);
    try {
      await provider.remove(deleteTarget.id, deleteTarget.version);
      if (context !== contextRef.current) return;
      setDeleteTarget(null);
      setNotice({ kind: "success", message: messages.deleted });
      const refreshed = await load("mutation-refresh");
      if (context !== contextRef.current) return;
      if (!refreshed) setNotice({ kind: "committed-refresh", message: messages.committedRefresh });
    } catch (error) {
      if (context !== contextRef.current) return;
      const kind = errorKind(error);
      setDeleteTarget(null);
      if (kind === "unknown-mutation") {
        setNotice({ kind: "unknown", message: messages.unknownMutation });
      } else if (kind === "conflict") {
        setNotice({ kind: "error", message: messages.conflict });
      } else {
        setNotice({ kind: "error", message: messages.errors[kind] ?? messages.errors.unavailable });
      }
    } finally {
      if (context === contextRef.current) setSaving(false);
    }
  };

  const loadErrorMessage = loadError ? messages.errors[loadError] ?? messages.errors.unavailable : "";

  if (!active) return null;

  return (
    <>
      <header className="assets-app__panel-header">
        <div><h2>{messages.title}</h2><p>{messages.context}</p></div>
        <button className="assets-app__primary" type="button" onClick={startCreate} disabled={saving || locked}>
          {messages.add}
        </button>
      </header>

      {form && (
        <form className="assets-app__form" onSubmit={submit}>
          {([
            ["technology-vendor", "vendor", messages.vendor],
            ["technology-product", "product", messages.product],
            ["technology-software-version", "softwareVersion", messages.softwareVersion],
          ] as const).map(([id, key, label]) => (
            <div className="assets-app__field" key={id}>
              <label htmlFor={id}>{label}</label>
              <input
                id={id}
                autoFocus={key === "vendor"}
                autoComplete="off"
                value={form[key]}
                onChange={(event) => setForm({ ...form, [key]: event.target.value })}
              />
            </div>
          ))}
          <div className="assets-app__field">
            <label htmlFor="technology-note">{messages.note}</label>
            <input id="technology-note" value={form.note} onChange={(event) => setForm({ ...form, note: event.target.value })} />
          </div>
          <div className="assets-app__form-actions">
            <button className="assets-app__primary" type="submit" disabled={saving}>
              {saving ? messages.saving : form.mode === "create" ? messages.save : messages.saveChanges}
            </button>
            <button className="assets-app__secondary" type="button" disabled={saving} onClick={() => setForm(null)}>{messages.cancel}</button>
          </div>
          {formError && <p className="assets-app__form-error" role="alert">{formError}</p>}
        </form>
      )}

      {notice && (
        <div className={`assets-app__notice assets-app__notice--${notice.kind}`} role={notice.kind === "success" ? "status" : "alert"}>
          <p>{notice.message}</p>
          {(notice.kind === "committed-refresh" || notice.kind === "unknown") && (
            <button
              className="assets-app__secondary"
              type="button"
              onClick={() => void load(notice.kind === "unknown" ? "unknown-reconcile" : "committed-retry")}
            >
              {notice.kind === "unknown" ? messages.reconcile : messages.reload}
            </button>
          )}
        </div>
      )}

      {loading && <div className="assets-app__state" role="status"><span className="loading-bar" />{messages.loading}</div>}
      {!loading && loadError && (
        <div className="assets-app__state assets-app__state--error" role="alert">
          <p>{loadErrorMessage}</p>
          {loadError === "unavailable" && <button className="assets-app__secondary" type="button" onClick={() => void load()}>{messages.retry}</button>}
        </div>
      )}
      {!loading && !loadError && items.length === 0 && <p className="assets-app__empty">{messages.empty}</p>}
      {!loading && !loadError && items.length > 0 && (
        <div className="assets-app__table-wrap">
          <table className="assets-app__table">
            <caption className="sr-only">{messages.tableCaption}</caption>
            <thead><tr><th>{messages.vendor}</th><th>{messages.product}</th><th>{messages.softwareVersion}</th><th>{messages.note}</th><th>{messages.recordVersion}</th><th>{messages.actions}</th></tr></thead>
            <tbody>{items.map((item) => {
              const identity = `${item.vendor} ${item.product}`;
              return (
                <tr key={item.id}>
                  <td>{item.vendor}</td>
                  <td>{item.product}</td>
                  <td><code>{item.softwareVersion}</code></td>
                  <td>{item.note || messages.noNote}</td>
                  <td><span className="assets-app__version">v{item.version}</span></td>
                  <td>
                    <div className="assets-app__row-actions">
                      <button type="button" disabled={locked} onClick={() => startEdit(item)} aria-label={`${messages.edit} ${identity}`}>{messages.edit}</button>
                      <button type="button" disabled={locked} onClick={() => { setDeleteTarget(item); setForm(null); }} aria-label={`${messages.delete} ${identity}`}>{messages.delete}</button>
                    </div>
                    {deleteTarget?.id === item.id && (
                      <div className="assets-app__confirm" role="alert">
                        <p>{messages.deleteQuestion} {identity}?</p>
                        <button type="button" disabled={saving} onClick={() => void remove()} aria-label={`${messages.confirmDelete} ${identity}`}>{messages.confirmDelete}</button>
                        <button type="button" disabled={saving} onClick={() => setDeleteTarget(null)}>{messages.cancel}</button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}</tbody>
          </table>
        </div>
      )}
      <footer className="assets-app__boundary">{messages.authority}</footer>
    </>
  );
}
