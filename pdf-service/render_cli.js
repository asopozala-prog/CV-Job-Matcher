// Local CLI for rendering one HTML file with the shared PDF renderer.

import fs from 'node:fs/promises'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
import { renderPdfFromFile } from './render.js'

const [, , htmlPath, outputPath] = process.argv

if (!htmlPath || !outputPath) {
  console.error('Usage: node render_cli.js <input.html> <output.pdf>')
  process.exit(2)
}

const sourcePath = path.resolve(htmlPath)
const destinationPath = path.resolve(outputPath)

await fs.access(sourcePath)

const pdf = await renderPdfFromFile(pathToFileURL(sourcePath).href)

await fs.mkdir(path.dirname(destinationPath), { recursive: true })
await fs.writeFile(destinationPath, pdf)

console.log(destinationPath)
