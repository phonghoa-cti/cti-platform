import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DraftReviewApp } from "@/components/draft-review-app";
import { ApiClientError, parseDraftDetailV1, type DraftApi, type DraftDetail, type DraftPage, type SelectionView } from "@/data/api-client";
import regular from "@/data/fixtures/01-regular.json";

const hash0 = "a".repeat(64);
const hash1 = "b".repeat(64);
const selection = (overrides: Partial<SelectionView> = {}): SelectionView => ({
  review_version: 0,
  selection_version: 0,
  selected_indices: [0],
  selected_sha256: hash0,
  saved_by_subject: null,
  saved_at: null,
  changed: false,
  ai_extracted_count: 1,
  ai_eligible_count: 1,
  human_deselected_count: 0,
  selection_save_count: 0,
  ...overrides,
});

function detail(selectionValue = selection()): DraftDetail {
  return parseDraftDetailV1({
    ...regular,
    review: { status: "pending", version: selectionValue.review_version, created_by_subject: "author-sub", decided_by_subject: null, decided_at: null, reason: null },
    selection: { ...selectionValue, changed: false },
  });
}

const summary = {
  id: regular.id,
  created_at: regular.created_at,
  status: "pending" as const,
  source: regular.source,
  language: regular.language as "vi",
  tlp: regular.tlp as "TLP:AMBER",
  item_count: regular.items.length,
  injection_warning: false,
  review_status: "pending" as const,
  review_version: 0,
  selection_version: 0,
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((done, fail) => { resolve = done; reject = fail; });
  return { promise, resolve, reject };
}

function api(overrides: Partial<DraftApi> = {}): DraftApi {
  return {
    list: vi.fn().mockResolvedValue({ items: [summary], next_before_id: null }),
    detail: vi.fn().mockResolvedValue(detail()),
    saveSelection: vi.fn(),
    decide: vi.fn(),
    ...overrides,
  };
}

