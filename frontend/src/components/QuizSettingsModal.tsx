import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { lrsGanaQuizApi } from '../services/lrsMiddleware'
import type { GanaCharacterSet, GanaQuizType, GanaQuizQuestionCount } from '../types'

interface QuizSettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

const CHARACTER_SETS: { value: GanaCharacterSet }[] = [
  { value: 'hiragana' },
  { value: 'katakana' },
  { value: 'all' },
]

const QUIZ_TYPES: { value: GanaQuizType }[] = [
  { value: 'gana_to_romaji' },
  { value: 'romaji_to_gana_select' },
  { value: 'romaji_to_gana_input' },
]

const QUESTION_COUNTS: { value: GanaQuizQuestionCount }[] = [
  { value: '10' },
  { value: '25' },
  { value: '0' },
]

export default function QuizSettingsModal({ isOpen, onClose }: QuizSettingsModalProps) {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [characterSet, setCharacterSet] = useState<GanaCharacterSet>('hiragana')
  const [quizType, setQuizType] = useState<GanaQuizType>('gana_to_romaji')
  const [questionCount, setQuestionCount] = useState<GanaQuizQuestionCount>('10')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleStartQuiz = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await lrsGanaQuizApi.startQuiz({
        character_set: characterSet,
        quiz_type: quizType,
        question_count: questionCount,
      })

      if (response.data.success) {
        const quizId = response.data.data.quiz.id
        onClose()
        navigate(`/quiz/${quizId}`)
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : t('quizSettings.startFailed')
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm transition-opacity"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative w-full max-w-lg transform rounded-2xl bg-white p-6 shadow-xl transition-all">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-slate-800">{t('quizSettings.title')}</h2>
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
              {error}
            </div>
          )}

          {/* Character Set Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 mb-3">{t('quizSettings.characterSet')}</label>
            <div className="grid grid-cols-3 gap-3">
              {CHARACTER_SETS.map((set) => (
                <button
                  key={set.value}
                  onClick={() => setCharacterSet(set.value)}
                  className={`p-3 rounded-xl border-2 transition-all text-center ${
                    characterSet === set.value
                      ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                      : 'border-slate-200 hover:border-slate-300 text-slate-600'
                  }`}
                >
                  <div className="font-medium text-sm">{t(`quizSettings.characterSets.${set.value}`)}</div>
                  <div className="text-xs mt-1 opacity-70">{t(`quizSettings.characterSets.${set.value}_desc`)}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Quiz Type Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 mb-3">{t('quizSettings.quizType')}</label>
            <div className="space-y-2">
              {QUIZ_TYPES.map((type) => (
                <button
                  key={type.value}
                  onClick={() => setQuizType(type.value)}
                  className={`w-full p-3 rounded-xl border-2 transition-all text-left ${
                    quizType === type.value
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className={`font-medium text-sm ${quizType === type.value ? 'text-indigo-700' : 'text-slate-700'}`}>
                    {t(`quizSettings.types.${type.value}`)}
                  </div>
                  <div className={`text-xs mt-1 ${quizType === type.value ? 'text-indigo-600' : 'text-slate-500'}`}>
                    {t(`quizSettings.types.${type.value}_desc`)}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Question Count Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 mb-3">{t('quizSettings.questionCount')}</label>
            <div className="grid grid-cols-3 gap-3">
              {QUESTION_COUNTS.map((count) => (
                <button
                  key={count.value}
                  onClick={() => setQuestionCount(count.value)}
                  className={`p-3 rounded-xl border-2 transition-all text-center ${
                    questionCount === count.value
                      ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                      : 'border-slate-200 hover:border-slate-300 text-slate-600'
                  }`}
                >
                  <div className="font-medium">{t(`quizSettings.counts.${count.value}`)}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 btn-secondary"
              disabled={isLoading}
            >
              {t('common.cancel')}
            </button>
            <button
              onClick={handleStartQuiz}
              className="flex-1 btn-primary"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  {t('common.starting')}
                </span>
              ) : (
                t('quizSettings.startQuiz')
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
