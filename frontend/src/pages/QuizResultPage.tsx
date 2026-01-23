import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { quizApi } from '../services/api'
import Header from '../components/Header'
import type { GanaQuiz } from '../types'

export default function QuizResultPage() {
  const { quizId } = useParams<{ quizId: string }>()
  const navigate = useNavigate()

  const [quiz, setQuiz] = useState<GanaQuiz | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showQuizModal, setShowQuizModal] = useState(false)

  const loadQuiz = useCallback(async () => {
    if (!quizId) return

    try {
      setIsLoading(true)
      const response = await quizApi.getQuizDetail(parseInt(quizId))

      if (response.data.success) {
        setQuiz(response.data.data)
      }
    } catch {
      setError('결과를 불러오는데 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }, [quizId])

  useEffect(() => {
    loadQuiz()
  }, [loadQuiz])

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

  if (error || !quiz) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30">
        <Header />
        <div className="flex flex-col items-center justify-center h-[calc(100vh-64px)] gap-4">
          <p className="text-slate-600">{error || '퀴즈를 찾을 수 없습니다.'}</p>
          <button onClick={() => navigate('/')} className="btn-primary">
            메인으로 돌아가기
          </button>
        </div>
      </div>
    )
  }

  const scorePercent = quiz.score_percentage
  const isPerfect = scorePercent === 100
  const isGood = scorePercent >= 80
  const isOkay = scorePercent >= 60

  const getScoreColor = () => {
    if (isPerfect) return 'from-amber-400 to-yellow-500'
    if (isGood) return 'from-emerald-500 to-teal-500'
    if (isOkay) return 'from-indigo-500 to-purple-500'
    return 'from-rose-500 to-pink-500'
  }

  const getScoreMessage = () => {
    if (isPerfect) return '완벽해요!'
    if (isGood) return '잘했어요!'
    if (isOkay) return '조금만 더 노력해요!'
    return '다시 도전해보세요!'
  }

  const incorrectQuestions = quiz.questions.filter((q) => !q.is_correct)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30">
      <Header />

      <main className="max-w-2xl mx-auto py-8 px-4">
        {/* Result Card */}
        <div className="card p-8 text-center mb-6">
          {/* Score Circle */}
          <div className="relative w-40 h-40 mx-auto mb-6">
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="80"
                cy="80"
                r="70"
                stroke="currentColor"
                strokeWidth="12"
                fill="none"
                className="text-slate-200"
              />
              <circle
                cx="80"
                cy="80"
                r="70"
                stroke="url(#scoreGradient)"
                strokeWidth="12"
                fill="none"
                strokeLinecap="round"
                strokeDasharray={`${(scorePercent / 100) * 440} 440`}
                className="transition-all duration-1000"
              />
              <defs>
                <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" className={`${getScoreColor().includes('amber') ? 'stop-amber-400' : getScoreColor().includes('emerald') ? 'stop-emerald-500' : getScoreColor().includes('indigo') ? 'stop-indigo-500' : 'stop-rose-500'}`} stopColor={isPerfect ? '#fbbf24' : isGood ? '#10b981' : isOkay ? '#6366f1' : '#f43f5e'} />
                  <stop offset="100%" className={`${getScoreColor().includes('yellow') ? 'stop-yellow-500' : getScoreColor().includes('teal') ? 'stop-teal-500' : getScoreColor().includes('purple') ? 'stop-purple-500' : 'stop-pink-500'}`} stopColor={isPerfect ? '#eab308' : isGood ? '#14b8a6' : isOkay ? '#a855f7' : '#ec4899'} />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={`text-4xl font-bold bg-gradient-to-r ${getScoreColor()} bg-clip-text text-transparent`}>
                {scorePercent}%
              </span>
            </div>
          </div>

          {/* Message */}
          <h1 className="text-2xl font-bold text-slate-800 mb-2">
            {getScoreMessage()}
          </h1>
          <p className="text-slate-500 mb-6">
            {quiz.total_questions}문제 중 {quiz.correct_count}문제 정답
          </p>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="p-4 bg-indigo-50 rounded-xl">
              <p className="text-2xl font-bold text-indigo-600">{quiz.total_questions}</p>
              <p className="text-xs text-slate-500">총 문제</p>
            </div>
            <div className="p-4 bg-emerald-50 rounded-xl">
              <p className="text-2xl font-bold text-emerald-600">{quiz.correct_count}</p>
              <p className="text-xs text-slate-500">정답</p>
            </div>
            <div className="p-4 bg-rose-50 rounded-xl">
              <p className="text-2xl font-bold text-rose-600">{quiz.total_questions - quiz.correct_count}</p>
              <p className="text-xs text-slate-500">오답</p>
            </div>
          </div>

          {/* Quiz Info */}
          <div className="text-sm text-slate-500 space-y-1">
            <p>{quiz.character_set_display} - {quiz.quiz_type_display}</p>
            <p>완료: {quiz.completed_at ? new Date(quiz.completed_at).toLocaleString('ko-KR') : '-'}</p>
          </div>
        </div>

        {/* Incorrect Questions */}
        {incorrectQuestions.length > 0 && (
          <div className="card p-6 mb-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">
              틀린 문제 ({incorrectQuestions.length}개)
            </h2>
            <div className="space-y-3">
              {incorrectQuestions.map((q) => (
                <div
                  key={q.id}
                  className="flex items-center justify-between p-3 bg-rose-50 rounded-xl"
                >
                  <div className="flex items-center gap-4">
                    <span className="text-2xl font-bold text-slate-700">{q.question}</span>
                    <span className="text-slate-400">→</span>
                    <div>
                      <p className="text-sm">
                        <span className="text-slate-500">내 답:</span>{' '}
                        <span className="text-rose-600 font-medium">{q.user_answer || '-'}</span>
                      </p>
                      <p className="text-sm">
                        <span className="text-slate-500">정답:</span>{' '}
                        <span className="text-emerald-600 font-medium">{q.correct_answer}</span>
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <Link to="/" className="flex-1 btn-secondary text-center">
            메인으로
          </Link>
          <Link to="/quiz/dashboard" className="flex-1 btn-secondary text-center">
            학습 통계
          </Link>
          <button
            onClick={() => setShowQuizModal(true)}
            className="flex-1 btn-primary"
          >
            다시 도전
          </button>
        </div>
      </main>

      {/* Quiz Settings Modal - Simple inline version */}
      {showQuizModal && (
        <QuizRetryModal
          characterSet={quiz.character_set}
          quizType={quiz.quiz_type}
          onClose={() => setShowQuizModal(false)}
        />
      )}
    </div>
  )
}

// Simple retry modal with same settings
function QuizRetryModal({
  characterSet,
  quizType,
  onClose,
}: {
  characterSet: string
  quizType: string
  onClose: () => void
}) {
  const navigate = useNavigate()
  const [questionCount, setQuestionCount] = useState<'10' | '25' | '0'>('10')
  const [isLoading, setIsLoading] = useState(false)

  const handleStart = async () => {
    setIsLoading(true)
    try {
      const response = await quizApi.startQuiz({
        character_set: characterSet as 'hiragana' | 'katakana' | 'all',
        quiz_type: quizType as 'gana_to_romaji' | 'romaji_to_gana_select' | 'romaji_to_gana_input',
        question_count: questionCount,
      })

      if (response.data.success) {
        navigate(`/quiz/${response.data.data.quiz.id}`)
      }
    } catch {
      // Handle error
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={onClose} />
        <div className="relative w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl">
          <h2 className="text-lg font-bold text-slate-800 mb-4">문제 수 선택</h2>
          <div className="grid grid-cols-3 gap-3 mb-6">
            {(['10', '25', '0'] as const).map((count) => (
              <button
                key={count}
                onClick={() => setQuestionCount(count)}
                className={`p-3 rounded-xl border-2 transition-all ${
                  questionCount === count
                    ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                    : 'border-slate-200 hover:border-slate-300 text-slate-600'
                }`}
              >
                {count === '0' ? '전체' : `${count}문제`}
              </button>
            ))}
          </div>
          <div className="flex gap-3">
            <button onClick={onClose} className="flex-1 btn-secondary">
              취소
            </button>
            <button onClick={handleStart} disabled={isLoading} className="flex-1 btn-primary">
              {isLoading ? '시작 중...' : '시작'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
