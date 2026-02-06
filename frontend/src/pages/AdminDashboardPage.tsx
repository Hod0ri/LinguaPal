import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { adminDashboardApi } from '../services/adminApi'
import type {
  DashboardOverview,
  UserStats,
  DashboardTrends,
  DashboardRealtime,
  TrendData,
  DifficultyAnalysis,
  EngagementMetrics,
  RetentionMetrics,
  GrowthMetrics,
} from '../types'

// Stats Card Component
function StatCard({
  title,
  value,
  subtitle,
  icon,
  color = 'indigo',
}: {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ReactNode
  color?: 'indigo' | 'emerald' | 'amber' | 'rose' | 'purple' | 'blue'
}) {
  const colorClasses = {
    indigo: 'bg-indigo-100 text-indigo-600',
    emerald: 'bg-emerald-100 text-emerald-600',
    amber: 'bg-amber-100 text-amber-600',
    rose: 'bg-rose-100 text-rose-600',
    purple: 'bg-purple-100 text-purple-600',
    blue: 'bg-blue-100 text-blue-600',
  }

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colorClasses[color]}`}>
          {icon}
        </div>
      </div>
      <p className="text-3xl font-bold text-slate-800">{value}</p>
      <p className="text-sm text-slate-500 mt-1">{title}</p>
      {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
    </div>
  )
}

// Mini Bar Chart Component
function MiniBarChart({ data, maxValue }: { data: { label: string; value: number; color: string }[]; maxValue: number }) {
  return (
    <div className="space-y-3">
      {data.map((item, index) => (
        <div key={index}>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-slate-600">{item.label}</span>
            <span className="font-medium text-slate-800">{item.value}</span>
          </div>
          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${item.color}`}
              style={{ width: `${maxValue > 0 ? (item.value / maxValue) * 100 : 0}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

// Trend Chart Component (Bar chart with grid)
function TrendChart({ trends, metric }: { trends: TrendData[]; metric: keyof TrendData }) {
  if (!trends.length) return <div className="text-center text-slate-400 py-8">데이터 없음</div>

  const getValue = (item: any, key: string) => {
    if (item[key] !== undefined && item[key] !== null) return Number(item[key]);
    const camelKey = key.replace(/_([a-z])/g, (g) => g[1].toUpperCase());
    if (item[camelKey] !== undefined && item[camelKey] !== null) return Number(item[camelKey]);
    return 0;
  }

  const displayTrends = trends.slice(-14)
  const values = displayTrends.map(t => getValue(t, metric as string))
  const maxVal = Math.max(...values, 1)
  const chartHeight = 140

  // Y축 눈금 계산
  const yTicks = [0, Math.round(maxVal / 2), maxVal]

  return (
    <div className="relative" style={{ height: `${chartHeight + 32}px` }}>
      {/* Y축 레이블 */}
      <div className="absolute left-0 top-0 bottom-8 w-8 flex flex-col justify-between text-right pr-2">
        {yTicks.slice().reverse().map((tick, i) => (
          <span key={i} className="text-[10px] text-slate-400">{tick}</span>
        ))}
      </div>

      {/* 차트 영역 */}
      <div className="ml-8 relative" style={{ height: `${chartHeight}px` }}>
        {/* 배경 그리드 라인 */}
        <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
          {yTicks.map((_, i) => (
            <div key={i} className="border-t border-slate-100 w-full" />
          ))}
        </div>

        {/* 바 차트 */}
        <div className="absolute inset-0 flex items-end gap-2 px-1">
          {displayTrends.map((trend, index) => {
            const value = getValue(trend, metric as string)
            const barHeight = Math.max((value / maxVal) * chartHeight, value > 0 ? 8 : 0)
            return (
              <div key={index} className="flex-1 flex flex-col items-center justify-end h-full group relative">
                {/* 툴팁 */}
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 pointer-events-none">
                  {trend.date}: {value}건
                </div>
                {/* 바 */}
                <div
                  className="w-full bg-gradient-to-t from-indigo-600 to-indigo-400 rounded-t transition-all duration-200 hover:from-indigo-700 hover:to-indigo-500 cursor-pointer shadow-sm"
                  style={{ height: `${barHeight}px`, minWidth: '12px' }}
                />
              </div>
            )
          })}
        </div>
      </div>

      {/* X축 레이블 */}
      <div className="ml-8 flex gap-2 px-1 mt-2">
        {displayTrends.map((trend, index) => (
          <div key={index} className="flex-1 text-center">
            <span className="text-[10px] text-slate-400">
              {trend.date.slice(5)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// Activity Feed Item
function ActivityItem({ activity }: { activity: DashboardRealtime['recent_activity'][0] }) {
  const verbColors: Record<string, string> = {
    initialized: 'bg-blue-100 text-blue-600',
    answered: 'bg-slate-100 text-slate-600',
    completed: 'bg-emerald-100 text-emerald-600',
    passed: 'bg-green-100 text-green-600',
    failed: 'bg-rose-100 text-rose-600',
    abandoned: 'bg-amber-100 text-amber-600',
    terminated: 'bg-slate-100 text-slate-500',
  }

  const verbLabels: Record<string, string> = {
    initialized: '시작',
    answered: '답변',
    completed: '완료',
    passed: '합격',
    failed: '불합격',
    abandoned: '중단',
    terminated: '종료',
  }

  const verbDisplay = activity.verb.display || activity.verb.id.split('/').pop() || 'unknown'
  const colorClass = verbColors[verbDisplay] || 'bg-slate-100 text-slate-600'
  const verbLabel = verbLabels[verbDisplay] || verbDisplay

  // 프로필 닉네임 우선 사용 (ES: actor.display_name, DB: actor_display_name)
  const actorName = activity.actor.display_name || activity.actor_display_name || activity.actor.name || 'Unknown'
  // 활동 표시명 (ES: activity.display_name, DB: activity_display_name)
  const activityName = activity.activity?.display_name || activity.activity_display_name || activity.object.id.split('/').slice(-3).join('/')

  return (
    <div className="flex items-center gap-3 py-3 border-b border-slate-100 last:border-0">
      <div className={`px-2 py-1 rounded text-xs font-medium ${colorClass}`}>
        {verbLabel}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-700 truncate">{actorName}</p>
        <p className="text-xs text-slate-400 truncate">{activityName}</p>
      </div>
      <div className="text-xs text-slate-400">
        {new Date(activity.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
      </div>
    </div>
  )
}

// User Ranking Item
function UserRankingItem({ user, rank }: { user: UserStats; rank: number }) {
  const medalColors = ['text-amber-500', 'text-slate-400', 'text-amber-700']

  return (
    <div className="flex items-center gap-4 py-3 border-b border-slate-100 last:border-0">
      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${rank <= 3 ? medalColors[rank - 1] + ' bg-slate-50' : 'text-slate-400 bg-slate-50'
        }`}>
        {rank}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-700 truncate">{user.username}</p>
        <p className="text-xs text-slate-400 truncate">{user.email}</p>
      </div>
      <div className="text-right">
        <p className="text-sm font-semibold text-indigo-600">{(user.accuracy ?? 0).toFixed(1)}%</p>
        <p className="text-xs text-slate-400">{user.total_quizzes ?? 0} 퀴즈</p>
      </div>
    </div>
  )
}

// Hourly Heatmap Component
function HourlyHeatmap({ data }: { data: Record<string, number> }) {
  const maxValue = Math.max(...Object.values(data), 1)
  const hours = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'))

  return (
    <div className="grid grid-cols-12 gap-1">
      {hours.map((hour) => {
        const value = data[hour] || 0
        const intensity = value / maxValue
        const bgColor = intensity > 0.8 ? 'bg-indigo-600' :
          intensity > 0.6 ? 'bg-indigo-500' :
            intensity > 0.4 ? 'bg-indigo-400' :
              intensity > 0.2 ? 'bg-indigo-300' :
                intensity > 0 ? 'bg-indigo-200' : 'bg-slate-100'
        return (
          <div key={hour} className="text-center">
            <div
              className={`w-full aspect-square rounded ${bgColor} transition-colors`}
              title={`${hour}시: ${value}건`}
            />
            <span className="text-[10px] text-slate-400">{hour}</span>
          </div>
        )
      })}
    </div>
  )
}

