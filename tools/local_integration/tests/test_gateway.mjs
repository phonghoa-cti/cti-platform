import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { startGateway } from "../gateway.mjs";

function listen(handler) {
  return new Promise((resolve) => {
    const server = http.createServer(handler);
    server.listen(0, "127.0.0.1", () => resolve(server));
  });
}

function close(server) {
  return new Promise((resolve) => server.close(resolve));
}

function request(port, path, options = {}) {
  return new Promise((resolve, reject) => {
    const req = http.request({ host: "127.0.0.1", port, path, method: options.method ?? "GET", headers: options.headers }, (res) => {
      const chunks = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => resolve({ status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks).toString("utf8") }));
    });
    req.on("error", reject);
    if (options.body) req.write(options.body);
    req.end();
  });
}

function requestOutcome(port, path, options = {}) {
  let req;
  const result = new Promise((resolve) => {
    req = http.request({ host: "127.0.0.1", port, path, method: options.method ?? "GET" }, (res) => {
      res.resume();
      res.once("end", () => resolve("end"));
      res.once("aborted", () => resolve("aborted"));
      res.once("error", () => resolve("response-error"));
    });
    req.once("error", () => resolve("request-error"));
    req.end();
  });
  return { result, destroy: () => req.destroy() };
}

function deadline(ms) {
  return new Promise((resolve) => setTimeout(() => resolve("deadline"), ms));
}

test("API proxy preserves status/body/security headers/cookies and replaces caller JWT", async () => {
  let seen;
  const api = await listen((req, res) => {
    seen = { headers: req.headers, origin: req.headers.origin };
    res.writeHead(409, ["Content-Type", "application/json", "Cache-Control", "no-store", "Vary", "Cf-Access-Jwt-Assertion", "Set-Cookie", "a=1; HttpOnly", "Set-Cookie", "b=2; HttpOnly", "Connection", "x-remove", "X-Remove", "secret"]);
    res.end('{"error":{"code":"draft_conflict"}}');
  });
  const ui = await listen((_req, res) => res.end("ui"));
  const gateway = await startGateway({ apiPort: api.address().port, uiPort: ui.address().port, port: 0, jwt: "server-token" });
  try {
    const result = await request(gateway.address().port, "/api/drafts/1/decision", {
      method: "POST",
      headers: { Origin: `http://127.0.0.1:${gateway.address().port}`, "Cf-Access-Jwt-Assertion": "caller-token", "Content-Type": "application/json" },
      body: "{}",
    });
    assert.equal(result.status, 409);
    assert.equal(result.body, '{"error":{"code":"draft_conflict"}}');
    assert.equal(result.headers["cache-control"], "no-store");
    assert.equal(result.headers.vary, "Cf-Access-Jwt-Assertion");
    assert.deepEqual(result.headers["set-cookie"], ["a=1; HttpOnly", "b=2; HttpOnly"]);
    assert.equal(result.headers["x-remove"], undefined);
    assert.equal(seen.headers["cf-access-jwt-assertion"], "server-token");
    assert.equal(seen.origin, `http://127.0.0.1:${gateway.address().port}`);
  } finally {
    await close(gateway); await close(api); await close(ui);
  }
});

test("gateway does not synthesize Origin, rejects wrong Host and oversized body", async () => {
  const origins = [];
  const api = await listen((req, res) => { origins.push(req.headers.origin); res.end("ok"); });
  const ui = await listen((_req, res) => res.end("ui"));
  const gateway = await startGateway({ apiPort: api.address().port, uiPort: ui.address().port, port: 0, jwt: null, maxBodyBytes: 8 });
  try {
    assert.equal((await request(gateway.address().port, "/api/drafts")).status, 200);
    assert.equal(origins[0], undefined);
    assert.equal((await request(gateway.address().port, "/api/drafts", { method: "POST", body: "0123456789" })).status, 413);
    const wrong = await request(gateway.address().port, "/api/drafts", { headers: { Host: "localhost:1" } });
    assert.equal(wrong.status, 400);
  } finally {
    await close(gateway); await close(api); await close(ui);
  }
});

