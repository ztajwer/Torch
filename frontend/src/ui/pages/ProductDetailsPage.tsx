import React from "react";
import { useQuery } from "@tanstack/react-query";
import { ExternalLink } from "lucide-react";
import { api } from "../../lib/api";
import { formatPkr } from "../../lib/format";
import { Card } from "../components/Card";

export function ProductDetailsPage(props: { id: string; onBack: () => void; onCompare: (ids: string[]) => void }) {
  const q = useQuery({ queryKey: ["product", props.id], queryFn: () => api.product(props.id), refetchInterval: 6000 });

  return (
    <div className="page-layout">
      <div className="page-header-row">
        <header className="page-header-block">
          <h1 className="page-title section-heading-3d">Product</h1>
          <p className="page-subtitle">Price and store details.</p>
        </header>
        <div className="flex flex-wrap gap-2 shrink-0">
          <button type="button" onClick={props.onBack} className="torch-btn-outline">
            Back to catalog
          </button>
        </div>
      </div>

      {q.isLoading && <Card title="Loading…">Fetching product…</Card>}
      {q.isError && <Card title="Error">{(q.error as Error).message}</Card>}
      {q.data && (
        <Card title="Overview">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="detail-thumb">
              {q.data.image_url ? (
                <img src={q.data.image_url} alt="" />
              ) : (
                <span className="text-xs text-muted-label">No image</span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-lg font-semibold leading-snug">{q.data.product_title}</div>
              <div className="mt-1 text-sm text-muted-label">
                {q.data.marketplace} · {q.data.category ?? "Uncategorized"}
              </div>
              <div className="metric-grid mt-4">
                <Metric label="Price" value={formatPkr(q.data.price)} />
                <Metric label="Rating" value={`${q.data.rating ?? "—"}`} />
                <Metric label="Reviews" value={`${q.data.review_count ?? "—"}`} />
                <Metric label="Trend" value={q.data.trend_score.toFixed(3)} />
              </div>
              <div className="flex flex-wrap gap-3 mt-5">
                <a
                  className="torch-btn-primary inline-flex"
                  href={q.data.product_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Buy on store <ExternalLink className="h-4 w-4" />
                </a>
                <button type="button" onClick={() => props.onCompare([props.id])} className="torch-btn-outline">
                  Compare in catalog
                </button>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

function Metric(props: { label: string; value: string }) {
  return (
    <div className="metric-box">
      <div className="section-label">{props.label}</div>
      <div className="mt-1 text-sm font-semibold">{props.value}</div>
    </div>
  );
}
