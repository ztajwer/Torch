const KEY = "torch_recent_searches";
const MAX = 8;

export type RecentSearch = {
  query: string;
  matches: number;
  at: string;
};

export function loadRecentSearches(): RecentSearch[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as RecentSearch[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveRecentSearch(query: string, matches: number) {
  const q = query.trim();
  if (q.length < 2) return;
  const list = loadRecentSearches().filter((x) => x.query.toLowerCase() !== q.toLowerCase());
  list.unshift({ query: q, matches, at: new Date().toISOString() });
  localStorage.setItem(KEY, JSON.stringify(list.slice(0, MAX)));
}
