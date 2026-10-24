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

describe('BookingForm', () => {
  it('shows validation errors when required fields are missing', async () => {
    const user = userEvent.setup()
    render(<BookingForm />)

    await screen.findByText('Dr. Asha Rao — General Medicine')
    await user.click(screen.getByRole('button', { name: /submit appointment request/i }))

    expect(await screen.findByText('Please enter the patient name.')).toBeInTheDocument()
    expect(screen.getByText('Please select patient type.')).toBeInTheDocument()
  })

  it('rejects a WhatsApp number that is not in international format', async () => {
    const user = userEvent.setup()
    render(<BookingForm />)
    await screen.findByText('Dr. Asha Rao — General Medicine')

    await user.type(screen.getByLabelText('WhatsApp number'), '9876543210')
    await user.click(screen.getByRole('button', { name: /submit appointment request/i }))

    expect(
      await screen.findByText(/Use international format starting with/i),
    ).toBeInTheDocument()
  })

  it('submits successfully and shows the reference number', async () => {
    vi.spyOn(publicApi, 'createAppointment').mockResolvedValue({
      public_reference: 'NAL-ABC12345',
      status: 'PENDING',
    })

    const user = userEvent.setup()
    render(<BookingForm />)
    await screen.findByText('Dr. Asha Rao — General Medicine')

    await user.type(screen.getByLabelText('Patient name'), 'Jane Doe')
    await user.selectOptions(screen.getByLabelText('Patient type'), 'NEW')
    await user.type(screen.getByLabelText('Phone number'), '+919876543210')
    await user.type(screen.getByLabelText('WhatsApp number'), '+919876543211')
    await user.selectOptions(screen.getByLabelText('Preferred doctor'), 'doc-1')

    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    const iso = `${tomorrow.getFullYear()}-${String(tomorrow.getMonth() + 1).padStart(2, '0')}-${String(
      tomorrow.getDate(),
    ).padStart(2, '0')}`
    await user.type(screen.getByLabelText('Preferred date'), iso)
    await user.type(screen.getByLabelText('Preferred time'), '10:30')
    await user.type(
      screen.getByLabelText(/Symptoms/i),
      'Persistent cough for a week.',
    )

    await user.click(screen.getByRole('button', { name: /submit appointment request/i }))

    await waitFor(() => expect(publicApi.createAppointment).toHaveBeenCalled())
    expect(await screen.findByText('NAL-ABC12345')).toBeInTheDocument()
    expect(screen.getByText(/pending clinic review/i)).toBeInTheDocument()
  })
})
