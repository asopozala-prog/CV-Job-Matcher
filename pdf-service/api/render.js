// Render self-contained HTML into PDF through Kiron's shared Chromium renderer.

import { renderPdf } from '../render.js'

export const maxDuration = 60

export default {
  async fetch(request) {
    try {
      const body = await request.json()
      const pdf = await renderPdf(body?.html)

      return new Response(pdf, {
        status: 200,
        headers: {
          'Content-Type': 'application/pdf',
        },
      })
    } catch (error) {
      console.error('PDF render failed', error)

      return Response.json(
        { detail: 'PDF rendering failed.' },
        { status: 500 },
      )
    }
  },
}
