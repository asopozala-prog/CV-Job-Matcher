// Vercel API endpoint for Kiron's PDF rendering service.

import { renderPdf } from '../render.js'

export const maxDuration = 60

export default async function handler(request, response) {
  if (request.method !== 'POST') {
    return response.status(405).json({ detail: 'Method not allowed.' })
  }

  try {
    const { html } = request.body ?? {}

    if (!html || typeof html !== 'string') {
      return response.status(400).json({ detail: 'html is required.' })
    }

    const pdf = await renderPdf(html)

    response.setHeader('Content-Type', 'application/pdf')
    return response.status(200).send(pdf)
  } catch (error) {
    console.error('PDF render failed:', error)
    return response.status(500).json({ detail: 'PDF rendering failed.' })
  }
}