test("gateway proxies only the four v1 draft routes and preserves query strings", async () => {
  const paths = [];
  const api = await listen((req, res) => {
    paths.push(req.url);
    res.writeHead(200, { "Cache-Control": "no-store" });
    res.end("ok");
  });
  const ui = await listen((_req, res) => res.end("ui"));
  const gateway = await startGateway({ apiPort: api.address().port, uiPort: ui.address().port, port: 0, jwt: null });
  try {
    for (const path of [
      "/api/v1/drafts?limit=20",
      "/api/v1/drafts/1",
      "/api/v1/drafts/1/selection",
      "/api/v1/drafts/1/decision",
    ]) {
      const result = await request(gateway.address().port, path);
      assert.equal(result.status, 200, path);
      assert.equal(result.headers["cache-control"], "no-store", path);
    }
    for (const path of [
      "/api/v1/drafts/0",
      "/api/v1/drafts/1/other",
      "/api/v1/other",
      "/api/drafts/1/selection",
    ]) {
      assert.equal((await request(gateway.address().port, path)).status, 404, path);
    }
    assert.deepEqual(paths, [
      "/api/v1/drafts?limit=20",
      "/api/v1/drafts/1",
      "/api/v1/drafts/1/selection",
      "/api/v1/drafts/1/decision",
    ]);
  } finally {
    await close(gateway); await close(api); await close(ui);
  }
});

test("gateway proxies only exact IOC route and replaces a caller-spoofed JWT", async () => {
  const seen = [];
  const api = await listen((req, res) => {
    seen.push({ path: req.url, token: req.headers["cf-access-jwt-assertion"] });
    res.writeHead(200, { "Content-Type": "application/json", "Cache-Control": "no-store", "Vary": "Cf-Access-Jwt-Assertion" });
    res.end('{"state":"not_found"}');
  });
  const ui = await listen((_req, res) => res.end("ui"));
  const gateway = await startGateway({ apiPort: api.address().port, uiPort: ui.address().port, port: 0, jwt: "gateway-token" });
  try {
    const allowed = await request(gateway.address().port, "/api/ioc?value=evil.example", {
      headers: { "Cf-Access-Jwt-Assertion": "caller-token" },
    });
    assert.equal(allowed.status, 200);
    assert.equal(allowed.headers["cache-control"], "no-store");
    assert.equal(allowed.headers.vary, "Cf-Access-Jwt-Assertion");
    for (const path of ["/api/ioc/", "/api/iocs", "/api/ioc/extra", "/api/other"]) {
      assert.equal((await request(gateway.address().port, path)).status, 404, path);
    }
    assert.deepEqual(seen, [{ path: "/api/ioc?value=evil.example", token: "gateway-token" }]);
  } finally {
    await close(gateway); await close(api); await close(ui);
  }
});

test("gateway allows only exact CVE status routes and gives PUT its own 16 KiB cap", async () => {
  const seen = [];
  const api = await listen((req, res) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => {
      seen.push({ method: req.method, path: req.url, size: Buffer.concat(chunks).length });
      res.writeHead(200, { "Cache-Control": "no-store" });
      res.end("{}");
    });
  });
  const ui = await listen((_req, res) => res.end("ui"));
  const gateway = await startGateway({ apiPort: api.address().port, uiPort: ui.address().port, port: 0, jwt: null });
  try {
    const statusPath = "/api/cves/CVE-2026-2001/technologies/1/status";
    assert.equal((await request(gateway.address().port, `${statusPath}?ignored=upstream`)).status, 200);
    assert.equal((await request(gateway.address().port, statusPath, { method: "PUT", body: "x".repeat(8193) })).status, 200);
    assert.equal((await request(gateway.address().port, statusPath, { method: "PUT", body: "x".repeat(16385) })).status, 413);
    assert.equal((await request(gateway.address().port, `${statusPath}-history?limit=1`)).status, 200);
    for (const [path, method] of [
      [statusPath, "POST"],
      [`${statusPath}-history`, "PUT"],
      ["/api/cves/CVE-2026-2001/technologies/0/status", "GET"],
      ["/api/cves/CVE-2026-2001/technologies/01/status", "GET"],
      ["/api/cves/CVE-2026-2001/technologies/1/status/extra", "GET"],
    ]) assert.equal((await request(gateway.address().port, path, { method })).status, 404, `${method} ${path}`);
    assert.deepEqual(seen.map(({ method, path, size }) => [method, path, size]), [
      ["GET", `${statusPath}?ignored=upstream`, 0],
      ["PUT", statusPath, 8193],
      ["GET", `${statusPath}-history?limit=1`, 0],
    ]);
  } finally {
    await close(gateway); await close(api); await close(ui);
  }
});

