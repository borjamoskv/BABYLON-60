import type { LucideIcon } from 'lucide-react';

type Action = {
  label: string;
  icon: LucideIcon;
  onClick: () => void;
  tone: 'ghost' | 'accent' | 'alert';
};

type TopbarActionsProps = {
  actions: Action[];
};

export function TopbarActions({ actions }: TopbarActionsProps) {
  return (
    <div className="topbar-actions">
      {actions.map(({ icon: Icon, label, onClick, tone }) => (
        <button className={`topbar-button topbar-button--${tone}`} key={label} onClick={onClick} type="button">
          <Icon aria-hidden="true" />
          <span>{label}</span>
        </button>
      ))}
    </div>
  );
}
