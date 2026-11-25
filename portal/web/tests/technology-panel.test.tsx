import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TechnologyPanel } from "@/components/technology-panel";
import { AssetsApp } from "@/components/assets-app";
import {
  AssetDataError,
  type TechnologyItem,
  type TechnologyProvider,
} from "@/data/technologies";
import type { AssetDataSource } from "@/data/assets";

const technology: TechnologyItem = {
  id: 41,
  vendor: "Fortinet",
  product: "FortiOS",
  softwareVersion: "7.2.1",
  note: "VPN gateway mẫu",
  createdBy: "synthetic-it",
  createdAt: "2026-11-11T16:00:00Z",
  updatedAt: "2026-11-11T16:00:00Z",
  version: 3,
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((done, fail) => { resolve = done; reject = fail; });
  return { promise, resolve, reject };
}

function provider(overrides: Partial<TechnologyProvider> = {}): TechnologyProvider {
  return {
    list: vi.fn().mockResolvedValue([technology]),
    create: vi.fn().mockResolvedValue(technology),
    update: vi.fn().mockResolvedValue({ ...technology, version: 4 }),
    remove: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  };
}

const assets: AssetDataSource = {
  list: vi.fn().mockResolvedValue([]),
  create: vi.fn(),
  update: vi.fn(),
  remove: vi.fn(),
};

async function openCreate(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("button", { name: "Thêm công nghệ" }));
  await user.type(screen.getByRole("textbox", { name: "Nhà cung cấp" }), "Microsoft");
  await user.type(screen.getByRole("textbox", { name: "Sản phẩm" }), "Exchange");
  await user.type(screen.getByRole("textbox", { name: "Phiên bản phần mềm" }), "2019 CU14");
}

