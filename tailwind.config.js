/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./core/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#2563eb",      // Azul principal (Tailwind blue-600)
        primaryLight: "#60a5fa", // Azul claro (blue-400)
        dark: "#111827",         // Casi negro (gray-900)
        graySoft: "#f3f4f6",     // Gris muy claro (background)
        grayMedium: "#9ca3af",   // Gris medio para texto
        white: "#ffffff",
      },
      fontFamily: {
        poppins: ["Poppins", "sans-serif"],
        inter: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
