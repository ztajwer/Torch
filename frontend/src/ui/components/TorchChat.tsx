import React from "react";
import { Loader2, MessageCircle, Send, Sparkles, X } from "lucide-react";
import { api, ChatMessage, ChatProductHint } from "../../lib/api";
import { formatPkr } from "../../lib/format";

const SUGGESTIONS = [
  "Best phone under 80,000 PKR?",
  "Compare Daraz vs PriceOye",
  "What's trending?",
  "Help me pick a laptop",
];

function getContextQuery(): string | undefined {
  try {
    const q = sessionStorage.getItem("torch_last_query");
    return q && q.length >= 2 ? q : undefined;
  } catch {
    return undefined;
  }
}

function formatLine(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="text-orange-300 font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <React.Fragment key={i}>{part}</React.Fragment>;
  });
}

function MessageBody(props: { content: string }) {
  return (
    <div className="chat-msg-body">
      {props.content.split("\n").map((line, i) => (
        <p key={i}>{formatLine(line)}</p>
      ))}
    </div>
  );
}

export function TorchChat() {
  const [open, setOpen] = React.useState(false);
  const [input, setInput] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [messages, setMessages] = React.useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm your **TORCH shopping assistant**. Ask about products, **PKR** prices, and store comparisons — I only answer shopping questions.",
    },
  ]);
  const [hints, setHints] = React.useState<ChatProductHint[]>([]);
  const listRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (open && listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages, open, loading, hints]);

  async function send(text?: string) {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;
    setInput("");
    const userMsg: ChatMessage = { role: "user", content: msg };
    const nextHistory = [...messages, userMsg];
    setMessages(nextHistory);
    setLoading(true);
    setHints([]);

    try {
      const prior = nextHistory.slice(0, -1).slice(-10);
      const res = await api.chat({
        message: msg,
        history: prior,
        context_query: getContextQuery(),
      });
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
      if (res.products?.length) setHints(res.products);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Sorry, I couldn't respond. ${(e as Error).message}\n\nMake sure the backend is running and **TORCH_GEMINI_API_KEY** is set in .env.`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {!open && (
        <button type="button" className="chat-fab" onClick={() => setOpen(true)} aria-label="Open shopping assistant">
          <MessageCircle className="h-6 w-6" />
          <span className="chat-fab-label">Ask TORCH</span>
        </button>
      )}

      {open && (
        <div className="chat-panel glass-panel" role="dialog" aria-label="TORCH shopping assistant">
          <header className="chat-header">
            <div className="chat-header-icon">
              <Sparkles className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="chat-header-title">TORCH Assistant</div>
              <div className="chat-header-sub">Products &amp; PKR prices only</div>
            </div>
            <button type="button" className="chat-close" onClick={() => setOpen(false)} aria-label="Close">
              <X className="h-5 w-5" />
            </button>
          </header>

          <div className="chat-messages" ref={listRef}>
            {messages.map((m, i) => (
              <div key={i} className={`chat-bubble chat-bubble--${m.role}`}>
                {m.role === "assistant" && (
                  <span className="chat-bubble-badge">
                    <Sparkles className="h-3 w-3" /> TORCH
                  </span>
                )}
                <MessageBody content={m.content} />
              </div>
            ))}
            {loading && (
              <div className="chat-bubble chat-bubble--assistant">
                <span className="flex items-center gap-2 text-sm text-muted-label">
                  <Loader2 className="h-4 w-4 animate-spin text-orange-400" />
                  Checking catalog…
                </span>
              </div>
            )}
            {hints.length > 0 && !loading && (
              <div className="chat-product-hints">
                {hints.slice(0, 4).map((p) => (
                  <a
                    key={p.id}
                    href={p.url || `#/products/${p.id}`}
                    target={p.url ? "_blank" : undefined}
                    rel={p.url ? "noreferrer" : undefined}
                    className="chat-product-hint"
                    onClick={(e) => {
                      if (!p.url) {
                        e.preventDefault();
                        window.location.hash = `#/products/${p.id}`;
                        setOpen(false);
                      }
                    }}
                  >
                    <span className="line-clamp-2 text-xs font-semibold">{p.title}</span>
                    <span className="text-xs font-bold text-orange-400">{formatPkr(p.price_pkr)}</span>
                    <span className="text-[10px] text-muted-label">{p.store}</span>
                  </a>
                ))}
              </div>
            )}
          </div>

          <div className="chat-suggestions">
            {SUGGESTIONS.map((s) => (
              <button key={s} type="button" className="torch-chip text-xs" disabled={loading} onClick={() => void send(s)}>
                {s}
              </button>
            ))}
          </div>

          <form
            className="chat-input-row"
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about a product…"
              className="torch-input chat-input"
              disabled={loading}
              maxLength={500}
            />
            <button type="submit" disabled={loading || !input.trim()} className="chat-send" aria-label="Send">
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
            </button>
          </form>
        </div>
      )}
    </>
  );
}
