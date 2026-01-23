export interface User {
  id: number
  email: string
  name: string
  profile_image: string | null
  role: 'ADMIN' | 'STAFF' | 'USER'
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
