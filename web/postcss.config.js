/**
 * PostCSS configuration
 * Uses ESM syntax because `package.json` specifies `"type": "module"`.
 * Tailwind CSS and Autoprefixer are loaded as PostCSS plugins.
 */

export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
