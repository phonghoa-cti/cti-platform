import fs from "node:fs";
import http from "node:http";
import process from "node:process";
import { pathToFileURL } from "node:url";

const HOP_BY_HOP = new Set(["connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer", "transfer-encoding", "upgrade"]);
const LEGACY_API_PATH = /^\/api\/drafts(?:\/[1-9][0-9]*(?:\/decision)?)?$/;
const V1_API_PATH = /^\/api\/v1\/drafts(?:\/[1-9][0-9]*(?:\/(?:selection|decision))?)?$/;
const IOC_API_PATH = "/api/ioc";
const ASSET_API_PATH = /^\/api\/assets(?:\/[1-9][0-9]*)?$/;
const TECHNOLOGY_API_PATH = /^\/api\/assets\/technologies(?:\/[1-9][0-9]*)?$/;
const CVE_API_PATH = "/api/cves";
const CVE_STATUS_API_PATH = /^\/api\/cves\/CVE-[0-9]{4}-[0-9]{4,}\/technologies\/[1-9][0-9]*\/status(?:-history)?$/;

function dynamicHopHeaders(headers) {
  const names = new Set(HOP_BY_HOP);
  for (const token of String(headers.connection ?? "").split(",")) {
    if (token.trim()) names.add(token.trim().toLowerCase());
  }
  return names;
}

function cleanRequestHeaders(headers, jwt, bodyLength) {
  const removed = dynamicHopHeaders(headers);
  removed.add("host"); removed.add("content-length"); removed.add("cf-access-jwt-assertion");
  const result = {};
  for (const [name, value] of Object.entries(headers)) {
    if (!removed.has(name.toLowerCase()) && value !== undefined) result[name] = value;
  }
  if (jwt !== null) result["cf-access-jwt-assertion"] = jwt;
  if (bodyLength > 0) result["content-length"] = String(bodyLength);
  return result;
}

function cleanResponseHeaders(upstream) {
  const removed = dynamicHopHeaders(upstream.headers);
  const result = {};
  const cookies = [];
  for (let index = 0; index < upstream.rawHeaders.length; index += 2) {
    const name = upstream.rawHeaders[index];
    const value = upstream.rawHeaders[index + 1];
    const lower = name.toLowerCase();
    if (removed.has(lower)) continue;
    if (lower === "set-cookie") cookies.push(value);
    else if (result[name] === undefined) result[name] = value;
    else result[name] = `${result[name]}, ${value}`;
  }
  if (cookies.length) result["Set-Cookie"] = cookies;
  return result;
}

function safeError(response, status, code) {
  if (response.destroyed || response.writableEnded) return;
  if (response.headersSent) return response.destroy();
  const body = JSON.stringify({ error: { code, message: "Dịch vụ tích hợp cục bộ chưa sẵn sàng" } });
  response.writeHead(status, { "Content-Type": "application/json", "Cache-Control": "no-store", "Content-Length": Buffer.byteLength(body) });
  response.end(body);
}

function readBody(request, limit) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    request.on("data", (chunk) => {
      size += chunk.length;
      if (size > limit) reject(Object.assign(new Error("body too large"), { code: "BODY_TOO_LARGE" }));
      else chunks.push(chunk);
    });
    request.on("end", () => resolve(Buffer.concat(chunks)));
    request.on("aborted", () => reject(new Error("request aborted")));
    request.on("error", reject);
  });
}

