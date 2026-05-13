import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { useDashboard } from "../state/DashboardContext";
import { X } from "./icons";

const LS_KEY = "dustpan-fda-dismissed-v1";

/**
 * Shows a Full Disk Access banner when any scanned category reports
 * permission_denied_count > 0.
 *
 * macOS TCC (Transparency, Consent, and Control) blocks `du` from reading
 * many key directories without FDA granted to the terminal app:
 *   ~/Downloads, ~/Library/Containers/*, ~/Library/Group Containers/*,
 *   Notes, Safari, device backups, iCloud Drive, and more.
 *
 * Without FDA those directories silently report 0 GB even when full.
 */
export function PermissionBanner() {
  const { scans } = useDashboard();
  const [dismissed, setDismissed] = useState(
    () => !!localStorage.getItem(LS_KEY),
  );

  // Collect every denied path label across all scanned categories.
  const deniedPaths: string[] = [];
  const deniedCategories: string[] = [];
  for (const [catId, cache] of Object.entries(scans)) {
    const count = cache.scan.permission_denied_count ?? 0;
    if (count > 0) {
      deniedCategories.push(cache.scan.label);
      (cache.scan.permission_denied_paths ?? []).forEach((p) => {
        if (!deniedPaths.includes(p)) deniedPaths.push(p);
      });
    }
  }

  const show = deniedPaths.length > 0 && !dismissed;

  function dismiss() {
    localStorage.setItem(LS_KEY, "1");
    setDismissed(true);
  }

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          className="mb-4 rounded-lg border border-warn/40 bg-[hsl(var(--warn)/0.08)] px-5 py-4"
          role="alert"
        >
          <div className="flex items-start gap-3">
            <span className="text-[18px] flex-shrink-0" aria-hidden>🔐</span>
            <div className="flex-1 min-w-0">
              <div className="text-[13px] font-semibold text-warn mb-1">
                Full Disk Access needed for accurate results
              </div>
              <p className="text-[12px] leading-[1.6] text-fg-dim mb-3">
                macOS blocks <code className="rounded bg-[hsl(var(--bg-3)/0.8)] px-1 font-mono text-[11px]">du</code> from reading
                protected directories without Full Disk Access granted to your terminal app.
                The sections below reported <strong className="font-semibold text-fg">0 GB</strong> even
                though data exists — they'll show real sizes once you grant access.
              </p>

              {/* Affected paths */}
              <div className="mb-3 flex flex-wrap gap-1.5">
                {deniedPaths.slice(0, 12).map((p) => (
                  <span
                    key={p}
                    className="rounded-full border border-warn/30 bg-[hsl(var(--warn)/0.10)] px-2 py-0.5 text-[11px] text-warn"
                  >
                    {p}
                  </span>
                ))}
                {deniedPaths.length > 12 && (
                  <span className="text-[11px] text-fg-faint self-center">
                    +{deniedPaths.length - 12} more
                  </span>
                )}
              </div>

              {/* Fix instructions */}
              <div className="rounded-md border border-border/20 bg-[hsl(var(--bg-2)/0.7)] px-4 py-3">
                <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-fg-faint">
                  How to fix — one-time setup
                </div>
                <ol className="list-decimal list-inside space-y-1 text-[12px] text-fg-dim">
                  <li>
                    Open{" "}
                    <strong className="font-semibold text-fg">
                      System Settings → Privacy &amp; Security → Full Disk Access
                    </strong>
                  </li>
                  <li>
                    Click <strong className="font-semibold text-fg">+</strong> and
                    add your terminal app (Terminal, iTerm2, Warp, Ghostty, etc.)
                  </li>
                  <li>
                    <strong className="font-semibold text-fg">Quit and reopen</strong>{" "}
                    your terminal, then run{" "}
                    <code className="rounded bg-[hsl(var(--bg-3)/0.8)] px-1 font-mono text-[10px]">
                      make ui
                    </code>{" "}
                    again
                  </li>
                  <li>
                    Click <strong className="font-semibold text-fg">Re-scan everything</strong>{" "}
                    — real sizes will appear
                  </li>
                </ol>
              </div>
            </div>

            <button
              type="button"
              onClick={dismiss}
              className="flex-shrink-0 rounded p-1 text-fg-faint hover:bg-[hsl(var(--bg-3)/0.6)] hover:text-fg transition-colors"
              title="Dismiss (don't show again)"
              aria-label="Dismiss"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
