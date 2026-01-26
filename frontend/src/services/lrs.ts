/**
 * LRS (Learning Record Store) Service
 *
 * Service for managing xAPI statements and quiz sessions.
 * Handles session tracking and provides helpers for xAPI statement creation.
 */

import type {
  QuizSession,
  XAPIStatement,
  XAPIActor,
  XAPIVerb,
  XAPIObject,
  XAPIResult,
  XAPIContext,
} from '../types/xapi'
import { XAPIVerbs, XAPIActivityTypes } from '../types/xapi'

const LINGUAPAL_BASE_IRI = 'https://linguapal.com'

// Session storage key
const SESSION_STORAGE_KEY = 'lrs_quiz_sessions'

/**
 * Generate a UUID v4
 */
export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

/**
 * Get current user info for xAPI Actor
 */
function getCurrentActor(): XAPIActor | null {
  const userStr = localStorage.getItem('user')
  if (!userStr) return null

  try {
    const user = JSON.parse(userStr)
    return {
      objectType: 'Agent',
      mbox: `mailto:${user.email}`,
      name: user.name || user.email,
    }
  } catch {
    return null
  }
}

/**
 * Session Manager for quiz tracking
 */
class QuizSessionManager {
  private sessions: Map<string, QuizSession> = new Map()

  constructor() {
    this.loadFromStorage()
  }

  private loadFromStorage(): void {
    try {
      const stored = sessionStorage.getItem(SESSION_STORAGE_KEY)
      if (stored) {
        const sessions = JSON.parse(stored) as QuizSession[]
        sessions.forEach((session) => {
          const key = this.getSessionKey(session.quizType, session.quizId)
          this.sessions.set(key, session)
        })
      }
    } catch (error) {
      console.warn('Failed to load quiz sessions from storage:', error)
    }
  }

  private saveToStorage(): void {
    try {
      const sessions = Array.from(this.sessions.values())
      sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessions))
    } catch (error) {
      console.warn('Failed to save quiz sessions to storage:', error)
    }
  }

  private getSessionKey(quizType: 'gana' | 'word', quizId: number): string {
    return `${quizType}_${quizId}`
  }

  /**
   * Start a new quiz session
   */
  startSession(
    quizType: 'gana' | 'word',
    quizId: number,
    totalQuestions: number,
    registration?: string
  ): QuizSession {
    const session: QuizSession = {
      quizId,
      quizType,
      registration: registration || generateUUID(),
      startedAt: new Date().toISOString(),
      totalQuestions,
      currentQuestion: 1,
      correctCount: 0,
    }

    const key = this.getSessionKey(quizType, quizId)
    this.sessions.set(key, session)
    this.saveToStorage()

    return session
  }

  /**
   * Get an existing session
   */
  getSession(quizType: 'gana' | 'word', quizId: number): QuizSession | null {
    const key = this.getSessionKey(quizType, quizId)
    return this.sessions.get(key) || null
  }

  /**
   * Update session progress
   */
  updateSession(
    quizType: 'gana' | 'word',
    quizId: number,
    updates: Partial<Pick<QuizSession, 'currentQuestion' | 'correctCount'>>
  ): QuizSession | null {
    const session = this.getSession(quizType, quizId)
    if (!session) return null

    const key = this.getSessionKey(quizType, quizId)
    const updatedSession = { ...session, ...updates }
    this.sessions.set(key, updatedSession)
    this.saveToStorage()

    return updatedSession
  }

  /**
   * End and remove a session
   */
  endSession(quizType: 'gana' | 'word', quizId: number): QuizSession | null {
    const key = this.getSessionKey(quizType, quizId)
    const session = this.sessions.get(key)
    if (session) {
      this.sessions.delete(key)
      this.saveToStorage()
    }
    return session || null
  }

  /**
   * Clear all sessions
   */
  clearAllSessions(): void {
    this.sessions.clear()
    sessionStorage.removeItem(SESSION_STORAGE_KEY)
  }
}

// Singleton instance
export const sessionManager = new QuizSessionManager()

/**
 * xAPI Statement Builder
 */
export class StatementBuilder {
  private actor: XAPIActor | null = null
  private verb: XAPIVerb | null = null
  private object: XAPIObject | null = null
  private result: XAPIResult | null = null
  private context: XAPIContext | null = null
  private timestamp: string | null = null

  constructor() {
    this.actor = getCurrentActor()
  }

  setVerb(verbId: string, display: string): this {
    this.verb = {
      id: verbId,
      display: { 'en-US': display, ko: display },
    }
    return this
  }