export async function startGateway({ apiPort, uiPort, port, jwt, requestTimeoutMs = 1000, maxBodyBytes = 8192, maxV1BodyBytes = 65536, maxStatusBodyBytes = 16384, failRefreshAfterPost = false, failAssetRefreshOnce = false, failAssetMutationResponseOnce = false, failTechnologyRefreshCount = 0, failTechnologyMutationResponseOnce = false, failCveGetOnce = false, failStatusGetCount = 0, failStatusMutationResponseOnce = false, tracePath = null }) {
  for (const value of [apiPort, uiPort]) {
    if (!Number.isInteger(value) || value < 1 || value > 65535) throw new TypeError("upstream port không hợp lệ");
  }
  if (!Number.isInteger(port) || port < 0 || port > 65535) throw new TypeError("gateway port không hợp lệ");
  if (jwt !== null && typeof jwt !== "string") throw new TypeError("jwt phải là string hoặc null");
  if (tracePath !== null && typeof tracePath !== "string") throw new TypeError("trace path phải là string hoặc null");
  let postRecorded = false;
  let assetRefreshPending = false;
  let assetMutationFaultUsed = false;
  let technologyRefreshFailuresRemaining = 0;
  let technologyMutationFaultUsed = false;
  let cveGetFailurePending = failCveGetOnce;
  let statusGetFailuresRemaining = 0;
  let statusMutationFaultUsed = false;
  let requestCounter = 0;
  const server = http.createServer(async (request, response) => {
    const ownPort = server.address()?.port;
    if (request.headers.host !== `127.0.0.1:${ownPort}`) return safeError(response, 400, "invalid_host");
    const rawPath = (request.url ?? "/").split("?", 1)[0];
    if (/(?:^|\/)(?:\.{2}|%2e%2e)(?:\/|$)/i.test(rawPath)) return safeError(response, 404, "not_found");
    let url;
    try {
      url = new URL(request.url ?? "/", `http://127.0.0.1:${ownPort}`);
    } catch {
      return safeError(response, 400, "invalid_request_target");
    }
    const counter = ++requestCounter;
    const trace = (status) => {
      if (tracePath === null) return;
      fs.appendFileSync(tracePath, `${JSON.stringify({ counter, method: request.method, path: url.pathname, status })}\n`, { encoding: "utf8" });
    };
    const isApi = url.pathname.startsWith("/api/");
    const isV1 = V1_API_PATH.test(url.pathname);
    const isAsset = ASSET_API_PATH.test(url.pathname);
    const isTechnology = TECHNOLOGY_API_PATH.test(url.pathname);
    const isCve = url.pathname === CVE_API_PATH;
    const isStatus = CVE_STATUS_API_PATH.test(url.pathname);
    const isStatusHistory = isStatus && url.pathname.endsWith("/status-history");
    const statusMethodAllowed = isStatusHistory ? request.method === "GET" : ["GET", "PUT"].includes(request.method ?? "");
    if (isCve && request.method !== "GET") return safeError(response, 404, "not_found");
    if (isStatus && !statusMethodAllowed) return safeError(response, 404, "not_found");
    if (isApi && !isV1 && !isAsset && !isTechnology && !isCve && !isStatus && url.pathname !== IOC_API_PATH && !LEGACY_API_PATH.test(url.pathname)) {
      return safeError(response, 404, "not_found");
    }
    if (isCve && cveGetFailurePending) {
      cveGetFailurePending = false;
      trace(503);
      return safeError(response, 503, "synthetic_refresh_failure");
    }
    if (isStatus && request.method === "GET" && statusGetFailuresRemaining > 0) {
      statusGetFailuresRemaining -= 1;
      trace(503);
      return safeError(response, 503, "synthetic_refresh_failure");
    }
    if (isApi && failRefreshAfterPost && postRecorded && request.method === "GET") {
      trace(503);
      return safeError(response, 503, "synthetic_refresh_failure");
    }
    if (isAsset && failAssetRefreshOnce && assetRefreshPending && request.method === "GET") {
      assetRefreshPending = false;
      trace(503);
      return safeError(response, 503, "synthetic_refresh_failure");
    }
    if (isTechnology && technologyRefreshFailuresRemaining > 0 && request.method === "GET") {
      technologyRefreshFailuresRemaining -= 1;
      trace(503);
      return safeError(response, 503, "synthetic_refresh_failure");
    }
    let body;
    try {
      body = await readBody(
        request,
        isV1 ? maxV1BodyBytes : (isStatus && request.method === "PUT" ? maxStatusBodyBytes : maxBodyBytes),
      );
    } catch (error) {
      if (error.code === "BODY_TOO_LARGE") return safeError(response, 413, "request_too_large");
      return safeError(response, 400, "invalid_request");
    }
    const targetPort = isApi ? apiPort : uiPort;
    const headers = cleanRequestHeaders(request.headers, isApi ? jwt : null, body.length);
    let responseComplete = false;
    let failureHandled = false;
    const failUpstream = () => {
      if (responseComplete || failureHandled) return;
      failureHandled = true;
      trace(503);
      safeError(response, 503, "upstream_unavailable");
    };
    const upstream = http.request({ host: "127.0.0.1", port: targetPort, method: request.method, path: `${url.pathname}${url.search}`, headers, timeout: requestTimeoutMs }, (upstreamResponse) => {
      if (isApi && failRefreshAfterPost && request.method === "POST" && (upstreamResponse.statusCode ?? 500) < 300) postRecorded = true;
      if (isAsset && failAssetRefreshOnce && ["POST", "PUT", "DELETE"].includes(request.method ?? "") && (upstreamResponse.statusCode ?? 500) < 300) assetRefreshPending = true;
      if (isTechnology && failTechnologyRefreshCount > 0 && ["POST", "PUT", "DELETE"].includes(request.method ?? "") && (upstreamResponse.statusCode ?? 500) < 300) technologyRefreshFailuresRemaining = failTechnologyRefreshCount;
      upstreamResponse.once("end", () => { responseComplete = true; });
      upstreamResponse.once("aborted", failUpstream);
      upstreamResponse.once("error", failUpstream);
      upstreamResponse.once("close", () => {
        if (!upstreamResponse.complete) failUpstream();
      });
      const successfulAssetMutation = isAsset
        && ["POST", "PUT", "DELETE"].includes(request.method ?? "")
        && (upstreamResponse.statusCode ?? 500) < 300;
      const successfulTechnologyMutation = isTechnology
        && ["POST", "PUT", "DELETE"].includes(request.method ?? "")
        && (upstreamResponse.statusCode ?? 500) < 300;
      const successfulStatusMutation = isStatus
        && !isStatusHistory
        && request.method === "PUT"
        && (upstreamResponse.statusCode ?? 500) < 300;
      if (successfulStatusMutation && failStatusGetCount > 0) {
        statusGetFailuresRemaining = failStatusGetCount;
      }
      if (failAssetMutationResponseOnce && !assetMutationFaultUsed && successfulAssetMutation) {
        assetMutationFaultUsed = true;
        upstreamResponse.once("end", () => {
          trace(503);
          safeError(response, 503, "synthetic_unknown_outcome");
        });
        upstreamResponse.resume();
        return;
      }
      if (failTechnologyMutationResponseOnce && !technologyMutationFaultUsed && successfulTechnologyMutation) {
        technologyMutationFaultUsed = true;
        technologyRefreshFailuresRemaining = 1;
        upstreamResponse.once("end", () => {
          trace(503);
          safeError(response, 503, "synthetic_unknown_outcome");
        });
        upstreamResponse.resume();
        return;
      }
      if (failStatusMutationResponseOnce && !statusMutationFaultUsed && successfulStatusMutation) {
        statusMutationFaultUsed = true;
        statusGetFailuresRemaining = Math.max(statusGetFailuresRemaining, 1);
        upstreamResponse.once("end", () => {
          trace(503);
          safeError(response, 503, "synthetic_unknown_outcome");
        });
        upstreamResponse.resume();
        return;
      }
      trace(upstreamResponse.statusCode ?? 502);
      response.writeHead(upstreamResponse.statusCode ?? 502, cleanResponseHeaders(upstreamResponse));
      upstreamResponse.pipe(response);
    });
    upstream.on("timeout", () => upstream.destroy(new Error("timeout")));
    upstream.on("error", failUpstream);
    response.once("close", () => {
      if (!response.writableEnded && !responseComplete && !upstream.destroyed) {
        upstream.destroy(new Error("downstream closed"));
      }
    });
    if (body.length) upstream.write(body);
    upstream.end();
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, "127.0.0.1", () => { server.removeListener("error", reject); resolve(); });
  });
  return server;
}

