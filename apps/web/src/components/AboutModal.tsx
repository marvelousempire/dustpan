import * as Dialog from "@radix-ui/react-dialog";
import { motion, AnimatePresence } from "motion/react";
import { X, ShieldCheck } from "./icons";
import { useDashboard } from "../state/DashboardContext";

interface Props {
  open: boolean;
  onClose: () => void;
}

/**
 * About modal — tells the user what Dustpan is, why it was created, and who built it.
 *
 * v0.19.0 — added in the Dustpan rebrand. Uses the flex-centered Overlay pattern
 * (v0.18.6) so the dialog stays pixel-perfect centered at every viewport size.
 * Motion is springy + slow-confident (premium feel): scale 0.94 → 1 with a soft
 * spring, not a snappy ease-out, so the modal "lands" rather than "pops in".
 */
export function AboutModal({ open, onClose }: Props) {
  const { status } = useDashboard();

  return (
    <Dialog.Root open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <Dialog.Portal>
        <AnimatePresence>
          {open && (
            <Dialog.Overlay asChild>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.22 }}
                className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto px-4 py-10 backdrop-blur-xl"
                style={{ background: "hsl(240 5% 4% / 0.62)" }}
              >
                <Dialog.Content asChild>
                  <motion.div
                    initial={{ opacity: 0, scale: 0.94, y: 12 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.96, y: 6 }}
                    transition={{ type: "spring", stiffness: 180, damping: 22, mass: 0.9 }}
                    className="relative flex w-full max-w-[560px] max-h-[88vh] flex-col overflow-hidden rounded-2xl border border-border/15 bg-bg-1 shadow-2xl"
                  >
                    {/* Title bar */}
                    <header className="flex items-center justify-between border-b border-border/10 px-6 py-4">
                      <Dialog.Title className="m-0 inline-flex items-center gap-2 text-[14px] font-semibold tracking-[-0.005em] text-fg-dim">
                        <svg
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth={1.6}
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          aria-hidden
                          className="w-4 h-4 text-accent"
                        >
                          <path d="m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.2 1.2 0 0 0 1.72 0L21.64 5.36a1.2 1.2 0 0 0 0-1.72"/>
                          <path d="m14 7 3 3"/>
                        </svg>
                        About Dustpan
                      </Dialog.Title>
                      <Dialog.Close
                        className="rounded-md p-1 text-fg-dim hover:bg-bg-3 hover:text-fg transition-colors"
                        aria-label="Close"
                      >
                        <X className="w-4 h-4" />
                      </Dialog.Close>
                    </header>

                    {/* Body */}
                    <div className="overflow-y-auto px-7 py-7">
                      {/* Hero */}
                      <div className="mb-6 text-center">
                        <h2
                          className="m-0 font-display font-semibold tracking-[-0.028em] leading-none text-fg"
                          style={{ fontSize: 44 }}
                        >
                          Dustpan
                        </h2>
                        <p className="m-0 mt-2.5 text-[13px] font-medium uppercase tracking-[0.16em] text-fg-faint">
                          by AVERY GOODMAN
                        </p>
                        <p className="m-0 mt-5 text-[16px] leading-[1.4] tracking-[-0.005em] text-fg">
                          Sweep your Mac clean.
                        </p>
                      </div>

                      {/* What it is */}
                      <section className="mb-5">
                        <h3 className="m-0 mb-2 text-[10px] font-semibold uppercase tracking-[0.1em] text-fg-faint">
                          What it is
                        </h3>
                        <p className="m-0 text-[13px] leading-[1.65] text-fg-dim">
                          A disk-cleanup utility for working Macs. Eleven categories — Xcode, Docker,
                          LLM tools, browsers, downloads, creative apps, archives, system caches, and
                          more. Every action carries a plain-English cost annotation so you know
                          exactly what you lose before you click anything.
                        </p>
                      </section>

                      {/* Why it exists */}
                      <section className="mb-5">
                        <h3 className="m-0 mb-2 text-[10px] font-semibold uppercase tracking-[0.1em] text-fg-faint">
                          Why it exists
                        </h3>
                        <p className="m-0 text-[13px] leading-[1.65] text-fg-dim">
                          Closed-source cleaners hide what they do and charge yearly for the privilege.
                          Dustpan is auditable end-to-end — every line is open. Safe by default — it
                          never deletes anything irreversible without surfacing the cost first. Fast — a
                          pure Python backend with zero pip installs, zero Docker, zero cloud, zero
                          telemetry. The cleanup logic is one readable AppleScript and one Python file
                          — you can fork it on a Sunday.
                        </p>
                      </section>

                      {/* Who built it */}
                      <section className="mb-2">
                        <h3 className="m-0 mb-2 text-[10px] font-semibold uppercase tracking-[0.1em] text-fg-faint">
                          Who built it
                        </h3>
                        <p className="m-0 text-[13px] leading-[1.65] text-fg-dim">
                          Crafted by AVERY GOODMAN at Learn Mappers LLC. Free. Open source. MIT
                          licensed. Made for developers, creative pros, and anyone tired of paying
                          rent to free up their own disk.
                        </p>
                      </section>

                      {/* Privacy line */}
                      <div className="mt-6 inline-flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.08em] text-fg-faint">
                        <ShieldCheck className="w-3 h-3 text-safe" aria-hidden />
                        Localhost only — nothing leaves your Mac
                      </div>
                    </div>

                    {/* Footer */}
                    <footer className="border-t border-border/10 px-6 py-3 text-center text-[10px] text-fg-faint tracking-[0.01em]">
                      {status?.version ? <>Dustpan {status.version} · </> : null}
                      © 2026 Learn Mappers LLC DBA AVERY GOODMAN · UCC 1-308
                    </footer>
                  </motion.div>
                </Dialog.Content>
              </motion.div>
            </Dialog.Overlay>
          )}
        </AnimatePresence>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
