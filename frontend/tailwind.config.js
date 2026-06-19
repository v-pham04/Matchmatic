/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Match score colours
        high:   { DEFAULT: "#16a34a", light: "#dcfce7" },
        medium: { DEFAULT: "#d97706", light: "#fef3c7" },
        low:    { DEFAULT: "#dc2626", light: "#fee2e2" },
      },
    },
  },
  plugins: [],
}

