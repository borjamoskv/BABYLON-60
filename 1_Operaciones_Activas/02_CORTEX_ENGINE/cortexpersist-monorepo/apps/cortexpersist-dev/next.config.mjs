/** @type {import('next').NextConfig} */
const config = {
  transpilePackages: ['@cortex/ui', '@cortex/sdk'],
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Cortex-Domain', value: 'cortexpersist.dev' },
          { key: 'Access-Control-Allow-Origin', value: 'https://cortexpersist.com' },
        ],
      },
    ];
  },
};

export default config;
