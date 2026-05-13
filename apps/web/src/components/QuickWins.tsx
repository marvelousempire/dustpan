import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { useDashboard } from "../state/DashboardContext";
import { TabIcon } from "./icons";
import { fmt } from "../lib/utils";

/**
 * QuickWins — the "what to clean right now" panel.
 *
 * After a scan, aggregates every safe-tier path entry across ALL categories,
 * ranks by size descending, and shows the top 10 with one-click clean buttons.
 *
 * This is the answer to "what would an expert tell me to delete first?" — no
 * category navigation needed, no interpretation required.
 */
export function QuickWins() {
  const { doctorReport, cleanPath, busy } = useDashboard();

  const [doneItems, setDoneItems] = useState<Set<string>>(new Set());
  const [cleaningPath, setCleaningPath] = useState<string | null>(null);
  const prevBusyRef = useRef(busy);

  // When busy drops false→false after a clean, mark that item done.
  useEffect(() => {
    if (prevBusyRef.current && !busy && cleaningPath) {
      setDoneItems((prev) => new Set([...prev, cleaningPath]));
      setCleaningPath(null);
    }
    prevBusyRef.current = busy;
  }, [busy, cleaningPath]);

  const wins = doctorReport?.quick_wins ?? [];
  if (wins.length === 0) return null;

  // Filter out already-done items from the display.
  const active = wins.filter((w) => !doneItems.has(w.path));
  if (active.length === 0) return null;

  const totalSavable = active.reduce((s, w) => s + w.size_gb, 0);

  function handleClean(item: typeof wins[number]) {
    if (busy || doneItems.has(item.path)) return;
    setCleaningPath(item.path);
    cleanPath(item.category, item.path, item.label);
  }

  return (
    <section
      className="glass mb-4 rounded-lg border border-accent/25 bg-[hsl(var(--accent)/0.04)] p-5 shadow-sm"
      aria-label="Quick wins — biggest safe items to clean right now"
    >
      {/* Header */}
      <div className="mb-3 flex items-baseline gap-2 flex-wrap">
        <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-accent">
          Quick wins
        </div>
        <div className="text-[12px] text-fg-dim">
          Top {active.length} safe items across all categories ·{" "}
          <strong className="font-semibold text-fg">{fmt(totalSavable)} GB</strong>{" "}
          cleanable right now
        </div>
      </div>

      {/* Items */}
      <div className="flex flex-col gap-1.5">
        <AnimatePresence initial={false}>
          {active.slice(0, 10).map((item, idx) => {
            const isCleaning = cleaningPath === item.path && busy;
            const canClean = !busy && !doneItems.has(item.path);

            return (
              <motion.div
                key={item.path}
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                transition={{ delay: idx * 0.03, duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
                className="flex items-center gap-3 rounded-md border border-border/15 bg-[hsl(var(--bg-2)/0.65)] px-3.5 py-2.5"
              >
                {/* Category icon */}
                <TabIcon
                  tabId={item.category}
                  className="h-3.5 w-3.5 flex-shrink-0 text-accent"
                />

                {/* Label + path */}
                <div className="flex-1 min-w-0">
                  <div className="text-[12px] font-semibold text-fg truncate">
                    {item.label}
                  </div>
                  <div className="text-[10px] text-fg-faint truncate font-mono">
                    {item.path.replace(/^~/, "~")}
                  </div>
                </div>

                {/* Size */}
                <div className="flex-shrink-0 text-right">
                  <span className="text-[12px] font-semibold tabular text-fg">
                    {fmt(item.size_gb)} GB
                  </span>
                </div>

                {/* Clean button */}
                <motion.button
                  type="button"
                  disabled={!canClean}
                  onClick={() => handleClean(item)}
                  whileTap={canClean ? { scale: 0.95 } : undefined}
                  className="flex-shrink-0 rounded-md border border-accent/30 bg-[hsl(var(--accent)/0.1)] px-3 py-1.5 text-[11px] font-semibold text-accent transition-all hover:bg-[hsl(var(--accent)/0.2)] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {isCleaning ? "…" : "↓ Clean"}
                </motion.button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      <p className="mt-2.5 text-[11px] text-fg-faint">
        All items above are{" "}
        <strong className="font-medium text-fg">safe</strong> — auto-rebuilt by
        the app the next time you use it. No user files, no preferences, no
        history.
      </p>
    </section>
  );
}
