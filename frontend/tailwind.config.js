/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Arial', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 10px 28px rgba(214, 36, 36, 0.12)',
      },
    },
  },
  plugins: [],
};
