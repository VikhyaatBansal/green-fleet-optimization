/** @type {import('next').NextConfig} */
const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || 'http://backend:8000';

const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/vessels',
        destination: `${BACKEND_URL}/vessels`,
      },
      {
        source: '/fuels',
        destination: `${BACKEND_URL}/fuels`,
      },
      {
        source: '/routes',
        destination: `${BACKEND_URL}/routes`,
      },
      {
        source: '/metrics',
        destination: `${BACKEND_URL}/metrics`,
      },
      {
        source: '/predict/:path*',
        destination: `${BACKEND_URL}/predict/:path*`,
      },
      {
        source: '/optimize',
        destination: `${BACKEND_URL}/optimize`,
      },
      {
        source: '/scenario',
        destination: `${BACKEND_URL}/scenario`,
      },
      {
        source: '/benchmark',
        destination: `${BACKEND_URL}/benchmark`,
      },
    ];
  },
};

export default nextConfig;
