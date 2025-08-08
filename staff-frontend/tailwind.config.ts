import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          '50': '#f0fdfa',
          '100': '#ccfbf1',
          '200': '#99f6e4',
          '300': '#5eead4',
          '400': '#2dd4bf',
          '500': '#14b8a6',
          '600': '#0d9488',
          '700': '#0f766e',
          '800': '#115e59',
          '900': '#134e4a',
          '950': '#042f2e',
        },
        secondary: {
          '50': '#fff7ed',
          '100': '#ffedd5',
          '200': '#fed7aa',
          '300': '#fdba74',
          '400': '#fb923c',
          '500': '#f97316',
          '600': '#ea580c',
          '700': '#c2410c',
          '800': '#9a3412',
          '900': '#7c2d12',
          '950': '#431407',
        },
        dark: {
          '50': '#f8fafc',
          '100': '#f1f5f9',
          '200': '#e2e8f0',
          '300': '#cbd5e1',
          '400': '#94a3b8',
          '500': '#64748b',
          '600': '#475569',
          '700': '#334155',
          '800': '#1e293b',
          '900': '#0f172a',
          '950': '#020617',
        },
        success: {
          '50': '#f0fdf4',
          '500': '#22c55e',
          '600': '#16a34a',
          '700': '#15803d',
        },
        warning: {
          '50': '#fffbeb',
          '500': '#f59e0b',
          '600': '#d97706',
          '700': '#b45309',
        },
        error: {
          '50': '#fef2f2',
          '500': '#ef4444',
          '600': '#dc2626',
          '700': '#b91c1c',
        },
      },
      fontFamily: {
        sans: ['Satoshi', 'Inter', 'system-ui', 'sans-serif'],
        display: ['Mona-Sans', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'Monaco', 'monospace'],
      },
      fontSize: {
        xs: ['0.75rem', { lineHeight: '1rem' }],
        sm: ['0.875rem', { lineHeight: '1.25rem' }],
        base: ['1rem', { lineHeight: '1.5rem' }],
        lg: ['1.125rem', { lineHeight: '1.75rem' }],
        xl: ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1' }],
        '6xl': ['3.75rem', { lineHeight: '1' }],
      },
      borderRadius: {
        xl: '0.875rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      boxShadow: {
        'inner-border': 'inset 0 0 0 1px rgba(255, 255, 255, 0.1)',
        'soft-glow': '0 0 10px rgba(20, 184, 166, 0.2)',
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
        'card-hover': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #2dd4bf 0%, #14b8a6 100%)',
        'gradient-secondary': 'linear-gradient(135deg, #fb923c 0%, #f97316 100%)',
        'gradient-dark': 'linear-gradient(180deg, #0f172a 0%, #020617 100%)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out forwards',
        'slide-up': 'slideUp 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards',
        'slide-down': 'slideDown 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards',
        'subtle-pulse': 'subtlePulse 2.5s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        subtlePulse: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.02)' },
        },
      },
    },
  },
  plugins: [
    function ({ addUtilities }: { addUtilities: (utilities: Record<string, any>) => void }) {
      const newUtilities = {
        '.glassmorphism': {
          'background': 'rgba(255, 255, 255, 0.1)',
          'backdrop-filter': 'blur(10px)',
          '-webkit-backdrop-filter': 'blur(10px)',
          'border': '1px solid rgba(255, 255, 255, 0.2)',
        },
        '.text-gradient-primary': {
          'background': 'linear-gradient(135deg, #2dd4bf 0%, #14b8a6 100%)',
          '-webkit-background-clip': 'text',
          '-webkit-text-fill-color': 'transparent',
        },
        '.text-gradient-secondary': {
            'background': 'linear-gradient(135deg, #fb923c 0%, #f97316 100%)',
            '-webkit-background-clip': 'text',
            '-webkit-text-fill-color': 'transparent',
        },
      }
      addUtilities(newUtilities)
    },
  ],
}

export default config