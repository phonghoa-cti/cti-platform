import assert from "node:assert/strict";
import http from "node:http";
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
