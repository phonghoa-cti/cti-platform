"use client";

import { useEffect, useRef, useState } from "react";
import { AssetDataError, type AssetDataSource } from "@/data/assets";
import type { TechnologyProvider } from "@/data/technologies";
import { assetsCsv, downloadCsv } from "@/lib/assets-csv";
import vi from "@/messages/vi.json";
import en from "@/messages/en.json";

export function AssetsCsvButton({ source, technologies, locale, sample }: {
  source: AssetDataSource;
  technologies: TechnologyProvider;
  locale: "vi" | "en";
  sample: boolean;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<AssetDataError["kind"] | null>(null);
  const request = useRef(0);
  const locked = useRef(false);
  const messages = locale === "vi" ? vi.w04 : en.w04;
  useEffect(() => () => { request.current += 1; locked.current = false; }, [source, technologies]);

  async function exportAll() {
    if (locked.current) return;
    locked.current = true;
    const current = ++request.current;
    setBusy(true);
    setError(null);
    try {
      // Không dùng hàng đang hiển thị (có thể cũ); đọc đủ ba nhóm qua quyền API hiện có.
      const [domains, ranges, software] = await Promise.all([
        source.list("domain"), source.list("ip_range"), technologies.list(),
      ]);
      if (request.current !== current) return;
      downloadCsv(assetsCsv([...domains, ...ranges], software), sample ? "phonghoa-assets-sample.csv" : "phonghoa-assets.csv");
    } catch (cause) {
      if (request.current === current) setError(cause instanceof AssetDataError ? cause.kind : "unavailable");
    } finally {
      if (request.current === current) {
        locked.current = false;
        setBusy(false);
      }
    }
  }

  return <div className="assets-csv-export">
    <button type="button" className="assets-app__secondary" disabled={busy} onClick={() => void exportAll()}>
      {locale === "vi" ? (busy ? "Đang xuất CSV…" : "Xuất CSV tài sản và công nghệ") : (busy ? "Exporting CSV…" : "Export assets and technologies CSV")}
    </button>
    {error && <p role="alert" className="assets-app__form-error">{locale === "vi" ? "Không xuất CSV: " : "CSV export failed: "}{messages.errors[error] ?? messages.errors.unavailable}</p>}
  </div>;
}
