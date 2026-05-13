import { useState, useEffect, useCallback } from "react";
import { KeyRound, Cpu, Sparkles } from "./icons";
import { cn } from "../lib/utils";
import { useDashboard } from "../state/DashboardContext";
import { api } from "../lib/api";

// ─── Provider definitions ───────────────────────────────────────────────────

interface Provider {
  id: string;
  label: string;
  placeholder: string;
  docsUrl: string;
  keyPrefix?: string;   // expected key prefix for light validation
  isLocal?: boolean;    // Ollama-style: URL + model, not a key
}

const PROVIDERS: Provider[] = [
  {
    id: "openai",
    label: "OpenAI",
    placeholder: "sk-proj-…",
    keyPrefix: "sk-",
    docsUrl: "https://platform.openai.com/api-keys",
  },
  {
    id: "anthropic",
    label: "Anthropic",
    placeholder: "sk-ant-…",
    keyPrefix: "sk-ant-",
    docsUrl: "https://console.anthropic.com/settings/keys",
  },
  {
    id: "perplexity",
    label: "Perplexity",
    placeholder: "pplx-…",
    docsUrl: "https://www.perplexity.ai/settings/api",
  },
  {
    id: "groq",
    label: "Groq",
    placeholder: "gsk_…",
    docsUrl: "https://console.groq.com/keys",
  },
  {
    id: "gemini",
    label: "Gemini (Google)",
    placeholder: "AIza…",
    docsUrl: "https://aistudio.google.com/app/apikey",
  },
];

// ─── localStorage helpers ────────────────────────────────────────────────────

const LS_PREFIX = "dustpan-ai-";

function loadKey(providerId: string): string {
  return localStorage.getItem(`${LS_PREFIX}${providerId}-key`) ?? "";
}

function saveKey(providerId: string, value: string) {
  if (value.trim()) {
    localStorage.setItem(`${LS_PREFIX}${providerId}-key`, value.trim());
  } else {
    localStorage.removeItem(`${LS_PREFIX}${providerId}-key`);
  }
}

function loadOllama(): { url: string; model: string } {
  return {
    url: localStorage.getItem(`${LS_PREFIX}ollama-url`) ?? "http://localhost:11434",
    model: localStorage.getItem(`${LS_PREFIX}ollama-model`) ?? "llama3.2",
  };
}

function saveOllama(url: string, model: string) {
  localStorage.setItem(`${LS_PREFIX}ollama-url`, url);
  localStorage.setItem(`${LS_PREFIX}ollama-model`, model);
}

// ─── Sub-components ──────────────────────────────────────────────────────────

