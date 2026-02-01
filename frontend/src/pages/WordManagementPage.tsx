import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { wordApi, wordTranslationApi, wordExampleApi } from '../services/wordApi'
import { masterApi } from '../services/api'
import type {
  Word,
  WordListItem,
  WordListParams,
  WordCreateRequest,
  WordUpdateRequest,
  WordCategory,
  PartOfSpeech,
  Language,
  WordTranslation,
  WordExample,
  WordTranslationCreate,
  WordExampleCreate,
  ExampleTranslationCreate,
} from '../types'
import {
  WORD_CATEGORY_OPTIONS,
  PART_OF_SPEECH_OPTIONS,
  DIFFICULTY_OPTIONS,
} from '../types/word'

// ============= Modal Component =============
function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
}: {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
}) {
  if (!isOpen) return null

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="fixed inset-0 bg-black/50" onClick={onClose} />
        <div className={`relative bg-white rounded-2xl shadow-xl w-full ${sizeClasses[size]} max-h-[90vh] overflow-hidden flex flex-col`}>
          <div className="flex items-center justify-between p-4 border-b border-slate-200">
            <h2 className="text-lg font-semibold text-slate-800">{title}</h2>
            <button
              onClick={onClose}
              className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}

// ============= Word Form Component =============
function WordForm({
  word,
  languages,
  onSubmit,
  onCancel,
  isLoading,
}: {
  word?: Word | null
  languages: Language[]
  onSubmit: (data: WordCreateRequest | WordUpdateRequest) => void
  onCancel: () => void
  isLoading: boolean
}) {
  const [formData, setFormData] = useState({
    language_id: word?.language || languages[0]?.id || 0,
    category: (word?.category || 'word') as WordCategory,
    text: word?.text || '',
    part_of_speech: (word?.part_of_speech || 'noun') as PartOfSpeech,
    pronunciation: word?.pronunciation || '',
    grammar: word?.grammar || {},
    order: word?.order || 0,
    difficulty_level: word?.difficulty_level || 1,
    is_active: word?.is_active ?? true,
  })

  const [grammarText, setGrammarText] = useState(
    word?.grammar ? JSON.stringify(word.grammar, null, 2) : '{}'
  )

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    let grammar = {}
    try {
      grammar = JSON.parse(grammarText)
    } catch {
      // ignore invalid JSON
    }

    if (word) {
      // Update - don't send language_id
      const updateData: WordUpdateRequest = {
        category: formData.category,
        text: formData.text,
        part_of_speech: formData.part_of_speech,
        pronunciation: formData.pronunciation,
        grammar,
        order: formData.order,
        difficulty_level: formData.difficulty_level,
        is_active: formData.is_active,
      }
      onSubmit(updateData)
    } else {
      // Create
      const createData: WordCreateRequest = {
        ...formData,
        grammar,
      }
      onSubmit(createData)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Language (only for create) */}
      {!word && (
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">언어 *</label>
          <select
            value={formData.language_id}
            onChange={(e) => setFormData({ ...formData, language_id: Number(e.target.value) })}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            required
          >
            {languages.map((lang) => (
              <option key={lang.id} value={lang.id}>
                {lang.name_ko} ({lang.code})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Category & Part of Speech */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">카테고리 *</label>
          <select
            value={formData.category}
            onChange={(e) => setFormData({ ...formData, category: e.target.value as WordCategory })}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            required
          >
            {WORD_CATEGORY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">품사 *</label>
          <select
            value={formData.part_of_speech}
            onChange={(e) => setFormData({ ...formData, part_of_speech: e.target.value as PartOfSpeech })}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            required
          >
            {PART_OF_SPEECH_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Text & Pronunciation */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">단어 *</label>
          <input
            type="text"
            value={formData.text}
            onChange={(e) => setFormData({ ...formData, text: e.target.value })}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">발음</label>
          <input
            type="text"
            value={formData.pronunciation}
            onChange={(e) => setFormData({ ...formData, pronunciation: e.target.value })}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="예: [hana], はな"
          />
        </div>
      </div>

      {/* Difficulty & Order */}
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">난이도</label>
          <select
            value={formData.difficulty_level}
            onChange={(e) => setFormData({ ...formData, difficulty_level: Number(e.target.value) })}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            {DIFFICULTY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">정렬 순서</label>
          <input
            type="number"
            value={formData.order}
            onChange={(e) => setFormData({ ...formData, order: Number(e.target.value) })}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            min={0}
          />
        </div>
        <div className="flex items-end">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
            />
            <span className="text-sm text-slate-700">활성화</span>
          </label>
        </div>
      </div>

      {/* Grammar (JSON) */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">
          문법 속성 (JSON)
        </label>
        <textarea
          value={grammarText}
          onChange={(e) => setGrammarText(e.target.value)}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm"
          rows={3}
          placeholder='{"romanji": "hana", "row": "ha"}'
        />
        <p className="text-xs text-slate-400 mt-1">동사변화, 로마자(romanji), 행(row) 등</p>
      </div>

      {/* Buttons */}
      <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200"
          disabled={isLoading}
        >
          취소
        </button>
        <button
          type="submit"
          className="px-4 py-2 text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          disabled={isLoading}
        >
          {isLoading ? '저장 중...' : word ? '수정' : '추가'}
        </button>
      </div>
    </form>
  )
}

// ============= Translation Form Component =============
function TranslationForm({
  translation,
  languages,
  onSubmit,
  onCancel,
  isLoading,
}: {
  translation?: WordTranslation | null
  languages: Language[]
  onSubmit: (data: WordTranslationCreate) => void
  onCancel: () => void
  isLoading: boolean
}) {
  const [formData, setFormData] = useState({
    language_id: translation?.language || languages[0]?.id || 0,
    translated_text: translation?.translated_text || '',
    notes: translation?.notes || '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">번역 언어 *</label>
        <select
          value={formData.language_id}
          onChange={(e) => setFormData({ ...formData, language_id: Number(e.target.value) })}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          required
          disabled={!!translation}
        >
          {languages.map((lang) => (
            <option key={lang.id} value={lang.id}>
              {lang.name_ko} ({lang.code})
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">번역 *</label>
        <input
          type="text"
          value={formData.translated_text}
          onChange={(e) => setFormData({ ...formData, translated_text: e.target.value })}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          required
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">메모</label>
        <textarea
          value={formData.notes}
          onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          rows={2}
          placeholder="추가 설명이나 뉘앙스"
        />
      </div>
      <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
        <button type="button" onClick={onCancel} className="px-4 py-2 text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200" disabled={isLoading}>
          취소
        </button>
        <button type="submit" className="px-4 py-2 text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50" disabled={isLoading}>
          {isLoading ? '저장 중...' : translation ? '수정' : '추가'}
        </button>
      </div>
    </form>
  )
}

// ============= Example Form Component =============
function ExampleForm({
  example,
  languages,
  onSubmit,
  onCancel,
  isLoading,
}: {
  example?: WordExample | null
  languages: Language[]
  onSubmit: (data: WordExampleCreate) => void
  onCancel: () => void
  isLoading: boolean
}) {
  const [sentence, setSentence] = useState(example?.sentence || '')
  const [translations, setTranslations] = useState<ExampleTranslationCreate[]>(
    example?.translations?.map((t) => ({
      language_id: t.language,
      translated_sentence: t.translated_sentence,
    })) || []
  )

  const addTranslation = () => {
    const availableLang = languages.find((l) => !translations.some((t) => t.language_id === l.id))
    if (availableLang) {
      setTranslations([...translations, { language_id: availableLang.id, translated_sentence: '' }])
    }
  }

  const removeTranslation = (index: number) => {
    setTranslations(translations.filter((_, i) => i !== index))
  }

  const updateTranslation = (index: number, field: keyof ExampleTranslationCreate, value: string | number) => {
    const updated = [...translations]
    updated[index] = { ...updated[index], [field]: value }
    setTranslations(updated)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      sentence,
      translations: translations.filter((t) => t.translated_sentence.trim()),
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">예문 *</label>
        <textarea
          value={sentence}
          onChange={(e) => setSentence(e.target.value)}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          rows={2}
          required
          placeholder="예문을 입력하세요"
        />
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-slate-700">예문 번역</label>
          <button
            type="button"
            onClick={addTranslation}
            className="text-sm text-indigo-600 hover:text-indigo-700"
            disabled={translations.length >= languages.length}
          >
            + 번역 추가
          </button>
        </div>
        <div className="space-y-3">
          {translations.map((trans, index) => (
            <div key={index} className="flex gap-2">
              <select
                value={trans.language_id}
                onChange={(e) => updateTranslation(index, 'language_id', Number(e.target.value))}
                className="w-32 px-2 py-2 border border-slate-300 rounded-lg text-sm"
              >
                {languages.map((lang) => (
                  <option key={lang.id} value={lang.id}>
                    {lang.name_ko}
                  </option>
                ))}
              </select>
              <input
                type="text"
                value={trans.translated_sentence}
                onChange={(e) => updateTranslation(index, 'translated_sentence', e.target.value)}
                className="flex-1 px-3 py-2 border border-slate-300 rounded-lg"
                placeholder="번역된 예문"
              />
              <button
                type="button"
                onClick={() => removeTranslation(index)}
                className="p-2 text-rose-500 hover:bg-rose-50 rounded-lg"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
        <button type="button" onClick={onCancel} className="px-4 py-2 text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200" disabled={isLoading}>
          취소
        </button>
        <button type="submit" className="px-4 py-2 text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50" disabled={isLoading}>
          {isLoading ? '저장 중...' : example ? '수정' : '추가'}
        </button>
      </div>
    </form>
  )
}

// ============= Word Detail Panel =============
function WordDetailPanel({
  word,
  languages,
  onClose,
  onRefresh,
}: {
  word: Word
  languages: Language[]
  onClose: () => void
  onRefresh: () => void
}) {
  const [isAddingTranslation, setIsAddingTranslation] = useState(false)
  const [editingTranslation, setEditingTranslation] = useState<WordTranslation | null>(null)
  const [isAddingExample, setIsAddingExample] = useState(false)
  const [editingExample, setEditingExample] = useState<WordExample | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleAddTranslation = async (data: WordTranslationCreate) => {
    setIsLoading(true)
    try {
      await wordTranslationApi.create(word.id, data)
      setIsAddingTranslation(false)
      onRefresh()
    } catch (error) {
      console.error('Failed to add translation:', error)
      alert('번역 추가에 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleUpdateTranslation = async (data: WordTranslationCreate) => {
    if (!editingTranslation) return
    setIsLoading(true)
    try {
      await wordTranslationApi.update(word.id, editingTranslation.id, data)
      setEditingTranslation(null)
      onRefresh()
    } catch (error) {
      console.error('Failed to update translation:', error)
      alert('번역 수정에 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteTranslation = async (translationId: number) => {
    if (!confirm('이 번역을 삭제하시겠습니까?')) return
    try {
      await wordTranslationApi.delete(word.id, translationId)
      onRefresh()
    } catch (error) {
      console.error('Failed to delete translation:', error)
      alert('번역 삭제에 실패했습니다.')
    }
  }

  const handleAddExample = async (data: WordExampleCreate) => {
    setIsLoading(true)
    try {
      await wordExampleApi.create(word.id, data)
      setIsAddingExample(false)
      onRefresh()
    } catch (error) {
      console.error('Failed to add example:', error)
      alert('예문 추가에 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleUpdateExample = async (data: WordExampleCreate) => {
    if (!editingExample) return
    setIsLoading(true)
    try {
      await wordExampleApi.update(word.id, editingExample.id, { sentence: data.sentence })
      // Handle translations separately if needed
      setEditingExample(null)
      onRefresh()
    } catch (error) {
      console.error('Failed to update example:', error)
      alert('예문 수정에 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteExample = async (exampleId: number) => {
    if (!confirm('이 예문을 삭제하시겠습니까?')) return
    try {
      await wordExampleApi.delete(word.id, exampleId)
      onRefresh()
    } catch (error) {
      console.error('Failed to delete example:', error)
      alert('예문 삭제에 실패했습니다.')
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">{word.text}</h2>
          <p className="text-slate-500">
            {word.language_name} | {word.category_display} | {word.part_of_speech_display}
          </p>
        </div>
        <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Word Info */}
      <div className="grid grid-cols-2 gap-4 mb-6 p-4 bg-slate-50 rounded-xl">
        <div>
          <span className="text-xs text-slate-500">발음</span>
          <p className="text-slate-700">{word.pronunciation || '-'}</p>
        </div>
        <div>
          <span className="text-xs text-slate-500">난이도</span>
          <p className="text-slate-700">{word.difficulty_level}</p>
        </div>
        {word.grammar && Object.keys(word.grammar).length > 0 && (
          <div className="col-span-2">
            <span className="text-xs text-slate-500">문법 속성</span>
            <pre className="text-sm text-slate-700 bg-white p-2 rounded mt-1 overflow-auto">
              {JSON.stringify(word.grammar, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Translations Section */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-slate-800">번역 ({word.translations.length})</h3>
          <button
            onClick={() => setIsAddingTranslation(true)}
            className="text-sm text-indigo-600 hover:text-indigo-700"
          >
            + 번역 추가
          </button>
        </div>

        {isAddingTranslation && (
          <div className="mb-4 p-4 bg-indigo-50 rounded-xl">
            <TranslationForm
              languages={languages}
              onSubmit={handleAddTranslation}
              onCancel={() => setIsAddingTranslation(false)}
              isLoading={isLoading}
            />
          </div>
        )}

        {editingTranslation && (
          <Modal isOpen={true} onClose={() => setEditingTranslation(null)} title="번역 수정">
            <TranslationForm
              translation={editingTranslation}
              languages={languages}
              onSubmit={handleUpdateTranslation}
              onCancel={() => setEditingTranslation(null)}
              isLoading={isLoading}
            />
          </Modal>
        )}

        <div className="space-y-2">
          {word.translations.map((trans) => (
            <div key={trans.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div>
                <span className="text-xs text-slate-500 mr-2">{trans.language_name}</span>
                <span className="text-slate-800">{trans.translated_text}</span>
                {trans.notes && <p className="text-xs text-slate-400 mt-1">{trans.notes}</p>}
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => setEditingTranslation(trans)}
                  className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </button>
                <button
                  onClick={() => handleDeleteTranslation(trans.id)}
                  className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
          {word.translations.length === 0 && !isAddingTranslation && (
            <p className="text-center text-slate-400 py-4">번역이 없습니다</p>
          )}
        </div>
      </div>

      {/* Examples Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-slate-800">예문 ({word.examples.length})</h3>
          <button
            onClick={() => setIsAddingExample(true)}
            className="text-sm text-indigo-600 hover:text-indigo-700"
          >
            + 예문 추가
          </button>
        </div>

        {isAddingExample && (
          <div className="mb-4 p-4 bg-indigo-50 rounded-xl">
            <ExampleForm
              languages={languages}
              onSubmit={handleAddExample}
              onCancel={() => setIsAddingExample(false)}
              isLoading={isLoading}
            />
          </div>
        )}

        {editingExample && (
          <Modal isOpen={true} onClose={() => setEditingExample(null)} title="예문 수정" size="lg">
            <ExampleForm
              example={editingExample}
              languages={languages}
              onSubmit={handleUpdateExample}
              onCancel={() => setEditingExample(null)}
              isLoading={isLoading}
            />
          </Modal>
        )}

        <div className="space-y-3">
          {word.examples.map((example) => (
            <div key={example.id} className="p-4 bg-slate-50 rounded-lg">
              <div className="flex items-start justify-between">
                <p className="text-slate-800 font-medium">{example.sentence}</p>
                <div className="flex gap-1 ml-2">
                  <button
                    onClick={() => setEditingExample(example)}
                    className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleDeleteExample(example.id)}
                    className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
              {example.translations.length > 0 && (
                <div className="mt-2 pl-4 border-l-2 border-slate-200 space-y-1">
                  {example.translations.map((trans) => (
                    <p key={trans.id} className="text-sm text-slate-600">
                      <span className="text-xs text-slate-400 mr-2">{trans.language_name}</span>
                      {trans.translated_sentence}
                    </p>
                  ))}
                </div>
              )}
            </div>
          ))}
          {word.examples.length === 0 && !isAddingExample && (
            <p className="text-center text-slate-400 py-4">예문이 없습니다</p>
          )}
        </div>
      </div>
    </div>
  )
}

// ============= Main Page Component =============
export default function WordManagementPage() {
  const { user } = useAuth()
  const [words, setWords] = useState<WordListItem[]>([])
  const [languages, setLanguages] = useState<Language[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [filters, setFilters] = useState<WordListParams>({
    page: 1,
    page_size: 20,
  })
  const [searchText, setSearchText] = useState('')

  // Modals
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [editingWord, setEditingWord] = useState<Word | null>(null)
  const [selectedWord, setSelectedWord] = useState<Word | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Load languages
  useEffect(() => {
    masterApi.getLanguages().then((res) => {
      setLanguages(res.data.data.languages)
    })
  }, [])

  // Load words
  const loadWords = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const params = { ...filters }
      if (searchText.trim()) {
        params.search = searchText.trim()
      }
      const res = await wordApi.getList(params)
      setWords(res.data.data.words)
      setTotalCount(res.data.data.total_count)
    } catch (err) {
      console.error('Failed to load words:', err)
      setError('단어 목록을 불러오는데 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }, [filters, searchText])

  useEffect(() => {
    loadWords()
  }, [loadWords])

  // Load word detail
  const loadWordDetail = async (id: number) => {
    try {
      const res = await wordApi.getDetail(id)
      setSelectedWord(res.data.data)
    } catch (err) {
      console.error('Failed to load word detail:', err)
    }
  }

  // Create word
  const handleCreate = async (data: WordCreateRequest | WordUpdateRequest) => {
    setIsSubmitting(true)
    try {
      await wordApi.create(data as WordCreateRequest)
      setIsCreateModalOpen(false)
      loadWords()
    } catch (err) {
      console.error('Failed to create word:', err)
      alert('단어 추가에 실패했습니다.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Update word
  const handleUpdate = async (data: WordCreateRequest | WordUpdateRequest) => {
    if (!editingWord) return
    setIsSubmitting(true)
    try {
      await wordApi.update(editingWord.id, data as WordUpdateRequest)
      setEditingWord(null)
      loadWords()
      if (selectedWord?.id === editingWord.id) {
        loadWordDetail(editingWord.id)
      }
    } catch (err) {
      console.error('Failed to update word:', err)
      alert('단어 수정에 실패했습니다.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Delete word
  const handleDelete = async (id: number) => {
    if (!confirm('이 단어를 삭제하시겠습니까? 관련된 번역과 예문도 모두 삭제됩니다.')) return
    try {
      await wordApi.delete(id)
      loadWords()
      if (selectedWord?.id === id) {
        setSelectedWord(null)
      }
    } catch (err) {
      console.error('Failed to delete word:', err)
      alert('단어 삭제에 실패했습니다.')
    }
  }

  // Pagination
  const totalPages = Math.ceil(totalCount / (filters.page_size || 20))

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <Link to="/" className="flex items-center gap-3">
                <div className="w-9 h-9 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                  </svg>
                </div>
              </Link>
              <div className="h-6 w-px bg-slate-200" />
              <h1 className="text-lg font-semibold text-slate-800">단어 관리</h1>
            </div>
            <div className="flex items-center gap-3">
              <Link to="/admin" className="text-sm text-slate-500 hover:text-indigo-600">
                대시보드
              </Link>
              <span className="text-sm text-slate-500">{user?.name}</span>
              <span className="px-2 py-1 bg-indigo-100 text-indigo-700 text-xs font-medium rounded">
                {user?.role}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-6">
          {/* Left: Word List */}
          <div className={`${selectedWord ? 'w-1/2' : 'w-full'} transition-all`}>
            {/* Filters */}
            <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 mb-6">
              <div className="flex flex-wrap gap-3">
                {/* Search */}
                <div className="flex-1 min-w-[200px]">
                  <input
                    type="text"
                    value={searchText}
                    onChange={(e) => setSearchText(e.target.value)}
                    placeholder="단어 검색..."
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>

                {/* Language Filter */}
                <select
                  value={filters.language || ''}
                  onChange={(e) => setFilters({ ...filters, language: e.target.value ? Number(e.target.value) : undefined, page: 1 })}
                  className="px-3 py-2 border border-slate-300 rounded-lg"
                >
                  <option value="">모든 언어</option>
                  {languages.map((lang) => (
                    <option key={lang.id} value={lang.id}>{lang.name_ko}</option>
                  ))}
                </select>

                {/* Category Filter */}
                <select
                  value={filters.category || ''}
                  onChange={(e) => setFilters({ ...filters, category: e.target.value as WordCategory || undefined, page: 1 })}
                  className="px-3 py-2 border border-slate-300 rounded-lg"
                >
                  <option value="">모든 카테고리</option>
                  {WORD_CATEGORY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>

                {/* Difficulty Filter */}
                <select
                  value={filters.difficulty_level || ''}
                  onChange={(e) => setFilters({ ...filters, difficulty_level: e.target.value ? Number(e.target.value) : undefined, page: 1 })}
                  className="px-3 py-2 border border-slate-300 rounded-lg"
                >
                  <option value="">모든 난이도</option>
                  {DIFFICULTY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>

                {/* Active Filter */}
                <select
                  value={filters.is_active === undefined ? '' : String(filters.is_active)}
                  onChange={(e) => setFilters({ ...filters, is_active: e.target.value === '' ? undefined : e.target.value === 'true', page: 1 })}
                  className="px-3 py-2 border border-slate-300 rounded-lg"
                >
                  <option value="">활성화 상태</option>
                  <option value="true">활성</option>
                  <option value="false">비활성</option>
                </select>

                {/* Add Button */}
                <button
                  onClick={() => setIsCreateModalOpen(true)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  단어 추가
                </button>
              </div>
            </div>

            {/* Word List */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100">
              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
                </div>
              ) : error ? (
                <div className="text-center py-12 text-rose-500">{error}</div>
              ) : words.length === 0 ? (
                <div className="text-center py-12 text-slate-400">검색 결과가 없습니다</div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-slate-50 border-b border-slate-100">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">단어</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">언어</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">카테고리</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">품사</th>
                          <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 uppercase">난이도</th>
                          <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 uppercase">번역</th>
                          <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 uppercase">예문</th>
                          <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 uppercase">상태</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase">작업</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {words.map((word) => (
                          <tr
                            key={word.id}
                            className={`hover:bg-slate-50 cursor-pointer ${selectedWord?.id === word.id ? 'bg-indigo-50' : ''}`}
                            onClick={() => loadWordDetail(word.id)}
                          >
                            <td className="px-4 py-3">
                              <div>
                                <p className="font-medium text-slate-800">{word.text}</p>
                                {word.pronunciation && (
                                  <p className="text-xs text-slate-400">{word.pronunciation}</p>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-sm text-slate-600">{word.language_name}</td>
                            <td className="px-4 py-3">
                              <span className="px-2 py-1 text-xs bg-slate-100 text-slate-600 rounded">
                                {word.category_display}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-sm text-slate-600">{word.part_of_speech_display}</td>
                            <td className="px-4 py-3 text-center">
                              <span className={`px-2 py-1 text-xs rounded ${
                                word.difficulty_level <= 2 ? 'bg-emerald-100 text-emerald-700' :
                                word.difficulty_level <= 3 ? 'bg-amber-100 text-amber-700' :
                                'bg-rose-100 text-rose-700'
                              }`}>
                                {word.difficulty_level}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-center text-sm text-slate-600">{word.translation_count}</td>
                            <td className="px-4 py-3 text-center text-sm text-slate-600">{word.example_count}</td>
                            <td className="px-4 py-3 text-center">
                              {word.is_active ? (
                                <span className="w-2 h-2 bg-emerald-500 rounded-full inline-block" title="활성" />
                              ) : (
                                <span className="w-2 h-2 bg-slate-300 rounded-full inline-block" title="비활성" />
                              )}
                            </td>
                            <td className="px-4 py-3 text-right">
                              <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                                <button
                                  onClick={() => {
                                    loadWordDetail(word.id).then(() => {
                                      // After loading, set editing
                                    })
                                    wordApi.getDetail(word.id).then((res) => setEditingWord(res.data.data))
                                  }}
                                  className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded"
                                  title="수정"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                  </svg>
                                </button>
                                <button
                                  onClick={() => handleDelete(word.id)}
                                  className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded"
                                  title="삭제"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                  </svg>
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Pagination */}
                  <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
                    <p className="text-sm text-slate-500">
                      총 {totalCount}개 중 {(filters.page! - 1) * filters.page_size! + 1}-{Math.min(filters.page! * filters.page_size!, totalCount)}개
                    </p>
                    <div className="flex gap-1">
                      <button
                        onClick={() => setFilters({ ...filters, page: filters.page! - 1 })}
                        disabled={filters.page === 1}
                        className="px-3 py-1 text-sm border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        이전
                      </button>
                      <span className="px-3 py-1 text-sm text-slate-600">
                        {filters.page} / {totalPages}
                      </span>
                      <button
                        onClick={() => setFilters({ ...filters, page: filters.page! + 1 })}
                        disabled={filters.page === totalPages}
                        className="px-3 py-1 text-sm border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        다음
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Right: Word Detail */}
          {selectedWord && (
            <div className="w-1/2">
              <WordDetailPanel
                word={selectedWord}
                languages={languages}
                onClose={() => setSelectedWord(null)}
                onRefresh={() => loadWordDetail(selectedWord.id)}
              />
            </div>
          )}
        </div>
      </main>

      {/* Create Modal */}
      <Modal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} title="단어 추가" size="lg">
        <WordForm
          languages={languages}
          onSubmit={handleCreate}
          onCancel={() => setIsCreateModalOpen(false)}
          isLoading={isSubmitting}
        />
      </Modal>

      {/* Edit Modal */}
      <Modal isOpen={!!editingWord} onClose={() => setEditingWord(null)} title="단어 수정" size="lg">
        {editingWord && (
          <WordForm
            word={editingWord}
            languages={languages}
            onSubmit={handleUpdate}
            onCancel={() => setEditingWord(null)}
            isLoading={isSubmitting}
          />
        )}
      </Modal>
    </div>
  )
}
