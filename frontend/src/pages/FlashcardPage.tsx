import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../contexts/AuthContext'
import Layout from '../components/Layout'
import { flashcardApi } from '../services/flashcardApi'
import { tts, getLanguageCode } from '../utils/textToSpeech'
import type {
  FlashcardSession,
  FlashcardRecord,
  FlashcardStartRequest,
} from '../types'
import type { WordCategory } from '../types/word'

type ViewState = 'setup' | 'learning' | 'result'

// 기본 카테고리 (모든 언어)
const BASE_CATEGORY_OPTIONS: { value: WordCategory | ''; label: string }[] = [
  { value: '', label: '전체' },
  { value: 'word', label: '단어' },
]

// 일본어 전용 카테고리
const JAPANESE_CATEGORY_OPTIONS: { value: WordCategory | ''; label: string }[] = [
  { value: 'hiragana', label: '히라가나' },
  { value: 'katakana', label: '가타카나' },
]

// 언어별 카테고리 필터링
const getCategoryOptions = (languageCode: string) => {
  if (languageCode === 'ja') {
    return [...BASE_CATEGORY_OPTIONS, ...JAPANESE_CATEGORY_OPTIONS]
  }
  return BASE_CATEGORY_OPTIONS
}

const CARD_COUNT_OPTIONS = [10, 20, 30, 50]

