// Hand-written mirror of the backend Pydantic models used by the UI (D-033).

export type DesignInput = Record<string, unknown> & {
  profile: string;
  root_prefix: string;
  sites: { name: string; kind: string }[];
  segments: { name: string; vlan: number; hosts: number; role: string; location: string; poe?: boolean }[];
  links?: { a: string; b: string; distance_m: number }[];
};

export interface Rationale {
  rule_id: string;
  domain: string;
  inputs: Record<string, unknown>;
  threshold: string | null;
  standard_ref: string;
  text: string;
}

export interface Subnet {
  name: string;
  vlan: number | null;
  requested_hosts: number;
  network: string;
  prefix: number;
  mask: string;
  wildcard: string;
  gateway: string | null;
  broadcast: string | null;
  usable_hosts: number;
  utilization_pct: number;
  unit: string | null;
}

export interface MediaDecision {
  link: string;
  distance_m: number;
  media: string;
  transceiver: string;
}

export interface Device {
  hostname: string;
  role: string;
  site: string;
}

export interface Cable {
  a: string;
  a_if: string;
  b: string;
  b_if: string;
  kind: string;
  media: string;
  transceiver: string;
}

export interface Design {
  input: DesignInput;
  media: MediaDecision[];
  subnets: Subnet[];
  routing: { protocol: string; areas: Record<string, number>; asn: Record<string, number> };
  devices: Device[];
  cables: Cable[];
  tiers: Record<string, string>;
  rationale: Rationale[];
}

export interface GraphNode { id: string; role: string; site: string; x: number; y: number }
export interface GraphEdge { a: string; a_if: string; b: string; b_if: string; kind: string; media: string }

export interface Check { name: string; passed: boolean; details: string[] }
export interface Probe { src: string; dst: string; proto: string; port: number | null; expected: string; actual: string; reason: string }
export interface Verification { passed: boolean; checks: Check[]; probes: Probe[] }

export interface Finding { rule: string; severity: string; title: string; where: string; fix: string }
export interface DeviceLint { hostname: string; score: number; findings: Finding[] }
export interface LintReport { score: number; devices: DeviceLint[] }

export interface BomLine { item: string; qty: number; unit: string; unit_price: number; total: number; rule_id: string; note: string }
export interface Bom { currency: string; lines: BomLine[]; capex: number; monthly: number; poe_watts: Record<string, number>; alternatives: Rationale[]; disclaimer: string }

export interface Spof { spof_devices: string[]; spof_cables: string[]; score: number; rationale: Rationale[] }

export interface Bundle {
  design: Design;
  graph: { nodes: GraphNode[]; edges: GraphEdge[] };
  configs: Record<string, string>;
  verification: Verification;
  lint: LintReport;
  bom: Bom;
  spof: Spof;
}

export interface Hop { device: string; in_if: string | null; out_if: string | null; action: string; detail: string }
export interface Trace { src: string; dst: string; proto: string; port: number | null; outcome: string; reason: string; hops: Hop[] }

export interface FlowChange { src: string; dst: string; before: string; after: string; before_path: string[]; after_path: string[]; reason: string }
export interface WhatIf { failed: string[]; broken: FlowChange[]; rerouted: FlowChange[]; unaffected: number; rationale: Rationale[]; survives: boolean }

export interface NLResult { source: string; input: DesignInput; valid: boolean; errors: { loc: string; msg: string }[]; assumptions: string[]; missing: string[]; note: string }

export interface DiffResult {
  decisions: { key: string; change: string; old: string[]; new: string[] }[];
  subnets: { name: string; change: string; old: string | null; new: string | null }[];
  configs: Record<string, string>;
  devices_added: string[];
  devices_removed: string[];
  empty: boolean;
}

export interface ApiError { type: string; message: string; details?: Record<string, unknown> }
