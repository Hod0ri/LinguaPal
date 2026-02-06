/**
 * 단어장 관련 타입 정의
 */

import { Word } from './word'

/**
 * 단어장 모델
 */
export interface Vocabulary {
  id: number
  name: string
  description: string
  language: number
  language_code: string
  language_name: string
  word_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

/**
 * 단어장 내 단어
 */
export interface VocabularyWord {
  id: number
  word: Word
  word_id: number
  notes: string
  added_at: string
}

/**
 * 단어장 상세 (단어 목록 포함)
 */
export interface VocabularyDetail extends Vocabulary {
  vocabulary_words: VocabularyWord[]
}

/**
 * 단어장 생성/수정 요청
 */
export interface VocabularyCreateRequest {
  name: string
  description?: string
  language: number
  is_active?: boolean
}

/**
 * 단어 추가 요청
 */
export interface AddWordToVocabularyRequest {
  word_id: number
  notes?: string
}
