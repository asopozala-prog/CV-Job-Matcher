import { KironNav } from '@/components/kiron/nav'
import { Hero } from '@/components/kiron/hero'
import { WhyCv } from '@/components/kiron/why-cv'
import { Mission } from '@/components/kiron/mission'
import { Materials } from '@/components/kiron/materials'
import { Prepare } from '@/components/kiron/prepare'
import { FormSection } from '@/components/kiron/form-section'

export default function Page() {
  return (
    <main className="bg-background">
      <KironNav />
      <Hero />
      <WhyCv />
      <Mission />
      <Materials />
      <Prepare />
      <FormSection />
    </main>
  )
}
