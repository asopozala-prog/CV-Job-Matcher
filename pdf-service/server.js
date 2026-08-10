// Private Vercel service exposing Kiron's HTML-to-PDF renderer.

import express from 'express'
import { renderPdf } from './render.js'

const app = express()

app.use(express.json({ limit: '10mb' }))

app.get('/health', (_request, response) => {
  response.json({ status: 'ok' })
})

app.post('/render', async (request, response) => {
  try {
    const html = request.body?.html
    const pdf = await renderPdf(html)

    response.setHeader('Content-Type', 'application/pdf')
    response.setHeader('Content-Length', String(pdf.length))
    response.send(pdf)
  } catch (error) {
    console.error('PDF render failed', error)
    response.status(500).json({
      detail: 'PDF rendering failed.',
    })
  }
})

const port = Number(process.env.PORT || 8787)

if (!process.env.VERCEL) {
  app.listen(port, '127.0.0.1', () => {
    console.log(`Kiron PDF service listening on http://127.0.0.1:${port}`)
  })
}

export default app
