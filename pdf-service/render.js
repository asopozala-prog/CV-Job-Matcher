// Render HTML into PDF with local Chrome or serverless Chromium.

import fs from 'node:fs'
import puppeteer from 'puppeteer-core'
import chromium from '@sparticuz/chromium'

const MAC_CHROME =
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

async function launchOptions() {
  if (process.platform === 'darwin' && fs.existsSync(MAC_CHROME)) {
    return {
      executablePath: MAC_CHROME,
      headless: true,
      args: [],
    }
  }

  return {
    executablePath: await chromium.executablePath(),
    headless: 'shell',
    args: await puppeteer.defaultArgs({
      args: chromium.args,
      headless: 'shell',
    }),
  }
}

async function renderPageToPdf(page) {
  await page.waitForFunction(
    () =>
      Array.from(document.images).every(
        (image) => image.complete && image.naturalWidth > 0,
      ),
    { timeout: 30_000 },
  )

  const pdf = await page.pdf({
    printBackground: true,
    preferCSSPageSize: true,
  })

  return Buffer.from(pdf)
}

export async function renderPdf(html) {
  if (typeof html !== 'string' || !html.trim()) {
    throw new TypeError('html must be a non-empty string')
  }

  const browser = await puppeteer.launch(await launchOptions())

  try {
    const page = await browser.newPage()

    await page.setContent(html, {
      waitUntil: 'networkidle0',
      timeout: 60_000,
    })

    return await renderPageToPdf(page)
  } finally {
    await browser.close()
  }
}

export async function renderPdfFromFile(fileUrl) {
  if (typeof fileUrl !== 'string' || !fileUrl.startsWith('file://')) {
    throw new TypeError('fileUrl must be a local file:// URL')
  }

  const browser = await puppeteer.launch(await launchOptions())

  try {
    const page = await browser.newPage()

    await page.goto(fileUrl, {
      waitUntil: 'networkidle0',
      timeout: 60_000,
    })

    return await renderPageToPdf(page)
  } finally {
    await browser.close()
  }
}