describe("W04 technology panel", () => {
  it("renders loading, empty, and data with software version separate from record revision", async () => {
    const pending = deferred<TechnologyItem[]>();
    const source = provider({ list: vi.fn().mockReturnValueOnce(pending.promise) });
    render(<TechnologyPanel provider={source} locale="vi" />);
    expect(screen.getByRole("status")).toHaveTextContent("Đang tải công nghệ");
    pending.resolve([technology]);

    expect(await screen.findByText("FortiOS")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Phiên bản phần mềm" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Lần sửa" })).toBeInTheDocument();
    expect(screen.getByText("7.2.1")).toBeInTheDocument();
    expect(screen.getByText("v3")).toBeInTheDocument();

    const empty = provider({ list: vi.fn().mockResolvedValue([]) });
    const { rerender } = render(<TechnologyPanel provider={empty} locale="vi" />);
    rerender(<TechnologyPanel provider={empty} locale="vi" />);
    expect(await screen.findByText(/Chưa có công nghệ nào/)).toBeInTheDocument();
  });

  it.each([
    ["authentication-required", "Cần đăng nhập để quản lý công nghệ"],
    ["forbidden", "Bạn không có quyền quản lý công nghệ"],
    ["unavailable", "Dịch vụ công nghệ tạm thời không sẵn sàng"],
  ] as const)("renders %s separately", async (kind, message) => {
    render(<TechnologyPanel provider={provider({ list: vi.fn().mockRejectedValue(new AssetDataError(kind)) })} locale="vi" />);
    expect(await screen.findByRole("alert")).toHaveTextContent(message);
  });

  it("rejects missing and over-bound code-point input before create", async () => {
    const source = provider();
    const user = userEvent.setup();
    render(<TechnologyPanel provider={source} locale="vi" />);
    await screen.findByText("FortiOS");
    await user.click(screen.getByRole("button", { name: "Thêm công nghệ" }));
    await user.type(screen.getByRole("textbox", { name: "Nhà cung cấp" }), "😀".repeat(129));
    await user.type(screen.getByRole("textbox", { name: "Sản phẩm" }), "FortiOS");
    await user.type(screen.getByRole("textbox", { name: "Phiên bản phần mềm" }), "7.2.1");
    await user.click(screen.getByRole("button", { name: "Lưu công nghệ" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Nhà cung cấp tối đa 128 ký tự");
    expect(source.create).not.toHaveBeenCalled();
  });

  it("creates once and preserves committed state when the refresh fails", async () => {
    const source = provider({
      list: vi.fn().mockResolvedValueOnce([]).mockRejectedValueOnce(new AssetDataError("unavailable")).mockResolvedValueOnce([technology]),
    });
    const user = userEvent.setup();
    render(<TechnologyPanel provider={source} locale="vi" />);
    await screen.findByText(/Chưa có công nghệ nào/);
    await openCreate(user);
    await user.click(screen.getByRole("button", { name: "Lưu công nghệ" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Đã lưu nhưng chưa tải lại được danh sách công nghệ");
    expect(source.create).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("button", { name: "Tải lại danh sách công nghệ" }));
    expect(await screen.findByText("FortiOS")).toBeInTheDocument();
    expect(source.create).toHaveBeenCalledTimes(1);
  });

  it.each(["create", "update", "delete"] as const)("keeps committed %s notice across failed GET retries and clears it only on GET success", async (operation) => {
    const initial = operation === "create" ? [] : [technology];
    const final = operation === "delete" ? [] : [technology];
    const source = provider({
      list: vi.fn()
        .mockResolvedValueOnce(initial)
        .mockRejectedValueOnce(new AssetDataError("unavailable"))
        .mockRejectedValueOnce(new AssetDataError("unavailable"))
        .mockResolvedValueOnce(final),
    });
    const user = userEvent.setup();
    render(<TechnologyPanel provider={source} locale="vi" />);
    if (operation === "create") {
      await screen.findByText(/Chưa có công nghệ nào/);
      await openCreate(user);
      await user.click(screen.getByRole("button", { name: "Lưu công nghệ" }));
    } else {
      await screen.findByText("FortiOS");
      if (operation === "update") {
        await user.click(screen.getByRole("button", { name: "Sửa Fortinet FortiOS" }));
        await user.click(screen.getByRole("button", { name: "Lưu thay đổi" }));
      } else {
        await user.click(screen.getByRole("button", { name: "Xóa Fortinet FortiOS" }));
        await user.click(screen.getByRole("button", { name: "Xác nhận xóa Fortinet FortiOS" }));
      }
    }
    expect(await screen.findByRole("alert")).toHaveTextContent("Đã lưu nhưng chưa tải lại được danh sách công nghệ");
    await user.click(screen.getByRole("button", { name: "Tải lại danh sách công nghệ" }));
    await waitFor(() => expect(source.list).toHaveBeenCalledTimes(3));
    expect(screen.getByRole("alert")).toHaveTextContent("Đã lưu nhưng chưa tải lại được danh sách công nghệ");
    expect(source[operation === "delete" ? "remove" : operation]).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("button", { name: "Tải lại danh sách công nghệ" }));
    if (operation === "delete") await screen.findByText(/Chưa có công nghệ nào/);
    else await screen.findByText("FortiOS");
    expect(screen.queryByText(/Đã lưu nhưng chưa tải lại được danh sách công nghệ/)).not.toBeInTheDocument();
    expect(source[operation === "delete" ? "remove" : operation]).toHaveBeenCalledTimes(1);
  });

  it("locks after an unknown create and reconciles with GET only", async () => {
    const reconciliation = deferred<TechnologyItem[]>();
    const source = provider({
      list: vi.fn().mockResolvedValueOnce([]).mockReturnValueOnce(reconciliation.promise),
      create: vi.fn().mockRejectedValue(new AssetDataError("unknown-mutation")),
    });
    const user = userEvent.setup();
    render(<TechnologyPanel provider={source} locale="vi" />);
    await screen.findByText(/Chưa có công nghệ nào/);
    await openCreate(user);
    await user.click(screen.getByRole("button", { name: "Lưu công nghệ" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Chưa xác định yêu cầu công nghệ đã được ghi hay chưa");
    expect(screen.queryByRole("button", { name: "Lưu công nghệ" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Đối soát danh sách công nghệ" }));
    expect(screen.getByRole("button", { name: "Thêm công nghệ" })).toBeDisabled();
    expect(screen.getByRole("alert")).toHaveTextContent("Chưa xác định yêu cầu công nghệ đã được ghi hay chưa");
    reconciliation.resolve([technology]);
    expect(await screen.findByText("FortiOS")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Thêm công nghệ" })).toBeEnabled();
    expect(source.create).toHaveBeenCalledTimes(1);
    expect(source.list).toHaveBeenCalledTimes(2);
  });

  it("preserves edited input on duplicate/stale conflict and sends expected version once", async () => {
    const source = provider({ update: vi.fn().mockRejectedValue(new AssetDataError("conflict")) });
    const user = userEvent.setup();
    render(<TechnologyPanel provider={source} locale="vi" />);
    await screen.findByText("FortiOS");
    await user.click(screen.getByRole("button", { name: "Sửa Fortinet FortiOS" }));
    const product = screen.getByRole("textbox", { name: "Sản phẩm" });
    await user.clear(product);
    await user.type(product, "FortiGate");
    await user.click(screen.getByRole("button", { name: "Lưu thay đổi" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("đã tồn tại hoặc đã thay đổi ở nơi khác");
    expect(product).toHaveValue("FortiGate");
    expect(source.update).toHaveBeenCalledWith(41, expect.objectContaining({ expectedVersion: 3 }));
    expect(source.update).toHaveBeenCalledTimes(1);
  });

  it("confirms delete and sends the record version once", async () => {
    const source = provider({ list: vi.fn().mockResolvedValueOnce([technology]).mockResolvedValueOnce([]) });
    const user = userEvent.setup();
    render(<TechnologyPanel provider={source} locale="vi" />);
    await screen.findByText("FortiOS");
    await user.click(screen.getByRole("button", { name: "Xóa Fortinet FortiOS" }));
    expect(screen.getByText("Xóa công nghệ Fortinet FortiOS?")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Xác nhận xóa Fortinet FortiOS" }));
    await waitFor(() => expect(source.remove).toHaveBeenCalledWith(41, 3));
    expect(source.remove).toHaveBeenCalledTimes(1);
  });

  it("prevents double submit while create is pending", async () => {
    const pending = deferred<TechnologyItem>();
    const source = provider({ list: vi.fn().mockResolvedValue([]), create: vi.fn().mockReturnValue(pending.promise) });
    const user = userEvent.setup();
    render(<TechnologyPanel provider={source} locale="vi" />);
    await screen.findByText(/Chưa có công nghệ nào/);
    await openCreate(user);
    await user.click(screen.getByRole("button", { name: "Lưu công nghệ" }));
    expect(screen.getByRole("button", { name: "Đang lưu…" })).toBeDisabled();
    expect(source.create).toHaveBeenCalledTimes(1);
  });

  it.each(["create", "update", "delete"] as const)("ignores stale %s completion after provider change", async (operation) => {
    const mutation = deferred<TechnologyItem | void>();
    const oldProvider = provider({
      list: vi.fn().mockResolvedValue(operation === "create" ? [] : [technology]),
      create: vi.fn().mockReturnValue(mutation.promise),
      update: vi.fn().mockReturnValue(mutation.promise),
      remove: vi.fn().mockReturnValue(mutation.promise),
    });
    const nextProvider = provider({ list: vi.fn().mockResolvedValue([{ ...technology, id: 99, product: "Exchange" }]) });
    const user = userEvent.setup();
    const view = render(<TechnologyPanel provider={oldProvider} locale="vi" />);
    if (operation === "create") {
      await screen.findByText(/Chưa có công nghệ nào/);
      await openCreate(user);
      await user.click(screen.getByRole("button", { name: "Lưu công nghệ" }));
    } else {
      await screen.findByText("FortiOS");
      if (operation === "update") {
        await user.click(screen.getByRole("button", { name: "Sửa Fortinet FortiOS" }));
        await user.click(screen.getByRole("button", { name: "Lưu thay đổi" }));
      } else {
        await user.click(screen.getByRole("button", { name: "Xóa Fortinet FortiOS" }));
        await user.click(screen.getByRole("button", { name: "Xác nhận xóa Fortinet FortiOS" }));
      }
    }

    view.rerender(<TechnologyPanel provider={nextProvider} locale="vi" />);
    expect(await screen.findByText("Exchange")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Thêm công nghệ" })).toBeEnabled();
    await act(async () => mutation.resolve(operation === "delete" ? undefined : technology));
    await waitFor(() => expect(nextProvider.list).toHaveBeenCalledTimes(1));
    expect(screen.getByText("Exchange")).toBeInTheDocument();
    expect(screen.queryByText("Đã lưu công nghệ.")).not.toBeInTheDocument();
    expect(oldProvider.list).toHaveBeenCalledTimes(1);
  });

  it("ignores a stale committed-refresh failure after provider change and after unmount", async () => {
    const refresh = deferred<TechnologyItem[]>();
    const oldProvider = provider({ list: vi.fn().mockResolvedValueOnce([]).mockReturnValueOnce(refresh.promise) });
    const nextProvider = provider({ list: vi.fn().mockResolvedValue([{ ...technology, product: "Exchange" }]) });
    const user = userEvent.setup();
    const view = render(<TechnologyPanel provider={oldProvider} locale="vi" />);
    await screen.findByText(/Chưa có công nghệ nào/);
    await openCreate(user);
    await user.click(screen.getByRole("button", { name: "Lưu công nghệ" }));
    await waitFor(() => expect(oldProvider.list).toHaveBeenCalledTimes(2));
    view.rerender(<TechnologyPanel provider={nextProvider} locale="vi" />);
    expect(await screen.findByText("Exchange")).toBeInTheDocument();
    await act(async () => refresh.reject(new AssetDataError("unavailable")));
    expect(screen.queryByText(/Đã lưu nhưng chưa tải lại/)).not.toBeInTheDocument();
    view.unmount();
  });

  it("does not refresh or write state when a mutation completes after unmount", async () => {
    const mutation = deferred<TechnologyItem>();
    const source = provider({ list: vi.fn().mockResolvedValue([]), create: vi.fn().mockReturnValue(mutation.promise) });
    const user = userEvent.setup();
    const view = render(<TechnologyPanel provider={source} locale="vi" />);
    await screen.findByText(/Chưa có công nghệ nào/);
    await openCreate(user);
    await user.click(screen.getByRole("button", { name: "Lưu công nghệ" }));
    view.unmount();
    await act(async () => mutation.resolve(technology));
    expect(source.list).toHaveBeenCalledTimes(1);
  });
});

describe("W04 technology tab injection", () => {
  it("keeps a pending mutation owned by the same provider across tabs and requires a later successful reconcile", async () => {
    const mutation = deferred<TechnologyItem>();
    const source = provider({
      list: vi.fn().mockResolvedValueOnce([]).mockResolvedValueOnce([technology]).mockResolvedValueOnce([technology]),
      create: vi.fn().mockReturnValue(mutation.promise),
    });
    const user = userEvent.setup();
    render(<AssetsApp dataSource={assets} technologyProvider={source} />);
    await user.click(screen.getByRole("tab", { name: "Công nghệ" }));
    await screen.findByText(/Chưa có công nghệ nào/);
    await openCreate(user);
    await user.click(screen.getByRole("button", { name: "Lưu công nghệ" }));
    await user.click(screen.getByRole("tab", { name: "Tên miền" }));
    await user.click(screen.getByRole("tab", { name: "Công nghệ" }));
    await waitFor(() => expect(source.list).toHaveBeenCalledTimes(2));
    expect(screen.getByRole("button", { name: "Thêm công nghệ" })).toBeDisabled();

    await act(async () => mutation.reject(new AssetDataError("unknown-mutation")));
    expect(await screen.findByRole("alert")).toHaveTextContent("Chưa xác định yêu cầu công nghệ đã được ghi hay chưa");
    expect(screen.getByRole("button", { name: "Thêm công nghệ" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Đối soát danh sách công nghệ" }));
    await waitFor(() => expect(source.list).toHaveBeenCalledTimes(3));
    expect(screen.getByRole("button", { name: "Thêm công nghệ" })).toBeEnabled();
    expect(source.create).toHaveBeenCalledTimes(1);
  });

  it("falls back to the existing domain view if the optional provider is removed", async () => {
    const user = userEvent.setup();
    const view = render(<AssetsApp dataSource={assets} technologyProvider={provider()} />);
    await user.click(screen.getByRole("tab", { name: "Công nghệ" }));
    await screen.findByText("FortiOS");
    view.rerender(<AssetsApp dataSource={assets} />);
    expect(screen.getByRole("tab", { name: "Tên miền" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText(/Chưa có tên miền nào/)).toBeInTheDocument();
  });

  it("shows technology only when a provider is supplied and invalidates callbacks when leaving its tab", async () => {
    const pending = deferred<TechnologyItem>();
    const source = provider({ create: vi.fn().mockReturnValue(pending.promise) });
    const user = userEvent.setup();
    const view = render(<AssetsApp dataSource={assets} />);
    expect(screen.queryByRole("tab", { name: "Công nghệ" })).not.toBeInTheDocument();

    view.rerender(<AssetsApp dataSource={assets} technologyProvider={source} />);
    await user.click(screen.getByRole("tab", { name: "Công nghệ" }));
    await screen.findByText("FortiOS");
    await openCreate(user);
    await user.click(screen.getByRole("button", { name: "Lưu công nghệ" }));
    await user.click(screen.getByRole("tab", { name: "Tên miền" }));
    await act(async () => pending.resolve(technology));
    expect(screen.getByRole("tab", { name: "Tên miền" })).toHaveAttribute("aria-selected", "true");
    expect(await screen.findByText(/Chưa có tên miền nào/)).toBeInTheDocument();
    expect(screen.queryByText("Đã lưu công nghệ.")).not.toBeInTheDocument();
  });

  it.each(["create", "update", "delete"] as const)("does not let a stale %s refresh write into the domain tab", async (operation) => {
    const refresh = deferred<TechnologyItem[]>();
    const source = provider({
      list: vi.fn().mockResolvedValueOnce(operation === "create" ? [] : [technology]).mockReturnValueOnce(refresh.promise),
    });
    const user = userEvent.setup();
    render(<AssetsApp dataSource={assets} technologyProvider={source} />);
    await user.click(screen.getByRole("tab", { name: "Công nghệ" }));
    if (operation === "create") {
      await screen.findByText(/Chưa có công nghệ nào/);
      await openCreate(user);
      await user.click(screen.getByRole("button", { name: "Lưu công nghệ" }));
    } else {
      await screen.findByText("FortiOS");
      if (operation === "update") {
        await user.click(screen.getByRole("button", { name: "Sửa Fortinet FortiOS" }));
        await user.click(screen.getByRole("button", { name: "Lưu thay đổi" }));
      } else {
        await user.click(screen.getByRole("button", { name: "Xóa Fortinet FortiOS" }));
        await user.click(screen.getByRole("button", { name: "Xác nhận xóa Fortinet FortiOS" }));
      }
    }
    await waitFor(() => expect(source.list).toHaveBeenCalledTimes(2));
    await user.click(screen.getByRole("tab", { name: "Tên miền" }));
    await act(async () => refresh.reject(new AssetDataError("unavailable")));
    expect(screen.getByRole("tab", { name: "Tên miền" })).toHaveAttribute("aria-selected", "true");
    expect(screen.queryByText(/Đã lưu nhưng chưa tải lại được danh sách công nghệ/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Đang tải công nghệ/)).not.toBeInTheDocument();
  });
});
