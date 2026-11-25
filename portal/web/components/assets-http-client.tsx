"use client";

import { AssetsApp } from "@/components/assets-app";
import { createAssetsHttpDataSource } from "@/data/assets-http";
import { createTechnologiesHttpProvider } from "@/data/technologies-http";
import { useState } from "react";

export function AssetsHttpClient() {
  const [httpAssetsSource] = useState(createAssetsHttpDataSource);
  const [httpTechnologyProvider] = useState(createTechnologiesHttpProvider);
  return (
    <AssetsApp
      dataSource={httpAssetsSource}
      sourceMode="local-api"
      technologyProvider={httpTechnologyProvider}
    />
  );
}
