/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0b0f17',
        surface: '#121826',
        kaspa: '#39d0d8',
      },
      boxShadow: {
        glow: '0 0 20px rgba(57, 208, 216, 0.35)',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', 'sans-serif'],
      },
      keyframes: {
        fadeInUp: {
          '0%': { opacity: 0, transform: 'translateY(8px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
        pulseDots: {
          '0%, 100%': { opacity: 0.2 },
          '50%': { opacity: 1 },
        },
      },
      animation: {
        fadeInUp: 'fadeInUp 0.28s ease-out both',
        pulseDots: 'pulseDots 1.2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}


