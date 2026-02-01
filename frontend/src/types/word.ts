/**
 * Word Management Types
 */

// Word Categories
export type WordCategory = 'word' | 'hiragana' | 'katakana' | 'kanji' | 'alphabet'

// Parts of Speech
export type PartOfSpeech =
  | 'noun'
  | 'verb'
  | 'adjective'
  | 'adverb'
  | 'pronoun'
  | 'preposition'
  | 'conjunction'
  | 'interjection'
  | 'article'
  | 'determiner'
  | 'numeral'
  | 'particle'
  | 'phrase'
  | 'character'
  | 'other'

// Word Translation
export interface WordTranslation {
  id: number
  language: number
  language_code: string
  language_name: string
  translated_text: string
  notes: string
  created_at: string
  updated_at: string
}

export interface WordTranslationCreate {
  language_id: number
  translated_text: string
  notes?: string
}

// Example Translation
export interface ExampleTranslation {
  id: number
  language: number
  language_code: string
  language_name: string
  translated_sentence: string
  created_at: string
  updated_at: string
}

export interface ExampleTranslationCreate {
  language_id: number
  translated_sentence: string
}

// Example (with translations)
export interface WordExample {
  id: number
  sentence: string
  highlight_indices: number[]
  translations: ExampleTranslation[]
  created_at: string
  updated_at: string
}

export interface WordExampleCreate {
  sentence: string
  highlight_indices?: number[]
  translations?: ExampleTranslationCreate[]
}

// Full Word (with translations and examples)
export interface Word {
  id: number
  language: number
  language_code: string
  language_name: string
  category: WordCategory
  category_display: string
  text: string
  part_of_speech: PartOfSpeech
  part_of_speech_display: string
  pronunciation: string
  audio_url: string
  grammar: Record<string, unknown>
  order: number
  difficulty_level: number
  is_active: boolean
  translations: WordTranslation[]
  examples: WordExample[]
  created_at: string
  updated_at: string
}

// Word List Item (lightweight)
export interface WordListItem {
  id: number
  language: number
  language_code: string
  language_name: string
  category: WordCategory
  category_display: string
  text: string
  part_of_speech: PartOfSpeech
  part_of_speech_display: string
  pronunciation: string
  difficulty_level: number
  is_active: boolean
  translation_count: number
  example_count: number
  created_at: string
}

// Word Create Request
export interface WordCreateRequest {
  language_id: number
  category: WordCategory
  text: string
  part_of_speech: PartOfSpeech
  pronunciation?: string
  audio_url?: string
  grammar?: Record<string, unknown>
  order?: number
  difficulty_level?: number
  is_active?: boolean
  translations?: WordTranslationCreate[]
  examples?: WordExampleCreate[]
}

// Word Update Request
export interface WordUpdateRequest {
  category?: WordCategory
  text?: string
  part_of_speech?: PartOfSpeech
  pronunciation?: string
  audio_url?: string
  grammar?: Record<string, unknown>
  order?: number
  difficulty_level?: number
  is_active?: boolean
}

// Word List Response
export interface WordListResponse {
  words: WordListItem[]
  total_count: number
  page: number
  page_size: number
}

// Word List Query Params
export interface WordListParams {
  language?: number
  category?: WordCategory
  part_of_speech?: PartOfSpeech
  difficulty_level?: number
  is_active?: boolean
  search?: string
  page?: number
  page_size?: number
}

// Choice Options for Forms
export const WORD_CATEGORY_OPTIONS: { value: WordCategory; label: string }[] = [
  { value: 'word', label: '단어' },
  { value: 'hiragana', label: '히라가나' },
  { value: 'katakana', label: '가타카나' },
  { value: 'kanji', label: '한자' },
  { value: 'alphabet', label: '알파벳' },
]

export const PART_OF_SPEECH_OPTIONS: { value: PartOfSpeech; label: string }[] = [
  { value: 'noun', label: '명사' },
  { value: 'verb', label: '동사' },
  { value: 'adjective', label: '형용사' },
  { value: 'adverb', label: '부사' },
  { value: 'pronoun', label: '대명사' },
  { value: 'preposition', label: '전치사' },
  { value: 'conjunction', label: '접속사' },
  { value: 'interjection', label: '감탄사' },
  { value: 'article', label: '관사' },
  { value: 'determiner', label: '한정사' },
  { value: 'numeral', label: '수사' },
  { value: 'particle', label: '조사' },
  { value: 'phrase', label: '구문' },
  { value: 'character', label: '문자' },
  { value: 'other', label: '기타' },
]

export const DIFFICULTY_OPTIONS = [
  { value: 1, label: '1 (초급)' },
  { value: 2, label: '2' },
  { value: 3, label: '3 (중급)' },
  { value: 4, label: '4' },
  { value: 5, label: '5 (고급)' },
]
