import Image from 'next/image'
import { ArrowRight, ScanLine, Clock, UserCheck } from 'lucide-react'
import { Reveal } from './reveal'

const steps = [
  {
    icon: ScanLine,
    number: '1',
    title: 'Pass the machine',
    body: 'ATS scans for keywords and structure.',
  },
  {
    icon: Clock,
    number: '2',
    title: 'Give HR clarity in 10 seconds',
    body: 'Enough to forward it.',
  },
  {
    icon: UserCheck,
    number: '3',
    title: 'Show the responsible person you could be the right one',
    body: '',
  },
]

export function Mission() {
  return (
    <section className="bg-secondary/40 py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <Reveal className="flex flex-col items-center gap-6 text-center">
          <Image
            src="/kiron/kiron_celebration.png"
            alt="Kiron with arms raised, cheering encouragingly"
            width={220}
            height={220}
            className="h-40 w-40 drop-shadow-lg md:h-48 md:w-48"
          />
          <h2 className="font-heading text-4xl font-bold leading-tight tracking-tight text-foreground text-balance md:text-5xl">
            One CV. One job offer. Three tasks.
          </h2>
        </Reveal>

        <ol className="mt-16 flex flex-col items-stretch gap-6 md:flex-row md:items-center md:gap-2">
          {steps.map((step, i) => (
            <li key={step.number} className="contents">
              <Reveal
                as="div"
                delay={i * 120}
                className="flex flex-1 flex-col rounded-3xl bg-card p-7 shadow-sm ring-1 ring-border"
              >
                <div className="flex items-center gap-3">
                  <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                    <step.icon className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <span className="font-heading text-3xl font-extrabold text-primary/30">
                    {step.number}
                  </span>
                </div>
                <h3 className="mt-5 font-heading text-lg font-bold leading-snug text-foreground text-pretty">
                  {step.title}
                </h3>
                {step.body ? (
                  <p className="mt-2 text-base leading-relaxed text-muted-foreground">
                    {step.body}
                  </p>
                ) : null}
              </Reveal>

              {i < steps.length - 1 ? (
                <Reveal
                  as="div"
                  delay={i * 120 + 60}
                  className="flex justify-center text-primary md:px-1"
                >
                  <ArrowRight className="h-6 w-6 rotate-90 md:rotate-0" aria-hidden="true" />
                </Reveal>
              ) : null}
            </li>
          ))}
        </ol>

        <Reveal delay={200}>
          <p className="mx-auto mt-14 max-w-2xl text-center text-lg leading-relaxed text-muted-foreground text-pretty">
            After that — it&apos;s the interview.{' '}
            <span className="font-semibold text-foreground">The CV just opens the door.</span>
          </p>
        </Reveal>
      </div>
    </section>
  )
}
