import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AssetsApp } from "@/components/assets-app";
import { AssetDataError, type AssetDataSource, type AssetItem } from "@/data/assets";

const domain: AssetItem = {
  id: 1,
  type: "domain",
  value: "congty.vn",
  note: "Tên miền chính",
  createdBy: "sample-it",
  createdAt: "2026-11-11T00:00:00Z",
  updatedAt: "2026-11-11T00:00:00Z",
  version: 1,
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((done, fail) => { resolve = done; reject = fail; });
  return { promise, resolve, reject };
}

function dataSource(overrides: Partial<AssetDataSource> = {}): AssetDataSource {
  return {
    list: vi.fn().mockResolvedValue([domain]),
    create: vi.fn().mockResolvedValue(domain),
    update: vi.fn().mockResolvedValue({ ...domain, version: 2 }),
    remove: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  };
}

describe("W04 assets management", () => {
  it("labels sample-only behavior and renders loading, data, and empty states", async () => {
    const first = deferred<AssetItem[]>();
    const source = dataSource({ list: vi.fn().mockReturnValueOnce(first.promise).mockResolvedValueOnce([]) });
    const user = userEvent.setup();
    render(<AssetsApp dataSource={source} />);

    expect(screen.getByText("Dữ liệu mẫu — thay đổi chỉ trong phiên thử")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Đang tải tài sản");
    first.resolve([domain]);
    expect(await screen.findByText("congty.vn")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Dải IP" }));
    expect(await screen.findByText(/Chưa có dải IP nào/)).toBeInTheDocument();
  });

  it.each([
    ["authentication-required", "Cần đăng nhập để quản lý tài sản"],
    ["forbidden", "Bạn không có quyền quản lý tài sản"],
    ["unavailable", "Dịch vụ tài sản tạm thời không sẵn sàng"],
  ] as const)("renders %s separately", async (kind, message) => {
    render(<AssetsApp dataSource={dataSource({ list: vi.fn().mockRejectedValue(new AssetDataError(kind)) })} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(message);
  });

  it("rejects an invalid domain locally without calling create", async () => {
    const source = dataSource();
    const user = userEvent.setup();
    render(<AssetsApp dataSource={source} />);
    await screen.findByText("congty.vn");
    await user.click(screen.getByRole("button", { name: "Thêm tên miền" }));
    await user.type(screen.getByRole("textbox", { name: "Tên miền" }), "https://congty.vn/path");
    await user.click(screen.getByRole("button", { name: "Lưu tài sản" }));

    expect(screen.getByRole("alert")).toHaveTextContent("Chỉ nhập hostname");
    expect(source.create).not.toHaveBeenCalled();
  });

  it("creates once, then distinguishes a committed write from a failed refresh", async () => {
    const source = dataSource({
      list: vi.fn().mockResolvedValueOnce([]).mockRejectedValueOnce(new AssetDataError("unavailable")).mockResolvedValueOnce([domain]),
      create: vi.fn().mockResolvedValue(domain),
    });
    const user = userEvent.setup();
    render(<AssetsApp dataSource={source} />);
    await screen.findByText(/Chưa có tên miền nào/);
    await user.click(screen.getByRole("button", { name: "Thêm tên miền" }));
    await user.type(screen.getByRole("textbox", { name: "Tên miền" }), "congty.vn");
    await user.click(screen.getByRole("button", { name: "Lưu tài sản" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Đã lưu nhưng chưa tải lại được danh sách");
    expect(source.create).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("button", { name: "Tải lại danh sách" }));
    expect(await screen.findByText("congty.vn")).toBeInTheDocument();
    expect(source.create).toHaveBeenCalledTimes(1);
    expect(source.list).toHaveBeenCalledTimes(3);
  });

  it("does not replay an unknown mutation outcome and directs the user to reload", async () => {
    const source = dataSource({
      list: vi.fn().mockResolvedValue([]),
      create: vi.fn().mockRejectedValue(new AssetDataError("unknown-mutation")),
    });
    const user = userEvent.setup();
    render(<AssetsApp dataSource={source} />);
    await screen.findByText(/Chưa có tên miền nào/);
    await user.click(screen.getByRole("button", { name: "Thêm tên miền" }));
    await user.type(screen.getByRole("textbox", { name: "Tên miền" }), "congty.vn");
    await user.click(screen.getByRole("button", { name: "Lưu tài sản" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Chưa xác định yêu cầu đã được ghi hay chưa");
    expect(source.create).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("button", { name: "Lưu tài sản" })).not.toBeInTheDocument();
  });

  it("keeps edited input after a 409 conflict and sends expected version once", async () => {
    const source = dataSource({ update: vi.fn().mockRejectedValue(new AssetDataError("conflict")) });
    const user = userEvent.setup();
    render(<AssetsApp dataSource={source} />);
    await screen.findByText("congty.vn");
    await user.click(screen.getByRole("button", { name: "Sửa congty.vn" }));
    const input = screen.getByRole("textbox", { name: "Tên miền" });
    await user.clear(input);
    await user.type(input, "portal.congty.vn");
    await user.click(screen.getByRole("button", { name: "Lưu thay đổi" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Tài sản đã thay đổi ở nơi khác");
    expect(input).toHaveValue("portal.congty.vn");
    expect(source.update).toHaveBeenCalledWith(1, expect.objectContaining({ expectedVersion: 1 }));
    expect(source.update).toHaveBeenCalledTimes(1);
  });

  it("asks for an object-specific confirmation before delete", async () => {
    const source = dataSource({ list: vi.fn().mockResolvedValueOnce([domain]).mockResolvedValueOnce([]) });
    const user = userEvent.setup();
    render(<AssetsApp dataSource={source} />);
    await screen.findByText("congty.vn");
    await user.click(screen.getByRole("button", { name: "Xóa congty.vn" }));
    expect(screen.getByText("Xóa tài sản congty.vn?")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Xác nhận xóa congty.vn" }));

    await waitFor(() => expect(source.remove).toHaveBeenCalledWith(1, 1));
    expect(source.remove).toHaveBeenCalledTimes(1);
  });

  it("prevents double submit while a create is pending", async () => {
    const pending = deferred<AssetItem>();
    const source = dataSource({ list: vi.fn().mockResolvedValue([]), create: vi.fn().mockReturnValue(pending.promise) });
    const user = userEvent.setup();
    render(<AssetsApp dataSource={source} />);
    await screen.findByText(/Chưa có tên miền nào/);
    await user.click(screen.getByRole("button", { name: "Thêm tên miền" }));
    await user.type(screen.getByRole("textbox", { name: "Tên miền" }), "congty.vn");
    const save = screen.getByRole("button", { name: "Lưu tài sản" });
    await user.click(save);

    expect(screen.getByRole("button", { name: "Đang lưu…" })).toBeDisabled();
    expect(source.create).toHaveBeenCalledTimes(1);
  });

  it("ignores a stale domain list after switching to IP ranges", async () => {
    const oldDomain = deferred<AssetItem[]>();
    const ip: AssetItem = { ...domain, id: 2, type: "ip_range", value: "203.0.113.0/24" };
    const source = dataSource({ list: vi.fn().mockReturnValueOnce(oldDomain.promise).mockResolvedValueOnce([ip]) });
    const user = userEvent.setup();
    render(<AssetsApp dataSource={source} />);
    await user.click(screen.getByRole("tab", { name: "Dải IP" }));
    expect(await screen.findByText("203.0.113.0/24")).toBeInTheDocument();
    oldDomain.resolve([domain]);

    await waitFor(() => expect(screen.getByText("203.0.113.0/24")).toBeInTheDocument());
    expect(screen.queryByText("congty.vn")).not.toBeInTheDocument();
  });

  it("does not let a completed mutation refresh overwrite a newer tab context", async () => {
    const mutation = deferred<AssetItem>();
    const ip: AssetItem = { ...domain, id: 2, type: "ip_range", value: "203.0.113.0/24" };
    const source = dataSource({
      list: vi.fn()
        .mockResolvedValueOnce([])
        .mockResolvedValueOnce([ip])
        .mockResolvedValueOnce([domain]),
      create: vi.fn().mockReturnValue(mutation.promise),
    });
    const user = userEvent.setup();
    render(<AssetsApp dataSource={source} />);
    await screen.findByText(/Chưa có tên miền nào/);
    await user.click(screen.getByRole("button", { name: "Thêm tên miền" }));
    await user.type(screen.getByRole("textbox", { name: "Tên miền" }), "congty.vn");
    await user.click(screen.getByRole("button", { name: "Lưu tài sản" }));

    await user.click(screen.getByRole("tab", { name: "Dải IP" }));
    expect(await screen.findByText("203.0.113.0/24")).toBeInTheDocument();
    await act(async () => mutation.resolve(domain));

    await waitFor(() => expect(source.create).toHaveBeenCalledTimes(1));
    expect(source.list).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("tab", { name: "Dải IP" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("203.0.113.0/24")).toBeInTheDocument();
    expect(screen.queryByText("congty.vn")).not.toBeInTheDocument();
    expect(screen.queryByText("Đã lưu tài sản.")).not.toBeInTheDocument();
  });
});
