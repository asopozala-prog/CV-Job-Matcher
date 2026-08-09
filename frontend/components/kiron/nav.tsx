// Shared Kiron navigation for the landing page and story page.

import Link from 'next/link'

export function KironNav() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/70 bg-background/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <Link
          href="/"
          className="font-heading text-lg font-bold text-foreground"
        >
          Kiron 🦕
        </Link>

        <nav
          aria-label="Kiron navigation"
          className="flex items-center gap-5 text-sm font-semibold text-muted-foreground sm:gap-7"
        >
          <Link href="/#apply" className="transition-colors hover:text-foreground">
            Create CV
          </Link>

          <Link href="/#prepare" className="transition-colors hover:text-foreground">
            Prepare Materials
          </Link>

          <Link href="/why-kiron" className="transition-colors hover:text-foreground">
            Why Kiron
          </Link>
        </nav>
      </div>
    </header>
  )
}
