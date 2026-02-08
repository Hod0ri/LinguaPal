import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { quizApi } from '../services/api'
import Layout from '../components/Layout'
import type { GanaQuiz } from '../types'

export default function QuizResultPage() {
  const { quizId } = useParams<{ quizId: string }>()
  const navigate = useNavigate()
  const { t, i18n } = useTranslation()

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
      setError(t('wordQuizResult.loadFailed'))
    } finally {
      setIsLoading(false)
    }
  }, [quizId])

  useEffect(() => {
    loadQuiz()
  }, [loadQuiz])

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-[calc(100vh-64px)]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
        </div>
      </Layout>
    )
  }

  if (error || !quiz) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center h-[calc(100vh-64px)] gap-4">
          <p className="text-slate-600">{error || t('wordQuiz.notFound')}</p>
          <button onClick={() => navigate('/')} className="btn-primary">
            {t('common.goToMain')}
          </button>
        </div>
      </Layout>
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
    if (isPerfect) return t('wordQuizResult.perfect')
    if (isGood) return t('wordQuizResult.good')
    if (isOkay) return t('wordQuizResult.okay')
    return t('wordQuizResult.tryAgain')
  }

  const incorrectQuestions = quiz.questions.filter((q) => !q.is_correct)

  return (
    <Layout>
      <div className="max-w-2xl mx-auto py-8 px-4">
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
            {t('wordQuizResult.questionSummary', { total: quiz.total_questions, correct: quiz.correct_count })}
          </p>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="p-4 bg-indigo-50 rounded-xl">
              <p className="text-2xl font-bold text-indigo-600">{quiz.total_questions}</p>
              <p className="text-xs text-slate-500">{t('wordQuizResult.totalQuestions')}</p>
            </div>
            <div className="p-4 bg-emerald-50 rounded-xl">
              <p className="text-2xl font-bold text-emerald-600">{quiz.correct_count}</p>
              <p className="text-xs text-slate-500">{t('wordQuizResult.correct')}</p>
            </div>
            <div className="p-4 bg-rose-50 rounded-xl">
              <p className="text-2xl font-bold text-rose-600">{quiz.total_questions - quiz.correct_count}</p>
              <p className="text-xs text-slate-500">{t('wordQuizResult.incorrect')}</p>
            </div>
          </div>

          {/* Quiz Info */}
          <div className="text-sm text-slate-500 space-y-1">
            <p>{quiz.character_set_display} - {quiz.quiz_type_display}</p>
            <p>{t('wordQuizResult.completed')}: {quiz.completed_at ? new Date(quiz.completed_at).toLocaleString(i18n.language) : '-'}</p>
          </div>
        </div>

        {/* Incorrect Questions */}
        {incorrectQuestions.length > 0 && (
          <div className="card p-6 mb-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">
              {t('wordQuizResult.incorrectQuestions', { count: incorrectQuestions.length })}
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
                        <span className="text-slate-500">{t('wordQuiz.myAnswer')}:</span>{' '}
                        <span className="text-rose-600 font-medium">{q.user_answer || '-'}</span>
                      </p>
                      <p className="text-sm">
                        <span className="text-slate-500">{t('wordQuiz.answer')}:</span>{' '}
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
            {t('common.goToMainShort')}
          </Link>
          <Link to="/quiz/dashboard" className="flex-1 btn-secondary text-center">
            {t('wordQuizResult.stats')}
          </Link>
          <button
            onClick={() => setShowQuizModal(true)}
            className="flex-1 btn-primary"
          >
            {t('wordQuizResult.retryQuiz')}
          </button>
        </div>
      </div>

      {/* Quiz Settings Modal - Simple inline version */}
      {showQuizModal && (
        <QuizRetryModal
          characterSet={quiz.character_set}
          quizType={quiz.quiz_type}
          onClose={() => setShowQuizModal(false)}
        />
      )}
    </Layout>
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
  const { t } = useTranslation()
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
          <h2 className="text-lg font-bold text-slate-800 mb-4">{t('quizResult.questionCountSelect')}</h2>
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
                {t(`wordQuizSettings.counts.${count}`)}
              </button>
            ))}
          </div>
          <div className="flex gap-3">
            <button onClick={onClose} className="flex-1 btn-secondary">
              {t('common.cancel')}
            </button>
            <button onClick={handleStart} disabled={isLoading} className="flex-1 btn-primary">
              {isLoading ? t('common.starting') : t('common.start')}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
