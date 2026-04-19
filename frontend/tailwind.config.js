/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#6366F1',
          dark: '#4F46E5',
          light: '#818CF8',
          glow: 'rgba(99, 102, 241, 0.35)',
        },
        accent: {
          DEFAULT: '#5B6AF0',
          cyan: '#22D3EE',
          pink: '#F472B6',
          amber: '#FBBF24',
          DEFAULT: '#5B6AF0',
          dim: '#1E2340',
        },
        background: '#0B0F1A',
        surface: {
          DEFAULT: 'rgba(15, 23, 42, 0.6)',
          solid: '#0F172A',
          raised: 'rgba(30, 41, 59, 0.5)',
        },
        'surface-alt': 'rgba(51, 65, 85, 0.3)',
        glass: {
          DEFAULT: 'rgba(15, 23, 42, 0.40)',
          light: 'rgba(30, 41, 59, 0.35)',
          border: 'rgba(148, 163, 184, 0.12)',
        },
        border: {
          DEFAULT: 'rgba(148, 163, 184, 0.12)',
          hover: 'rgba(148, 163, 184, 0.25)',
        },
        text: {
          DEFAULT: '#F1F5F9',
          muted: '#94A3B8',
          faint: '#64748B',
        },
        success: { DEFAULT: '#34D399', glow: 'rgba(52, 211, 153, 0.25)' },
        warning: { DEFAULT: '#FBBF24', glow: 'rgba(251, 191, 36, 0.25)' },
        danger: { DEFAULT: '#F87171', glow: 'rgba(248, 113, 113, 0.25)' },

        // Neutral aliases used by the simplified sidebar styles
        bg: '#0A0A0A',
        card: '#1E1E1E',
        muted: '#6B6B6B',
        soft: '#9A9A9A',
        coral: '#E8694A',
        green: '#2DB8A0',
        amber: '#F0C040',
        white: '#FFFFFF',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        '2xs': ['11px', '14px'],
        xs: ['12px', '16px'],
        sm: ['13px', '18px'],
        base: ['15px', '22px'],
        lg: ['18px', '26px'],
        xl: ['20px', '28px'],
        '2xl': ['24px', '32px'],
      },
      fontWeight: {
        normal: '400',
        medium: '500',
        semibold: '600',
      },
      letterSpacing: {
        tight: '-0.02em',
      },
      spacing: {
        '1': '4px',
        '2': '8px',
        '3': '12px',
        '4': '16px',
        '5': '20px',
        '6': '24px',
        '8': '32px',
        '10': '40px',
        '12': '48px',
      },
      borderRadius: {
        sm: '6px',
        md: '8px',
        lg: '12px',
        xl: '16px',
      },
      boxShadow: {
        glass: '0 8px 32px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.05)',
        'glass-sm': '0 4px 16px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.04)',
        'glass-lg': '0 16px 48px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.06)',
        glow: '0 0 20px rgba(99, 102, 241, 0.3)',
        'glow-lg': '0 0 40px rgba(99, 102, 241, 0.2)',
        focus: '0 0 0 2px rgba(91, 106, 240, 0.3)',
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'fade-slide-up': 'fadeSlideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'fade-in': 'fadeIn 0.3s ease-out forwards',
        shimmer: 'shimmer 2s linear infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        float: 'float 6s ease-in-out infinite',
        'bounce-dot': 'bounceDot 1.4s infinite ease-in-out both',
        'gradient-shift': 'gradientShift 8s ease infinite',
      },
      keyframes: {
        fadeSlideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        bounceDot: {
          '0%, 80%, 100%': { transform: 'scale(0)' },
          '40%': { transform: 'scale(1)' },
        },
        gradientShift: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
      },
      transitionProperty: {
        colors: 'color, background-color, border-color, text-decoration-color, fill, stroke',
      },
      transitionDuration: {
        DEFAULT: '150ms',
      },
      transitionTimingFunction: {
        DEFAULT: 'ease',
      },
    },
  },
  plugins: [],
}
