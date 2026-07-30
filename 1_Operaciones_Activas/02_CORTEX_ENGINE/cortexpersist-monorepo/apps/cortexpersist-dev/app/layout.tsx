import type { Metadata } from 'next';
import type { ReactNode } from 'react';

export const metadata: Metadata = {
  metadataBase: new URL('https://cortexpersist.dev'),
  title: {
    default: 'CORTEX-Persist Dev Hub — SDK & Integration',
    template: '%s | CORTEX-Persist Dev Hub',
  },
  description:
    'Developer portal and SDK documentation for CORTEX-Persist. Build sovereign agent architectures with zero-latency cryptographic storage.',
  alternates: { canonical: 'https://cortexpersist.dev' },
  openGraph: {
    type: 'website',
    url: 'https://cortexpersist.dev',
    siteName: 'CORTEX-Persist Dev Hub',
    images: [{ url: '/og-image-dev.png', width: 1200, height: 630 }],
  },
  twitter: {
    card: 'summary_large_image',
    creator: '@bakaladetroya',
    site: '@bakaladetroya',
  },
};

const schemaMarkup = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: 'CORTEX-Persist Developer Hub',
  url: 'https://cortexpersist.dev',
  author: {
    '@type': 'Person',
    name: 'Borja Moskv',
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(schemaMarkup) }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
