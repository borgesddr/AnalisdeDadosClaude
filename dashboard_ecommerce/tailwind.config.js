/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: '#0B2265',
          'navy-800': '#0A1F5C',
          cyan: '#29ABE2',
          'cyan-400': '#38BDF8',
          orange: '#F5A623',
        },
        bg: '#F7F8FA',
        surface: '#FFFFFF',
        border: '#E4E7EC',
        text: {
          DEFAULT: '#1A1A1A',
          muted: '#667085',
        },
        success: '#16A34A',
        warning: '#F5A623',
        danger: '#DC2626',
        neutral: '#94A3B8',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'Segoe UI', 'sans-serif'],
      },
      borderRadius: {
        '2xl': '16px',
      },
    },
  },
  plugins: [],
};
