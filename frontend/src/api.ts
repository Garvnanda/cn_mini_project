import type { ApiError, Bundle, DesignInput, DiffResult, DeviceLint, NLResult, Trace, WhatIf } from "./types";

export const API_URL: string = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

export class ApiFailure extends Error {
  constructor(public status: number, public body: ApiError) {
    super(body.message);
  }
}

async function call<T>(path: string, body?: unknown, timeoutMs = 60_000): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_URL}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: ctrl.signal,
    });
    if (!res.ok) {
      let err: ApiError;
      try {
        const j = await res.json();
        err = "type" in j ? j : { type: `HTTP ${res.status}`, message: typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail) };
      } catch {
        err = { type: `HTTP ${res.status}`, message: res.statusText };
      }
      throw new ApiFailure(res.status, err);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  health: () => call<{ status: string; batfish: string }>("/health", undefined, 8_000),
  presets: () => call<{ name: string; profile: string; sites: number; endpoints: number }[]>("/presets"),
  preset: (name: string) => call<DesignInput>(`/presets/${encodeURIComponent(name)}`),
  design: (input: DesignInput) => call<Bundle>("/design", input),
  trace: (input: DesignInput, src: string, dst: string, proto: string, port: number | null) =>
    call<Trace>("/trace", { input, src, dst, proto, port }),
  whatif: (input: DesignInput, links: string[], nodes: string[]) => call<WhatIf>("/whatif", { input, links, nodes }),
  lintText: (text: string) => call<DeviceLint>("/lint", { text }),
  diff: (a: DesignInput, b: DesignInput) => call<DiffResult>("/diff", { a, b }),
  nl: (text: string) => call<NLResult>("/nl", { text }, 180_000),  // free LLMs can take ~2 min
  exportUrl: (fmt: string) => `${API_URL}/export/${fmt}`,
};

export async function download(fmt: string, input: DesignInput, filename: string): Promise<void> {
  const res = await fetch(api.exportUrl(fmt), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new Error(`export failed: HTTP ${res.status}`);
  const url = URL.createObjectURL(await res.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function saveText(text: string, filename: string): void {
  const url = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
