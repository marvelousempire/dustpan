import { useMemo } from "react";
import { motion } from "motion/react";
import { useDashboard } from "../state/DashboardContext";
import { TabIcon } from "./icons";
import { fmt } from "../lib/utils";

function stripGlyph(s: string) {
  return s.replace(/^[\p{Extended_Pictographic}\p{Emoji}☀-➿]+\s*/u, "").trim() || s;
}

/**
 * Animated horizontal stacked bar chart showing disk space usage per category.
 * Each row: [icon · label] | [████ safe ░░ opt-in ▒▒ caution] | X.X GB · Y%
 *
 * Bars animate in on mount with a staggered spring entrance.
 * Only renders once at least one category has been scanned.
 */
export function SpaceBarChart() {
  const { tabs, scans } = useDashboard();

  // Build rows from scanned categories only.
  const rows = useMemo(() => {
    const out: Array<{
      id: string;
      label: string;
      safe: number;
      optin: number;
      caution: number;
      total: number;
    }> = [];
    for (const tab of tabs) {
      if (tab.meta) continue;
      let safe = 0, optin = 0, caution = 0;
      if (tab.subcategories) {
        for (const sub of tab.subcategories) {
          const s = scans[sub]?.scan;
          if (s) {
            safe += s.totals.safe || 0;
            optin += s.totals.probably_safe || 0;
            caution += s.totals.caution || 0;
          }
        }
      } else if (tab.category) {
        const s = scans[tab.category]?.scan;
        if (s) {
          safe = s.totals.safe || 0;
          optin = s.totals.probably_safe || 0;
          caution = s.totals.caution || 0;
        }
      }
      const total = safe + optin + caution;
      // Only include tabs that have been scanned (even if total is 0).
      const scanned = tab.subcategories
        ? tab.subcategories.some((sub) => !!scans[sub])
        : !!scans[tab.category ?? ""];
      if (!scanned) continue;
      out.push({ id: tab.id, label: stripGlyph(tab.label), safe, optin, caution, total });
    }
    // Sort by total descending.
    return out.sort((a, b) => b.total - a.total);
  }, [tabs, scans]);

  if (rows.length === 0) return null;

  const grandTotal = rows.reduce((s, r) => s + r.total, 0);
  const maxTotal = rows[0]?.total ?? 1; // largest row = 100% of bar track

  return (
    <section
      className="glass mb-4 rounded-lg border border-border/20 p-5 shadow-sm"
      aria-label="Space usage by category"
    >
      <div className="mb-3 text-[10px] font-semibold uppercase tracking-[0.08em] text-fg-faint">
        Space breakdown
      </div>
      <div className="flex flex-col gap-2.5">
        {rows.map((row, idx) => {
          const pctOfTotal = grandTotal > 0 ? (row.total / grandTotal) * 100 : 0;
          // Each segment's width is its share of the bar track (which goes to maxTotal).
          const barPct = maxTotal > 0 ? (row.total / maxTotal) * 100 : 0;
          const safePct  = row.total > 0 ? (row.safe   / row.total) * 100 : 0;
          const optinPct = row.total > 0 ? (row.optin  / row.total) * 100 : 0;
          const cautPct  = row.total > 0 ? (row.caution/ row.total) * 100 : 0;

          return (
            <div key={row.id} className="flex items-center gap-3">
              {/* Label — fixed width so bars align */}
              <div className="flex w-[130px] flex-shrink-0 items-center gap-1.5 truncate">
                <TabIcon tabId={row.id} className="h-3.5 w-3.5 flex-shrink-0 text-accent" />
                <span className="truncate text-[12px] font-medium text-fg-dim">{row.label}</span>
              </div>

              {/* Bar track */}
              <div className="relative flex-1 h-5 overflow-hidden rounded-sm bg-[hsl(var(--bg-3)/0.7)]">
                {/* Outer container animates to barPct width */}
                <motion.div
                  className="absolute inset-y-0 left-0 flex overflow-hidden rounded-sm"
                  initial={{ width: 0 }}
                  animate={{ width: `${barPct}%` }}
                  transition={{ delay: 0.05 * idx, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                >
                  {row.safe > 0 && (
                    <div
                      className="h-full"
                      style={{ width: `${safePct}%`, background: "hsl(var(--safe) / 0.85)" }}
                    />
                  )}
                  {row.optin > 0 && (
                    <div
                      className="h-full"
                      style={{ width: `${optinPct}%`, background: "hsl(var(--warn) / 0.75)" }}
                    />
                  )}
                  {row.caution > 0 && (
                    <div
                      className="h-full"
                      style={{ width: `${cautPct}%`, background: "hsl(var(--danger) / 0.55)" }}
                    />
                  )}
                </motion.div>
              </div>

              {/* Stats — fixed width so columns align */}
              <motion.div
                className="w-[100px] flex-shrink-0 text-right"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.05 * idx + 0.45, duration: 0.3 }}
              >
                <span className="text-[12px] font-semibold tabular text-fg">
                  {fmt(row.total)} GB
                </span>
                <span className="ml-1.5 text-[11px] tabular text-fg-faint">
                  {pctOfTotal.toFixed(0)}%
                </span>
              </motion.div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-fg-faint">
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded-sm" style={{ background: "hsl(var(--safe) / 0.85)" }} />
          Safe to delete
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded-sm" style={{ background: "hsl(var(--warn) / 0.75)" }} />
          Opt-in
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-4 rounded-sm" style={{ background: "hsl(var(--danger) / 0.55)" }} />
          Caution
        </span>
        <span className="ml-auto tabular">
          {fmt(grandTotal)} GB monitored total
        </span>
      </div>
    </section>
  );
}
