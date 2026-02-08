import axios from 'axios'
import type {
  ApiResponse,
  User,
  UserProfile,
  Language,
  Country,
  QuizStartRequest,
  QuizStartResponse,
  QuizAnswerRequest,
  QuizAnswerResponse,
  GanaQuiz,
  GanaQuizListItem,
  CurrentQuestion,
  QuizProgress,
  QuizStats,
  WordQuizStartRequest,
  WordQuizStartResponse,
  WordQuizAnswerRequest,
  WordQuizAnswerResponse,
  WordQuiz,
  WordQuizListItem,
  WordQuizStats,
  BrowseWord,
  BrowseWordListResponse,
  BrowseWordParams,
  RandomWordParams,
  StreakRecommendationResponse,
} from '../types'
import type {
  Vocabulary,
  VocabularyDetail,
  VocabularyCreateRequest,
  AddWordToVocabularyRequest,
} from '../types/vocabulary'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for adding auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  const apiKey = import.meta.env.VITE_API_KEY
  if (apiKey) {
    config.headers['X-API-KEY'] = apiKey
  }

  return config
})

// Response interceptor for handling token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh`, {
            refresh: refreshToken,
          })
          const { access } = response.data
          localStorage.setItem('access_token', access)
          originalRequest.headers.Authorization = `Bearer ${access}`
          return api(originalRequest)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  getGoogleConfig: () =>
    api.get<ApiResponse<{ client_id: string }>>('/auth/google/config'),

  googleLogin: (credential: string) =>
    api.post<ApiResponse<{ access_token: string; refresh_token: string; user: User }>>('/auth/google/login', {
      access_token: credential,
    }),

  refreshToken: (refresh: string) =>
    api.post<{ access: string }>('/auth/token/refresh', { refresh }),
}

// User API
export const userApi = {
  getMe: () => api.get<ApiResponse<User>>('/users/me'),

  getProfile: () => api.get<ApiResponse<UserProfile>>('/users/me/profile'),

  createProfile: (data: {
    nickname: string
    country: number
    learning_language_ids: number[]
  }) => api.post<ApiResponse<UserProfile>>('/users/me/profile/create', data),

  updateProfile: (data: {
    nickname?: string
    learning_language_ids?: number[]
  }) => api.patch<ApiResponse<UserProfile>>('/users/me/profile/update', data),
}

// Master Data API
export const masterApi = {
  getLanguages: () => api.get<ApiResponse<{ languages: Language[]; total_count: number }>>('/master/languages'),
  getCountries: () => api.get<ApiResponse<{ countries: Country[]; total_count: number }>>('/master/countries'),
}

// Gana Quiz API
export const quizApi = {
  startQuiz: (data: QuizStartRequest) =>
    api.post<ApiResponse<QuizStartResponse>>('/quiz/gana/start', data),

  submitAnswer: (quizId: number, data: QuizAnswerRequest) =>
    api.post<ApiResponse<QuizAnswerResponse>>(`/quiz/gana/${quizId}/answer`, data),

  getQuizDetail: (quizId: number) =>
    api.get<ApiResponse<GanaQuiz>>(`/quiz/gana/${quizId}`),

  getCurrentQuestion: (quizId: number) =>
    api.get<ApiResponse<{ question: CurrentQuestion; progress: QuizProgress }>>(`/quiz/gana/${quizId}/current`),

  getQuizHistory: (params?: {
    character_set?: string
    quiz_type?: string
    is_completed?: boolean
    limit?: number
  }) =>
    api.get<ApiResponse<{ quizzes: GanaQuizListItem[]; total_count: number }>>('/quiz/gana/history', { params }),

  getQuizStats: () =>
    api.get<ApiResponse<QuizStats>>('/quiz/gana/stats'),
}