// Difficulty Item Row
function DifficultyItemRow({ item, type }: { item: { item_name: string; accuracy: number; total_attempts: number }; type: 'hard' | 'easy' }) {
  return (
    <div className="flex items-center gap-3 py-2 border-b border-slate-50 last:border-0">
      <div className={`w-2 h-2 rounded-full ${type === 'hard' ? 'bg-rose-500' : 'bg-emerald-500'}`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-700 truncate">{item.item_name}</p>
      </div>
      <div className="text-right">
        <p className={`text-sm font-semibold ${type === 'hard' ? 'text-rose-600' : 'text-emerald-600'}`}>
          {(item.accuracy ?? 0).toFixed(1)}%
        </p>
        <p className="text-xs text-slate-400">{item.total_attempts}회</p>
      </div>
    </div>
  )
}

// Streak Item Row
function StreakItemRow({ streak, rank }: { streak: { username: string; max_streak: number; total_active_days: number }; rank: number }) {
  return (
    <div className="flex items-center gap-3 py-2 border-b border-slate-50 last:border-0">
      <div className="w-6 h-6 rounded-full bg-amber-100 flex items-center justify-center text-xs font-bold text-amber-600">
        {rank}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-700 truncate">{streak.username}</p>
      </div>
      <div className="text-right">
        <p className="text-sm font-semibold text-amber-600">{streak.max_streak}일 연속</p>
        <p className="text-xs text-slate-400">총 {streak.total_active_days}일</p>
      </div>
    </div>
  )
}

// Mastery Donut Chart
function MasteryDonut({ stats }: { stats: { mastered: number; learning: number; struggling: number; total_items: number } }) {
  const total = stats.total_items || 1
  const masteredPct = (stats.mastered / total) * 100
  const learningPct = (stats.learning / total) * 100
  const strugglingPct = (stats.struggling / total) * 100

  return (
    <div className="flex items-center gap-6">
      <div className="relative w-24 h-24">
        <svg className="w-full h-full transform -rotate-90">
          <circle cx="48" cy="48" r="36" fill="none" stroke="#e2e8f0" strokeWidth="12" />
          <circle
            cx="48" cy="48" r="36" fill="none" stroke="#10b981" strokeWidth="12"
            strokeDasharray={`${masteredPct * 2.26} 226`}
          />
          <circle
            cx="48" cy="48" r="36" fill="none" stroke="#f59e0b" strokeWidth="12"
            strokeDasharray={`${learningPct * 2.26} 226`}
            strokeDashoffset={`${-masteredPct * 2.26}`}
          />
          <circle
            cx="48" cy="48" r="36" fill="none" stroke="#ef4444" strokeWidth="12"
            strokeDasharray={`${strugglingPct * 2.26} 226`}
            strokeDashoffset={`${-(masteredPct + learningPct) * 2.26}`}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-bold text-slate-700">{stats.total_items}</span>
        </div>
      </div>
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-500" />
          <span className="text-sm text-slate-600">마스터 ({stats.mastered})</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-amber-500" />
          <span className="text-sm text-slate-600">학습 중 ({stats.learning})</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-rose-500" />
          <span className="text-sm text-slate-600">어려움 ({stats.struggling})</span>
        </div>
      </div>
    </div>
  )
}

// Localization Helpers
// 언어 코드 정규화 (한글 이름 → 코드)
const normalizeLanguageCode = (lang: string): string => {
  const reverseMap: Record<string, string> = {
    '스페인어': 'es',
    '영어': 'en',
    '일본어': 'ja',
    '한국어': 'ko',
    '중국어': 'zh',
    '프랑스어': 'fr',
    '독일어': 'de',
    '히라가나': 'hiragana',
    '가타카나': 'katakana',
  }
  return reverseMap[lang] || lang
}

const getLocalizedSubcategory = (sub: string) => {
  const map: Record<string, string> = {
    'hiragana': '히라가나',
    'katakana': '가타카나',
    'ja': '일본어',
    'en': '영어',
    'ko': '한국어',
    'es': '스페인어',
    'zh': '중국어',
    'fr': '프랑스어',
    'de': '독일어',
    'all': '전체'
  }
  // 이미 한글이면 그대로 반환 (flashcard에서 직접 언어명/카테고리명 저장)
  return map[sub] || sub;
}

const getLocalizedQuizType = (type?: string) => {
  if (!type) return '-';
  const map: Record<string, string> = {
    'gana_to_romaji': '가나 -> 로마자',
    'romaji_to_gana_select': '로마자 -> 가나 (선택)',
    'romaji_to_gana_input': '로마자 -> 가나 (입력)',
    'word_to_native': '단어 -> 모국어 (선택)',
    'native_to_word_select': '모국어 -> 단어 (선택)',
    'native_to_word_input': '모국어 -> 단어 (입력)',
    'flashcard': '플래시카드'
  }
  // 이미 한글이면 그대로 반환 (flashcard에서 직접 '일반 학습' 저장)
  return map[type] || type;
}

const getLocalizedCategory = (cat: string) => {
  const map: Record<string, string> = {
    'gana': '가나',
    'word': '단어',
    'flashcard': '플래시카드'
  }
  return map[cat] || cat;
}

export default function AdminDashboardPage() {
  const { user } = useAuth()
  const [overview, setOverview] = useState<DashboardOverview | null>(null)
  const [users, setUsers] = useState<UserStats[]>([])
  const [trends, setTrends] = useState<DashboardTrends | null>(null)
  const [realtime, setRealtime] = useState<DashboardRealtime | null>(null)
  const [difficulty, setDifficulty] = useState<DifficultyAnalysis | null>(null)
  const [engagement, setEngagement] = useState<EngagementMetrics | null>(null)
  const [retention, setRetention] = useState<RetentionMetrics | null>(null)
  const [growth, setGrowth] = useState<GrowthMetrics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedPeriod, setSelectedPeriod] = useState<'day' | 'week' | 'month'>('day')
  const [activeTab, setActiveTab] = useState<'overview' | 'activity' | 'language' | 'students' | 'analytics'>('overview')
  const [refreshInterval, setRefreshInterval] = useState<number | null>(30000) // 30s default
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [studentSearch, setStudentSearch] = useState('')

  const loadData = async (isInitial = false) => {
    try {
      if (isInitial) {
        setIsLoading(true)
      } else {
        setIsRefreshing(true)
      }
      setError(null)

      const [
        overviewRes,
        usersRes,
        trendsRes,
        realtimeRes,
        difficultyRes,
        engagementRes,
        retentionRes,
        growthRes,
      ] = await Promise.all([
        adminDashboardApi.getOverview(),
        adminDashboardApi.getUsers({ limit: 10, sort_by: 'accuracy' }),
        adminDashboardApi.getTrends({ period: selectedPeriod, days: 30 }),
        adminDashboardApi.getRealtime(),
        adminDashboardApi.getDifficulty({ limit: 10 }),
        adminDashboardApi.getEngagement({ days: 30 }),
        adminDashboardApi.getRetention(),
        adminDashboardApi.getGrowth({ days: 30 }),
      ])

      setOverview(overviewRes.data)
      setUsers(usersRes.data)
      setTrends(trendsRes.data)
      setRealtime(realtimeRes.data)
      setDifficulty(difficultyRes.data)
      setEngagement(engagementRes.data)
      setRetention(retentionRes.data)
      setGrowth(growthRes.data)
      setLastUpdate(new Date())
    } catch (err) {
      console.error('Dashboard load error:', err)
      if (isInitial) {
        setError('대시보드 데이터를 불러오는데 실패했습니다.')
      }
    } finally {
      setIsLoading(false)
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    loadData(true)
  }, [selectedPeriod])

  // Auto-refresh all data based on selected interval
  useEffect(() => {
    if (!refreshInterval) return

    const interval = setInterval(() => {
      loadData(false)
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [refreshInterval, selectedPeriod])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-rose-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-slate-600">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            다시 시도
          </button>
        </div>
      </div>
    )
  }

  const categoryData = overview?.quiz_type_breakdown || {}
  const ganaStats = categoryData['gana'] || { completed: 0, passed: 0, questions: 0, correct: 0, accuracy: 0 }
  const wordStats = categoryData['word'] || { completed: 0, passed: 0, questions: 0, correct: 0, accuracy: 0 }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <Link to="/" className="flex items-center gap-3">
                <div className="w-9 h-9 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                  </svg>
                </div>
              </Link>
              <div className="h-6 w-px bg-slate-200" />
              <h1 className="text-lg font-semibold text-slate-800">관리자 대시보드</h1>
            </div>
            <div className="flex items-center gap-4">
              <Link
                to="/admin/words"
                className="text-sm text-slate-500 hover:text-indigo-600 flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                단어 관리
              </Link>
              <Link
                to="/admin/policies"
                className="text-sm text-slate-500 hover:text-indigo-600 flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                정책 관리
              </Link>
              <span className="text-sm text-slate-500">{user?.name}</span>
              <span className="px-2 py-1 bg-indigo-100 text-indigo-700 text-xs font-medium rounded">
                {user?.role}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Data Source Badge & Tab Navigation */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span className={`px-2 py-1 text-xs font-medium rounded ${overview?.source === 'elasticsearch'
              ? 'bg-green-100 text-green-700'
              : 'bg-amber-100 text-amber-700'
              }`}>
              {overview?.source === 'elasticsearch' ? 'Elasticsearch' : 'Database'}
            </span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">
                {lastUpdate.toLocaleTimeString('ko-KR')}
              </span>
              {isRefreshing && (
                <div className="w-3 h-3 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
              )}
            </div>
            {/* Manual Refresh Button */}
            <button
              onClick={() => loadData(false)}
              disabled={isRefreshing}
              className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors disabled:opacity-50"
              title="새로고침"
            >
              <svg className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            {/* Refresh Interval Selector */}
            <div className="flex items-center gap-1 ml-2 border-l border-slate-200 pl-3">
              <span className="text-xs text-slate-400 mr-1">자동:</span>
              {[
                { label: '5초', value: 5000 },
                { label: '15초', value: 15000 },
                { label: '30초', value: 30000 },
                { label: '1분', value: 60000 },
                { label: '없음', value: null },
              ].map((option) => (
                <button
                  key={option.label}
                  onClick={() => setRefreshInterval(option.value)}
                  className={`px-2 py-1 text-xs rounded transition-colors ${refreshInterval === option.value
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-500 hover:bg-slate-100'
                    }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${activeTab === 'overview'
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
                }`}
            >
              개요
            </button>
            <button
              onClick={() => setActiveTab('activity')}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${activeTab === 'activity'
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
                }`}
            >
              활동별
            </button>
            <button
              onClick={() => setActiveTab('language')}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${activeTab === 'language'
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
                }`}
            >
              언어별
            </button>
            <button
              onClick={() => setActiveTab('students')}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${activeTab === 'students'
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
                }`}
            >
              학생별
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${activeTab === 'analytics'
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
                }`}
            >
              상세 분석
            </button>
          </div>
        </div>

        {/* Overview Tab Content */}
        {activeTab === 'overview' && (
          <>
            {/* Overview Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
              <StatCard
                title="전체 사용자"
                value={overview?.total_users || 0}
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>}
                color="indigo"
              />
              <StatCard
                title="활성 사용자"
                value={overview?.active_users || 0}
                subtitle="최근 30일"
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
                color="blue"
              />
              <StatCard
                title="완료된 퀴즈"
                value={overview?.completed_quizzes || 0}
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
                color="emerald"
              />
              <StatCard
                title="답변한 문제"
                value={overview?.total_questions?.toLocaleString() || 0}
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
                color="purple"
              />
              <StatCard
                title="전체 정답률"
                value={`${overview?.overall_accuracy?.toFixed(1) || 0}%`}
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>}
                color="amber"
              />
              <StatCard
                title="합격률"
                value={`${overview?.pass_rate?.toFixed(1) || 0}%`}
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" /></svg>}
                color="rose"
              />
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column - Charts */}
              <div className="lg:col-span-2 space-y-6">
                {/* Trends Chart */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-lg font-semibold text-slate-800">학습 트렌드</h2>
                    <div className="flex gap-2">
                      {(['day', 'week', 'month'] as const).map((period) => (
                        <button
                          key={period}
                          onClick={() => setSelectedPeriod(period)}
                          className={`px-3 py-1 text-sm rounded-lg transition-colors ${selectedPeriod === period
                            ? 'bg-indigo-600 text-white'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                            }`}
                        >
                          {period === 'day' ? '일별' : period === 'week' ? '주별' : '월별'}
                        </button>
                      ))}
                    </div>
                  </div>
                  <TrendChart trends={trends?.trends || []} metric="quizzes_completed" />
                  <div className="flex items-center justify-center gap-6 mt-4 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-indigo-500 rounded" />
                      <span className="text-slate-600">완료된 퀴즈</span>
                    </div>
                  </div>
                </div>

                {/* Category Breakdown */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Gana Quiz Stats */}
                  <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center">
                        <span className="text-lg font-bold text-indigo-600">あ</span>
                      </div>
                      <h3 className="text-lg font-semibold text-slate-800">가나 퀴즈</h3>
                    </div>
                    <MiniBarChart
                      maxValue={Math.max(ganaStats.completed, ganaStats.passed, ganaStats.questions)}
                      data={[
                        { label: '완료', value: ganaStats.completed, color: 'bg-indigo-500' },
                        { label: '합격', value: ganaStats.passed, color: 'bg-emerald-500' },
                        { label: '문제 수', value: ganaStats.questions, color: 'bg-purple-500' },
                      ]}
                    />
                    <div className="mt-4 pt-4 border-t border-slate-100">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-500">정답률</span>
                        <span className="font-semibold text-indigo-600">{(ganaStats.accuracy ?? 0).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>

                  {/* Word Quiz Stats */}
                  <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                        <span className="text-lg font-bold text-purple-600">A</span>
                      </div>
                      <h3 className="text-lg font-semibold text-slate-800">단어 퀴즈</h3>
                    </div>
                    <MiniBarChart
                      maxValue={Math.max(wordStats.completed, wordStats.passed, wordStats.questions)}
                      data={[
                        { label: '완료', value: wordStats.completed, color: 'bg-purple-500' },
                        { label: '합격', value: wordStats.passed, color: 'bg-emerald-500' },
                        { label: '문제 수', value: wordStats.questions, color: 'bg-indigo-500' },
                      ]}
                    />
                    <div className="mt-4 pt-4 border-t border-slate-100">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-500">정답률</span>
                        <span className="font-semibold text-purple-600">{(wordStats.accuracy ?? 0).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Activity Breakdown */}
                {overview?.activity_breakdown && overview.activity_breakdown.length > 0 && (
                  <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                    <h3 className="text-lg font-semibold text-slate-800 mb-4">활동별 상세</h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-slate-100">
                            <th className="text-left py-2 px-3 text-slate-500 font-medium">카테고리</th>
                            <th className="text-left py-2 px-3 text-slate-500 font-medium">세부</th>
                            <th className="text-left py-2 px-3 text-slate-500 font-medium">학습 방식</th>
                            <th className="text-right py-2 px-3 text-slate-500 font-medium">완료</th>
                            <th className="text-right py-2 px-3 text-slate-500 font-medium">합격</th>
                            <th className="text-right py-2 px-3 text-slate-500 font-medium">정답률</th>
                          </tr>
                        </thead>
                        <tbody>
                          {overview.activity_breakdown.map((activity, index) => (
                            <tr key={index} className="border-b border-slate-50 hover:bg-slate-50">
                              <td className="py-2 px-3">
                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                  activity.category === 'gana'
                                    ? 'bg-indigo-100 text-indigo-700'
                                    : activity.category === 'flashcard'
                                    ? 'bg-amber-100 text-amber-700'
                                    : 'bg-purple-100 text-purple-700'
                                  }`}>
                                  {getLocalizedCategory(activity.category)}
                                </span>
                              </td>
                              <td className="py-2 px-3 text-slate-700">{getLocalizedSubcategory(activity.subcategory)}</td>
                              <td className="py-2 px-3 text-slate-700 text-xs">{getLocalizedQuizType(activity.quiz_type)}</td>
                              <td className="py-2 px-3 text-right text-slate-700">{activity.completed}</td>
                              <td className="py-2 px-3 text-right text-emerald-600">{activity.passed}</td>
                              <td className="py-2 px-3 text-right font-medium text-slate-800">{(activity.accuracy ?? 0).toFixed(1)}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>

              {/* Right Column - Realtime & Rankings */}
              <div className="space-y-6">
                {/* 24h Stats */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-slate-800">24시간 통계</h3>
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-slate-50 rounded-xl">
                      <p className="text-2xl font-bold text-indigo-600">{realtime?.stats_24h.quizzes_started || 0}</p>
                      <p className="text-xs text-slate-500">시작된 퀴즈</p>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-xl">
                      <p className="text-2xl font-bold text-emerald-600">{realtime?.stats_24h.quizzes_completed || 0}</p>
                      <p className="text-xs text-slate-500">완료된 퀴즈</p>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-xl">
                      <p className="text-2xl font-bold text-purple-600">{realtime?.stats_24h.unique_users || 0}</p>
                      <p className="text-xs text-slate-500">활동 사용자</p>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-xl">
                      <p className="text-2xl font-bold text-amber-600">{realtime?.active_sessions || 0}</p>
                      <p className="text-xs text-slate-500">활성 세션</p>
                    </div>
                  </div>
                </div>

                {/* User Rankings */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                  <h3 className="text-lg font-semibold text-slate-800 mb-4">사용자 랭킹</h3>
                  {users.length > 0 ? (
                    <div>
                      {users.slice(0, 5).map((user, index) => (
                        <UserRankingItem key={user.user_id} user={user} rank={index + 1} />
                      ))}
                    </div>
                  ) : (
                    <p className="text-center text-slate-400 py-4">데이터 없음</p>
                  )}
                </div>

                {/* Recent Activity */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-slate-800">최근 활동</h3>
                    <span className="text-xs text-slate-400">실시간</span>
                  </div>
                  {realtime?.recent_activity && realtime.recent_activity.length > 0 ? (
                    <div className="max-h-80 overflow-y-auto">
                      {realtime.recent_activity.slice(0, 10).map((activity, index) => (
                        <ActivityItem key={index} activity={activity} />
                      ))}
                    </div>
                  ) : (
                    <p className="text-center text-slate-400 py-4">최근 활동 없음</p>
                  )}
                </div>
              </div>
            </div>
          </>
        )}

        {/* Activity Tab Content - 활동별 */}
        {activeTab === 'activity' && (
          <div className="space-y-6">
            {/* Activity Overview Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                title="가나 퀴즈"
                value={ganaStats.completed}
                subtitle={`합격 ${ganaStats.passed}건`}
                icon={<span className="text-lg font-bold">あ</span>}
                color="indigo"
              />
              <StatCard
                title="단어 퀴즈"
                value={wordStats.completed}
                subtitle={`합격 ${wordStats.passed}건`}
                icon={<span className="text-lg font-bold">A</span>}
                color="purple"
              />
              <StatCard
                title="플래시카드"
                value={(categoryData['flashcard'] || { completed: 0 }).completed}
                subtitle={`완료 ${(categoryData['flashcard'] || { completed: 0 }).completed}건`}
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>}
                color="amber"
              />
              <StatCard
                title="전체 활동"
                value={overview?.completed_quizzes || 0}
                subtitle={`합격률 ${overview?.pass_rate?.toFixed(1) || 0}%`}
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>}
                color="emerald"
              />
            </div>

            {/* Activity Breakdown Table */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">활동별 상세 통계</h3>
              {overview?.activity_breakdown && overview.activity_breakdown.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-200 bg-slate-50">
                        <th className="text-left py-3 px-4 text-slate-600 font-semibold">카테고리</th>
                        <th className="text-left py-3 px-4 text-slate-600 font-semibold">세부</th>
                        <th className="text-left py-3 px-4 text-slate-600 font-semibold">학습 방식</th>
                        <th className="text-right py-3 px-4 text-slate-600 font-semibold">완료</th>
                        <th className="text-right py-3 px-4 text-slate-600 font-semibold">합격</th>
                        <th className="text-right py-3 px-4 text-slate-600 font-semibold">문제 수</th>
                        <th className="text-right py-3 px-4 text-slate-600 font-semibold">정답</th>
                        <th className="text-right py-3 px-4 text-slate-600 font-semibold">정답률</th>
                      </tr>
                    </thead>
                    <tbody>
                      {overview.activity_breakdown.map((activity, index) => (
                        <tr key={index} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              activity.category === 'gana'
                                ? 'bg-indigo-100 text-indigo-700'
                                : activity.category === 'flashcard'
                                ? 'bg-amber-100 text-amber-700'
                                : 'bg-purple-100 text-purple-700'
                              }`}>
                              {getLocalizedCategory(activity.category)}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-slate-700">{getLocalizedSubcategory(activity.subcategory)}</td>
                          <td className="py-3 px-4 text-slate-600 text-xs">{getLocalizedQuizType(activity.quiz_type)}</td>
                          <td className="py-3 px-4 text-right text-slate-700 font-medium">{activity.completed}</td>
                          <td className="py-3 px-4 text-right text-emerald-600 font-medium">{activity.passed}</td>
                          <td className="py-3 px-4 text-right text-slate-600">{activity.questions || '-'}</td>
                          <td className="py-3 px-4 text-right text-slate-600">{activity.correct || '-'}</td>
                          <td className="py-3 px-4 text-right">
                            <span className={`font-semibold ${
                              (activity.accuracy ?? 0) >= 80 ? 'text-emerald-600' :
                              (activity.accuracy ?? 0) >= 60 ? 'text-amber-600' : 'text-rose-600'
                            }`}>
                              {(activity.accuracy ?? 0).toFixed(1)}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-center text-slate-400 py-8">활동 데이터가 없습니다.</p>
              )}
            </div>

            {/* Activity Charts - Row 1 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Category Distribution Donut */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">카테고리별 분포</h3>
                {(() => {
                  const flashcardCompleted = (categoryData['flashcard'] || { completed: 0 }).completed
                  const total = ganaStats.completed + wordStats.completed + flashcardCompleted || 1
                  const ganaPct = (ganaStats.completed / total) * 100
                  const wordPct = (wordStats.completed / total) * 100
                  const flashcardPct = (flashcardCompleted / total) * 100

                  return (
                    <div className="flex items-center gap-6">
                      <div className="relative w-24 h-24">
                        <svg className="w-full h-full transform -rotate-90">
                          <circle cx="48" cy="48" r="36" fill="none" stroke="#e2e8f0" strokeWidth="12" />
                          <circle
                            cx="48" cy="48" r="36" fill="none" stroke="#6366f1" strokeWidth="12"
                            strokeDasharray={`${ganaPct * 2.26} 226`}
                          />
                          <circle
                            cx="48" cy="48" r="36" fill="none" stroke="#a855f7" strokeWidth="12"
                            strokeDasharray={`${wordPct * 2.26} 226`}
                            strokeDashoffset={`${-ganaPct * 2.26}`}
                          />
                          <circle
                            cx="48" cy="48" r="36" fill="none" stroke="#f59e0b" strokeWidth="12"
                            strokeDasharray={`${flashcardPct * 2.26} 226`}
                            strokeDashoffset={`${-(ganaPct + wordPct) * 2.26}`}
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-lg font-bold text-slate-700">{total}</span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-indigo-500" />
                          <span className="text-sm text-slate-600">가나 ({ganaStats.completed})</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-purple-500" />
                          <span className="text-sm text-slate-600">단어 ({wordStats.completed})</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-amber-500" />
                          <span className="text-sm text-slate-600">플래시카드 ({flashcardCompleted})</span>
                        </div>
                      </div>
                    </div>
                  )
                })()}
              </div>

              {/* Completion vs Pass Comparison */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">완료 vs 합격 비교</h3>
                <div className="space-y-4">
                  {[
                    { label: '가나 퀴즈', completed: ganaStats.completed, passed: ganaStats.passed, color: 'indigo' },
                    { label: '단어 퀴즈', completed: wordStats.completed, passed: wordStats.passed, color: 'purple' },
                    { label: '플래시카드', completed: (categoryData['flashcard'] || { completed: 0 }).completed, passed: (categoryData['flashcard'] || { passed: 0 }).passed, color: 'amber' },
                  ].map((item) => (
                    <div key={item.label} className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-600">{item.label}</span>
                        <span className="text-xs text-slate-400">{item.passed}/{item.completed}</span>
                      </div>
                      <div className="h-4 bg-slate-100 rounded-full overflow-hidden relative">
                        <div
                          className={`absolute h-full bg-${item.color}-200 rounded-full`}
                          style={{ width: `${Math.max(item.completed, 1) > 0 ? 100 : 0}%` }}
                        />
                        <div
                          className={`absolute h-full bg-${item.color}-500 rounded-full`}
                          style={{ width: `${item.completed > 0 ? (item.passed / item.completed) * 100 : 0}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-slate-100 text-xs">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-slate-200 rounded" />
                    <span className="text-slate-600">완료</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-slate-500 rounded" />
                    <span className="text-slate-600">합격</span>
                  </div>
                </div>
              </div>

              {/* Pass Rate by Category */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">카테고리별 합격률</h3>
                <MiniBarChart
                  maxValue={100}
                  data={[
                    { label: '가나 퀴즈', value: ganaStats.completed ? Math.round((ganaStats.passed / ganaStats.completed) * 100) : 0, color: 'bg-indigo-500' },
                    { label: '단어 퀴즈', value: wordStats.completed ? Math.round((wordStats.passed / wordStats.completed) * 100) : 0, color: 'bg-purple-500' },
                    { label: '전체', value: overview?.pass_rate || 0, color: 'bg-emerald-500' },
                  ]}
                />
              </div>
            </div>

            {/* Activity Charts - Row 2 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Accuracy by Category */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">카테고리별 정답률</h3>
                <div className="space-y-4">
                  {[
                    { label: '가나 퀴즈', accuracy: ganaStats.accuracy, icon: 'あ', color: 'indigo' },
                    { label: '단어 퀴즈', accuracy: wordStats.accuracy, icon: 'A', color: 'purple' },
                    { label: '플래시카드', accuracy: (categoryData['flashcard'] || { accuracy: 0 }).accuracy || 0, icon: '📚', color: 'amber' },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center gap-4">
                      <div className={`w-10 h-10 bg-${item.color}-100 rounded-xl flex items-center justify-center`}>
                        <span className={`text-${item.color}-600 font-bold`}>{item.icon}</span>
                      </div>
                      <div className="flex-1">
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-slate-600">{item.label}</span>
                          <span className={`font-semibold ${
                            (item.accuracy ?? 0) >= 80 ? 'text-emerald-600' :
                            (item.accuracy ?? 0) >= 60 ? 'text-amber-600' : 'text-rose-600'
                          }`}>{(item.accuracy ?? 0).toFixed(1)}%</span>
                        </div>
                        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              (item.accuracy ?? 0) >= 80 ? 'bg-emerald-500' :
                              (item.accuracy ?? 0) >= 60 ? 'bg-amber-500' : 'bg-rose-500'
                            }`}
                            style={{ width: `${item.accuracy ?? 0}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Questions Answered Stats */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">문제 풀이 현황</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-4 bg-indigo-50 rounded-xl">
                    <p className="text-2xl font-bold text-indigo-600">{ganaStats.questions.toLocaleString()}</p>
                    <p className="text-xs text-slate-500">가나 문제</p>
                    <p className="text-xs text-emerald-600 mt-1">정답 {ganaStats.correct.toLocaleString()}</p>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-xl">
                    <p className="text-2xl font-bold text-purple-600">{wordStats.questions.toLocaleString()}</p>
                    <p className="text-xs text-slate-500">단어 문제</p>
                    <p className="text-xs text-emerald-600 mt-1">정답 {wordStats.correct.toLocaleString()}</p>
                  </div>
                  <div className="col-span-2 text-center p-4 bg-emerald-50 rounded-xl">
                    <p className="text-3xl font-bold text-emerald-600">{(ganaStats.questions + wordStats.questions).toLocaleString()}</p>
                    <p className="text-sm text-slate-500">총 문제 수</p>
                    <p className="text-sm text-slate-600 mt-1">
                      전체 정답률: <span className="font-semibold text-emerald-600">{overview?.overall_accuracy?.toFixed(1) || 0}%</span>
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Language Tab Content - 언어별 */}
        {activeTab === 'language' && (
          <div className="space-y-6">
            {/* Language Stats - Extracted from activity breakdown */}
            {(() => {
              const languageStats: Record<string, { completed: number; passed: number; questions: number; correct: number; accuracy: number }> = {}

              overview?.activity_breakdown?.forEach(activity => {
                // 언어 코드 정규화 (한글 이름을 코드로 변환하여 중복 방지)
                const rawLang = activity.subcategory || 'unknown'
                const lang = normalizeLanguageCode(rawLang)

                if (!languageStats[lang]) {
                  languageStats[lang] = { completed: 0, passed: 0, questions: 0, correct: 0, accuracy: 0 }
                }
                languageStats[lang].completed += activity.completed || 0
                languageStats[lang].passed += activity.passed || 0
                languageStats[lang].questions += activity.questions || 0
                languageStats[lang].correct += activity.correct || 0
              })

              Object.keys(languageStats).forEach(lang => {
                const stats = languageStats[lang]
                stats.accuracy = stats.questions > 0 ? (stats.correct / stats.questions) * 100 : 0
              })

              const languages = Object.entries(languageStats)

              return (
                <>
                  {/* Language Overview Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {languages.slice(0, 4).map(([lang, stats]) => (
                      <StatCard
                        key={lang}
                        title={getLocalizedSubcategory(lang)}
                        value={stats.completed ?? 0}
                        subtitle={`정답률 ${(stats.accuracy ?? 0).toFixed(1)}%`}
                        icon={<span className="text-lg font-bold">{lang === 'hiragana' ? 'あ' : lang === 'katakana' ? 'ア' : lang.charAt(0).toUpperCase()}</span>}
                        color={lang === 'hiragana' ? 'indigo' : lang === 'katakana' ? 'purple' : 'blue'}
                      />
                    ))}
                  </div>

                  {/* Language Table */}
                  <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                    <h3 className="text-lg font-semibold text-slate-800 mb-4">언어별 상세 통계</h3>
                    {languages.length > 0 ? (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-slate-200 bg-slate-50">
                              <th className="text-left py-3 px-4 text-slate-600 font-semibold">언어/카테고리</th>
                              <th className="text-right py-3 px-4 text-slate-600 font-semibold">완료</th>
                              <th className="text-right py-3 px-4 text-slate-600 font-semibold">합격</th>
                              <th className="text-right py-3 px-4 text-slate-600 font-semibold">문제 수</th>
                              <th className="text-right py-3 px-4 text-slate-600 font-semibold">정답 수</th>
                              <th className="text-right py-3 px-4 text-slate-600 font-semibold">정답률</th>
                              <th className="text-right py-3 px-4 text-slate-600 font-semibold">합격률</th>
                            </tr>
                          </thead>
                          <tbody>
                            {languages.map(([lang, stats]) => (
                              <tr key={lang} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                                <td className="py-3 px-4">
                                  <div className="flex items-center gap-2">
                                    <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${
                                      lang === 'hiragana' ? 'bg-indigo-100 text-indigo-600' :
                                      lang === 'katakana' ? 'bg-purple-100 text-purple-600' :
                                      'bg-slate-100 text-slate-600'
                                    }`}>
                                      {lang === 'hiragana' ? 'あ' : lang === 'katakana' ? 'ア' : lang.charAt(0).toUpperCase()}
                                    </span>
                                    <span className="font-medium text-slate-700">{getLocalizedSubcategory(lang)}</span>
                                  </div>
                                </td>
                                <td className="py-3 px-4 text-right text-slate-700 font-medium">{stats.completed}</td>
                                <td className="py-3 px-4 text-right text-emerald-600 font-medium">{stats.passed}</td>
                                <td className="py-3 px-4 text-right text-slate-600">{stats.questions}</td>
                                <td className="py-3 px-4 text-right text-slate-600">{stats.correct ?? 0}</td>
                                <td className="py-3 px-4 text-right">
                                  <span className={`font-semibold ${
                                    (stats.accuracy ?? 0) >= 80 ? 'text-emerald-600' :
                                    (stats.accuracy ?? 0) >= 60 ? 'text-amber-600' : 'text-rose-600'
                                  }`}>
                                    {(stats.accuracy ?? 0).toFixed(1)}%
                                  </span>
                                </td>
                                <td className="py-3 px-4 text-right">
                                  <span className={`font-semibold ${
                                    stats.completed > 0 && (stats.passed / stats.completed) * 100 >= 80 ? 'text-emerald-600' :
                                    stats.completed > 0 && (stats.passed / stats.completed) * 100 >= 60 ? 'text-amber-600' : 'text-rose-600'
                                  }`}>
                                    {stats.completed > 0 ? ((stats.passed / stats.completed) * 100).toFixed(1) : 0}%
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="text-center text-slate-400 py-8">언어별 데이터가 없습니다.</p>
                    )}
                  </div>

                  {/* Language Charts - Row 1 */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Language Distribution Donut */}
                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                      <h3 className="text-lg font-semibold text-slate-800 mb-4">언어별 분포</h3>
                      {(() => {
                        const total = languages.reduce((sum, [, stats]) => sum + stats.completed, 0) || 1
                        const colors = ['#6366f1', '#a855f7', '#3b82f6', '#10b981', '#f59e0b', '#ef4444']
                        let offset = 0

                        return (
                          <div className="flex items-center gap-6">
                            <div className="relative w-24 h-24">
                              <svg className="w-full h-full transform -rotate-90">
                                <circle cx="48" cy="48" r="36" fill="none" stroke="#e2e8f0" strokeWidth="12" />
                                {languages.map(([lang, stats], i) => {
                                  const pct = (stats.completed / total) * 100
                                  const dashArray = `${pct * 2.26} 226`
                                  const dashOffset = `${-offset * 2.26}`
                                  offset += pct
                                  return (
                                    <circle
                                      key={lang}
                                      cx="48" cy="48" r="36" fill="none"
                                      stroke={colors[i % colors.length]}
                                      strokeWidth="12"
                                      strokeDasharray={dashArray}
                                      strokeDashoffset={dashOffset}
                                    />
                                  )
                                })}
                              </svg>
                              <div className="absolute inset-0 flex items-center justify-center">
                                <span className="text-lg font-bold text-slate-700">{total}</span>
                              </div>
                            </div>
                            <div className="space-y-1.5 max-h-32 overflow-y-auto">
                              {languages.map(([lang, stats], i) => (
                                <div key={lang} className="flex items-center gap-2">
                                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: colors[i % colors.length] }} />
                                  <span className="text-xs text-slate-600">{getLocalizedSubcategory(lang)} ({stats.completed})</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )
                      })()}
                    </div>

                    {/* Completion Distribution Bar */}
                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                      <h3 className="text-lg font-semibold text-slate-800 mb-4">언어별 완료 수</h3>
                      <MiniBarChart
                        maxValue={Math.max(...languages.map(([, stats]) => stats.completed), 1)}
                        data={languages.map(([lang, stats]) => ({
                          label: getLocalizedSubcategory(lang),
                          value: stats.completed,
                          color: lang === 'hiragana' ? 'bg-indigo-500' : lang === 'katakana' ? 'bg-purple-500' : 'bg-blue-500'
                        }))}
                      />
                    </div>

                    {/* Accuracy Distribution */}
                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                      <h3 className="text-lg font-semibold text-slate-800 mb-4">언어별 정답률</h3>
                      <MiniBarChart
                        maxValue={100}
                        data={languages.map(([lang, stats]) => ({
                          label: getLocalizedSubcategory(lang),
                          value: Math.round(stats.accuracy ?? 0),
                          color: (stats.accuracy ?? 0) >= 80 ? 'bg-emerald-500' : (stats.accuracy ?? 0) >= 60 ? 'bg-amber-500' : 'bg-rose-500'
                        }))}
                      />
                    </div>
                  </div>

                  {/* Language Charts - Row 2 */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Accuracy vs Pass Rate Comparison */}
                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                      <h3 className="text-lg font-semibold text-slate-800 mb-4">정답률 vs 합격률 비교</h3>
                      <div className="space-y-4">
                        {languages.map(([lang, stats]) => {
                          const passRate = stats.completed > 0 ? (stats.passed / stats.completed) * 100 : 0
                          return (
                            <div key={lang} className="space-y-1">
                              <div className="flex justify-between text-sm">
                                <span className="text-slate-600">{getLocalizedSubcategory(lang)}</span>
                                <div className="flex gap-3 text-xs">
                                  <span className="text-indigo-600">정답률 {(stats.accuracy ?? 0).toFixed(0)}%</span>
                                  <span className="text-emerald-600">합격률 {passRate.toFixed(0)}%</span>
                                </div>
                              </div>
                              <div className="flex gap-1 h-3">
                                <div className="flex-1 bg-slate-100 rounded-full overflow-hidden">
                                  <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${stats.accuracy ?? 0}%` }} />
                                </div>
                                <div className="flex-1 bg-slate-100 rounded-full overflow-hidden">
                                  <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${passRate}%` }} />
                                </div>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                      <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-slate-100 text-xs">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 bg-indigo-500 rounded" />
                          <span className="text-slate-600">정답률</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 bg-emerald-500 rounded" />
                          <span className="text-slate-600">합격률</span>
                        </div>
                      </div>
                    </div>

                    {/* Questions & Correct Answers Stats */}
                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                      <h3 className="text-lg font-semibold text-slate-800 mb-4">언어별 문제 풀이 현황</h3>
                      <div className="space-y-4">
                        {languages.map(([lang, stats]) => (
                          <div key={lang} className="flex items-center gap-4">
                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                              lang === 'hiragana' ? 'bg-indigo-100' :
                              lang === 'katakana' ? 'bg-purple-100' : 'bg-blue-100'
                            }`}>
                              <span className={`font-bold ${
                                lang === 'hiragana' ? 'text-indigo-600' :
                                lang === 'katakana' ? 'text-purple-600' : 'text-blue-600'
                              }`}>
                                {lang === 'hiragana' ? 'あ' : lang === 'katakana' ? 'ア' : lang.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <div className="flex-1">
                              <div className="flex justify-between text-sm mb-1">
                                <span className="text-slate-600">{getLocalizedSubcategory(lang)}</span>
                                <span className="text-slate-400 text-xs">{stats.correct}/{stats.questions} 정답</span>
                              </div>
                              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full ${
                                    (stats.accuracy ?? 0) >= 80 ? 'bg-emerald-500' :
                                    (stats.accuracy ?? 0) >= 60 ? 'bg-amber-500' : 'bg-rose-500'
                                  }`}
                                  style={{ width: `${stats.accuracy ?? 0}%` }}
                                />
                              </div>
                            </div>
                            <span className={`text-sm font-semibold ${
                              (stats.accuracy ?? 0) >= 80 ? 'text-emerald-600' :
                              (stats.accuracy ?? 0) >= 60 ? 'text-amber-600' : 'text-rose-600'
                            }`}>
                              {(stats.accuracy ?? 0).toFixed(0)}%
                            </span>
                          </div>
                        ))}
                      </div>
                      <div className="mt-4 pt-4 border-t border-slate-100 text-center">
                        <p className="text-sm text-slate-600">
                          총 문제: <span className="font-semibold">{languages.reduce((sum, [, stats]) => sum + stats.questions, 0).toLocaleString()}</span>
                          {' | '}
                          총 정답: <span className="font-semibold text-emerald-600">{languages.reduce((sum, [, stats]) => sum + stats.correct, 0).toLocaleString()}</span>
                        </p>
                      </div>
                    </div>
                  </div>
                </>
              )
            })()}
          </div>
        )}

        {/* Students Tab Content - 학생별 */}
        {activeTab === 'students' && (
          <div className="space-y-6">
            {/* Student Overview Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                title="전체 학생"
                value={overview?.total_users || 0}
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>}
                color="indigo"
              />
              <StatCard
                title="활성 학생"
                value={overview?.active_users || 0}
                subtitle="최근 30일"
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
                color="emerald"
              />
              <StatCard
                title="평균 정답률"
                value={`${overview?.overall_accuracy?.toFixed(1) || 0}%`}
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>}
                color="purple"
              />
              <StatCard
                title="평균 합격률"
                value={`${overview?.pass_rate?.toFixed(1) || 0}%`}
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" /></svg>}
                color="amber"
              />
            </div>

            {/* Student Search & Table */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-800">학생별 상세 통계</h3>
                {/* Search Input */}
                <div className="relative">
                  <input
                    type="text"
                    value={studentSearch}
                    onChange={(e) => setStudentSearch(e.target.value)}
                    placeholder="학생 검색 (이름, 이메일)"
                    className="pl-10 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 w-64"
                  />
                  <svg className="w-5 h-5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  {studentSearch && (
                    <button
                      onClick={() => setStudentSearch('')}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
              {(() => {
                const filteredUsers = users.filter(u =>
                  !studentSearch ||
                  u.username.toLowerCase().includes(studentSearch.toLowerCase()) ||
                  u.email.toLowerCase().includes(studentSearch.toLowerCase())
                )
                return filteredUsers.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-200 bg-slate-50">
                          <th className="text-left py-3 px-4 text-slate-600 font-semibold">순위</th>
                          <th className="text-left py-3 px-4 text-slate-600 font-semibold">학생</th>
                          <th className="text-right py-3 px-4 text-slate-600 font-semibold">총 퀴즈</th>
                          <th className="text-right py-3 px-4 text-slate-600 font-semibold">합격</th>
                          <th className="text-right py-3 px-4 text-slate-600 font-semibold">정답률</th>
                          <th className="text-right py-3 px-4 text-slate-600 font-semibold">최근 활동</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredUsers.map((userStats, index) => {
                          const rank = users.indexOf(userStats) + 1
                          return (
                            <tr key={userStats.user_id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                              <td className="py-3 px-4">
                                <span className={`w-8 h-8 inline-flex items-center justify-center rounded-full font-bold text-sm ${
                                  rank === 1 ? 'bg-amber-100 text-amber-600' :
                                  rank === 2 ? 'bg-slate-200 text-slate-600' :
                                  rank === 3 ? 'bg-orange-100 text-orange-600' :
                                  'bg-slate-100 text-slate-500'
                                }`}>
                                  {rank}
                                </span>
                              </td>
                              <td className="py-3 px-4">
                                <div>
                                  <p className="font-medium text-slate-700">{userStats.username}</p>
                                  <p className="text-xs text-slate-400">{userStats.email}</p>
                                </div>
                              </td>
                              <td className="py-3 px-4 text-right text-slate-700 font-medium">{userStats.total_quizzes ?? 0}</td>
                              <td className="py-3 px-4 text-right text-emerald-600 font-medium">{userStats.passed_quizzes ?? 0}</td>
                              <td className="py-3 px-4 text-right">
                                <span className={`font-semibold ${
                                  (userStats.accuracy ?? 0) >= 80 ? 'text-emerald-600' :
                                  (userStats.accuracy ?? 0) >= 60 ? 'text-amber-600' : 'text-rose-600'
                                }`}>
                                  {(userStats.accuracy ?? 0).toFixed(1)}%
                                </span>
                              </td>
                              <td className="py-3 px-4 text-right text-slate-500 text-xs">
                                {userStats.last_activity ? new Date(userStats.last_activity).toLocaleDateString('ko-KR') : '-'}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                    {studentSearch && (
                      <p className="text-xs text-slate-400 mt-2 text-center">
                        검색 결과: {filteredUsers.length}명 / 전체 {users.length}명
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-center text-slate-400 py-8">
                    {studentSearch ? `"${studentSearch}"에 대한 검색 결과가 없습니다.` : '학생 데이터가 없습니다.'}
                  </p>
                )
              })()}
            </div>

            {/* Student Charts - Row 1 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Performance Distribution Donut */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">성적 분포</h3>
                {(() => {
                  const excellent = users.filter(u => (u.accuracy ?? 0) >= 80).length
                  const good = users.filter(u => (u.accuracy ?? 0) >= 60 && (u.accuracy ?? 0) < 80).length
                  const needsWork = users.filter(u => (u.accuracy ?? 0) < 60).length
                  const total = users.length || 1
                  const excellentPct = (excellent / total) * 100
                  const goodPct = (good / total) * 100
                  const needsWorkPct = (needsWork / total) * 100

                  return (
                    <div className="flex items-center gap-6">
                      <div className="relative w-24 h-24">
                        <svg className="w-full h-full transform -rotate-90">
                          <circle cx="48" cy="48" r="36" fill="none" stroke="#e2e8f0" strokeWidth="12" />
                          <circle
                            cx="48" cy="48" r="36" fill="none" stroke="#10b981" strokeWidth="12"
                            strokeDasharray={`${excellentPct * 2.26} 226`}
                          />
                          <circle
                            cx="48" cy="48" r="36" fill="none" stroke="#f59e0b" strokeWidth="12"
                            strokeDasharray={`${goodPct * 2.26} 226`}
                            strokeDashoffset={`${-excellentPct * 2.26}`}
                          />
                          <circle
                            cx="48" cy="48" r="36" fill="none" stroke="#ef4444" strokeWidth="12"
                            strokeDasharray={`${needsWorkPct * 2.26} 226`}
                            strokeDashoffset={`${-(excellentPct + goodPct) * 2.26}`}
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-lg font-bold text-slate-700">{users.length}</span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-emerald-500" />
                          <span className="text-sm text-slate-600">우수 80%+ ({excellent}명)</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-amber-500" />
                          <span className="text-sm text-slate-600">양호 60-79% ({good}명)</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-rose-500" />
                          <span className="text-sm text-slate-600">노력필요 &lt;60% ({needsWork}명)</span>
                        </div>
                      </div>
                    </div>
                  )
                })()}
              </div>

              {/* Top Students by Quiz Count */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">퀴즈 수 Top 10</h3>
                <MiniBarChart
                  maxValue={Math.max(...users.slice(0, 10).map(u => u.total_quizzes), 1)}
                  data={users.slice(0, 10).map(userStats => ({
                    label: userStats.username,
                    value: userStats.total_quizzes,
                    color: 'bg-indigo-500'
                  }))}
                />
              </div>

              {/* Top Students by Accuracy */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">정답률 Top 10</h3>
                <MiniBarChart
                  maxValue={100}
                  data={[...users].sort((a, b) => (b.accuracy ?? 0) - (a.accuracy ?? 0)).slice(0, 10).map(userStats => ({
                    label: userStats.username,
                    value: Math.round(userStats.accuracy ?? 0),
                    color: (userStats.accuracy ?? 0) >= 80 ? 'bg-emerald-500' : (userStats.accuracy ?? 0) >= 60 ? 'bg-amber-500' : 'bg-rose-500'
                  }))}
                />
              </div>
            </div>

            {/* Student Charts - Row 2 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Pass Rate vs Accuracy Comparison */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">정답률 vs 합격률 비교</h3>
                <div className="space-y-3">
                  {[...users].sort((a, b) => b.total_quizzes - a.total_quizzes).slice(0, 5).map((userStats) => {
                    const passRate = userStats.total_quizzes > 0 ? (userStats.passed_quizzes / userStats.total_quizzes) * 100 : 0
                    return (
                      <div key={userStats.user_id} className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-600 truncate max-w-[120px]">{userStats.username}</span>
                          <div className="flex gap-4 text-xs">
                            <span className="text-indigo-600">정답률 {(userStats.accuracy ?? 0).toFixed(0)}%</span>
                            <span className="text-emerald-600">합격률 {(passRate ?? 0).toFixed(0)}%</span>
                          </div>
                        </div>
                        <div className="flex gap-1 h-3">
                          <div className="flex-1 bg-slate-100 rounded-full overflow-hidden">
                            <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${userStats.accuracy ?? 0}%` }} />
                          </div>
                          <div className="flex-1 bg-slate-100 rounded-full overflow-hidden">
                            <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${passRate ?? 0}%` }} />
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
                <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-slate-100 text-xs">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-indigo-500 rounded" />
                    <span className="text-slate-600">정답률</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-emerald-500 rounded" />
                    <span className="text-slate-600">합격률</span>
                  </div>
                </div>
              </div>

              {/* Activity Level Distribution */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">활동량 분포</h3>
                {(() => {
                  const veryActive = users.filter(u => u.total_quizzes >= 10).length
                  const active = users.filter(u => u.total_quizzes >= 5 && u.total_quizzes < 10).length
                  const moderate = users.filter(u => u.total_quizzes >= 1 && u.total_quizzes < 5).length
                  const inactive = users.filter(u => u.total_quizzes === 0).length
                  const maxVal = Math.max(veryActive, active, moderate, inactive, 1)

                  return (
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-slate-600">매우 활발 (10회+)</span>
                          <span className="font-medium text-indigo-600">{veryActive}명</span>
                        </div>
                        <div className="h-4 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-indigo-500 rounded-full transition-all" style={{ width: `${(veryActive / maxVal) * 100}%` }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-slate-600">활발 (5-9회)</span>
                          <span className="font-medium text-purple-600">{active}명</span>
                        </div>
                        <div className="h-4 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-purple-500 rounded-full transition-all" style={{ width: `${(active / maxVal) * 100}%` }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-slate-600">보통 (1-4회)</span>
                          <span className="font-medium text-amber-600">{moderate}명</span>
                        </div>
                        <div className="h-4 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-amber-500 rounded-full transition-all" style={{ width: `${(moderate / maxVal) * 100}%` }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-slate-600">미활동 (0회)</span>
                          <span className="font-medium text-slate-500">{inactive}명</span>
                        </div>
                        <div className="h-4 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-slate-400 rounded-full transition-all" style={{ width: `${(inactive / maxVal) * 100}%` }} />
                        </div>
                      </div>
                    </div>
                  )
                })()}
              </div>
            </div>

            {/* Recent Student Activity */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">최근 학생 활동</h3>
              {realtime?.recent_activity && realtime.recent_activity.length > 0 ? (
                <div className="max-h-80 overflow-y-auto">
                  {realtime.recent_activity.slice(0, 20).map((activity, index) => (
                    <ActivityItem key={index} activity={activity} />
                  ))}
                </div>
              ) : (
                <p className="text-center text-slate-400 py-4">최근 활동 없음</p>
              )}
            </div>
          </div>
        )}

        {/* Analytics Tab Content */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            {/* Analytics Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                title="이탈률"
                value={`${engagement?.abandonment_rate?.toFixed(1) || 0}%`}
                subtitle={`${engagement?.quizzes_abandoned || 0}건 중단`}
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>}
                color="rose"
              />
              <StatCard
                title="7일 리텐션"
                value={`${retention?.retention_7d?.toFixed(1) || 0}%`}
                subtitle={`${retention?.retention_7d_users?.retained || 0}명 유지`}
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>}
                color="emerald"
              />
              <StatCard
                title="평균 퀴즈 시간"
                value={engagement?.avg_quiz_duration_minutes ? `${engagement.avg_quiz_duration_minutes}분` : '-'}
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
                color="blue"
              />
              <StatCard
                title="전체 평균 점수"
                value={`${growth?.overall_avg_score?.toFixed(1) || 0}%`}
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>}
                color="purple"
              />
            </div>

            {/* Main Analytics Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Difficulty Analysis */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">난이도 분석</h3>
                <div className="grid grid-cols-2 gap-6">
                  {/* Hardest Items */}
                  <div>
                    <h4 className="text-sm font-medium text-rose-600 mb-3 flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                      </svg>
                      가장 어려운 항목
                    </h4>
                    {difficulty?.hardest_items?.slice(0, 5).map((item, index) => (
                      <DifficultyItemRow key={index} item={item} type="hard" />
                    ))}
                    {!difficulty?.hardest_items?.length && (
                      <p className="text-sm text-slate-400 text-center py-4">데이터 없음</p>
                    )}
                  </div>
                  {/* Easiest Items */}
                  <div>
                    <h4 className="text-sm font-medium text-emerald-600 mb-3 flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                      </svg>
                      가장 쉬운 항목
                    </h4>
                    {difficulty?.easiest_items?.slice(0, 5).map((item, index) => (
                      <DifficultyItemRow key={index} item={item} type="easy" />
                    ))}
                    {!difficulty?.easiest_items?.length && (
                      <p className="text-sm text-slate-400 text-center py-4">데이터 없음</p>
                    )}
                  </div>
                </div>
                {difficulty && (
                  <div className="mt-4 pt-4 border-t border-slate-100 text-center">
                    <span className="text-xs text-slate-400">총 {difficulty.total_items_analyzed}개 항목 분석</span>
                  </div>
                )}
              </div>

              {/* Engagement - Hourly Heatmap */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-800 mb-2">시간대별 활동</h3>
                <p className="text-xs text-slate-400 mb-4">
                  피크 시간: {engagement?.peak_hour ? `${engagement.peak_hour}시` : '-'}
                </p>
                {engagement?.hourly_activity && (
                  <HourlyHeatmap data={engagement.hourly_activity} />
                )}
                <div className="mt-4 pt-4 border-t border-slate-100">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-500">완료율</span>
                    <span className="font-semibold text-slate-700">
                      {engagement?.quizzes_started
                        ? ((engagement.quizzes_completed / engagement.quizzes_started) * 100).toFixed(1)
                        : 0}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Retention & Streaks */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">리텐션 & 학습 스트릭</h3>
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="text-center p-4 bg-emerald-50 rounded-xl">
                    <p className="text-2xl font-bold text-emerald-600">{retention?.retention_7d?.toFixed(1) || 0}%</p>
                    <p className="text-xs text-slate-500">7일 리텐션</p>
                    <p className="text-xs text-slate-400 mt-1">
                      {retention?.retention_7d_users?.week1_active || 0}명 중 {retention?.retention_7d_users?.retained || 0}명
                    </p>
                  </div>
                  <div className="text-center p-4 bg-blue-50 rounded-xl">
                    <p className="text-2xl font-bold text-blue-600">{retention?.retention_30d?.toFixed(1) || 0}%</p>
                    <p className="text-xs text-slate-500">30일 리텐션</p>
                    <p className="text-xs text-slate-400 mt-1">
                      {retention?.retention_30d_users?.month1_active || 0}명 중 {retention?.retention_30d_users?.retained || 0}명
                    </p>
                  </div>
                </div>
                <h4 className="text-sm font-medium text-amber-600 mb-3">학습 스트릭 Top 5</h4>
                {retention?.top_streaks?.slice(0, 5).map((streak, index) => (
                  <StreakItemRow key={index} streak={streak} rank={index + 1} />
                ))}
                {!retention?.top_streaks?.length && (
                  <p className="text-sm text-slate-400 text-center py-4">데이터 없음</p>
                )}
              </div>

              {/* Growth & Mastery */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">성장 & 숙달도</h3>
                {/* Mastery Stats */}
                {growth?.mastery_stats && (
                  <MasteryDonut stats={growth.mastery_stats} />
                )}
                {/* Improvement Trend */}
                {growth?.improvement_trend && growth.improvement_trend.length > 0 && (
                  <div className="mt-6 pt-4 border-t border-slate-100">
                    <h4 className="text-sm font-medium text-slate-600 mb-3">주간 성적 변화</h4>
                    <div className="flex items-end justify-between h-20 gap-2">
                      {growth.improvement_trend.slice(-8).map((week, index) => {
                        const height = week.avg_score || 0
                        return (
                          <div key={index} className="flex-1 flex flex-col items-center gap-1">
                            <div
                              className="w-full bg-purple-500 rounded-t transition-all"
                              style={{ height: `${Math.max(height, 4)}%` }}
                              title={`${week.week}: ${week.avg_score.toFixed(1)}%`}
                            />
                            <span className="text-[9px] text-slate-400 truncate w-full text-center">
                              {week.week.slice(5, 10)}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Wrong Answer Patterns */}
            {difficulty?.wrong_answer_patterns && difficulty.wrong_answer_patterns.length > 0 && (
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold text-slate-800 mb-4">자주 틀리는 오답 패턴</h3>
                <div className="flex flex-wrap gap-2">
                  {difficulty.wrong_answer_patterns.map((pattern, index) => (
                    <span
                      key={index}
                      className="px-3 py-1.5 bg-rose-50 text-rose-700 rounded-full text-sm"
                    >
                      "{pattern.answer}" ({pattern.count}회)
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
