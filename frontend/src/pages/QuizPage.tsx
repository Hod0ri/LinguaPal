import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { lrsGanaQuizApi } from '../services/lrsMiddleware'
import Header from '../components/Header'
import type { GanaQuiz, CurrentQuestion, QuizProgress, QuizAnswerResponse } from '../types'

type AnswerState = 'answering' | 'correct' | 'incorrect'

export default function QuizPage() {
  const { quizId } = useParams<{ quizId: string }>()
  const navigate = useNavigate()

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
        setError('퀴즈를 찾을 수 없습니다.')
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
          setError('퀴즈를 찾을 수 없습니다.')
        } else if (err.response?.status === 403) {
          setError('이 퀴즈에 접근할 권한이 없습니다.')
        } else {
          setError('퀴즈를 불러오는데 실패했습니다.')
        }
      } else {
        setError('퀴즈를 불러오는데 실패했습니다.')
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
      setError('답변을 제출할 수 없습니다.')
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
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30">
        <Header />
        <div className="flex items-center justify-center h-[calc(100vh-64px)]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
        </div>
      </div>
    )
  }

  if (error || !quiz || !currentQuestion) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30">
        <Header />
        <div className="flex flex-col items-center justify-center h-[calc(100vh-64px)] gap-4">
          <p className="text-slate-600">{error || '퀴즈를 찾을 수 없습니다.'}</p>
          <button onClick={() => navigate('/')} className="btn-primary">
            메인으로 돌아가기
          </button>
        </div>
      </div>
    )
  }

  const isSelectType = quiz.quiz_type === 'romaji_to_gana_select'
  const progressPercent = progress ? (progress.current / progress.total) * 100 : 0

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30">
      <Header />

      <main className="max-w-2xl mx-auto py-8 px-4">
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
              정답: {progress?.correct_so_far}개
            </span>
            <span className="text-xs text-slate-500">
              정답률: {progress && progress.current > 1
                ? Math.round((progress.correct_so_far / (progress.current - 1)) * 100)
                : 0}%
            </span>
          </div>
        </div>

        {/* Question Card */}
        <div className="card p-8 mb-6">
          <div className="text-center mb-8">
            <p className="text-sm text-slate-500 mb-4">문제 {currentQuestion.question_number}</p>
            <p className="text-6xl font-bold text-slate-800 mb-2">
              {currentQuestion.question}
            </p>
            <p className="text-sm text-slate-400">
              {quiz.quiz_type === 'gana_to_romaji'
                ? '위 문자의 발음을 로마자로 입력하세요'
                : quiz.quiz_type === 'romaji_to_gana_select'
                ? '위 발음에 해당하는 문자를 선택하세요'
                : '위 발음에 해당하는 문자를 입력하세요'}
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
                  <span className="font-medium">정답입니다!</span>
                </div>
              ) : (
                <div>
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span className="font-medium">틀렸습니다</span>
                  </div>
                  <p className="text-sm">
                    정답: <span className="font-bold text-lg">{lastResult.correct_answer}</span>
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
            그만하기
          </button>
          {answerState === 'answering' ? (
            <button
              onClick={handleSubmitAnswer}
              disabled={!userAnswer.trim() || isSubmitting}
              className="flex-1 btn-primary disabled:opacity-50"
            >
              {isSubmitting ? '확인 중...' : '확인'}
            </button>
          ) : lastResult?.quiz_completed ? (
            <button
              onClick={() => navigate(`/quiz/result/${quizId}`)}
              className="flex-1 btn-primary"
            >
              결과 보기
            </button>
          ) : (
            <button
              onClick={handleNextQuestion}
              className="flex-1 btn-primary"
            >
              다음 문제
            </button>
          )}
        </div>
      </main>
    </div>
  )
}
