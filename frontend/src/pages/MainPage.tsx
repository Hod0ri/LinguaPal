import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import Layout from '../components/Layout'
import WordQuizSettingsModal from '../components/WordQuizSettingsModal'
import { quizApi, wordQuizApi } from '../services/api'
import type { QuizStats, WordQuizStats } from '../types'

interface CombinedStats {
  total_quizzes: number
  completed_quizzes: number
  total_questions_answered: number
  total_correct: number
  overall_accuracy: number
}

export default function MainPage() {
  const { profile } = useAuth()
  const [showWordQuizModal, setShowWordQuizModal] = useState(false)
  const [combinedStats, setCombinedStats] = useState<CombinedStats | null>(null)

  // 일본어 학습 중인지 확인
  const isLearningJapanese = profile?.learning_languages.some(
    (lang) => lang.code === 'ja'
  ) ?? false

  // 학습 중인 언어 코드 목록
  const learningLanguageCodes = profile?.learning_languages.map(l => l.code) ?? []

  useEffect(() => {
    const loadStats = async () => {
      try {
        let gana: QuizStats | null = null
        let word: WordQuizStats | null = null

        // 일본어 학습 중인 경우에만 가나 퀴즈 통계 로드
        if (isLearningJapanese) {
          const [ganaResponse, wordResponse] = await Promise.all([
            quizApi.getQuizStats(),
            wordQuizApi.getQuizStats(),
          ])
          if (ganaResponse.data.success) {
            gana = ganaResponse.data.data
          }
          if (wordResponse.data.success) {
            word = wordResponse.data.data
          }
        } else {
          const wordResponse = await wordQuizApi.getQuizStats()
          if (wordResponse.data.success) {
            word = wordResponse.data.data
          }
        }

        // 학습 중인 언어만 필터링하여 단어 퀴즈 통계 계산
        const filteredWordStats = {
          total_quizzes: 0,
          completed_quizzes: 0,
          total_questions_answered: 0,
          total_correct: 0,
        }

        if (word?.language_stats) {
          Object.entries(word.language_stats).forEach(([langCode, langStats]) => {
            if (learningLanguageCodes.includes(langCode)) {
              filteredWordStats.total_quizzes += langStats.quiz_count || 0
              filteredWordStats.total_questions_answered += langStats.total_attempts || 0
              filteredWordStats.total_correct += langStats.correct_count || 0
            }
          })
          filteredWordStats.completed_quizzes = filteredWordStats.total_quizzes
        }

        // Combine stats (가나 퀴즈 + 필터링된 단어 퀴즈)
        const totalQuizzes = (gana?.total_quizzes || 0) + filteredWordStats.total_quizzes
        const completedQuizzes = (gana?.completed_quizzes || 0) + filteredWordStats.completed_quizzes
        const totalQuestionsAnswered = (gana?.total_questions_answered || 0) + filteredWordStats.total_questions_answered
        const totalCorrect = (gana?.total_correct || 0) + filteredWordStats.total_correct
        const overallAccuracy = totalQuestionsAnswered > 0
          ? (totalCorrect / totalQuestionsAnswered) * 100
          : 0

        setCombinedStats({
          total_quizzes: totalQuizzes,
          completed_quizzes: completedQuizzes,
          total_questions_answered: totalQuestionsAnswered,
          total_correct: totalCorrect,
          overall_accuracy: overallAccuracy,
        })
      } catch {
        // Handle error silently
      }
    }
    loadStats()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLearningJapanese, JSON.stringify(learningLanguageCodes)])

  return (
    <Layout>
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">👋</span>
            <h1 className="text-3xl font-bold text-slate-800">
              안녕하세요, <span className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">{profile?.nickname}</span>님!
            </h1>
          </div>
          <p className="text-slate-500">
            오늘도 새로운 언어를 배워볼까요?
          </p>
        </div>

        {/* Main Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {/* Learning Languages Card */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center">
                  <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                  </svg>
                </div>
                <h2 className="text-lg font-semibold text-slate-800">학습 중인 언어</h2>
              </div>
              <Link to="/profile" className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">
                수정
              </Link>
            </div>
            <div className="flex flex-wrap gap-2">
              {profile?.learning_languages.map((lang) => (
                <span
                  key={lang.id}
                  className="px-4 py-2 bg-gradient-to-r from-indigo-50 to-purple-50 text-indigo-700 rounded-xl text-sm font-medium border border-indigo-100"
                >
                  {lang.name_ko}
                </span>
              ))}
            </div>
          </div>

          {/* Quiz Card - 단어 퀴즈 (일본어의 경우 가나 포함) */}
          <div className="card p-6 group hover:border-emerald-200 transition-colors">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-slate-800">퀴즈</h2>
            </div>
            <p className="text-slate-500 text-sm mb-3">
              {isLearningJapanese ? '단어와 가나를 연습하세요.' : '외국어 단어를 연습하세요.'}
            </p>
            <div className="text-xs text-slate-400 mb-4">
              {combinedStats && combinedStats.completed_quizzes > 0 ? (
                <span>완료: {combinedStats.completed_quizzes}회 | 정답률: {combinedStats.overall_accuracy?.toFixed(0) || 0}%</span>
              ) : (
                <span>아직 기록이 없습니다</span>
              )}
            </div>
            <button onClick={() => setShowWordQuizModal(true)} className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 px-4 rounded-xl transition-all">
              퀴즈 풀기
            </button>
          </div>

          {/* Flashcard Card */}
          <div className="card p-6 group hover:border-purple-200 transition-colors">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-slate-800">플래시카드</h2>
            </div>
            <p className="text-slate-500 text-sm mb-3">
              카드를 넘기며 단어를 학습하세요.
            </p>
            <div className="text-xs text-slate-400 mb-4">
              자신의 페이스로 학습하기
            </div>
            <Link to="/flashcard" className="block w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2 px-4 rounded-xl transition-all text-center">
              학습하기
            </Link>
          </div>
        </div>

        {/* Stats Section */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-slate-800">전체 학습 통계</h2>
            </div>
            <Link to="/word-quiz/dashboard" className="text-sm text-emerald-600 hover:text-emerald-700 font-medium">
              상세 보기
            </Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-5 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl border border-indigo-100/50">
              <p className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                {combinedStats?.total_questions_answered || 0}
              </p>
              <p className="text-sm text-slate-500 mt-1">푼 문제</p>
            </div>
            <div className="text-center p-5 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl border border-emerald-100/50">
              <p className="text-4xl font-bold text-emerald-600">{combinedStats?.completed_quizzes || 0}</p>
              <p className="text-sm text-slate-500 mt-1">완료한 퀴즈</p>
            </div>
            <div className="text-center p-5 bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl border border-amber-100/50">
              <p className="text-4xl font-bold text-amber-600">{combinedStats?.total_correct || 0}</p>
              <p className="text-sm text-slate-500 mt-1">맞은 문제</p>
            </div>
            <div className="text-center p-5 bg-gradient-to-br from-rose-50 to-pink-50 rounded-2xl border border-rose-100/50">
              <p className="text-4xl font-bold text-rose-600">{combinedStats?.overall_accuracy?.toFixed(0) || 0}%</p>
              <p className="text-sm text-slate-500 mt-1">정답률</p>
            </div>
          </div>
        </div>
      </div>

      <WordQuizSettingsModal isOpen={showWordQuizModal} onClose={() => setShowWordQuizModal(false)} />
    </Layout>
  )
}
