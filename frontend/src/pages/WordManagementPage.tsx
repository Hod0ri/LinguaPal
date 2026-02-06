import { useState, useEffect, useCallback, useMemo } from 'react'
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
import {
  GRAMMAR_PROPERTIES,
  getSuggestedGrammarProperties,
  getGrammarLabel,
  getGrammarDescription,
  getGrammarExamples,
  translateGrammarValue,
} from '../constants/grammar'

/**
 * Format grammar value for display
 * Handles objects, arrays, and primitive values
 * Uses Korean labels for nested keys
 * Translates Japanese grammar terms to Korean
 */
function formatGrammarValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '-'
  }
  if (typeof value === 'object') {
    if (Array.isArray(value)) {
      return value.map(v => translateGrammarValue(String(v))).join(', ')
    }
    // For objects, show key-value pairs with Korean labels
    return Object.entries(value as Record<string, unknown>)
      .map(([k, v]) => `${getGrammarLabel(k)}: ${formatGrammarValue(v)}`)
      .join(', ')
  }
  // Translate Japanese grammar terms (like 五段動詞, い形容詞)
  return translateGrammarValue(String(value))
}

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

// ============= Grammar Editor Modal =============
function GrammarEditorModal({
  isOpen,
  onClose,
  grammar,
  onSave,
}: {
  isOpen: boolean
  onClose: () => void
  grammar: Record<string, unknown>
  onSave: (grammar: Record<string, unknown>) => void
}) {
  const [editedGrammar, setEditedGrammar] = useState<Record<string, unknown>>(grammar)
  const [newPropertyKey, setNewPropertyKey] = useState('')
  const [showAddProperty, setShowAddProperty] = useState(false)
  const [expandedObjects, setExpandedObjects] = useState<Set<string>>(new Set())
  const [customPropertyMode, setCustomPropertyMode] = useState(false)

  // Reset when modal opens
  useEffect(() => {
    if (isOpen) {
      setEditedGrammar(grammar)
      setNewPropertyKey('')
      setShowAddProperty(false)
      setCustomPropertyMode(false)
    }
  }, [isOpen, grammar])

  // Update a simple value
  const updateValue = (key: string, value: string) => {
    setEditedGrammar(prev => ({ ...prev, [key]: value }))
  }

  // Update a nested value (for objects like forms)
  const updateNestedValue = (parentKey: string, childKey: string, value: string) => {
    setEditedGrammar(prev => ({
      ...prev,
      [parentKey]: {
        ...(prev[parentKey] as Record<string, unknown>),
        [childKey]: value,
      },
    }))
  }

  // Delete a property
  const deleteProperty = (key: string) => {
    setEditedGrammar(prev => {
      const newGrammar = { ...prev }
      delete newGrammar[key]
      return newGrammar
    })
  }

  // Delete a nested property
  const deleteNestedProperty = (parentKey: string, childKey: string) => {
    setEditedGrammar(prev => {
      const parent = { ...(prev[parentKey] as Record<string, unknown>) }
      delete parent[childKey]
      if (Object.keys(parent).length === 0) {
        const newGrammar = { ...prev }
        delete newGrammar[parentKey]
        return newGrammar
      }
      return { ...prev, [parentKey]: parent }
    })
  }

  // Add a new property
  const addProperty = (key: string) => {
    if (key && !(key in editedGrammar)) {
      setEditedGrammar(prev => ({ ...prev, [key]: '' }))
      setNewPropertyKey('')
      setShowAddProperty(false)
      setCustomPropertyMode(false)
    }
  }

  // Add a nested property to an object
  const addNestedProperty = (parentKey: string, childKey: string) => {
    if (childKey) {
      const parent = (editedGrammar[parentKey] as Record<string, unknown>) || {}
      if (!(childKey in parent)) {
        setEditedGrammar(prev => ({
          ...prev,
          [parentKey]: { ...parent, [childKey]: '' },
        }))
      }
    }
  }

  // Convert simple value to object (for forms-like properties)
  const convertToObject = (key: string) => {
    setEditedGrammar(prev => ({
      ...prev,
      [key]: { 'm.sg': '', 'f.sg': '', 'm.pl': '', 'f.pl': '' },
    }))
    setExpandedObjects(prev => new Set(prev).add(key))
  }

  // Toggle object expansion
  const toggleExpanded = (key: string) => {
    setExpandedObjects(prev => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

  const handleSave = () => {
    // Clean up empty values
    const cleaned: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(editedGrammar)) {
      if (typeof value === 'object' && value !== null) {
        const nestedCleaned: Record<string, unknown> = {}
        for (const [nk, nv] of Object.entries(value as Record<string, unknown>)) {
          if (nv !== '' && nv !== null && nv !== undefined) {
            nestedCleaned[nk] = nv
          }
        }
        if (Object.keys(nestedCleaned).length > 0) {
          cleaned[key] = nestedCleaned
        }
      } else if (value !== '' && value !== null && value !== undefined) {
        cleaned[key] = value
      }
    }
    onSave(cleaned)
    onClose()
  }

  // Common nested keys for forms
  const nestedKeyOptions = [
    { value: 'm.sg', label: '남성 단수 (m.sg)' },
    { value: 'f.sg', label: '여성 단수 (f.sg)' },
    { value: 'm.pl', label: '남성 복수 (m.pl)' },
    { value: 'f.pl', label: '여성 복수 (f.pl)' },
    { value: 'n.sg', label: '중성 단수 (n.sg)' },
    { value: 'n.pl', label: '중성 복수 (n.pl)' },
  ]

  if (!isOpen) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="문법 속성 편집" size="lg">
      <div className="space-y-4">
        {/* Existing Properties */}
        {Object.entries(editedGrammar).map(([key, value]) => (
          <div key={key} className="border border-slate-200 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="font-medium text-indigo-600">{getGrammarLabel(key)}</span>
                <span className="text-xs text-slate-400">({key})</span>
              </div>
              <div className="flex items-center gap-1">
                {typeof value !== 'object' && (
                  <button
                    type="button"
                    onClick={() => convertToObject(key)}
                    className="p-1 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded"
                    title="객체로 변환 (성/수 변화형)"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" />
                    </svg>
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => deleteProperty(key)}
                  className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded"
                  title="삭제"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>

            {typeof value === 'object' && value !== null ? (
              // Nested object (like forms)
              <div className="space-y-2">
                <button
                  type="button"
                  onClick={() => toggleExpanded(key)}
                  className="text-xs text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                >
                  <svg className={`w-3 h-3 transition-transform ${expandedObjects.has(key) ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  {expandedObjects.has(key) ? '접기' : '펼치기'} ({Object.keys(value as object).length}개)
                </button>

                {expandedObjects.has(key) && (
                  <div className="ml-4 space-y-2 border-l-2 border-indigo-100 pl-3">
                    {Object.entries(value as Record<string, unknown>).map(([nk, nv]) => (
                      <div key={nk} className="flex items-center gap-2">
                        <span className="text-sm text-slate-600 w-24">{getGrammarLabel(nk)}</span>
                        <input
                          type="text"
                          value={String(nv || '')}
                          onChange={(e) => updateNestedValue(key, nk, e.target.value)}
                          className="flex-1 px-2 py-1 text-sm border border-slate-300 rounded focus:ring-1 focus:ring-indigo-500"
                        />
                        <button
                          type="button"
                          onClick={() => deleteNestedProperty(key, nk)}
                          className="p-1 text-slate-400 hover:text-rose-600"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    ))}
                    {/* Add nested property */}
                    <div className="flex items-center gap-2 mt-2">
                      <select
                        className="text-sm border border-slate-300 rounded px-2 py-1"
                        onChange={(e) => {
                          if (e.target.value) {
                            addNestedProperty(key, e.target.value)
                            e.target.value = ''
                          }
                        }}
                        defaultValue=""
                      >
                        <option value="">+ 항목 추가...</option>
                        {nestedKeyOptions
                          .filter(opt => !(opt.value in (value as Record<string, unknown>)))
                          .map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                          ))}
                      </select>
                      <span className="text-xs text-slate-400">또는</span>
                      <input
                        type="text"
                        placeholder="커스텀 키"
                        className="text-sm border border-slate-300 rounded px-2 py-1 w-24"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault()
                            const input = e.target as HTMLInputElement
                            if (input.value.trim()) {
                              addNestedProperty(key, input.value.trim())
                              input.value = ''
                            }
                          }
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ) : (
              // Simple value
              <input
                type="text"
                value={String(value || '')}
                onChange={(e) => updateValue(key, e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                placeholder={getGrammarExamples(key) || '값을 입력하세요'}
              />
            )}

            {getGrammarDescription(key) && (
              <p className="text-xs text-slate-400 mt-1">{getGrammarDescription(key)}</p>
            )}
          </div>
        ))}

        {/* Add New Property */}
        {showAddProperty ? (
          <div className="border border-dashed border-indigo-300 rounded-lg p-3 bg-indigo-50">
            {/* Toggle between predefined and custom */}
            <div className="flex gap-2 mb-3">
              <button
                type="button"
                onClick={() => setCustomPropertyMode(false)}
                className={`px-3 py-1 text-sm rounded-lg ${!customPropertyMode ? 'bg-indigo-600 text-white' : 'bg-white text-slate-600 border border-slate-300'}`}
              >
                사전 정의 속성
              </button>
              <button
                type="button"
                onClick={() => setCustomPropertyMode(true)}
                className={`px-3 py-1 text-sm rounded-lg ${customPropertyMode ? 'bg-indigo-600 text-white' : 'bg-white text-slate-600 border border-slate-300'}`}
              >
                커스텀 속성
              </button>
            </div>

            <div className="flex items-center gap-2 mb-2">
              {customPropertyMode ? (
                // Custom property input
                <input
                  type="text"
                  value={newPropertyKey}
                  onChange={(e) => setNewPropertyKey(e.target.value)}
                  className="flex-1 px-3 py-2 border border-slate-300 rounded-lg"
                  placeholder="속성 키 입력 (예: custom_field)"
                />
              ) : (
                // Predefined property dropdown
                <select
                  value={newPropertyKey}
                  onChange={(e) => setNewPropertyKey(e.target.value)}
                  className="flex-1 px-3 py-2 border border-slate-300 rounded-lg"
                >
                  <option value="">속성 선택...</option>
                  {Object.keys(GRAMMAR_PROPERTIES)
                    .filter(k => !(k in editedGrammar))
                    .map(k => (
                      <option key={k} value={k}>{getGrammarLabel(k)} ({k})</option>
                    ))}
                </select>
              )}
              <button
                type="button"
                onClick={() => addProperty(newPropertyKey)}
                disabled={!newPropertyKey || (newPropertyKey in editedGrammar)}
                className="px-3 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                추가
              </button>
              <button
                type="button"
                onClick={() => setShowAddProperty(false)}
                className="px-3 py-2 text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200"
              >
                취소
              </button>
            </div>
            {newPropertyKey && getGrammarDescription(newPropertyKey) && (
              <p className="text-xs text-indigo-600">{getGrammarDescription(newPropertyKey)}</p>
            )}
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setShowAddProperty(true)}
            className="w-full py-3 border-2 border-dashed border-slate-300 rounded-lg text-slate-500 hover:border-indigo-400 hover:text-indigo-600 transition-colors"
          >
            + 새 속성 추가
          </button>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200"
          >
            취소
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="px-4 py-2 text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
          >
            저장
          </button>
        </div>
      </div>
    </Modal>
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

  // Grammar helper state
  const [showGrammarHelper, setShowGrammarHelper] = useState(false)
  const [showGrammarEditor, setShowGrammarEditor] = useState(false)

  // Get current grammar object for editor
  const currentGrammar = useMemo(() => {
    try {
      return JSON.parse(grammarText) as Record<string, unknown>
    } catch {
      return {}
    }
  }, [grammarText])

  // Handle grammar save from editor
  const handleGrammarSave = (newGrammar: Record<string, unknown>) => {
    setGrammarText(JSON.stringify(newGrammar, null, 2))
  }

  // Get selected language code
  const selectedLanguageCode = useMemo(() => {
    const lang = languages.find(l => l.id === formData.language_id)
    return lang?.code || ''
  }, [languages, formData.language_id])

  // Get suggested grammar properties based on language and part of speech
  const suggestedProperties = useMemo(() => {
    return getSuggestedGrammarProperties(selectedLanguageCode, formData.part_of_speech)
  }, [selectedLanguageCode, formData.part_of_speech])

  // Add a grammar property to the JSON
  const addGrammarProperty = (key: string) => {
    try {
      const current = JSON.parse(grammarText) as Record<string, unknown>
      if (!(key in current)) {
        current[key] = ''
        setGrammarText(JSON.stringify(current, null, 2))
      }
    } catch {
      // If parse fails, create new object with the property
      setGrammarText(JSON.stringify({ [key]: '' }, null, 2))
    }
  }

  // Apply a template for the language/part_of_speech
  const applyTemplate = () => {
    const properties = suggestedProperties.reduce((acc, key) => {
      acc[key] = ''
      return acc
    }, {} as Record<string, string>)
    setGrammarText(JSON.stringify(properties, null, 2))
  }

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

      {/* Grammar (JSON) with Helper */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="block text-sm font-medium text-slate-700">
            문법 속성
          </label>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowGrammarEditor(true)}
              className="text-xs px-2 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700 flex items-center gap-1"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
              편집기 열기
            </button>
            <button
              type="button"
              onClick={() => setShowGrammarHelper(!showGrammarHelper)}
              className="text-xs text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {showGrammarHelper ? '도움말 닫기' : 'JSON 도움말'}
            </button>
          </div>
        </div>

        {/* Grammar Helper Panel */}
        {showGrammarHelper && (
          <div className="mb-3 p-4 bg-indigo-50 rounded-lg border border-indigo-100">
            {/* Suggested Properties */}
            {suggestedProperties.length > 0 && (
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-indigo-800">
                    추천 속성 ({selectedLanguageCode.toUpperCase()} - {formData.part_of_speech})
                  </span>
                  <button
                    type="button"
                    onClick={applyTemplate}
                    className="text-xs px-2 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                  >
                    템플릿 적용
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {suggestedProperties.map((key) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => addGrammarProperty(key)}
                      className="group relative px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs hover:bg-indigo-200 transition-colors"
                    >
                      <span className="font-medium">{getGrammarLabel(key)}</span>
                      <span className="text-indigo-400 ml-1">({key})</span>
                      {/* Tooltip */}
                      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-slate-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50 max-w-xs text-left">
                        <span className="font-medium block">{getGrammarLabel(key)}</span>
                        <span className="text-slate-300 block">{getGrammarDescription(key)}</span>
                        {getGrammarExamples(key) && (
                          <span className="text-indigo-300 block mt-1">예: {getGrammarExamples(key)}</span>
                        )}
                        <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* All Properties */}
            <div>
              <span className="text-sm font-medium text-slate-700 block mb-2">
                모든 속성 (클릭하여 추가)
              </span>
              <div className="max-h-48 overflow-y-auto">
                <div className="flex flex-wrap gap-1.5">
                  {Object.keys(GRAMMAR_PROPERTIES).map((key) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => addGrammarProperty(key)}
                      className="group relative px-2 py-1 bg-white text-slate-600 rounded text-xs hover:bg-slate-100 border border-slate-200 transition-colors"
                    >
                      <span>{getGrammarLabel(key)}</span>
                      {/* Tooltip */}
                      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-slate-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50 max-w-xs text-left">
                        <span className="font-medium block">{getGrammarLabel(key)} ({key})</span>
                        <span className="text-slate-300 block">{getGrammarDescription(key)}</span>
                        {getGrammarExamples(key) && (
                          <span className="text-indigo-300 block mt-1">예: {getGrammarExamples(key)}</span>
                        )}
                        <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Current grammar preview */}
        {Object.keys(currentGrammar).length > 0 && (
          <div className="mb-2 p-3 bg-slate-50 rounded-lg">
            <p className="text-xs text-slate-500 mb-2">현재 설정된 속성:</p>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(currentGrammar).map(([key, value]) => (
                <span key={key} className="px-2 py-1 bg-white text-slate-700 rounded text-xs border border-slate-200">
                  <span className="font-medium text-indigo-600">{getGrammarLabel(key)}:</span>{' '}
                  {formatGrammarValue(value)}
                </span>
              ))}
            </div>
          </div>
        )}

        <details className="text-sm">
          <summary className="text-slate-500 cursor-pointer hover:text-slate-700">JSON 직접 편집</summary>
          <textarea
            value={grammarText}
            onChange={(e) => setGrammarText(e.target.value)}
            className="mt-2 w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm"
            rows={4}
            placeholder='{"past": "went", "past_participle": "gone"}'
          />
        </details>
        <p className="text-xs text-slate-400 mt-1">
          "편집기 열기" 버튼으로 쉽게 편집하거나, JSON을 직접 수정할 수 있습니다
        </p>
      </div>

      {/* Grammar Editor Modal */}
      <GrammarEditorModal
        isOpen={showGrammarEditor}
        onClose={() => setShowGrammarEditor(false)}
        grammar={currentGrammar}
        onSave={handleGrammarSave}
      />

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
            <div className="flex flex-wrap gap-2 mt-1">
              {Object.entries(word.grammar).map(([key, value]) => (
                <span
                  key={key}
                  className="group relative px-2 py-1 bg-white text-slate-700 rounded text-sm border border-slate-200 cursor-help"
                  title={getGrammarDescription(key)}
                >
                  <span className="font-medium text-indigo-600">{getGrammarLabel(key)}:</span>{' '}
                  {formatGrammarValue(value)}
                  {/* Tooltip */}
                  <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-slate-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50 max-w-xs text-left">
                    <span className="font-medium block">{getGrammarLabel(key)} ({key})</span>
                    <span className="text-slate-300 block">{getGrammarDescription(key)}</span>
                    <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
                  </span>
                </span>
              ))}
            </div>
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
