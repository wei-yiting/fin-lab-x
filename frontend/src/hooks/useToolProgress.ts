import { useState, useCallback } from "react"
import type { ToolProgressRecord } from "@/models"

export function useToolProgress() {
  const [toolProgress, setProgress] = useState<ToolProgressRecord>({})
  const handleData = useCallback((dataPart: { type: string; id?: string; data: unknown }) => {
    if (dataPart.type !== "data-tool-progress") return
    if (!dataPart.id) return
    const payload = dataPart.data as { message?: string } | undefined
    if (payload?.message) {
      setProgress(prev => ({ ...prev, [dataPart.id!]: payload.message! }))
    }
  }, [])
  const clearProgress = useCallback(() => setProgress({}), [])
  return { toolProgress, handleData, clearProgress }
}
