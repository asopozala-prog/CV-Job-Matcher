// Kiron hero introducing the three core CV-assistant features.

import Image from 'next/image'
import { Reveal } from './reveal'

const features = [
  {
    number: '①',
    title: 'CV Reformulation',
    body:
      'Paste the job offer, company info, and your raw materials. Kiron rewrites your CV — tailored to that specific position, ATS-optimized. Once ready, she sends the result to your email.',
  },
  {
    number: '②',
    title: 'Two-Page PDF — built for two different readers',
    body:
      'Page 1 — designed for the 10-second HR scan. Clear, fast, decisive. Page 2 — project depth for the person who actually knows the role. Layout balanced for machines and humans. No over-design.',
  },
  {
    number: '③',
    title: 'Honest Assessment',
    body:
      'Before you submit — know where you stand. Kiron evaluates your realistic chance among 200 applications.',
  },
]

export function Hero() {
  return (
    <section className="relative overflow-hidden py-20 md:py-28">
      <div
        className="absolute inset-0 -z-10 bg-gradient-to-b from-sky-50/70 via-background to-background"
        aria-hidden="true"
      />

      <div className="mx-auto grid w-full max-w-6xl items-center gap-10 px-6 md:grid-cols-[0.9fr_1.1fr] md:gap-14">
        <Reveal className="order-1">
          <Image
            src="/kiron/kiron_work_experience.png"
            alt="Kiron, a friendly teal-green dinosaur, walking cheerfully with a backpack"
            width={440}
            height={440}
            priority
            className="mx-auto h-64 w-64 object-contain drop-shadow-xl sm:h-80 sm:w-80 md:h-[26rem] md:w-[26rem]"
          />
        </Reveal>

        <Reveal delay={120} className="order-2">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-card px-4 py-2 text-sm font-semibold text-primary shadow-sm ring-1 ring-border">
              <span
                className="h-2 w-2 rounded-full bg-primary"
                aria-hidden="true"
              />
              Free AI CV optimization
            </div>

            <h1 className="mt-6 font-heading text-5xl font-bold tracking-tight text-foreground sm:text-6xl">
              Hi, I&apos;m Kiron.
            </h1>

            <p className="mt-6 max-w-2xl font-heading text-2xl font-semibold leading-snug text-foreground md:text-3xl">
              Three features. One click. Kiron does the rest.
            </p>

            <div className="mt-8 space-y-6">
              {features.map((feature) => (
                <div key={feature.title} className="max-w-2xl">
                  <h2 className="font-heading text-lg font-bold text-foreground">
                    <span className="mr-2 text-primary">{feature.number}</span>
                    {feature.title}
                  </h2>
                  <p className="mt-2 text-base leading-relaxed text-muted-foreground">
                    {feature.body}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  )
}
