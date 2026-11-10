import { useMemo } from "react";
import type { GraphEdge, GraphNode } from "./types";

const MEDIA_CLASS: [string, string][] = [
  ["OS2", "m-os2"],
  ["OM4", "m-om4"],
  ["handoff", "m-wan"],
  ["Cat6a", "m-cu"],
];

function mediaClass(media: string): string {
  return MEDIA_CLASS.find(([k]) => media.includes(k))?.[1] ?? "m-cu";
}

export function edgeId(e: GraphEdge): string {
  return `${e.a}:${e.a_if}--${e.b}:${e.b_if}`;
}

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
  path?: string[];
  failed?: string[];
  spof?: string[];
  onNode?: (id: string) => void;
  onEdge?: (e: GraphEdge) => void;
}

export function Topology({ nodes, edges, path = [], failed = [], spof = [], onNode, onEdge }: Props) {
  const pos = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes]);
  const box = useMemo(() => {
    const xs = nodes.map((n) => n.x);
    const ys = nodes.map((n) => n.y);
    const pad = 90;
    return { x: Math.min(...xs) - pad, y: Math.min(...ys) - pad, w: Math.max(...xs) - Math.min(...xs) + 2 * pad, h: Math.max(...ys) - Math.min(...ys) + 2 * pad };
  }, [nodes]);
  const onPath = (a: string, b: string) => {
    for (let i = 0; i + 1 < path.length; i++) {
      if ((path[i] === a && path[i + 1] === b) || (path[i] === b && path[i + 1] === a)) return true;
    }
    return false;
  };
  // parallel cables between the same pair are fanned out so each stays clickable
  const seen = new Map<string, number>();

  return (
    <figure className="topology">
      <svg viewBox={`${box.x} ${box.y} ${box.w} ${box.h}`} role="img" aria-label="Network topology">
        {edges.map((e) => {
          const a = pos.get(e.a);
          const b = pos.get(e.b);
          if (!a || !b) return null;
          const pair = [e.a, e.b].sort().join("|");
          const k = seen.get(pair) ?? 0;
          seen.set(pair, k + 1);
          const off = k * 14;
          const id = edgeId(e);
          const cls = [
            "edge", mediaClass(e.media), `k-${e.kind}`,
            onPath(e.a, e.b) ? "on-path" : "",
            failed.includes(id) ? "failed" : "",
            spof.includes(id) ? "spof" : "",
          ].join(" ");
          return (
            <line key={id} className={cls} x1={a.x + off} y1={a.y} x2={b.x + off} y2={b.y} onClick={() => onEdge?.(e)}>
              <title>{`${e.a} ${e.a_if} ↔ ${e.b} ${e.b_if}\n${e.kind}, ${e.media}`}</title>
            </line>
          );
        })}
        {nodes.map((n) => {
          const cls = [
            "node", `r-${n.role}`,
            path.includes(n.id) ? "on-path" : "",
            failed.includes(n.id) ? "failed" : "",
            spof.includes(n.id) ? "spof" : "",
          ].join(" ");
          return (
            <g key={n.id} className={cls} transform={`translate(${n.x},${n.y})`} onClick={() => onNode?.(n.id)}>
              <rect x={-62} y={-16} width={124} height={32} rx={6} />
              <text textAnchor="middle" dy="0.35em">{n.id.length > 18 ? n.id.slice(0, 17) + "…" : n.id}</text>
              <title>{`${n.id} (${n.role}, ${n.site})`}</title>
            </g>
          );
        })}
      </svg>
      <figcaption className="legend">
        <span className="sw m-cu" /> Cat6a <span className="sw m-om4" /> OM4 <span className="sw m-os2" /> OS2
        <span className="sw m-wan" /> carrier / internet <span className="dash" /> trunk
        <span className="sw on-path" /> traced path <span className="sw failed" /> failed <span className="sw spof" /> single point of failure
      </figcaption>
    </figure>
  );
}
