"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import {
  AssetDataError,
  createSampleAssetsDataSource,
  type AssetDataSource,
  type AssetErrorKind,
  type AssetItem,
  type AssetType,
} from "@/data/assets";
import type { TechnologyProvider } from "@/data/technologies";
import { TechnologyPanel } from "@/components/technology-panel";
import en from "@/messages/en.json";
import vi from "@/messages/vi.json";

type Locale = "vi" | "en";
type FormState = { mode: "create" | "edit"; item?: AssetItem; value: string; note: string };
type Notice = { kind: "error" | "success" | "committed-refresh" | "unknown"; message: string };

function errorKind(error: unknown): AssetErrorKind {
  return error instanceof AssetDataError ? error.kind : "unavailable";
}

function validate(type: AssetType, value: string, messages: typeof vi.w04) {
  if (!value.trim()) return messages.validationRequired;
  if (type === "domain") {
    if (/[:/@*\s]/.test(value) || value.includes("/") || !value.replace(/\.$/, "").includes(".")) {
      return messages.validationDomain;
    }
  } else if (!/^\S+\/\d+$/.test(value)) {
    return messages.validationCidr;
  }
  return null;
}

export function AssetsApp({
  dataSource,
  sourceMode = "sample",
  technologyProvider,
}: {
  dataSource?: AssetDataSource;
  sourceMode?: "sample" | "local-api";
  technologyProvider?: TechnologyProvider;
}) {
  const [sampleSource] = useState(createSampleAssetsDataSource);
  const source = dataSource ?? sampleSource;
  const [locale, setLocale] = useState<Locale>("vi");
  const [type, setType] = useState<AssetType>("domain");
  const [technologyActive, setTechnologyActive] = useState(false);
  const [items, setItems] = useState<AssetItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<AssetErrorKind | null>(null);
  const [form, setForm] = useState<FormState | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<AssetItem | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const requestRef = useRef(0);
  const contextRef = useRef(0);
  const messages = locale === "vi" ? vi.w04 : en.w04;
  const technologyVisible = technologyActive && technologyProvider !== undefined;

  const load = useCallback(async (selectedType: AssetType, preserveCommitted = false) => {
    const request = ++requestRef.current;
    setLoading(true);
    setLoadError(null);
    if (!preserveCommitted) setNotice(null);
    try {
      const next = await source.list(selectedType);
      if (request !== requestRef.current) return true;
      setItems(next);
      setLoading(false);
      return true;
    } catch (error) {
      if (request !== requestRef.current) return false;
      setLoading(false);
      if (!preserveCommitted) {
        setLoadError(errorKind(error));
      }
      return false;
    }
  }, [source]);

  useEffect(() => {
    queueMicrotask(() => void load(type));
    return () => {
      requestRef.current += 1;
      contextRef.current += 1;
    };
  }, [load, type]);

  const switchType = (next: AssetType) => {
    if (next === type && !technologyActive) return;
    const reloadCurrentType = next === type && technologyActive;
    requestRef.current += 1;
    contextRef.current += 1;
    setTechnologyActive(false);
    setType(next);
    setItems([]);
    setLoading(true);
    setLoadError(null);
    setForm(null);
    setDeleteTarget(null);
    setNotice(null);
    setSaving(false);
    if (reloadCurrentType) queueMicrotask(() => void load(next));
  };

  const switchTechnology = () => {
    if (technologyActive || !technologyProvider) return;
    requestRef.current += 1;
    contextRef.current += 1;
    setTechnologyActive(true);
    setForm(null);
    setDeleteTarget(null);
    setNotice(null);
    setSaving(false);
  };

  const startCreate = () => {
    setForm({ mode: "create", value: "", note: "" });
    setFormError(null);
    setDeleteTarget(null);
    setNotice(null);
  };

  const startEdit = (item: AssetItem) => {
    setForm({ mode: "edit", item, value: item.value, note: item.note });
    setFormError(null);
    setDeleteTarget(null);
    setNotice(null);
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!form || saving) return;
    const invalid = validate(type, form.value, messages);
    if (invalid) {
      setFormError(invalid);
      return;
    }
    setSaving(true);
    const context = contextRef.current;
    setFormError(null);
    setNotice(null);
    try {
      if (form.mode === "create") {
        await source.create({ type, value: form.value, note: form.note });
      } else {
        await source.update(form.item!.id, {
          type,
          value: form.value,
          note: form.note,
          expectedVersion: form.item!.version,
        });
      }
      if (context !== contextRef.current) return;
      setForm(null);
      setNotice({ kind: "success", message: messages.saved });
      const refreshed = await load(type, true);
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
    if (!deleteTarget || saving) return;
    setSaving(true);
    const context = contextRef.current;
    setNotice(null);
    try {
      await source.remove(deleteTarget.id, deleteTarget.version);
      if (context !== contextRef.current) return;
      setDeleteTarget(null);
      setNotice({ kind: "success", message: messages.deleted });
      const refreshed = await load(type, true);
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

  const typeLabel = type === "domain" ? messages.domain : messages.ipRange;
  const empty = type === "domain" ? messages.emptyDomain : messages.emptyIpRange;
  const loadErrorMessage = loadError ? messages.errors[loadError] ?? messages.errors.unavailable : "";

  return (
    <main className="assets-app">
      <header className="assets-app__topbar">
        <div>
          <h1>{messages.title}</h1>
          <p>{messages.description}</p>
        </div>
        <div className="assets-app__locale" aria-label={messages.language}>
          <button type="button" aria-pressed={locale === "vi"} onClick={() => setLocale("vi")}>Tiếng Việt</button>
          <button type="button" aria-pressed={locale === "en"} onClick={() => setLocale("en")}>English</button>
        </div>
      </header>
      <p className="assets-app__sample-label">
        {sourceMode === "sample" ? messages.sampleLabel : messages.apiLabel}
      </p>

      <section className="assets-app__workspace" aria-label={messages.workspace}>
        <div className="assets-app__tabs" role="tablist" aria-label={messages.assetTypes}>
          <button type="button" role="tab" aria-selected={!technologyVisible && type === "domain"} onClick={() => switchType("domain")}>{messages.domain}</button>
          <button type="button" role="tab" aria-selected={!technologyVisible && type === "ip_range"} onClick={() => switchType("ip_range")}>{messages.ipRange}</button>
          {technologyProvider && (
            <button type="button" role="tab" aria-selected={technologyActive} onClick={switchTechnology}>
              {locale === "vi" ? vi.w04Technology.title : en.w04Technology.title}
            </button>
          )}
        </div>

        {technologyVisible && <TechnologyPanel provider={technologyProvider} locale={locale} />}
        {!technologyVisible && <>
        <header className="assets-app__panel-header">
          <div><h2>{typeLabel}</h2><p>{messages.context}</p></div>
          <button className="assets-app__primary" type="button" onClick={startCreate} disabled={saving}>
            {type === "domain" ? messages.addDomain : messages.addIpRange}
          </button>
        </header>

        {form && (
          <form className="assets-app__form" onSubmit={submit}>
            <div className="assets-app__field">
              <label htmlFor="asset-value">{typeLabel}</label>
              <input
                id="asset-value"
                autoFocus
                autoComplete="off"
                value={form.value}
                onChange={(event) => setForm({ ...form, value: event.target.value })}
              />
              <span>{type === "domain" ? messages.domainHelp : messages.cidrHelp}</span>
            </div>
            <div className="assets-app__field">
              <label htmlFor="asset-note">{messages.note}</label>
              <input id="asset-note" maxLength={500} value={form.note} onChange={(event) => setForm({ ...form, note: event.target.value })} />
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
              <button className="assets-app__secondary" type="button" onClick={() => void load(type)}>{messages.reload}</button>
            )}
          </div>
        )}

        {loading && <div className="assets-app__state" role="status"><span className="loading-bar" />{messages.loading}</div>}
        {!loading && loadError && (
          <div className="assets-app__state assets-app__state--error" role="alert">
            <p>{loadErrorMessage}</p>
            {loadError === "unavailable" && <button className="assets-app__secondary" type="button" onClick={() => void load(type)}>{messages.retry}</button>}
          </div>
        )}
        {!loading && !loadError && items.length === 0 && <p className="assets-app__empty">{empty}</p>}
        {!loading && !loadError && items.length > 0 && (
          <div className="assets-app__table-wrap">
            <table className="assets-app__table">
              <caption className="sr-only">{messages.tableCaption} {typeLabel}</caption>
              <thead><tr><th>{typeLabel}</th><th>{messages.note}</th><th>{messages.version}</th><th>{messages.actions}</th></tr></thead>
              <tbody>{items.map((item) => (
                <tr key={item.id}>
                  <td><code>{item.value}</code></td>
                  <td>{item.note || messages.noNote}</td>
                  <td><span className="assets-app__version">v{item.version}</span></td>
                  <td>
                    <div className="assets-app__row-actions">
                      <button type="button" onClick={() => startEdit(item)} aria-label={`${messages.edit} ${item.value}`}>{messages.edit}</button>
                      <button type="button" onClick={() => { setDeleteTarget(item); setForm(null); }} aria-label={`${messages.delete} ${item.value}`}>{messages.delete}</button>
                    </div>
                    {deleteTarget?.id === item.id && (
                      <div className="assets-app__confirm" role="alert">
                        <p>{messages.deleteQuestion} {item.value}?</p>
                        <button type="button" disabled={saving} onClick={() => void remove()} aria-label={`${messages.confirmDelete} ${item.value}`}>{messages.confirmDelete}</button>
                        <button type="button" disabled={saving} onClick={() => setDeleteTarget(null)}>{messages.cancel}</button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
        <footer className="assets-app__boundary">{messages.authority}</footer>
        </>}
      </section>
    </main>
  );
}
