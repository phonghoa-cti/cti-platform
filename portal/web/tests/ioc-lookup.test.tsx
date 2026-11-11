import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { IocLookup } from "@/components/ioc-lookup";
import {
  sampleLookupSource,
  type LookupDataSource,
  type LookupResponse,
} from "@/data/ioc-lookup";

const found: LookupResponse = {
  state: "result",
  input: "hxxp://Evil[.]COM/a",
  ioc: {
    type: "url",
    value: "http://evil.com/a",
    display: "hxxp://evil[.]com/a",
  },
  found: true,
  allowlisted: false,
  score: { value: 78, level: "high", reason: "Nguồn tổng hợp xác nhận IOC trong fixture." },
  sources: [{ name: "Nguồn CTI tổng hợp", firstSeen: "2026-10-20T08:00:00+07:00" }],
  related: { techniques: ["T1566.001"], malware: ["Họ mã độc mẫu"], actors: [] },
  enrichment: { country: "NL", asn: "AS64500", detections: "12/90" },
  tlp: "TLP:GREEN",
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((done, fail) => { resolve = done; reject = fail; });
  return { promise, resolve, reject };
}

function source(lookup: LookupDataSource["lookup"]): LookupDataSource {
  return { lookup };
}

async function submit(value: string, dataSource: LookupDataSource) {
  const user = userEvent.setup();
  render(<IocLookup dataSource={dataSource} />);
  await user.click(screen.getByRole("textbox", { name: "IOC cần tra cứu" }));
  await user.paste(value);
  await user.click(screen.getByRole("button", { name: "Tra cứu" }));
  return user;
}

describe("IOC lookup interaction", () => {
  it("starts idle, sends one exact value, and announces loading", async () => {
    const pending = deferred<LookupResponse>();
    const lookup = vi.fn().mockReturnValue(pending.promise);
    await submit("  hxxp://Evil[.]COM/a  ", source(lookup));

    expect(lookup).toHaveBeenCalledWith("  hxxp://Evil[.]COM/a  ");
    expect(screen.getByRole("status")).toHaveTextContent("Đang tra cứu");
    expect(screen.getByRole("button", { name: "Đang tra cứu…" })).toBeEnabled();
  });

  it("renders API-provided result fields as text without recalculating them", async () => {
    await submit(found.input, source(vi.fn().mockResolvedValue(found)));

    expect(await screen.findByRole("region", { name: "Kết quả tra cứu" })).toHaveFocus();
    expect(screen.getByText(found.ioc.display)).toBeInTheDocument();
    expect(screen.getByText("78 / 100")).toBeInTheDocument();
    expect(screen.getByText(found.score!.reason)).toBeInTheDocument();
    expect(screen.getByText("Nguồn CTI tổng hợp")).toBeInTheDocument();
    expect(screen.getByText("T1566.001")).toBeInTheDocument();
    expect(screen.getByText("NL")).toBeInTheDocument();
    expect(screen.getByText(/TLP:GREEN/)).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it.each([
    ["not-found", "Chưa có nguồn nào báo IOC này"],
    ["invalid", "Không phải IOC hợp lệ"],
    ["private-ip", "Đây là IP nội bộ"],
    ["unavailable", "Tạm thời không thể tra cứu"],
    ["forbidden", "Bạn không có quyền xem kết quả này"],
  ] as const)("renders the %s state without presenting it as safe", async (state, message) => {
    await submit("unknown.example", source(vi.fn().mockResolvedValue({ state })));

    expect(await screen.findByRole("alert")).toHaveTextContent(message);
    expect(screen.queryByText("Thấp")).not.toBeInTheDocument();
    expect(screen.queryByText(/0 \/ 100/)).not.toBeInTheDocument();
  });

  it("ignores an older response that resolves after a newer lookup", async () => {
    const first = deferred<LookupResponse>();
    const second = deferred<LookupResponse>();
    const lookup = vi.fn()
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise);
    const user = userEvent.setup();
    render(<IocLookup dataSource={source(lookup)} />);
    const input = screen.getByRole("textbox", { name: "IOC cần tra cứu" });

    await user.type(input, "a.example");
    await user.click(screen.getByRole("button", { name: "Tra cứu" }));
    await user.clear(input);
    await user.type(input, "b.example");
    await user.click(screen.getByRole("button", { name: "Đang tra cứu…" }));
    second.resolve({ ...found, input: "b.example", ioc: { ...found.ioc, value: "b.example", display: "b[.]example" } });
    expect(await screen.findByText("b[.]example")).toBeInTheDocument();
    first.resolve({ ...found, input: "a.example", ioc: { ...found.ioc, value: "a.example", display: "a[.]example" } });

    await waitFor(() => expect(screen.getByText("b[.]example")).toBeInTheDocument());
    expect(screen.queryByText("a[.]example")).not.toBeInTheDocument();
  });

  it("clears an earlier result while a new request fails", async () => {
    const lookup = vi.fn()
      .mockResolvedValueOnce(found)
      .mockRejectedValueOnce(new Error("offline"));
    const user = userEvent.setup();
    render(<IocLookup dataSource={source(lookup)} />);
    const input = screen.getByRole("textbox", { name: "IOC cần tra cứu" });
    await user.click(input);
    await user.paste(found.input);
    await user.click(screen.getByRole("button", { name: "Tra cứu" }));
    expect(await screen.findByText(found.ioc.display)).toBeInTheDocument();

    await user.clear(input);
    await user.type(input, "other.example");
    await user.click(screen.getByRole("button", { name: "Tra cứu" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Tạm thời không thể tra cứu");
    expect(screen.queryByText(found.ioc.display)).not.toBeInTheDocument();
  });

  it("copies the exact original value only after the clipboard Promise succeeds", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    const user = await submit(found.input, source(vi.fn().mockResolvedValue(found)));
    const copy = await screen.findByRole("button", { name: "Sao chép giá trị gốc" });
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText } });
    await user.click(copy);

    expect(writeText).toHaveBeenCalledWith("http://evil.com/a");
    expect(screen.getByRole("status")).toHaveTextContent("Đã sao chép giá trị gốc");
  });

  it.each(["missing", "rejected"] as const)("reports copy failure when clipboard is %s", async (mode) => {
    const user = await submit(found.input, source(vi.fn().mockResolvedValue(found)));
    const copy = await screen.findByRole("button", { name: "Sao chép giá trị gốc" });
    if (mode === "missing") Object.defineProperty(navigator, "clipboard", { configurable: true, value: undefined });
    else Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: vi.fn().mockRejectedValue(new Error("denied")) } });
    await user.click(copy);

    expect(await screen.findByRole("alert")).toHaveTextContent("Không thể sao chép");
  });

  it("switches all lookup controls to English without issuing another lookup", async () => {
    const lookup = vi.fn().mockResolvedValue({ state: "not-found" });
    const user = await submit("unknown.example", source(lookup));
    await screen.findByText("Chưa có nguồn nào báo IOC này");
    await user.click(screen.getByRole("button", { name: "English" }));

    expect(screen.getByRole("heading", { name: "Look up one IOC" })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "IOC to look up" })).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("No source has reported this IOC");
    expect(lookup).toHaveBeenCalledTimes(1);
  });
});

describe("offline sample data source", () => {
  it("returns the declared fixture and treats every unmatched query as not found without network", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    const known = await sampleLookupSource.lookup("hxxp://Evil[.]COM/a");
    const unknown = await sampleLookupSource.lookup("unlisted.example");

    expect(known).toMatchObject({ state: "result", found: true, allowlisted: false });
    expect(unknown).toEqual({ state: "not-found" });
    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });
});
