import Image from 'next/image'
import { Reveal } from './reveal'

export function WhyCv() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-24 md:py-32">
      <div className="flex flex-col items-center gap-12 md:flex-row md:justify-between md:gap-16">
        <Reveal className="max-w-xl">
          <h2 className="font-heading text-4xl font-bold leading-tight tracking-tight text-foreground text-balance md:text-5xl">
            A CV is not your value.
          </h2>
          <div className="mt-6 space-y-5 text-lg leading-relaxed text-muted-foreground text-pretty">
            <p>
              When a company hires, it&apos;s a big investment. Time, money, contracts, team
              integration. They&apos;re not asking{' '}
              <span className="font-semibold text-foreground">&ldquo;is this person good?&rdquo;</span>{' '}
              They&apos;re asking{' '}
              <span className="font-semibold text-foreground">
                &ldquo;is this the right match for this role?&rdquo;
              </span>
            </p>
            <p>
              Think of it like finding the right fit — in millions of possibilities. Not every role
              is yours. And that&apos;s okay.
            </p>
          </div>
        </Reveal>

        <Reveal delay={120} className="shrink-0">
          <Image
            src="/kiron/kiron_achievements.png"
            alt="Kiron looking through a telescope, curious"
            width={360}
            height={360}
            className="h-56 w-56 drop-shadow-xl md:h-72 md:w-72"
          />
        </Reveal>
      </div>
    </section>
  )
}
