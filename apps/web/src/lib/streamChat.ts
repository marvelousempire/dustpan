/**
 * Plan 0023 — POST-based SSE stream parser.
 *
 * EventSource (used by streamSSE) is GET-only. The chat endpoint needs to
 * POST the conversation history, so we roll a minimal fetch-based reader
 * that emits {event, data} objects matching streamSSE's shape.
 *
 * Server emits standard SSE frames:
 *   event: <name>
 *   data: <json>
 *   <blank line>
 */

export interface ChatSSEMessage {
  event: string;
  data:  any;
}

export interface ChatStreamHandle {
  close: () => void;
}

export function streamChat(
  body: any,
  onMessage: (msg: ChatSSEMessage) => void,
  onError?:  (err: Error) => void,
): ChatStreamHandle {
  const controller = new AbortController();
  let closed = false;

  (async () => {
    let resp: Response;
    try {
      resp = await fetch("/api/ai/chat", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(body),
        signal:  controller.signal,
      });
    } catch (e) {
      if (!closed) onError?.(e as Error);
      return;
    }

    if (!resp.ok || !resp.body) {
      if (!closed) onError?.(new Error(`chat stream failed: ${resp.status}`));
      return;
    }

    const reader  = resp.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";

    try {
      while (!closed) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });

        // SSE: frames separated by blank line
        let idx;
        while ((idx = buf.indexOf("\n\n")) !== -1) {
          const frame = buf.slice(0, idx);
          buf = buf.slice(idx + 2);

          let eventName = "message";
          const dataLines: string[] = [];
          for (const line of frame.split("\n")) {
            if (line.startsWith("event:")) {
              eventName = line.slice(6).trim();
            } else if (line.startsWith("data:")) {
              dataLines.push(line.slice(5).trim());
            }
            // ignore comments (lines starting with `:`)
          }
          if (dataLines.length === 0) continue;
          const dataStr = dataLines.join("\n");
          try {
            const data = JSON.parse(dataStr);
            onMessage({ event: eventName, data });
          } catch {
            onMessage({ event: eventName, data: dataStr });
          }
        }
      }
    } catch (e) {
      if (!closed) onError?.(e as Error);
    }
  })();

  return {
    close() {
      closed = true;
      try { controller.abort(); } catch { /* ignore */ }
    },
  };
}
