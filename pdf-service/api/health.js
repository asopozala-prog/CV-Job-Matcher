// Health endpoint for Kiron's PDF rendering service.

export default {
  fetch() {
    return Response.json({ status: 'ok' })
  },
}
