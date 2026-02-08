import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { wordQuizApi } from '../services/api'
import Layout from '../components/Layout'
import WordQuizSettingsModal from '../components/WordQuizSettingsModal'
import type { WordQuiz } from '../types'

export default function WordQuizResultPage() {
  const { quizId } = useParams<{ quizId: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()

  const [quiz, setQuiz] = useState<WordQuiz | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showQuizModal, setShowQuizModal] = useState(false)

  const loadQuiz = useCallback(async () => {
    if (!quizId) return

    try {
      setIsLoading(true)
      const response = await wordQuizApi.getQuizDetail(parseInt(quizId))

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
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600" />
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
    if (isOkay) return 'from-blue-500 to-indigo-500'
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
        <div className="card p-8 text-center mb-6">
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
                stroke="url(#wordScoreGradient)"
                strokeWidth="12"
                fill="none"
                strokeLinecap="round"
                strokeDasharray={`${(scorePercent / 100) * 440} 440`}
                className="transition-all duration-1000"
              />
              <defs>
                <linearGradient id="wordScoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor={isPerfect ? '#fbbf24' : isGood ? '#10b981' : isOkay ? '#3b82f6' : '#f43f5e'} />
                  <stop offset="100%" stopColor={isPerfect ? '#eab308' : isGood ? '#14b8a6' : isOkay ? '#6366f1' : '#ec4899'} />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={`text-4xl font-bold bg-gradient-to-r ${getScoreColor()} bg-clip-text text-transparent`}>
                {scorePercent}%
              </span>
            </div>
          </div>

          <h1 className="text-2xl font-bold text-slate-800 mb-2">
            {getScoreMessage()}
          </h1>
          <p className="text-slate-500 mb-6">
            {t('wordQuizResult.questionSummary', { total: quiz.total_questions, correct: quiz.correct_count })}
          </p>

          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="p-4 bg-emerald-50 rounded-xl">
              <p className="text-2xl font-bold text-emerald-600">{quiz.total_questions}</p>
              <p className="text-xs text-slate-500">{t('wordQuizResult.totalQuestions')}</p>
            </div>
            <div className="p-4 bg-blue-50 rounded-xl">
              <p className="text-2xl font-bold text-blue-600">{quiz.correct_count}</p>
              <p className="text-xs text-slate-500">{t('wordQuizResult.correct')}</p>
            </div>
            <div className="p-4 bg-rose-50 rounded-xl">
              <p className="text-2xl font-bold text-rose-600">{quiz.total_questions - quiz.correct_count}</p>
              <p className="text-xs text-slate-500">{t('wordQuizResult.incorrect')}</p>
            </div>
          </div>

          <div className="text-sm text-slate-500 space-y-1">
            <p>{quiz.learning_language_name} - {quiz.quiz_type_display}</p>
            <p>{t('wordQuizResult.completed')}: {quiz.completed_at ? new Date(quiz.completed_at).toLocaleString('ko-KR') : '-'}</p>
          </div>
        </div>

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
                    <span className="text-xl font-bold text-slate-700">{q.question}</span>
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

        <div className="flex gap-3">
          <Link to="/" className="flex-1 btn-secondary text-center">
            {t('common.goToMainShort')}
          </Link>
          <Link to="/word-quiz/dashboard" className="flex-1 btn-secondary text-center">
            {t('wordQuizResult.stats')}
          </Link>
          <button
            onClick={() => setShowQuizModal(true)}
            className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg hover:shadow-xl"
          >
            {t('wordQuizResult.retryQuiz')}
          </button>
        </div>
      </div>

      <WordQuizSettingsModal isOpen={showQuizModal} onClose={() => setShowQuizModal(false)} />
    </Layout>
  )
}
