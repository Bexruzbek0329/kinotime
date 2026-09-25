import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#6366f1', foreground: '#fff' },
        sidebar: { bg: '#0f0f1a', border: '#1e1e2e' },
      },
    },
  },
  plugins: [],
};

export default config;
