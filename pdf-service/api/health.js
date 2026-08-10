// Health endpoint for Kiron's PDF rendering service.

export default function handler(request, response) {
  response.status(200).json({ status: 'ok' })
}
