export type UIMessageChunk =
  | { type: 'start'; messageId: string }
  | { type: 'text-start'; id: string }
  | { type: 'text-delta'; id: string; delta: string }
  | { type: 'text-end'; id: string }
  | { type: 'tool-input-available'; toolCallId: string; toolName: string; input: object }
  | { type: 'tool-output-available'; toolCallId: string; output: object }
  | { type: 'tool-output-error'; toolCallId: string; errorText: string }
  | { type: 'data-tool-progress'; id: string; data: { message: string }; transient: true }
  | { type: 'error'; errorText: string }
  | { type: 'finish' }

export type SSEStreamFixture = {
  description: string
  scenarios: string[]
  chunks: Array<{ delayMs?: number; data: UIMessageChunk }>
  dropConnectionBeforeEnd?: boolean
}

export type PreStreamErrorFixture = {
  description: string
  scenarios: string[]
  preStreamError: {
    status: number
    body?: string
  }
}

export type NetworkFailureFixture = {
  description: string
  scenarios: string[]
  networkFailure: true
}

export type SingleFixture = SSEStreamFixture | PreStreamErrorFixture | NetworkFailureFixture

export type SequentialFixture = {
  description: string
  scenarios: string[]
  responses: SingleFixture[]
}

export type SSEFixture = SingleFixture | SequentialFixture
