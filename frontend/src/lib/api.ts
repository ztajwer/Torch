/** Pakistani e-commerce sources TORCH searches. */
export const PK_STORE_HINTS = ["PriceOye", "Daraz", "Telemart", "Shophive", "Mega.pk"] as const;

export function isPkStore(marketplace: string | undefined | null): boolean {
  const m = marketplace ?? "";
  return PK_STORE_HINTS.some((h) => m.includes(h));
}

export type Product = {
  id: string;
  product_title: string;
  price: number;
  original_price?: number | null;
  rating?: number | null;
  review_count?: number | null;
  brand_or_seller?: string | null;
  category?: string | null;
  marketplace: string;
  availability?: string | null;
  product_url: string;
  image_url?: string | null;
  timestamp_scraped: string;
  trend_score: number;
  best_value_score: number;
  canonical_id?: string;
};

export type ProductsResponse = {
  total: number;
  offset: number;
  limit: number;
  items: Product[];
};

export type Analytics = Record<string, unknown>;

export type ProductBrief = {
  id: string;
  product_title: string;
  marketplace: string;
  price: number;
  rating?: number | null;
  review_count?: number | null;
  product_url: string;
  trend_score?: number;
  best_value_score?: number;
  reason?: string;
};

export type AiRanking = {
  rank: number;
  product_id: string;
  title?: string;
  marketplace?: string;
  price?: number;
  currency?: string;
  reason?: string;
  product_url?: string;
  image_url?: string | null;
  rating?: number | null;
  relevance_percent?: number;
  value_score?: number;
};

export type AiInsights = {
  total_matches?: number;
  cheapest?: { product_title?: string; price?: number; marketplace?: string } | null;
  premium?: { product_title?: string; price?: number; marketplace?: string } | null;
  top_pick_relevance?: number;
  top_pick_value_score?: number;
  why_number_one?: string;
  intent_note?: string;
};

export type AiAdvice = {
  summary: string;
  rankings: AiRanking[];
  insights?: AiInsights;
  powered_by: "gemini" | "torch-rules" | "none" | string;
};

export type IntelligenceResult = {
  status: string;
  phase?: string;
  query: string;
  store_count?: number;
  sources_scraped: string[];
  scraped_count: number;
  total_matches: number;
  items: Product[];
  by_marketplace: Record<string, Product[]>;
  recommendations: {
    best_overall: ProductBrief | null;
    cheapest: ProductBrief | null;
    best_quality: ProductBrief | null;
    summary: string;
  };
  compare: { items: Product[]; best_id: string | null };
  user_message?: string | null;
  ai?: AiAdvice;
};

export type CompareResult = {
  items: Product[];
  best_id: string | null;
  query?: string;
  message?: string | null;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type ChatProductHint = {
  id: string;
  title: string;
  price_pkr: number;
  store: string;
  rating?: number | null;
  url?: string;
};

export type ChatResponse = {
  reply: string;
  powered_by: string;
  refused?: boolean;
  products?: ChatProductHint[];
};

/**
 * Dev: Vite proxy (empty base).
 * Production same-host (Docker/Render): empty base.
 * Split deploy: set VITE_API_BASE=https://your-api.example.com at build time.
 */
const API_BASE =
  (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, "") ??
  (import.meta.env.DEV ? "" : "");

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    let detail = text;
    try {
      const parsed = JSON.parse(text) as { detail?: string };
      if (parsed.detail) detail = typeof parsed.detail === "string" ? parsed.detail : JSON.stringify(parsed.detail);
    } catch {
      /* keep raw text */
    }
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

export const api = {
  products: (params: Record<string, string | number | undefined>) => {
    const usp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v === undefined || v === "" || v === null) return;
      usp.set(k, String(v));
    });
    return http<ProductsResponse>(`/api/products?${usp.toString()}`);
  },
  product: (id: string) => http<Product>(`/api/products/${encodeURIComponent(id)}`),
  compare: (ids: string[]) =>
    http<CompareResult>(`/api/compare?ids=${encodeURIComponent(ids.join(","))}`),
  compareByQuery: (q: string) => http<CompareResult>(`/api/compare?${new URLSearchParams({ q }).toString()}`),
  /** Cached matches from database (instant). */
  searchCached: (query: string) =>
    http<ProductsResponse>(`/api/products?${new URLSearchParams({ q: query, limit: "50", sort: "best_value_desc" }).toString()}`),

  /** Scrape all stores and return best picks (10–60 seconds). */
  intelligenceSearch: async (query: string) => {
    try {
      return await http<IntelligenceResult>("/api/intelligence/search", {
        method: "POST",
        body: JSON.stringify({ query }),
      });
    } catch {
      return http<IntelligenceResult>(
        `/api/intelligence/search?${new URLSearchParams({ q: query }).toString()}`
      );
    }
  },

  status: () => http<{ products: number; stores: number; ready: boolean }>("/api/status"),
  analytics: () => http<Analytics>("/api/analytics"),
  filterMeta: () => http<{ categories: string[]; marketplaces: string[] }>("/api/filter"),
  refresh: () => http<{ status: string }>("/api/refresh", { method: "POST" }),

  chat: (body: { message: string; history?: ChatMessage[]; context_query?: string }) =>
    http<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  /** Fetch every product (paginates automatically if needed). */
  productsAll: async (params: Record<string, string | number | undefined> = {}) => {
    const pageSize = 500;
    let offset = 0;
    let total = 0;
    const all: Product[] = [];
    do {
      const page = await api.products({ ...params, limit: pageSize, offset });
      total = page.total;
      all.push(...page.items);
      offset += page.items.length;
      if (page.items.length === 0) break;
    } while (offset < total);
    return { total, items: all };
  },
};
