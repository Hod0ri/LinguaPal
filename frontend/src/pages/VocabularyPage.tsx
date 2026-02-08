import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { vocabularyApi, masterApi } from '../services/api'
import type { Vocabulary, VocabularyDetail, VocabularyCreateRequest } from '../types/vocabulary'
import type { Language } from '../types'
import NotificationModal from '../components/NotificationModal'
import Layout from '../components/Layout'
import { tts, getLanguageCode } from '../utils/textToSpeech'

export default function VocabularyPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [vocabularies, setVocabularies] = useState<Vocabulary[]>([])
  const [selectedVocabulary, setSelectedVocabulary] = useState<VocabularyDetail | null>(null)
  const [languages, setLanguages] = useState<Language[]>([])
  const [loading, setLoading] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)

  // Notification modal state
  const [notification, setNotification] = useState<{
    show: boolean
    type: 'success' | 'error' | 'warning' | 'info'
    title: string
    message: string
  }>({ show: false, type: 'info', title: '', message: '' })

  // Confirm modal state
  const [confirmModal, setConfirmModal] = useState<{
    show: boolean
    title: string
    message: string
    onConfirm: () => void
  }>({ show: false, title: '', message: '', onConfirm: () => {} })

  const showNotification = (type: 'success' | 'error' | 'warning' | 'info', title: string, message: string) => {
    setNotification({ show: true, type, title, message })
  }

  const showConfirm = (title: string, message: string, onConfirm: () => void) => {
    setConfirmModal({ show: true, title, message, onConfirm })
  }

  // 단어장 목록 조회
  const fetchVocabularies = async () => {
    try {
      setLoading(true)
      const response = await vocabularyApi.getVocabularies()
      if (response.data.success) {
        setVocabularies(response.data.data.vocabularies)
      }
    } catch (error) {
      console.error('Failed to fetch vocabularies:', error)
    } finally {
      setLoading(false)
    }
  }

  // 언어 목록 조회
  const fetchLanguages = async () => {
    try {
      const response = await masterApi.getLanguages()
      if (response.data.success) {
        setLanguages(response.data.data.languages)
      }
    } catch (error) {
      console.error('Failed to fetch languages:', error)
    }
  }

  // 단어장 상세 조회
  const fetchVocabularyDetail = async (vocabularyId: number) => {
    try {
      const response = await vocabularyApi.getVocabulary(vocabularyId)
      if (response.data.success) {
        setSelectedVocabulary(response.data.data.vocabulary)
      }
    } catch (error) {
      console.error('Failed to fetch vocabulary detail:', error)
    }
  }

  // 단어장 삭제
  const handleDeleteVocabulary = async (vocabularyId: number) => {
    showConfirm(
      t('vocabulary.deleteVocabulary'),
      t('vocabulary.deleteConfirm'),
      async () => {
        try {
          await vocabularyApi.deleteVocabulary(vocabularyId)
          fetchVocabularies()
          if (selectedVocabulary?.id === vocabularyId) {
            setSelectedVocabulary(null)
          }
          showNotification('success', t('common.confirm'), t('vocabulary.deleteSuccess'))
        } catch (error) {
          console.error('Failed to delete vocabulary:', error)
          showNotification('error', t('common.error'), t('vocabulary.deleteFailed'))
        }
      }
    )
  }

  // 단어 제거
  const handleRemoveWord = async (wordId: number) => {
    if (!selectedVocabulary) return

    showConfirm(
      t('vocabulary.removeWord'),
      t('vocabulary.removeConfirm'),
      async () => {
        try {
          await vocabularyApi.removeWord(selectedVocabulary.id, wordId)
          fetchVocabularyDetail(selectedVocabulary.id)
          fetchVocabularies() // word_count 업데이트
          showNotification('success', t('common.confirm'), t('vocabulary.removeSuccess'))
        } catch (error) {
          console.error('Failed to remove word:', error)
          showNotification('error', t('common.error'), t('vocabulary.removeFailed'))
        }
      }
    )
  }

  useEffect(() => {
    fetchVocabularies()
    fetchLanguages()
  }, [])

  return (
    <Layout>
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-slate-800">{t('vocabulary.title')}</h1>
              <p className="text-slate-500 mt-2">
                {t('vocabulary.subtitle')}
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all font-medium shadow-lg shadow-indigo-500/30 hover:shadow-xl hover:shadow-indigo-500/40 hover:-translate-y-0.5 duration-200"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              {t('vocabulary.createNew')}
            </button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 단어장 목록 */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                <h2 className="text-lg font-semibold text-slate-800 mb-4">{t('vocabulary.vocabularyList')}</h2>
                {vocabularies.length === 0 ? (
                  <p className="text-slate-500 text-center py-8">{t('vocabulary.noVocabulary')}</p>
                ) : (
                  <div className="space-y-2">
                    {vocabularies.map((vocab) => (
                      <div
                        key={vocab.id}
                        onClick={() => fetchVocabularyDetail(vocab.id)}
                        className={`p-4 rounded-lg cursor-pointer transition-colors border ${
                          selectedVocabulary?.id === vocab.id
                            ? 'bg-indigo-50 border-indigo-200'
                            : 'bg-slate-50 border-slate-100 hover:bg-slate-100'
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1 min-w-0">
                            <h3 className="font-semibold text-slate-800 truncate">{vocab.name}</h3>
                            <p className="text-sm text-slate-500 mt-1">{vocab.language_name}</p>
                            <p className="text-xs text-slate-400 mt-1">{t('common.words', { count: vocab.word_count })}</p>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteVocabulary(vocab.id)
                            }}
                            className="text-slate-400 hover:text-rose-600 transition-colors"
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                        {vocab.description && (
                          <p className="text-xs text-slate-500 mt-2 line-clamp-2">{vocab.description}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* 단어장 상세 */}
            <div className="lg:col-span-2">
              {selectedVocabulary ? (
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <h2 className="text-2xl font-bold text-slate-800">{selectedVocabulary.name}</h2>
                      <p className="text-slate-500 mt-1">{selectedVocabulary.language_name}</p>
                      {selectedVocabulary.description && (
                        <p className="text-slate-600 mt-2">{selectedVocabulary.description}</p>
                      )}
                    </div>
                    <button
                      onClick={() => setShowEditModal(true)}
                      className="px-3 py-1.5 text-sm bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
                    >
                      {t('common.edit')}
                    </button>
                  </div>

                  {/* 단어 목록 */}
                  <div className="space-y-3">
                    <h3 className="text-lg font-semibold text-slate-800">
                      {t('vocabulary.wordList', { count: selectedVocabulary.vocabulary_words.length })}
                    </h3>
                    {selectedVocabulary.vocabulary_words.length === 0 ? (
                      <p className="text-slate-500 text-center py-12">{t('vocabulary.noWords')}</p>
                    ) : (
                      <div className="space-y-2">
                        {selectedVocabulary.vocabulary_words.map((vocabWord) => (
                          <div
                            key={vocabWord.id}
                            className="p-4 bg-slate-50 rounded-lg border border-slate-100 hover:border-indigo-200 transition-all hover:shadow-sm"
                          >
                            <div className="flex justify-between items-start">
                              <div className="flex-1">
                                <div className="flex items-center gap-3">
                                  <span
                                    onClick={() => navigate(`/words?id=${vocabWord.word.id}`)}
                                    className="text-lg font-semibold text-slate-800 cursor-pointer hover:text-indigo-600 transition-colors"
                                  >
                                    {vocabWord.word.text}
                                  </span>
                                  <button
                                    onClick={() => tts.speak(vocabWord.word.text, { lang: getLanguageCode(selectedVocabulary.language_code), rate: 0.9 })}
                                    className="p-1.5 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 transition-colors"
                                    title={t('wordBrowse.listenPronunciation')}
                                  >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                      <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                                    </svg>
                                  </button>
                                  {vocabWord.word.pronunciation && (
                                    <span className="text-sm text-slate-500">
                                      {vocabWord.word.pronunciation}
                                    </span>
                                  )}
                                </div>
                                <p className="text-slate-600 mt-1">{vocabWord.word.translation}</p>

                                {/* 예문 */}
                                {vocabWord.word.example && (
                                  <div className="mt-3 p-3 bg-white rounded-lg border border-slate-100">
                                    <div className="flex items-start gap-2">
                                      <div className="flex-1">
                                        <p className="text-slate-700 text-sm">
                                          {vocabWord.word.example}
                                        </p>
                                        {vocabWord.word.example_translation && (
                                          <p className="text-slate-500 text-xs mt-1">
                                            {vocabWord.word.example_translation}
                                          </p>
                                        )}
                                      </div>
                                      <button
                                        onClick={() => tts.speak(vocabWord.word.example!, { lang: getLanguageCode(selectedVocabulary.language_code), rate: 0.85 })}
                                        className="p-1.5 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors flex-shrink-0"
                                        title={t('wordBrowse.listenExample')}
                                      >
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                          <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                                        </svg>
                                      </button>
                                    </div>
                                  </div>
                                )}

                                {vocabWord.notes && (
                                  <p className="text-sm text-indigo-600 mt-2 italic">💡 {vocabWord.notes}</p>
                                )}
                              </div>
                              <button
                                onClick={() => handleRemoveWord(vocabWord.word.id)}
                                className="text-slate-400 hover:text-rose-600 transition-colors ml-4"
                              >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-12 text-center">
                  <p className="text-slate-500">{t('vocabulary.selectVocabulary')}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 단어장 생성 모달 */}
      {showCreateModal && (
        <CreateVocabularyModal
          languages={languages}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false)
            fetchVocabularies()
            showNotification('success', t('common.confirm'), t('vocabulary.createSuccess'))
          }}
          showNotification={showNotification}
        />
      )}

      {/* 단어장 수정 모달 */}
      {showEditModal && selectedVocabulary && (
        <EditVocabularyModal
          vocabulary={selectedVocabulary}
          languages={languages}
          onClose={() => setShowEditModal(false)}
          onSuccess={() => {
            setShowEditModal(false)
            fetchVocabularies()
            if (selectedVocabulary) {
              fetchVocabularyDetail(selectedVocabulary.id)
            }
            showNotification('success', t('common.confirm'), t('vocabulary.editSuccess'))
          }}
          showNotification={showNotification}
        />
      )}

      {/* Notification Modal */}
      <NotificationModal
        isOpen={notification.show}
        onClose={() => setNotification({ ...notification, show: false })}
        type={notification.type}
        title={notification.title}
        message={notification.message}
      />

      {/* Confirm Modal */}
      {confirmModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl">
            <h3 className="font-bold text-xl mb-4 text-slate-800">{confirmModal.title}</h3>
            <p className="text-slate-600 mb-6">{confirmModal.message}</p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setConfirmModal({ ...confirmModal, show: false })}
                className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors font-medium"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={() => {
                  confirmModal.onConfirm()
                  setConfirmModal({ ...confirmModal, show: false })
                }}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
              >
                {t('common.confirm')}
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}

// 단어장 생성 모달
function CreateVocabularyModal({
  languages,
  onClose,
  onSuccess,
  showNotification,
}: {
  languages: Language[]
  onClose: () => void
  onSuccess: () => void
  showNotification: (type: 'success' | 'error' | 'warning' | 'info', title: string, message: string) => void
}) {
  const { t } = useTranslation()
  const [formData, setFormData] = useState<VocabularyCreateRequest>({
    name: '',
    description: '',
    language: languages[0]?.id || 0,
    is_active: true,
  })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name.trim()) {
      showNotification('warning', t('vocabulary.inputRequired'), t('vocabulary.nameRequired'))
      return
    }

    try {
      setLoading(true)
      await vocabularyApi.createVocabulary(formData)
      onSuccess()
    } catch (error) {
      console.error('Failed to create vocabulary:', error)
      showNotification('error', t('common.error'), t('vocabulary.createFailed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-md w-full p-6">
        <h2 className="text-2xl font-bold text-slate-800 mb-4">{t('vocabulary.createTitle')}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">{t('vocabulary.nameLabel')} *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder={t('vocabulary.namePlaceholder')}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">{t('vocabulary.descriptionLabel')}</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              rows={3}
              placeholder={t('vocabulary.descriptionPlaceholder')}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">{t('vocabulary.languageLabel')} *</label>
            <select
              value={formData.language}
              onChange={(e) => setFormData({ ...formData, language: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {languages.map((lang) => (
                <option key={lang.id} value={lang.id}>
                  {lang.name_ko}
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
            >
              {loading ? t('vocabulary.creating') : t('vocabulary.create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// 단어장 수정 모달
function EditVocabularyModal({
  vocabulary,
  languages,
  onClose,
  onSuccess,
  showNotification,
}: {
  vocabulary: VocabularyDetail
  languages: Language[]
  onClose: () => void
  onSuccess: () => void
  showNotification: (type: 'success' | 'error' | 'warning' | 'info', title: string, message: string) => void
}) {
  const { t } = useTranslation()
  const [formData, setFormData] = useState<VocabularyCreateRequest>({
    name: vocabulary.name,
    description: vocabulary.description,
    language: vocabulary.language,
    is_active: vocabulary.is_active,
  })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name.trim()) {
      showNotification('warning', t('vocabulary.inputRequired'), t('vocabulary.nameRequired'))
      return
    }

    try {
      setLoading(true)
      await vocabularyApi.updateVocabulary(vocabulary.id, formData)
      onSuccess()
    } catch (error) {
      console.error('Failed to update vocabulary:', error)
      showNotification('error', t('common.error'), t('vocabulary.editFailed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-md w-full p-6">
        <h2 className="text-2xl font-bold text-slate-800 mb-4">{t('vocabulary.editTitle')}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">{t('vocabulary.nameLabel')} *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">{t('vocabulary.descriptionLabel')}</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              rows={3}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">{t('vocabulary.languageLabel')} *</label>
            <select
              value={formData.language}
              onChange={(e) => setFormData({ ...formData, language: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {languages.map((lang) => (
                <option key={lang.id} value={lang.id}>
                  {lang.name_ko}
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
            >
              {loading ? t('vocabulary.editing') : t('common.edit')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
