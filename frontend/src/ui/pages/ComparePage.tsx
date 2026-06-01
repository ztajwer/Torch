import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Scale, Search } from "lucide-react";
import { api } from "../../lib/api";
import { formatPkr } from "../../lib/format";
import { CompareTable } from "../components/CompareTable";

export function ComparePage(props: {
  initialQuery?: string;
  initialIds?: string[];
  onOpen: (id: string) => void;
  onAnalyze: (q: string) => void;
}) {
  const [searchQuery, setSearchQuery] = React.useState(props.initialQuery ?? "");
  const [activeQuery, setActiveQuery] = React.useState(props.initialQuery?.trim() ?? "");

  React.useEffect(() => {
    if (props.initialQuery && props.initialQuery.length >= 2) {
      setSearchQuery(props.initialQuery);
      setActiveQuery(props.initialQuery.trim());
    }
  }, [props.initialQuery]);

  const ids = (props.initialIds ?? []).filter(Boolean).slice(0, 12);
  const useQueryMode = activeQuery.length >= 2;

  const q = useQuery({
    queryKey: ["compare-page", useQueryMode ? "q" : "ids", useQueryMode ? activeQuery : ids.join(",")],
    queryFn: () =>
      useQueryMode ? api.compareByQuery(activeQuery) : ids.length ? api.compare(ids) : Promise.resolve({ items: [], best_id: null, message: "" }),
    enabled: useQueryMode || ids.length > 0,
  });

  function runCompare() {
    const term = searchQuery.trim();
    if (term.length < 2) return;
    setActiveQuery(term);
    window.location.hash = `#/compare?q=${encodeURIComponent(term)}`;
  }

  const items = q.data?.items ?? [];
  const top3 = items.slice(0, 3);

  return (
    <div className="page-layout">
      <header className="page-header-block">
        <h1 className="page-title section-heading-3d">
          <Scale className="inline h-7 w-7 mr-2 text-orange-400" style={{ verticalAlign: "-0.15em" }} />
          Compare prices
        </h1>
        <p className="page-subtitle">
          See the same product across Daraz, PriceOye, Telemart, Mega.pk, and Shophive — best value highlighted.
        </p>
      </header>

      <section className="torch-card-elevated glass-panel page-panel">
        <form
          className="search-row"
          onSubmit={(e) => {
            e.preventDefault();
            runCompare();
          }}
        >
          <div className="input-wrap">
            <Search className="h-5 w-5" />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Product name from a recent search…"
              className="torch-input"
              style={{ paddingLeft: "3rem" }}
            />
          </div>
          <button type="submit" className="torch-btn-primary">
            Compare stores
          </button>
        </form>
        <p className="body-text mt-3">
          Tip: run <button type="button" className="torch-btn-ghost" onClick={() => props.onAnalyze("")}>Analyze on Home</button> first
          so we have live results to compare.
        </p>
      </section>

      {q.isLoading && (
        <p className="empty-state flex items-center justify-center gap-2">
          <Loader2 className="h-5 w-5 animate-spin text-orange-400" />
          Comparing…
        </p>
      )}
      {q.isError && <p className="alert-error">{ (q.error as Error).message}</p>}
      {!q.isLoading && !useQueryMode && ids.length === 0 && (
        <p className="empty-state">Enter a product name above to compare across stores.</p>
      )}
      {q.data?.message && items.length === 0 && !q.isLoading && (
        <p className="empty-state">{q.data.message}</p>
      )}

      {items.length > 0 && (
        <>
          {top3.length > 0 && (
            <section className="home-block glass-panel">
              <h2 className="section-heading-3d home-block-title mb-4">Quick picks</h2>
              <div className="scrape-picks">
                {top3.map((p, i) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => props.onOpen(p.id)}
                    className="scrape-pick-card text-left w-full"
                  >
                    <div className="text-xs font-bold text-orange-400">#{i + 1}</div>
                    <div className="text-sm font-semibold line-clamp-2 mt-1">{p.product_title}</div>
                    <div className="catalog-card-price mt-2">{formatPkr(p.price)}</div>
                    <div className="catalog-card-meta">{p.marketplace}</div>
                  </button>
                ))}
              </div>
            </section>
          )}

          <section className="torch-card glass-panel page-panel">
            <h2 className="section-heading-3d mb-4" style={{ fontSize: "1.125rem" }}>
              Full comparison ({items.length})
            </h2>
            <CompareTable items={items} bestId={q.data?.best_id ?? null} onOpen={props.onOpen} />
          </section>
        </>
      )}
    </div>
  );
}
