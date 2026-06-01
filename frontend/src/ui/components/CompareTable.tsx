import React from "react";
import { Product } from "../../lib/api";
import { formatPkr } from "../../lib/format";

export function CompareTable(props: { items: Product[]; bestId: string | null; onOpen: (id: string) => void }) {
  const cols: { label: string; key: (p: Product) => React.ReactNode; numeric?: boolean }[] = [
    { label: "Product", key: (p) => <span className="font-medium">{p.product_title}</span> },
    { label: "Store", key: (p) => <span className="cell-muted">{p.marketplace}</span> },
    { label: "Price", key: (p) => formatPkr(p.price), numeric: true },
    { label: "Rating", key: (p) => (p.rating ?? "—"), numeric: true },
    { label: "Reviews", key: (p) => (p.review_count ?? "—"), numeric: true },
    { label: "Value", key: (p) => p.best_value_score.toFixed(3), numeric: true },
  ];

  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {cols.map((c) => (
              <th key={c.label} className={c.numeric ? "cell-num" : ""}>
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {props.items.map((p) => (
            <tr
              key={p.id}
              className={p.id === props.bestId ? "row-best" : ""}
              onClick={() => props.onOpen(p.id)}
              title={p.id === props.bestId ? "Best value pick" : "View details"}
            >
              {cols.map((c) => (
                <td key={c.label} className={c.numeric ? "cell-num" : ""}>
                  {c.key(p)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="body-text mt-3">Highlighted row = best overall value across stores.</p>
    </div>
  );
}
