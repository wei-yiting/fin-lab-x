export class ChatHttpError extends Error {
  readonly status: number

  constructor(status: number, body: string) {
    super(body || `HTTP ${status}`)
    this.name = "ChatHttpError"
    this.status = status
  }
}
