"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { sampleLookupSource, type LookupDataSource, type LookupResponse, type LookupResult } from "@/data/ioc-lookup";
import en from "@/messages/en.json";
import vi from "@/messages/vi.json";

type Locale = "vi" | "en";

function ResultView({ result, messages, onCopy }: {
  result: LookupResult;
  messages: typeof vi.w02;
  onCopy: () => void;
}) {
  const related = [...result.related.techniques, ...result.related.malware, ...result.related.actors];
  const enrichment = [result.enrichment.country, result.enrichment.asn, result.enrichment.detections].filter(Boolean) as string[];
  return (
    <section className="ioc-lookup__result" aria-label={messages.resultRegion} tabIndex={-1}>
      <header className="ioc-lookup__result-header">
        <div>
          <code className="ioc-lookup__display">{result.ioc.display}</code>
          <p className="ioc-lookup__meta">{messages.types[result.ioc.type]} · {result.tlp}</p>
        </div>
        <button className="ioc-lookup__secondary" type="button" onClick={onCopy}>{messages.copy}</button>
      </header>
      <div className="ioc-lookup__badges">
        <span className={result.found ? "ioc-lookup__badge ioc-lookup__badge--found" : "ioc-lookup__badge"}>{result.found ? messages.found : messages.notFound}</span>
        {result.allowlisted && <span className="ioc-lookup__badge ioc-lookup__badge--allowlist">{messages.allowlisted}</span>}
      </div>
      {result.assetMatch?.matched && <AssetMatchView assets={result.assetMatch.assets} messages={messages} />}
      {result.score && (
        <section className={`ioc-lookup__score ioc-lookup__score--${result.score.level}`} aria-label={messages.score}>
          <strong>{result.score.value} / 100</strong>
          <span>{messages.levels[result.score.level]}</span>
          <p>{result.score.reason}</p>
        </section>
      )}
      <div className="ioc-lookup__columns">
        <section><h2>{messages.sources}</h2>{result.sources.length ? <ul>{result.sources.map((item) => <li key={`${item.name}-${item.firstSeen}`}><span>{item.name}</span><time dateTime={item.firstSeen}>{item.firstSeen}</time></li>)}</ul> : <p>{messages.noSources}</p>}</section>
        <section><h2>{messages.related}</h2>{related.length ? <ul>{related.map((item) => <li key={item}>{item}</li>)}</ul> : <p>{messages.noRelated}</p>}</section>
        <section><h2>{messages.enrichment}</h2>{enrichment.length ? <ul>{enrichment.map((item) => <li key={item}>{item}</li>)}</ul> : <p>{messages.noEnrichment}</p>}</section>
      </div>
    </section>
  );
}

function AssetMatchView({ assets, messages }: { assets: string[]; messages: typeof vi.w02 }) {
  return (
    <section className="ioc-lookup__asset" aria-label={messages.assetMatch}>
      <div><strong>{messages.assetMatch}</strong><span>{messages.assetCaution}</span></div>
      <ul>{assets.map((asset) => <li key={asset}><code>{asset}</code></li>)}</ul>
    </section>
  );
}

export function IocLookup({
  dataSource = sampleLookupSource,
  sourceMode = "sample",
}: {
  dataSource?: LookupDataSource;
  sourceMode?: "sample" | "local-api";
}) {
  const [locale, setLocale] = useState<Locale>("vi");
  const [value, setValue] = useState("");
  const [response, setResponse] = useState<LookupResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [copyState, setCopyState] = useState<"success" | "error" | null>(null);
  const requestRef = useRef(0);
  const copyRef = useRef(0);
  const resultRef = useRef<HTMLElement | null>(null);
  const messages = locale === "vi" ? vi.w02 : en.w02;
  const sourceLabel = sourceMode === "local-api" ? messages.localApiLabel : messages.sampleLabel;
  const noSources = sourceMode === "local-api" ? messages.localApiNoSources : messages.noSources;
  const noRelated = sourceMode === "local-api" ? messages.localApiNoRelated : messages.noRelated;
  const noEnrichment = sourceMode === "local-api" ? messages.localApiNoEnrichment : messages.noEnrichment;

  useEffect(() => {
    if (response?.state === "result") resultRef.current?.focus();
  }, [response]);

  useEffect(() => () => {
    copyRef.current += 1;
  }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const request = ++requestRef.current;
    copyRef.current += 1;
    setLoading(true);
    setResponse(null);
    setCopyState(null);
    try {
      const next = await dataSource.lookup(value);
      if (request === requestRef.current) setResponse(next);
    } catch {
      if (request === requestRef.current) setResponse({ state: "unavailable" });
    } finally {
      if (request === requestRef.current) setLoading(false);
    }
  };

  const copy = async () => {
    if (response?.state !== "result") return;
    const request = requestRef.current;
    const copyAttempt = ++copyRef.current;
    const originalValue = response.ioc.value;
    setCopyState(null);
    try {
      if (!navigator.clipboard?.writeText) throw new Error("clipboard unavailable");
      await navigator.clipboard.writeText(originalValue);
      if (request === requestRef.current && copyAttempt === copyRef.current) setCopyState("success");
    } catch {
      if (request === requestRef.current && copyAttempt === copyRef.current) setCopyState("error");
    }
  };

  const stateMessage = response && response.state !== "result" ? messages.states[response.state] : null;
  const stateBody = response?.state === "not-found" && sourceMode === "local-api"
    ? messages.localApiNotFoundBody
    : stateMessage?.body;
  return (
    <main className="ioc-lookup">
      <header className="ioc-lookup__topbar">
        <div><h1>{messages.title}</h1><p>{messages.description}</p></div>
        <div className="ioc-lookup__locale" aria-label={messages.language}>
          <button type="button" aria-pressed={locale === "vi"} onClick={() => setLocale("vi")}>Tiếng Việt</button>
          <button type="button" aria-pressed={locale === "en"} onClick={() => setLocale("en")}>English</button>
        </div>
      </header>
      <p className="ioc-lookup__sample-label">{sourceLabel}</p>
      <form className="ioc-lookup__form" onSubmit={submit}>
        <label htmlFor="ioc-lookup-value">{messages.inputLabel}</label>
        <div className="ioc-lookup__form-row">
          <input id="ioc-lookup-value" value={value} onChange={(event) => setValue(event.target.value)} placeholder={messages.placeholder} autoComplete="off" />
          <button className="ioc-lookup__primary" type="submit">{loading ? messages.loadingButton : messages.submit}</button>
        </div>
        <p>{messages.hint}</p>
      </form>
      <div className="ioc-lookup__live" aria-live="polite">
        {loading && <p role="status">{messages.loading}</p>}
        {copyState === "success" && <p role="status">{messages.copySuccess}</p>}
        {copyState === "error" && <p role="alert">{messages.copyError}</p>}
      </div>
      {stateMessage && <section className="ioc-lookup__state" role="alert"><h2>{stateMessage.title}</h2><p>{stateBody}</p></section>}
      {response?.state === "not-found" && response.assetMatch?.matched && (
        <div className="ioc-lookup__not-found-asset">
          <h2>{messages.noThreatData}</h2>
          <AssetMatchView assets={response.assetMatch.assets} messages={messages} />
        </div>
      )}
      {response?.state === "result" && (
        <div ref={(node) => { resultRef.current = node?.querySelector("section") ?? null; }}>
          <ResultView
            result={response}
            messages={{ ...messages, noSources, noRelated, noEnrichment }}
            onCopy={copy}
          />
        </div>
      )}
    </main>
  );
}
