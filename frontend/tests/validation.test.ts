import { describe, expect, it } from 'vitest'
import { isPastDate, isValidE164, todayIsoDate } from '../src/utils/validation'

function toLocalIsoDate(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

describe('isValidE164', () => {
  it('accepts a number with a leading + and country code', () => {
    expect(isValidE164('+919876543210')).toBe(true)
  })

  it('rejects a number without a country code prefix', () => {
    expect(isValidE164('9876543210')).toBe(false)
  })

  it('rejects a number starting with a zero after the +', () => {
    expect(isValidE164('+0123456789')).toBe(false)
  })

  it('rejects empty input', () => {
    expect(isValidE164('')).toBe(false)
  })
})

describe('isPastDate', () => {
  it('treats yesterday as past', () => {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    expect(isPastDate(toLocalIsoDate(yesterday))).toBe(true)
  })

  it('treats today as not past', () => {
    expect(isPastDate(todayIsoDate())).toBe(false)
  })

  it('treats tomorrow as not past', () => {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    expect(isPastDate(toLocalIsoDate(tomorrow))).toBe(false)
  })
})
