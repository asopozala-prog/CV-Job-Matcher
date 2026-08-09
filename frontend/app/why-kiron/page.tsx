// Story page explaining why Kiron exists.

import Image from 'next/image'
import Link from 'next/link'
import { ArrowLeft, ArrowUpRight } from 'lucide-react'
import { KironNav } from '@/components/kiron/nav'

const LINKEDIN_URL = 'https://www.linkedin.com/in/dany-gr%C3%BCnewald-20bb3a3b8'

export default function WhyKironPage() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <KironNav />

      <section className="py-16 md:py-24">
        <div className="mx-auto w-full max-w-5xl px-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm font-semibold text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Back to Kiron
          </Link>

          <div className="mt-10 grid items-start gap-10 md:grid-cols-[0.75fr_1.25fr] md:gap-16">
            <div className="md:sticky md:top-28">
              <Image
                src="/kiron/kiron_supportive.png"
                alt="Kiron offering calm support"
                width={420}
                height={420}
                priority
                className="mx-auto h-auto w-64 object-contain drop-shadow-xl md:w-full"
              />
            </div>

            <article>
              <p className="font-heading text-sm font-bold uppercase tracking-[0.16em] text-muted-foreground">
                Why Kiron exists
              </p>

              <h1 className="mt-3 font-heading text-4xl font-bold tracking-tight text-foreground md:text-5xl">
                Built from gratitude, and offered back.
              </h1>

              <div className="mt-8 space-y-6 text-lg leading-relaxed text-muted-foreground">
                <p>
                  I am a participant of the Kiron THRIVE program.
                </p>

                <p>
                  The supporting team — their patience, warmth, and genuine care
                  for every learner — became the personality of this character.
                  Kiron the dinosaur is how I experienced them.
                </p>

                <p>
                  Watching a small, dedicated team work under real pressure with
                  limited resources, supporting so many people to reach the next
                  stage of their lives — that moved me.
                </p>

                <p>
                  And in our workshops, I saw clearly what many learners carry —
                  especially those crossing borders, starting over, trying to build
                  a career in a new country. The confusion, the self-doubt, the not
                  knowing how to present themselves in a system that was not
                  designed for them.
                </p>

                <p className="font-semibold text-foreground">
                  That is why I built this.
                </p>

                <p>
                  Kiron CV is not a commercial product. It is a free tool — built
                  from gratitude, and offered back.
                </p>
              </div>

              <div className="mt-10 border-t border-border pt-8">
                <p className="text-sm leading-relaxed text-muted-foreground">
                  Built by Dany Grünewald — Kiron THRIVE participant, 2026.
                </p>

                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  Inspired by the{' '}
                  <a
                    href="https://www.kiron.ngo/thrive-dach"
                    target="_blank"
                    rel="noreferrer"
                    className="font-semibold text-primary underline decoration-primary/40 underline-offset-4 hover:decoration-primary"
                  >
                    Kiron Higher Education community
                  </a>
                  .
                </p>

                <a
                  href={LINKEDIN_URL}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-8 inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 font-heading text-base font-bold text-primary-foreground shadow-sm transition-all hover:brightness-105 focus:outline-none focus:ring-2 focus:ring-ring/40 focus:ring-offset-2 focus:ring-offset-background"
                >
                  Connect with Dany on LinkedIn
                  <ArrowUpRight className="h-5 w-5" aria-hidden="true" />
                </a>
              </div>
            </article>
          </div>
        </div>
      </section>
    </main>
  )
}
