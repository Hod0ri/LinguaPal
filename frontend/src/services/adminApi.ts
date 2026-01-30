/**
 * Admin Dashboard API Service
 *
 * API calls for LRS admin dashboard endpoints.
 * These endpoints are only accessible to staff/admin users.
 */

import api from './api'
import type {
  DashboardOverview,
  UserStats,
  DashboardTrends,
  DashboardRealtime,
  ActivityListResponse,
  DifficultyAnalysis,
  EngagementMetrics,
  RetentionMetrics,
  GrowthMetrics,
} from '../types'

// Admin Dashboard API
export const adminDashboardApi = {
  /**
   * Get dashboard overview statistics
   */
  getOverview: () =>
    api.get<DashboardOverview>('/lrs/dashboard/overview'),

  /**
   * Get user statistics and rankings
   */
  getUsers: (params?: {
    sort_by?: 'quizzes' | 'accuracy' | 'recent'
    limit?: number
  }) =>
    api.get<UserStats[]>('/lrs/dashboard/users', { params }),

  /**
   * Get time-based learning trends
   */
  getTrends: (params?: {
    period?: 'day' | 'week' | 'month'
    days?: number
    category?: string
    subcategory?: string
  }) =>
    api.get<DashboardTrends>('/lrs/dashboard/trends', { params }),

  /**
   * Get real-time activity data
   */
  getRealtime: () =>
    api.get<DashboardRealtime>('/lrs/dashboard/realtime'),

  /**
   * Get activity list with statistics
   */
  getActivities: (params?: {
    category?: string
    subcategory?: string
    sort?: string
    order?: 'asc' | 'desc'
    limit?: number
  }) =>
    api.get<ActivityListResponse>('/lrs/dashboard/activities', { params }),

  /**
   * Get difficulty analysis (hardest/easiest items)
   */
  getDifficulty: (params?: {
    category?: string
    limit?: number
  }) =>
    api.get<DifficultyAnalysis>('/lrs/dashboard/difficulty', { params }),

  /**
   * Get engagement metrics (abandonment, duration, hourly activity)
   */
  getEngagement: (params?: {
    days?: number
  }) =>
    api.get<EngagementMetrics>('/lrs/dashboard/engagement', { params }),

  /**
   * Get retention metrics (7/30 day retention, streaks)
   */
  getRetention: () =>
    api.get<RetentionMetrics>('/lrs/dashboard/retention'),

  /**
   * Get growth metrics (improvement trends, mastery stats)
   */
  getGrowth: (params?: {
    user_id?: number
    days?: number
  }) =>
    api.get<GrowthMetrics>('/lrs/dashboard/growth', { params }),
}

export default adminDashboardApi
