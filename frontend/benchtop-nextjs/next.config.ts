// frontend/benchtop-nextjs/next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Your existing config options can go here if you have any.
  // For example: reactStrictMode: true,
  
  // --- ADD THIS WEBPACK CONFIGURATION BLOCK ---
  webpack: (config, { isServer }) => {
    // This configuration helps resolve issues with libraries that rely on
    // Node.js core modules in a browser environment.
    
    // For 'buffer', we direct the bundler to use the 'buffer' package,
    // which is a browser-compatible polyfill.
    config.resolve.alias = {
      ...config.resolve.alias,
      "buffer": "buffer",
    };

    // This ensures that the polyfill is available globally, which some
    // libraries like plotly.js might expect.
    config.plugins.push(
      new (require('webpack').ProvidePlugin)({
        Buffer: ['buffer', 'Buffer'],
      })
    );

    return config;
  },
};

export default nextConfig;