/**
 * 예문에서 특정 부분을 하이라이트하여 렌더링
 * @param text - 전체 예문 텍스트
 * @param highlight - [시작 인덱스, 끝 인덱스] 또는 null
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
      <span className="bg-white/30 px-1 rounded font-semibold underline underline-offset-2">
        {highlighted}
      </span>
      {after}
    </>
  )
}

export default function FlashcardPage() {
  const navigate = useNavigate()
  const { profile } = useAuth()
  const { t } = useTranslation()

  // Setup state
  const [selectedLanguage, setSelectedLanguage] = useState<string>('')
  const [selectedCategory, setSelectedCategory] = useState<WordCategory | ''>('')
  const [cardCount, setCardCount] = useState<number>(20)

  // Session state
  const [viewState, setViewState] = useState<ViewState>('setup')
  const [session, setSession] = useState<FlashcardSession | null>(null)
  const [currentCard, setCurrentCard] = useState<FlashcardRecord | null>(null)
  const [isFlipped, setIsFlipped] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isCardTransitioning, setIsCardTransitioning] = useState(false)

  // Result state (단순 완료 표시용)

  // Set default language when profile loads
  useEffect(() => {
    if (profile?.learning_languages && profile.learning_languages.length > 0) {
      setSelectedLanguage(profile.learning_languages[0].code)
    }
  }, [profile])

  // Reset category when language changes if current category is not valid
  useEffect(() => {
    const validCategories = getCategoryOptions(selectedLanguage).map(o => o.value)
    if (!validCategories.includes(selectedCategory)) {
      setSelectedCategory('')
    }
  }, [selectedLanguage])

  const startSession = async () => {
    if (!selectedLanguage) {
      setError(t('flashcard.selectLanguage'))
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const request: FlashcardStartRequest = {
        learning_language: selectedLanguage,
        category: selectedCategory,
        card_count: cardCount,
      }

      const response = await flashcardApi.start(request)
      if (response.data.success) {
        setSession(response.data.data.session)
        setCurrentCard(response.data.data.current_card)
        setIsFlipped(false)
        setViewState('learning')
        setKnownCount(0)
        setUnknownCount(0)
      } else {
        setError(response.data.message || t('flashcard.sessionStartFailed'))
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : t('flashcard.sessionStartError')
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFlip = useCallback(() => {
    setIsFlipped((prev) => !prev)
  }, [])

  const handleNext = async () => {
    if (!session || !currentCard || isCardTransitioning) return

    setIsLoading(true)

    try {
      const response = await flashcardApi.answer(session.id, {
        record_id: currentCard.id,
      })

      if (response.data.success) {
        const data = response.data.data
        // viewed 기록만 남김 (known_count, unknown_count 제거)

        if (data.session_completed) {
          setViewState('result')
        } else if (data.next_card) {
          // 카드 전환 애니메이션:
          // 1. 먼저 카드를 앞면으로 뒤집기 (번역→단어)
          // 2. 뒤집기 완료 후 페이드 아웃
          // 3. 카드 데이터 변경
          // 4. 페이드 인

          // Step 1: 카드를 앞면으로 뒤집기 (isCardTransitioning은 아직 false)
          setIsFlipped(false)

          // Step 2: 뒤집기 애니메이션 완료 대기 (500ms) 후 페이드 아웃 시작
          setTimeout(() => {
            // 페이드 아웃 시작
            setIsCardTransitioning(true)

            // Step 3: 페이드 아웃 완료 대기 (300ms) 후 카드 데이터 변경
            setTimeout(() => {
              setCurrentCard(data.next_card)

              // Step 4: DOM 업데이트 대기 후 페이드 인
              requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                  setIsCardTransitioning(false)
                })
              })
            }, 300) // 페이드 아웃 시간
          }, 500) // 카드 뒤집기 애니메이션 시간
        }
      }
    } catch (err) {
      console.error('Answer error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRestart = () => {
    setViewState('setup')
    setSession(null)
    setCurrentCard(null)
    setIsFlipped(false)
    setKnownCount(0)
    setUnknownCount(0)
  }

  // Keyboard shortcuts
  useEffect(() => {
    if (viewState !== 'learning') return

    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault()
        if (!isFlipped) {
          handleFlip()
        }
      } else if (isFlipped) {
        if (e.key === 'ArrowRight' || e.key === 'n' || e.key === 'N' || e.key === 'Enter') {
          e.preventDefault()
          handleNext()
        }
      }
    }

    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [viewState, isFlipped, handleFlip])

  // 학습 중 이탈 시 abandoned verb 전송 (라우팅 이동 시)
  useEffect(() => {
    // 학습 중이고 세션이 있으며 완료되지 않은 경우에만
    if (viewState !== 'learning' || !session || session.is_completed) return

    // cleanup: 컴포넌트 언마운트 시 (라우팅 이동 등)
    return () => {
      // 라우팅으로 이탈 시 abandon API 호출
      flashcardApi.abandon(session.id).catch(() => {
        // 에러 무시 (이미 이탈 중)
      })
    }
  }, [viewState, session?.id, session?.is_completed])

  const renderSetup = () => (
    <div className="max-w-md mx-auto">
      <div className="bg-white rounded-2xl shadow-lg p-8">
        <h2 className="text-2xl font-bold text-slate-800 mb-6 text-center">
          {t('flashcard.title')}
        </h2>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
            {error}
          </div>
        )}

        <div className="space-y-6">
          {/* Language Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              {t('flashcard.language')}
            </label>
            <div className="grid grid-cols-2 gap-2">
              {profile?.learning_languages?.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => setSelectedLanguage(lang.code)}
                  className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                    selectedLanguage === lang.code
                      ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/25'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {lang.name_ko}
                </button>
              ))}
            </div>
            {(!profile?.learning_languages || profile.learning_languages.length === 0) && (
              <p className="text-sm text-slate-400 mt-2">{t('flashcard.setLanguageInProfile')}</p>
            )}
          </div>

          {/* Category Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              {t('flashcard.category')}
            </label>
            <div className="grid grid-cols-2 gap-2">
              {getCategoryOptions(selectedLanguage).map((option) => (
                <button
                  key={option.value}
                  onClick={() => setSelectedCategory(option.value)}
                  className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                    selectedCategory === option.value
                      ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/25'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {option.value ? t('wordBrowse.categories.' + option.value, option.label) : t('common.all')}
                </button>
              ))}
            </div>
          </div>

          {/* Card Count Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              {t('flashcard.cardCount')}
            </label>
            <div className="grid grid-cols-4 gap-2">
              {CARD_COUNT_OPTIONS.map((count) => (
                <button
                  key={count}
                  onClick={() => setCardCount(count)}
                  className={`px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                    cardCount === count
                      ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/25'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {t('common.items', { count })}
                </button>
              ))}
            </div>
          </div>

          {/* Start Button */}
          <button
            onClick={startSession}
            disabled={isLoading || !selectedLanguage}
            className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold text-lg hover:from-indigo-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? t('common.starting') : t('flashcard.startSession')}
          </button>
        </div>
      </div>

      {/* Keyboard Shortcuts Info */}
      <div className="mt-6 bg-slate-50 rounded-xl p-4 text-sm text-slate-600">
        <p className="font-medium mb-2">{t('flashcard.keyboard.title')}</p>
        <ul className="space-y-1">
          <li><kbd className="px-2 py-1 bg-white rounded border">Space</kbd> - {t('flashcard.keyboard.space')}</li>
          <li><kbd className="px-2 py-1 bg-white rounded border">→</kbd> / <kbd className="px-2 py-1 bg-white rounded border">Enter</kbd> / <kbd className="px-2 py-1 bg-white rounded border">N</kbd> - {t('flashcard.keyboard.nextCardKey')}</li>
        </ul>
      </div>
    </div>
  )

  const renderLearning = () => {
    if (!session || !currentCard) return null

    const currentIndex = session.current_index + 1
    const progress = (currentIndex / session.total_cards) * 100

    return (
      <div className="max-w-2xl mx-auto">
        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-slate-600 mb-2">
            <span className="font-medium">{currentIndex} / {session.total_cards}</span>
            <span className="text-indigo-600">{t('flashcard.studying')}</span>
          </div>
          <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Flashcard */}
        <div
          className={`relative w-full aspect-[3/2] cursor-pointer transition-opacity duration-300 ease-in-out ${
            isCardTransitioning ? 'opacity-0 pointer-events-none' : 'opacity-100'
          }`}
          style={{ perspective: '1000px' }}
          onClick={handleFlip}
        >
          <div
            className="absolute inset-0 transition-transform duration-500"
            style={{
              transformStyle: 'preserve-3d',
              transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
            }}
          >
            {/* Front Side (Word) */}
            <div
              className="absolute inset-0 bg-white rounded-3xl shadow-xl flex flex-col items-center justify-center p-8"
              style={{
                backfaceVisibility: 'hidden',
                WebkitBackfaceVisibility: 'hidden',
              }}
            >
              <div className="flex items-center gap-4 mb-4">
                <div className="text-5xl font-bold text-slate-800">
                  {currentCard.word.word_text}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    tts.speak(currentCard.word.word_text, {
                      lang: getLanguageCode(selectedLanguage),
                      rate: 0.9,
                    })
                  }}
                  className="p-3 bg-indigo-100 text-indigo-700 rounded-xl hover:bg-indigo-200 transition-colors flex-shrink-0"
                  title={t('flashcard.listenPronunciation')}
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                  </svg>
                </button>
              </div>
              {currentCard.word.word_pronunciation && (
                <div className="text-xl text-slate-500">
                  {currentCard.word.word_pronunciation}
                </div>
              )}
              <div className="mt-6 text-sm text-slate-400">
                {t('flashcard.clickToFlip')}
              </div>
            </div>

            {/* Back Side (Translation & Example) */}
            <div
              className="absolute inset-0 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-3xl shadow-xl flex flex-col items-center justify-center p-8 text-white"
              style={{
                backfaceVisibility: 'hidden',
                WebkitBackfaceVisibility: 'hidden',
                transform: 'rotateY(180deg)',
              }}
            >
              <div className="text-3xl font-bold mb-4">
                {currentCard.word.translation || t('flashcard.noTranslation')}
              </div>
              {currentCard.word.example && (
                <div className="text-center mt-4">
                  <div className="flex items-center justify-center gap-3 mb-2">
                    <div className="text-lg opacity-90">
                      {renderHighlightedText(currentCard.word.example, currentCard.word.example_highlight)}
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        tts.speak(currentCard.word.example, {
                          lang: getLanguageCode(selectedLanguage),
                          rate: 0.85,
                        })
                      }}
                      className="p-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors flex-shrink-0"
                      title={t('flashcard.listenExample')}
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                      </svg>
                    </button>
                  </div>
                  {currentCard.word.example_translation && (
                    <div className="text-sm opacity-75">
                      {renderHighlightedText(currentCard.word.example_translation, currentCard.word.example_translation_highlight)}
                    </div>
                  )}
                </div>
              )}
              <div className="absolute bottom-4 text-sm opacity-60">
                {currentCard.word.category ? t('wordBrowse.categories.' + currentCard.word.category, [...BASE_CATEGORY_OPTIONS, ...JAPANESE_CATEGORY_OPTIONS].find((c) => c.value === currentCard.word.category)?.label) : t('common.all')}
              </div>
            </div>
          </div>
        </div>

        {/* Next Button */}
        <div className="mt-8">
          <button
            onClick={handleNext}
            disabled={!isFlipped || isLoading}
            className="w-full py-4 bg-indigo-600 text-white rounded-xl font-semibold text-lg hover:bg-indigo-700 transition-colors disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                {t('flashcard.processing')}
              </>
            ) : (
              <>
                {t('flashcard.nextCard')}
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </>
            )}
          </button>
        </div>

        {/* Help Text */}
        {!isFlipped ? (
          <p className="text-center text-slate-500 mt-4">
            {t('flashcard.flipOrSpace')}
          </p>
        ) : (
          <p className="text-center text-slate-500 mt-4">
            {t('flashcard.nextCardOrEnter')}
          </p>
        )}
      </div>
    )
  }

  const renderResult = () => {
    const total = session?.total_cards || 0

    return (
      <div className="max-w-md mx-auto">
        <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
          <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
            <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>

          <h2 className="text-2xl font-bold text-slate-800 mb-2">
            {t('flashcard.complete')}
          </h2>
          <p className="text-slate-600 mb-8">
            {t('flashcard.goodJob')}
          </p>

          {/* Stats */}
          <div className="mb-8">
            <div className="bg-indigo-50 rounded-xl p-6">
              <div className="text-5xl font-bold text-indigo-600 mb-2">{total}</div>
              <div className="text-lg text-indigo-700">{t('flashcard.wordsStudied')}</div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <button
              onClick={handleRestart}
              className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all"
            >
              {t('flashcard.studyAgain')}
            </button>
            <button
              onClick={() => navigate('/')}
              className="w-full py-4 bg-slate-100 text-slate-700 rounded-xl font-semibold hover:bg-slate-200 transition-colors"
            >
              {t('flashcard.goHome')}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        {viewState === 'setup' && renderSetup()}
        {viewState === 'learning' && renderLearning()}
        {viewState === 'result' && renderResult()}
      </div>
    </Layout>
  )
}
