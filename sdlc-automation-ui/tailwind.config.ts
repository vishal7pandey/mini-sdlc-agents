import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Background layers
        "bg-primary": "#0d1117",
        "bg-secondary": "#161b22",
        "bg-tertiary": "#21262d",
        "bg-elevated": "#2d333b",

        // Borders
        "border-primary": "#30363d",
        "border-secondary": "#373e47",

        // Text
        "text-primary": "#e6edf3",
        "text-secondary": "#8d96a0",
        "text-tertiary": "#636e7b",

        // Accents
        "accent-primary": "#58a6ff",
        "accent-secondary": "#1f6feb",
        "accent-tertiary": "#388bfd",

        // Agent colors
        "agent-finalize": "#58a6ff",
        "agent-design": "#bc8cff",
        "agent-code": "#3fb950",
        "agent-test": "#d29922",

        // Semantic
        success: "#3fb950",
        warning: "#d29922",
        error: "#f85149",
        info: "#58a6ff",
        purple: "#bc8cff",
        teal: "#56d4dd",
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          '"Noto Sans"',
          "Helvetica",
          "Arial",
          "sans-serif",
        ],
        mono: [
          '"Berkeley Mono"',
          '"SF Mono"',
          '"Courier New"',
          "monospace",
        ],
      },
      fontSize: {
        xs: ["11px", { lineHeight: "1.5" }],
        sm: ["12px", { lineHeight: "1.5" }],
        base: ["14px", { lineHeight: "1.6" }],
        md: ["14px", { lineHeight: "1.6" }],
        lg: ["16px", { lineHeight: "1.5" }],
        xl: ["18px", { lineHeight: "1.4" }],
        "2xl": ["20px", { lineHeight: "1.3" }],
        "3xl": ["24px", { lineHeight: "1.3" }],
        "4xl": ["30px", { lineHeight: "1.2" }],
        display: ["32px", { lineHeight: "1.2" }],
      },
      spacing: {
        xs: "4px",
        sm: "8px",
        md: "16px",
        lg: "24px",
        xl: "32px",
      },
      borderRadius: {
        sm: "6px",
        DEFAULT: "8px",
        md: "8px",
        lg: "12px",
        full: "9999px",
      },
      boxShadow: {
        sm: "0 2px 8px rgba(0, 0, 0, 0.2)",
        DEFAULT: "0 4px 12px rgba(0, 0, 0, 0.3)",
        md: "0 4px 12px rgba(0, 0, 0, 0.3)",
        lg: "0 8px 24px rgba(0, 0, 0, 0.4)",
      },
      transitionDuration: {
        fast: "150ms",
        normal: "250ms",
      },
    },
  },
  plugins: [],
};

export default config;
