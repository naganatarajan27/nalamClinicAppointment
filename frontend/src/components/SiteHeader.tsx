import type { ReactNode } from 'react'

export function SiteHeader({ subtitle, actions }: { subtitle: string; actions?: ReactNode }) {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <div>
          <div className="brand">Nalam Clinic</div>
          <div className="brand-subtitle">{subtitle}</div>
        </div>
        {actions}
      </div>
    </header>
  )
}
