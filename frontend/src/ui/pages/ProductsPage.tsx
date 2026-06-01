import React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Package, Search, ShoppingBag, Star } from "lucide-react";
import { api, IntelligenceResult, isPkStore, Product } from "../../lib/api";
import { formatPkr, sanitizeAiText } from "../../lib/format";
import { ComparePanel } from "../components/ComparePanel";
import { Card } from "../components/Card";

type SortKey = "trend_desc" | "best_value_desc" | "price_asc" | "price_desc" | "rating_desc" | "reviews_desc";

export function ProductsPage(props: {
  initialSearch?: string;
  compareIds?: string[];
  onOpen: (id: string) => void;
  onGoHome: (q: string) => void;
  onClearCompare: () => void;
}) {
  const [searchInput, setSearchInput] = React.useState(props.initialSearch ?? "");
  const [localFilter, setLocalFilter] = React.useState("");
  const [category, setCategory] = React.useState("");
  const [marketplace, setMarketplace] = React.useState("");
  const [sort, setSort] = React.useState<SortKey>("price_asc");
  const [scrapeResult, setScrapeResult] = React.useState<IntelligenceResult | null>(null);
  const [scraping, setScraping] = React.useState(false);
  const [scrapeError, setScrapeError] = React.useState<string | null>(null);

  const queryClient = useQueryClient();
  const metaQ = useQuery({ queryKey: ["filter-meta"], queryFn: api.filterMeta });

  React.useEffect(() => {
    if (props.initialSearch && props.initialSearch.length >= 2) {
      setSearchInput(props.initialSearch);
      setLocalFilter(props.initialSearch);
      void searchAllStores(props.initialSearch);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.initialSearch]);

  const catalogQ = useQuery({
    queryKey: ["catalog-all", sort],
    queryFn: () => api.productsAll({ sort }),
    refetchInterval: 15000,
  });

  const catalog = React.useMemo(
    () => (catalogQ.data?.items ?? []).filter((p) => isPkStore(p.marketplace)),
    [catalogQ.data?.items]
  );
  const catalogTotal = catalog.length;

  const filteredCatalog = React.useMemo(() => {
    let list = catalog;
    const f = localFilter.trim().toLowerCase();
    if (f) {
      list = list.filter(
        (p) =>
          p.product_title.toLowerCase().includes(f) ||
          (p.category ?? "").toLowerCase().includes(f) ||
          p.marketplace.toLowerCase().includes(f)
      );
    }
    if (category) list = list.filter((p) => (p.category ?? "Uncategorized") === category);
    if (marketplace) list = list.filter((p) => p.marketplace === marketplace);
    return list;
  }, [catalog, localFilter, category, marketplace]);

  async function searchAllStores(term?: string) {
    const q = (term ?? searchInput).trim();
    if (q.length < 2) {
      setScrapeError("Type what you want to buy (at least 2 letters).");
      return;
    }
    setSearchInput(q);
    setLocalFilter(q);
    setScrapeError(null);
    setScraping(true);
    setScrapeResult(null);
    window.location.hash = `#/products?q=${encodeURIComponent(q)}`;
    try {
      const full = await api.intelligenceSearch(q);
      setScrapeResult(full);
      void queryClient.invalidateQueries({ queryKey: ["catalog-all"] });
    } catch (e) {
      const msg = (e as Error).message;
      if (msg.includes("Failed to fetch")) {
        setScrapeError("Start the backend first (see README or run start.ps1).");
      } else {
        setScrapeError(msg);
      }
    } finally {
      setScraping(false);
    }
  }

  const scrapeItems = scrapeResult?.compare.items ?? [];
  const winner = scrapeResult?.recommendations.best_overall;
  const showScrapeResults = Boolean(scrapeResult && searchInput.trim());

  return (
    <div className="page-layout">
      <header className="page-header-block">
        <h1 className="page-title section-heading-3d">Products catalog</h1>
        <p className="page-subtitle">
          Full list with filters and sort. Compare live PKR from <strong>Daraz</strong>, <strong>PriceOye</strong>,{" "}
          <strong>Telemart</strong>, <strong>Mega.pk</strong>, <strong>Shophive</strong>.
        </p>
      </header>

      <section className="torch-card-elevated glass-panel page-panel">
        <form
          className="search-row"
          onSubmit={(e) => {
            e.preventDefault();
            void searchAllStores();
          }}
        >
          <div className="input-wrap">
            <Search className="h-5 w-5" />
            <input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search all stores… e.g. phone, cup, laptop"
              className="torch-input"
              style={{ paddingLeft: "3rem" }}
              disabled={scraping}
            />
          </div>
          <button type="submit" disabled={scraping} className="torch-btn-primary">
            {scraping ? <Loader2 className="h-5 w-5 animate-spin" /> : <ShoppingBag className="h-5 w-5" />}
            {scraping ? "Searching…" : "Search stores"}
          </button>
        </form>
        {scrapeError && <p className="alert-error">{scrapeError}</p>}
        <p className="body-text mt-3 text-center sm:text-left">
          <button type="button" className="torch-btn-ghost" onClick={() => props.onGoHome("")}>
            ← Home for top 3 picks
          </button>
        </p>
      </section>

      {props.compareIds && props.compareIds.length > 0 && (
        <ComparePanel ids={props.compareIds} onOpen={props.onOpen} onClose={props.onClearCompare} />
      )}

      {showScrapeResults && (
        <ScrapeResults
          result={scrapeResult!}
          winner={winner ?? null}
          items={scrapeItems}
          onOpen={props.onOpen}
          onClear={() => {
            setScrapeResult(null);
            setSearchInput("");
            setLocalFilter("");
            window.location.hash = "#/products";
          }}
        />
      )}

      <section>
        <div className="page-header-row mb-3">
          <h2 className="section-heading-3d" style={{ fontSize: "1.125rem" }}>
            <Package className="inline h-5 w-5 mr-2 text-orange-400" style={{ verticalAlign: "-0.2em" }} />
            Saved catalog
            {catalogTotal > 0 && (
              <span className="text-muted-label font-normal text-base ml-2">({catalogTotal})</span>
            )}
          </h2>
        </div>

        <Card>
          <div className="filters-grid !p-0">
            <input
              value={localFilter}
              onChange={(e) => setLocalFilter(e.target.value)}
              placeholder="Filter by name, category, store…"
              className="torch-input py-2.5 text-sm"
            />
            <select value={marketplace} onChange={(e) => setMarketplace(e.target.value)} className="torch-input py-2.5 text-sm">
              <option value="">All stores</option>
              {(metaQ.data?.marketplaces ?? []).map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
            <select value={sort} onChange={(e) => setSort(e.target.value as SortKey)} className="torch-input py-2.5 text-sm">
              <option value="price_asc">Price: low → high</option>
              <option value="price_desc">Price: high → low</option>
              <option value="rating_desc">Best rating</option>
              <option value="trend_desc">Most popular</option>
            </select>
          </div>
          {(metaQ.data?.categories ?? []).length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              <FilterChip active={!category} label="All" onClick={() => setCategory("")} />
              {(metaQ.data?.categories ?? []).slice(0, 8).map((c) => (
                <FilterChip key={c} active={category === c} label={c} onClick={() => setCategory(category === c ? "" : c)} />
              ))}
            </div>
          )}
        </Card>

        {catalogQ.isLoading && <p className="empty-state mt-3">Loading catalog…</p>}
        {catalogQ.isError && (
          <p className="empty-state mt-3">Cannot load products. Is the backend running on port 8010?</p>
        )}
        {!catalogQ.isLoading && catalogTotal === 0 && (
          <div className="empty-state mt-3 space-y-2">
            <p>Catalog is empty.</p>
            <p>
              Use <strong>Menu → Update stores</strong> and wait 1–2 minutes.
            </p>
          </div>
        )}
        {!catalogQ.isLoading && catalogTotal > 0 && filteredCatalog.length === 0 && (
          <div className="empty-state mt-3 space-y-3">
            <p>
              No &ldquo;{localFilter}&rdquo; in saved catalog ({catalogTotal} other products).
            </p>
            <button type="button" onClick={() => void searchAllStores(localFilter)} disabled={scraping} className="torch-btn-primary">
              Search all stores for &ldquo;{localFilter}&rdquo;
            </button>
          </div>
        )}
        {filteredCatalog.length > 0 && (
          <>
            <p className="text-xs text-muted-label my-3">
              Showing {filteredCatalog.length} of {catalogTotal} products
            </p>
            <div className="catalog-grid">
              {filteredCatalog.map((p) => (
                <ProductCard key={p.id} p={p} onOpen={props.onOpen} />
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  );
}

function ScrapeResults(props: {
  result: IntelligenceResult;
  winner: IntelligenceResult["recommendations"]["best_overall"];
  items: Product[];
  onOpen: (id: string) => void;
  onClear: () => void;
}) {
  const rankings = props.result.ai?.rankings ?? [];
  return (
    <section className="flex flex-col gap-4">
      <div className="page-header-row">
        <h2 className="section-heading-3d" style={{ fontSize: "1.125rem" }}>
          Results for &ldquo;{props.result.query}&rdquo;
          <span className="text-muted-label font-normal text-base ml-2">({props.result.total_matches} matches)</span>
        </h2>
        <button type="button" onClick={props.onClear} className="torch-btn-outline">
          Clear results
        </button>
      </div>

      {props.result.ai?.summary && (
        <div className="torch-card glass-panel p-4">
          <p className="body-text body-text-strong">{sanitizeAiText(props.result.ai.summary)}</p>
        </div>
      )}

      {rankings.length > 0 && (
        <div className="scrape-picks">
          {rankings.map((r) => (
            <a key={r.product_id} href={r.product_url} target="_blank" rel="noreferrer" className="scrape-pick-card">
              <div className="text-xs font-bold text-orange-400">#{r.rank} pick</div>
              <div className="text-sm font-semibold line-clamp-2 mt-1">{r.title}</div>
              <div className="catalog-card-price mt-2">{formatPkr(r.price ?? 0)}</div>
              <div className="catalog-card-meta">{r.marketplace}</div>
            </a>
          ))}
        </div>
      )}

      {props.winner && rankings.length === 0 && (
        <div className="torch-card-elevated glass-panel p-4">
          <div className="section-label">Best pick</div>
          <div className="text-lg font-bold mt-1">{props.winner.product_title}</div>
          <div className="catalog-card-row mt-2">
            <span className="catalog-card-price">{formatPkr(Number(props.winner.price))}</span>
            <span className="catalog-card-meta">{props.winner.marketplace}</span>
          </div>
          <p className="body-text mt-2">{props.result.recommendations.summary}</p>
        </div>
      )}

      {props.items.length > 0 ? (
        <div className="catalog-grid">
          {props.items.map((p) => (
            <ProductCard
              key={p.id}
              p={p}
              onOpen={props.onOpen}
              highlight={p.id === props.result.compare.best_id}
            />
          ))}
        </div>
      ) : (
        <p className="empty-state">No matches on stores for this query. Try another spelling.</p>
      )}
    </section>
  );
}

function FilterChip(props: { active: boolean; label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={props.onClick}
      className={`filter-chip ${props.active ? "filter-chip--active" : ""}`}
    >
      {props.label}
    </button>
  );
}

function ProductCard(props: { p: Product; onOpen: (id: string) => void; highlight?: boolean }) {
  const p = props.p;
  return (
    <button
      type="button"
      onClick={() => props.onOpen(p.id)}
      className={`catalog-card ${props.highlight ? "catalog-card--highlight" : ""}`}
    >
      <div className="catalog-card-media">
        {p.image_url ? (
          <img src={p.image_url} alt="" loading="lazy" />
        ) : (
          <Package className="h-10 w-10 opacity-40" />
        )}
      </div>
      <div className="catalog-card-body">
        <div className="catalog-card-title">{p.product_title}</div>
        <div className="catalog-card-row">
          <span className="catalog-card-price">{formatPkr(p.price)}</span>
          {p.rating != null && (
            <span className="catalog-card-meta flex items-center gap-1">
              <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
              {p.rating}
            </span>
          )}
        </div>
        <div className="catalog-card-meta">{p.marketplace}</div>
        {props.highlight && <div className="catalog-card-badge">Best deal</div>}
      </div>
    </button>
  );
}
