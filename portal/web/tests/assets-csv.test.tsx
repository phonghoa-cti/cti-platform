import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AssetsApp } from "@/components/assets-app";
import { createSampleAssetsDataSource, AssetDataError } from "@/data/assets";
import { createSampleTechnologyProvider } from "@/data/technologies";
import { assetsCsv, csvCell, downloadCsv } from "@/lib/assets-csv";

vi.mock("@/lib/assets-csv", async (importOriginal) => ({
  ...await importOriginal<typeof import("@/lib/assets-csv")>(),
  downloadCsv: vi.fn(),
}));

describe("W04 combined CSV", () => {
  it.each(["=SUM(1,2)", "+1", "-1", "@cmd", "  =1", "\t=1", "\r\n@x", "＝1"])("neutralizes formula %s", (value) => {
    expect(csvCell(value)).toBe(`"'${value.replaceAll('"', '""')}"`);
  });

  it("escapes quotes, commas, line breaks and keeps Unicode with BOM and CRLF", async () => {
    const source = createSampleAssetsDataSource();
    const tech = createSampleTechnologyProvider();
    const domain = await source.create({ type: "domain", value: "example.invalid", note: 'Việt, "ghi chú"\nDòng 2' });
    const technology = await tech.create({ vendor: "@vendor", product: "App", softwareVersion: "-1", note: "=1" });
    const csv = assetsCsv([domain], [technology]);
    expect(csv.charCodeAt(0)).toBe(0xfeff);
    expect(csv).toContain('"type","value","vendor","product","software_version","note"\r\n');
    expect(csv).toContain('"Việt, ""ghi chú""\nDòng 2"');
    expect(csv).toContain('"technology","","\'@vendor","App","\'-1","\'=1"');
    expect(assetsCsv([], [])).toBe('\uFEFF"type","value","vendor","product","software_version","note"\r\n');
  });

  it("exports all three groups from current providers without writing data", async () => {
    vi.mocked(downloadCsv).mockClear();
    const source = createSampleAssetsDataSource();
    const technology = createSampleTechnologyProvider();
    const list = vi.spyOn(source, "list");
    const listTech = vi.spyOn(technology, "list");
    const create = vi.spyOn(source, "create");
    render(<AssetsApp dataSource={source} technologyProvider={technology} />);
    await screen.findByText("congty-mau.vn");
    await userEvent.click(screen.getByRole("button", { name: "Xuất CSV tài sản và công nghệ" }));
    await waitFor(() => expect(downloadCsv).toHaveBeenCalledTimes(1));
    const csv = vi.mocked(downloadCsv).mock.calls[0][0];
    expect(csv).toContain("congty-mau.vn");
    expect(csv).toContain("203.0.113.0/24");
    expect(csv).toContain("FortiOS");
    expect(list).toHaveBeenCalledWith("domain");
    expect(list).toHaveBeenCalledWith("ip_range");
    expect(listTech).toHaveBeenCalled();
    expect(create).not.toHaveBeenCalled();
  });

  it("does not download a partial CSV if a provider denies access", async () => {
    vi.mocked(downloadCsv).mockClear();
    const source = createSampleAssetsDataSource();
    const originalList = source.list;
    source.list = vi.fn(async (type) => {
      if (type === "ip_range") throw new AssetDataError("forbidden");
      return originalList(type);
    });
    render(<AssetsApp dataSource={source} technologyProvider={createSampleTechnologyProvider()} />);
    await screen.findByText("congty-mau.vn");
    await userEvent.click(screen.getByRole("button", { name: "Xuất CSV tài sản và công nghệ" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Không xuất CSV");
    expect(downloadCsv).not.toHaveBeenCalled();
  });
});
