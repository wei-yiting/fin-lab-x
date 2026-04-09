import { describe, test, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useToolProgress } from '../useToolProgress'

describe('useToolProgress — routing isolation', () => {
  test('progress for tc-A does not affect tc-B', () => {
    const { result } = renderHook(() => useToolProgress())

    act(() => {
      result.current.handleData({ type: 'data-tool-progress', id: 'tc-A', data: { message: 'A loading' } })
    })
    expect(result.current.toolProgress).toEqual({ 'tc-A': 'A loading' })

    act(() => {
      result.current.handleData({ type: 'data-tool-progress', id: 'tc-B', data: { message: 'B loading' } })
    })
    expect(result.current.toolProgress).toEqual({
      'tc-A': 'A loading',
      'tc-B': 'B loading',
    })

    act(() => {
      result.current.handleData({ type: 'data-tool-progress', id: 'tc-A', data: { message: 'A done' } })
    })
    expect(result.current.toolProgress).toEqual({
      'tc-A': 'A done',
      'tc-B': 'B loading',
    })
  })
})

test('rapid 3 progress updates within same tick produce final = 3rd', () => {
  const { result } = renderHook(() => useToolProgress())

  act(() => {
    result.current.handleData({ type: 'data-tool-progress', id: 'tc-1', data: { message: 'step 1' } })
    result.current.handleData({ type: 'data-tool-progress', id: 'tc-1', data: { message: 'step 2' } })
    result.current.handleData({ type: 'data-tool-progress', id: 'tc-1', data: { message: 'step 3' } })
  })

  expect(result.current.toolProgress['tc-1']).toBe('step 3')
})

test('clearProgress empties the toolProgress record', () => {
  const { result } = renderHook(() => useToolProgress())

  act(() => {
    result.current.handleData({ type: 'data-tool-progress', id: 'tc-1', data: { message: 'loading' } })
    result.current.handleData({ type: 'data-tool-progress', id: 'tc-2', data: { message: 'loading' } })
  })
  expect(Object.keys(result.current.toolProgress)).toHaveLength(2)

  act(() => result.current.clearProgress())

  expect(result.current.toolProgress).toEqual({})
})
