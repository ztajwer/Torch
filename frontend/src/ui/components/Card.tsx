import React from "react";
import clsx from "clsx";

export function Card(props: { title?: string; right?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <div className={clsx("torch-card glass-panel overflow-hidden", props.className)}>
      {(props.title || props.right) && (
        <div
          className="flex items-center justify-between gap-3 px-5 py-3.5 border-b"
          style={{ borderColor: "var(--border-dim)", background: "rgba(0,0,0,0.2)" }}
        >
          <div className="section-heading-3d" style={{ fontSize: "0.9375rem" }}>
            {props.title}
          </div>
          {props.right}
        </div>
      )}
      <div className="p-5 body-text">{props.children}</div>
    </div>
  );
}
