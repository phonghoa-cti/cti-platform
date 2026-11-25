import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DraftReview } from "@/components/draft-review";
import { parseDraft } from "@/data/draft-adapter";
import regular from "@/data/fixtures/01-regular.json";

const clipboardDescriptor = Object.getOwnPropertyDescriptor(navigator, "clipboard");

function setClipboard(clipboard: Pick<Clipboard, "writeText"> | undefined) {
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: clipboard,
  });
}

afterEach(() => {
  if (clipboardDescriptor) {
    Object.defineProperty(navigator, "clipboard", clipboardDescriptor);
  } else {
    Reflect.deleteProperty(navigator, "clipboard");
  }
});

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

  it("announces an accessible error when the Clipboard API is unavailable", async () => {
    const user = userEvent.setup();
    setClipboard(undefined);
    render(<DraftReview draft={parseDraft(regular)} locale="vi" />);

    await user.click(screen.getAllByRole("button", { name: "Sao chép IOC gốc" })[0]);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Không thể sao chép IOC. Hãy thử lại.",
    );
    expect(screen.queryByRole("status", { name: /đã sao chép/i })).not.toBeInTheDocument();
  });

  it("waits for clipboard success, reports rejection, and lets the user retry", async () => {
    const user = userEvent.setup();
    let finishCopy: (() => void) | undefined;
    const writeText = vi
      .fn<(value: string) => Promise<void>>()
      .mockRejectedValueOnce(new DOMException("permission denied", "NotAllowedError"))
      .mockImplementationOnce(
        () => new Promise<void>((resolve) => { finishCopy = resolve; }),
      );
    setClipboard({ writeText });
    render(<DraftReview draft={parseDraft(regular)} locale="en" />);
    const copyButton = screen.getAllByRole("button", { name: "Copy original IOC" })[0];

    expect(writeText).not.toHaveBeenCalled();
    await user.click(copyButton);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not copy the IOC. Try again.",
    );
    expect(screen.queryByRole("status", { name: /copied/i })).not.toBeInTheDocument();

    await user.click(copyButton);
    expect(writeText).toHaveBeenCalledTimes(2);
    expect(writeText).toHaveBeenLastCalledWith("evil.example");
    expect(screen.queryByRole("status", { name: /copied/i })).not.toBeInTheDocument();

    finishCopy?.();
    expect(await screen.findByRole("status", { name: /copied/i })).toHaveTextContent("Copied");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