describe("W05 saved and editing selection UI", () => {
  it.each(["dirty", "saving"])("does not let queue retry reset %s selection state", async (state) => {
    const user = userEvent.setup();
    const pending = deferred<SelectionView>();
    const list = vi.fn().mockResolvedValueOnce({ items: [summary], next_before_id: 1 })
      .mockRejectedValueOnce(new ApiClientError("network"))
      .mockResolvedValue({ items: [summary], next_before_id: null });
    const draftApi = api({ list, saveSelection: vi.fn().mockReturnValue(pending.promise) });
    render(<DraftReviewApp mode="api" api={draftApi} />);
    await screen.findByRole("checkbox", { name: /evil\.example/i });
    await user.click(screen.getByRole("button", { name: "Tải thêm" }));
    const retry = await screen.findByRole("button", { name: "Thử lại" });
    await user.click(screen.getByRole("checkbox", { name: /evil\.example/i }));
    if (state === "saving") await user.click(screen.getByRole("button", { name: "Lưu lựa chọn" }));
    await user.click(retry);
    expect(list).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("checkbox", { name: /evil\.example/i })).not.toBeChecked();
  });

  it("keeps a read selection above 1024 intact and lets the analyst deselect to the save limit", async () => {
    const user = userEvent.setup();
    const items = Array.from({ length: 1025 }, (_, index) => ({ ...regular.items[0], value: `ioc-${index}.example`, span: null, evidence: "" }));
    const readSelection = selection({ selected_indices: items.map((_, index) => index), ai_extracted_count: 1025, ai_eligible_count: 1025 });
    const readDetail = parseDraftDetailV1({
      ...regular,
      items,
      review: { status: "pending", version: 0, created_by_subject: "author-sub", decided_by_subject: null, decided_at: null, reason: null },
      selection: readSelection,
    });
    const saved = selection({ review_version: 1, selection_version: 1, selected_indices: items.slice(1).map((_, index) => index + 1), selected_sha256: hash1, changed: true, ai_extracted_count: 1025, ai_eligible_count: 1025, human_deselected_count: 1, selection_save_count: 1 });
    const refreshed = parseDraftDetailV1({ ...readDetail, review: { ...readDetail.review, version: 1 }, selection: { ...saved, changed: false } });
    const saveSelection = vi.fn().mockResolvedValue(saved);
    const draftApi = api({ detail: vi.fn().mockResolvedValueOnce(readDetail).mockResolvedValueOnce(refreshed), saveSelection });
    render(<DraftReviewApp mode="api" api={draftApi} />);

    const first = await screen.findByRole("checkbox", { name: /ioc-0\.example/i });
    expect(first).toBeEnabled();
    expect(screen.getByRole("button", { name: "Duyệt bản nháp" })).toBeEnabled();
    await user.click(first);
    await user.click(screen.getByRole("button", { name: "Lưu lựa chọn" }));
    expect(saveSelection).toHaveBeenCalledWith(regular.id, { expected_version: 0, selected_indices: items.slice(1).map((_, index) => index + 1) });
  });

  it("keeps editing local until explicit save, blocks navigation, and pins the exact save snapshot", async () => {
    const user = userEvent.setup();
    const pending = deferred<SelectionView>();
    const saved = selection({ review_version: 1, selection_version: 1, selected_indices: [], selected_sha256: hash1, saved_by_subject: "analyst", saved_at: "2026-11-11T01:00:00Z", changed: true, human_deselected_count: 1, selection_save_count: 1 });
    const draftApi = api({
      detail: vi.fn().mockResolvedValueOnce(detail()).mockResolvedValueOnce(detail(saved)),
      saveSelection: vi.fn().mockReturnValue(pending.promise),
    });
    render(<DraftReviewApp mode="api" api={draftApi} />);

    const checkbox = await screen.findByRole("checkbox", { name: /evil\.example/i });
    expect(checkbox).toBeChecked();
    await user.click(checkbox);

    expect(screen.getByRole("status")).toHaveTextContent("thay đổi chưa lưu");
    expect(draftApi.saveSelection).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: /synthetic-regular\.txt/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Duyệt bản nháp" })).toBeDisabled();

    const save = screen.getByRole("button", { name: "Lưu lựa chọn" });
    await Promise.all([user.click(save), user.click(save)]);
    expect(draftApi.saveSelection).toHaveBeenCalledTimes(1);
    expect(draftApi.saveSelection).toHaveBeenCalledWith(regular.id, { expected_version: 0, selected_indices: [] });

    pending.resolve(saved);
    expect(await screen.findByText(/Lựa chọn đã được lưu/)).toBeInTheDocument();
    await waitFor(() => expect(draftApi.detail).toHaveBeenCalledTimes(2));
    expect(regular.items[0].keep).toBe(true);
  });

  it("discards editing back to the exact saved set without a POST", async () => {
    const user = userEvent.setup();
    const draftApi = api();
    render(<DraftReviewApp mode="api" api={draftApi} />);
    const checkbox = await screen.findByRole("checkbox", { name: /evil\.example/i });
    await user.click(checkbox);
    await user.click(screen.getByRole("button", { name: "Hủy thay đổi" }));
    expect(checkbox).toBeChecked();
    expect(screen.queryByText(/thay đổi chưa lưu/i)).not.toBeInTheDocument();
    expect(draftApi.saveSelection).not.toHaveBeenCalled();
  });

  it("allows an empty saved selection to reject with a trimmed reason but never approve", async () => {
    const user = userEvent.setup();
    const empty = selection({ selected_indices: [], human_deselected_count: 1 });
    const decide = vi.fn().mockResolvedValue({
      draft_id: regular.id, status: "rejected", version: 1, decided_by_subject: "analyst", decided_at: "2026-11-11T01:02:00Z",
      reason: "Sai bằng chứng", selection_version: 0, selected_indices: [], selected_sha256: hash0,
    });
    render(<DraftReviewApp mode="api" api={api({ detail: vi.fn().mockResolvedValue(detail(empty)), decide })} />);

    expect(await screen.findByRole("button", { name: "Duyệt bản nháp" })).toBeDisabled();
    const reject = screen.getByRole("button", { name: "Từ chối bản nháp" });
    expect(reject).toBeEnabled();
    await user.type(screen.getByRole("textbox", { name: "Lý do từ chối" }), "  Sai bằng chứng  ");
    await user.click(reject);
    expect(decide).toHaveBeenCalledWith(regular.id, { decision: "reject", expected_version: 0, reason: "Sai bằng chứng" }, empty);
  });

  it("locks duplicate writes after an ambiguous save until explicit discard and reload", async () => {
    const user = userEvent.setup();
    const saveSelection = vi.fn().mockRejectedValue(new ApiClientError("network"));
    const draftApi = api({ saveSelection });
    render(<DraftReviewApp mode="api" api={draftApi} />);
    await user.click(await screen.findByRole("checkbox", { name: /evil\.example/i }));
    await user.click(screen.getByRole("button", { name: "Lưu lựa chọn" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Chưa xác định lựa chọn đã được lưu");
    expect(screen.getByRole("button", { name: "Lưu lựa chọn" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Lưu lựa chọn" }));
    expect(saveSelection).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole("button", { name: "Bỏ thay đổi cục bộ và tải lại trạng thái" }));
    await waitFor(() => expect(draftApi.detail).toHaveBeenCalledTimes(2));
    expect(saveSelection).toHaveBeenCalledTimes(1);
    expect(screen.queryByText(/đã được lưu/i)).not.toBeInTheDocument();
  });

  it("keeps edits on 409 and uses recovery GET without replaying the POST", async () => {
    const user = userEvent.setup();
    const saveSelection = vi.fn().mockRejectedValue(new ApiClientError("http", 409));
    const draftApi = api({ saveSelection });
    render(<DraftReviewApp mode="api" api={draftApi} />);
    await user.click(await screen.findByRole("checkbox", { name: /evil\.example/i }));
    await user.click(screen.getByRole("button", { name: "Lưu lựa chọn" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Dữ liệu đã thay đổi");
    expect(screen.getByRole("checkbox", { name: /evil\.example/i })).not.toBeChecked();
    await user.click(screen.getByRole("button", { name: "Bỏ thay đổi cục bộ và tải lại trạng thái" }));
    await waitFor(() => expect(draftApi.detail).toHaveBeenCalledTimes(2));
    expect(saveSelection).toHaveBeenCalledTimes(1);
  });

  it("retains a valid save when refresh fails and retry performs GET only", async () => {
    const user = userEvent.setup();
    const saved = selection({ review_version: 1, selection_version: 1, selected_indices: [], selected_sha256: hash1, changed: true, human_deselected_count: 1, selection_save_count: 1 });
    const saveSelection = vi.fn().mockResolvedValue(saved);
    const detailRequest = vi.fn().mockResolvedValueOnce(detail()).mockRejectedValueOnce(new ApiClientError("network")).mockResolvedValueOnce(detail());
    const draftApi = api({ saveSelection, detail: detailRequest });
    render(<DraftReviewApp mode="api" api={draftApi} />);
    await user.click(await screen.findByRole("checkbox", { name: /evil\.example/i }));
    await user.click(screen.getByRole("button", { name: "Lưu lựa chọn" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("đã được lưu nhưng chưa tải lại được trạng thái");
    expect(screen.getByRole("button", { name: "Duyệt bản nháp" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Tải lại trạng thái" }));
    await waitFor(() => expect(detailRequest).toHaveBeenCalledTimes(3));
    expect(saveSelection).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("checkbox", { name: /evil\.example/i })).not.toBeChecked();
    expect(screen.getByRole("checkbox", { name: /evil\.example/i })).toBeDisabled();
  });

  it("does not roll a confirmed decision back to pending during refresh", async () => {
    const user = userEvent.setup();
    const decide = vi.fn().mockResolvedValue({ draft_id: regular.id, status: "approved", version: 1, decided_by_subject: "analyst", decided_at: "2026-11-11T01:02:00Z", reason: null, selection_version: 0, selected_indices: [0], selected_sha256: hash0 });
    const draftApi = api({ decide });
    render(<DraftReviewApp mode="api" api={draftApi} />);
    await user.click(await screen.findByRole("button", { name: "Duyệt bản nháp" }));
    await waitFor(() => expect(draftApi.detail).toHaveBeenCalledTimes(2));
    expect(screen.getByText("Đã duyệt", { selector: "span" })).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: /evil\.example/i })).toBeDisabled();
    expect(decide).toHaveBeenCalledTimes(1);
  });

  it("escapes a missing draft to the remaining queue after explicit discard", async () => {
    const user = userEvent.setup();
    const secondSummary = { ...summary, id: 2, source: { ...summary.source, name: "second.txt" } };
    const secondDetail = { ...detail(), id: 2, source: { ...detail().source, name: "second.txt" } };
    const details = vi.fn().mockResolvedValueOnce(detail()).mockImplementation(async (id: number) => {
      if (id === regular.id) throw new ApiClientError("http", 404);
      return secondDetail;
    });
    const draftApi = api({
      list: vi.fn().mockResolvedValueOnce({ items: [summary, secondSummary], next_before_id: null }).mockResolvedValue({ items: [secondSummary], next_before_id: null }),
      detail: details,
      saveSelection: vi.fn().mockRejectedValue(new ApiClientError("http", 404)),
    });
    render(<DraftReviewApp mode="api" api={draftApi} />);
    await user.click(await screen.findByRole("checkbox", { name: /evil\.example/i }));
    await user.click(screen.getByRole("button", { name: "Lưu lựa chọn" }));
    await user.click(await screen.findByRole("button", { name: "Bỏ thay đổi cục bộ và tải lại trạng thái" }));
    const second = await screen.findByRole("button", { name: /second\.txt/i });
    expect(second).toBeEnabled();
    await user.click(second);
    expect(await screen.findByText("second.txt", { selector: "dd" })).toBeInTheDocument();
  });

  it("does not apply mismatched detail from an injected API", async () => {
    const draftApi = api({ detail: vi.fn().mockResolvedValue({ ...detail(), id: 2, source: { ...detail().source, name: "second.txt" } }) });
    render(<DraftReviewApp mode="api" api={draftApi} />);
    await waitFor(() => expect(draftApi.detail).toHaveBeenCalled());
    expect(screen.queryByText("second.txt", { selector: "dd" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Duyệt bản nháp" })).not.toBeInTheDocument();
  });

  it.each(["success", "error"])("ends an old pagination lifecycle after selecting another draft on %s", async (outcome) => {
    const user = userEvent.setup();
    const pending = deferred<DraftPage>();
    const summaryFor = (id: number) => ({ ...summary, id, source: { ...summary.source, name: `draft-${id}.txt` } });
    const detailFor = (id: number) => ({ ...detail(), id, source: { ...detail().source, name: `draft-${id}.txt` } });
    const list = vi.fn().mockResolvedValueOnce({ items: [summaryFor(3), summaryFor(2)], next_before_id: 2 })
      .mockReturnValueOnce(pending.promise).mockResolvedValue({ items: [summaryFor(1)], next_before_id: null });
    const draftApi = api({ list, detail: vi.fn(async (id: number) => detailFor(id)) });
    render(<DraftReviewApp mode="api" api={draftApi} />);
    await screen.findByText("draft-3.txt", { selector: "dd" });
    await user.click(screen.getByRole("button", { name: "Tải thêm" }));
    await user.click(screen.getByRole("button", { name: /draft-2\.txt/ }));
    await screen.findByText("draft-2.txt", { selector: "dd" });
    await act(async () => {
      if (outcome === "success") pending.resolve({ items: [], next_before_id: 2 });
      else pending.reject(new ApiClientError("network"));
      await Promise.resolve();
    });
    const loadMore = screen.getByRole("button", { name: "Tải thêm" });
    expect(loadMore).toBeEnabled();
    await user.click(loadMore);
    await screen.findByRole("button", { name: /draft-1\.txt/ });
    expect(screen.getByText("draft-2.txt", { selector: "dd" })).toBeInTheDocument();
  });

  it("does not let an old pagination callback unlock the current pagination request", async () => {
    const user = userEvent.setup();
    const oldRequest = deferred<DraftPage>(); const currentRequest = deferred<DraftPage>();
    const summaryFor = (id: number) => ({ ...summary, id, source: { ...summary.source, name: `draft-${id}.txt` } });
    const detailFor = (id: number) => ({ ...detail(), id, source: { ...detail().source, name: `draft-${id}.txt` } });
    const list = vi.fn().mockResolvedValueOnce({ items: [summaryFor(3), summaryFor(2)], next_before_id: 2 })
      .mockReturnValueOnce(oldRequest.promise).mockReturnValueOnce(currentRequest.promise);
    render(<DraftReviewApp mode="api" api={api({ list, detail: vi.fn(async (id: number) => detailFor(id)) })} />);
    await screen.findByText("draft-3.txt", { selector: "dd" });
    await user.click(screen.getByRole("button", { name: "Tải thêm" }));
    await user.click(screen.getByRole("button", { name: /draft-2\.txt/ }));
    await screen.findByText("draft-2.txt", { selector: "dd" });
    await user.click(screen.getByRole("button", { name: "Tải thêm" }));
    await act(async () => { oldRequest.resolve({ items: [], next_before_id: 2 }); await Promise.resolve(); });
    expect(screen.getByRole("button", { name: "Đang tải thêm…" })).toBeDisabled();
    await act(async () => { currentRequest.resolve({ items: [summaryFor(1)], next_before_id: null }); await Promise.resolve(); });
    await screen.findByRole("button", { name: /draft-1\.txt/ });
    expect(screen.getByText("draft-2.txt", { selector: "dd" })).toBeInTheDocument();
  });
});
