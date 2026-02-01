/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        mist: "#f8fafc",
        sunrise: "#ff8a5b",
        ocean: "#2b59c3",
        moss: "#1f7a1f",
        clay: "#f2e9e4"
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        body: ["Space Grotesk", "sans-serif"]
      },
      boxShadow: {
        soft: "0 10px 30px rgba(15, 23, 42, 0.12)"
      }
    }
  },
  plugins: []
};