/** Server-mode provider row — saves/deletes via API, never exposes key value. */
function ServerProviderRow({ provider, configuredProviders, onChanged }: {
  provider: Provider;
  configuredProviders: string[];
  onChanged: () => void;
}) {
  const hasKey = configuredProviders.includes(provider.id);
  const [value, setValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [show, setShow] = useState(false);
  const [feedback, setFeedback] = useState<"saved" | "cleared" | null>(null);

  async function handleSave() {
    if (!value.trim()) return;
    setSaving(true);
    try {
      await api.saveKey(provider.id, value.trim());
      setValue("");
      setFeedback("saved");
      setTimeout(() => setFeedback(null), 2000);
      onChanged();
    } finally {
      setSaving(false);
    }
  }

  async function handleClear() {
    setSaving(true);
    try {
      await api.deleteKey(provider.id);
      setFeedback("cleared");
      setTimeout(() => setFeedback(null), 2000);
      onChanged();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex items-center gap-3 rounded-md border border-border/15 bg-[hsl(var(--bg-2)/0.6)] px-4 py-3">
      <div className="w-[130px] flex-shrink-0">
        <div className="text-[13px] font-semibold text-fg">{provider.label}</div>
        <a href={provider.docsUrl} target="_blank" rel="noopener noreferrer" className="text-[10px] text-accent hover:underline">
          Get API key →
        </a>
      </div>
      <div className="relative flex-1">
        {hasKey ? (
          <div className="flex items-center gap-2 rounded-md border border-border/20 bg-[hsl(var(--bg-1)/0.8)] px-3 py-2">
            <span className="text-[12px] text-fg-dim">••••••••••••  (stored securely)</span>
          </div>
        ) : (
          <>
            <input
              type={show ? "text" : "password"}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={provider.placeholder}
              className="w-full rounded-md border border-border/20 bg-[hsl(var(--bg-1)/0.8)] px-3 py-2 font-mono text-[12px] text-fg outline-none placeholder:text-fg-faint focus:border-accent"
              autoComplete="off" spellCheck={false}
              onKeyDown={(e) => { if (e.key === "Enter") void handleSave(); }}
            />
            <button type="button" onClick={() => setShow((s) => !s)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-fg-faint hover:text-fg" tabIndex={-1}>
              {show ? "hide" : "show"}
            </button>
          </>
        )}
      </div>
      <div className={cn("h-2 w-2 flex-shrink-0 rounded-full", hasKey ? "bg-safe" : "bg-fg-faint/30")}
        title={hasKey ? "Key stored on server" : "No key"} />
      <div className="flex flex-shrink-0 gap-1.5">
        {!hasKey && (
          <button type="button" onClick={handleSave} disabled={!value.trim() || saving}
            className="rounded-md bg-accent px-3 py-1.5 text-[11px] font-semibold text-white transition-colors hover:bg-accent-strong disabled:opacity-40">
            {feedback === "saved" ? "Saved ✓" : saving ? "…" : "Save"}
          </button>
        )}
        {hasKey && (
          <button type="button" onClick={handleClear} disabled={saving}
            className="rounded-md border border-border/20 px-2 py-1.5 text-[11px] text-fg-dim hover:text-fg disabled:opacity-40">
            {feedback === "cleared" ? "Cleared" : "Remove"}
          </button>
        )}
      </div>
    </div>
  );
}

/** localStorage-mode provider row — stores key in browser. */
function LocalProviderRow({ provider }: { provider: Provider }) {
  const [value, setValue] = useState(() => loadKey(provider.id));
  const [saved, setSaved] = useState(false);
  const [show, setShow] = useState(false);

  const hasKey = !!loadKey(provider.id);
  const dirty = value !== loadKey(provider.id);

  function handleSave() {
    saveKey(provider.id, value);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  function handleClear() {
    setValue("");
    saveKey(provider.id, "");
    setSaved(false);
  }

  return (
    <div className="flex items-center gap-3 rounded-md border border-border/15 bg-[hsl(var(--bg-2)/0.6)] px-4 py-3">
      <div className="w-[130px] flex-shrink-0">
        <div className="text-[13px] font-semibold text-fg">{provider.label}</div>
        <a href={provider.docsUrl} target="_blank" rel="noopener noreferrer" className="text-[10px] text-accent hover:underline">
          Get API key →
        </a>
      </div>
      <div className="relative flex-1">
        <input
          type={show ? "text" : "password"}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={provider.placeholder}
          className="w-full rounded-md border border-border/20 bg-[hsl(var(--bg-1)/0.8)] px-3 py-2 font-mono text-[12px] text-fg outline-none placeholder:text-fg-faint focus:border-accent"
          autoComplete="off" spellCheck={false}
        />
        <button type="button" onClick={() => setShow((s) => !s)}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-fg-faint hover:text-fg" tabIndex={-1}>
          {show ? "hide" : "show"}
        </button>
      </div>
      <div className={cn("h-2 w-2 flex-shrink-0 rounded-full", hasKey && !dirty ? "bg-safe" : "bg-fg-faint/30")}
        title={hasKey && !dirty ? "Key saved" : "No key"} />
      <div className="flex flex-shrink-0 gap-1.5">
        <button type="button" onClick={handleSave} disabled={!dirty && !value}
          className="rounded-md bg-accent px-3 py-1.5 text-[11px] font-semibold text-white transition-colors hover:bg-accent-strong disabled:opacity-40">
          {saved ? "Saved ✓" : "Save"}
        </button>
        {hasKey && (
          <button type="button" onClick={handleClear}
            className="rounded-md border border-border/20 px-2 py-1.5 text-[11px] text-fg-dim hover:text-fg">
            Clear
          </button>
        )}
      </div>
    </div>
  );
}

// Legacy alias for non-Docker mode
const ProviderRow = LocalProviderRow;

function OllamaRow() {
  const initial = loadOllama();
  const [url, setUrl] = useState(initial.url);
  const [model, setModel] = useState(initial.model);
  const [saved, setSaved] = useState(false);

  function handleSave() {
    saveOllama(url, model);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className="rounded-md border border-accent/30 bg-[hsl(var(--accent)/0.06)] px-4 py-4">
      <div className="mb-3 flex items-center gap-2">
        <Cpu className="h-4 w-4 text-accent" />
        <span className="text-[13px] font-semibold text-fg">Ollama — local models</span>
        <span className="ml-1 rounded-full border border-accent/30 px-2 py-0.5 text-[10px] font-medium text-accent">
          private · free
        </span>
      </div>
      <p className="mb-3 text-[12px] leading-[1.55] text-fg-dim">
        Runs entirely on your machine — no data leaves your computer. Works with
        any model Ollama supports (Llama 3.2, Mistral, Phi, etc.). For the best
        experience, run Ollama via the Docker stack so it starts automatically
        with <code className="rounded bg-[hsl(var(--bg-3)/0.8)] px-1 py-0.5 font-mono text-[11px]">./go</code>.
      </p>
      <div className="flex flex-wrap gap-3">
        <div className="flex-1 min-w-[200px]">
          <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-fg-faint">
            Ollama URL
          </label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="w-full rounded-md border border-border/20 bg-[hsl(var(--bg-1)/0.8)] px-3 py-2 font-mono text-[12px] text-fg outline-none placeholder:text-fg-faint focus:border-accent"
          />
        </div>
        <div className="w-[180px]">
          <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-fg-faint">
            Model
          </label>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="llama3.2"
            className="w-full rounded-md border border-border/20 bg-[hsl(var(--bg-1)/0.8)] px-3 py-2 font-mono text-[12px] text-fg outline-none placeholder:text-fg-faint focus:border-accent"
          />
        </div>
        <div className="flex items-end">
          <button
            type="button"
            onClick={handleSave}
            className="rounded-md bg-accent px-4 py-2 text-[11px] font-semibold text-white transition-colors hover:bg-accent-strong"
          >
            {saved ? "Saved ✓" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main panel ──────────────────────────────────────────────────────────────

export function AISettingsPanel() {
  const { aiStatus } = useDashboard();
  const dockerMode = aiStatus?.docker_mode ?? false;

  // Server-mode: track which providers have keys on the server.
  const [serverProviders, setServerProviders] = useState<string[]>(aiStatus?.providers ?? []);
  const refreshServerProviders = useCallback(() => {
    api.settingsKeys().then((d) => setServerProviders(d.providers ?? [])).catch(() => {});
  }, []);
  useEffect(() => {
    if (dockerMode) refreshServerProviders();
  }, [dockerMode, refreshServerProviders]);

  // Ollama state (server-backed when Docker mode, localStorage otherwise)
  const [ollamaUrl, setOllamaUrl]     = useState(() => loadOllama().url);
  const [ollamaModel, setOllamaModel] = useState(() => loadOllama().model);
  const [ollamaSaved, setOllamaSaved] = useState(false);
  useEffect(() => {
    if (dockerMode) {
      api.settingsOllama().then((d) => { setOllamaUrl(d.url); setOllamaModel(d.model); }).catch(() => {});
    }
  }, [dockerMode]);

  async function handleSaveOllama() {
    if (dockerMode) {
      await api.saveOllama(ollamaUrl, ollamaModel);
    } else {
      saveOllama(ollamaUrl, ollamaModel);
    }
    setOllamaSaved(true);
    setTimeout(() => setOllamaSaved(false), 2000);
  }

  return (
    <div className="max-w-[760px]">
      {/* Header */}
      <div className="glass mb-5 rounded-lg border border-border/20 p-5 shadow-sm">
        <div className="flex items-center gap-3">
          <Sparkles className="h-5 w-5 text-accent flex-shrink-0" />
          <div>
            <h2 className="text-[17px] font-semibold tracking-[-0.01em]">AI Settings</h2>
            <p className="mt-0.5 text-[13px] text-fg-dim">
              {dockerMode
                ? "Docker mode active — keys stored in an encrypted server-side vault. Keys never leave the server."
                : "Connect an AI provider to get smart summaries and habit-based recommendations."}
            </p>
          </div>
          {dockerMode && (
            <span className="ml-auto flex-shrink-0 rounded-full border border-safe/40 bg-[hsl(var(--safe)/0.1)] px-2.5 py-1 text-[11px] font-semibold text-safe">
              🐳 Docker mode
            </span>
          )}
        </div>

        {/* Upgrade callout — only shown when NOT in Docker mode */}
        {!dockerMode && (
          <div className="mt-4 rounded-md border border-accent/20 bg-[hsl(var(--accent)/0.05)] px-4 py-3">
            <div className="text-[12px] leading-[1.6] text-fg-dim">
              <strong className="font-semibold text-fg">Enable Docker mode for full features:</strong>{" "}
              encrypted key vault (keys never reach the browser), usage history, habit tracking
              with growth-slope analysis, AI summaries, and self-hosted Ollama. Run{" "}
              <code className="rounded bg-[hsl(var(--bg-3)/0.8)] px-1 font-mono text-[11px]">./docker/go</code>{" "}
              to start the stack.
            </div>
          </div>
        )}
      </div>

      {/* Cloud providers */}
      <section className="glass mb-4 rounded-lg border border-border/20 p-5 shadow-sm">
        <div className="mb-3 flex items-center gap-2">
          <KeyRound className="h-4 w-4 text-accent" />
          <span className="text-[10px] font-semibold uppercase tracking-[0.08em] text-fg-faint">
            Cloud providers
          </span>
          {dockerMode && (
            <span className="ml-1 text-[10px] text-fg-faint">
              (encrypted vault — enter a new key to update)
            </span>
          )}
        </div>
        <div className="flex flex-col gap-2">
          {dockerMode
            ? PROVIDERS.map((p) => (
                <ServerProviderRow
                  key={p.id}
                  provider={p}
                  configuredProviders={serverProviders}
                  onChanged={refreshServerProviders}
                />
              ))
            : PROVIDERS.map((p) => <ProviderRow key={p.id} provider={p} />)}
        </div>
      </section>

      {/* Ollama */}
      <section className="glass mb-4 rounded-lg border border-border/20 p-5 shadow-sm">
        <div className="mb-3 flex items-center gap-2">
          <Cpu className="h-4 w-4 text-accent" />
          <span className="text-[10px] font-semibold uppercase tracking-[0.08em] text-fg-faint">
            Local models (Ollama)
          </span>
        </div>
        <div className="rounded-md border border-accent/30 bg-[hsl(var(--accent)/0.06)] px-4 py-4">
          <div className="mb-3 flex items-center gap-2">
            <Cpu className="h-4 w-4 text-accent" />
            <span className="text-[13px] font-semibold text-fg">Ollama — local models</span>
            <span className="ml-1 rounded-full border border-accent/30 px-2 py-0.5 text-[10px] font-medium text-accent">
              private · free
            </span>
          </div>
          <p className="mb-3 text-[12px] leading-[1.55] text-fg-dim">
            Runs entirely on your machine — no data leaves your computer.
            {dockerMode
              ? " With Docker mode active, run `docker compose --profile ollama up` to start the bundled Ollama service."
              : " Install Ollama or use the Docker stack (./docker/go --profile ollama) to start it automatically."}
          </p>
          <div className="flex flex-wrap gap-3">
            <div className="flex-1 min-w-[200px]">
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-fg-faint">
                Ollama URL
              </label>
              <input type="url" value={ollamaUrl} onChange={(e) => setOllamaUrl(e.target.value)}
                className="w-full rounded-md border border-border/20 bg-[hsl(var(--bg-1)/0.8)] px-3 py-2 font-mono text-[12px] text-fg outline-none placeholder:text-fg-faint focus:border-accent" />
            </div>
            <div className="w-[180px]">
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-fg-faint">
                Model
              </label>
              <input type="text" value={ollamaModel} onChange={(e) => setOllamaModel(e.target.value)}
                placeholder="llama3.2"
                className="w-full rounded-md border border-border/20 bg-[hsl(var(--bg-1)/0.8)] px-3 py-2 font-mono text-[12px] text-fg outline-none placeholder:text-fg-faint focus:border-accent" />
            </div>
            <div className="flex items-end">
              <button type="button" onClick={() => void handleSaveOllama()}
                className="rounded-md bg-accent px-4 py-2 text-[11px] font-semibold text-white transition-colors hover:bg-accent-strong">
                {ollamaSaved ? "Saved ✓" : "Save"}
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* How AI will be used */}
      <section className="glass rounded-lg border border-border/20 p-5 shadow-sm">
        <div className="mb-3 text-[10px] font-semibold uppercase tracking-[0.08em] text-fg-faint">
          How AI will be used
        </div>
        <ul className="flex flex-col gap-2 text-[13px] text-fg-dim">
          <li className="flex gap-2.5">
            <span className="mt-0.5 flex-shrink-0 text-accent">→</span>
            <span><strong className="font-semibold text-fg">Post-scan summaries.</strong> After every scan, get a plain-English 2-sentence summary of what was found and whether to clean.</span>
          </li>
          <li className="flex gap-2.5">
            <span className="mt-0.5 flex-shrink-0 text-accent">→</span>
            <span><strong className="font-semibold text-fg">Habit-based recommendations.</strong> Dustpan tracks how fast each category fills up. When a category is growing faster than usual, AI explains why and what to do.</span>
          </li>
          <li className="flex gap-2.5">
            <span className="mt-0.5 flex-shrink-0 text-accent">→</span>
            <span><strong className="font-semibold text-fg">Smart manager proposals.</strong> When Dustpan detects a consistent pattern (e.g. Xcode fills 4 GB/week every time you build), it can draft a recurring clean schedule — or even an automated agent — tailored to your actual habits.</span>
          </li>
          <li className="flex gap-2.5">
            <span className="mt-0.5 flex-shrink-0 text-accent">→</span>
            <span><strong className="font-semibold text-fg">Your data stays yours.</strong> Dustpan sends only anonymized disk summaries to the AI (category name, GB, trend). No file paths, no content, no personal data. Ollama sends nothing — it runs on your machine.</span>
          </li>
        </ul>
      </section>
    </div>
  );
}
