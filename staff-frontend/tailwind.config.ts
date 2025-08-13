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
<<<<<<< HEAD
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
=======
        // MCP Codex Brand Colors - Purple Theme
        primary: {
          50: '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#a855f7', // Main purple
          600: '#9333ea',
          700: '#7c3aed',
          800: '#6b21a8',
          900: '#581c87',
          950: '#3b0764',
        },
        secondary: {
          50: '#eff8ff',
          100: '#dbeefe',
          200: '#bfe1fe',
          300: '#93d0fd',
          400: '#60b4fa',
          500: '#3b96f6',
          600: '#2477eb', // Main blue
          700: '#1d63d8',
          800: '#1e51af',
          900: '#1e468a',
          950: '#172c54',
        },
        // Dark theme colors (matching globals.css variables)
        dark: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1', // --muted-foreground
          400: '#94a3b8',
          500: '#64748b', // --muted
          600: '#475569', // --border
          700: '#334155', // --surface-hover, --card-border
          800: '#1e293b', // --surface, --card-background
          900: '#0f172a', // --background, --code-background
          950: '#020617', // Darkest background
        },
        // Success, warning, error colors
        success: {
          50: '#f0fdf4',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        warning: {
          50: '#fffbeb',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
        error: {
          50: '#fef2f2',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'Monaco', 'monospace'],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
>>>>>>> main
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1' }],
        '6xl': ['3.75rem', { lineHeight: '1' }],
      },
<<<<<<< HEAD
      borderRadius: {
        xl: '0.875rem',
=======
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      borderRadius: {
        'xl': '0.875rem',
>>>>>>> main
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      boxShadow: {
<<<<<<< HEAD
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
=======
        'card': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'card-hover': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'glow': '0 0 20px rgba(243, 122, 10, 0.3)',
        'glow-blue': '0 0 20px rgba(36, 119, 235, 0.3)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'gradient-primary': 'linear-gradient(135deg, #f37a0a 0%, #e45e07 100%)',
        'gradient-secondary': 'linear-gradient(135deg, #2477eb 0%, #1d63d8 100%)',
        'gradient-dark': 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
>>>>>>> main
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
<<<<<<< HEAD
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
=======
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(243, 122, 10, 0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(243, 122, 10, 0.6)' },
>>>>>>> main
        },
      },
    },
  },
  plugins: [
<<<<<<< HEAD
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
=======
    function ({ addUtilities }) {
      const newUtilities = {
        '.bg-dark-900': {
          'background-color': '#0f172a',
        },
        '.bg-dark-800': {
          'background-color': '#1e293b',
        },
        '.bg-dark-700': {
          'background-color': '#334155',
        },
        '.border-dark-700': {
          'border-color': '#475569',
        },
        '.border-dark-600': {
          'border-color': '#334155',
        },
        '.text-dark-300': {
          'color': '#94a3b8',
        },
        '.text-dark-400': {
          'color': '#64748b',
        },
        '.shadow-glow': {
          'box-shadow': '0 0 20px rgba(243, 122, 10, 0.3)',
        },
        '.shadow-glow-blue': {
          'box-shadow': '0 0 20px rgba(36, 119, 235, 0.3)',
        },
        '.bg-gradient-primary': {
          'background': 'linear-gradient(135deg, #f37a0a 0%, #e45e07 100%)',
        },
        '.bg-gradient-secondary': {
          'background': 'linear-gradient(135deg, #2477eb 0%, #1d63d8 100%)',
        },
        '.bg-gradient-dark': {
          'background': 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        },
        '.bg-gray-750': {
          'background-color': '#374151',
        },
        '.hover\\:bg-gray-750:hover': {
          'background-color': '#374151',
>>>>>>> main
        },
      }
      addUtilities(newUtilities)
    },
  ],
}

export default config