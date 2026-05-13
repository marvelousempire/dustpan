import { motion, AnimatePresence } from "motion/react";
import { useDashboard } from "../state/DashboardContext";
import { TabIcon } from "./icons";
import { fmt } from "../lib/utils";

/**
 * Surfaces habit alerts when a category is projected to hit its cleanup
 * threshold within 14 days. One chip per at-risk category, sorted by
 * urgency (fewest days first).
 *
 * Only visible when:
 *   1. The DB is available (Docker mode) — habits are computed from snapshots
 *   2. At least one category has days_to_threshold <= 14
 */
export function HabitBanner() {
  const { habits, aiStatus, setActiveTab } = useDashboard();

  if (!aiStatus?.docker_mode) return null;

  const urgent = habits
    .filter((h) => h.days_to_threshold <= 14 && h.growth_gb_per_week > 0)
    .sort((a, b) => a.days_to_threshold - b.days_to_threshold);

  if (urgent.length === 0) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -6 }}
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        className="mb-4 flex flex-col gap-2"
        aria-label="Habit alerts"
      >
        {urgent.map((h) => (
          <button
            key={h.category}
            type="button"
            onClick={() => setActiveTab(h.category)}
            className="flex w-full items-start gap-3 rounded-lg border border-warn/30 bg-[hsl(var(--warn)/0.07)] px-4 py-3 text-left transition-colors hover:border-warn/50 hover:bg-[hsl(var(--warn)/0.12)]"
          >
            <TabIcon tabId={h.category} className="mt-0.5 h-4 w-4 flex-shrink-0 text-warn" />
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-baseline gap-x-1.5 gap-y-0.5">
                <span className="text-[13px] font-semibold text-warn capitalize">
                  {h.category}
                </span>
                <span className="text-[12px] text-fg-dim">
                  growing <strong className="font-semibold text-fg">
                    +{fmt(h.growth_gb_per_week)} GB/week
                  </strong>
                </span>
                {h.days_to_threshold < 9999 && (
                  <span className="text-[12px] text-fg-dim">
                    · threshold in{" "}
                    <strong className="font-semibold text-warn">
                      ~{h.days_to_threshold}d
                    </strong>
                  </span>
                )}
              </div>
              {h.recommendation && (
                <p className="mt-1 text-[12px] leading-[1.5] text-fg-dim">
                  {h.recommendation}
                </p>
              )}
            </div>
            <span className="flex-shrink-0 text-[11px] text-fg-faint">
              Open →
            </span>
          </button>
        ))}
      </motion.div>
    </AnimatePresence>
  );
}
