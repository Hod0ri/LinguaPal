/**
 * LRS Middleware
 *
 * Middleware that wraps quiz API calls to automatically handle
 * xAPI statement creation and session management.
 *
 * The backend already creates statements asynchronously, so this middleware:
 * 1. Manages local session state (registration UUID)
 * 2. Tracks quiz progress client-side
 * 3. Can optionally send additional client-side statements
 */

import type { AxiosResponse } from 'axios'
import { quizApi, wordQuizApi } from './api'
import { sessionManager, QuizStatements, generateUUID } from './lrs'
import type { ApiResponse } from '../types'
import type {
  QuizStartRequest,
  QuizStartResponse,
  QuizAnswerRequest,
  QuizAnswerResponse,
  WordQuizStartRequest,
  WordQuizStartResponse,
  WordQuizAnswerRequest,
  WordQuizAnswerResponse,
} from '../types'
import type { QuizSession, XAPIStatement } from '../types/xapi'

// Event callback types
type QuizEventCallback = (event: {
  type: 'start' | 'answer' | 'complete'
  quizType: 'gana' | 'word'
  quizId: number
  session: QuizSession
  statement?: XAPIStatement | null
  data?: Record<string, unknown>
}) => void

// Global event listeners
const eventListeners: Set<QuizEventCallback> = new Set()

/**
 * Subscribe to quiz events
 */
export function subscribeToQuizEvents(callback: QuizEventCallback): () => void {
  eventListeners.add(callback)
  return () => eventListeners.delete(callback)
}

/**
 * Emit quiz event to all listeners
 */
function emitEvent(event: Parameters<QuizEventCallback>[0]): void {
  eventListeners.forEach((callback) => {
    try {
      callback(event)
    } catch (error) {
      console.error('Quiz event callback error:', error)
    }
  })
}

/**
 * Get quiz name for statements
 */
function getQuizName(quizType: 'gana' | 'word', quizId: number): string {
  return quizType === 'gana' ? `가나 퀴즈 #${quizId}` : `단어 퀴즈 #${quizId}`
}

/**
 * LRS-enhanced Gana Quiz API
 */
export const lrsGanaQuizApi = {
  /**
   * Start quiz with LRS session tracking
   */
  async startQuiz(
    data: QuizStartRequest
  ): Promise<AxiosResponse<ApiResponse<QuizStartResponse & { registration: string }>>> {
    const response = await quizApi.startQuiz(data)

    if (response.data.success && response.data.data) {
      const quiz = response.data.data.quiz
      // Backend returns registration in response
      const registration =
        (response.data.data as unknown as { registration?: string }).registration ||
        generateUUID()

      // Start local session
      const session = sessionManager.startSession(
        'gana',
        quiz.id,
        quiz.total_questions,
        registration
      )

      // Create statement for client-side tracking (optional)
      const statement = QuizStatements.initialized(
        'gana',
        quiz.id,
        getQuizName('gana', quiz.id),
        registration,
        {
          character_set: data.character_set,
          quiz_type: data.quiz_type,
          total_questions: quiz.total_questions,
        }
      )

      // Emit event
      emitEvent({
        type: 'start',
        quizType: 'gana',
        quizId: quiz.id,
        session,
        statement,
        data: { characterSet: data.character_set, quizType: data.quiz_type },
      })

      // Return with registration added to response data
      return {
        ...response,
        data: {
          ...response.data,
          data: {
            ...response.data.data,
            registration,
          },
        },
      } as AxiosResponse<ApiResponse<QuizStartResponse & { registration: string }>>
    }

    return response as AxiosResponse<ApiResponse<QuizStartResponse & { registration: string }>>
  },

  /**
   * Submit answer with LRS tracking
   */
  async submitAnswer(
    quizId: number,
    data: QuizAnswerRequest
  ): Promise<AxiosResponse<ApiResponse<QuizAnswerResponse>>> {
    const response = await quizApi.submitAnswer(quizId, data)

    if (response.data.success && response.data.data) {
      const result = response.data.data
      const session = sessionManager.getSession('gana', quizId)

      if (session) {
        // Update session
        const updatedSession = sessionManager.updateSession('gana', quizId, {
          currentQuestion: session.currentQuestion + 1,
          correctCount: session.correctCount + (result.is_correct ? 1 : 0),
        })

        // Create answered statement
        const answeredStatement = QuizStatements.answered(
          'gana',
          quizId,
          data.question_id,
          session.currentQuestion,
          data.answer,
          result.is_correct,
          session.registration,
          { correctAnswer: result.correct_answer }
        )

        // Emit answer event
        emitEvent({
          type: 'answer',
          quizType: 'gana',
          quizId,
          session: updatedSession || session,
          statement: answeredStatement,
          data: {
            questionId: data.question_id,
            isCorrect: result.is_correct,
            correctAnswer: result.correct_answer,
          },
        })

        // Handle completion
        if (result.quiz_completed && updatedSession) {
          const completedStatement = QuizStatements.completed(
            'gana',
            quizId,
            getQuizName('gana', quizId),
            updatedSession.correctCount,
            updatedSession.totalQuestions,
            session.registration
          )

          // Emit complete event
          emitEvent({
            type: 'complete',
            quizType: 'gana',
            quizId,
            session: updatedSession,
            statement: completedStatement,
            data: {
              correctCount: updatedSession.correctCount,
              totalQuestions: updatedSession.totalQuestions,
              scorePercentage:
                (updatedSession.correctCount / updatedSession.totalQuestions) * 100,
            },
          })

          // End session
          sessionManager.endSession('gana', quizId)
        }
      }
    }

    return response
  },

  /**
   * Get current session
   */
  getSession(quizId: number): QuizSession | null {
    return sessionManager.getSession('gana', quizId)
  },

  // Passthrough methods
  getQuizDetail: quizApi.getQuizDetail,
  getCurrentQuestion: quizApi.getCurrentQuestion,
  getQuizHistory: quizApi.getQuizHistory,
  getQuizStats: quizApi.getQuizStats,
}

