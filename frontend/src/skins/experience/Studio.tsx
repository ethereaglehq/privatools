import type { ButtonHTMLAttributes, ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';
import { FolderOpen } from 'lucide-react';
import './studio.css';

export function StudioPage({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`pt-studio-page ${className}`}>{children}</div>;
}

export function StudioHeader({ title, description, kicker, actions, visual, className = '' }: {
  title: ReactNode; description?: ReactNode; kicker?: ReactNode; actions?: ReactNode; visual?: ReactNode; className?: string;
}) {
  return <header className={`pt-studio-header ${className}`}>
    <div className="pt-studio-heading">{kicker && <div className="pt-studio-kicker">{kicker}</div>}<h1>{title}</h1>{description && <p>{description}</p>}{actions && <div className="pt-studio-actions">{actions}</div>}</div>
    {visual && <div className="pt-studio-header-visual" aria-hidden="true">{visual}</div>}
  </header>;
}

export function StudioPanel({ children, className = '', tone = 'plain' }: { children: ReactNode; className?: string; tone?: 'plain' | 'soft' | 'accent' }) {
  return <section className={`pt-studio-panel pt-studio-panel-${tone} ${className}`}>{children}</section>;
}

export function StudioEmpty({ icon: Icon = FolderOpen, title, description, children }: {
  icon?: LucideIcon; title: ReactNode; description: ReactNode; children?: ReactNode;
}) {
  return <div className="pt-studio-empty"><div className="pt-studio-empty-object" aria-hidden="true"><Icon size={34} strokeWidth={1.4}/></div><h2>{title}</h2><p>{description}</p>{children && <div className="pt-studio-actions">{children}</div>}</div>;
}

export function StudioAction({ href, children, variant = 'primary', className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & {
  href?: string; children: ReactNode; variant?: 'primary' | 'secondary' | 'text';
}) {
  const classes = `pt-studio-action pt-studio-action-${variant} ${className}`;
  if (href) return <a className={classes} href={href}>{children}</a>;
  return <button type="button" className={classes} {...props}>{children}</button>;
}

export function StudioNote({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`pt-studio-note ${className}`}>{children}</div>;
}
