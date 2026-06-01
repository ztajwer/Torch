import React from "react";
import { RefreshCw } from "lucide-react";
import { ParallaxBackground } from "./components/ParallaxBackground";
import { SearchPage } from "./pages/SearchPage";
import { ProductsPage } from "./pages/ProductsPage";
import { ProductDetailsPage } from "./pages/ProductDetailsPage";
import { TrendingPage } from "./pages/TrendingPage";
import { ComparePage } from "./pages/ComparePage";
import { TorchChat } from "./components/TorchChat";
import { api } from "../lib/api";

type Route =
  | { name: "search"; q?: string }
  | { name: "products"; q?: string; compareIds?: string[] }
  | { name: "product"; id: string }
  | { name: "trending" }
  | { name: "compare"; q?: string; ids?: string[] };

function parseHash(): Route {
  const h = (window.location.hash || "#/search").replace(/^#/, "");
  const [path, qs] = h.split("?");
  const parts = path.split("/").filter(Boolean);
  const params = new URLSearchParams(qs || "");

  if (parts[0] === "search") return { name: "search", q: params.get("q") || undefined };
  if (parts[0] === "trending") return { name: "trending" };
  if (parts[0] === "products" && parts[1]) return { name: "product", id: parts[1] };

  if (parts[0] === "products") {
    const compareIds = (params.get("ids") || "").split(",").map((x) => x.trim()).filter(Boolean);
    const q = params.get("q") || undefined;
    return { name: "products", q, compareIds: compareIds.length ? compareIds : undefined };
  }

  if (parts[0] === "compare") {
    const ids = (params.get("ids") || "").split(",").map((x) => x.trim()).filter(Boolean);
    return {
      name: "compare",
      q: params.get("q") || undefined,
      ids: ids.length ? ids : undefined,
    };
  }

  if (["dashboard", "analytics", "marketplaces"].includes(parts[0] ?? "")) {
    return { name: "search" };
  }

  return { name: "search" };
}

function navTo(hash: string) {
  window.location.hash = hash;
}

export function App() {
  const [route, setRoute] = React.useState<Route>(() => parseHash());
  const [refreshing, setRefreshing] = React.useState(false);
  const [toast, setToast] = React.useState<string | null>(null);

  React.useEffect(() => {
    const onHash = () => {
      const h = (window.location.hash || "").replace(/^#/, "");
      const legacy = h.split("/")[0]?.split("?")[0];
      if (["dashboard", "analytics", "marketplaces"].includes(legacy)) {
        window.location.replace("#/search");
        return;
      }
      setRoute(parseHash());
    };
    window.addEventListener("hashchange", onHash);
    onHash();
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  async function refresh() {
    setRefreshing(true);
    try {
      await api.refresh();
      setToast("Updating stores in the background…");
    } catch (e) {
      setToast(`Update failed: ${(e as Error).message}`);
    } finally {
      setRefreshing(false);
      setTimeout(() => setToast(null), 3500);
    }
  }

  function scrollToSearch() {
    navTo("#/search");
    setTimeout(() => document.getElementById("torch-search")?.focus(), 100);
  }

  function goAnalyze(q: string) {
    navTo(q ? `#/search?q=${encodeURIComponent(q)}` : "#/search");
  }

  const isSearch = route.name === "search";
  const isProducts = route.name === "products" || route.name === "product";
  const isTrending = route.name === "trending";
  const isCompare = route.name === "compare";
  const useWide = isProducts || isTrending || isCompare;

  return (
    <div className="app-shell">
      <ParallaxBackground />
      <div className={`app-container ${useWide ? "app-container--wide" : ""}`}>
        <header className="site-header glass-panel">
          <div className="header-inner">
            <button type="button" onClick={() => navTo("#/search")} className="brand-lockup" aria-label="Home">
              <img src="/logo.png" alt="Torch" className="site-logo" />
            </button>

            <nav className="header-nav" aria-label="Main">
              <button type="button" onClick={() => navTo("#/search")} className={`nav-link ${isSearch ? "active" : ""}`}>
                Home
              </button>
              <button type="button" onClick={() => navTo("#/trending")} className={`nav-link ${isTrending ? "active" : ""}`}>
                Trending
              </button>
              <button type="button" onClick={() => navTo("#/products")} className={`nav-link ${isProducts ? "active" : ""}`}>
                Products
              </button>
              <button type="button" onClick={() => navTo("#/compare")} className={`nav-link ${isCompare ? "active" : ""}`}>
                Compare
              </button>
            </nav>

            <div className="header-actions">
              <button type="button" onClick={scrollToSearch} className="btn-header-cta">
                Analyze Now →
              </button>
              <button
                type="button"
                onClick={() => void refresh()}
                disabled={refreshing}
                className="menu-btn"
                title="Update all stores"
              >
                <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>
        </header>

        <main className="page-wrap">
          {route.name === "search" && (
            <SearchPage
              initialQuery={route.q}
              onOpenProduct={(id) => navTo(`#/products/${id}`)}
            />
          )}
          {route.name === "trending" && (
            <TrendingPage onOpen={(id) => navTo(`#/products/${id}`)} onAnalyze={goAnalyze} />
          )}
          {route.name === "products" && (
            <ProductsPage
              initialSearch={route.q}
              compareIds={route.compareIds}
              onOpen={(id) => navTo(`#/products/${id}`)}
              onGoHome={goAnalyze}
              onClearCompare={() => navTo(route.q ? `#/products?q=${encodeURIComponent(route.q)}` : "#/products")}
            />
          )}
          {route.name === "product" && (
            <ProductDetailsPage
              id={route.id}
              onBack={() => navTo("#/products")}
              onCompare={(ids) => navTo(`#/compare?ids=${ids.join(",")}`)}
            />
          )}
          {route.name === "compare" && (
            <ComparePage
              initialQuery={route.q}
              initialIds={route.ids}
              onOpen={(id) => navTo(`#/products/${id}`)}
              onAnalyze={goAnalyze}
            />
          )}
        </main>

        <footer className="app-footer">
          <p>Daraz · PriceOye · Telemart · Mega.pk · Shophive — PKR</p>
        </footer>
      </div>

      {toast && <div className="toast-bar glass-panel">{toast}</div>}
      <TorchChat />
    </div>
  );
}
