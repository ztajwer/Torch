import React from "react";
import {
  ArrowLeft,
  ArrowRight,
  Clock,
  Crown,
  ExternalLink,
  Loader2,
  List,
  Medal,
  Search,
  Sparkles,
  Star,
} from "lucide-react";
import { AiRanking, api, IntelligenceResult } from "../../lib/api";
import { formatPkr, sanitizeAiText } from "../../lib/format";
import { loadRecentSearches, saveRecentSearch, type RecentSearch } from "../../lib/recentSearches";
import {
  HomeCtaSection,
  HowItWorksSection,
  StoresSection,
  TrendingPreview,
} from "../components/HomeSections";

const EXAMPLES = ["aesthetic cup", "bed", "iphone", "laptop"];

const RANK_LABELS: Record<number, string> = {
  1: "Best pick",
  2: "Runner up",
  3: "Also good",
};

export function SearchPage(props: { initialQuery?: string; onOpenProduct: (id: string) => void }) {
  const [query, setQuery] = React.useState(props.initialQuery ?? "");
  const [loading, setLoading] = React.useState(false);
  const [statusText, setStatusText] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<IntelligenceResult | null>(null);
  const [recent, setRecent] = React.useState<RecentSearch[]>(() => loadRecentSearches());

  React.useEffect(() => {
    if (props.initialQuery && props.initialQuery.length >= 2) {
      void runSearch(props.initialQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.initialQuery]);

  async function runSearch(term?: string) {
    const q = (term ?? query).trim();
    if (q.length < 2) {
      setError("Type what you want to buy (at least 2 letters).");
      return;
    }
    setQuery(q);
    setError(null);
    setResult(null);
    setLoading(true);
    window.location.hash = `#/search?q=${encodeURIComponent(q)}`;
    window.scrollTo({ top: 0, behavior: "smooth" });

    try {
      setStatusText("Analyzing Daraz, PriceOye, Telemart, Mega.pk, Shophive… (30–60 sec)");
      const full = await api.intelligenceSearch(q);
      setResult(full);
      saveRecentSearch(q, full.total_matches ?? 0);
      setRecent(loadRecentSearches());
      try {
        sessionStorage.setItem("torch_last_query", q);
      } catch {
        /* ignore */
      }
      setStatusText("");
    } catch (e) {
      const msg = (e as Error).message;
      if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
        setError("Cannot reach server. Run start.ps1 or start the backend on port 8010.");
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }

  function clearResults() {
    setResult(null);
    setError(null);
    window.location.hash = "#/search";
  }

  const hasMatches = (result?.total_matches ?? 0) > 0;
  const hasResults = Boolean(result);
  const rankings = result?.ai?.rankings ?? [];
  const total = result?.total_matches ?? 0;
  const poweredBy = result?.ai?.powered_by;
  const productsPageHref = result?.query ? `#/products?q=${encodeURIComponent(result.query)}` : "#/products";

  const searchForm = (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        void runSearch();
      }}
    >
      <div className="search-row">
        <div className="input-wrap">
          <Search className="h-5 w-5" />
          <input
            id="torch-search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter a product name…"
            className="torch-input"
            style={{ paddingLeft: "3rem" }}
            disabled={loading}
            autoFocus={!hasResults}
          />
        </div>
        <button type="submit" disabled={loading} className="torch-btn-primary">
          {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : null}
          {loading ? "Analyzing…" : "Analyze Now →"}
        </button>
      </div>
    </form>
  );

  return (
    <div className={`search-page page-layout ${hasResults ? "search-page--results" : ""}`}>
      {hasResults ? (
        /* —— Results only: top 3 + summary + link to Products page —— */
        <>
          <section className="compact-search glass-panel animate-fade-in">
            <button type="button" className="btn-text-back" onClick={clearResults}>
              <ArrowLeft className="h-4 w-4" /> Back to home
            </button>
            <div className="compact-search-form">{searchForm}</div>
            {hasMatches && (
              <p className="results-count">
                <span className="text-3d-orange">{total}</span> matches for &ldquo;
                <strong>{result?.query}</strong>&rdquo;
              </p>
            )}
            {statusText && <p className="status-loading">{statusText}</p>}
            {error && <p className="status-error">{error}</p>}
          </section>

          {result?.user_message && !hasMatches && <div className="alert-warn glass-panel">{result.user_message}</div>}

          {rankings.length > 0 && (
            <section className="results-section animate-fade-up">
              <div className="section-head">
                <span className="section-icon">
                  <Medal className="h-4 w-4" />
                </span>
                <h2 className="section-heading-3d">Your top 3 picks</h2>
              </div>
              <div className="rank-list">
                {rankings.map((r) => (
                  <RankCard key={`${r.rank}-${r.product_id}`} ranking={r} />
                ))}
              </div>
            </section>
          )}

          {result && hasMatches && result.ai?.summary && (
            <section className="torch-card glass-panel p-5 sm:p-6 space-y-4 animate-fade-up">
              <div className="section-head mb-0">
                <span className="section-icon">
                  <Sparkles className="h-4 w-4" />
                </span>
                <div>
                  <h2 className="section-heading-3d">Smart advice</h2>
                  <p className="text-xs mt-0.5 text-muted-label">
                    {poweredBy === "gemini" ? "Google Gemini" : "Intent-based ranking"}
                  </p>
                </div>
              </div>
              <p className="body-text body-text-strong line-clamp-4">{sanitizeAiText(result.ai.summary)}</p>
              {result.ai.insights && (
                <div className="insight-grid">
                  <InsightChip
                    label="Match"
                    value={
                      result.ai.insights.top_pick_relevance != null
                        ? `${Math.round(result.ai.insights.top_pick_relevance)}%`
                        : "—"
                    }
                  />
                  <InsightChip
                    label="Value"
                    value={
                      result.ai.insights.top_pick_value_score != null
                        ? `${Math.round(result.ai.insights.top_pick_value_score)}/100`
                        : "—"
                    }
                  />
                  <InsightChip label="Cheapest" value={formatPkr(result.ai.insights.cheapest?.price)} />
                  <InsightChip label="Premium" value={formatPkr(result.ai.insights.premium?.price)} />
                </div>
              )}
            </section>
          )}

          {hasMatches && total > 3 && (
            <a href={productsPageHref} className="view-all-card glass-panel animate-fade-up">
              <span className="view-all-icon">
                <List className="h-6 w-6" />
              </span>
              <span className="view-all-text">
                <span className="view-all-title">View all {total} products</span>
                <span className="view-all-sub">Opens the Products page — filters, sort & full comparison</span>
              </span>
              <ArrowRight className="h-6 w-6 shrink-0 text-orange-400" />
            </a>
          )}

          {!loading && result && !hasMatches && (
            <p className="text-center body-text">
              No match for &ldquo;{result.query}&rdquo;. Try another spelling or product name.
            </p>
          )}
        </>
      ) : (
        /* —— Home landing with sections —— */
        <>
          <section className="hero-grid animate-fade-in">
            <div className="hero-copy">
              <h1 className="hero-title">
                <span className="text-3d-white">Find The Best.</span>
                <br />
                <span className="text-3d-orange">Buy Smarter.</span>
              </h1>
              <p className="hero-sub">
                Live PKR prices from five Pakistani stores. Get your top 3 picks instantly — open Products for the full list.
              </p>
              <div className="search-box-dark glass-panel mt-6">
                {searchForm}
                <div className="mt-3 flex flex-wrap gap-2 justify-center lg:justify-start items-center">
                  <span className="text-xs text-muted-label">Try:</span>
                  {EXAMPLES.map((ex) => (
                    <button
                      key={ex}
                      type="button"
                      disabled={loading}
                      onClick={() => void runSearch(ex)}
                      className="torch-chip"
                    >
                      {ex}
                    </button>
                  ))}
                </div>
                {statusText && <p className="status-loading">{statusText}</p>}
                {error && <p className="status-error">{error}</p>}
              </div>
            </div>
            <div className="hero-visual" aria-hidden>
              <div className="hero-beam" />
              <div className="hero-shadow-floor" />
              <img src="/torch_hero.png" alt="" className="hero-torch-banner" />
            </div>
          </section>

          {recent.length > 0 && (
            <section className="recent-bar glass-panel animate-fade-in">
              <div className="recent-bar-head">
                <Clock className="h-4 w-4 text-orange-400" />
                <span className="recent-bar-title">Recent searches</span>
              </div>
              <div className="recent-chips">
                {recent.map((r) => (
                  <button
                    key={r.at}
                    type="button"
                    disabled={loading}
                    onClick={() => void runSearch(r.query)}
                    className="torch-chip"
                  >
                    {r.query}
                  </button>
                ))}
              </div>
            </section>
          )}

          <div className="home-sections-flow">
            <HowItWorksSection />
            <TrendingPreview
              onOpenProduct={props.onOpenProduct}
              onAnalyze={(q) => void runSearch(q)}
            />
            <StoresSection />
            <HomeCtaSection onFocusSearch={() => document.getElementById("torch-search")?.focus()} />
          </div>
        </>
      )}
    </div>
  );
}

function InsightChip(props: { label: string; value: string }) {
  return (
    <div className="insight-chip">
      <div className="insight-chip-label">{props.label}</div>
      <div className="insight-chip-value">{props.value}</div>
    </div>
  );
}

function RankCard({ ranking }: { ranking: AiRanking }) {
  const rankNum = ranking.rank;
  const label = RANK_LABELS[rankNum] ?? `#${rankNum}`;
  const isGold = rankNum === 1;

  return (
    <article className={`rank-card glass-panel ${isGold ? "rank-card--gold" : ""}`}>
      <div className={`rank-card-accent rank-accent--${rankNum}`} />
      <div className="rank-card-inner">
        {ranking.image_url ? (
          <div className="rank-thumb">
            <img src={ranking.image_url} alt="" loading="lazy" />
          </div>
        ) : null}
        <div className="rank-body">
          <span className={`rank-badge rank-badge--${rankNum}`}>
            {rankNum === 1 && <Crown className="h-3 w-3" />}
            {rankNum === 1 ? "1st" : rankNum === 2 ? "2nd" : "3rd"} · {label}
          </span>
          <h3 className="rank-title line-clamp-2">{ranking.title}</h3>
          <div className="rank-tags">
            {ranking.relevance_percent != null && (
              <span className="tag-match">{Math.round(ranking.relevance_percent)}% match</span>
            )}
            {ranking.value_score != null && (
              <span className="tag-value">Value {Math.round(ranking.value_score)}/100</span>
            )}
          </div>
          <div className="rank-meta">
            <span className="rank-price">{formatPkr(ranking.price)}</span>
            <span className="text-muted-label text-sm">{ranking.marketplace}</span>
            {ranking.rating != null && (
              <span className="rank-rating">
                <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                {ranking.rating}
              </span>
            )}
          </div>
          {ranking.product_url && (
            <a href={ranking.product_url} target="_blank" rel="noreferrer" className="btn-buy-inline">
              Buy on store <ExternalLink className="h-4 w-4" />
            </a>
          )}
        </div>
      </div>
    </article>
  );
}
