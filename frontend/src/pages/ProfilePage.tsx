import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../contexts/AuthContext'
import { userApi, masterApi } from '../services/api'
import type { Language } from '../types'
import Layout from '../components/Layout'

export default function ProfilePage() {
  const { user, profile, refreshProfile } = useAuth()
  const navigate = useNavigate()
  const { t } = useTranslation()

  const [nickname, setNickname] = useState('')
  const [selectedLanguages, setSelectedLanguages] = useState<number[]>([])
  const [languages, setLanguages] = useState<Language[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    if (profile) {
      setNickname(profile.nickname)
      setSelectedLanguages(profile.learning_languages.map((l) => l.id))
    }
  }, [profile])

  useEffect(() => {
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
    fetchLanguages()
  }, [])

  const toggleLanguage = (langId: number) => {
    setSelectedLanguages((prev) =>
      prev.includes(langId)
        ? prev.filter((id) => id !== langId)
        : [...prev, langId]
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!nickname.trim()) {
      setError(t('profile.nicknameRequired'))
      return
    }
    if (nickname.length < 2 || nickname.length > 50) {
      setError(t('profile.nicknameLengthError'))
      return
    }
    if (selectedLanguages.length === 0) {
      setError(t('profile.selectLanguageError'))
      return
    }

    setIsLoading(true)
    try {
      const response = await userApi.updateProfile({
        nickname: nickname.trim(),
        learning_language_ids: selectedLanguages,
      })
      if (response.data.success) {
        await refreshProfile()
        setSuccess(t('profile.profileUpdated'))
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } }
      setError(error.response?.data?.message || t('profile.profileUpdateFailed'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Layout>
      <div className="max-w-2xl mx-auto py-8 px-4">
        <div className="mb-6">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-slate-500 hover:text-slate-700 transition-colors group"
          >
            <svg className="w-5 h-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            {t('common.goToMain')}
          </button>
        </div>

        <div className="card p-8">
          {/* Header */}
          <div className="flex items-center gap-4 mb-8 pb-6 border-b border-slate-100">
            {user?.profile_image ? (
              <img
                src={user.profile_image}
                alt={user.name}
                className="w-16 h-16 rounded-2xl object-cover ring-4 ring-slate-100"
              />
            ) : (
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-indigo-500/20">
                {user?.name?.charAt(0) || user?.email.charAt(0).toUpperCase()}
              </div>
            )}
            <div>
              <h1 className="text-2xl font-bold text-slate-800">{t('profile.title')}</h1>
              <p className="text-slate-500">{t('profile.subtitle')}</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="flex items-center gap-3 bg-red-50 text-red-600 px-4 py-3 rounded-xl text-sm border border-red-100">
                <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {error}
              </div>
            )}
            {success && (
              <div className="flex items-center gap-3 bg-emerald-50 text-emerald-600 px-4 py-3 rounded-xl text-sm border border-emerald-100">
                <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {success}
              </div>
            )}

            {/* Read-only fields */}
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  {t('profile.email')}
                </label>
                <input
                  type="email"
                  value={user?.email || ''}
                  disabled
                  className="w-full px-4 py-3 border-2 border-slate-100 rounded-xl bg-slate-50 text-slate-500"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  {t('profile.country')}
                </label>
                <input
                  type="text"
                  value={profile?.country ? `${profile.country.name_ko}` : ''}
                  disabled
                  className="w-full px-4 py-3 border-2 border-slate-100 rounded-xl bg-slate-50 text-slate-500"
                />
              </div>
            </div>

            {/* Nickname */}
            <div>
              <label htmlFor="nickname" className="block text-sm font-semibold text-slate-700 mb-2">
                {t('profile.nickname')} <span className="text-indigo-500">*</span>
              </label>
              <input
                type="text"
                id="nickname"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder={t('profile.nicknamePlaceholder')}
                className="input-field"
                maxLength={50}
              />
              <p className="mt-2 text-xs text-slate-400">{t('profile.nicknameLength', { count: nickname.length })}</p>
            </div>

            {/* Languages */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-3">
                {t('profile.learningLanguages')} <span className="text-indigo-500">*</span>
                <span className="font-normal text-slate-400 ml-2">{t('profile.multipleSelection')}</span>
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {languages.map((lang) => (
                  <button
                    key={lang.id}
                    type="button"
                    onClick={() => toggleLanguage(lang.id)}
                    className={`relative px-4 py-3 rounded-xl border-2 text-sm font-medium transition-all duration-200 ${
                      selectedLanguages.includes(lang.id)
                        ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white border-transparent shadow-lg shadow-indigo-500/25'
                        : 'bg-white text-slate-600 border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/50'
                    }`}
                  >
                    {selectedLanguages.includes(lang.id) && (
                      <span className="absolute top-2 right-2">
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </span>
                    )}
                    {lang.name_ko}
                  </button>
                ))}
              </div>
              {selectedLanguages.length > 0 && (
                <p className="mt-3 text-sm text-indigo-600 font-medium">
                  {t('profile.languagesSelected', { count: selectedLanguages.length })}
                </p>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => navigate('/')}
                className="flex-1 btn-secondary"
              >
                {t('common.cancel')}
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="flex-1 btn-primary"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    {t('profile.saving')}
                  </span>
                ) : (
                  t('profile.saveButton')
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Layout>
  )
}
