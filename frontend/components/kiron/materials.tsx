import Image from 'next/image'
import { Reveal } from './reveal'

export function Materials() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-24 md:py-32">
      <div className="flex flex-col items-center gap-12 md:flex-row-reverse md:justify-between md:gap-16">
        <Reveal className="max-w-xl">
          <h2 className="font-heading text-4xl font-bold leading-tight tracking-tight text-foreground text-balance md:text-5xl">
            You don&apos;t need a perfect CV. You need your story.
          </h2>
          <div className="mt-6 space-y-5 text-lg leading-relaxed text-muted-foreground text-pretty">
            <p>
              Don&apos;t worry about format, wording, or what to include. Think of it as your
              personal career dataset.
            </p>
            <p>
              Kiron selects what&apos;s relevant for each offer. You focus on what you&apos;ve done.{' '}
              <span className="font-semibold text-foreground">She handles the rest.</span>
            </p>
          </div>
        </Reveal>

        <Reveal delay={120} className="shrink-0">
          <Image
            src="/kiron/kiron_support.png"
            alt="Kiron holding a heart, looking supportive"
            width={360}
            height={360}
            className="h-56 w-56 drop-shadow-xl md:h-72 md:w-72"
          />
        </Reveal>
      </div>
    </section>
  )
}
