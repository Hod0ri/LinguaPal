/**
 * Flashcard Learning API Service
 *
 * API calls for flashcard learning sessions.
 */

import api from './api'
import type {
  ApiResponse,
  FlashcardSession,
  FlashcardSessionDetail,
  FlashcardStartRequest,
  FlashcardStartResponse,
  FlashcardCurrentResponse,
  FlashcardAnswerRequest,
  FlashcardAnswerResponse,
} from '../types'

export const flashcardApi = {
  /**
   * Start a new flashcard session
   */
  start: (data: FlashcardStartRequest) =>
    api.post<ApiResponse<FlashcardStartResponse>>('/flashcard/start', data),

  /**
   * Get current card in session
   */
  getCurrent: (sessionId: number) =>
    api.get<ApiResponse<FlashcardCurrentResponse>>(`/flashcard/${sessionId}/current`),

  /**
   * Submit answer for current card
   */
  answer: (sessionId: number, data: FlashcardAnswerRequest) =>
    api.post<ApiResponse<FlashcardAnswerResponse>>(`/flashcard/${sessionId}/answer`, data),

  /**
   * Get session detail with all records
   */
  getDetail: (sessionId: number) =>
    api.get<ApiResponse<FlashcardSessionDetail>>(`/flashcard/${sessionId}`),

  /**
   * Get flashcard history
   */
  getHistory: (params?: { learning_language?: string; is_completed?: boolean; page?: number }) =>
    api.get<ApiResponse<{ results: FlashcardSession[]; count: number }>>('/flashcard/history', { params }),

  /**
   * Abandon (leave) a session in progress
   */
  abandon: (sessionId: number) =>
    api.post<ApiResponse<FlashcardSession>>(`/flashcard/${sessionId}/abandon`),
}

export default flashcardApi
