"use client";

import { useState } from "react";
import { AssetsApp } from "@/components/assets-app";
import { createSampleAssetsDataSource } from "@/data/assets";
import { createSampleTechnologyProvider } from "@/data/technologies";

export function AssetsSampleClient() {
  const [assetsSource] = useState(createSampleAssetsDataSource);
  const [technologyProvider] = useState(createSampleTechnologyProvider);
  return <AssetsApp dataSource={assetsSource} technologyProvider={technologyProvider} sourceMode="sample" />;
}
