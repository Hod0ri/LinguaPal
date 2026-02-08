import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import { lrsWordQuizApi } from '../services/lrsMiddleware'
import Layout from '../components/Layout'
import type { WordQuiz, CurrentQuestion, QuizProgress, WordQuizAnswerResponse } from '../types'

type AnswerState = 'answering' | 'correct' | 'incorrect'

export default function WordQuizPage() {
  const { quizId } = useParams<{ quizId: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()

  const [quiz, setQuiz] = useState<WordQuiz | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState<CurrentQuestion | null>(null)
  const [progress, setProgress] = useState<QuizProgress | null>(null)
  const [userAnswer, setUserAnswer] = useState('')
  const [answerState, setAnswerState] = useState<AnswerState>('answering')
  const [lastResult, setLastResult] = useState<WordQuizAnswerResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadQuiz = useCallback(async () => {
    if (!quizId) return

    try {
      setIsLoading(true)
      const quizResponse = await lrsWordQuizApi.getQuizDetail(parseInt(quizId))

      if (!quizResponse.data.success) {
        setError(t('wordQuiz.notFound'))
        return
      }

      const quizData = quizResponse.data.data
      setQuiz(quizData)

      if (quizData.is_completed) {
        navigate(`/word-quiz/result/${quizId}`, { replace: true })
        return
      }

      try {
        const questionResponse = await lrsWordQuizApi.getCurrentQuestion(parseInt(quizId))
        if (questionResponse.data.success) {
          setCurrentQuestion(questionResponse.data.data.question)
          setProgress(questionResponse.data.data.progress)
        }
      } catch (questionErr) {
        if (axios.isAxiosError(questionErr) && questionErr.response?.status === 400) {
          navigate(`/word-quiz/result/${quizId}`, { replace: true })
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
      const response = await lrsWordQuizApi.submitAnswer(parseInt(quizId), {
        question_id: currentQuestion.id,
        answer: userAnswer.trim(),
      })

      if (response.data.success) {
        const result = response.data.data
        setLastResult(result)
        setAnswerState(result.is_correct ? 'correct' : 'incorrect')

        if (result.quiz_completed) {
          setTimeout(() => {
            navigate(`/word-quiz/result/${quizId}`)
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
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600" />
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

  // For mixed quiz type, determine question type dynamically
  const isMixedQuiz = quiz.quiz_type === 'mixed'
  const isCurrentQuestionExample = currentQuestion.question.includes('Example:')
  const isSelectType = quiz.quiz_type === 'native_to_word_select' ||
                       quiz.quiz_type === 'example_fill_in_blank' ||
                       (isMixedQuiz && currentQuestion.choices && currentQuestion.choices.length > 0)
  const isExampleFillType = quiz.quiz_type === 'example_fill_in_blank' ||
                            (isMixedQuiz && isCurrentQuestionExample)
  const progressPercent = progress ? (progress.current / progress.total) * 100 : 0

  const getQuizTypeDescription = () => {
    // For mixed quiz, determine description based on current question
    if (isMixedQuiz) {
      if (isCurrentQuestionExample) {
        return t('wordQuiz.selectFillBlank')
      } else if (currentQuestion.choices && currentQuestion.choices.length > 0) {
        return t('wordQuiz.selectWord', { native: quiz.native_language_name, learning: quiz.learning_language_name })
      } else {
        // Determine if it's word_to_native or native_to_word_input based on question content
        // Check if question contains Korean characters (Hangul)
        const hasKorean = /[ㄱ-ㅎ|ㅏ-ㅣ|가-힣]/.test(currentQuestion.question)
        if (hasKorean) {
          // Question is in native language (Korean) -> user needs to input in learning language
          return t('wordQuiz.inputWordFromNative', { native: quiz.native_language_name, learning: quiz.learning_language_name })
        } else {
          // Question is in learning language -> user needs to input in native language
          return t('wordQuiz.inputMeaning', { learning: quiz.learning_language_name, native: quiz.native_language_name })
        }
      }
    }

    switch (quiz.quiz_type) {
      case 'word_to_native':
        return t('wordQuiz.inputMeaning', { learning: quiz.learning_language_name, native: quiz.native_language_name })
      case 'native_to_word_select':
        return t('wordQuiz.selectWord', { native: quiz.native_language_name, learning: quiz.learning_language_name })
      case 'native_to_word_input':
        return t('wordQuiz.inputWordFromNative', { native: quiz.native_language_name, learning: quiz.learning_language_name })
      case 'example_fill_in_blank':
        return t('wordQuiz.selectFillBlank')
      default:
        return ''
    }
  }

  // Parse example fill-in-blank question format
  // Expected format: "Example: <sentence with ___>\nTranslation: <translation>"
  const parseExampleQuestion = (questionText: string) => {
    const parts = questionText.split('\n')
    const example = parts.find(p => p.startsWith('Example:'))?.replace('Example:', '').trim() || ''
    const translation = parts.find(p => p.startsWith('Translation:'))?.replace('Translation:', '').trim() || ''
    return { example, translation }
  }

  return (
    <Layout>
      <div className="max-w-2xl mx-auto py-8 px-4">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-600">
              {quiz.learning_language_name} - {quiz.quiz_type_display}
            </span>
            <span className="text-sm font-medium text-emerald-600">
              {progress?.current} / {progress?.total}
            </span>
          </div>
          <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <div className="flex justify-between mt-2">
            <span className="text-xs text-slate-500">
              {t('wordQuiz.correctCount', { count: progress?.correct_so_far })}
            </span>
            <span className="text-xs text-slate-500">
              {t('wordQuiz.accuracy') + ":"} {progress && progress.current > 1
                ? Math.round((progress.correct_so_far / (progress.current - 1)) * 100)
                : 0}%
            </span>
          </div>
        </div>

        <div className="card p-8 mb-6">
          <div className="text-center mb-8">
            <p className="text-sm text-slate-500 mb-4">{t('wordQuiz.question', { number: currentQuestion.question_number })}</p>
            {isExampleFillType ? (
              <div>
                {(() => {
                  const { example, translation } = parseExampleQuestion(currentQuestion.question)
                  return (
                    <>
                      <div className="bg-indigo-50 p-6 rounded-xl mb-4">
                        <p className="text-2xl font-bold text-slate-800 mb-3">
                          {example}
                        </p>
                        <p className="text-lg text-slate-600">
                          {translation}
                        </p>
                      </div>
                      <p className="text-sm text-slate-400">
                        {getQuizTypeDescription()}
                      </p>
                    </>
                  )
                })()}
              </div>
            ) : (
              <>
                <p className="text-4xl font-bold text-slate-800 mb-2">
                  {currentQuestion.question}
                </p>
                <p className="text-sm text-slate-400">
                  {getQuizTypeDescription()}
                </p>
              </>
            )}
          </div>

          {isSelectType ? (
            <div className="grid grid-cols-1 gap-3">
              {currentQuestion.choices?.map((choice, index) => (
                <button
                  key={index}
                  onClick={() => handleSelectChoice(choice)}
                  disabled={answerState !== 'answering'}
                  className={`p-4 rounded-xl border-2 text-xl font-medium transition-all ${
                    answerState === 'answering'
                      ? userAnswer === choice
                        ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
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
            <div>
              <input
                type="text"
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={answerState !== 'answering'}
                placeholder={
                  quiz.quiz_type === 'word_to_native'
                    ? t('wordQuiz.inputNative', { language: quiz.native_language_name })
                    : t('wordQuiz.inputWord', { language: quiz.learning_language_name })
                }
                className={`w-full p-4 text-center text-2xl rounded-xl border-2 transition-all focus:outline-none ${
                  answerState === 'answering'
                    ? 'border-slate-200 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100'
                    : answerState === 'correct'
                    ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                    : 'border-red-500 bg-red-50 text-red-700'
                }`}
                autoFocus
              />
            </div>
          )}

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
                    {t('wordQuiz.answer') + ": "}<span className="font-bold text-lg">{lastResult.correct_answer}</span>
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

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
              className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? t('wordQuiz.checking') : t('wordQuiz.submit')}
            </button>
          ) : lastResult?.quiz_completed ? (
            <button
              onClick={() => navigate(`/word-quiz/result/${quizId}`)}
              className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg hover:shadow-xl"
            >
              {t('wordQuiz.viewResult')}
            </button>
          ) : (
            <button
              onClick={handleNextQuestion}
              className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg hover:shadow-xl"
            >
              {t('wordQuiz.nextQuestion')}
            </button>
          )}
        </div>
      </div>
    </Layout>
  )
}
