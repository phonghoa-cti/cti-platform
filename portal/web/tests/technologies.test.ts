import { describe, expect, it } from "vitest";
import {
  AssetDataError,
  createSampleTechnologyProvider,
} from "@/data/technologies";

describe("W04 sample technology provider", () => {
  it("supports CRUD with separate software and record versions", async () => {
    const provider = createSampleTechnologyProvider();
    const initial = await provider.list();
    expect(initial[0]).toMatchObject({
      vendor: "Fortinet",
      product: "FortiOS",
      softwareVersion: "7.2.1",
      version: 1,
    });

    const created = await provider.create({
      vendor: "Microsoft",
      product: "Exchange",
      softwareVersion: "2019 CU14",
      note: "Dữ liệu tổng hợp",
    });
    expect(created).toMatchObject({ softwareVersion: "2019 CU14", version: 1 });

    const updated = await provider.update(created.id, {
      vendor: created.vendor,
      product: created.product,
      softwareVersion: "2019 CU15",
      note: created.note,
      expectedVersion: 1,
    });
    expect(updated).toMatchObject({ softwareVersion: "2019 CU15", version: 2 });

    await provider.remove(updated.id, 2);
    expect(await provider.list()).not.toContainEqual(expect.objectContaining({ id: updated.id }));
  });

  it("models the documented ASCII duplicate and stale-version responses without claiming production casefold", async () => {
    const provider = createSampleTechnologyProvider();
    await expect(provider.create({
      vendor: " FORTINET ",
      product: "fortios",
      softwareVersion: "7.2.1",
      note: "duplicate fixture",
    })).rejects.toMatchObject({ kind: "conflict" });

    const [item] = await provider.list();
    await expect(provider.update(item.id, {
      vendor: item.vendor,
      product: item.product,
      softwareVersion: item.softwareVersion,
      note: item.note,
      expectedVersion: item.version + 1,
    })).rejects.toMatchObject({ kind: "conflict" });
  });

  it("returns defensive copies", async () => {
    const provider = createSampleTechnologyProvider();
    const first = await provider.list();
    first[0].vendor = "changed";
    expect((await provider.list())[0].vendor).toBe("Fortinet");
    expect(new AssetDataError("forbidden").kind).toBe("forbidden");
  });
});
