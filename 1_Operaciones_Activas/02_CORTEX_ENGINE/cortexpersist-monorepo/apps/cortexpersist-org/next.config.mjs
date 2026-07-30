/** @type {import('next').NextConfig} */
const config = {
  transpilePackages: ['@cortex/ui', '@cortex/sdk'],
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Cortex-Domain', value: 'cortexpersist.org' },
        ],
      },
    ];
  },
};

export default config;
