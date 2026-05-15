import { useMemo } from "react";
import { useDashboard } from "../state/DashboardContext";
import type { GrowthPathRow, GrowthWindowDelta } from "../lib/types";
import { cn, fmt } from "../lib/utils";

function formatDeltaGb(gb: number | null): string {
  if (gb === null) return "—";
  if (Math.abs(gb) < 0.01) return "0";
  const sign = gb > 0 ? "+" : "";
  return `${sign}${fmt(gb)} GB`;
}

function formatDeltaPct(d: GrowthWindowDelta): string {
  if (d.gb === null || d.pct === null) return "";
  if (Math.abs(d.gb) < 0.01 && Math.abs(d.pct) < 0.05) return "";
  const sign = d.pct > 0 ? "+" : "";
  return `${sign}${fmt(d.pct, 1)}%`;
}

function DeltaCell({
  d, diskUsed,
}: {
  d: GrowthWindowDelta;
  diskUsed?: boolean;
}) {
  if (d.gb === null || d.pct === null) {
    return (
      <span className="tabular-nums text-[11px] text-fg-faint" title="Need more samples (~30s apart)">
        —
      </span>
    );
  }

  const growing = d.gb > 0;
  const hot = Math.abs(d.pct) >= 10 || Math.abs(d.gb) >= 1;
  const diskFill = diskUsed && growing;

  const tone = diskFill || (growing && hot)
    ? "text-danger"
    : growing
      ? "text-warn"
      : d.gb < 0
        ? "text-safe"
        : "text-fg-dim";

  const pctStr = formatDeltaPct(d);

  return (
    <span
      className={cn("tabular-nums text-[11px] font-semibold leading-tight", tone)}
      title={`${formatDeltaGb(d.gb)}${pctStr ? ` (${pctStr})` : ""}${d.partial ? " · shorter history than full window" : ""}`}
    >
      {formatDeltaGb(d.gb)}
      {pctStr ? (
        <span className="font-normal text-fg-faint ml-0.5">({pctStr})</span>
      ) : null}
      {d.partial ? <span className="text-fg-faint font-normal">*</span> : null}
    </span>
  );
}

function sortedPaths(rows: GrowthPathRow[], topIds: string[]): GrowthPathRow[] {
  const byId = new Map(rows.map((r) => [r.id, r]));
  const out: GrowthPathRow[] = [];
  const seen = new Set<string>();
  for (const id of topIds) {
    const r = byId.get(id);
    if (r && !seen.has(r.id)) {
      out.push(r);
      seen.add(r.id);
    }
  }
  const rest = rows
    .filter((r) => !seen.has(r.id))
    .sort((a, b) => a.label.localeCompare(b.label));
  return [...out, ...rest];
}

/** Plan 0027 — rolling 3m / 9m / 20m directory + disk growth from /api/growth + SSE. */
export function GrowthWatch() {
  const { growth } = useDashboard();

  const ordered = useMemo(() => {
    if (!growth?.paths?.length) return [];
    return sortedPaths(growth.paths, growth.top_ids_m3 ?? []);
  }, [growth]);

  if (!growth?.paths?.length) {
    return (
      <section
        className="mb-4 rounded-lg border border-border/15 p-4 shadow-sm"
        style={{ background: "hsl(var(--bg-2) / 0.55)" }}
      >
        <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-fg-faint mb-1">
          Growth watch
        </div>
        <p className="text-[12px] text-fg-dim m-0">Sampling disk and key folders… refresh in a moment.</p>
      </section>
    );
  }

  return (
    <section
      className="mb-4 rounded-lg border border-border/15 p-4 shadow-sm"
      style={{ background: "hsl(var(--bg-2) / 0.55)" }}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2 mb-2">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-fg-faint">
            Growth watch
          </div>
          <p className="text-[12px] text-fg-dim mt-0.5 mb-0 max-w-[640px] leading-[1.5]">
            Change in size vs ~3 min, ~9 min, and ~20 min ago (from ~{growth.sample_interval_sec}s samples). Rows are ordered with the largest 3m movers first. * = not enough history for the full window yet.
          </p>
        </div>
      </div>

      <div
        className="overflow-x-auto rounded-md border border-border/10"
        style={{ maxHeight: "320px", overflowY: "auto", minHeight: "120px" }}
      >
        <table className="w-full border-collapse text-[12px]">
          <thead>
            <tr className="border-b border-border/15 text-left text-[10px] uppercase tracking-[0.06em] text-fg-faint sticky top-0 bg-[hsl(var(--bg-2))] z-[1]">
              <th className="py-2 px-2 font-semibold">Location</th>
              <th className="py-2 px-2 font-semibold whitespace-nowrap text-right">Now</th>
              <th className="py-2 px-2 font-semibold whitespace-nowrap text-right">3 min Δ</th>
              <th className="py-2 px-2 font-semibold whitespace-nowrap text-right">9 min Δ</th>
              <th className="py-2 px-2 font-semibold whitespace-nowrap text-right pr-3">20 min Δ</th>
            </tr>
          </thead>
          <tbody>
            {ordered.map((row) => (
              <tr
                key={row.id}
                className={cn(
                  "border-b border-border/[0.08]",
                  row.disk_used && "bg-[hsl(var(--danger)/0.06)]",
                )}
              >
                <td className="py-2 px-2 align-top">
                  <div className="font-semibold text-fg leading-snug">{row.label}</div>
                  {row.path ? (
                    <div className="font-mono text-[10px] text-fg-faint mt-0.5 break-all">{row.path}</div>
                  ) : null}
                </td>
                <td className="py-2 px-2 align-top text-right tabular-nums text-fg-dim whitespace-nowrap">
                  {fmt(row.current_gb)} GB
                </td>
                <td className="py-2 px-2 align-top text-right whitespace-nowrap">
                  <DeltaCell d={row.deltas.m3} diskUsed={row.disk_used} />
                </td>
                <td className="py-2 px-2 align-top text-right whitespace-nowrap">
                  <DeltaCell d={row.deltas.m9} diskUsed={row.disk_used} />
                </td>
                <td className="py-2 px-2 align-top text-right pr-3 whitespace-nowrap">
                  <DeltaCell d={row.deltas.m20} diskUsed={row.disk_used} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
