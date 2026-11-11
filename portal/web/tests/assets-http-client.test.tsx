import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { AssetsHttpClient } from "@/components/assets-http-client";

afterEach(() => vi.unstubAllGlobals());

test("route client uses the same-origin assets API in local-api mode", async () => {
  const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [] }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  }));
  vi.stubGlobal("fetch", fetcher);

  render(<AssetsHttpClient />);

  expect(screen.getByText(/Bản thử kết nối API/)).toBeInTheDocument();
  await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(1));
  expect(fetcher).toHaveBeenCalledWith("/api/assets?type=domain", expect.objectContaining({ method: "GET" }));
});