test("gateway proxies only exact asset collection and positive-id routes", async () => {
  const seen = [];
  const api = await listen((req, res) => {
    seen.push({ path: req.url, token: req.headers["cf-access-jwt-assertion"] });
    res.writeHead(200, { "Cache-Control": "no-store", "Vary": "Cf-Access-Jwt-Assertion" });
    res.end("{}");
  });
  const ui = await listen((_req, res) => res.end("ui"));
  const gateway = await startGateway({ apiPort: api.address().port, uiPort: ui.address().port, port: 0, jwt: "gateway-token" });
  try {
    for (const path of ["/api/assets?type=domain", "/api/assets/1?expected_version=1"]) {
      const result = await request(gateway.address().port, path, {
        headers: { "Cf-Access-Jwt-Assertion": "caller-token" },
      });
      assert.equal(result.status, 200, path);
      assert.equal(result.headers["cache-control"], "no-store", path);
      assert.equal(result.headers.vary, "Cf-Access-Jwt-Assertion", path);
    }
    for (const path of ["/api/assets/", "/api/assets/0", "/api/assets/01", "/api/assets/-1", "/api/assets/1/extra", "/api/asset"]) {
      assert.equal((await request(gateway.address().port, path)).status, 404, path);
    }
    assert.deepEqual(seen, [
      { path: "/api/assets?type=domain", token: "gateway-token" },
      { path: "/api/assets/1?expected_version=1", token: "gateway-token" },
    ]);
  } finally {
    await close(gateway); await close(api); await close(ui);
  }
});

test("gateway proxies exact technology routes, rejects traversal, and streams a response over 1 MiB", async () => {
  const payload = JSON.stringify({ items: [{ note: "x".repeat(1_200_000) }] });
  const seen = [];
  const api = await listen((req, res) => {
    seen.push(req.url);
    res.writeHead(200, { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(payload) });
    res.end(payload);
  });
  const ui = await listen((_req, res) => res.end("ui"));
  const gateway = await startGateway({ apiPort: api.address().port, uiPort: ui.address().port, port: 0, jwt: "gateway-token" });
  try {
    for (const route of ["/api/assets/technologies", "/api/assets/technologies/41?expected_version=1"]) {
      const result = await request(gateway.address().port, route);
      assert.equal(result.status, 200, route);
      assert.equal(result.body, payload, route);
    }
    for (const route of [
      "/api/assets/technologies/", "/api/assets/technologies/0", "/api/assets/technologies/01",
      "/api/assets/technologies/-1", "/api/assets/technologies/1/extra", "/api/assets/technology",
      "/api/assets/technologies/../1", "/api/assets/technologies/%2e%2e/1",
    ]) {
      assert.equal((await request(gateway.address().port, route)).status, 404, route);
    }
    assert.deepEqual(seen, ["/api/assets/technologies", "/api/assets/technologies/41?expected_version=1"]);
  } finally {
    await close(gateway); await close(api); await close(ui);
  }
});

test("gateway proxies only GET on the exact CVE route and preserves its query string", async () => {
  const seen = [];
  const api = await listen((request, response) => {
    seen.push({ method: request.method, path: request.url, token: request.headers["cf-access-jwt-assertion"] });
    response.writeHead(200, { "Content-Type": "application/json" }); response.end("{}");
  });
  const ui = await listen((_request, response) => response.end("ui"));
  const gateway = await startGateway({ apiPort: api.address().port, uiPort: ui.address().port, port: 0, jwt: "gateway-token" });
  try {
    assert.equal((await request(gateway.address().port, "/api/cves?kev=true&limit=25")).status, 200);
    for (const [method, path] of [
      ["POST", "/api/cves"], ["PUT", "/api/cves"], ["PATCH", "/api/cves"], ["DELETE", "/api/cves"],
      ["GET", "/api/cves/1"], ["GET", "/api/cve"], ["GET", "/api/cves%2f1"],
    ]) assert.equal((await request(gateway.address().port, path, { method })).status, 404, `${method} ${path}`);
    assert.deepEqual(seen, [{ method: "GET", path: "/api/cves?kev=true&limit=25", token: "gateway-token" }]);
  } finally {
    await close(gateway); await close(api); await close(ui);
  }
});

