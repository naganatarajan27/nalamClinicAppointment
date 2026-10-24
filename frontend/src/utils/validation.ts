const E164_PATTERN = /^\+[1-9]\d{6,14}$/
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function isValidE164(value: string): boolean {
  return E164_PATTERN.test(value.trim())
}

export function isValidEmail(value: string): boolean {
  return EMAIL_PATTERN.test(value.trim())
}

export function isPastDate(isoDate: string): boolean {
  if (!isoDate) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const [year, month, day] = isoDate.split('-').map(Number)
  const candidate = new Date(year, (month ?? 1) - 1, day ?? 1)
  return candidate < today
}

export function todayIsoDate(): string {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}
