import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Proxy /api/* requests to the FastAPI backend during development.
  // This avoids CORS issues in the browser since requests appear same-origin.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/:path*`,
      },
    ];
  },

  // Image domains (for avatar URLs from external sources)
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "ui-avatars.com",
      },
    ],
  },
};

export default nextConfig;