  setActivity(
    activityId: string,
    name: string,
    activityType: string = XAPIActivityTypes.ASSESSMENT,
    description?: string
  ): this {
    const fullId = activityId.startsWith('http')
      ? activityId
      : `${LINGUAPAL_BASE_IRI}/${activityId}`

    this.object = {
      objectType: 'Activity',
      id: fullId,
      definition: {
        type: activityType,
        name: { ko: name },
        ...(description && { description: { ko: description } }),
      },
    }
    return this
  }

  setResult(result: XAPIResult): this {
    this.result = result
    return this
  }

  setContext(registration?: string, extensions?: Record<string, unknown>): this {
    this.context = {
      ...(registration && { registration }),
      ...(extensions && { extensions }),
    }
    return this
  }

  setTimestamp(timestamp?: string): this {
    this.timestamp = timestamp || new Date().toISOString()
    return this
  }

  build(): XAPIStatement | null {
    if (!this.actor || !this.verb || !this.object) {
      console.warn('Cannot build statement: missing required fields')
      return null
    }

    const statement: XAPIStatement = {
      actor: this.actor,
      verb: this.verb,
      object: this.object,
    }

    if (this.result) statement.result = this.result
    if (this.context) statement.context = this.context
    if (this.timestamp) statement.timestamp = this.timestamp

    return statement
  }
}

/**
 * Pre-built statement creators for common quiz events
 */
export const QuizStatements = {
  /**
   * Create INITIALIZED statement for quiz start
   */
  initialized(
    quizType: 'gana' | 'word',
    quizId: number,
    quizName: string,
    registration: string,
    extensions?: Record<string, unknown>
  ): XAPIStatement | null {
    return new StatementBuilder()
      .setVerb(XAPIVerbs.INITIALIZED, 'initialized')
      .setActivity(
        `quiz/${quizType}/${quizId}`,
        quizName,
        XAPIActivityTypes.ASSESSMENT
      )
      .setContext(registration, extensions)
      .setTimestamp()
      .build()
  },

  /**
   * Create ANSWERED statement for question response
   */
  answered(
    quizType: 'gana' | 'word',
    quizId: number,
    questionId: number,
    questionNumber: number,
    userAnswer: string,
    isCorrect: boolean,
    registration?: string,
    extensions?: Record<string, unknown>
  ): XAPIStatement | null {
    return new StatementBuilder()
      .setVerb(XAPIVerbs.ANSWERED, 'answered')
      .setActivity(
        `quiz/${quizType}/${quizId}/question/${questionId}`,
        `문제 #${questionNumber}`,
        XAPIActivityTypes.QUESTION
      )
      .setResult({
        success: isCorrect,
        response: userAnswer,
      })
      .setContext(registration, {
        questionNumber,
        ...extensions,
      })
      .setTimestamp()
      .build()
  },

  /**
   * Create COMPLETED statement for quiz completion
   */
  completed(
    quizType: 'gana' | 'word',
    quizId: number,
    quizName: string,
    correctCount: number,
    totalQuestions: number,
    registration?: string
  ): XAPIStatement | null {
    const scoreScaled = totalQuestions > 0 ? correctCount / totalQuestions : 0

    return new StatementBuilder()
      .setVerb(XAPIVerbs.COMPLETED, 'completed')
      .setActivity(
        `quiz/${quizType}/${quizId}`,
        quizName,
        XAPIActivityTypes.ASSESSMENT
      )
      .setResult({
        completion: true,
        score: {
          scaled: scoreScaled,
          raw: correctCount,
          min: 0,
          max: totalQuestions,
        },
      })
      .setContext(registration)
      .setTimestamp()
      .build()
  },

  /**
   * Create PASSED or FAILED statement based on score
   */
  passedOrFailed(
    quizType: 'gana' | 'word',
    quizId: number,
    quizName: string,
    correctCount: number,
    totalQuestions: number,
    masteryScore: number = 0.8,
    registration?: string
  ): XAPIStatement | null {
    const scoreScaled = totalQuestions > 0 ? correctCount / totalQuestions : 0
    const passed = scoreScaled >= masteryScore

    return new StatementBuilder()
      .setVerb(
        passed ? XAPIVerbs.PASSED : XAPIVerbs.FAILED,
        passed ? 'passed' : 'failed'
      )
      .setActivity(
        `quiz/${quizType}/${quizId}`,
        quizName,
        XAPIActivityTypes.ASSESSMENT
      )
      .setResult({
        success: passed,
        score: {
          scaled: scoreScaled,
        },
      })
      .setContext(registration, { masteryScore })
      .setTimestamp()
      .build()
  },
}

export default {
  sessionManager,
  StatementBuilder,
  QuizStatements,
  generateUUID,
}