async function main() {
  const server = await startGateway({
    apiPort: Number(process.env.W05_API_PORT), uiPort: Number(process.env.W05_UI_PORT),
    port: Number(process.env.W05_GATEWAY_PORT), jwt: process.env.W05_GATEWAY_JWT ?? null,
    requestTimeoutMs: Number(process.env.W05_REQUEST_TIMEOUT_MS ?? "1000"),
    failRefreshAfterPost: process.env.W05_FAIL_REFRESH === "1",
    failAssetRefreshOnce: process.env.W04_FAIL_ASSET_REFRESH_ONCE === "1",
    failAssetMutationResponseOnce: process.env.W04_FAIL_ASSET_MUTATION_RESPONSE_ONCE === "1",
    failTechnologyRefreshCount: process.env.W04_FAIL_TECHNOLOGY_REFRESH_TWICE === "1" ? 2 : 0,
    failTechnologyMutationResponseOnce: process.env.W04_FAIL_TECHNOLOGY_MUTATION_RESPONSE_ONCE === "1",
    failCveGetOnce: process.env.W03_FAIL_CVE_GET_ONCE === "1",
    failStatusGetCount: Number(process.env.W03_FAIL_STATUS_GET_COUNT ?? "0"),
    failStatusMutationResponseOnce: process.env.W03_FAIL_STATUS_MUTATION_RESPONSE_ONCE === "1",
    tracePath: process.env.W04_TRACE_PATH ?? null,
  });
  const stop = () => server.close(() => process.exit(0));
  process.on("SIGINT", stop); process.on("SIGTERM", stop);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) main().catch(() => process.exit(1));
