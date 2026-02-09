import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import Layout from '../components/Layout'
import WordQuizSettingsModal from '../components/WordQuizSettingsModal'
import { quizApi, wordQuizApi, streakApi } from '../services/api'
import type { QuizStats, WordQuizStats, LearningStreak, CardRecommendation, UserXPStatus } from '../types'

interface CombinedStats {
  total_quizzes: number
  completed_quizzes: number
  total_questions_answered: number
  total_correct: number
  overall_accuracy: number
}

export default function MainPage() {
  const { profile } = useAuth()
  const { t } = useTranslation()
  const [showWordQuizModal, setShowWordQuizModal] = useState(false)
  const [combinedStats, setCombinedStats] = useState<CombinedStats | null>(null)
  const [streak, setStreak] = useState<LearningStreak | null>(null)
  const [recommendation, setRecommendation] = useState<CardRecommendation | null>(null)
  const [xp, setXp] = useState<UserXPStatus | null>(null)

  // 일본어 학습 중인지 확인
  const isLearningJapanese = profile?.learning_languages.some(
    (lang) => lang.code === 'ja'
  ) ?? false

  // 학습 중인 언어 코드 목록
  const learningLanguageCodes = profile?.learning_languages.map(l => l.code) ?? []

  const greetingParts = t('main.greeting', { name: '|||' }).split('|||')

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

  useEffect(() => {
    const loadStreak = async () => {
      try {
        const response = await streakApi.getStreakAndRecommendation()
        if (response.data.success) {
          setStreak(response.data.data.streak)
          setRecommendation(response.data.data.recommendation)
          setXp(response.data.data.xp)
        }
      } catch {
        // Silently handle - streak is non-critical
      }
    }
    loadStreak()
  }, [])

  const isRecommended = (cardId: string) => recommendation?.card_id === cardId

  const cardHighlightClass = (cardId: string) => {
    if (!isRecommended(cardId)) return ''
    const colorMap: Record<string, string> = {
      wordBrowse: 'card-glow-amber',
      flashcard: 'card-glow-purple',
      learnedWords: 'card-glow-indigo',
      vocabulary: 'card-glow-rose',
      quiz: 'card-glow-emerald',
    }
    return colorMap[cardId] || ''
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">👋</span>
            <h1 className="text-3xl font-bold text-slate-800">
              {greetingParts[0]}
              <span className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">{profile?.nickname}</span>
              {greetingParts[1]}
            </h1>
          </div>
          <p className="text-slate-500">
            {t('main.subtitle')}
          </p>
        </div>

        {/* Streak & XP Banner */}
        {(streak || xp) && (
          <div className="mb-8 p-5 bg-gradient-to-r from-orange-50 via-amber-50 to-yellow-50 rounded-2xl border border-orange-200/60">
            <div className="flex flex-col lg:flex-row gap-4 lg:gap-6">

              {/* Left: Streak Section */}
              {streak && (
                <div className="flex-1 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{(streak.current_streak ?? 0) > 0 ? '\uD83D\uDD25' : '\uD83D\uDCDA'}</span>
                    <div>
                      {(streak.current_streak ?? 0) > 0 ? (
                        <p className="text-lg font-bold text-orange-800">
                          {t('main.streak.days', { count: streak.current_streak ?? 0 })} {t('main.streak.keepGoing')}
                        </p>
                      ) : streak.days_since_last_study != null ? (
                        <p className="text-lg font-bold text-slate-700">
                          {t('main.streak.comeBack', { days: streak.days_since_last_study ?? 0 })}
                        </p>
                      ) : (
                        <p className="text-lg font-bold text-slate-700">
                          {t('main.streak.startToday')}
                        </p>
                      )}
                      {(streak.max_streak ?? 0) > 0 && (
                        <p className="text-sm text-orange-600/70">
                          {t('main.streak.best')}: {t('main.streak.days', { count: streak.max_streak ?? 0 })}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="lg:hidden">
                    {streak.is_active_today ? (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-100 text-emerald-700 rounded-full text-sm font-medium">
                        <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                        {t('main.streak.studiedToday')}
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 text-slate-500 rounded-full text-sm font-medium">
                        <span className="w-2 h-2 bg-slate-400 rounded-full"></span>
                        {t('main.streak.notYetToday')}
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Divider */}
              {streak && xp && (
                <>
                  <div className="hidden lg:block w-px bg-orange-200/80 self-stretch" />
                  <div className="lg:hidden h-px bg-orange-200/80" />
                </>
              )}

              {/* Right: XP & Level Section */}
              {xp && (
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">{(xp.current_level ?? 1) >= 10 ? '\uD83D\uDC51' : '\u2B50'}</span>
                      <span className="text-2xl font-black bg-gradient-to-r from-amber-600 to-orange-600 bg-clip-text text-transparent">
                        Lv. {xp.current_level ?? 1}
                      </span>
                      <span className="text-sm font-medium text-amber-700/70 ml-1">
                        {xp.total_xp ?? 0} XP
                      </span>
                    </div>
                    {/* Today status badge - desktop only (mobile shown with streak) */}
                    {streak && (
                      <div className="hidden lg:block">
                        {streak.is_active_today ? (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-100 text-emerald-700 rounded-full text-sm font-medium">
                            <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                            {t('main.streak.studiedToday')}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 text-slate-500 rounded-full text-sm font-medium">
                            <span className="w-2 h-2 bg-slate-400 rounded-full"></span>
                            {t('main.streak.notYetToday')}
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Level Progress Bar */}
                  {xp.next_level && (
                    <div className="mb-2">
                      <div className="flex justify-between text-xs text-amber-700/60 mb-1">
                        <span>{t('main.xp.levelProgress')}</span>
                        <span>{xp.xp_in_level ?? 0} / {xp.xp_for_next_level ?? 0}</span>
                      </div>
                      <div className="h-2.5 bg-amber-200/50 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-full transition-all duration-500"
                          style={{ width: `${xp.progress_percentage ?? 0}%` }}
                        />
                      </div>
                    </div>
                  )}
                  {!xp.next_level && (
                    <div className="mb-2">
                      <p className="text-sm font-medium text-amber-600">{t('main.xp.maxLevel')}</p>
                    </div>
                  )}

                  {/* Daily XP Tracker */}
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 bg-amber-200/50 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-emerald-400 to-emerald-500 rounded-full transition-all duration-500"
                        style={{ width: `${((xp.daily_xp_earned ?? 0) / (xp.daily_xp_max || 1)) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-medium text-amber-700/60 whitespace-nowrap">
                      {t('main.xp.dailyXP')}: {xp.daily_xp_earned ?? 0}/{xp.daily_xp_max ?? 30} XP
                    </span>
                  </div>
                </div>
              )}

            </div>
          </div>
        )}

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
                <h2 className="text-lg font-semibold text-slate-800">{t('main.learningLanguages')}</h2>
              </div>
              <Link to="/profile" className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">
                {t('common.edit')}
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

          {/* Word Browse Card */}
          <div className={`card p-6 group hover:border-amber-200 transition-colors relative flex flex-col ${cardHighlightClass('wordBrowse')}`}>
            {isRecommended('wordBrowse') && (
              <div className="absolute -top-2.5 left-4 px-2.5 py-0.5 bg-amber-500 text-white text-xs font-bold rounded-full shadow-sm">
                {t('main.recommendation.recommended')}
              </div>
            )}
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-slate-800">{t('main.wordBrowse.title')}</h2>
            </div>
            <p className="text-slate-500 text-sm mb-3">
              {t('main.wordBrowse.desc')}
            </p>
            <div className="text-xs text-slate-400 mb-4">
              {isRecommended('wordBrowse') && recommendation ? (
                <span className="text-amber-600 font-medium">{t(`main.recommendation.${recommendation.reason_key}`, recommendation.reason_params)}</span>
              ) : (
                t('main.wordBrowse.subdesc')
              )}
            </div>
            <Link to="/words" className="block w-full mt-auto bg-amber-600 hover:bg-amber-700 text-white font-semibold py-2 px-4 rounded-xl transition-all text-center">
              {t('main.wordBrowse.button')}
            </Link>
          </div>

          {/* Flashcard Card */}
          <div className={`card p-6 group hover:border-purple-200 transition-colors relative flex flex-col ${cardHighlightClass('flashcard')}`}>
            {isRecommended('flashcard') && (
              <div className="absolute -top-2.5 left-4 px-2.5 py-0.5 bg-purple-500 text-white text-xs font-bold rounded-full shadow-sm">
                {t('main.recommendation.recommended')}
              </div>
            )}
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-slate-800">{t('main.flashcard.title')}</h2>
            </div>
            <p className="text-slate-500 text-sm mb-3">
              {t('main.flashcard.desc')}
            </p>
            <div className="text-xs text-slate-400 mb-4">
              {isRecommended('flashcard') && recommendation ? (
                <span className="text-purple-600 font-medium">{t(`main.recommendation.${recommendation.reason_key}`, recommendation.reason_params)}</span>
              ) : (
                t('main.flashcard.subdesc')
              )}
            </div>
            <Link to="/flashcard" className="block w-full mt-auto bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2 px-4 rounded-xl transition-all text-center">
              {t('main.flashcard.button')}
            </Link>
          </div>

          {/* Learned Words Card */}
          <div className={`card p-6 group hover:border-indigo-200 transition-colors relative flex flex-col ${cardHighlightClass('learnedWords')}`}>
            {isRecommended('learnedWords') && (
              <div className="absolute -top-2.5 left-4 px-2.5 py-0.5 bg-indigo-500 text-white text-xs font-bold rounded-full shadow-sm">
                {t('main.recommendation.recommended')}
              </div>
            )}
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-slate-800">{t('main.learnedWords.title')}</h2>
            </div>
            <p className="text-slate-500 text-sm mb-3">
              {t('main.learnedWords.desc')}
            </p>
            <div className="text-xs text-slate-400 mb-4">
              {isRecommended('learnedWords') && recommendation ? (
                <span className="text-indigo-600 font-medium">{t(`main.recommendation.${recommendation.reason_key}`, recommendation.reason_params)}</span>
              ) : (
                t('main.learnedWords.subdesc')
              )}
            </div>
            <Link to="/learned-words" className="block w-full mt-auto bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-4 rounded-xl transition-all text-center">
              {t('main.learnedWords.button')}
            </Link>
          </div>

          {/* Vocabulary Card */}
          <div className={`card p-6 group hover:border-rose-200 transition-colors relative flex flex-col ${cardHighlightClass('vocabulary')}`}>
            {isRecommended('vocabulary') && (
              <div className="absolute -top-2.5 left-4 px-2.5 py-0.5 bg-rose-500 text-white text-xs font-bold rounded-full shadow-sm">
                {t('main.recommendation.recommended')}
              </div>
            )}
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-rose-100 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-slate-800">{t('main.vocabulary.title')}</h2>
            </div>
            <p className="text-slate-500 text-sm mb-3">
              {t('main.vocabulary.desc')}
            </p>
            <div className="text-xs text-slate-400 mb-4">
              {isRecommended('vocabulary') && recommendation ? (
                <span className="text-rose-600 font-medium">{t(`main.recommendation.${recommendation.reason_key}`, recommendation.reason_params)}</span>
              ) : (
                t('main.vocabulary.subdesc')
              )}
            </div>
            <Link to="/vocabulary" className="block w-full mt-auto bg-rose-600 hover:bg-rose-700 text-white font-semibold py-2 px-4 rounded-xl transition-all text-center">
              {t('main.vocabulary.button')}
            </Link>
          </div>

          {/* Quiz Card - 단어 퀴즈 (일본어의 경우 가나 포함) */}
          <div className={`card p-6 group hover:border-emerald-200 transition-colors relative flex flex-col ${cardHighlightClass('quiz')}`}>
            {isRecommended('quiz') && (
              <div className="absolute -top-2.5 left-4 px-2.5 py-0.5 bg-emerald-500 text-white text-xs font-bold rounded-full shadow-sm">
                {t('main.recommendation.recommended')}
              </div>
            )}
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-slate-800">{t('main.quiz.title')}</h2>
            </div>
            <p className="text-slate-500 text-sm mb-3">
              {t('main.quiz.desc')}
            </p>
            <div className="text-xs text-slate-400 mb-4">
              {isRecommended('quiz') && recommendation ? (
                <span className="text-emerald-600 font-medium">{t(`main.recommendation.${recommendation.reason_key}`, recommendation.reason_params)}</span>
              ) : combinedStats && combinedStats.completed_quizzes > 0 ? (
                <span>{t('main.quizStats', { completed: combinedStats.completed_quizzes, accuracy: combinedStats.overall_accuracy?.toFixed(0) || 0 })}</span>
              ) : (
                <span>{t('dashboard.noHistory')}</span>
              )}
            </div>
            <button onClick={() => setShowWordQuizModal(true)} className="w-full mt-auto bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 px-4 rounded-xl transition-all">
              {t('dashboard.takeQuiz')}
            </button>
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
              <h2 className="text-lg font-semibold text-slate-800">{t('main.quizDashboard.title')}</h2>
            </div>
            <Link to="/word-quiz/dashboard" className="text-sm text-emerald-600 hover:text-emerald-700 font-medium">
              {t('main.quizDashboard.button')}
            </Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-5 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl border border-indigo-100/50">
              <p className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                {combinedStats?.total_questions_answered || 0}
              </p>
              <p className="text-sm text-slate-500 mt-1">{t('dashboard.solvedProblems')}</p>
            </div>
            <div className="text-center p-5 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl border border-emerald-100/50">
              <p className="text-4xl font-bold text-emerald-600">{combinedStats?.completed_quizzes || 0}</p>
              <p className="text-sm text-slate-500 mt-1">{t('dashboard.completedQuizzes')}</p>
            </div>
            <div className="text-center p-5 bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl border border-amber-100/50">
              <p className="text-4xl font-bold text-amber-600">{combinedStats?.total_correct || 0}</p>
              <p className="text-sm text-slate-500 mt-1">{t('dashboard.correctAnswers')}</p>
            </div>
            <div className="text-center p-5 bg-gradient-to-br from-rose-50 to-pink-50 rounded-2xl border border-rose-100/50">
              <p className="text-4xl font-bold text-rose-600">{combinedStats?.overall_accuracy?.toFixed(0) || 0}%</p>
              <p className="text-sm text-slate-500 mt-1">{t('main.accuracy')}</p>
            </div>
          </div>
        </div>
      </div>

      <WordQuizSettingsModal isOpen={showWordQuizModal} onClose={() => setShowWordQuizModal(false)} />
    </Layout>
  )
}
