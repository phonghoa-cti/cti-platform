import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { DraftReviewApp } from "@/components/draft-review-app";
import { parseDraftQueue } from "@/data/draft-adapter";
import regular from "@/data/fixtures/01-regular.json";
import empty from "@/data/fixtures/03-empty.json";

describe("draft review application states", () => {
  it("announces loading while the fixture adapter is pending", () => {
    render(<DraftReviewApp loadDrafts={() => new Promise(() => undefined)} />);
    expect(screen.getByRole("status")).toHaveTextContent("Đang tải bản nháp");
  });

  it("shows a valid empty queue as empty, not as an error", async () => {
    render(<DraftReviewApp loadDrafts={async () => []} />);
    expect(await screen.findByText("Chưa có bản nháp trong hàng đợi mẫu.")).toBeInTheDocument();
  });

  it("shows adapter failures as errors instead of an empty queue", async () => {
    render(<DraftReviewApp loadDrafts={async () => { throw new Error("invalid fixture"); }} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Không đọc được dữ liệu mẫu");
  });

  it("switches drafts and changes the interface language", async () => {
    const user = userEvent.setup();
    const drafts = parseDraftQueue([regular, empty]);
    render(<DraftReviewApp loadDrafts={async () => drafts} />);

    await user.click(await screen.findByRole("button", { name: /synthetic-regular\.txt/i }));
    expect(screen.getByRole("region", { name: "Văn bản nguồn" })).toHaveTextContent(
      "😀 Báo cáo tiếng Việt: ghi nhận kết nối tới evil[.]example.",
    );

    await user.click(screen.getByRole("button", { name: "English" }));
    await waitFor(() => expect(screen.getByRole("heading", { name: "Draft review queue" })).toBeInTheDocument());
  });
});
