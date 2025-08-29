/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        kaspa: {
          50: '#e6fbff',
          100: '#c0f3ff',
          200: '#93e8ff',
          300: '#58d9ff',
          400: '#1cc4ff',
          500: '#00a3ff',
          600: '#0082e6',
          700: '#0064b4',
          800: '#004b87',
          900: '#00355f'
        }
      },
      boxShadow: {
        soft: '0 8px 24px rgba(0,0,0,0.25)'
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace']
      }
    },
  },
  plugins: [],
}
