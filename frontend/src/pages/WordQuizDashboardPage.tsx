import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { lrsWordQuizApi, lrsQuizApi } from '../services/lrsMiddleware'
import Layout from '../components/Layout'
import WordQuizSettingsModal from '../components/WordQuizSettingsModal'
import QuizSettingsModal from '../components/QuizSettingsModal'
import type { WordQuizStats, WordQuizListItem, QuizStats, GanaQuizListItem } from '../types'

export default function WordQuizDashboardPage() {
  const { profile } = useAuth()
  const { t, i18n } = useTranslation()
  const [stats, setStats] = useState<WordQuizStats | null>(null)
  const [ganaStats, setGanaStats] = useState<QuizStats | null>(null)
  const [history, setHistory] = useState<WordQuizListItem[]>([])
  const [ganaHistory, setGanaHistory] = useState<GanaQuizListItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showQuizModal, setShowQuizModal] = useState(false)
  const [showGanaQuizModal, setShowGanaQuizModal] = useState(false)
  const [showResetModal, setShowResetModal] = useState(false)
  const [resetTargetLang, setResetTargetLang] = useState<{ code: string; name: string } | null>(null)
  const [isResetting, setIsResetting] = useState(false)
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([])

  // 학습 중인 언어 코드 목록
  const learningLanguageCodes = profile?.learning_languages.map(l => l.code) ?? []

  // 선택된 언어 필터 초기화 (학습 중인 언어 목록이 바뀔 때)
  useEffect(() => {
    if (learningLanguageCodes.length > 0 && selectedLanguages.length === 0) {
      setSelectedLanguages(learningLanguageCodes)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(learningLanguageCodes)])

  const toggleLanguageFilter = (langCode: string) => {
    setSelectedLanguages(prev =>
      prev.includes(langCode)
        ? prev.filter(code => code !== langCode)
        : [...prev, langCode]
    )
  }

  // 일본어 학습 중인지 확인
  const isLearningJapanese = learningLanguageCodes.includes('ja')

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true)

      // 기본 단어 퀴즈 데이터 로드
      const promises: Promise<unknown>[] = [
        lrsWordQuizApi.getQuizStats(),
        lrsWordQuizApi.getQuizHistory({ limit: 10 }),
      ]

      // 일본어 학습 중이면 가나 퀴즈 데이터도 로드
      if (isLearningJapanese) {
        promises.push(lrsQuizApi.getQuizStats())
        promises.push(lrsQuizApi.getQuizHistory({ limit: 10 }))
      }

      const results = await Promise.all(promises)

      const statsResponse = results[0] as { data: { success: boolean; data: WordQuizStats } }
      const historyResponse = results[1] as { data: { success: boolean; data: { quizzes: WordQuizListItem[] } } }

      if (statsResponse.data.success) {
        setStats(statsResponse.data.data)
      }
      if (historyResponse.data.success) {
        setHistory(historyResponse.data.data.quizzes)
      }

      // 가나 퀴즈 데이터 처리
      if (isLearningJapanese && results.length > 2) {
        const ganaStatsResponse = results[2] as { data: { success: boolean; data: QuizStats } }
        const ganaHistoryResponse = results[3] as { data: { success: boolean; data: { quizzes: GanaQuizListItem[] } } }

        if (ganaStatsResponse.data.success) {
          setGanaStats(ganaStatsResponse.data.data)
        }
        if (ganaHistoryResponse.data.success) {
          setGanaHistory(ganaHistoryResponse.data.data.quizzes)
        }
      } else {
        setGanaStats(null)
        setGanaHistory([])
      }
    } catch {
      // Handle error silently
    } finally {
      setIsLoading(false)
    }
  }, [isLearningJapanese])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleResetClick = (langCode: string, langName: string) => {
    setResetTargetLang({ code: langCode, name: langName })
    setShowResetModal(true)
  }

  const handleResetConfirm = async () => {
    if (!resetTargetLang) return

    setIsResetting(true)
    try {
      const response = await lrsWordQuizApi.resetStats(resetTargetLang.code)
      if (response.data.success) {
        // 데이터 새로고침
        await loadData()
        setShowResetModal(false)
        setResetTargetLang(null)
      }
    } catch {
      // Handle error silently
    } finally {
      setIsResetting(false)
    }
  }

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-[calc(100vh-64px)]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600" />
        </div>
      </Layout>
    )
  }

  // 선택된 언어만 필터링 (학습 중인 언어 & 선택된 언어)
  const languageStats = stats?.language_stats
    ? Object.entries(stats.language_stats).filter(([langCode]) =>
        learningLanguageCodes.includes(langCode) && selectedLanguages.includes(langCode)
      )
    : []

  // 일본어가 선택되었는지 확인
  const isJapaneseSelected = selectedLanguages.includes('ja')

  // 가나 퀴즈 통계 (일본어 선택 시에만)
  const ganaStatsForCalc = isJapaneseSelected && ganaStats ? {
    completed_quizzes: ganaStats.completed_quizzes || 0,
    total_questions_answered: ganaStats.total_questions_answered || 0,
    total_correct: ganaStats.total_correct || 0,
  } : { completed_quizzes: 0, total_questions_answered: 0, total_correct: 0 }

  // 선택된 언어만으로 전체 통계 계산 (가나 퀴즈 포함)
  const wordQuizTotal = {
    completed_quizzes: languageStats.reduce((sum, [, ls]) => sum + (ls.quiz_count || 0), 0),
    total_questions_answered: languageStats.reduce((sum, [, ls]) => sum + (ls.total_attempts || 0), 0),
    total_correct: languageStats.reduce((sum, [, ls]) => sum + (ls.correct_count || 0), 0),
  }

  const filteredOverallStats = {
    completed_quizzes: wordQuizTotal.completed_quizzes + ganaStatsForCalc.completed_quizzes,
    total_questions_answered: wordQuizTotal.total_questions_answered + ganaStatsForCalc.total_questions_answered,
    total_correct: wordQuizTotal.total_correct + ganaStatsForCalc.total_correct,
    overall_accuracy: (wordQuizTotal.total_questions_answered + ganaStatsForCalc.total_questions_answered) > 0
      ? ((wordQuizTotal.total_correct + ganaStatsForCalc.total_correct) /
         (wordQuizTotal.total_questions_answered + ganaStatsForCalc.total_questions_answered)) * 100
      : 0,
  }

  // 히스토리도 선택된 언어로 필터링
  const filteredWordHistory = history.filter(quiz =>
    selectedLanguages.includes(quiz.learning_language_code)
  )

  // 가나 퀴즈 히스토리를 통합된 형식으로 변환
  const convertedGanaHistory = isJapaneseSelected ? ganaHistory.map(quiz => ({
    ...quiz,
    learning_language_code: 'ja',
    learning_language_name: t('dashboard.japaneseGana'),
    isGanaQuiz: true as const,
  })) : []

  // 전체 히스토리 합치기 (시간순 정렬)
  const filteredHistory = [...filteredWordHistory.map(q => ({ ...q, isGanaQuiz: false as const })), ...convertedGanaHistory]
    .sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime())
    .slice(0, 10)

  // 취약한 단어/강점 단어도 선택된 언어로 필터링
  const filteredWeakestWords = stats?.weakest_words?.filter(word =>
    selectedLanguages.includes(word.word_language)
  ) ?? []

  const filteredStrongestWords = stats?.strongest_words?.filter(word =>
    selectedLanguages.includes(word.word_language)
  ) ?? []

  // 가나 취약/강점 문자 (일본어 선택 시)
  const ganaWeakestChars = isJapaneseSelected ? (ganaStats?.weakest_characters ?? []) : []
  const ganaStrongestChars = isJapaneseSelected ? (ganaStats?.strongest_characters ?? []) : []

  return (
    <Layout>
      <div className="max-w-4xl mx-auto py-8 px-4">
        {/* Page Title */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">{t('dashboard.title')}</h1>
            <p className="text-slate-500">{t('dashboard.subtitle')}</p>
          </div>
          <div className="flex gap-2">
            {isLearningJapanese && (
              <button onClick={() => setShowGanaQuizModal(true)} className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-4 rounded-xl transition-all">
                {t('dashboard.ganaQuiz')}
              </button>
            )}
            <button onClick={() => setShowQuizModal(true)} className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 px-4 rounded-xl transition-all">
              {t('dashboard.wordQuiz')}
            </button>
          </div>
        </div>

        {/* Language Filter */}
        {profile?.learning_languages && profile.learning_languages.length > 0 && (
          <div className="card p-4 mb-6">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-slate-600">{t('dashboard.languageFilter')}</span>
              <button
                onClick={() => setSelectedLanguages(
                  selectedLanguages.length === learningLanguageCodes.length
                    ? []
                    : [...learningLanguageCodes]
                )}
                className="text-xs text-emerald-600 hover:text-emerald-700"
              >
                {selectedLanguages.length === learningLanguageCodes.length ? t('dashboard.deselectAll') : t('dashboard.selectAll')}
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {profile.learning_languages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => toggleLanguageFilter(lang.code)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                    selectedLanguages.includes(lang.code)
                      ? 'bg-emerald-100 text-emerald-700 border-2 border-emerald-300'
                      : 'bg-slate-100 text-slate-500 border-2 border-transparent hover:bg-slate-200'
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    {selectedLanguages.includes(lang.code) && (
                      <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                    {lang.name_ko}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Overall Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="card p-5 text-center">
            <p className="text-3xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
              {filteredOverallStats.completed_quizzes}
            </p>
            <p className="text-sm text-slate-500 mt-1">{t('dashboard.completedQuizzes')}</p>
          </div>
          <div className="card p-5 text-center">
            <p className="text-3xl font-bold text-blue-600">
              {filteredOverallStats.total_questions_answered}
            </p>
            <p className="text-sm text-slate-500 mt-1">{t('dashboard.solvedProblems')}</p>
          </div>
          <div className="card p-5 text-center">
            <p className="text-3xl font-bold text-amber-600">
              {filteredOverallStats.total_correct}
            </p>
            <p className="text-sm text-slate-500 mt-1">{t('dashboard.correctAnswers')}</p>
          </div>
          <div className="card p-5 text-center">
            <p className="text-3xl font-bold text-rose-600">
              {filteredOverallStats.overall_accuracy.toFixed(1)}%
            </p>
            <p className="text-sm text-slate-500 mt-1">{t('dashboard.overallAccuracy')}</p>
          </div>
        </div>

        {/* Language Stats */}
        {(languageStats.length > 0 || (isJapaneseSelected && ganaStats)) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {languageStats.map(([langCode, langStats]) => (
              <div key={langCode} className="card p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
                      <span className="text-sm font-bold text-emerald-600">{langCode.toUpperCase()}</span>
                    </div>
                    <h2 className="text-lg font-semibold text-slate-800">{langStats.language_name}</h2>
                  </div>
                  <button
                    onClick={() => handleResetClick(langCode, langStats.language_name)}
                    className="text-xs text-slate-400 hover:text-rose-500 transition-colors"
                    title={t('dashboard.resetStats')}
                  >
                    {t('dashboard.reset')}
                  </button>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-500">{t('dashboard.completedQuizzesLabel')}</span>
                    <span className="font-medium text-slate-700">{langStats.quiz_count || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-500">{t('dashboard.attemptedProblems')}</span>
                    <span className="font-medium text-slate-700">{langStats.total_attempts || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-500">{t('dashboard.correctCount')}</span>
                    <span className="font-medium text-emerald-600">{langStats.correct_count || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-500">{t('dashboard.accuracy')}</span>
                    <span className="font-medium text-emerald-600">{langStats.accuracy?.toFixed(1) || 0}%</span>
                  </div>
                </div>

                {/* 일본어인 경우 가나 퀴즈 통계 추가 (데이터가 있을 때만) */}
                {langCode === 'ja' && ganaStats && (ganaStats.completed_quizzes > 0 || ganaStats.total_questions_answered > 0) && (
                  <div className="mt-4 pt-4 border-t border-slate-100">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-bold text-indigo-600">あ</span>
                        <span className="text-sm font-medium text-slate-600">{t('dashboard.ganaQuizLabel')}</span>
                      </div>
                      <button
                        onClick={() => setShowGanaQuizModal(true)}
                        className="text-xs text-indigo-600 hover:text-indigo-700 font-medium"
                      >
                        {t('dashboard.takeQuiz')}
                      </button>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">{t('dashboard.completedQuizzesLabel')}</span>
                        <span className="font-medium text-slate-700">{ganaStats.completed_quizzes || 0}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">{t('dashboard.solvedProblems')}</span>
                        <span className="font-medium text-slate-700">{ganaStats.total_questions_answered || 0}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">{t('dashboard.accuracy')}</span>
                        <span className="font-medium text-indigo-600">{ganaStats.overall_accuracy?.toFixed(1) || 0}%</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* 일본어가 선택됐는데 단어 퀴즈 데이터가 없고 가나 퀴즈만 있는 경우 (데이터가 있을 때만) */}
            {isJapaneseSelected && ganaStats && (ganaStats.completed_quizzes > 0 || ganaStats.total_questions_answered > 0) && !languageStats.some(([code]) => code === 'ja') && (
              <div className="card p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center">
                      <span className="text-lg font-bold text-indigo-600">あ</span>
                    </div>
                    <h2 className="text-lg font-semibold text-slate-800">{t('dashboard.japaneseGana')}</h2>
                  </div>
                  <button
                    onClick={() => setShowGanaQuizModal(true)}
                    className="text-xs text-indigo-600 hover:text-indigo-700 font-medium"
                  >
                    {t('dashboard.takeQuiz')}
                  </button>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-500">{t('dashboard.completedQuizzesLabel')}</span>
                    <span className="font-medium text-slate-700">{ganaStats.completed_quizzes || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-500">{t('dashboard.solvedProblems')}</span>
                    <span className="font-medium text-slate-700">{ganaStats.total_questions_answered || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-500">{t('dashboard.correctCount')}</span>
                    <span className="font-medium text-indigo-600">{ganaStats.total_correct || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-500">{t('dashboard.accuracy')}</span>
                    <span className="font-medium text-indigo-600">{ganaStats.overall_accuracy?.toFixed(1) || 0}%</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Weakest & Strongest Words */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Weakest Words */}
          {filteredWeakestWords.length > 0 && (
            <div className="card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-rose-100 rounded-xl flex items-center justify-center">
                  <svg className="w-5 h-5 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                  </svg>
                </div>
                <h2 className="text-lg font-semibold text-slate-800">{t('dashboard.weakWords')}</h2>
              </div>
              <div className="space-y-2">
                {filteredWeakestWords.map((word, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-rose-50 rounded-xl">
                    <div className="flex items-center gap-3">
                      <span className="text-lg font-bold text-slate-700">{word.word_text}</span>
                      <span className="text-xs px-2 py-0.5 bg-rose-100 text-rose-600 rounded-full">
                        {word.word_language}
                      </span>
                    </div>
                    <span className="text-sm font-medium text-rose-600">
                      {word.accuracy.toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Strongest Words */}
          {filteredStrongestWords.length > 0 && (
            <div className="card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
                  <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </div>
                <h2 className="text-lg font-semibold text-slate-800">{t('dashboard.strongWords')}</h2>
              </div>
              <div className="space-y-2">
                {filteredStrongestWords.map((word, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-emerald-50 rounded-xl">
                    <div className="flex items-center gap-3">
                      <span className="text-lg font-bold text-slate-700">{word.word_text}</span>
                      <span className="text-xs px-2 py-0.5 bg-emerald-100 text-emerald-600 rounded-full">
                        {word.word_language}
                      </span>
                    </div>
                    <span className="text-sm font-medium text-emerald-600">
                      {word.accuracy.toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Gana Weakest Characters */}
          {ganaWeakestChars.length > 0 && (
            <div className="card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-rose-100 rounded-xl flex items-center justify-center">
                  <span className="text-lg font-bold text-rose-600">あ</span>
                </div>
                <h2 className="text-lg font-semibold text-slate-800">{t('dashboard.weakGana')}</h2>
              </div>
              <div className="space-y-2">
                {ganaWeakestChars.slice(0, 5).map((char, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-rose-50 rounded-xl">
                    <div className="flex items-center gap-3">
                      <span className="text-lg font-bold text-slate-700">{char.word_text}</span>
                      <span className="text-xs px-2 py-0.5 bg-rose-100 text-rose-600 rounded-full">
                        {char.word_pronunciation}
                      </span>
                    </div>
                    <span className="text-sm font-medium text-rose-600">
                      {char.accuracy.toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Gana Strongest Characters */}
          {ganaStrongestChars.length > 0 && (
            <div className="card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center">
                  <span className="text-lg font-bold text-indigo-600">あ</span>
                </div>
                <h2 className="text-lg font-semibold text-slate-800">{t('dashboard.strongGana')}</h2>
              </div>
              <div className="space-y-2">
                {ganaStrongestChars.slice(0, 5).map((char, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-indigo-50 rounded-xl">
                    <div className="flex items-center gap-3">
                      <span className="text-lg font-bold text-slate-700">{char.word_text}</span>
                      <span className="text-xs px-2 py-0.5 bg-indigo-100 text-indigo-600 rounded-full">
                        {char.word_pronunciation}
                      </span>
                    </div>
                    <span className="text-sm font-medium text-indigo-600">
                      {char.accuracy.toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Data Management (Reset) */}
        {profile?.learning_languages && profile.learning_languages.length > 0 && (
          <div className="card p-6 mb-8">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-800">{t('dashboard.dataManagement')}</h2>
                <p className="text-xs text-slate-400">{t('dashboard.dataManagementDesc')}</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {profile.learning_languages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => handleResetClick(lang.code, lang.name_ko)}
                  className="px-3 py-2 bg-rose-50 hover:bg-rose-100 text-rose-600 text-sm font-medium rounded-lg border border-rose-200 transition-colors flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  {t('dashboard.resetLanguage', { language: lang.name_ko })}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Recent Quiz History */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-slate-800">{t('dashboard.recentHistory')}</h2>
            </div>
          </div>

          {filteredHistory.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-slate-500 mb-4">
                {selectedLanguages.length === 0
                  ? t('dashboard.selectLanguage')
                  : t('dashboard.noHistoryForLanguage')}
              </p>
              {selectedLanguages.length > 0 && (
                <button onClick={() => setShowQuizModal(true)} className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 px-4 rounded-xl transition-all">
                  {t('dashboard.startFirstQuiz')}
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {filteredHistory.map((quiz) => {
                // 가나 퀴즈와 단어 퀴즈 URL 분기
                const quizUrl = quiz.isGanaQuiz
                  ? (quiz.is_completed ? `/quiz/result/${quiz.id}` : `/quiz/${quiz.id}`)
                  : (quiz.is_completed ? `/word-quiz/result/${quiz.id}` : `/word-quiz/${quiz.id}`)

                return (
                  <Link
                    key={`${quiz.isGanaQuiz ? 'gana' : 'word'}-${quiz.id}`}
                    to={quizUrl}
                    className="flex items-center justify-between p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors"
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        {quiz.isGanaQuiz ? (
                          <>
                            <span className="px-2 py-0.5 bg-indigo-100 text-indigo-600 text-xs font-medium rounded">{t('dashboard.gana')}</span>
                            <span className="font-medium text-slate-700">
                              {'character_set_display' in quiz ? quiz.character_set_display : t('dashboard.japaneseGana')}
                            </span>
                          </>
                        ) : (
                          <span className="font-medium text-slate-700">
                            {quiz.learning_language_name}
                          </span>
                        )}
                        <span className="text-slate-300">|</span>
                        <span className="text-sm text-slate-500">{quiz.quiz_type_display}</span>
                      </div>
                      <p className="text-xs text-slate-400">
                        {new Date(quiz.started_at).toLocaleString(i18n.language)}
                      </p>
                    </div>
                    <div className="text-right">
                      {quiz.is_completed ? (
                        <>
                          <p className={`text-lg font-bold ${
                            quiz.score_percentage >= 80
                              ? 'text-emerald-600'
                              : quiz.score_percentage >= 60
                              ? 'text-amber-600'
                              : 'text-rose-600'
                          }`}>
                            {quiz.score_percentage}%
                          </p>
                          <p className="text-xs text-slate-400">
                            {quiz.correct_count}/{quiz.total_questions}
                          </p>
                        </>
                      ) : (
                        <span className="px-3 py-1 bg-amber-100 text-amber-700 text-sm font-medium rounded-full">
                          {t('dashboard.inProgress')}
                        </span>
                      )}
                    </div>
                  </Link>
                )
              })}
            </div>
          )}
        </div>
      </div>

      <WordQuizSettingsModal isOpen={showQuizModal} onClose={() => setShowQuizModal(false)} />
      {isLearningJapanese && (
        <QuizSettingsModal isOpen={showGanaQuizModal} onClose={() => setShowGanaQuizModal(false)} />
      )}

      {/* Reset Confirmation Modal */}
      {showResetModal && resetTargetLang && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-rose-100 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-800">{t('dashboard.resetStats')}</h3>
                <p className="text-sm text-slate-500">{resetTargetLang.name}</p>
              </div>
            </div>

            <p className="text-slate-600 mb-6">
              {t('dashboard.resetConfirm', { language: resetTargetLang.name })}
              {resetTargetLang.code === 'ja' && (
                <>
                  <br />
                  <span className="text-sm text-amber-600">{t('dashboard.ganaResetWarning')}</span>
                </>
              )}
              <br />
              <span className="text-sm text-slate-400">{t('dashboard.irreversible')}</span>
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowResetModal(false)
                  setResetTargetLang(null)
                }}
                disabled={isResetting}
                className="flex-1 px-4 py-2 border-2 border-slate-200 text-slate-600 font-semibold rounded-xl hover:bg-slate-50 transition-colors disabled:opacity-50"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleResetConfirm}
                disabled={isResetting}
                className="flex-1 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-semibold rounded-xl transition-colors disabled:opacity-50"
              >
                {isResetting ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    {t('dashboard.resetting')}
                  </span>
                ) : (
                  t('dashboard.reset')
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}
