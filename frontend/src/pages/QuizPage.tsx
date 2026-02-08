import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import { lrsGanaQuizApi } from '../services/lrsMiddleware'
import Layout from '../components/Layout'
import type { GanaQuiz, CurrentQuestion, QuizProgress, QuizAnswerResponse } from '../types'

type AnswerState = 'answering' | 'correct' | 'incorrect'

export default function QuizPage() {
  const { quizId } = useParams<{ quizId: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()

  const [quiz, setQuiz] = useState<GanaQuiz | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState<CurrentQuestion | null>(null)
  const [progress, setProgress] = useState<QuizProgress | null>(null)
  const [userAnswer, setUserAnswer] = useState('')
  const [answerState, setAnswerState] = useState<AnswerState>('answering')
  const [lastResult, setLastResult] = useState<QuizAnswerResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadQuiz = useCallback(async () => {
    if (!quizId) return

    try {
      setIsLoading(true)

      // 먼저 퀴즈 상세 정보 조회
      const quizResponse = await lrsGanaQuizApi.getQuizDetail(parseInt(quizId))

      if (!quizResponse.data.success) {
        setError(t('wordQuiz.notFound'))
        return
      }

      const quizData = quizResponse.data.data
      setQuiz(quizData)

      // 이미 완료된 퀴즈면 결과 페이지로 이동
      if (quizData.is_completed) {
        navigate(`/quiz/result/${quizId}`, { replace: true })
        return
      }

      // 현재 문제 조회
      try {
        const questionResponse = await lrsGanaQuizApi.getCurrentQuestion(parseInt(quizId))
        if (questionResponse.data.success) {
          setCurrentQuestion(questionResponse.data.data.question)
          setProgress(questionResponse.data.data.progress)
        }
      } catch (questionErr) {
        if (axios.isAxiosError(questionErr) && questionErr.response?.status === 400) {
          // 퀴즈가 이미 완료됨 - 결과 페이지로 이동
          navigate(`/quiz/result/${quizId}`, { replace: true })
          return
        }
        throw questionErr
      }
    } catch (err) {
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 404) {
          setError(t('wordQuiz.notFound'))
        } else if (err.response?.status === 403) {
          setError(t('wordQuiz.noPermission'))
        } else {
          setError(t('wordQuiz.loadFailed'))
        }
      } else {
        setError(t('wordQuiz.loadFailed'))
      }
    } finally {
      setIsLoading(false)
    }
  }, [quizId, navigate])

  useEffect(() => {
    loadQuiz()
  }, [loadQuiz])

  const handleSubmitAnswer = async () => {
    if (!quizId || !currentQuestion || !userAnswer.trim()) return

    setIsSubmitting(true)
    try {
      const response = await lrsGanaQuizApi.submitAnswer(parseInt(quizId), {
        question_id: currentQuestion.id,
        answer: userAnswer.trim(),
      })

      if (response.data.success) {
        const result = response.data.data
        setLastResult(result)
        setAnswerState(result.is_correct ? 'correct' : 'incorrect')

        if (result.quiz_completed) {
          // Navigate to result page after showing feedback
          setTimeout(() => {
            navigate(`/quiz/result/${quizId}`)
          }, 1500)
        }
      }
    } catch {
      setError(t('wordQuiz.submitFailed'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleNextQuestion = () => {
    if (lastResult?.next_question) {
      setCurrentQuestion(lastResult.next_question)
      setProgress((prev) =>
        prev
          ? {
              ...prev,
              current: prev.current + 1,
              correct_so_far: lastResult.is_correct ? prev.correct_so_far + 1 : prev.correct_so_far,
            }
          : null
      )
    }
    setUserAnswer('')
    setAnswerState('answering')
    setLastResult(null)
  }

  const handleSelectChoice = (choice: string) => {
    if (answerState !== 'answering') return
    setUserAnswer(choice)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && userAnswer.trim()) {
      if (answerState === 'answering') {
        handleSubmitAnswer()
      } else if (!lastResult?.quiz_completed) {
        handleNextQuestion()
      }
    }
  }

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-[calc(100vh-64px)]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
        </div>
      </Layout>
    )
  }

  if (error || !quiz || !currentQuestion) {
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

  const isSelectType = quiz.quiz_type === 'romaji_to_gana_select'
  const progressPercent = progress ? (progress.current / progress.total) * 100 : 0

  return (
    <Layout>
      <div className="max-w-2xl mx-auto py-8 px-4">
        {/* Quiz Info */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-600">
              {quiz.character_set_display} - {quiz.quiz_type_display}
            </span>
            <span className="text-sm font-medium text-indigo-600">
              {progress?.current} / {progress?.total}
            </span>
          </div>
          {/* Progress Bar */}
          <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <div className="flex justify-between mt-2">
            <span className="text-xs text-slate-500">
              {t('wordQuiz.correctCount', { count: progress?.correct_so_far })}
            </span>
            <span className="text-xs text-slate-500">
              {t('wordQuiz.accuracy') + ':'} {progress && progress.current > 1
                ? Math.round((progress.correct_so_far / (progress.current - 1)) * 100)
                : 0}%
            </span>
          </div>
        </div>

        {/* Question Card */}
        <div className="card p-8 mb-6">
          <div className="text-center mb-8">
            <p className="text-sm text-slate-500 mb-4">{t('wordQuiz.question', { number: currentQuestion.question_number })}</p>
            <p className="text-6xl font-bold text-slate-800 mb-2">
              {currentQuestion.question}
            </p>
            <p className="text-sm text-slate-400">
              {quiz.quiz_type === 'gana_to_romaji'
                ? t('quiz.enterRomaji')
                : quiz.quiz_type === 'romaji_to_gana_select'
                ? t('quiz.selectCharacter')
                : t('quiz.enterCharacter')}
            </p>
          </div>

          {/* Answer Section */}
          {isSelectType ? (
            /* Multiple Choice */
            <div className="grid grid-cols-1 gap-3">
              {currentQuestion.choices?.map((choice, index) => (
                <button
                  key={index}
                  onClick={() => handleSelectChoice(choice)}
                  disabled={answerState !== 'answering'}
                  className={`p-4 rounded-xl border-2 text-2xl font-medium transition-all ${
                    answerState === 'answering'
                      ? userAnswer === choice
                        ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                        : 'border-slate-200 hover:border-slate-300 text-slate-700'
                      : answerState === 'correct' && choice === lastResult?.correct_answer
                      ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                      : answerState === 'incorrect' && choice === userAnswer
                      ? 'border-red-500 bg-red-50 text-red-700'
                      : answerState === 'incorrect' && choice === lastResult?.correct_answer
                      ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                      : 'border-slate-200 text-slate-400'
                  }`}
                >
                  {choice}
                </button>
              ))}
            </div>
          ) : (
            /* Text Input */
            <div>
              <input
                type="text"
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={answerState !== 'answering'}
                placeholder={
                  quiz.quiz_type === 'gana_to_romaji'
                    ? 'ex) a, ka, sa...'
                    : 'ex) あ, か, さ...'
                }
                className={`w-full p-4 text-center text-2xl rounded-xl border-2 transition-all focus:outline-none ${
                  answerState === 'answering'
                    ? 'border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100'
                    : answerState === 'correct'
                    ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                    : 'border-red-500 bg-red-50 text-red-700'
                }`}
                autoFocus
              />
            </div>
          )}

          {/* Feedback */}
          {answerState !== 'answering' && lastResult && (
            <div
              className={`mt-4 p-4 rounded-xl text-center ${
                answerState === 'correct'
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'bg-red-50 text-red-700'
              }`}
            >
              {answerState === 'correct' ? (
                <div className="flex items-center justify-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="font-medium">{t('wordQuiz.correctAnswer')}</span>
                </div>
              ) : (
                <div>
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span className="font-medium">{t('wordQuiz.incorrectAnswer')}</span>
                  </div>
                  <p className="text-sm">
                    {t('wordQuiz.answer') + ':'} <span className="font-bold text-lg">{lastResult.correct_answer}</span>
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={() => navigate('/')}
            className="flex-1 btn-secondary"
          >
            {t('wordQuiz.quit')}
          </button>
          {answerState === 'answering' ? (
            <button
              onClick={handleSubmitAnswer}
              disabled={!userAnswer.trim() || isSubmitting}
              className="flex-1 btn-primary disabled:opacity-50"
            >
              {isSubmitting ? t('wordQuiz.checking') : t('wordQuiz.submit')}
            </button>
          ) : lastResult?.quiz_completed ? (
            <button
              onClick={() => navigate(`/quiz/result/${quizId}`)}
              className="flex-1 btn-primary"
            >
              {t('wordQuiz.viewResult')}
            </button>
          ) : (
            <button
              onClick={handleNextQuestion}
              className="flex-1 btn-primary"
            >
              {t('wordQuiz.nextQuestion')}
            </button>
          )}
        </div>
      </div>
    </Layout>
  )
}
