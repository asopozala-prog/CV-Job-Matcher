// Kiron preparation section explaining how to build reusable career materials.

import Image from 'next/image'
import Link from 'next/link'
import { Reveal } from './reveal'

export function Prepare() {
  return (
    <section id="prepare" className="py-20 md:py-28">
      <div className="mx-auto w-full max-w-6xl px-6">
        <Reveal>
          <div className="text-center">
            <p className="font-heading text-sm font-bold uppercase tracking-[0.16em] text-muted-foreground">
              Prepare materials
            </p>

            <h2 className="mt-3 font-heading text-3xl font-bold tracking-tight text-foreground md:text-4xl">
              Your CV materials are not a document.
            </h2>

            <p className="mx-auto mt-4 max-w-3xl text-lg leading-relaxed text-muted-foreground">
              They are a living file — yours to grow anytime.
            </p>
          </div>
        </Reveal>

        <div className="mt-14 grid gap-6 md:grid-cols-3">
          <Reveal
            as="div"
            className="flex flex-col rounded-3xl bg-card p-7 shadow-sm ring-1 ring-border"
          >
            <Image
              src="/kiron/kiron_education.png"
              alt="Kiron representing learning and preparation"
              width={160}
              height={160}
              className="mb-4 h-28 w-28 object-contain drop-shadow-md"
            />

            <h3 className="font-heading text-xl font-bold text-foreground">
              <Link
                href="/prompt"
                className="underline decoration-primary/40 underline-offset-4 transition-colors hover:text-primary hover:decoration-primary"
              >
                ① Prompt preview
              </Link>
            </h3>

            <p className="mt-3 text-base leading-relaxed text-muted-foreground text-pretty">
              One click. A ready-made prompt designed to help any AI chat tool
              extract and organize your professional information correctly.
            </p>
          </Reveal>

          <Reveal
            as="div"
            delay={120}
            className="flex flex-col rounded-3xl bg-card p-7 shadow-sm ring-1 ring-border"
          >
            <Image
              src="/kiron/kiron_gaps.png"
              alt="Kiron thinking about missing information"
              width={160}
              height={160}
              className="mb-4 h-28 w-28 object-contain drop-shadow-md"
            />

            <h3 className="font-heading text-xl font-bold text-foreground">
              ② Open your trusted AI chat
            </h3>

            <p className="mt-3 text-base leading-relaxed text-muted-foreground text-pretty">
              Use whatever you already trust —
            </p>

            <p className="mt-3 font-heading text-sm font-bold tracking-wide text-foreground">
              ChatGPT · Gemini · Claude · or any other
            </p>

            <p className="mt-3 text-base leading-relaxed text-muted-foreground text-pretty">
              Paste the prompt. Add everything you have — old CV, LinkedIn,
              certificates, project notes, anything. Even rough notes count.
              The AI will organize it.
            </p>
          </Reveal>

          <Reveal
            as="div"
            delay={240}
            className="flex flex-col rounded-3xl bg-card p-7 shadow-sm ring-1 ring-border"
          >
            <Image
              src="/kiron/kiron_files.png"
              alt="Kiron representing saved career files"
              width={160}
              height={160}
              className="mb-4 h-28 w-28 object-contain drop-shadow-md"
            />

            <h3 className="font-heading text-xl font-bold text-foreground">
              ③ Save it as a file
            </h3>

            <p className="mt-3 text-base leading-relaxed text-muted-foreground text-pretty">
              When you feel satisfied — save the result as a simple{' '}
              <span className="font-semibold text-foreground">.md file</span>.
            </p>

            <p className="mt-3 text-base leading-relaxed text-muted-foreground text-pretty">
              No formatting needed. No perfect structure. Just your information,
              in one place.
            </p>

            <p className="mt-3 text-base leading-relaxed text-muted-foreground text-pretty">
              Anytime something changes — a new project, a new skill, a new role —
              open the file and add it. That&apos;s it.
            </p>
          </Reveal>
        </div>

        <Reveal delay={320}>
          <p className="mx-auto mt-10 max-w-3xl text-center text-lg leading-relaxed text-muted-foreground">
            When you&apos;re ready to apply —{' '}
            <span className="font-semibold text-foreground">
              Kiron reads the file and does the rest.
            </span>
          </p>
        </Reveal>
      </div>
    </section>
  )
}
