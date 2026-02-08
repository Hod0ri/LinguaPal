import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { userApi, vocabularyApi } from '../services/api'
import { lrsWordQuizApi } from '../services/lrsMiddleware'
import type { WordQuizType, WordQuizQuestionCount, Language } from '../types'
import type { Vocabulary } from '../types/vocabulary'

interface WordQuizSettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

const QUIZ_TYPES: { value: WordQuizType; label: string; description: string }[] = [
  { value: 'word_to_native', label: '단어 -> 모국어', description: '학습 언어 단어를 보고 모국어 뜻 입력' },
  { value: 'native_to_word_select', label: '모국어 -> 단어 (선택)', description: '모국어 뜻을 보고 단어 선택' },
  { value: 'native_to_word_input', label: '모국어 -> 단어 (입력)', description: '모국어 뜻을 보고 단어 입력' },
  { value: 'example_fill_in_blank', label: '예문 빈칸 채우기 (3지선다)', description: '예문과 번역을 보고 빈칸에 들어갈 단어 선택' },
  { value: 'mixed', label: '🎲 혼합 문제 (추천)', description: '모든 유형의 문제가 랜덤하게 출제됩니다' },
]

const QUESTION_COUNTS: { value: WordQuizQuestionCount; label: string }[] = [
  { value: '10', label: '10문제' },
  { value: '25', label: '25문제' },
  { value: '0', label: '전체' },
]

