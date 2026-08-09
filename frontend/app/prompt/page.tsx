// Kiron prompt-preview page with copy and download actions.

'use client'

import Image from 'next/image'
import Link from 'next/link'
import { Check, Clipboard, Download, ArrowLeft } from 'lucide-react'
import { useEffect, useState } from 'react'

const PROMPT_URL = '/resources/Prompt_Build_RawCV.md'

export default function PromptPage() {
  const [promptText, setPromptText] = useState('')
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    async function loadPrompt() {
      try {
        const response = await fetch(PROMPT_URL, { cache: 'no-store' })

        if (!response.ok) {
          throw new Error(`Prompt file could not be loaded (${response.status}).`)
        }

        const text = await response.text()

        if (active) {
          setPromptText(text)
          setLoading(false)
        }
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : 'Prompt file could not be loaded.'
          )
          setLoading(false)
        }
      }
    }

    loadPrompt()

    return () => {
      active = false
    }
  }, [])

  async function copyPrompt() {
    if (!promptText) {
      return
    }

    await navigator.clipboard.writeText(promptText)
    setCopied(true)

    window.setTimeout(() => {
      setCopied(false)
    }, 1800)
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <section className="py-16 md:py-24">
        <div className="mx-auto w-full max-w-5xl px-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm font-semibold text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Back to Kiron
          </Link>

          <div className="mt-10 grid items-center gap-8 md:grid-cols-[1fr_auto]">
            <div>
              <p className="font-heading text-sm font-bold uppercase tracking-[0.16em] text-muted-foreground">
                Prepare materials
              </p>

              <h1 className="mt-3 font-heading text-3xl font-bold tracking-tight text-foreground md:text-5xl">
                Build your reusable career-material file.
              </h1>

              <p className="mt-5 max-w-3xl text-lg leading-relaxed text-muted-foreground">
                Preview the full prompt below. Copy it into the AI chat you trust,
                or download the Markdown file and keep it with your own career
                materials.
              </p>
            </div>

            <Image
              src="/kiron/kiron_projects.png"
              alt="Kiron organizing project materials"
              width={180}
              height={180}
              className="mx-auto h-auto w-32 object-contain drop-shadow-md md:w-40"
            />
          </div>

          <div className="mt-10 flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={copyPrompt}
              disabled={loading || Boolean(error) || !promptText}
              className="inline-flex items-center justify-center gap-2 rounded-full bg-primary px-6 py-3 font-heading text-base font-bold text-primary-foreground shadow-sm transition-all hover:brightness-105 focus:outline-none focus:ring-2 focus:ring-ring/40 focus:ring-offset-2 focus:ring-offset-background disabled:cursor-not-allowed disabled:opacity-40"
            >
              {copied ? (
                <>
                  <Check className="h-5 w-5" aria-hidden="true" />
                  Copied
                </>
              ) : (
                <>
                  <Clipboard className="h-5 w-5" aria-hidden="true" />
                  Copy full prompt
                </>
              )}
            </button>

            <a
              href={PROMPT_URL}
              download="Prompt_Build_RawCV.md"
              className="inline-flex items-center justify-center gap-2 rounded-full border border-border bg-card px-6 py-3 font-heading text-base font-bold text-foreground shadow-sm transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring/40 focus:ring-offset-2 focus:ring-offset-background"
            >
              <Download className="h-5 w-5" aria-hidden="true" />
              Download .md
            </a>
          </div>

          <section
            aria-label="Prompt preview"
            className="mt-8 rounded-3xl bg-card p-6 shadow-sm ring-1 ring-border md:p-8"
          >
            <div className="mb-5 flex items-center justify-between gap-4 border-b border-border pb-4">
              <div>
                <p className="font-heading text-xs font-bold uppercase tracking-[0.14em] text-muted-foreground">
                  Prompt preview
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Prompt_Build_RawCV.md
                </p>
              </div>
            </div>

            {loading && (
              <p className="text-sm leading-relaxed text-muted-foreground">
                Loading prompt…
              </p>
            )}

            {error && (
              <p className="text-sm leading-relaxed text-red-700">
                {error}
              </p>
            )}

            {!loading && !error && (
              <pre className="max-h-[70vh] overflow-auto whitespace-pre-wrap break-words rounded-2xl bg-muted/40 p-5 font-mono text-sm leading-7 text-foreground ring-1 ring-border/60">
                {promptText}
              </pre>
            )}
          </section>

          <p className="mx-auto mt-8 max-w-3xl text-center text-sm leading-relaxed text-muted-foreground">
            Keep the resulting file somewhere you control. Whenever your work
            changes, update that same file instead of rebuilding your CV history
            from scratch.
          </p>
        </div>
      </section>
    </main>
  )
}
