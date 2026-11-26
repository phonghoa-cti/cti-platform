import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { OverviewApp } from "@/components/overview-app";
import { createSampleCveProvider, CveDataError } from "@/data/cves";
import { createCvesHttpProvider } from "@/data/cves-http";
import summaryFixture from "./fixtures/w03-summary.json";

describe("W01 overview (read only)", () => {
  it("uses existing sample records and labels fixture scope", async () => {
    render(<OverviewApp mode="sample" provider={createSampleCveProvider()} />);
    expect(await within(screen.getByRole("heading", { name: "CVE ưu tiên" }).closest("section")!).findByText("CVE-2026-0001")).toBeInTheDocument();
    expect(screen.getByText(/Dữ liệu mẫu/)).toBeInTheDocument();
    expect(within(screen.getByRole("region", { name: "IOC khớp tài sản" })).queryByText("hxxps://found[.]congty[.]vn/path")).toBeInTheDocument();
    expect(screen.queryByText("mail[.]congty[.]vn")).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Tình trạng nguồn dữ liệu" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Đã xử lý/ })).not.toBeInTheDocument();
  });

  it("API mode uses GET only, respects the leader projection and never substitutes sample IOC", async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify(summaryFixture), {
      status: 200, headers: { "Content-Type": "application/json" },
    }));
    render(<OverviewApp mode="api" provider={createCvesHttpProvider({ fetcher })} />);
    expect(await within(screen.getByRole("heading", { name: "CVE ưu tiên" }).closest("section")!).findByText("CVE-2026-1001")).toBeInTheDocument();
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(fetcher).toHaveBeenCalledWith(expect.stringMatching(/^\/api\/cves\?/), expect.objectContaining({ method: "GET", credentials: "same-origin" }));
    expect(screen.queryByText("hxxps://found[.]congty[.]vn/path")).not.toBeInTheDocument();
    expect(screen.queryByText("Fortinet")).not.toBeInTheDocument();
    expect(screen.getAllByText(/Chưa có nguồn/).length).toBeGreaterThan(0);
  });

  it("distinguishes an unavailable CVE panel from a valid empty result and retries GET", async () => {
    const sample = createSampleCveProvider();
    const empty = await sample.list({ kev: false, q: "no match", technologyId: null, limit: 10, cursor: null });
    const provider = { list: vi.fn().mockRejectedValueOnce(new CveDataError("unavailable")).mockResolvedValue(empty) };
    render(<OverviewApp mode="api" provider={provider} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Không tải được dữ liệu CVE");
    await userEvent.click(screen.getByRole("button", { name: "Làm mới" }));
    expect(await screen.findByText("Không có CVE liên quan trong dữ liệu trả về.")).toBeInTheDocument();
    await waitFor(() => expect(provider.list).toHaveBeenCalledTimes(2));
    await userEvent.click(screen.getByRole("button", { name: "English" }));
    expect(screen.getByRole("heading", { name: "Overview" })).toBeInTheDocument();
  });
});
