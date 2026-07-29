// Multi-Locale Dictionary for BABYLON 60 (C5-REAL i18n Transducer)

export type Locale = 'en' | 'es' | 'pt' | 'de' | 'fr' | 'ja';

export interface Translations {
  urgencyBanner: string;
  urgencyLink: string;
  badge: string;
  heroHeadingStart: string;
  heroHeadingAccent: string;
  heroSubheading: string;
  ctaPro: string;
  ctaQuickstart: string;
  pricingTitle: string;
  pricingSub: string;
  monthly: string;
  annual: string;
  mostPopular: string;
  communityTitle: string;
  communityDesc: string;
  communityCta: string;
  proTitle: string;
  proDesc: string;
  proCta: string;
  enterpriseTitle: string;
  enterpriseDesc: string;
  enterpriseCta: string;
}

export const translations: Record<Locale, Translations> = {
  en: {
    urgencyBanner: '⚠️ EU AI ACT ENFORCEMENT (AUGUST 2026): Non-compliant AI systems face fines up to €30M.',
    urgencyLink: 'Explore Enterprise Compliance Tiers →',
    badge: '⚡ B2B SaaS & Enterprise Sovereign Engine',
    heroHeadingStart: 'Prove your AI agents\' integrity ',
    heroHeadingAccent: 'in <5ms',
    heroSubheading: 'BABYLON 60 is the deterministic memory substrate with Ed25519/SHA3-256 cryptographic signatures for autonomous agent teams. Zero cloud lock-in, 100% auditable.',
    ctaPro: 'Get Pro License ($49/mo)',
    ctaQuickstart: 'Quickstart SDK (30s)',
    pricingTitle: 'Sovereign Tiers & Commercial Licensing',
    pricingSub: 'Free and 100% Open Source for independent developers. Mandatory commercial licensing and compliance for enterprise deployments (INV_C5_17).',
    monthly: 'Monthly Billing',
    annual: 'Annual Billing (20% Off)',
    mostPopular: 'MOST POPULAR',
    communityTitle: 'Community',
    communityDesc: 'For indie developers and non-commercial projects. Complete local autonomy with zero cloud dependency.',
    communityCta: 'Explore GitHub',
    proTitle: 'Pro Team',
    proDesc: 'For startups and production teams running autonomous agents requiring tamper-evident auditing and SLA performance.',
    proCta: 'Get Pro License ➔',
    enterpriseTitle: 'Enterprise Sovereign',
    enterpriseDesc: 'For large enterprise organizations requiring dedicated Private Cloud isolation (GCP/AWS WIF) and legal compliance certification.',
    enterpriseCta: 'Contact Enterprise ➔',
  },
  es: {
    urgencyBanner: '⚠️ CUMPLIMIENTO EU AI ACT (AGOSTO 2026): Las empresas sin registro inmutable se enfrentan a multas de hasta 30M€.',
    urgencyLink: 'Ver Planes de Licencia Empresarial →',
    badge: '⚡ Motor Soberano B2B SaaS & Enterprise',
    heroHeadingStart: 'Demuestra la integridad de tus agentes IA ',
    heroHeadingAccent: 'en <5ms',
    heroSubheading: 'BABYLON 60 es el sustrato de memoria determinista y firma criptográfica Ed25519/SHA3-256 para equipos de agentes autónomos. 0% dependencia de la nube, 100% auditable.',
    ctaPro: 'Obtener Licencia Pro ($49/mes)',
    ctaQuickstart: 'Quickstart SDK (30s)',
    pricingTitle: 'Planes Soberanos & Licencia Empresarial',
    pricingSub: 'Gratis y 100% Open Source para desarrolladores independientes. Licencia comercial y compliance obligatorio para empresas (INV_C5_17).',
    monthly: 'Facturación Mensual',
    annual: 'Facturación Anual (20% Dcto)',
    mostPopular: 'MÁS POPULAR',
    communityTitle: 'Comunidad',
    communityDesc: 'Para desarrolladores independientes y proyectos no comerciales. Autonomía total sin depender de la nube.',
    communityCta: 'Explorar GitHub',
    proTitle: 'Pro Team',
    proDesc: 'Para startups y equipos de producción que ejecutan agentes autónomos con requisitos de auditoría y rendimiento.',
    proCta: 'Obtener Licencia Pro ➔',
    enterpriseTitle: 'Enterprise Sovereign',
    enterpriseDesc: 'Para grandes corporaciones que requieren aislamiento en nube privada (GCP/AWS WIF) y certificación de cumplimiento legal.',
    enterpriseCta: 'Contactar Enterprise ➔',
  },
  pt: {
    urgencyBanner: '⚠️ CONFORMIDADE EU AI ACT (AGOSTO 2026): Sistemas sem registro imutável enfrentam multas de até €30M.',
    urgencyLink: 'Ver Planos de Conformidade →',
    badge: '⚡ Motor Soberano B2B SaaS & Enterprise',
    heroHeadingStart: 'Prove a integridade dos seus agentes IA ',
    heroHeadingAccent: 'em <5ms',
    heroSubheading: 'BABYLON 60 é o substrato de memória determinística com assinaturas criptográficas Ed25519/SHA3-256 para equipes de agentes autônomos.',
    ctaPro: 'Obter Licença Pro ($49/mês)',
    ctaQuickstart: 'SDK Quickstart (30s)',
    pricingTitle: 'Planos Soberanos e Licenciamento Comercial',
    pricingSub: 'Gratuito e 100% Open Source para desenvolvedores independentes. Licenciamento comercial obrigatório para empresas.',
    monthly: 'Cobrança Mensal',
    annual: 'Cobrança Anual (20% Desc.)',
    mostPopular: 'MAIS POPULAR',
    communityTitle: 'Comunidade',
    communityDesc: 'Para desenvolvedores indie e projetos não comerciais. Autonomia local completa sem nuvem.',
    communityCta: 'Explorar GitHub',
    proTitle: 'Pro Team',
    proDesc: 'Para startups e equipes de produção executando agentes autônomos.',
    proCta: 'Obter Licença Pro ➔',
    enterpriseTitle: 'Enterprise Sovereign',
    enterpriseDesc: 'Para grandes corporações que exigem isolamento em nuvem privada (GCP/AWS WIF) e certificação de conformidade.',
    enterpriseCta: 'Contatar Enterprise ➔',
  },
  de: {
    urgencyBanner: '⚠️ EU AI ACT EINHALTUNG (AUGUST 2026): Nichtkonforme KI-Systeme drohen Strafen bis zu 30 Mio. €.',
    urgencyLink: 'Enterprise Compliance Pläne anzeigen →',
    badge: '⚡ B2B SaaS & Enterprise Sovereign Engine',
    heroHeadingStart: 'Beweisen Sie die Integrität Ihrer KI-Agenten ',
    heroHeadingAccent: 'in <5ms',
    heroSubheading: 'BABYLON 60 ist das deterministische Speichersubstrat mit kryptografischen Ed25519/SHA3-256-Signaturen für autonome Agententeams.',
    ctaPro: 'Pro-Lizenz holen ($49/Monat)',
    ctaQuickstart: 'Quickstart SDK (30s)',
    pricingTitle: 'Souveräne Tarife & Kommerzielle Lizenzierung',
    pricingSub: 'Kostenlos und 100% Open Source für unabhängige Entwickler. Kommerzielle Lizenzierung für Unternehmen.',
    monthly: 'Monatliche Abrechnung',
    annual: 'Jährliche Abrechnung (20% Rabatt)',
    mostPopular: 'AM BELIEBTESTEN',
    communityTitle: 'Community',
    communityDesc: 'Für Indie-Entwickler und nicht-kommerzielle Projekte. Vollständige lokale Autonomie ohne Cloud-Abhängigkeit.',
    communityCta: 'GitHub erkunden',
    proTitle: 'Pro Team',
    proDesc: 'Für Start-ups und Produktionsteams, die autonome Agenten betreiben.',
    proCta: 'Pro-Lizenz holen ➔',
    enterpriseTitle: 'Enterprise Sovereign',
    enterpriseDesc: 'Für Großunternehmen, die eine dedizierte Private-Cloud-Isolierung (GCP/AWS WIF) benötigen.',
    enterpriseCta: 'Enterprise kontaktieren ➔',
  },
  fr: {
    urgencyBanner: '⚠️ CONFORMITÉ EU AI ACT (AOÛT 2026): Les systèmes d’IA non conformes risquent des amendes jusqu’à 30 M€.',
    urgencyLink: 'Explorer les plans Enterprise →',
    badge: '⚡ Moteur Souverain B2B SaaS & Enterprise',
    heroHeadingStart: 'Prouvez l’intégrité de vos agents IA ',
    heroHeadingAccent: 'en <5ms',
    heroSubheading: 'BABYLON 60 est le substrat de mémoire déterministe avec signatures cryptographiques Ed25519/SHA3-256 pour agents autonomes.',
    ctaPro: 'Obtenir la licence Pro (49 $/mois)',
    ctaQuickstart: 'SDK Quickstart (30s)',
    pricingTitle: 'Tarifs Souverains & Licences Commerciales',
    pricingSub: 'Gratuit et 100% Open Source pour les développeurs indépendants. Licence commerciale obligatoire pour les entreprises.',
    monthly: 'Facturation Mensuelle',
    annual: 'Facturation Annuelle (-20%)',
    mostPopular: 'LE PLUS POPULAIRE',
    communityTitle: 'Communauté',
    communityDesc: 'Pour les développeurs indépendants et projets non commerciaux. Autonomie locale totale.',
    communityCta: 'Explorer GitHub',
    proTitle: 'Pro Team',
    proDesc: 'Pour les startups et équipes en production gérant des agents autonomes.',
    proCta: 'Obtenir la licence Pro ➔',
    enterpriseTitle: 'Enterprise Sovereign',
    enterpriseDesc: 'Pour les grandes entreprises nécessitant un isolement Cloud Privé (GCP/AWS WIF) et certification de conformité.',
    enterpriseCta: 'Contacter Enterprise ➔',
  },
  ja: {
    urgencyBanner: '⚠️ EU AI Act 施行（2026年8月）: 不適合のAIシステムには最大3000万ユーロの制裁金。',
    urgencyLink: 'エンタープライズ準拠プランを見る →',
    badge: '⚡ B2B SaaS & エンタープライズ自立型エンジン',
    heroHeadingStart: 'AIエージェントの整合性を',
    heroHeadingAccent: '5ms未満で証明',
    heroSubheading: 'BABYLON 60は、自立型エージェントチーム向けのEd25519/SHA3-256暗号署名を備えた決定論的メモリ基盤です。クラウド依存度0%、100%監査可能。',
    ctaPro: 'Proライセンスを取得 ($49/月)',
    ctaQuickstart: 'クイックスタート SDK (30秒)',
    pricingTitle: 'ソブリンプラン & 商用ライセンス',
    pricingSub: '個人開発者には無料＆100%オープンソース。企業導入には商用ライセンスが必要となります（INV_C5_17）。',
    monthly: '月払い',
    annual: '年払い (20% OFF)',
    mostPopular: '最も人気',
    communityTitle: 'コミュニティ',
    communityDesc: '個人開発者および非商用プロジェクト向け。クラウド依存ゼロの完全ローカル自立型。',
    communityCta: 'GitHubを見る',
    proTitle: 'Pro Team',
    proDesc: '自立型エージェントを運用し、改ざん防止の監査を必要とするスタートアップおよびプロダクションチーム向け。',
    proCta: 'Proライセンスを取得 ➔',
    enterpriseTitle: 'Enterprise Sovereign',
    enterpriseDesc: '専用プライベートクラウド分離（GCP/AWS WIF）および法的コンプライアンス認証を必要とする大企業向け。',
    enterpriseCta: 'エンタープライズにお問い合わせ ➔',
  }
};

export function detectLocale(): Locale {
  if (typeof window === 'undefined') return 'en';
  const lang = (navigator.language || '').toLowerCase();
  if (lang.startsWith('es')) return 'es';
  if (lang.startsWith('pt')) return 'pt';
  if (lang.startsWith('de')) return 'de';
  if (lang.startsWith('fr')) return 'fr';
  if (lang.startsWith('ja')) return 'ja';
  return 'en';
}
