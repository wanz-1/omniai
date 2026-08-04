/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['localhost', 'omniai.app'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/v1/:path*',
      },
      {
        source: '/ws',
        destination: 'http://localhost:8000/api/v1/ws',
      },
    ];
  },
};

module.exports = nextConfig;
