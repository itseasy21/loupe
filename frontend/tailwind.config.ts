import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        ink: '#0f172a',
        mist: '#f8fafc',
        signal: '#0f766e',
        ember: '#fb7185',
        gold: '#f59e0b'
      },
      boxShadow: {
        halo: '0 20px 80px rgba(15, 23, 42, 0.14)'
      },
      backgroundImage: {
        'loupe-grid': 'linear-gradient(rgba(15, 23, 42, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(15, 23, 42, 0.08) 1px, transparent 1px)'
      },
      fontFamily: {
        sans: ['"Space Grotesk"', '"IBM Plex Sans"', 'sans-serif']
      }
    }
  },
  plugins: []
};

export default config;
