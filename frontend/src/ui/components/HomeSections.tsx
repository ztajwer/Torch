import React from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Package, Sparkles, Store, TrendingUp, Zap } from "lucide-react";
import { api, isPkStore, Product } from "../../lib/api";
import { formatPkr } from "../../lib/format";

const STEPS = [
  { num: "1", title: "Search", desc: "Type what you want to buy." },
  { num: "2", title: "Analyze", desc: "We scan 5 Pakistani stores live." },
  { num: "3", title: "Decide", desc: "Top 3 here — full list on Products." },
];

const STORES = ["Daraz", "PriceOye", "Telemart", "Mega.pk", "Shophive"];

export function HowItWorksSection() {
  return (
    <section className="home-block glass-panel">
      <div className="home-block-head">
        <Sparkles className="h-5 w-5 text-orange-400" />
        <h2 className="section-heading-3d home-block-title">How Torch works</h2>
      </div>
      <div className="steps-row steps-row--compact">
        {STEPS.map((s) => (
          <div key={s.num} className="step-card step-card--compact">
            <div className="step-num-3d">{s.num}</div>
            <h3 className="step-title">{s.title}</h3>
            <p className="step-desc">{s.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export function StoresSection() {
  return (
    <section className="home-block glass-panel">
      <div className="home-block-head">
        <Store className="h-5 w-5 text-orange-400" />
        <h2 className="section-heading-3d home-block-title">Stores we scan</h2>
      </div>
      <div className="stores-row">
        {STORES.map((name) => (
          <span key={name} className="store-pill">
            {name}
          </span>
        ))}
      </div>
      <p className="body-text mt-3">All prices shown in Pakistani Rupees (PKR).</p>
    </section>
  );
}

export function TrendingPreview(props: { onOpenProduct: (id: string) => void; onAnalyze: (q: string) => void }) {
  const q = useQuery({
    queryKey: ["trending-preview"],
    queryFn: () => api.products({ sort: "trend_desc", limit: 6, offset: 0 }),
    refetchInterval: 30_000,
  });

  const items = (q.data?.items ?? []).filter((p) => isPkStore(p.marketplace)).slice(0, 6);

  return (
    <section className="home-block glass-panel">
      <div className="home-block-head home-block-head--between">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-orange-400" />
          <h2 className="section-heading-3d home-block-title">Trending now</h2>
        </div>
        <a href="#/trending" className="section-link">
          See all <ArrowRight className="h-4 w-4" />
        </a>
      </div>
      {q.isLoading && <p className="body-text">Loading trending…</p>}
      {!q.isLoading && items.length === 0 && (
        <p className="body-text">
          Run a search or tap <strong>Update stores</strong> in the header to fill the catalog.
        </p>
      )}
      {items.length > 0 && (
        <div className="trending-grid trending-grid--home">
          {items.map((p) => (
            <TrendingTile key={p.id} product={p} onOpen={props.onOpenProduct} />
          ))}
        </div>
      )}
      <div className="mt-4 flex flex-wrap gap-2">
        <button type="button" onClick={() => props.onAnalyze("iphone")} className="torch-chip">
          Try: iphone
        </button>
        <button type="button" onClick={() => props.onAnalyze("laptop")} className="torch-chip">
          Try: laptop
        </button>
      </div>
    </section>
  );
}

export function HomeCtaSection(props: { onFocusSearch: () => void }) {
  return (
    <section className="home-cta glass-panel">
      <Zap className="h-8 w-8 text-orange-400 mx-auto mb-3" />
      <h2 className="section-heading-3d">Ready to find the best deal?</h2>
      <p className="body-text mt-2 mb-5 max-w-md mx-auto">
        One search. Five stores. Your top 3 picks in under a minute.
      </p>
      <button type="button" onClick={props.onFocusSearch} className="torch-btn-primary btn-inline">
        Start analyzing →
      </button>
    </section>
  );
}

function TrendingTile(props: { product: Product; onOpen: (id: string) => void }) {
  const p = props.product;
  return (
    <button type="button" onClick={() => props.onOpen(p.id)} className="trending-card trending-card--btn">
      <div className="trending-thumb">
        {p.image_url ? <img src={p.image_url} alt="" loading="lazy" /> : <Package className="h-6 w-6 opacity-40" />}
      </div>
      <div className="trending-body">
        <div className="trending-title">{p.product_title}</div>
        <div className="trending-price">{formatPkr(p.price)}</div>
        <div className="text-xs text-muted-label">{p.marketplace}</div>
      </div>
    </button>
  );
}
