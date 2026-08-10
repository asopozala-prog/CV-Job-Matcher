// Integration-test Kiron's shared PDF renderer with real local Chrome.

import test from 'node:test'
import assert from 'node:assert/strict'

import { renderPdf } from '../render.js'

test('renderPdf creates a real PDF from simple HTML', async () => {
  const pdf = await renderPdf(`
    <!doctype html>
    <html>
      <head>
        <style>
          @page { size: A4; margin: 20mm; }
          body { font-family: sans-serif; }
        </style>
      </head>
      <body>
        <h1>Kiron PDF integration test</h1>
        <p>The renderer is working.</p>
      </body>
    </html>
  `)

  assert.ok(Buffer.isBuffer(pdf))
  assert.ok(pdf.length > 1000)
  assert.equal(pdf.subarray(0, 4).toString(), '%PDF')
})

test('renderPdf rejects empty HTML', async () => {
  await assert.rejects(
    () => renderPdf(''),
    /html must be a non-empty string/,
  )
})
