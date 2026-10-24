const LABELS: Record<string, string> = {
  PENDING: 'Pending review',
  CONFIRMED: 'Confirmed',
  ALTERNATE_PROPOSED: 'Alternate proposed',
  CANCELLED: 'Cancelled',
  COMPLETED: 'Completed',
  QUEUED: 'Queued',
  SENT: 'Sent',
  DELIVERED: 'Delivered',
  FAILED: 'Failed',
}

export function StatusBadge({ status }: { status: string }) {
  const key = status.toLowerCase()
  return <span className={`badge badge--${key}`}>{LABELS[status] ?? status}</span>
}
