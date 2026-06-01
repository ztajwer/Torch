import React from "react";
import { useQuery } from "@tanstack/react-query";
import { X } from "lucide-react";
import { api } from "../../lib/api";
import { CompareTable } from "./CompareTable";

export function ComparePanel(props: { ids: string[]; onOpen: (id: string) => void; onClose: () => void }) {
  const ids = props.ids.filter(Boolean).slice(0, 8);
  const q = useQuery({
    queryKey: ["compare", ids.join(",")],
    queryFn: () => api.compare(ids),
    enabled: ids.length > 0,
  });

  if (ids.length === 0) return null;

  return (
    <section className="torch-card-elevated glass-panel page-panel">
      <div className="page-header-row mb-4">
        <h2 className="section-heading-3d" style={{ fontSize: "1.125rem" }}>
          Side-by-side compare
        </h2>
        <button type="button" onClick={props.onClose} className="torch-btn-outline" aria-label="Close compare">
          <X className="h-4 w-4" />
        </button>
      </div>
      {q.isLoading && <p className="body-text">Loading…</p>}
      {q.isError && <p className="alert-error !text-left">{(q.error as Error).message}</p>}
      {q.data?.items && q.data.items.length > 0 && (
        <CompareTable items={q.data.items} bestId={q.data.best_id} onOpen={props.onOpen} />
      )}
      {q.data?.message && (q.data.items?.length ?? 0) === 0 && <p className="body-text">{q.data.message}</p>}
    </section>
  );
}
