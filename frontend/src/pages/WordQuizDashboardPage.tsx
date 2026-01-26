import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { lrsWordQuizApi } from '../services/lrsMiddleware'
import Header from '../components/Header'
import WordQuizSettingsModal from '../components/WordQuizSettingsModal'
import type { WordQuizStats, WordQuizListItem } from '../types'

export default function WordQuizDashboardPage() {
  const [stats, setStats] = useState<WordQuizStats | null>(null)
  const [history, setHistory] = useState<WordQuizListItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showQuizModal, setShowQuizModal] = useState(false)

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true)
        const [statsResponse, historyResponse] = await Promise.all([
          lrsWordQuizApi.getQuizStats(),
          lrsWordQuizApi.getQuizHistory({ limit: 10 }),
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
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-emerald-50/30">
        <Header />
        <div className="flex items-center justify-center h-[calc(100vh-64px)]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600" />
        </div>
      </div>
    )
  }

  const languageStats = stats?.language_stats ? Object.entries(stats.language_stats) : []

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-emerald-50/30">
      <Header />

      <main className="max-w-4xl mx-auto py-8 px-4">
        {/* Page Title */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">단어 학습 대시보드</h1>
            <p className="text-slate-500">나의 단어 학습 현황을 확인하세요</p>
          </div>
          <button onClick={() => setShowQuizModal(true)} className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 px-4 rounded-xl transition-all">
            새 퀴즈 시작
          </button>
        </div>

        {/* Overall Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="card p-5 text-center">
            <p className="text-3xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
              {stats?.completed_quizzes || 0}
            </p>
            <p className="text-sm text-slate-500 mt-1">완료한 퀴즈</p>
          </div>
          <div className="card p-5 text-center">
            <p className="text-3xl font-bold text-blue-600">
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

        {/* Language Stats */}
        {languageStats.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {languageStats.map(([langCode, langStats]) => (
              <div key={langCode} className="card p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
                    <span className="text-sm font-bold text-emerald-600">{langCode.toUpperCase()}</span>
                  </div>
                  <h2 className="text-lg font-semibold text-slate-800">{langStats.language_name}</h2>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-500">완료한 퀴즈</span>
                    <span className="font-medium text-slate-700">{langStats.quiz_count || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-500">시도한 문제</span>
                    <span className="font-medium text-slate-700">{langStats.total_attempts || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-500">정답 수</span>
                    <span className="font-medium text-emerald-600">{langStats.correct_count || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-500">정답률</span>
                    <span className="font-medium text-emerald-600">{langStats.accuracy?.toFixed(1) || 0}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Weakest & Strongest Words */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Weakest Words */}
          {stats?.weakest_words && stats.weakest_words.length > 0 && (
            <div className="card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-rose-100 rounded-xl flex items-center justify-center">
                  <svg className="w-5 h-5 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                  </svg>
                </div>
                <h2 className="text-lg font-semibold text-slate-800">취약한 단어</h2>
              </div>
              <div className="space-y-2">
                {stats.weakest_words.map((word, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-rose-50 rounded-xl">
                    <div className="flex items-center gap-3">
                      <span className="text-lg font-bold text-slate-700">{word.word_text}</span>
                      <span className="text-xs px-2 py-0.5 bg-rose-100 text-rose-600 rounded-full">
                        {word.word_language}
                      </span>
                    </div>
                    <span className="text-sm font-medium text-rose-600">
                      {word.accuracy.toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Strongest Words */}
          {stats?.strongest_words && stats.strongest_words.length > 0 && (
            <div className="card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
                  <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </div>
                <h2 className="text-lg font-semibold text-slate-800">강점 단어</h2>
              </div>
              <div className="space-y-2">
                {stats.strongest_words.map((word, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-emerald-50 rounded-xl">
                    <div className="flex items-center gap-3">
                      <span className="text-lg font-bold text-slate-700">{word.word_text}</span>
                      <span className="text-xs px-2 py-0.5 bg-emerald-100 text-emerald-600 rounded-full">
                        {word.word_language}
                      </span>
                    </div>
                    <span className="text-sm font-medium text-emerald-600">
                      {word.accuracy.toFixed(0)}%
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
              <button onClick={() => setShowQuizModal(true)} className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 px-4 rounded-xl transition-all">
                첫 퀴즈 시작하기
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {history.map((quiz) => (
                <Link
                  key={quiz.id}
                  to={quiz.is_completed ? `/word-quiz/result/${quiz.id}` : `/word-quiz/${quiz.id}`}
                  className="flex items-center justify-between p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors"
                >
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-slate-700">
                        {quiz.learning_language_name}
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

      <WordQuizSettingsModal isOpen={showQuizModal} onClose={() => setShowQuizModal(false)} />
    </div>
  )
}
