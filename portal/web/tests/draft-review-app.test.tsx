import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DraftReviewApp } from "@/components/draft-review-app";
import { ApiClientError, parseDraftDetail, type DraftApi } from "@/data/api-client";
import { parseDraftQueue } from "@/data/draft-adapter";
import regular from "@/data/fixtures/01-regular.json";
import empty from "@/data/fixtures/03-empty.json";

const pendingDetail = parseDraftDetail({
  ...regular,
  review: { status: "pending", version: 0, created_by_subject: "author-sub", decided_by_subject: null, decided_at: null, reason: null },
});
const summary = {
  id: regular.id,
  created_at: regular.created_at,
  status: "pending" as const,
  source: regular.source,
  language: regular.language as "vi",
  tlp: regular.tlp as "TLP:AMBER",
  item_count: regular.items.length,
  injection_warning: regular.injection_warning,
  review_status: "pending" as const,
  review_version: 0 as const,
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

function api(overrides: Partial<DraftApi> = {}): DraftApi {
  return {
    list: vi.fn().mockResolvedValue({ items: [summary], next_before_id: null }),
    detail: vi.fn().mockResolvedValue(pendingDetail),
    decide: vi.fn(),
    ...overrides,
  };
}

describe("draft review application states", () => {
  it("announces loading while the fixture adapter is pending", () => {
    render(<DraftReviewApp mode="sample" loadDrafts={() => new Promise(() => undefined)} />);
    expect(screen.getByRole("status")).toHaveTextContent("Đang tải bản nháp");
  });

  it("shows a valid empty queue as empty, not as an error", async () => {
    render(<DraftReviewApp mode="sample" loadDrafts={async () => []} />);
    expect(await screen.findByText("Chưa có bản nháp trong hàng đợi mẫu.")).toBeInTheDocument();
  });

  it("shows adapter failures as errors instead of an empty queue", async () => {
    render(<DraftReviewApp mode="sample" loadDrafts={async () => { throw new Error("invalid fixture"); }} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Không tải được hàng đợi");
  });

  it("switches drafts and changes the interface language", async () => {
    const user = userEvent.setup();
    const drafts = parseDraftQueue([regular, empty]);
    render(<DraftReviewApp mode="sample" loadDrafts={async () => drafts} />);

    await user.click(await screen.findByRole("button", { name: /synthetic-regular\.txt/i }));
    expect(screen.getByRole("region", { name: "Văn bản nguồn" })).toHaveTextContent(
      "😀 Báo cáo tiếng Việt: ghi nhận kết nối tới evil[.]example.",
    );

    await user.click(screen.getByRole("button", { name: "English" }));
    await waitFor(() => expect(screen.getByRole("heading", { name: "Draft review queue" })).toBeInTheDocument());
  });

  it("loads API queue pages and counts only loaded rows", async () => {
    const user = userEvent.setup();
    const second = { ...summary, id: 2, source: { ...summary.source, name: "second.txt" } };
    const draftApi = api({
      list: vi.fn()
        .mockResolvedValueOnce({ items: [summary], next_before_id: 2 })
        .mockResolvedValueOnce({ items: [second], next_before_id: null }),
    });
    render(<DraftReviewApp mode="api" api={draftApi} />);

    expect(await screen.findByText("1 bản nháp đã tải")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Tải thêm" }));
    expect(await screen.findByText("2 bản nháp đã tải")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Tải thêm" })).not.toBeInTheDocument();
  });

  it("shows detail loading separately and ignores a stale response after selecting another row", async () => {
    const user = userEvent.setup();
    const oldDetail = deferred<typeof pendingDetail>();
    const selectedDetail = { ...pendingDetail, id: 2, source: { ...pendingDetail.source, name: "selected.txt" } };
    const draftApi = api({
      list: vi.fn().mockResolvedValue({ items: [summary, { ...summary, id: 2, source: { ...summary.source, name: "selected.txt" } }], next_before_id: null }),
      detail: vi.fn((id: number) => id === regular.id ? oldDetail.promise : Promise.resolve(selectedDetail)),
    });
    render(<DraftReviewApp mode="api" api={draftApi} />);

    expect(await screen.findByText("Đang tải chi tiết…")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /selected\.txt/i }));
    expect(await screen.findByText("selected.txt", { selector: "dd" })).toBeInTheDocument();
    oldDetail.resolve(pendingDetail);
    await waitFor(() => expect(screen.getByText("selected.txt", { selector: "dd" })).toBeInTheDocument());
  });

  it("submits approve once with detail version and refreshes queue and detail", async () => {
    const user = userEvent.setup();
    const draftApi = api({
      decide: vi.fn().mockResolvedValue({ draft_id: regular.id, status: "approved", version: 1, decided_by_subject: "analyst-sub", decided_at: "2026-11-11T01:02:03+00:00", reason: null }),
    });
    render(<DraftReviewApp mode="api" api={draftApi} />);
    const approve = await screen.findByRole("button", { name: "Duyệt bản nháp" });

    await Promise.all([user.click(approve), user.click(approve)]);

    expect(draftApi.decide).toHaveBeenCalledTimes(1);
    expect(draftApi.decide).toHaveBeenCalledWith(regular.id, { decision: "approve", expected_version: 0 });
    expect(await screen.findByRole("status")).toHaveTextContent("đã được duyệt cục bộ");
    expect(draftApi.list).toHaveBeenCalledTimes(2);
    expect(draftApi.detail).toHaveBeenCalledTimes(2);
  });

  it("keeps the decided draft selected while its decision and refresh are in flight", async () => {
    const user = userEvent.setup();
    const decision = deferred<{ draft_id: number; status: "approved"; version: 1; decided_by_subject: string; decided_at: string; reason: null }>();
    const secondSummary = { ...summary, id: 2, source: { ...summary.source, name: "second.txt" } };
    const secondDetail = { ...pendingDetail, id: 2, source: { ...pendingDetail.source, name: "second.txt" } };
    const approvedFirst = {
      ...pendingDetail,
      review: { ...pendingDetail.review, status: "approved" as const, version: 1, decided_by_subject: "analyst-sub", decided_at: "2026-11-11T01:02:03+00:00" },
    };
    const detail = vi.fn((id: number) => Promise.resolve(id === 2 ? secondDetail : detail.mock.calls.length > 1 ? approvedFirst : pendingDetail));
    const draftApi = api({
      list: vi.fn().mockResolvedValue({ items: [summary, secondSummary], next_before_id: 2 }),
      detail,
      decide: vi.fn().mockReturnValue(decision.promise),
    });
    render(<DraftReviewApp mode="api" api={draftApi} />);
    await screen.findByRole("button", { name: "Duyệt bản nháp" });

    await user.click(screen.getByRole("button", { name: "Duyệt bản nháp" }));
    const secondRow = screen.getByRole("button", { name: /second\.txt/i });
    expect(secondRow).toBeDisabled();
    expect(screen.getByRole("button", { name: "Tải thêm" })).toBeDisabled();
    await user.click(secondRow);
    expect(screen.getByText(pendingDetail.source.name, { selector: "dd" })).toBeInTheDocument();

    decision.resolve({ draft_id: regular.id, status: "approved", version: 1, decided_by_subject: "analyst-sub", decided_at: "2026-11-11T01:02:03+00:00", reason: null });
    expect(await screen.findByText("Đã duyệt")).toBeInTheDocument();
    expect(screen.getByText(pendingDetail.source.name, { selector: "dd" })).toBeInTheDocument();
    expect(screen.queryByText("second.txt", { selector: "dd" })).not.toBeInTheDocument();
  });

  it("requires a trimmed rejection reason and sends it with expected version", async () => {
    const user = userEvent.setup();
    const draftApi = api({
      decide: vi.fn().mockResolvedValue({ draft_id: regular.id, status: "rejected", version: 1, decided_by_subject: "analyst-sub", decided_at: "2026-11-11T01:02:03+00:00", reason: "Sai bằng chứng" }),
    });
    render(<DraftReviewApp mode="api" api={draftApi} />);
    await screen.findByRole("button", { name: "Từ chối bản nháp" });

    await user.click(screen.getByRole("button", { name: "Từ chối bản nháp" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Nhập lý do từ chối");
    expect(draftApi.decide).not.toHaveBeenCalled();
    await user.type(screen.getByRole("textbox", { name: "Lý do từ chối" }), "  Sai bằng chứng  ");
    await user.click(screen.getByRole("button", { name: "Từ chối bản nháp" }));
    expect(draftApi.decide).toHaveBeenCalledWith(regular.id, { decision: "reject", expected_version: 0, reason: "Sai bằng chứng" });
  });

  it("does not retry a failed POST until the user clicks again", async () => {
    const user = userEvent.setup();
    const decide = vi.fn()
      .mockRejectedValueOnce(new ApiClientError("service", 503))
      .mockResolvedValueOnce({ draft_id: regular.id, status: "approved", version: 1, decided_by_subject: "analyst-sub", decided_at: "2026-11-11T01:02:03+00:00", reason: null });
    render(<DraftReviewApp mode="api" api={api({ decide })} />);
    const approve = await screen.findByRole("button", { name: "Duyệt bản nháp" });

    await user.click(approve);
    expect(await screen.findByRole("alert")).toHaveTextContent("Dịch vụ duyệt chưa sẵn sàng");
    expect(decide).toHaveBeenCalledTimes(1);
    await user.click(approve);
    expect(decide).toHaveBeenCalledTimes(2);
  });

  it.each([
    [401, "Cần phiên đăng nhập hợp lệ"],
    [403, "không có quyền"],
    [404, "không còn khả dụng"],
    [409, "Dữ liệu đã thay đổi"],
    [422, "Kiểm tra thông tin nhập"],
    [415, "Dịch vụ duyệt chưa sẵn sàng"],
    [503, "Dịch vụ duyệt chưa sẵn sàng"],
  ])("shows safe decision error for HTTP %s", async (status, message) => {
    const user = userEvent.setup();
    render(<DraftReviewApp mode="api" api={api({ decide: vi.fn().mockRejectedValue(new ApiClientError("http", status)) })} />);
    await user.click(await screen.findByRole("button", { name: "Duyệt bản nháp" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(message);
  });

  it("keeps sample preview labelled and never posts a decision", async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    render(<DraftReviewApp mode="sample" loadDrafts={async () => parseDraftQueue([regular])} />);
    const disabled = await screen.findByRole("button", { name: /chức năng duyệt đang được hoàn thiện/i });
    expect(disabled).toBeDisabled();
    await user.click(disabled);
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(screen.getByText("Dữ liệu mẫu")).toBeInTheDocument();
    fetchSpy.mockRestore();
  });

  it("does not fall back to samples when the API queue fails", async () => {
    render(<DraftReviewApp mode="api" api={api({ list: vi.fn().mockRejectedValue(new ApiClientError("network")) })} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Không tải được hàng đợi");
    expect(screen.queryByText("Dữ liệu mẫu")).not.toBeInTheDocument();
    expect(screen.queryByText(regular.source.name)).not.toBeInTheDocument();
  });

  it("renders the live review status instead of the stored pending payload status", async () => {
    const approved = {
      ...pendingDetail,
      status: "pending" as const,
      review: { ...pendingDetail.review, status: "approved" as const, version: 1, decided_by_subject: "analyst-sub", decided_at: "2026-11-11T01:02:03+00:00" },
    };
    render(<DraftReviewApp mode="api" api={api({ detail: vi.fn().mockResolvedValue(approved) })} />);

    expect(await screen.findByText("Đã duyệt")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Duyệt bản nháp" })).toBeDisabled();
  });
});
