import type { Metadata } from 'next';
import type { ReactNode } from 'react';

export const metadata: Metadata = {
  metadataBase: new URL('https://agents.archi'),
  title: {
    default: 'agents.archi — Sovereign Audit Ledger',
    template: '%s | agents.archi',
  },
  description: 'Cryptographically anchored forensic audit records powered by CORTEX-Persist.',
  alternates: { canonical: 'https://agents.archi' },
  openGraph: {
    type: 'website',
    url: 'https://agents.archi',
    siteName: 'agents.archi',
    images: [{ url: '/og-image.png', width: 1200, height: 630 }],
  },
  twitter: {
    card: 'summary_large_image',
    creator: '@bakaladetroya',
    site: '@bakaladetroya',
  },
};

const schemaMarkup = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'CORTEX-Persist Audit Engine',
  operatingSystem: 'Independent',
  applicationCategory: 'SecurityApplication',
  offers: {
    '@type': 'Offer',
    price: '0.00',
    priceCurrency: 'EUR',
  },
  author: {
    '@type': 'Person',
    name: 'Borja Moskv',
    url: 'https://cortexpersist.com',
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
