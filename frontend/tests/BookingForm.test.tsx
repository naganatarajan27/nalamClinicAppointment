import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { BookingForm } from '../src/features/booking/BookingForm'
import * as publicApi from '../src/api/publicApi'

const DOCTOR = { id: 'doc-1', display_name: 'Dr. Asha Rao', specialty: 'General Medicine' }

beforeEach(() => {
  vi.restoreAllMocks()
  vi.spyOn(publicApi, 'listDoctors').mockResolvedValue([DOCTOR])
  vi.spyOn(publicApi, 'getAvailability').mockResolvedValue({ available_times: [] })
})

function tomorrowIso(): string {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  return `${tomorrow.getFullYear()}-${String(tomorrow.getMonth() + 1).padStart(2, '0')}-${String(
    tomorrow.getDate(),
  ).padStart(2, '0')}`
}

describe('BookingForm', () => {
  it('shows validation errors when required fields are missing', async () => {
    const user = userEvent.setup()
    render(<BookingForm />)

    await screen.findByText('Dr. Asha Rao — General Medicine')
    await user.click(screen.getByRole('button', { name: /submit appointment request/i }))

    expect(await screen.findByText('Please enter the patient name.')).toBeInTheDocument()
    expect(screen.getByText('Please select patient type.')).toBeInTheDocument()
  })

  it('rejects a mobile number that is not in international format', async () => {
    const user = userEvent.setup()
    render(<BookingForm />)
    await screen.findByText('Dr. Asha Rao — General Medicine')

    await user.type(screen.getByLabelText('Mobile number'), '9876543210')
    await user.click(screen.getByRole('button', { name: /submit appointment request/i }))

    expect(
      await screen.findByText(/Use international format starting with/i),
    ).toBeInTheDocument()
  })

  it('hides the WhatsApp number field until the "same as mobile" checkbox is unchecked', async () => {
    const user = userEvent.setup()
    render(<BookingForm />)
    await screen.findByText('Dr. Asha Rao — General Medicine')

    expect(screen.queryByLabelText('WhatsApp number')).not.toBeInTheDocument()

    await user.click(screen.getByLabelText(/My WhatsApp number is the same as my mobile number/i))
    expect(screen.getByLabelText('WhatsApp number')).toBeInTheDocument()
  })

  it('rejects an invalid email address but allows an empty one', async () => {
    const user = userEvent.setup()
    render(<BookingForm />)
    await screen.findByText('Dr. Asha Rao — General Medicine')

    await user.type(screen.getByLabelText(/Email address/i), 'not-an-email')
    await user.click(screen.getByRole('button', { name: /submit appointment request/i }))

    expect(await screen.findByText('Please enter a valid email address.')).toBeInTheDocument()
  })

  it('submits successfully using the mobile number as the WhatsApp number', async () => {
    vi.spyOn(publicApi, 'createAppointment').mockResolvedValue({
      public_reference: 'NAL-ABC12345',
      status: 'PENDING',
    })

    const user = userEvent.setup()
    render(<BookingForm />)
    await screen.findByText('Dr. Asha Rao — General Medicine')

    await user.type(screen.getByLabelText('Patient name'), 'Jane Doe')
    await user.selectOptions(screen.getByLabelText('Patient type'), 'NEW')
    await user.type(screen.getByLabelText('Mobile number'), '+919876543210')
    await user.type(screen.getByLabelText(/Email address/i), 'jane@example.com')
    await user.selectOptions(screen.getByLabelText('Preferred doctor'), 'doc-1')
    await user.type(screen.getByLabelText('Preferred date'), tomorrowIso())
    await user.type(screen.getByLabelText('Preferred time'), '10:30')
    await user.type(screen.getByLabelText(/Symptoms/i), 'Persistent cough for a week.')

    await user.click(screen.getByRole('button', { name: /submit appointment request/i }))

    await waitFor(() => expect(publicApi.createAppointment).toHaveBeenCalled())
    expect(publicApi.createAppointment).toHaveBeenCalledWith(
      expect.objectContaining({
        phone_number: '+919876543210',
        whatsapp_number: '+919876543210',
        email: 'jane@example.com',
      }),
    )
    expect(await screen.findByText('NAL-ABC12345')).toBeInTheDocument()
    expect(screen.getByText(/pending clinic review/i)).toBeInTheDocument()
  })

  it('submits with a separate WhatsApp number when the checkbox is unchecked', async () => {
    vi.spyOn(publicApi, 'createAppointment').mockResolvedValue({
      public_reference: 'NAL-DEF67890',
      status: 'PENDING',
    })

    const user = userEvent.setup()
    render(<BookingForm />)
    await screen.findByText('Dr. Asha Rao — General Medicine')

    await user.type(screen.getByLabelText('Patient name'), 'Ravi Kumar')
    await user.selectOptions(screen.getByLabelText('Patient type'), 'EXISTING')
    await user.type(screen.getByLabelText('Mobile number'), '+919123456780')
    await user.click(screen.getByLabelText(/My WhatsApp number is the same as my mobile number/i))
    await user.type(screen.getByLabelText('WhatsApp number'), '+919123456781')
    await user.selectOptions(screen.getByLabelText('Preferred doctor'), 'doc-1')
    await user.type(screen.getByLabelText('Preferred date'), tomorrowIso())
    await user.type(screen.getByLabelText('Preferred time'), '11:00')
    await user.type(screen.getByLabelText(/Symptoms/i), 'Routine checkup.')

    await user.click(screen.getByRole('button', { name: /submit appointment request/i }))

    await waitFor(() => expect(publicApi.createAppointment).toHaveBeenCalled())
    expect(publicApi.createAppointment).toHaveBeenCalledWith(
      expect.objectContaining({
        phone_number: '+919123456780',
        whatsapp_number: '+919123456781',
        email: undefined,
      }),
    )
  })
})