/**
 * LRS-enhanced Word Quiz API
 */
export const lrsWordQuizApi = {
  /**
   * Start quiz with LRS session tracking
   */
  async startQuiz(
    data: WordQuizStartRequest
  ): Promise<AxiosResponse<ApiResponse<WordQuizStartResponse & { registration: string }>>> {
    const response = await wordQuizApi.startQuiz(data)

    if (response.data.success && response.data.data) {
      const quiz = response.data.data.quiz
      const registration =
        (response.data.data as unknown as { registration?: string }).registration ||
        generateUUID()

      // Start local session
      const session = sessionManager.startSession(
        'word',
        quiz.id,
        quiz.total_questions,
        registration
      )

      // Create statement
      const statement = QuizStatements.initialized(
        'word',
        quiz.id,
        getQuizName('word', quiz.id),
        registration,
        {
          learning_language: quiz.learning_language_code,
          quiz_type: data.quiz_type,
          total_questions: quiz.total_questions,
        }
      )

      // Emit event
      emitEvent({
        type: 'start',
        quizType: 'word',
        quizId: quiz.id,
        session,
        statement,
        data: {
          learningLanguage: quiz.learning_language_code,
          quizType: data.quiz_type,
        },
      })

      return {
        ...response,
        data: {
          ...response.data,
          data: {
            ...response.data.data,
            registration,
          },
        },
      } as AxiosResponse<ApiResponse<WordQuizStartResponse & { registration: string }>>
    }

    return response as AxiosResponse<ApiResponse<WordQuizStartResponse & { registration: string }>>
  },

  /**
   * Submit answer with LRS tracking
   */
  async submitAnswer(
    quizId: number,
    data: WordQuizAnswerRequest
  ): Promise<AxiosResponse<ApiResponse<WordQuizAnswerResponse>>> {
    const response = await wordQuizApi.submitAnswer(quizId, data)

    if (response.data.success && response.data.data) {
      const result = response.data.data
      const session = sessionManager.getSession('word', quizId)

      if (session) {
        // Update session
        const updatedSession = sessionManager.updateSession('word', quizId, {
          currentQuestion: session.currentQuestion + 1,
          correctCount: session.correctCount + (result.is_correct ? 1 : 0),
        })

        // Create answered statement
        const answeredStatement = QuizStatements.answered(
          'word',
          quizId,
          data.question_id,
          session.currentQuestion,
          data.answer,
          result.is_correct,
          session.registration,
          { correctAnswer: result.correct_answer }
        )

        // Emit answer event
        emitEvent({
          type: 'answer',
          quizType: 'word',
          quizId,
          session: updatedSession || session,
          statement: answeredStatement,
          data: {
            questionId: data.question_id,
            isCorrect: result.is_correct,
            correctAnswer: result.correct_answer,
          },
        })

        // Handle completion
        if (result.quiz_completed && updatedSession) {
          const completedStatement = QuizStatements.completed(
            'word',
            quizId,
            getQuizName('word', quizId),
            updatedSession.correctCount,
            updatedSession.totalQuestions,
            session.registration
          )

          // Emit complete event
          emitEvent({
            type: 'complete',
            quizType: 'word',
            quizId,
            session: updatedSession,
            statement: completedStatement,
            data: {
              correctCount: updatedSession.correctCount,
              totalQuestions: updatedSession.totalQuestions,
              scorePercentage:
                (updatedSession.correctCount / updatedSession.totalQuestions) * 100,
            },
          })

          // End session
          sessionManager.endSession('word', quizId)
        }
      }
    }

    return response
  },

  /**
   * Get current session
   */
  getSession(quizId: number): QuizSession | null {
    return sessionManager.getSession('word', quizId)
  },

  // Passthrough methods
  getQuizDetail: wordQuizApi.getQuizDetail,
  getCurrentQuestion: wordQuizApi.getCurrentQuestion,
  getQuizHistory: wordQuizApi.getQuizHistory,
  getQuizStats: wordQuizApi.getQuizStats,
}

export default {
  ganaQuiz: lrsGanaQuizApi,
  wordQuiz: lrsWordQuizApi,
  subscribeToQuizEvents,
}
