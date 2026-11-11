import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";

import { AssetsHttpClient } from "@/components/assets-http-client";

afterEach(() => vi.unstubAllGlobals());

test("route client uses stable same-origin asset and technology providers in local-api mode", async () => {
  const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [] }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  }));
  vi.stubGlobal("fetch", fetcher);

  const view = render(<AssetsHttpClient />);
  view.rerender(<AssetsHttpClient />);

  expect(screen.getByText(/Bản thử kết nối API/)).toBeInTheDocument();
  expect(screen.getByRole("tab", { name: "Công nghệ" })).toBeInTheDocument();
  await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
  expect(fetcher).toHaveBeenCalledWith("/api/assets?type=domain", expect.objectContaining({ method: "GET" }));
  expect(fetcher).toHaveBeenCalledWith(
    "/api/assets/technologies",
    expect.objectContaining({ method: "GET" }),
  );
  await userEvent.click(screen.getByRole("tab", { name: "Công nghệ" }));
  expect(fetcher).toHaveBeenCalledTimes(2);
});
