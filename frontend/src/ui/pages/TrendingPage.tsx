import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Package, Search, TrendingUp } from "lucide-react";
import { api, isPkStore, Product } from "../../lib/api";
import { formatPkr } from "../../lib/format";

type SortKey = "trend_desc" | "best_value_desc" | "rating_desc" | "price_asc";

export function TrendingPage(props: { onOpen: (id: string) => void; onAnalyze: (q: string) => void }) {
  const [sort, setSort] = React.useState<SortKey>("trend_desc");

  const q = useQuery({
    queryKey: ["trending-page", sort],
    queryFn: () => api.products({ sort, limit: 48, offset: 0 }),
    refetchInterval: 20_000,
  });

  const items = (q.data?.items ?? []).filter((p) => isPkStore(p.marketplace));

  return (
    <div className="page-layout">
      <header className="page-header-block">
        <h1 className="page-title section-heading-3d">
          <TrendingUp className="inline h-7 w-7 mr-2 text-orange-400" style={{ verticalAlign: "-0.15em" }} />
          Trending &amp; popular
        </h1>
        <p className="page-subtitle">
          What shoppers are looking at across Pakistani stores — sorted by popularity, value, or price.
        </p>
      </header>

      <section className="torch-card glass-panel page-panel">
        <div className="filters-grid filters-grid--2">
          <select value={sort} onChange={(e) => setSort(e.target.value as SortKey)} className="torch-input py-2.5 text-sm">
            <option value="trend_desc">Most popular</option>
            <option value="best_value_desc">Best value</option>
            <option value="rating_desc">Top rated</option>
            <option value="price_asc">Lowest price</option>
          </select>
          <button type="button" onClick={() => props.onAnalyze("")} className="torch-btn-outline">
            <Search className="h-4 w-4" />
            Smart search on Home
          </button>
        </div>
      </section>

      {q.isLoading && (
        <p className="empty-state flex items-center justify-center gap-2">
          <Loader2 className="h-5 w-5 animate-spin text-orange-400" />
          Loading products…
        </p>
      )}
      {q.isError && <p className="empty-state">Could not load catalog. Is the backend running?</p>}
      {!q.isLoading && items.length === 0 && (
        <div className="empty-state space-y-2">
          <p>No products in catalog yet.</p>
          <p>
            Use <strong>Home → Analyze</strong> or the refresh button in the header.
          </p>
        </div>
      )}
      {items.length > 0 && (
        <>
          <p className="text-xs text-muted-label">{items.length} products</p>
          <div className="catalog-grid">
            {items.map((p) => (
              <TrendingProductCard key={p.id} p={p} onOpen={props.onOpen} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function TrendingProductCard(props: { p: Product; onOpen: (id: string) => void }) {
  const p = props.p;
  return (
    <button type="button" onClick={() => props.onOpen(p.id)} className="catalog-card">
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
          <span className="catalog-card-meta">★ {p.trend_score.toFixed(2)}</span>
        </div>
        <div className="catalog-card-meta">{p.marketplace}</div>
      </div>
    </button>
  );
}