export default function WordQuizSettingsModal({ isOpen, onClose }: WordQuizSettingsModalProps) {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [learningLanguages, setLearningLanguages] = useState<Language[]>([])
  const [selectedLanguage, setSelectedLanguage] = useState<string>('')
  const [quizType, setQuizType] = useState<WordQuizType>('word_to_native')
  const [questionCount, setQuestionCount] = useState<WordQuizQuestionCount>('10')
  const [vocabularies, setVocabularies] = useState<Vocabulary[]>([])
  const [selectedVocabularyId, setSelectedVocabularyId] = useState<number | null>(null)
  const [useVocabulary, setUseVocabulary] = useState(false)
  const [learnedWordsOnly, setLearnedWordsOnly] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingProfile, setIsLoadingProfile] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      loadUserProfile()
      loadVocabularies()
    }
  }, [isOpen])

  // Reset vocabulary selection when language changes
  useEffect(() => {
    setSelectedVocabularyId(null)
    setUseVocabulary(false)
  }, [selectedLanguage])

  const loadUserProfile = async () => {
    setIsLoadingProfile(true)
    try {
      const response = await userApi.getProfile()
      if (response.data.success && response.data.data.learning_languages) {
        const languages = response.data.data.learning_languages
        setLearningLanguages(languages)
        if (languages.length > 0) {
          setSelectedLanguage(languages[0].code)
        }
      }
    } catch {
      setError(t('wordQuizSettings.profileLoadFailed'))
    } finally {
      setIsLoadingProfile(false)
    }
  }

  const loadVocabularies = async () => {
    try {
      const response = await vocabularyApi.getVocabularies()
      if (response.data.success) {
        setVocabularies(response.data.data.vocabularies)
      }
    } catch {
      // Silently fail - vocabularies are optional
    }
  }

  const handleStartQuiz = async () => {
    if (!selectedLanguage) {
      setError(t('wordQuizSettings.selectLanguage'))
      return
    }

    if (useVocabulary && !selectedVocabularyId) {
      setError(t('wordQuizSettings.selectVocabularyError'))
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await lrsWordQuizApi.startQuiz({
        learning_language: selectedLanguage,
        quiz_type: quizType,
        question_count: questionCount,
        vocabulary_id: useVocabulary ? selectedVocabularyId : null,
        learned_words_only: learnedWordsOnly,
      })

      if (response.data.success) {
        const quizId = response.data.data.quiz.id
        onClose()
        navigate(`/word-quiz/${quizId}`)
      }
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { message?: string } } }
        setError(axiosErr.response?.data?.message || t('wordQuizSettings.startFailed'))
      } else {
        setError(t('wordQuizSettings.startFailed'))
      }
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm transition-opacity"
          onClick={onClose}
        />

        <div className="relative w-full max-w-lg transform rounded-2xl bg-white p-6 shadow-xl transition-all">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-slate-800">{t('wordQuizSettings.title')}</h2>
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

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
              {error}
            </div>
          )}

          {isLoadingProfile ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
            </div>
          ) : learningLanguages.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-slate-500 mb-4">{t('wordQuizSettings.noLanguages')}</p>
              <p className="text-sm text-slate-400">{t('wordQuizSettings.noLanguagesDesc')}</p>
            </div>
          ) : (
            <>
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-700 mb-3">{t('wordQuizSettings.learningLanguage')}</label>
                <div className="grid grid-cols-2 gap-3">
                  {learningLanguages.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => setSelectedLanguage(lang.code)}
                      className={`p-3 rounded-xl border-2 transition-all text-center ${
                        selectedLanguage === lang.code
                          ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                          : 'border-slate-200 hover:border-slate-300 text-slate-600'
                      }`}
                    >
                      <div className="font-medium text-sm">{lang.name_ko}</div>
                      <div className="text-xs mt-1 opacity-70">{lang.code.toUpperCase()}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-700 mb-3">{t('wordQuizSettings.quizType')}</label>
                <div className="space-y-2">
                  {QUIZ_TYPES.map((type) => (
                    <button
                      key={type.value}
                      onClick={() => setQuizType(type.value)}
                      className={`w-full p-3 rounded-xl border-2 transition-all text-left ${
                        quizType === type.value
                          ? 'border-emerald-500 bg-emerald-50'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <div className={`font-medium text-sm ${quizType === type.value ? 'text-emerald-700' : 'text-slate-700'}`}>
                        {t(`wordQuizSettings.types.${type.value}`)}
                      </div>
                      <div className={`text-xs mt-1 ${quizType === type.value ? 'text-emerald-600' : 'text-slate-500'}`}>
                        {t(`wordQuizSettings.types.${type.value}_desc`)}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Vocabulary Selection */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-sm font-medium text-slate-700">{t('wordQuizSettings.useVocabulary')}</label>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={useVocabulary}
                      onChange={(e) => setUseVocabulary(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-emerald-300 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                  </label>
                </div>
                {useVocabulary && (
                  <div className="space-y-2">
                    <select
                      value={selectedVocabularyId || ''}
                      onChange={(e) => setSelectedVocabularyId(e.target.value ? parseInt(e.target.value) : null)}
                      className="w-full p-3 border-2 border-slate-200 rounded-xl focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 outline-none transition-all"
                    >
                      <option value="">{t('wordQuizSettings.selectVocabulary')}</option>
                      {vocabularies
                        .filter((vocab) => vocab.language_code === selectedLanguage)
                        .map((vocab) => (
                          <option key={vocab.id} value={vocab.id}>
                            {vocab.name} ({t('common.words', { count: vocab.word_count })})
                          </option>
                        ))}
                    </select>
                    {vocabularies.filter((vocab) => vocab.language_code === selectedLanguage).length === 0 && (
                      <p className="text-xs text-slate-500 mt-1">{t('wordQuizSettings.noVocabulary')}</p>
                    )}
                  </div>
                )}
              </div>

              {/* Learned Words Only */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <label className="block text-sm font-medium text-slate-700">{t('wordQuizSettings.learnedWordsOnly')}</label>
                    <p className="text-xs text-slate-500 mt-1">{t('wordQuizSettings.learnedWordsOnlyDesc')}</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={learnedWordsOnly}
                      onChange={(e) => setLearnedWordsOnly(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-emerald-300 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                  </label>
                </div>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-700 mb-3">{t('wordQuizSettings.questionCount')}</label>
                <div className="grid grid-cols-3 gap-3">
                  {QUESTION_COUNTS.map((count) => (
                    <button
                      key={count.value}
                      onClick={() => setQuestionCount(count.value)}
                      className={`p-3 rounded-xl border-2 transition-all text-center ${
                        questionCount === count.value
                          ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                          : 'border-slate-200 hover:border-slate-300 text-slate-600'
                      }`}
                    >
                      <div className="font-medium">{t(`wordQuizSettings.counts.${count.value}`)}</div>
                    </button>
                  ))}
                </div>
              </div>

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
                  className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg hover:shadow-xl disabled:opacity-50"
                  disabled={isLoading || !selectedLanguage}
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
                    t('wordQuizSettings.startQuiz')
                  )}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
