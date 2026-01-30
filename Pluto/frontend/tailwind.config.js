/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: '[data-theme="dark"]',
  theme: {
    extend: {
      colors: {
        pluto: {
          purple: '#6366f1',
          'purple-dark': '#4f46e5',
          'purple-light': '#a5b4fc',
        },
        dark: {
          bg: '#1B1B1D',
          surface: '#14141f',
          'surface-glass': 'rgba(20, 20, 31, 0.7)',
          border: '#1f1f2e',
          text: '#e5e7eb',
          'text-muted': '#9ca3af',
        },
        light: {
          bg: '#ffffff',
          surface: '#DADADA',
          border: '#e5e7eb',
          text: '#111827',
          'text-muted': '#6b7280',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      spacing: {
        '260': '260px',
        '300': '300px',
      },
      maxWidth: {
        'desktop': '1440px',
      },
      backdropBlur: {
        'glass': '20px',
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '14px',
      },
    },
  },
  plugins: [],
}
