/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', "system-ui", "sans-serif"],
      },
      colors: {
        bg: "#0a0a0f",
        card: "#12121a",
        "card-muted": "#1a1a26",
        border: "rgba(255, 255, 255, 0.08)",
        text: "#f8fafc",
        muted: "#94a3b8",
        brand: "#f97316",
        "brand-dark": "#ea580c",
        "brand-light": "#fb923c",
        hover: "rgba(249, 115, 22, 0.08)",
        accent: "#fdba74",
      },
      boxShadow: {
        soft: "0 8px 32px rgba(0, 0, 0, 0.35)",
        card: "0 8px 32px rgba(0, 0, 0, 0.45)",
        glow: "0 0 40px rgba(249, 115, 22, 0.25), 0 8px 24px rgba(0, 0, 0, 0.4)",
        input: "0 0 0 3px rgba(249, 115, 22, 0.2)",
      },
      borderRadius: {
        "3xl": "1.25rem",
        "4xl": "1.5rem",
      },
    },
  },
  plugins: [],
};
