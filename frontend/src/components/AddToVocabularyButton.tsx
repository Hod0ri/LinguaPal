import { useState, useEffect } from 'react'
import { vocabularyApi } from '../services/api'
import type { Vocabulary } from '../types/vocabulary'
import NotificationModal from './NotificationModal'

interface AddToVocabularyButtonProps {
  wordId: number
  wordText: string
  wordLanguageId: number
  className?: string
}

export default function AddToVocabularyButton({ wordId, wordText, wordLanguageId, className = '' }: AddToVocabularyButtonProps) {
  const [showModal, setShowModal] = useState(false)
  const [vocabularies, setVocabularies] = useState<Vocabulary[]>([])
  const [wordVocabularies, setWordVocabularies] = useState<Vocabulary[]>([])
  const [selectedVocabularyId, setSelectedVocabularyId] = useState<number>(0)
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)

  // Notification modal state
  const [notification, setNotification] = useState<{
    show: boolean
    type: 'success' | 'error' | 'warning' | 'info'
    title: string
    message: string
  }>({ show: false, type: 'info', title: '', message: '' })

  const showNotification = (type: 'success' | 'error' | 'warning' | 'info', title: string, message: string) => {
    setNotification({ show: true, type, title, message })
  }

  // 내 단어장 목록 조회 (단어 언어와 일치하는 것만)
  const fetchVocabularies = async () => {
    try {
      const response = await vocabularyApi.getVocabularies()
      if (response.data.success) {
        // Filter vocabularies to only show those matching the word's language
        const filteredVocabularies = response.data.data.vocabularies.filter(
          vocab => vocab.language === wordLanguageId
        )
        setVocabularies(filteredVocabularies)
        if (filteredVocabularies.length > 0) {
          setSelectedVocabularyId(filteredVocabularies[0].id)
        }
      }
    } catch (error) {
      console.error('Failed to fetch vocabularies:', error)
    }
  }

  // 이 단어가 속한 단어장 목록 조회
  const fetchWordVocabularies = async () => {
    try {
      const response = await vocabularyApi.getWordVocabularies(wordId)
      if (response.data.success) {
        setWordVocabularies(response.data.data.vocabularies)
      }
    } catch (error) {
      console.error('Failed to fetch word vocabularies:', error)
    }
  }

  // 단어장에 추가
  const handleAddToVocabulary = async () => {
    if (!selectedVocabularyId) {
      showNotification('warning', '선택 필요', '단어장을 선택해주세요')
      return
    }

    // 이미 추가되어 있는지 확인
    if (wordVocabularies.some(v => v.id === selectedVocabularyId)) {
      showNotification('warning', '이미 추가됨', '이미 이 단어장에 추가된 단어입니다')
      return
    }

    try {
      setLoading(true)
      await vocabularyApi.addWord(selectedVocabularyId, {
        word_id: wordId,
        notes: notes.trim(),
      })
      showNotification('success', '추가 완료', '단어장에 추가되었습니다!')
      setShowModal(false)
      setNotes('')
      fetchWordVocabularies()
    } catch (error: any) {
      console.error('Failed to add word to vocabulary:', error)
      if (error.response?.data?.error_code === 'DUPLICATE_RESOURCE') {
        showNotification('warning', '이미 추가됨', '이미 이 단어장에 추가된 단어입니다')
      } else if (error.response?.data?.error_code === 'VALIDATION_ERROR' && error.response?.data?.message?.includes('Language mismatch')) {
        showNotification('error', '언어 불일치', error.response.data.message.split(': ')[1] || '단어장 언어와 단어 언어가 일치하지 않습니다')
      } else {
        showNotification('error', '추가 실패', '단어장에 추가하는데 실패했습니다')
      }
    } finally {
      setLoading(false)
    }
  }

  // 모달 열릴 때 데이터 로드
  useEffect(() => {
    if (showModal) {
      fetchVocabularies()
      fetchWordVocabularies()
    }
  }, [showModal])

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className={`inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors ${className}`}
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        단어장에 추가
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl animate-in slide-in-from-bottom-4 duration-300">
            {/* Header with gradient */}
            <div className="bg-gradient-to-r from-indigo-500 to-purple-500 rounded-t-2xl p-6 text-white">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-xl font-bold">단어장에 추가</h2>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="px-3 py-1 bg-white/20 backdrop-blur-sm rounded-lg text-sm font-medium">
                        {wordText}
                      </span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-white/80 hover:text-white hover:bg-white/10 rounded-lg p-1 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">

            {vocabularies.length === 0 ? (
              <div className="py-12 text-center">
                <div className="w-20 h-20 mx-auto mb-4 bg-slate-100 rounded-full flex items-center justify-center">
                  <svg className="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <p className="text-slate-600 font-medium mb-2">생성된 단어장이 없습니다</p>
                <p className="text-slate-500 text-sm mb-6">먼저 단어장을 만들어주세요</p>
                <button
                  onClick={() => {
                    setShowModal(false)
                    window.location.href = '/vocabulary'
                  }}
                  className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all font-medium shadow-lg shadow-indigo-500/30"
                >
                  단어장 만들기
                </button>
              </div>
            ) : (
              <div className="space-y-5">
                {/* 이미 속한 단어장 표시 */}
                {wordVocabularies.length > 0 && (
                  <div className="p-4 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-xl border border-emerald-200">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-6 h-6 bg-emerald-500 rounded-lg flex items-center justify-center">
                        <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <p className="text-sm font-semibold text-emerald-900">이미 추가된 단어장</p>
                    </div>
                    <div className="space-y-2">
                      {wordVocabularies.map((vocab) => (
                        <div key={vocab.id} className="flex items-center gap-2 text-sm text-emerald-800 bg-white/60 px-3 py-2 rounded-lg">
                          <svg className="w-4 h-4 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span className="font-medium">{vocab.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">단어장 선택</label>
                  <div className="relative">
                    <select
                      value={selectedVocabularyId}
                      onChange={(e) => setSelectedVocabularyId(parseInt(e.target.value))}
                      className="w-full px-4 py-3 pr-10 bg-white border-2 border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all appearance-none cursor-pointer hover:border-slate-300 text-slate-800 font-medium"
                    >
                      {vocabularies.map((vocab) => {
                        const isAdded = wordVocabularies.some(v => v.id === vocab.id)
                        return (
                          <option key={vocab.id} value={vocab.id} disabled={isAdded}>
                            {vocab.name} - {vocab.word_count}개 {isAdded && '✓'}
                          </option>
                        )
                      })}
                    </select>
                    <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                      <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                    <svg className="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    메모 (선택사항)
                  </label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all resize-none"
                    rows={3}
                    placeholder="이 단어에 대한 개인적인 메모나 암기 팁을 입력하세요 💡"
                  />
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-slate-100">
                  <button
                    onClick={() => setShowModal(false)}
                    className="px-5 py-2.5 bg-slate-100 text-slate-700 rounded-xl hover:bg-slate-200 transition-colors font-medium"
                  >
                    취소
                  </button>
                  <button
                    onClick={handleAddToVocabulary}
                    disabled={loading || !selectedVocabularyId}
                    className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all font-medium shadow-lg shadow-indigo-500/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
                  >
                    {loading ? (
                      <span className="flex items-center gap-2">
                        <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        추가 중...
                      </span>
                    ) : (
                      <span className="flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                        추가
                      </span>
                    )}
                  </button>
                </div>
              </div>
            )}
            </div>
          </div>
        </div>
      )}

      {/* Notification Modal */}
      <NotificationModal
        isOpen={notification.show}
        onClose={() => setNotification({ ...notification, show: false })}
        type={notification.type}
        title={notification.title}
        message={notification.message}
      />
    </>
  )
}
