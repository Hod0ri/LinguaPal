/**
 * Admin Dashboard Types
 *
 * Types for LRS admin dashboard API responses.
 */

// Dashboard Overview
export interface ActivityBreakdown {
  category: string
  subcategory: string
  completed: number
  passed: number
  failed: number
  questions: number
  correct: number
  accuracy: number
  quiz_type?: string
}

export interface CategoryStats {
  completed: number
  passed: number
  questions: number
  correct: number
  accuracy: number
}

export interface DashboardOverview {
  total_users: number
  active_users: number
  total_quizzes: number
  completed_quizzes: number
  total_questions: number
  total_correct: number
  overall_accuracy: number
  pass_rate: number
  quiz_type_breakdown: Record<string, CategoryStats>
  activity_breakdown?: ActivityBreakdown[]
  source: 'elasticsearch' | 'database'
}

// Dashboard Users
export interface UserStats {
  user_id: number
  username: string
  email: string
  total_quizzes: number
  passed_quizzes: number
  total_questions: number
  correct_answers: number
  accuracy: number
  last_activity: string | null
}

// Dashboard Trends
export interface TrendCategory {
  completed: number
}

export interface TrendData {
  date: string
  quizzes_completed: number
  quizzes_passed: number
  quizzes_failed: number
  questions_answered: number
  correct_answers: number
  accuracy: number
  unique_users: number
  by_category?: Record<string, TrendCategory>
}

export interface DashboardTrends {
  period: 'day' | 'week' | 'month'
  days: number
  trends: TrendData[]
  source: 'elasticsearch' | 'database'
}

// Dashboard Realtime
export interface Stats24h {
  quizzes_started: number
  quizzes_completed: number
  questions_answered: number
  unique_users: number
  passed: number
  failed: number
  by_category?: Record<string, { completed: number }>
}

export interface RecentActivity {
  id: string
  actor: {
    user_id: number
    mbox: string
    name: string
    display_name?: string  // 프로필 닉네임 (ES 소스)
  }
  verb: {
    id: string
    display: string
  }
  object: {
    type: string
    id: string
  }
  activity?: {
    display_name?: string  // 활동 표시명
    category?: string
    subcategory?: string
    quiz_type?: string
  }
  result?: {
    success?: boolean
    score_scaled?: number
  }
  timestamp: string
  actor_display_name?: string  // 프로필 닉네임 (DB 소스)
  activity_display_name?: string  // 활동 표시명 (DB 소스)
}

export interface DashboardRealtime {
  active_sessions: number
  recent_completions: RecentActivity[]
  recent_activity: RecentActivity[]
  stats_24h: Stats24h
  source: 'elasticsearch' | 'database'
}

// Activities
export interface ActivityStats {
  total_attempts: number
  total_completions: number
  total_passes: number
  total_fails: number
  avg_score: number
  unique_users: number
}

export interface Activity {
  id: string
  category: string
  subcategory: string
  quiz_type: string
  language_code?: string
  language_name?: string
  character_set?: string
  name: string
  type: string
  stats: ActivityStats
  created_at: string
  updated_at: string
}

export interface ActivityListResponse {
  total: number
  activities: Activity[]
  source: 'elasticsearch'
}

// Difficulty Analysis
export interface DifficultyItem {
  item_id: string
  item_name: string
  category?: string
  subcategory?: string
  total_attempts: number
  correct_count: number
  accuracy: number
}

export interface WrongAnswerPattern {
  answer: string
  count: number
}

export interface DifficultyAnalysis {
  hardest_items: DifficultyItem[]
  easiest_items: DifficultyItem[]
  wrong_answer_patterns: WrongAnswerPattern[]
  total_items_analyzed: number
  source: 'elasticsearch' | 'database'
}

// Engagement Metrics
export interface EngagementMetrics {
  period_days: number
  abandonment_rate: number
  quizzes_started: number
  quizzes_completed: number
  quizzes_abandoned: number
  avg_quiz_duration_minutes: number | null
  hourly_activity: Record<string, number>
  peak_hour: string | null
  source: 'elasticsearch' | 'database'
}

// Retention Metrics
export interface UserStreak {
  user_id: number
  username: string
  max_streak: number
  total_active_days: number
}

export interface RetentionMetrics {
  retention_7d: number
  retention_7d_users: {
    week1_active: number
    retained: number
  }
  retention_30d: number
  retention_30d_users: {
    month1_active: number
    retained: number
  }
  top_streaks: UserStreak[]
  source: 'elasticsearch' | 'database'
}

// Growth Metrics
export interface ImprovementTrend {
  week: string
  avg_score: number
  quiz_count: number
}

export interface MasteryStats {
  mastered: number
  learning: number
  struggling: number
  total_items: number
}

export interface GrowthMetrics {
  period_days: number
  improvement_trend: ImprovementTrend[]
  overall_avg_score: number
  mastery_stats: MasteryStats
  source: 'elasticsearch' | 'database'
}
