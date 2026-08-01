/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter Variable", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        terracotta: "#C96F45",
        "terracotta-dark": "#A85A38",
        cream: "#F5F1EA",
        ivory: "#F0E0C8",
        espresso: "#3A2A1E",
        "warm-gray": "#8A7A6A",
        "near-black": "#1E1B16",
        sage: "#3D5A3D",
        rust: "#B5533C",
      },
    },
  },
  plugins: [],
}
