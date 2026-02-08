import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../contexts/AuthContext'
import Layout from '../components/Layout'
import { wordBrowseApi } from '../services/api'
import type {
  BrowseWord,
  BrowseWordListItem,
  BrowseWordParams,
  Pagination,
  WordCategory,
  PartOfSpeech,
} from '../types'
import { PART_OF_SPEECH_OPTIONS, DIFFICULTY_OPTIONS } from '../types/word'
import { getGrammarLabel, getGrammarDescription, translateGrammarValue } from '../constants/grammar'
import AddToVocabularyButton from '../components/AddToVocabularyButton'
import { tts, getLanguageCode } from '../utils/textToSpeech'

// View modes
type ViewMode = 'list' | 'random' | 'detail'

// Category options for filtering (labels resolved via i18n at render time)
const BASE_CATEGORY_OPTIONS: { value: WordCategory | '' }[] = [
  { value: '' },
  { value: 'word' },
]

const JAPANESE_CATEGORY_OPTIONS: { value: WordCategory | '' }[] = [
  { value: '' },
  { value: 'word' },
  { value: 'hiragana' },
  { value: 'katakana' },
]

/**
 * Render text with highlight
 */
function renderHighlightedText(text: string, highlight: number[] | null): React.ReactNode {
  if (!highlight || highlight.length < 2) {
    return text
  }

  const [start, end] = highlight
  if (start < 0 || end > text.length || start >= end) {
    return text
  }

  const before = text.slice(0, start)
  const highlighted = text.slice(start, end)
  const after = text.slice(end)

  return (
    <>
      {before}
      <span className="bg-yellow-200 px-1 rounded font-semibold">
        {highlighted}
      </span>
      {after}
    </>
  )
}

/**
 * Format grammar value for display
 * Handles objects, arrays, and primitive values
 * Uses Korean labels for nested keys
 * Translates Japanese grammar terms to Korean
 */
function formatGrammarValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '-'
  }
  if (typeof value === 'object') {
    if (Array.isArray(value)) {
      return value.map(v => translateGrammarValue(String(v))).join(', ')
    }
    // For objects, show key-value pairs with Korean labels
    return Object.entries(value as Record<string, unknown>)
      .map(([k, v]) => `${getGrammarLabel(k)}: ${formatGrammarValue(v)}`)
      .join(', ')
  }
  // Translate Japanese grammar terms (like 五段動詞, い形容詞)
  return translateGrammarValue(String(value))
}

/**
 * Render grammar properties with tooltips
 */
function renderGrammar(grammar: Record<string, unknown>): React.ReactNode {
  if (!grammar || Object.keys(grammar).length === 0) {
    return null
  }

  return (
    <div className="flex flex-wrap gap-2">
      {Object.entries(grammar).map(([key, value]) => {
        const label = getGrammarLabel(key)
        const description = getGrammarDescription(key)
        const displayValue = formatGrammarValue(value)

        return (
          <span
            key={key}
            className="px-2 py-1 bg-indigo-50 text-indigo-700 rounded-lg text-xs group relative cursor-help"
            title={description}
          >
            <span className="font-medium">{label}:</span>{' '}
            {displayValue}
            {description && (
              <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-slate-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                {description}
                <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
              </span>
            )}
          </span>
        )
      })}
    </div>
  )
}

