// Kiron frontend form for privacy acknowledgement and application submission.

'use client'

import Image from 'next/image'
import { useState, type FormEvent } from 'react'
import { ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react'
import { Reveal } from './reveal'

const JOB_OFFER_MAX = 30_000
const CAREER_MATERIAL_MAX = 60_000
const API_BASE_URL =
  process.env.NODE_ENV === 'production'
    ? '/api/backend'
    : 'http://127.0.0.1:8000'

type JobResponse = {
  status: string
  job_id: string
  message: string
}

export function FormSection() {
  const [jobOffer, setJobOffer] = useState('')
  const [careerMaterial, setCareerMaterial] = useState('')
  const [email, setEmail] = useState('')
  const [acknowledged, setAcknowledged] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')

  const canSubmit =
    acknowledged &&
    jobOffer.trim().length > 0 &&
    careerMaterial.trim().length > 0 &&
    email.trim().length > 0 &&
    !submitting

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!canSubmit) {
      return
    }

    setSubmitting(true)
    setSuccessMessage('')
    setErrorMessage('')

    try {
      const response = await fetch(`${API_BASE_URL}/api/jobs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_offer_text: jobOffer,
          candidate_material_text: careerMaterial,
          email,
          consent_confirmed: acknowledged,
        }),
      })

      let payload: JobResponse | { detail?: string } | null = null

      try {
        payload = await response.json()
      } catch {
        payload = null
      }

      if (!response.ok) {
        const detail =
          payload && 'detail' in payload && typeof payload.detail === 'string'
            ? payload.detail
            : 'Kiron could not complete your request.'

        throw new Error(detail)
      }

      const result = payload as JobResponse

      setSuccessMessage(
        result.message ||
          'Kiron finished your application and sent the results by email.'
      )
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'Kiron could not complete your request.'
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section id="apply" className="relative overflow-hidden py-20 md:py-28">
      <div className="mx-auto w-full max-w-6xl px-6">
        <div className="relative">
          <div className="mb-8 flex items-end justify-between gap-6">
            <div>
              <p className="font-heading text-sm font-bold uppercase tracking-[0.16em] text-muted-foreground">
                Your application
              </p>

              <h2 className="mt-2 font-heading text-3xl font-bold tracking-tight text-foreground md:text-4xl">
                Let&apos;s get started.
              </h2>
            </div>

            <Image
              src="/kiron/kiron_skills.png"
              alt="Kiron preparing to help"
              width={150}
              height={150}
              className="hidden h-auto w-28 object-contain md:block lg:w-36"
            />
          </div>

          <Reveal delay={100}>
            <form
              onSubmit={handleSubmit}
              className="rounded-3xl bg-card p-6 shadow-sm ring-1 ring-border md:p-8"
            >
              <div className="border-b border-border pb-7">
                <p className="font-heading text-xs font-bold uppercase tracking-[0.14em] text-muted-foreground">
                  A note about your data
                </p>

                <div className="mt-3 max-w-4xl space-y-2 text-sm leading-relaxed text-muted-foreground">
                  <p>
                    Kiron is a free, non-commercial online app demo. It uses the{' '}
                    <strong className="font-semibold text-foreground">
                      Google Gemini Free Tier API
                    </strong>{' '}
                    to analyse the job offer and career information you submit.
                  </p>

                  <p>
                    Your submitted information is therefore sent to Google Gemini
                    for AI processing. If you have privacy concerns, please review
                    the specific terms and data-handling policies that apply to the
                    Google Gemini API Free Tier before using Kiron. Kiron does not
                    interpret or make guarantees about Google&apos;s policies.
                  </p>

                  <p>
                    Kiron uses your information only to generate your job-match
                    evaluation and tailored CV. Processing files are kept
                    temporarily while your request is being completed and will be
                    removed after the delivery workflow is finished.
                  </p>

                  <p>
                    If you prefer a different setup, you can contact the developer
                    to discuss a customized version using your own API key and
                    deployment environment.
                  </p>

                  <p>
                    <a
                      href="https://ai.google.dev/gemini-api/terms"
                      target="_blank"
                      rel="noreferrer"
                      className="font-semibold text-primary underline decoration-primary/40 underline-offset-4 hover:decoration-primary"
                    >
                      Review the Google Gemini API terms
                    </a>
                  </p>
                </div>

                <label className="mt-5 flex cursor-pointer items-start gap-3">
                  <input
                    type="checkbox"
                    checked={acknowledged}
                    onChange={(event) => setAcknowledged(event.target.checked)}
                    className="mt-1 h-4 w-4 rounded border-input text-primary focus:ring-primary/30"
                  />

                  <span className="text-sm leading-relaxed text-foreground">
                    I understand how my information will be processed and want to
                    continue.
                  </span>
                </label>
              </div>

              <div className="mt-7 space-y-7">
                <div className="flex flex-col gap-2">
                  <div className="flex items-end justify-between gap-4">
                    <label
                      htmlFor="job-offer"
                      className="font-heading text-sm font-bold uppercase tracking-wide text-muted-foreground"
                    >
                      The job offer
                    </label>

                    <span className="text-xs text-muted-foreground">
                      {jobOffer.length.toLocaleString()} /{' '}
                      {JOB_OFFER_MAX.toLocaleString()}
                    </span>
                  </div>

                  <textarea
                    id="job-offer"
                    name="job_offer"
                    rows={7}
                    maxLength={JOB_OFFER_MAX}
                    value={jobOffer}
                    onChange={(event) => setJobOffer(event.target.value)}
                    placeholder="Paste the complete job offer, including any company information available."
                    className="w-full resize-y rounded-2xl border border-input bg-background px-4 py-3 text-base leading-relaxed text-foreground placeholder:text-muted-foreground/70 focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/30"
                    required
                  />
                </div>

                <div className="flex flex-col gap-2">
                  <div className="flex items-end justify-between gap-4">
                    <label
                      htmlFor="career-material"
                      className="font-heading text-sm font-bold uppercase tracking-wide text-muted-foreground"
                    >
                      Your CV &amp; career material
                    </label>

                    <span className="text-xs text-muted-foreground">
                      {careerMaterial.length.toLocaleString()} /{' '}
                      {CAREER_MATERIAL_MAX.toLocaleString()}
                    </span>
                  </div>

                  <textarea
                    id="career-material"
                    name="candidate_material"
                    rows={10}
                    maxLength={CAREER_MATERIAL_MAX}
                    value={careerMaterial}
                    onChange={(event) => setCareerMaterial(event.target.value)}
                    placeholder="Paste your CV and any relevant career material, projects, skills, education, certifications, or experience you want Kiron to consider."
                    className="w-full resize-y rounded-2xl border border-input bg-background px-4 py-3 text-base leading-relaxed text-foreground placeholder:text-muted-foreground/70 focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/30"
                    required
                  />
                </div>

                <div className="flex max-w-2xl flex-col gap-2">
                  <label
                    htmlFor="email"
                    className="font-heading text-sm font-bold uppercase tracking-wide text-muted-foreground"
                  >
                    Email
                  </label>

                  <input
                    id="email"
                    name="email"
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="Where should Kiron send your two PDFs?"
                    autoComplete="email"
                    className="w-full rounded-2xl border border-input bg-background px-4 py-3 text-base text-foreground placeholder:text-muted-foreground/70 focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/30"
                    required
                  />
                </div>
              </div>

              {successMessage && (
                <div
                  role="status"
                  className="mt-7 flex items-start gap-3 rounded-2xl border border-primary/20 bg-primary/5 px-4 py-3 text-sm leading-relaxed text-foreground"
                >
                  <CheckCircle2
                    className="mt-0.5 h-5 w-5 shrink-0 text-primary"
                    aria-hidden="true"
                  />
                  <span>{successMessage}</span>
                </div>
              )}

              {errorMessage && (
                <div
                  role="alert"
                  className="mt-7 flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-relaxed text-red-800"
                >
                  <AlertCircle
                    className="mt-0.5 h-5 w-5 shrink-0"
                    aria-hidden="true"
                  />
                  <span>{errorMessage}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={!canSubmit}
                className="mt-8 inline-flex w-full items-center justify-center gap-2 rounded-full bg-primary px-8 py-4 font-heading text-lg font-bold text-primary-foreground shadow-sm transition-all hover:brightness-105 focus:outline-none focus:ring-2 focus:ring-ring/40 focus:ring-offset-2 focus:ring-offset-card disabled:cursor-not-allowed disabled:opacity-40 md:w-auto"
              >
                {submitting ? 'Kiron is working…' : 'Let Kiron work'}
                {!submitting && (
                  <ArrowRight className="h-5 w-5" aria-hidden="true" />
                )}
              </button>

              {submitting && (
                <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
                  This can take a little while. Please keep this page open while
                  Kiron analyses the application, creates both PDFs, and sends the
                  email.
                </p>
              )}
            </form>
          </Reveal>
        </div>
      </div>
    </section>
  )
}
