import { LayoutDashboard, PackageCheck, ScrollText } from 'lucide-react';
import { decisionHref, proofHref, routeHref, type HashRoute } from '../hooks/useHashRoute';

type SidebarNavProps = {
  activeRoute: HashRoute['name'];
  activeDecisionId: string;
};

const primaryLinks = [
  { label: 'Control room', route: routeHref({ name: 'overview' }), badge: 'Live', icon: LayoutDashboard },
  { label: 'Targets', route: '#/targets', badge: 'Hunter-Ω', icon: PackageCheck },
  { label: 'Decisions', route: '#/decisions', badge: '12 open', icon: ScrollText },
];

const proofLinks = [
  { label: 'Selected decision', getHref: (decisionId: string) => decisionHref(decisionId), badge: 'Inspect' },
  { label: 'Proof package', getHref: (decisionId: string) => proofHref(decisionId), badge: 'Export' },
];

const narrativeLinks = [
  { label: 'Store', index: '01' },
  { label: 'Verify', index: '02' },
  { label: 'Tamper', index: '03' },
  { label: 'Audit', index: '04' },
  { label: 'Export proof', index: '05' },
];

export function SidebarNav({ activeRoute, activeDecisionId }: SidebarNavProps) {
  return (
    <aside className="sidebar">
      <div className="brand-card">
        <div className="brand-mark">CX</div>
        <div>
          <strong>BABYLON60 Persist</strong>
          <p>Canonical product demo</p>
        </div>
      </div>

      <div className="sidebar-section">
        <span className="sidebar-section-label">Primary</span>
        {primaryLinks.map(({ badge, icon: Icon, label, route }) => {
          const isActive =
            (label === 'Control room' && activeRoute === 'overview') ||
            (label === 'Targets' && activeRoute === 'targets') ||
            (label === 'Decisions' && activeRoute === 'decisions');

          return (
            <a className="sidebar-link" data-active={isActive} href={route} key={label}>
              <span className="sidebar-link__label">
                <Icon size={16} />
                {label}
              </span>
              <span className="section-anchor">{badge}</span>
            </a>
          );
        })}

        {proofLinks.map(({ badge, getHref, label }) => {
          const href = getHref(activeDecisionId);
          const isActive = label === 'Proof package' ? activeRoute === 'proof' : false;

          return (
            <a className="sidebar-link" data-active={isActive} href={href} key={label}>
              <span className="sidebar-link__label">
                <PackageCheck size={16} />
                {label}
              </span>
              <span className="section-anchor">{badge}</span>
            </a>
          );
        })}
      </div>

      <div className="sidebar-section sidebar-section--flow">
        <span className="sidebar-section-label">Narrative</span>
        {narrativeLinks.map((link) => (
          <div className="sidebar-link sidebar-link--static" data-active={false} key={link.label}>
            <span className="sidebar-link__label">
              <span className="sidebar-link__dot" />
              {link.label}
            </span>
            <span className="section-anchor">{link.index}</span>
          </div>
        ))}
      </div>

      <div className="sidebar-note">
        <span className="sidebar-section-label">Why this shape</span>
        <p>
          This app sells compliance operations, not generic dashboard aesthetics: decisions, tamper
          signals, audit evidence, and proof export are always first-class.
        </p>
      </div>
    </aside>
  );
}
