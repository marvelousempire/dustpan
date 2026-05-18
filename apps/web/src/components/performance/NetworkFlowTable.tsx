import type { PerformanceNetworkRow } from "../../lib/types";

export function NetworkFlowTable({ title, rows }: { title: string; rows: PerformanceNetworkRow[] }) {
  const meter = Math.min((rows.length / 24) * 100, 100);
  return (
    <div className="min-w-0">
      <div className="mb-2 flex items-center justify-between gap-2 text-[11px]">
        <span className="font-semibold uppercase tracking-[0.08em] text-fg-faint">{title}</span>
        <span className="tabular font-bold text-accent">{rows.length}</span>
      </div>
      <div className="mb-2 h-1.5 overflow-hidden rounded-full bg-[hsl(var(--bg-3))]">
        <div className="h-full rounded-full bg-accent" style={{ width: `${Math.max(meter, rows.length ? 4 : 0)}%` }} />
      </div>
      <div className="max-h-[280px] overflow-auto rounded-md border border-border/10">
        {rows.length ? rows.slice(0, 14).map((row, idx) => (
          <div key={`${row.pid}-${row.name}-${idx}`} className="border-b border-border/10 px-3 py-1.5 last:border-b-0">
            <div className="flex items-center justify-between gap-2">
              <span className="truncate text-[12px] font-semibold text-fg">{row.command}</span>
              <span className="flex items-center gap-1.5 text-[10px] tabular text-fg-faint">
                {row.scope ? <span className="rounded-full bg-accent/10 px-1.5 py-0.5 font-bold text-accent">{row.scope}</span> : null}
                pid {row.pid}
              </span>
            </div>
            <div className="mt-0.5 truncate text-[10px] tabular text-fg-dim">{row.name}</div>
            {row.remote ? <div className="mt-0.5 truncate text-[10px] tabular text-fg-faint">remote: {row.remote}</div> : null}
          </div>
        )) : (
          <div className="px-3 py-6 text-center text-[12px] text-fg-faint">No rows visible.</div>
        )}
      </div>
    </div>
  );
}
