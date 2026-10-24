type AlertVariant = 'error' | 'success' | 'info'

export function Alert({ variant, children }: { variant: AlertVariant; children: React.ReactNode }) {
  return (
    <div className={`alert alert--${variant}`} role={variant === 'error' ? 'alert' : 'status'}>
      {children}
    </div>
  )
}
