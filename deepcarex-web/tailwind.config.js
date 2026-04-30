/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        deepnavy: '#0a0f1e',
        cyan: {
          400: '#00d4ff', // Glowing neon cyan
        },
        biogreen: '#00ff88',
        alertred: '#ff4d6d',
        purpleaccent: '#7b2fff'
      },
      fontFamily: {
        interface: ['Inter', 'sans-serif'],
        mono: ['Space Grotesk', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
      animation: {
        'scan': 'scan 2s linear infinite',
        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'heartbeat': 'heartbeat 1.5s ease-in-out infinite',
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' }
        },
        'pulse-glow': {
          '0%, 100%': { opacity: 1, boxShadow: '0 0 10px #00d4ff, 0 0 20px #00d4ff' },
          '50%': { opacity: .7, boxShadow: '0 0 5px #00d4ff, 0 0 10px #00d4ff' },
        },
        heartbeat: {
          '0%, 100%': { transform: 'scale(1)' },
          '25%': { transform: 'scale(1.1)' },
          '50%': { transform: 'scale(1)' },
          '75%': { transform: 'scale(1.1)' },
        }
      }
    },
  },
  plugins: [],
}
