import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        accent: { DEFAULT: '#CFF800', dim: 'rgba(207,248,0,0.15)', glow: 'rgba(207,248,0,0.08)' },
        bg:     { DEFAULT: 'transparent', panel: 'rgba(10, 10, 12, 0.6)', raised: 'rgba(20, 20, 24, 0.8)' },
        line:   'rgba(207,248,0,0.3)',
        ink:    { DEFAULT: '#e8e8ea', mute: '#8b8b93' },
        up:     '#22c55e',
        down:   '#ef4444',
      },
      fontFamily: {
        sans: ['var(--font-geist-sans)'],
        mono: ['var(--font-geist-mono)'],
      },
    },
  },
  plugins: [],
};
export default config;
