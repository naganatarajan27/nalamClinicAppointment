import { useState, type FormEvent } from 'react'
import { Alert } from '../../components/Alert'
import { Button } from '../../components/Button'
import { FormField } from '../../components/FormField'
import { createAppointment } from '../../api/publicApi'
import { ApiError } from '../../api/client'
import { isPastDate, isValidE164, todayIsoDate } from '../../utils/validation'
import { useAvailability } from './useAvailability'
import { useDoctors } from './useDoctors'
import type { PatientType } from '../../types/api'

const SYMPTOMS_MAX_LENGTH = 1000

interface FormState {
  patientName: string
  patientType: PatientType | ''
  phoneNumber: string
  whatsappNumber: string
  doctorId: string
  requestedDate: string
  requestedTime: string
  symptoms: string
}

const INITIAL_STATE: FormState = {
  patientName: '',
  patientType: '',
  phoneNumber: '',
  whatsappNumber: '',
  doctorId: '',
  requestedDate: '',
  requestedTime: '',
  symptoms: '',
}

type FormErrors = Partial<Record<keyof FormState, string>>

function validate(values: FormState): FormErrors {
  const errors: FormErrors = {}

  if (!values.patientName.trim()) errors.patientName = 'Please enter the patient name.'
  if (!values.patientType) errors.patientType = 'Please select patient type.'

  if (!values.phoneNumber.trim()) {
    errors.phoneNumber = 'Please enter a phone number.'
  } else if (!isValidE164(values.phoneNumber)) {
    errors.phoneNumber = "Use international format starting with '+' and the country code, e.g. +91XXXXXXXXXX."
  }

  if (!values.whatsappNumber.trim()) {
    errors.whatsappNumber = 'Please enter a WhatsApp number.'
  } else if (!isValidE164(values.whatsappNumber)) {
    errors.whatsappNumber = "Use international format starting with '+' and the country code, e.g. +91XXXXXXXXXX."
  }

  if (!values.doctorId) errors.doctorId = 'Please select a doctor.'

  if (!values.requestedDate) {
    errors.requestedDate = 'Please select a preferred date.'
  } else if (isPastDate(values.requestedDate)) {
    errors.requestedDate = 'The preferred date cannot be in the past.'
  }

  if (!values.requestedTime) errors.requestedTime = 'Please select a preferred time.'

  if (!values.symptoms.trim()) {
    errors.symptoms = 'Please briefly describe the reason for your visit.'
  } else if (values.symptoms.length > SYMPTOMS_MAX_LENGTH) {
    errors.symptoms = `Please keep this under ${SYMPTOMS_MAX_LENGTH} characters.`
  }

  return errors
}

