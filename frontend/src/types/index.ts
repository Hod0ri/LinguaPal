export interface User {
  id: number
  email: string
  name: string
  profile_image: string | null
  role: 'admin' | 'staff' | 'user'
}

export interface Language {
  id: number
  code: string
  name_ko: string
  name_en: string
}

export interface Country {
  id: number
  code: string
  name_ko: string
  name_en: string
}

export interface UserProfile {
  id: number
  user_email: string
  nickname: string
  country: Country
  learning_languages: Language[]
  created_at: string
  updated_at: string
}

export interface ApiResponse<T> {
  success: boolean
  message: string
  data: T
}

export interface AuthTokens {
  access: string
  refresh: string
}

// Quiz Types
export type GanaCharacterSet = 'hiragana' | 'katakana' | 'all'
export type GanaQuizType = 'gana_to_romaji' | 'romaji_to_gana_select' | 'romaji_to_gana_input'
export type GanaQuizQuestionCount = '10' | '25' | '0'

export interface GanaQuizQuestion {
  id: number
  question_number: number
  question: string
  choices: string[] | null
  user_answer: string | null
  is_correct: boolean | null
  correct_answer?: string
  answered_at: string | null
}

export interface GanaQuiz {
  id: number
  character_set: GanaCharacterSet
  character_set_display: string
  quiz_type: GanaQuizType
  quiz_type_display: string
  question_count_setting: number
  total_questions: number
  correct_count: number
  current_question: number
  is_completed: boolean
  score_percentage: number
  started_at: string
  completed_at: string | null
  questions: GanaQuizQuestion[]
}

export interface GanaQuizListItem {
  id: number
  character_set: GanaCharacterSet
  character_set_display: string
  quiz_type: GanaQuizType
  quiz_type_display: string
  total_questions: number
  correct_count: number
  is_completed: boolean
  score_percentage: number
  started_at: string
  completed_at: string | null
}

export interface CurrentQuestion {
  id: number
  question_number: number
  question: string
  choices: string[] | null
}

export interface QuizProgress {
  current: number
  total: number
  correct_so_far: number
}

export interface QuizStartRequest {
  character_set: GanaCharacterSet
  quiz_type: GanaQuizType
  question_count: GanaQuizQuestionCount
}

export interface QuizStartResponse {
  quiz: GanaQuiz
  current_question: CurrentQuestion
}

export interface QuizAnswerRequest {
  question_id: number
  answer: string
}

export interface QuizAnswerResponse {
  is_correct: boolean
  correct_answer: string
  user_answer: string
  next_question: CurrentQuestion | null
  quiz_completed: boolean
  current_score: number
  total_answered: number
}

export interface CharacterStats {
  total_attempts: number
  correct_count: number
  accuracy: number
  characters_practiced: number
}

export interface UserGanaStats {
  word_text: string
  word_pronunciation: string
  character_type: string
  total_attempts: number
  correct_count: number
  incorrect_count: number
  accuracy: number
}

export interface QuizStats {
  total_quizzes: number
  completed_quizzes: number
  total_questions_answered: number
  total_correct: number
  overall_accuracy: number
  hiragana_stats: CharacterStats
  katakana_stats: CharacterStats
  weakest_characters: UserGanaStats[]
  strongest_characters: UserGanaStats[]
}

// ============= Word Quiz Types =============
export type WordQuizType = 'word_to_native' | 'native_to_word_select' | 'native_to_word_input'
export type WordQuizQuestionCount = '10' | '25' | '0'

export interface WordQuizQuestion {
  id: number
  question_number: number
  question: string
  choices: string[] | null
  user_answer: string | null
  is_correct: boolean | null
  correct_answer?: string
  answered_at: string | null
}

export interface WordQuiz {
  id: number
  learning_language: number
  learning_language_code: string
  learning_language_name: string
  native_language: number
  native_language_code: string
  native_language_name: string
  quiz_type: WordQuizType
  quiz_type_display: string
  question_count_setting: number
  total_questions: number
  correct_count: number
  current_question: number
  is_completed: boolean
  score_percentage: number
  started_at: string
  completed_at: string | null
  questions: WordQuizQuestion[]
}

export interface WordQuizListItem {
  id: number
  learning_language: number
  learning_language_code: string
  learning_language_name: string
  quiz_type: WordQuizType
  quiz_type_display: string
  total_questions: number
  correct_count: number
  is_completed: boolean
  score_percentage: number
  started_at: string
  completed_at: string | null
}

export interface WordQuizStartRequest {
  learning_language: string
  quiz_type: WordQuizType
  question_count: WordQuizQuestionCount
  vocabulary_id?: number | null
}

export interface WordQuizStartResponse {
  quiz: WordQuiz
  current_question: CurrentQuestion
}

export interface WordQuizAnswerRequest {
  question_id: number
  answer: string
}

export interface WordQuizAnswerResponse {
  is_correct: boolean
  correct_answer: string
  user_answer: string
  next_question: CurrentQuestion | null
  quiz_completed: boolean
  current_score: number
  total_answered: number
}

export interface UserWordStats {
  word_text: string
  word_language: string
  total_attempts: number
  correct_count: number
  incorrect_count: number
  accuracy: number
}

export interface LanguageStats {
  language_name: string
  total_attempts: number
  correct_count: number
  accuracy: number
  quiz_count: number
}

export interface WordQuizStats {
  total_quizzes: number
  completed_quizzes: number
  total_questions_answered: number
  total_correct: number
  overall_accuracy: number
  language_stats: Record<string, LanguageStats>
  weakest_words: UserWordStats[]
  strongest_words: UserWordStats[]
}

// ============= Flashcard Types =============
import type { WordCategory as FlashcardWordCategory } from './word'

export interface FlashcardWord {
  id: number
  word_text: string
  word_pronunciation: string | null
  category: FlashcardWordCategory
  difficulty: number
  translation: string | null
  example: string | null
  example_translation: string | null
  example_highlight: number[] | null
  example_translation_highlight: number[] | null
}

export interface FlashcardRecord {
  id: number
  card_index: number
  is_known: boolean | null
  viewed_at: string | null
  answered_at: string | null
  word: FlashcardWord
}

export interface FlashcardSession {
  id: number
  learning_language: number
  learning_language_code: string
  learning_language_name: string
  category: FlashcardWordCategory | ''
  total_cards: number
  known_count: number
  unknown_count: number
  current_index: number
  is_completed: boolean
  progress_percentage: number
  created_at: string
  completed_at: string | null
}

export interface FlashcardSessionDetail extends FlashcardSession {
  records: FlashcardRecord[]
}

export interface FlashcardStartRequest {
  learning_language: string
  category?: FlashcardWordCategory | ''
  card_count?: number
  vocabulary_id?: number | null
}

export interface FlashcardStartResponse {
  session: FlashcardSession
  current_card: FlashcardRecord
}

export interface FlashcardCurrentResponse {
  session: FlashcardSession
  current_card: FlashcardRecord | null
}

export interface FlashcardAnswerRequest {
  record_id: number
  is_known: boolean
}

export interface FlashcardAnswerResponse {
  record: FlashcardRecord
  next_card: FlashcardRecord | null
  session_completed: boolean
  known_count: number
  unknown_count: number
}

// Re-export xAPI types
export * from './xapi'

// Re-export admin types
export * from './admin'

// Re-export word types
export * from './word'