test("asset refresh fault fires once after a successful mutation then recovers", async () => {
  const seen = [];
  const api = await listen((req, res) => {
    seen.push(`${req.method} ${req.url}`);
    res.writeHead(req.method === "POST" ? 201 : 200, { "Cache-Control": "no-store" });
    res.end("{}");
  });
  const ui = await listen((_req, res) => res.end("ui"));
  const gateway = await startGateway({
    apiPort: api.address().port,
    uiPort: ui.address().port,
    port: 0,
    jwt: "gateway-token",
    failAssetRefreshOnce: true,
  });
  try {
    assert.equal((await request(gateway.address().port, "/api/assets", {
      method: "POST",
      headers: { Origin: `http://127.0.0.1:${gateway.address().port}` },
      body: "{}",
    })).status, 201);
    assert.equal((await request(gateway.address().port, "/api/assets")).status, 503);
    assert.equal((await request(gateway.address().port, "/api/assets")).status, 200);
    assert.deepEqual(seen, ["POST /api/assets", "GET /api/assets"]);
  } finally {
    await close(gateway); await close(api); await close(ui);
  }
});

test("asset unknown-outcome fault commits once, hides success, and writes sanitized trace", async () => {
  let mutations = 0;
  const api = await listen((req, res) => {
    if (req.method === "POST") mutations += 1;
    res.writeHead(req.method === "POST" ? 201 : 200, { "Content-Type": "application/json" });
    res.end(req.method === "POST" ? '{"id":1}' : '{"items":[{"id":1}]}');
  });
  const ui = await listen((_req, res) => res.end("ui"));
  const traceRoot = fs.mkdtempSync(path.join(os.tmpdir(), "w04-gateway-trace-"));
  const tracePath = path.join(traceRoot, "trace.jsonl");
  const gateway = await startGateway({
    apiPort: api.address().port,
    uiPort: ui.address().port,
    port: 0,
    jwt: "gateway-token",
    failAssetMutationResponseOnce: true,
    tracePath,
  });
  try {
    const mutation = await request(gateway.address().port, "/api/assets", {
      method: "POST",
      headers: { Origin: `http://127.0.0.1:${gateway.address().port}` },
      body: "{}",
    });
    assert.equal(mutation.status, 503);
    assert.equal(JSON.parse(mutation.body).error.code, "synthetic_unknown_outcome");
    assert.equal((await request(gateway.address().port, "/api/assets")).status, 200);
    assert.equal(mutations, 1);
    const trace = fs.readFileSync(tracePath, "utf8").trim().split("\n").map(JSON.parse);
    assert.deepEqual(trace, [
      { counter: 1, method: "POST", path: "/api/assets", status: 503 },
      { counter: 2, method: "GET", path: "/api/assets", status: 200 },
    ]);
    assert.equal(fs.readFileSync(tracePath, "utf8").includes("gateway-token"), false);
  } finally {
    await close(gateway); await close(api); await close(ui);
    fs.rmSync(traceRoot, { recursive: true, force: true });
  }
});

test("v1 accepts chunked bodies through 65536 bytes without raising the legacy cap", async () => {
  const sizes = [];
  const api = await listen((req, res) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => {
      sizes.push(Buffer.concat(chunks).length);
      res.writeHead(200, { "Content-Type": "application/json", "Cache-Control": "no-store" });
      res.end("{}");
    });
  });
  const ui = await listen((_req, res) => res.end("ui"));
  const gateway = await startGateway({ apiPort: api.address().port, uiPort: ui.address().port, port: 0, jwt: null });
  try {
    const aboveLegacy = " ".repeat(8193);
    assert.equal((await request(gateway.address().port, "/api/v1/drafts/1/selection", { method: "POST", body: aboveLegacy })).status, 200);
    assert.equal((await request(gateway.address().port, "/api/drafts/1/decision", { method: "POST", body: aboveLegacy })).status, 413);
    assert.equal((await request(gateway.address().port, "/api/v1/drafts/1/selection", { method: "POST", body: " ".repeat(65536) })).status, 200);
    const tooLarge = await request(gateway.address().port, "/api/v1/drafts/1/selection", { method: "POST", body: " ".repeat(65537) });
    assert.equal(tooLarge.status, 413);
    assert.equal(tooLarge.headers["cache-control"], "no-store");
    assert.deepEqual(sizes, [8193, 65536]);
  } finally {
    await close(gateway); await close(api); await close(ui);
  }
});

