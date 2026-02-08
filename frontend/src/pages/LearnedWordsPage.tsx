import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../contexts/AuthContext'
import Layout from '../components/Layout'
import api from '../services/api'
import { tts, getLanguageCode } from '../utils/textToSpeech'
import type { Word, Language } from '../types'

export default function LearnedWordsPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { user, profile } = useAuth()
  const [words, setWords] = useState<Word[]>([])
  const [learningLanguages, setLearningLanguages] = useState<Language[]>([])
  const [selectedLanguage, setSelectedLanguage] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (profile?.learning_languages) {
      setLearningLanguages(profile.learning_languages)
      if (profile.learning_languages.length > 0) {
        setSelectedLanguage(profile.learning_languages[0].code)
      }
    }
  }, [profile])

  useEffect(() => {
    if (selectedLanguage) {
      loadLearnedWords()
    }
  }, [selectedLanguage])

  const loadLearnedWords = async () => {
    if (!selectedLanguage) return

    setIsLoading(true)
    setError(null)

    try {
      const response = await api.get('/words/learned', {
        params: { learning_language: selectedLanguage }
      })

      if (response.data.success) {
        setWords(response.data.data.words)
      }
    } catch (err) {
      console.error('Failed to load learned words:', err)
      setError(t('learnedWords.loadFailed'))
    } finally {
      setIsLoading(false)
    }
  }

  const handleWordClick = (wordId: number) => {
    navigate(`/words/${wordId}`)
  }

  const handleSpeak = (text: string, e: React.MouseEvent) => {
    e.stopPropagation()
    tts.speak(text, {
      lang: getLanguageCode(selectedLanguage),
      rate: 0.9,
    })
  }

  if (!user) {
    return (
      <Layout>
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">
            <p className="text-slate-600">{t('common.loginRequired')}</p>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-slate-800">{t('learnedWords.title')}</h1>
              <p className="text-slate-500 mt-1">{t('learnedWords.subtitle')}</p>
            </div>
          </div>
        </div>

        {/* Language Selector */}
        {learningLanguages.length > 0 && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-700 mb-3">{t('learnedWords.learningLanguage')}</label>
            <div className="flex gap-3">
              {learningLanguages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => setSelectedLanguage(lang.code)}
                  className={`px-6 py-3 rounded-xl border-2 transition-all font-medium ${
                    selectedLanguage === lang.code
                      ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                      : 'border-slate-200 hover:border-slate-300 text-slate-600'
                  }`}
                >
                  {lang.name_ko}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">
            {error}
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
          </div>
        )}

        {/* Words List */}
        {!isLoading && (
          <>
            {words.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-20 h-20 mx-auto mb-4 bg-slate-100 rounded-full flex items-center justify-center">
                  <svg className="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <p className="text-slate-500 mb-2">{t('learnedWords.noWords')}</p>
                <p className="text-sm text-slate-400">{t('learnedWords.noWordsDesc')}</p>
              </div>
            ) : (
              <>
                <div className="mb-4 flex items-center justify-between">
                  <p className="text-sm text-slate-600">
                    {t('learnedWords.totalCount', { count: words.length }).replace(/<\/?strong>/g, '')}
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {words.map((word) => (
                    <div
                      key={word.id}
                      onClick={() => handleWordClick(word.id)}
                      className="bg-white rounded-xl p-5 shadow-sm border border-slate-100 hover:shadow-md hover:border-indigo-200 transition-all cursor-pointer"
                    >
                      {/* Word Header */}
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <h3 className="text-2xl font-bold text-slate-800">{word.text}</h3>
                          <button
                            onClick={(e) => handleSpeak(word.text, e)}
                            className="p-2 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 transition-colors flex-shrink-0"
                            title={t('flashcard.listenPronunciation')}
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                            </svg>
                          </button>
                        </div>
                      </div>

                      {/* Pronunciation */}
                      {word.pronunciation && (
                        <p className="text-sm text-slate-500 mb-2">{word.pronunciation}</p>
                      )}

                      {/* Translation */}
                      {word.translations && word.translations.length > 0 && (
                        <p className="text-slate-700 mb-3">{word.translations[0].translated_text}</p>
                      )}

                      {/* Example */}
                      {word.examples && word.examples.length > 0 && word.examples[0].sentence && (
                        <div className="mt-3 pt-3 border-t border-slate-100">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="text-sm text-slate-600 italic">{word.examples[0].sentence}</p>
                            <button
                              onClick={(e) => handleSpeak(word.examples[0].sentence, e)}
                              className="p-1 bg-slate-100 text-slate-600 rounded hover:bg-slate-200 transition-colors flex-shrink-0"
                              title="예문 듣기"
                            >
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                              </svg>
                            </button>
                          </div>
                          {word.examples[0].translations && word.examples[0].translations.length > 0 && (
                            <p className="text-xs text-slate-500">{word.examples[0].translations[0].translated_sentence}</p>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </div>
    </Layout>
  )
}