// Word Quiz API
export const wordQuizApi = {
  startQuiz: (data: WordQuizStartRequest) =>
    api.post<ApiResponse<WordQuizStartResponse>>('/quiz/word/start', {
      learning_language: data.learning_language,
      quiz_type: data.quiz_type,
      question_count: parseInt(data.question_count),
    }),

  submitAnswer: (quizId: number, data: WordQuizAnswerRequest) =>
    api.post<ApiResponse<WordQuizAnswerResponse>>(`/quiz/word/${quizId}/answer`, data),

  getQuizDetail: (quizId: number) =>
    api.get<ApiResponse<WordQuiz>>(`/quiz/word/${quizId}`),

  getCurrentQuestion: (quizId: number) =>
    api.get<ApiResponse<{ question: CurrentQuestion; progress: QuizProgress }>>(`/quiz/word/${quizId}/current`),

  getQuizHistory: (params?: {
    learning_language?: string
    quiz_type?: string
    is_completed?: boolean
    limit?: number
  }) =>
    api.get<ApiResponse<{ quizzes: WordQuizListItem[]; total_count: number }>>('/quiz/word/history', { params }),

  getQuizStats: (params?: { learning_language?: string }) =>
    api.get<ApiResponse<WordQuizStats>>('/quiz/word/stats', { params }),

  resetStats: (languageCode: string) =>
    api.post<ApiResponse<{ deleted_quizzes: number }>>('/quiz/word/reset', { language_code: languageCode }),
}

// Policy API (이용약관, 개인정보처리방침)
export interface PolicyDocument {
  type: 'terms' | 'privacy'
  content: string
  content_html: string
  updated_at: string
}

export const policyApi = {
  getTermsOfService: () =>
    api.get<ApiResponse<PolicyDocument>>('/policies/terms'),

  getPrivacyPolicy: () =>
    api.get<ApiResponse<PolicyDocument>>('/policies/privacy'),

  updatePolicy: (type: 'terms' | 'privacy', content: string) =>
    api.put<ApiResponse<PolicyDocument>>(`/policies/${type}`, { content }),
}

// Word Browse API (학생용 단어 보기)
export const wordBrowseApi = {
  getWords: (params?: BrowseWordParams) =>
    api.get<ApiResponse<BrowseWordListResponse>>('/words/browse', { params }),

  getWordDetail: (wordId: number) =>
    api.get<ApiResponse<BrowseWord>>(`/words/browse/${wordId}`),

  getRandomWords: (params?: RandomWordParams) =>
    api.get<ApiResponse<{ words: BrowseWord[]; count: number }>>('/words/browse/random', { params }),
}

// Vocabulary API (단어장)
export const vocabularyApi = {
  // 단어장 목록 조회
  getVocabularies: () =>
    api.get<ApiResponse<{ vocabularies: Vocabulary[] }>>('/vocabularies'),

  // 단어장 생성
  createVocabulary: (data: VocabularyCreateRequest) =>
    api.post<ApiResponse<{ vocabulary: Vocabulary }>>('/vocabularies/create', data),

  // 단어장 상세 조회
  getVocabulary: (vocabularyId: number) =>
    api.get<ApiResponse<{ vocabulary: VocabularyDetail }>>(`/vocabularies/${vocabularyId}`),

  // 단어장 수정
  updateVocabulary: (vocabularyId: number, data: Partial<VocabularyCreateRequest>) =>
    api.patch<ApiResponse<{ vocabulary: Vocabulary }>>(`/vocabularies/${vocabularyId}/update`, data),

  // 단어장 삭제
  deleteVocabulary: (vocabularyId: number) =>
    api.delete<ApiResponse>(`/vocabularies/${vocabularyId}/delete`),

  // 단어장에 단어 추가
  addWord: (vocabularyId: number, data: AddWordToVocabularyRequest) =>
    api.post<ApiResponse>(`/vocabularies/${vocabularyId}/words/add`, data),

  // 단어장에서 단어 제거
  removeWord: (vocabularyId: number, wordId: number) =>
    api.delete<ApiResponse>(`/vocabularies/${vocabularyId}/words/${wordId}/remove`),

  // 특정 단어가 속한 내 단어장 목록
  getWordVocabularies: (wordId: number) =>
    api.get<ApiResponse<{ vocabularies: Vocabulary[] }>>(`/words/${wordId}/vocabularies`),
}

// Streak & Recommendation API
export const streakApi = {
  getStreakAndRecommendation: () =>
    api.get<ApiResponse<StreakRecommendationResponse>>('/lrs/user/streak-recommendation'),
}

export default api