export function BookingForm() {
  const { doctors, loading: doctorsLoading, error: doctorsError } = useDoctors()
  const [values, setValues] = useState<FormState>(INITIAL_STATE)
  const [errors, setErrors] = useState<FormErrors>({})
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [reference, setReference] = useState<string | null>(null)

  const { times: availableTimes, loading: availabilityLoading } = useAvailability(
    values.doctorId,
    values.requestedDate,
  )

  function updateField<K extends keyof FormState>(field: K, value: FormState[K]) {
    setValues((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (submitting) return

    const validationErrors = validate(values)
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return

    setSubmitting(true)
    setSubmitError(null)
    try {
      const result = await createAppointment({
        patient_name: values.patientName.trim(),
        patient_type: values.patientType as PatientType,
        phone_number: values.phoneNumber.trim(),
        whatsapp_number: values.whatsappNumber.trim(),
        doctor_id: values.doctorId,
        requested_date: values.requestedDate,
        requested_time: values.requestedTime.length === 5 ? `${values.requestedTime}:00` : values.requestedTime,
        symptoms: values.symptoms.trim(),
      })
      setReference(result.public_reference)
    } catch (err) {
      setSubmitError(
        err instanceof ApiError
          ? err.message
          : 'We could not submit your request right now. Please try again in a moment.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  if (reference) {
    return (
      <div className="card">
        <Alert variant="success">Your appointment request has been submitted.</Alert>
        <p>
          Reference number: <strong>{reference}</strong>
        </p>
        <p>
          Your request is <strong>pending clinic review</strong>. The clinic will confirm your
          requested time or suggest another time, and will message you on WhatsApp once reviewed.
        </p>
        <Button
          variant="secondary"
          onClick={() => {
            setValues(INITIAL_STATE)
            setReference(null)
          }}
        >
          Submit another request
        </Button>
      </div>
    )
  }

  return (
    <form className="card" onSubmit={handleSubmit} noValidate>
      {submitError && <Alert variant="error">{submitError}</Alert>}
      {doctorsError && <Alert variant="error">{doctorsError}</Alert>}

      <FormField label="Patient name" htmlFor="patientName" error={errors.patientName}>
        <input
          id="patientName"
          type="text"
          value={values.patientName}
          onChange={(e) => updateField('patientName', e.target.value)}
          aria-invalid={Boolean(errors.patientName)}
          disabled={submitting}
          required
        />
      </FormField>

      <FormField label="Patient type" htmlFor="patientType" error={errors.patientType}>
        <select
          id="patientType"
          value={values.patientType}
          onChange={(e) => updateField('patientType', e.target.value as PatientType)}
          aria-invalid={Boolean(errors.patientType)}
          disabled={submitting}
          required
        >
          <option value="">Select one</option>
          <option value="NEW">New patient</option>
          <option value="EXISTING">Existing patient</option>
        </select>
      </FormField>

      <div className="form-row">
        <FormField
          label="Phone number"
          htmlFor="phoneNumber"
          error={errors.phoneNumber}
          hint="Include country code, e.g. +91XXXXXXXXXX"
        >
          <input
            id="phoneNumber"
            type="tel"
            value={values.phoneNumber}
            onChange={(e) => updateField('phoneNumber', e.target.value)}
            aria-invalid={Boolean(errors.phoneNumber)}
            disabled={submitting}
            required
          />
        </FormField>

        <FormField
          label="WhatsApp number"
          htmlFor="whatsappNumber"
          error={errors.whatsappNumber}
          hint="Used to send your confirmation. May differ from your phone number."
        >
          <input
            id="whatsappNumber"
            type="tel"
            value={values.whatsappNumber}
            onChange={(e) => updateField('whatsappNumber', e.target.value)}
            aria-invalid={Boolean(errors.whatsappNumber)}
            disabled={submitting}
            required
          />
        </FormField>
      </div>

      <FormField label="Preferred doctor" htmlFor="doctorId" error={errors.doctorId}>
        <select
          id="doctorId"
          value={values.doctorId}
          onChange={(e) => updateField('doctorId', e.target.value)}
          aria-invalid={Boolean(errors.doctorId)}
          disabled={submitting || doctorsLoading}
          required
        >
          <option value="">{doctorsLoading ? 'Loading doctors...' : 'Select a doctor'}</option>
          {doctors.map((doctor) => (
            <option key={doctor.id} value={doctor.id}>
              {doctor.display_name}
              {doctor.specialty ? ` — ${doctor.specialty}` : ''}
            </option>
          ))}
        </select>
      </FormField>

      <div className="form-row">
        <FormField label="Preferred date" htmlFor="requestedDate" error={errors.requestedDate}>
          <input
            id="requestedDate"
            type="date"
            min={todayIsoDate()}
            value={values.requestedDate}
            onChange={(e) => updateField('requestedDate', e.target.value)}
            aria-invalid={Boolean(errors.requestedDate)}
            disabled={submitting}
            required
          />
        </FormField>

        <FormField
          label="Preferred time"
          htmlFor="requestedTime"
          error={errors.requestedTime}
          hint={
            values.doctorId && values.requestedDate && !availabilityLoading && availableTimes.length === 0
              ? 'No configured slots are free for that day — you may still request a time.'
              : undefined
          }
        >
          {availableTimes.length > 0 ? (
            <select
              id="requestedTime"
              value={values.requestedTime}
              onChange={(e) => updateField('requestedTime', e.target.value)}
              aria-invalid={Boolean(errors.requestedTime)}
              disabled={submitting || availabilityLoading}
              required
            >
              <option value="">{availabilityLoading ? 'Loading times...' : 'Select a time'}</option>
              {availableTimes.map((time) => (
                <option key={time} value={time}>
                  {time}
                </option>
              ))}
            </select>
          ) : (
            <input
              id="requestedTime"
              type="time"
              value={values.requestedTime}
              onChange={(e) => updateField('requestedTime', e.target.value)}
              aria-invalid={Boolean(errors.requestedTime)}
              disabled={submitting}
              required
            />
          )}
        </FormField>
      </div>

      <FormField
        label="Symptoms / reason for visit"
        htmlFor="symptoms"
        error={errors.symptoms}
        hint={`${values.symptoms.length}/${SYMPTOMS_MAX_LENGTH} characters. Please do not enter emergency details.`}
      >
        <textarea
          id="symptoms"
          rows={4}
          maxLength={SYMPTOMS_MAX_LENGTH}
          value={values.symptoms}
          onChange={(e) => updateField('symptoms', e.target.value)}
          aria-invalid={Boolean(errors.symptoms)}
          disabled={submitting}
          required
        />
      </FormField>

      <Button type="submit" block loading={submitting} disabled={submitting}>
        {submitting ? 'Submitting...' : 'Submit appointment request'}
      </Button>
    </form>
  )
}
