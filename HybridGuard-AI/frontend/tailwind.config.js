/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          950: '#070a12',
          900: '#0c111e',
          850: '#111827',
          800: '#182236',
          700: '#22304d',
          600: '#334468',
        },
        primary: {
          50: '#edf5ff',
          100: '#d6e8ff',
          200: '#b5d7ff',
          300: '#83beff',
          400: '#4a9aff',
          500: '#2077fa',
          600: '#0d57ed',
          700: '#0a42cb',
          800: '#0e38a3',
          900: '#113380',
        },
      },
    },
  },
  plugins: [],
}
