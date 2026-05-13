import { motion, AnimatePresence } from "motion/react";
import { useDashboard } from "../state/DashboardContext";
import { fmt } from "../lib/utils";

/**
 * RescueBanner — shown when free disk is critically low (< 10 GB or < 5% free).
 *
 * Before scan: shows hard-coded "best bet" items (biggest paths on any Mac,
 * no scan data needed) so the user can act immediately.
 *
 * After scan: shows the actual top items from the doctor report with real sizes.
 */

// Hard-coded best bets — shown before any scan when disk is critically low.
const BEST_BETS = [
  { label: "Xcode DerivedData",       estimate: "5–20 GB",  category: "xcode",       hint: "safe — Xcode rebuilds on next build" },
  { label: "Xcode iOS DeviceSupport", estimate: "2–10 GB",  category: "xcode",       hint: "safe — re-downloads when device connects" },
  { label: "Xcode DocumentationIndex", estimate: "1–5 GB",  category: "xcode",       hint: "safe — Xcode rebuilds when you open docs" },
  { label: "Browser caches + WebKit", estimate: "1–10 GB",  category: "browsers",    hint: "safe — pages reload from origin" },
  { label: "npm cache (~/.npm)",      estimate: "0.5–5 GB", category: "space-eaters",hint: "safe — npm re-downloads on next install" },
];

export function RescueBanner() {
  const { status, doctorReport, setActiveTab, scanning } = useDashboard();

  const freeGb    = status?.free_gb ?? Infinity;
  const freePct   = status && status.total_gb > 0
    ? (status.free_gb / status.total_gb) * 100 : 100;

  const critical  = freePct < 5  || freeGb < 5;
  const warning   = freePct < 15 || freeGb < 10;

  if (!critical && !warning) return null;

  const hasScanned  = (doctorReport?.categories_scanned ?? 0) > 0;
  const topItems    = (doctorReport?.quick_wins ?? []).slice(0, 5);
  const totalSavable = doctorReport?.total_cleanable_gb ?? 0;

  const bgColor     = critical
    ? "border-danger/40 bg-[hsl(var(--danger)/0.07)]"
    : "border-warn/40 bg-[hsl(var(--warn)/0.07)]";
  const textColor   = critical ? "text-danger" : "text-warn";
  const icon        = critical ? "🚨" : "⚠️";
  const headline    = critical
    ? `Disk critically full — ${fmt(freeGb)} GB (${freePct.toFixed(0)}%) free`
    : `Disk running low — ${fmt(freeGb)} GB (${freePct.toFixed(0)}%) free`;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        className={`mb-4 rounded-lg border p-5 ${bgColor}`}
        role="alert"
      >
        {/* Header */}
        <div className="mb-3 flex items-center gap-2.5">
          <span className="text-[18px]" aria-hidden>{icon}</span>
          <div>
            <div className={`text-[13px] font-semibold ${textColor}`}>{headline}</div>
            {hasScanned && totalSavable > 0 && (
              <div className="text-[12px] text-fg-dim">
                Scan found{" "}
                <strong className="font-semibold text-fg">{fmt(totalSavable)} GB</strong>{" "}
                you can safely reclaim right now.
              </div>
            )}
            {!hasScanned && (
              <div className="text-[12px] text-fg-dim">
                {scanning
                  ? "Scanning now — biggest items will appear here…"
                  : "Click Re-scan everything to find exactly what to clean."}
              </div>
            )}
          </div>
        </div>

        {/* Items */}
        <div className="flex flex-col gap-1.5">
          {hasScanned && topItems.length > 0
            ? topItems.map((item, i) => (
                <RescueRow
                  key={item.path}
                  label={item.label}
                  detail={`${fmt(item.size_gb)} GB · ${item.category}`}
                  onOpen={() => setActiveTab(item.category)}
                  idx={i}
                  critical={critical}
                />
              ))
            : BEST_BETS.map((bet, i) => (
                <RescueRow
                  key={bet.label}
                  label={bet.label}
                  detail={`est. ${bet.estimate} · ${bet.hint}`}
                  onOpen={() => setActiveTab(bet.category)}
                  idx={i}
                  critical={critical}
                />
              ))}
        </div>

        {!hasScanned && (
          <p className="mt-3 text-[11px] text-fg-faint">
            Tap any row to open that category and clean it, or click{" "}
            <strong className="font-medium text-fg">Re-scan everything</strong>{" "}
            to get exact sizes first.
          </p>
        )}
      </motion.div>
    </AnimatePresence>
  );
}

function RescueRow({
  label, detail, onOpen, idx, critical,
}: {
  label: string;
  detail: string;
  onOpen: () => void;
  idx: number;
  critical: boolean;
}) {
  return (
    <motion.button
      type="button"
      onClick={onOpen}
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.05 * idx, duration: 0.25 }}
      className="flex w-full items-center gap-3 rounded-md border border-border/20 bg-[hsl(var(--bg-2)/0.6)] px-3.5 py-2.5 text-left transition-colors hover:border-accent"
    >
      <div className="flex-1 min-w-0">
        <div className="text-[12px] font-semibold text-fg truncate">{label}</div>
        <div className="text-[11px] text-fg-dim truncate">{detail}</div>
      </div>
      <span className={`flex-shrink-0 text-[11px] font-semibold ${critical ? "text-danger" : "text-warn"}`}>
        Open →
      </span>
    </motion.button>
  );
}
