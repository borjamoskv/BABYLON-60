/** @type {import('next').NextConfig} */
const config = {
  transpilePackages: ['@cortex/ui', '@cortex/sdk'],
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Cortex-Domain', value: 'agents.archi' },
          { key: 'X-Robots-Tag', value: 'index, follow' },
        ],
      },
    ];
  },
};

export default config;