test("gateway timeout returns sanitized 503 once without retry", async () => {
  let hits = 0;
  const api = await listen((_req, _res) => { hits += 1; });
  const ui = await listen((_req, res) => res.end("ui"));
  const gateway = await startGateway({ apiPort: api.address().port, uiPort: ui.address().port, port: 0, jwt: null, requestTimeoutMs: 30 });
  try {
    const result = await request(gateway.address().port, "/api/drafts/1/decision", { method: "POST", body: "{}" });
    assert.equal(result.status, 503);
    assert.equal(result.headers["cache-control"], "no-store");
    assert.equal(hits, 1);
    assert.doesNotMatch(result.body, /token|header|127\.0\.0\.1/i);
  } finally {
    await close(gateway); await close(api); await close(ui);
  }
});

test("malformed request target returns 400 and gateway serves the next request", async () => {
  const api = await listen((_req, res) => res.end("ok"));
  const ui = await listen((_req, res) => res.end("ui"));
  const gateway = await startGateway({ apiPort: api.address().port, uiPort: ui.address().port, port: 0, jwt: null });
  try {
    const malformed = await request(gateway.address().port, "http://[");
    assert.equal(malformed.status, 400);
    assert.equal(malformed.headers["cache-control"], "no-store");
    assert.deepEqual(JSON.parse(malformed.body), {
      error: { code: "invalid_request_target", message: "Dịch vụ tích hợp cục bộ chưa sẵn sàng" },
    });
    assert.equal((await request(gateway.address().port, "/api/drafts")).status, 200);
  } finally {
    await close(gateway); await close(api); await close(ui);
  }
});

test("headers then stall closes downstream by timeout and gateway remains usable", async () => {
  let hits = 0;
  const api = await listen((_req, res) => {
    hits += 1;
    if (hits === 1) {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.flushHeaders();
      return;
    }
    res.end("ok");
  });
  const ui = await listen((_req, res) => res.end("ui"));
  const gateway = await startGateway({ apiPort: api.address().port, uiPort: ui.address().port, port: 0, jwt: null, requestTimeoutMs: 40 });
  const stalled = requestOutcome(gateway.address().port, "/api/drafts");
  try {
    assert.notEqual(await Promise.race([stalled.result, deadline(500)]), "deadline");
    assert.equal((await request(gateway.address().port, "/api/drafts")).status, 200);
    assert.equal(hits, 2);
  } finally {
    stalled.destroy(); await close(gateway); await close(api); await close(ui);
  }
});

test("upstream abort closes downstream and gateway remains usable", async () => {
  let hits = 0;
  const api = await listen((_req, res) => {
    hits += 1;
    if (hits === 1) {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.flushHeaders();
      return res.destroy();
    }
    res.end("ok");
  });
  const ui = await listen((_req, res) => res.end("ui"));
  const gateway = await startGateway({ apiPort: api.address().port, uiPort: ui.address().port, port: 0, jwt: null });
  const aborted = requestOutcome(gateway.address().port, "/api/drafts");
  try {
    assert.notEqual(await Promise.race([aborted.result, deadline(500)]), "deadline");
    assert.equal((await request(gateway.address().port, "/api/drafts")).status, 200);
  } finally {
    aborted.destroy(); await close(gateway); await close(api); await close(ui);
  }
});

test("client abort destroys upstream without retry and gateway remains usable", async () => {
  let hits = 0;
  let firstArrived;
  const firstArrivedPromise = new Promise((resolve) => { firstArrived = resolve; });
  let firstClosed;
  const firstClosedPromise = new Promise((resolve) => { firstClosed = resolve; });
  const api = await listen((req, res) => {
    hits += 1;
    if (hits === 1) {
      req.once("close", firstClosed);
      firstArrived();
      return;
    }
    res.end("ok");
  });
  const ui = await listen((_req, res) => res.end("ui"));
  const gateway = await startGateway({ apiPort: api.address().port, uiPort: ui.address().port, port: 0, jwt: null, requestTimeoutMs: 1000 });
  const abandoned = requestOutcome(gateway.address().port, "/api/drafts");
  try {
    assert.notEqual(await Promise.race([firstArrivedPromise.then(() => "arrived"), deadline(500)]), "deadline");
    abandoned.destroy();
    assert.notEqual(await Promise.race([firstClosedPromise.then(() => "closed"), deadline(500)]), "deadline");
    assert.equal(hits, 1);
    assert.equal((await request(gateway.address().port, "/api/drafts")).status, 200);
    assert.equal(hits, 2);
  } finally {
    abandoned.destroy(); await close(gateway); await close(api); await close(ui);
  }
});
