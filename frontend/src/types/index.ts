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
