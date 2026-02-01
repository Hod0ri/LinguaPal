/**
 * Word Management API Service
 *
 * API calls for word CRUD operations.
 * These endpoints are only accessible to staff/admin users.
 */

import api from './api'
import type {
  ApiResponse,
  Word,
  WordListResponse,
  WordListParams,
  WordCreateRequest,
  WordUpdateRequest,
  WordTranslation,
  WordTranslationCreate,
  WordExample,
  WordExampleCreate,
  ExampleTranslationCreate,
} from '../types'

// Word CRUD API
export const wordApi = {
  /**
   * Get paginated list of words with filtering
   */
  getList: (params?: WordListParams) =>
    api.get<ApiResponse<WordListResponse>>('/admin/words', { params }),

  /**
   * Get single word detail with translations and examples
   */
  getDetail: (id: number) =>
    api.get<ApiResponse<Word>>(`/admin/words/${id}`),

  /**
   * Create a new word (with optional translations and examples)
   */
  create: (data: WordCreateRequest) =>
    api.post<ApiResponse<Word>>('/admin/words/create', data),

  /**
   * Update a word
   */
  update: (id: number, data: WordUpdateRequest) =>
    api.patch<ApiResponse<Word>>(`/admin/words/${id}/update`, data),

  /**
   * Delete a word
   */
  delete: (id: number) =>
    api.delete<ApiResponse<null>>(`/admin/words/${id}/delete`),
}

// Word Translation API
export const wordTranslationApi = {
  /**
   * Get translations for a word
   */
  getList: (wordId: number) =>
    api.get<ApiResponse<WordTranslation[]>>(`/admin/words/${wordId}/translations`),

  /**
   * Add translation to a word
   */
  create: (wordId: number, data: WordTranslationCreate) =>
    api.post<ApiResponse<WordTranslation>>(`/admin/words/${wordId}/translations/create`, data),

  /**
   * Update a translation
   */
  update: (wordId: number, translationId: number, data: Partial<WordTranslationCreate>) =>
    api.patch<ApiResponse<WordTranslation>>(
      `/admin/words/${wordId}/translations/${translationId}/update`,
      data
    ),

  /**
   * Delete a translation
   */
  delete: (wordId: number, translationId: number) =>
    api.delete<ApiResponse<null>>(
      `/admin/words/${wordId}/translations/${translationId}/delete`
    ),
}

// Word Example API
export const wordExampleApi = {
  /**
   * Get examples for a word
   */
  getList: (wordId: number) =>
    api.get<ApiResponse<WordExample[]>>(`/admin/words/${wordId}/examples`),

  /**
   * Add example to a word
   */
  create: (wordId: number, data: WordExampleCreate) =>
    api.post<ApiResponse<WordExample>>(`/admin/words/${wordId}/examples/create`, data),

  /**
   * Update an example
   */
  update: (wordId: number, exampleId: number, data: Partial<WordExampleCreate>) =>
    api.patch<ApiResponse<WordExample>>(
      `/admin/words/${wordId}/examples/${exampleId}/update`,
      data
    ),

  /**
   * Delete an example
   */
  delete: (wordId: number, exampleId: number) =>
    api.delete<ApiResponse<null>>(
      `/admin/words/${wordId}/examples/${exampleId}/delete`
    ),
}

// Example Translation API
export const exampleTranslationApi = {
  /**
   * Add translation to an example
   */
  create: (wordId: number, exampleId: number, data: ExampleTranslationCreate) =>
    api.post<ApiResponse<{ id: number }>>(
      `/admin/words/${wordId}/examples/${exampleId}/translations/create`,
      data
    ),

  /**
   * Update an example translation
   */
  update: (
    wordId: number,
    exampleId: number,
    translationId: number,
    data: Partial<ExampleTranslationCreate>
  ) =>
    api.patch<ApiResponse<{ id: number }>>(
      `/admin/words/${wordId}/examples/${exampleId}/translations/${translationId}/update`,
      data
    ),

  /**
   * Delete an example translation
   */
  delete: (wordId: number, exampleId: number, translationId: number) =>
    api.delete<ApiResponse<null>>(
      `/admin/words/${wordId}/examples/${exampleId}/translations/${translationId}/delete`
    ),
}

export default wordApi
