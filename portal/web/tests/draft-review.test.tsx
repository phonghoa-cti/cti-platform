import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DraftReview } from "@/components/draft-review";
import { parseDraft } from "@/data/draft-adapter";
import regular from "@/data/fixtures/01-regular.json";

describe("draft review preview", () => {
  it("renders untrusted report HTML as text and never creates a link", () => {
    const malicious = parseDraft({
      ...regular,
      text: '<img src=x onerror="alert(1)"> hxxps://evil.example',
      source: { ...regular.source, name: "<script>alert(1)</script>" },
      items: [],
    });

    const { container } = render(<DraftReview draft={malicious} locale="vi" />);
    expect(screen.getByText(/<img src=x/)).toBeInTheDocument();
    expect(screen.getByText("<script>alert(1)</script>")).toBeInTheDocument();
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("script")).toBeNull();
    expect(container.querySelector("a")).toBeNull();
  });

  it("keeps approval disabled and performs no write request", async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    render(<DraftReview draft={parseDraft(regular)} locale="vi" />);

    const approval = screen.getByRole("button", { name: /chức năng duyệt đang được hoàn thiện/i });
    expect(approval).toBeDisabled();
    await user.click(approval);
    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });

  it("shows a rejected item and its reason instead of hiding it", () => {
    const rejected = parseDraft({
      ...regular,
      items: [
        {
          ...regular.items[0],
          span: null,
          evidence: "",
          keep: false,
          status: "bia",
          value: "missing.example",
          warning: "IOC không có evidence trong nguồn",
        },
      ],
    });
    render(<DraftReview draft={rejected} locale="vi" />);
    expect(screen.getByText("missing[.]example")).toBeInTheDocument();
    expect(screen.getByText("IOC không có evidence trong nguồn")).toBeInTheDocument();
  });
});
