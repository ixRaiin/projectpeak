/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{vue,js,ts}',
  ],
  theme: {
    container: { center: true, padding: '1rem' },
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
      },
      colors: {
        cream: {
          DEFAULT: '#FDFBF7',
          100: '#FFFEFB',
          200: '#FBF9F3',
        },
        navy: {
          DEFAULT: '#1D3557',
          600: '#1D3557',
          500: '#2C4A72',
          700: '#16314C',
        },
        graywarm: {
          border: '#E4E0DA',
          text: '#555555',
          muted: '#7A7A7A',
        },
        neutraldark: {
          DEFAULT: '#2B2B2B',
          hover: '#1F1F1F',
        },
        success: '#2F855A',
        warning: '#B7791F',
        error: '#C53030',
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
      },
      borderRadius: {
        lg: '0.5rem',
        xl: '0.75rem',
      },
    },
  },
  plugins: [],
}
