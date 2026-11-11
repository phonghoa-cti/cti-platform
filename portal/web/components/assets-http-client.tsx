"use client";

import { AssetsApp } from "@/components/assets-app";
import { createAssetsHttpDataSource } from "@/data/assets-http";
import { useState } from "react";

export function AssetsHttpClient() {
  const [httpAssetsSource] = useState(createAssetsHttpDataSource);
  return <AssetsApp dataSource={httpAssetsSource} sourceMode="local-api" />;
}
