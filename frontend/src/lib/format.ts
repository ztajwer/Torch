/** Format amount as Pakistani Rupees (whole rupees, comma-separated). */
export function formatPkr(price: number | undefined | null): string {
  if (price == null || Number.isNaN(price)) return "—";
  const n = Math.round(price);
  if (n <= 0) return "—";
  return `Rs ${n.toLocaleString("en-PK")}`;
}

/** Remove dollar amounts from AI-generated text (prices come from cards in PKR). */
export function sanitizeAiText(text: string): string {
  return text
    .replace(/\$\s*[\d,.]+/g, "")
    .replace(/\bUSD\b/gi, "PKR")
    .replace(/\s{2,}/g, " ")
    .trim();
}
