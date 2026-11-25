"use client";

import { IocLookup } from "@/components/ioc-lookup";
import { createIocHttpDataSource } from "@/data/ioc-lookup-http";

const httpLookupSource = createIocHttpDataSource();

export function IocLookupHttpClient() {
  return <IocLookup dataSource={httpLookupSource} sourceMode="local-api" />;
}
