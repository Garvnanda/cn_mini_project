import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import bundle from "./fixtures/bundle.json";

const preset = (bundle as { design: { input: unknown } }).design.input;

function mockFetch() {
  return vi.fn(async (url: string, init?: RequestInit) => {
    const path = new URL(url).pathname;
    const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
    if (path === "/health") return json({ status: "ok", batfish: "n/a" });
    if (path === "/presets") return json([{ name: "metro_man", profile: "metro_man", sites: 3, endpoints: 550 }]);
    if (path.startsWith("/presets/")) return json(preset);
    if (path === "/design") {
      const body = JSON.parse(String(init?.body));
      if (body.profile === "bad") return json({ type: "PhysicalDistanceViolationError", message: "Copper was requested" }, 422);
      return json(bundle);
    }
    if (path === "/trace") return json({ src: "a", dst: "b", proto: "icmp", port: null, outcome: "delivered", reason: "reached", hops: [{ device: "HQ-CORE1", in_if: "Vlan10", out_if: null, action: "deliver", detail: "ok" }] });
    return json({ detail: "not mocked" }, 404);
  });
}

describe("App", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", mockFetch());
  });
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("wakes the server, designs a preset and shows every tab", async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByRole("status").textContent).toContain("Server ready"));
    await waitFor(() => expect((screen.getByLabelText("Design input (editable JSON)") as HTMLTextAreaElement).value).toContain("metro_man"));
    fireEvent.click(screen.getByRole("button", { name: /Design network/ }));
    await waitFor(() => expect(screen.getByText(/verify PASS/)).toBeTruthy());
    expect(screen.getByRole("img", { name: "Network topology" })).toBeTruthy();
    for (const tab of ["Decisions", "IP Plan", "Configs", "Verify", "Security", "BOM", "Versions", "Report"]) {
      fireEvent.click(screen.getByRole("tab", { name: tab }));
    }
    expect(screen.getByText(/NetArchitect design report/)).toBeTruthy();
  });

  it("shows typed engine errors", async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByRole("status").textContent).toContain("Server ready"));
    fireEvent.change(screen.getByLabelText("Design input (editable JSON)"), { target: { value: JSON.stringify({ profile: "bad" }) } });
    fireEvent.click(screen.getByRole("button", { name: /Design network/ }));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("PhysicalDistanceViolationError"));
  });

  it("rejects malformed JSON before calling the API", async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByRole("status").textContent).toContain("Server ready"));
    fireEvent.change(screen.getByLabelText("Design input (editable JSON)"), { target: { value: "{oops" } });
    fireEvent.click(screen.getByRole("button", { name: /Design network/ }));
    expect(screen.getByText(/Invalid JSON/)).toBeTruthy();
  });

  it("traces a packet on the topology", async () => {
    render(<App />);
    await waitFor(() => expect(screen.getByRole("status").textContent).toContain("Server ready"));
    await waitFor(() => expect((screen.getByLabelText("Design input (editable JSON)") as HTMLTextAreaElement).value).toContain("metro_man"));
    fireEvent.click(screen.getByRole("button", { name: /Design network/ }));
    await waitFor(() => screen.getByRole("button", { name: /Trace packet/ }));
    fireEvent.click(screen.getByRole("button", { name: /Trace packet/ }));
    await waitFor(() => expect(screen.getByText(/DELIVERED: reached/)).toBeTruthy());
  });
});
