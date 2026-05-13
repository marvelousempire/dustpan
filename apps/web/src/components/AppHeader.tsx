import type { DiskStatus } from "../lib/types";

interface Props {
  status: DiskStatus | null;
  onOpenChangelog: () => void;
}

/**
 * Dustpan header — wand-sparkles glyph + wordmark + "by AVERY GOODMAN" attribution.
 * v0.19.0 rebrand from "Cleanup Hub".
 */
export function AppHeader({ status, onOpenChangelog }: Props) {
  return (
    <header className="flex items-end gap-3 mb-5 px-1">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.6}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden
        className="w-[26px] h-[26px] text-accent flex-shrink-0 mb-[2px]"
      >
        <path d="m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.2 1.2 0 0 0 1.72 0L21.64 5.36a1.2 1.2 0 0 0 0-1.72" />
        <path d="m14 7 3 3" />
        <path d="M5 6v4" />
        <path d="M19 14v4" />
        <path d="M10 2v2" />
        <path d="M7 8H3" />
        <path d="M21 16h-4" />
        <path d="M11 3H9" />
      </svg>
      <div className="flex items-baseline gap-2">
        <h1
          className="m-0 font-display font-semibold tracking-[-0.022em] leading-none"
          style={{ fontSize: 22 }}
        >
          Dustpan
        </h1>
        <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-fg-faint leading-none">
          by AVERY GOODMAN
        </span>
      </div>
      <button
        type="button"
        onClick={onOpenChangelog}
        title="Click to view changelog"
        className="ml-auto px-2.5 py-1.5 rounded-full text-[11px] text-fg-dim tabular border border-transparent hover:bg-bg-3 hover:border-border hover:text-fg transition-colors duration-150"
      >
        {status?.version ? `${status.version} · localhost` : "…"}
      </button>
    </header>
  );
}