export default function WordBrowsePage() {
  const { t } = useTranslation()
  const { profile } = useAuth()
  const [searchParams] = useSearchParams()

  // View state
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [selectedWord, setSelectedWord] = useState<BrowseWord | null>(null)

  // List state
  const [words, setWords] = useState<BrowseWordListItem[]>([])
  const [pagination, setPagination] = useState<Pagination | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Random state
  const [randomWords, setRandomWords] = useState<BrowseWord[]>([])
  const [currentRandomIndex, setCurrentRandomIndex] = useState(0)

  // Filter state
  const [selectedLanguage, setSelectedLanguage] = useState<string>('')
  const [selectedCategory, setSelectedCategory] = useState<WordCategory | ''>('')
  const [selectedPartOfSpeech, setSelectedPartOfSpeech] = useState<PartOfSpeech | ''>('')
  const [selectedDifficulty, setSelectedDifficulty] = useState<number | ''>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)

  // Set default language when profile loads
  useEffect(() => {
    if (profile?.learning_languages && profile.learning_languages.length > 0) {
      setSelectedLanguage(profile.learning_languages[0].code)
    }
  }, [profile])

  // Load words when filters change
  const loadWords = useCallback(async () => {
    if (!selectedLanguage) return

    setIsLoading(true)
    setError(null)

    try {
      const params: BrowseWordParams = {
        language: selectedLanguage,
        page: currentPage,
        page_size: 20,
      }

      if (selectedCategory) params.category = selectedCategory
      if (selectedPartOfSpeech) params.part_of_speech = selectedPartOfSpeech
      if (selectedDifficulty) params.difficulty_level = selectedDifficulty
      if (searchQuery.trim()) params.search = searchQuery.trim()

      const response = await wordBrowseApi.getWords(params)
      if (response.data.success) {
        setWords(response.data.data.words)
        setPagination(response.data.data.pagination)
      } else {
        setError(response.data.message || t('wordBrowse.loadFailed'))
      }
    } catch (err) {
      console.error('Failed to load words:', err)
      setError(t('wordBrowse.loadFailed'))
    } finally {
      setIsLoading(false)
    }
  }, [selectedLanguage, selectedCategory, selectedPartOfSpeech, selectedDifficulty, searchQuery, currentPage, t])

  // Load words on mount and filter changes
  useEffect(() => {
    if (viewMode === 'list') {
      loadWords()
    }
  }, [loadWords, viewMode])

  // Load word detail
  const loadWordDetail = async (wordId: number) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await wordBrowseApi.getWordDetail(wordId)
      if (response.data.success) {
        setSelectedWord(response.data.data)
        setViewMode('detail')
      } else {
        setError(response.data.message || t('wordBrowse.loadFailed'))
      }
    } catch (err) {
      console.error('Failed to load word detail:', err)
      setError(t('wordBrowse.loadFailed'))
    } finally {
      setIsLoading(false)
    }
  }

  // Load random words
  const loadRandomWords = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const params: { language?: string; category?: WordCategory; count: number } = {
        count: 5,
      }
      if (selectedLanguage) params.language = selectedLanguage
      if (selectedCategory) params.category = selectedCategory

      const response = await wordBrowseApi.getRandomWords(params)
      if (response.data.success && response.data.data.words.length > 0) {
        setRandomWords(response.data.data.words)
        setCurrentRandomIndex(0)
        setViewMode('random')
      } else {
        setError(t('wordBrowse.noMatchingWords'))
      }
    } catch (err) {
      console.error('Failed to load random words:', err)
      setError(t('wordBrowse.loadRandomFailed'))
    } finally {
      setIsLoading(false)
    }
  }

  // Load word detail from URL parameter
  useEffect(() => {
    const wordId = searchParams.get('id')
    if (wordId) {
      const id = parseInt(wordId, 10)
      if (!isNaN(id)) {
        loadWordDetail(id)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setCurrentPage(1)
    loadWords()
  }

  // Render list view
  const renderListView = () => (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          {/* Language filter */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              {t('wordBrowse.language')}
            </label>
            <select
              value={selectedLanguage}
              onChange={(e) => {
                const newLang = e.target.value
                setSelectedLanguage(newLang)
                // Reset category if switching away from Japanese with hiragana/katakana selected
                if (newLang !== 'ja' && (selectedCategory === 'hiragana' || selectedCategory === 'katakana')) {
                  setSelectedCategory('')
                }
                setCurrentPage(1)
              }}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {profile?.learning_languages?.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name_ko}
                </option>
              ))}
            </select>
          </div>

          {/* Category filter */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              {t('wordBrowse.category')}
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value as WordCategory | '')
                setCurrentPage(1)
              }}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {(selectedLanguage === 'ja' ? JAPANESE_CATEGORY_OPTIONS : BASE_CATEGORY_OPTIONS).map((option) => (
                <option key={option.value} value={option.value}>
                  {option.value === '' ? t('common.all') : t(`wordBrowse.categories.${option.value}`)}
                </option>
              ))}
            </select>
          </div>

          {/* Part of speech filter */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              {t('wordBrowse.partOfSpeech')}
            </label>
            <select
              value={selectedPartOfSpeech}
              onChange={(e) => {
                setSelectedPartOfSpeech(e.target.value as PartOfSpeech | '')
                setCurrentPage(1)
              }}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">{t('common.all')}</option>
              {PART_OF_SPEECH_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Difficulty filter */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              {t('wordBrowse.difficulty')}
            </label>
            <select
              value={selectedDifficulty}
              onChange={(e) => {
                setSelectedDifficulty(e.target.value ? Number(e.target.value) : '')
                setCurrentPage(1)
              }}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">{t('common.all')}</option>
              {DIFFICULTY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Search and Random */}
        <div className="flex gap-4">
          <form onSubmit={handleSearch} className="flex-1 flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t('wordBrowse.searchPlaceholder')}
              className="flex-1 px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="submit"
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              {t('common.search')}
            </button>
          </form>
          <button
            onClick={loadRandomWords}
            disabled={isLoading}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {t('wordBrowse.random')}
          </button>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
          {error}
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
        </div>
      )}

      {/* Word list */}
      {!isLoading && words.length > 0 && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="divide-y divide-slate-100">
            {words.map((word) => (
              <div
                key={word.id}
                onClick={() => loadWordDetail(word.id)}
                className="p-4 hover:bg-slate-50 cursor-pointer transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div>
                      <span className="text-xl font-bold text-slate-800">{word.text}</span>
                      {word.pronunciation && (
                        <span className="ml-2 text-slate-500">({word.pronunciation})</span>
                      )}
                    </div>
                    <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-xs">
                      {word.part_of_speech_display}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    {word.translation && (
                      <span className="text-slate-600">{word.translation}</span>
                    )}
                    <div className="flex items-center gap-1">
                      {[...Array(5)].map((_, i) => (
                        <div
                          key={i}
                          className={`w-2 h-2 rounded-full ${
                            i < word.difficulty_level ? 'bg-indigo-500' : 'bg-slate-200'
                          }`}
                        />
                      ))}
                    </div>
                    <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && words.length === 0 && (
        <div className="text-center py-12 text-slate-500">
          {t('wordBrowse.noResults')}
        </div>
      )}

      {/* Pagination */}
      {pagination && pagination.total_pages > 1 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-50"
          >
            {t('common.previous')}
          </button>
          <span className="px-4 py-2 text-slate-600">
            {currentPage} / {pagination.total_pages}
          </span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(pagination.total_pages, p + 1))}
            disabled={currentPage === pagination.total_pages}
            className="px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-50"
          >
            {t('common.next')}
          </button>
        </div>
      )}
    </div>
  )

  // Render random view
  const renderRandomView = () => {
    const currentWord = randomWords[currentRandomIndex]
    if (!currentWord) return null

    return (
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Back button */}
        <button
          onClick={() => setViewMode('list')}
          className="flex items-center gap-2 text-slate-600 hover:text-slate-800"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          {t('wordBrowse.backToList')}
        </button>

        {/* Progress indicator */}
        <div className="flex justify-center gap-2">
          {randomWords.map((_, i) => (
            <button
              key={i}
              onClick={() => setCurrentRandomIndex(i)}
              className={`w-3 h-3 rounded-full transition-colors ${
                i === currentRandomIndex ? 'bg-indigo-600' : 'bg-slate-300'
              }`}
            />
          ))}
        </div>

        {/* Word card */}
        <div className="bg-white rounded-2xl shadow-lg p-8">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="flex items-center justify-center gap-3 mb-2">
              <div className="text-5xl font-bold text-slate-800">
                {currentWord.text}
              </div>
              <button
                onClick={() => tts.speak(currentWord.text, { lang: getLanguageCode(currentWord.language_code), rate: 0.9 })}
                className="p-3 bg-indigo-100 text-indigo-700 rounded-xl hover:bg-indigo-200 transition-colors"
                title={t('wordBrowse.listenPronunciation')}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
              </button>
            </div>
            {currentWord.pronunciation && (
              <div className="text-xl text-slate-500 mb-2">
                {currentWord.pronunciation}
              </div>
            )}
            <div className="flex justify-center items-center gap-3">
              <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-lg text-sm font-medium">
                {currentWord.part_of_speech_display}
              </span>
              <span className="px-3 py-1 bg-slate-100 text-slate-600 rounded-lg text-sm">
                {currentWord.category_display}
              </span>
              <div className="flex items-center gap-1">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-2 h-2 rounded-full ${
                      i < currentWord.difficulty_level ? 'bg-indigo-500' : 'bg-slate-200'
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Translations */}
          {currentWord.translations.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-slate-500 mb-2">{t('wordBrowse.translation')}</h3>
              <div className="space-y-2">
                {currentWord.translations.map((trans) => (
                  <div key={trans.id} className="p-3 bg-slate-50 rounded-lg">
                    <span className="text-lg text-slate-800">{trans.translated_text}</span>
                    {trans.notes && (
                      <span className="ml-2 text-slate-500">({trans.notes})</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Grammar properties */}
          {currentWord.grammar && Object.keys(currentWord.grammar).length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-slate-500 mb-2">{t('wordBrowse.grammarProperties')}</h3>
              {renderGrammar(currentWord.grammar)}
            </div>
          )}

          {/* Examples */}
          {currentWord.examples.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-slate-500 mb-2">{t('wordBrowse.examples')}</h3>
              <div className="space-y-4">
                {currentWord.examples.map((example) => (
                  <div key={example.id} className="p-4 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl">
                    <div className="flex items-start gap-2 mb-2">
                      <div className="flex-1 text-lg text-slate-800">
                        {renderHighlightedText(example.sentence, example.highlight_indices)}
                      </div>
                      <button
                        onClick={() => tts.speak(example.sentence, { lang: getLanguageCode(currentWord.language_code), rate: 0.85 })}
                        className="p-2 bg-white/60 text-indigo-700 rounded-lg hover:bg-white transition-colors flex-shrink-0"
                        title={t('wordBrowse.listenExample')}
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                        </svg>
                      </button>
                    </div>
                    {example.translations.map((trans) => (
                      <div key={trans.id} className="text-slate-600">
                        {renderHighlightedText(trans.translated_sentence, trans.highlight_indices)}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Navigation buttons */}
        <div className="flex justify-between">
          <button
            onClick={() => setCurrentRandomIndex((i) => Math.max(0, i - 1))}
            disabled={currentRandomIndex === 0}
            className="px-6 py-3 bg-slate-100 text-slate-700 rounded-xl hover:bg-slate-200 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            {t('common.previous')}
          </button>
          <button
            onClick={loadRandomWords}
            className="px-6 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {t('wordBrowse.loadNew')}
          </button>
          <button
            onClick={() => setCurrentRandomIndex((i) => Math.min(randomWords.length - 1, i + 1))}
            disabled={currentRandomIndex === randomWords.length - 1}
            className="px-6 py-3 bg-slate-100 text-slate-700 rounded-xl hover:bg-slate-200 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            {t('common.next')}
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    )
  }

  // Render detail view
  const renderDetailView = () => {
    if (!selectedWord) return null

    return (
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Back button */}
        <button
          onClick={() => setViewMode('list')}
          className="flex items-center gap-2 text-slate-600 hover:text-slate-800"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          {t('wordBrowse.backToList')}
        </button>

        {/* Word card */}
        <div className="bg-white rounded-2xl shadow-lg p-8">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="flex items-center justify-center gap-3 mb-2">
              <div className="text-5xl font-bold text-slate-800">
                {selectedWord.text}
              </div>
              <button
                onClick={() => tts.speak(selectedWord.text, { lang: getLanguageCode(selectedWord.language_code), rate: 0.9 })}
                className="p-3 bg-indigo-100 text-indigo-700 rounded-xl hover:bg-indigo-200 transition-colors"
                title={t('wordBrowse.listenPronunciation')}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
              </button>
            </div>
            {selectedWord.pronunciation && (
              <div className="text-xl text-slate-500 mb-2">
                {selectedWord.pronunciation}
              </div>
            )}
            <div className="flex justify-center items-center gap-3 mb-4">
              <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-lg text-sm font-medium">
                {selectedWord.part_of_speech_display}
              </span>
              <span className="px-3 py-1 bg-slate-100 text-slate-600 rounded-lg text-sm">
                {selectedWord.category_display}
              </span>
              <div className="flex items-center gap-1">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-2 h-2 rounded-full ${
                      i < selectedWord.difficulty_level ? 'bg-indigo-500' : 'bg-slate-200'
                    }`}
                  />
                ))}
              </div>
            </div>
            {/* Add to Vocabulary Button */}
            <div className="flex justify-center">
              <AddToVocabularyButton
                wordId={selectedWord.id}
                wordText={selectedWord.text}
                wordLanguageId={selectedWord.language}
              />
            </div>
          </div>

          {/* Translations */}
          {selectedWord.translations.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-slate-500 mb-2">{t('wordBrowse.translation')}</h3>
              <div className="space-y-2">
                {selectedWord.translations.map((trans) => (
                  <div key={trans.id} className="p-3 bg-slate-50 rounded-lg">
                    <span className="text-lg text-slate-800">{trans.translated_text}</span>
                    {trans.notes && (
                      <span className="ml-2 text-slate-500">({trans.notes})</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Grammar properties */}
          {selectedWord.grammar && Object.keys(selectedWord.grammar).length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-slate-500 mb-2">{t('wordBrowse.grammarProperties')}</h3>
              {renderGrammar(selectedWord.grammar)}
            </div>
          )}

          {/* Examples */}
          {selectedWord.examples.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-slate-500 mb-2">{t('wordBrowse.examples')}</h3>
              <div className="space-y-4">
                {selectedWord.examples.map((example) => (
                  <div key={example.id} className="p-4 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl">
                    <div className="flex items-start gap-2 mb-2">
                      <div className="flex-1 text-lg text-slate-800">
                        {renderHighlightedText(example.sentence, example.highlight_indices)}
                      </div>
                      <button
                        onClick={() => tts.speak(example.sentence, { lang: getLanguageCode(selectedWord.language_code), rate: 0.85 })}
                        className="p-2 bg-white/60 text-indigo-700 rounded-lg hover:bg-white transition-colors flex-shrink-0"
                        title={t('wordBrowse.listenExample')}
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                        </svg>
                      </button>
                    </div>
                    {example.translations.map((trans) => (
                      <div key={trans.id} className="text-slate-600">
                        {renderHighlightedText(trans.translated_sentence, trans.highlight_indices)}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto py-8 px-4">
        {/* Page header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-800">{t('wordBrowse.title')}</h1>
          <p className="text-slate-500">{t('wordBrowse.subtitle')}</p>
        </div>

        {/* Content */}
        {viewMode === 'list' && renderListView()}
        {viewMode === 'random' && renderRandomView()}
        {viewMode === 'detail' && renderDetailView()}
      </div>
    </Layout>
  )
}
