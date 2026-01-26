import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { lrsGanaQuizApi } from '../services/lrsMiddleware'
import Header from '../components/Header'
import QuizSettingsModal from '../components/QuizSettingsModal'
import type { QuizStats, GanaQuizListItem } from '../types'

export default function QuizDashboardPage() {
  const [stats, setStats] = useState<QuizStats | null>(null)
  const [history, setHistory] = useState<GanaQuizListItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showQuizModal, setShowQuizModal] = useState(false)

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true)
        const [statsResponse, historyResponse] = await Promise.all([
          lrsGanaQuizApi.getQuizStats(),
          lrsGanaQuizApi.getQuizHistory({ limit: 10 }),
        ])

        if (statsResponse.data.success) {
          setStats(statsResponse.data.data)
        }
        if (historyResponse.data.success) {
          setHistory(historyResponse.data.data.quizzes)
        }
      } catch {
        // Handle error silently
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30">
        <Header />
        <div className="flex items-center justify-center h-[calc(100vh-64px)]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30">
      <Header />

      <main className="max-w-4xl mx-auto py-8 px-4">
        {/* Page Title */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">학습 대시보드</h1>
            <p className="text-slate-500">나의 학습 현황을 확인하세요</p>
          </div>
          <button onClick={() => setShowQuizModal(true)} className="btn-primary">
            새 퀴즈 시작
          </button>
        </div>

        {/* Overall Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="card p-5 text-center">
            <p className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              {stats?.completed_quizzes || 0}
            </p>
            <p className="text-sm text-slate-500 mt-1">완료한 퀴즈</p>
          </div>
          <div className="card p-5 text-center">
            <p className="text-3xl font-bold text-emerald-600">
              {stats?.total_questions_answered || 0}
            </p>
            <p className="text-sm text-slate-500 mt-1">푼 문제</p>
          </div>
          <div className="card p-5 text-center">
            <p className="text-3xl font-bold text-amber-600">
              {stats?.total_correct || 0}
            </p>
            <p className="text-sm text-slate-500 mt-1">맞은 문제</p>
          </div>
          <div className="card p-5 text-center">
            <p className="text-3xl font-bold text-rose-600">
              {stats?.overall_accuracy?.toFixed(1) || 0}%
            </p>
            <p className="text-sm text-slate-500 mt-1">전체 정답률</p>
          </div>
        </div>

        {/* Character Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Hiragana Stats */}
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center">
                <span className="text-lg font-bold text-indigo-600">あ</span>
              </div>
              <h2 className="text-lg font-semibold text-slate-800">히라가나</h2>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-500">시도한 문제</span>
                <span className="font-medium text-slate-700">{stats?.hiragana_stats.total_attempts || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-500">정답 수</span>
                <span className="font-medium text-emerald-600">{stats?.hiragana_stats.correct_count || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-500">정답률</span>
                <span className="font-medium text-indigo-600">{stats?.hiragana_stats.accuracy?.toFixed(1) || 0}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-500">학습한 문자</span>
                <span className="font-medium text-slate-700">{stats?.hiragana_stats.characters_practiced || 0}개</span>
              </div>
            </div>
          </div>

          {/* Katakana Stats */}
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                <span className="text-lg font-bold text-purple-600">ア</span>
              </div>
              <h2 className="text-lg font-semibold text-slate-800">가타카나</h2>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-500">시도한 문제</span>
                <span className="font-medium text-slate-700">{stats?.katakana_stats.total_attempts || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-500">정답 수</span>
                <span className="font-medium text-emerald-600">{stats?.katakana_stats.correct_count || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-500">정답률</span>
                <span className="font-medium text-purple-600">{stats?.katakana_stats.accuracy?.toFixed(1) || 0}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-500">학습한 문자</span>
                <span className="font-medium text-slate-700">{stats?.katakana_stats.characters_practiced || 0}개</span>
              </div>
            </div>
          </div>
        </div>

        {/* Weakest & Strongest Characters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Weakest Characters */}
          {stats?.weakest_characters && stats.weakest_characters.length > 0 && (
            <div className="card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-rose-100 rounded-xl flex items-center justify-center">
                  <svg className="w-5 h-5 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                  </svg>
                </div>
                <h2 className="text-lg font-semibold text-slate-800">취약한 문자</h2>
              </div>
              <div className="space-y-2">
                {stats.weakest_characters.map((char, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-rose-50 rounded-xl">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl font-bold text-slate-700">{char.word_text}</span>
                      <span className="text-sm text-slate-500">({char.word_pronunciation})</span>
                    </div>
                    <span className="text-sm font-medium text-rose-600">
                      {char.accuracy.toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Strongest Characters */}
          {stats?.strongest_characters && stats.strongest_characters.length > 0 && (
            <div className="card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
                  <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </div>
                <h2 className="text-lg font-semibold text-slate-800">강점 문자</h2>
              </div>
              <div className="space-y-2">
                {stats.strongest_characters.map((char, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-emerald-50 rounded-xl">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl font-bold text-slate-700">{char.word_text}</span>
                      <span className="text-sm text-slate-500">({char.word_pronunciation})</span>
                    </div>
                    <span className="text-sm font-medium text-emerald-600">
                      {char.accuracy.toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Recent Quiz History */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-slate-800">최근 퀴즈 기록</h2>
            </div>
          </div>

          {history.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-slate-500 mb-4">아직 퀴즈 기록이 없습니다</p>
              <button onClick={() => setShowQuizModal(true)} className="btn-primary">
                첫 퀴즈 시작하기
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {history.map((quiz) => (
                <Link
                  key={quiz.id}
                  to={quiz.is_completed ? `/quiz/result/${quiz.id}` : `/quiz/${quiz.id}`}
                  className="flex items-center justify-between p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors"
                >
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-slate-700">
                        {quiz.character_set_display}
                      </span>
                      <span className="text-slate-300">|</span>
                      <span className="text-sm text-slate-500">{quiz.quiz_type_display}</span>
                    </div>
                    <p className="text-xs text-slate-400">
                      {new Date(quiz.started_at).toLocaleString('ko-KR')}
                    </p>
                  </div>
                  <div className="text-right">
                    {quiz.is_completed ? (
                      <>
                        <p className={`text-lg font-bold ${
                          quiz.score_percentage >= 80
                            ? 'text-emerald-600'
                            : quiz.score_percentage >= 60
                            ? 'text-amber-600'
                            : 'text-rose-600'
                        }`}>
                          {quiz.score_percentage}%
                        </p>
                        <p className="text-xs text-slate-400">
                          {quiz.correct_count}/{quiz.total_questions}
                        </p>
                      </>
                    ) : (
                      <span className="px-3 py-1 bg-amber-100 text-amber-700 text-sm font-medium rounded-full">
                        진행 중
                      </span>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>

      <QuizSettingsModal isOpen={showQuizModal} onClose={() => setShowQuizModal(false)} />
    </div>
  )
}
