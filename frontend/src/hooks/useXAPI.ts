/**
 * useXAPI Hook
 *
 * React hook for integrating xAPI/LRS functionality into quiz components.
 * Provides session management and event subscription.
 */

import { useEffect, useCallback, useState, useRef } from 'react'
import { sessionManager } from '../services/lrs'
import {
  lrsGanaQuizApi,
  lrsWordQuizApi,
  subscribeToQuizEvents,
} from '../services/lrsMiddleware'
import type { QuizSession, XAPIStatement } from '../types/xapi'

interface QuizEvent {
  type: 'start' | 'answer' | 'complete'
  quizType: 'gana' | 'word'
  quizId: number
  session: QuizSession
  statement?: XAPIStatement | null
  data?: Record<string, unknown>
}

interface UseXAPIOptions {
  quizType: 'gana' | 'word'
  quizId?: number
  onStart?: (event: QuizEvent) => void
  onAnswer?: (event: QuizEvent) => void
  onComplete?: (event: QuizEvent) => void
}

interface UseXAPIReturn {
  // Current session
  session: QuizSession | null

  // API methods (LRS-enhanced)
  api: typeof lrsGanaQuizApi | typeof lrsWordQuizApi

  // Session management
  getSession: () => QuizSession | null
  clearSession: () => void

  // Event history (last N events)
  recentEvents: QuizEvent[]
}

/**
 * Hook for using xAPI/LRS in quiz components
 */
export function useXAPI(options: UseXAPIOptions): UseXAPIReturn {
  const { quizType, quizId, onStart, onAnswer, onComplete } = options

  const [session, setSession] = useState<QuizSession | null>(null)
  const [recentEvents, setRecentEvents] = useState<QuizEvent[]>([])
  const callbacksRef = useRef({ onStart, onAnswer, onComplete })

  // Update refs when callbacks change
  useEffect(() => {
    callbacksRef.current = { onStart, onAnswer, onComplete }
  }, [onStart, onAnswer, onComplete])

  // Get the appropriate API
  const api = quizType === 'gana' ? lrsGanaQuizApi : lrsWordQuizApi

  // Load session on mount or when quizId changes
  useEffect(() => {
    if (quizId) {
      const existingSession = sessionManager.getSession(quizType, quizId)
      setSession(existingSession)
    }
  }, [quizType, quizId])

  // Subscribe to quiz events
  useEffect(() => {
    const unsubscribe = subscribeToQuizEvents((event) => {
      // Only handle events for our quiz type
      if (event.quizType !== quizType) return

      // If we have a specific quizId, only handle events for that quiz
      if (quizId && event.quizId !== quizId) return

      // Update session state
      setSession(event.session)

      // Add to recent events (keep last 50)
      setRecentEvents((prev) => [...prev.slice(-49), event])

      // Call appropriate callback
      const callbacks = callbacksRef.current
      switch (event.type) {
        case 'start':
          callbacks.onStart?.(event)
          break
        case 'answer':
          callbacks.onAnswer?.(event)
          break
        case 'complete':
          callbacks.onComplete?.(event)
          break
      }
    })

    return unsubscribe
  }, [quizType, quizId])

  // Get current session
  const getSession = useCallback((): QuizSession | null => {
    if (!quizId) return null
    return sessionManager.getSession(quizType, quizId)
  }, [quizType, quizId])

  // Clear session
  const clearSession = useCallback((): void => {
    if (quizId) {
      sessionManager.endSession(quizType, quizId)
      setSession(null)
    }
  }, [quizType, quizId])

  return {
    session,
    api,
    getSession,
    clearSession,
    recentEvents,
  }
}

/**
 * Hook for Gana Quiz with xAPI
 */
export function useGanaQuizXAPI(
  quizId?: number,
  callbacks?: {
    onStart?: (event: QuizEvent) => void
    onAnswer?: (event: QuizEvent) => void
    onComplete?: (event: QuizEvent) => void
  }
) {
  return useXAPI({
    quizType: 'gana',
    quizId,
    ...callbacks,
  })
}

/**
 * Hook for Word Quiz with xAPI
 */
export function useWordQuizXAPI(
  quizId?: number,
  callbacks?: {
    onStart?: (event: QuizEvent) => void
    onAnswer?: (event: QuizEvent) => void
    onComplete?: (event: QuizEvent) => void
  }
) {
  return useXAPI({
    quizType: 'word',
    quizId,
    ...callbacks,
  })
}

/**
 * Hook for subscribing to all quiz events (useful for analytics/debugging)
 */
export function useQuizEventSubscription(
  callback: (event: QuizEvent) => void
): void {
  const callbackRef = useRef(callback)

  useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  useEffect(() => {
    return subscribeToQuizEvents((event) => {
      callbackRef.current(event)
    })
  }, [])
}

export default useXAPI
