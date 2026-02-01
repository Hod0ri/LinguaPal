import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import Layout from '../components/Layout'
import { flashcardApi } from '../services/flashcardApi'
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

  // Result state
  const [knownCount, setKnownCount] = useState(0)
  const [unknownCount, setUnknownCount] = useState(0)

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
      setError('학습할 언어를 선택해주세요.')
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
        setError(response.data.message || '세션 시작에 실패했습니다.')
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '세션 시작 중 오류가 발생했습니다.'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFlip = useCallback(() => {
    setIsFlipped((prev) => !prev)
  }, [])

  const handleAnswer = async (isKnown: boolean) => {
    if (!session || !currentCard || isCardTransitioning) return

    setIsLoading(true)

    try {
      const response = await flashcardApi.answer(session.id, {
        record_id: currentCard.id,
        is_known: isKnown,
      })

      if (response.data.success) {
        const data = response.data.data
        setKnownCount(data.known_count)
        setUnknownCount(data.unknown_count)

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
        if (e.key === 'ArrowLeft' || e.key === 'x' || e.key === 'X') {
          e.preventDefault()
          handleAnswer(false)
        } else if (e.key === 'ArrowRight' || e.key === 'o' || e.key === 'O') {
          e.preventDefault()
          handleAnswer(true)
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
          플래시카드 학습
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
              학습 언어
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
              <p className="text-sm text-slate-400 mt-2">학습 언어를 프로필에서 설정해주세요.</p>
            )}
          </div>

          {/* Category Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              카테고리
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
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Card Count Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              카드 수
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
                  {count}개
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
            {isLoading ? '시작 중...' : '학습 시작'}
          </button>
        </div>
      </div>

      {/* Keyboard Shortcuts Info */}
      <div className="mt-6 bg-slate-50 rounded-xl p-4 text-sm text-slate-600">
        <p className="font-medium mb-2">키보드 단축키</p>
        <ul className="space-y-1">
          <li><kbd className="px-2 py-1 bg-white rounded border">Space</kbd> / <kbd className="px-2 py-1 bg-white rounded border">Enter</kbd> - 카드 뒤집기</li>
          <li><kbd className="px-2 py-1 bg-white rounded border">←</kbd> / <kbd className="px-2 py-1 bg-white rounded border">X</kbd> - 모르겠어요</li>
          <li><kbd className="px-2 py-1 bg-white rounded border">→</kbd> / <kbd className="px-2 py-1 bg-white rounded border">O</kbd> - 알아요</li>
        </ul>
      </div>
    </div>
  )

  const renderLearning = () => {
    if (!session || !currentCard) return null

    const progress = ((knownCount + unknownCount) / session.total_cards) * 100

    return (
      <div className="max-w-2xl mx-auto">
        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-slate-600 mb-2">
            <span>{knownCount + unknownCount + 1} / {session.total_cards}</span>
            <span>
              <span className="text-green-600">알아요: {knownCount}</span>
              {' | '}
              <span className="text-red-600">몰라요: {unknownCount}</span>
            </span>
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
              <div className="text-5xl font-bold text-slate-800 mb-4">
                {currentCard.word.word_text}
              </div>
              {currentCard.word.word_pronunciation && (
                <div className="text-xl text-slate-500">
                  {currentCard.word.word_pronunciation}
                </div>
              )}
              <div className="mt-6 text-sm text-slate-400">
                클릭하여 뒤집기
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
                {currentCard.word.translation || '번역 없음'}
              </div>
              {currentCard.word.example && (
                <div className="text-center mt-4">
                  <div className="text-lg opacity-90 mb-2">
                    {renderHighlightedText(currentCard.word.example, currentCard.word.example_highlight)}
                  </div>
                  {currentCard.word.example_translation && (
                    <div className="text-sm opacity-75">
                      {renderHighlightedText(currentCard.word.example_translation, currentCard.word.example_translation_highlight)}
                    </div>
                  )}
                </div>
              )}
              <div className="absolute bottom-4 text-sm opacity-60">
                {[...BASE_CATEGORY_OPTIONS, ...JAPANESE_CATEGORY_OPTIONS].find((c) => c.value === currentCard.word.category)?.label}
              </div>
            </div>
          </div>
        </div>

        {/* Answer Buttons */}
        <div className="mt-8 flex gap-4">
          <button
            onClick={() => handleAnswer(false)}
            disabled={!isFlipped || isLoading}
            className="flex-1 py-4 bg-red-500 text-white rounded-xl font-semibold text-lg hover:bg-red-600 transition-colors disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            모르겠어요
          </button>
          <button
            onClick={() => handleAnswer(true)}
            disabled={!isFlipped || isLoading}
            className="flex-1 py-4 bg-green-500 text-white rounded-xl font-semibold text-lg hover:bg-green-600 transition-colors disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            알아요
          </button>
        </div>

        {/* Help Text */}
        {!isFlipped && (
          <p className="text-center text-slate-500 mt-4">
            카드를 클릭하거나 Space 키를 눌러 뒤집으세요
          </p>
        )}
      </div>
    )
  }

  const renderResult = () => {
    const total = knownCount + unknownCount
    const knownPercentage = total > 0 ? Math.round((knownCount / total) * 100) : 0

    return (
      <div className="max-w-md mx-auto">
        <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
          <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
            <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>

          <h2 className="text-2xl font-bold text-slate-800 mb-2">
            학습 완료!
          </h2>
          <p className="text-slate-600 mb-8">
            수고하셨습니다!
          </p>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="bg-slate-50 rounded-xl p-4">
              <div className="text-3xl font-bold text-slate-800">{total}</div>
              <div className="text-sm text-slate-500">총 카드</div>
            </div>
            <div className="bg-green-50 rounded-xl p-4">
              <div className="text-3xl font-bold text-green-600">{knownCount}</div>
              <div className="text-sm text-green-600">알아요</div>
            </div>
            <div className="bg-red-50 rounded-xl p-4">
              <div className="text-3xl font-bold text-red-600">{unknownCount}</div>
              <div className="text-sm text-red-600">몰라요</div>
            </div>
          </div>

          {/* Progress Circle */}
          <div className="relative w-32 h-32 mx-auto mb-8">
            <svg className="w-full h-full -rotate-90">
              <circle
                cx="64"
                cy="64"
                r="56"
                fill="none"
                stroke="#e2e8f0"
                strokeWidth="12"
              />
              <circle
                cx="64"
                cy="64"
                r="56"
                fill="none"
                stroke="url(#gradient)"
                strokeWidth="12"
                strokeLinecap="round"
                strokeDasharray={`${knownPercentage * 3.52} 352`}
              />
              <defs>
                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="#a855f7" />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-bold text-slate-800">{knownPercentage}%</span>
              <span className="text-sm text-slate-500">숙지율</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <button
              onClick={handleRestart}
              className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all"
            >
              다시 학습하기
            </button>
            <button
              onClick={() => navigate('/')}
              className="w-full py-4 bg-slate-100 text-slate-700 rounded-xl font-semibold hover:bg-slate-200 transition-colors"
            >
              홈으로
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
