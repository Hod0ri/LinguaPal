import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { userApi, masterApi } from '../services/api'
import type { Language, Country } from '../types'

const APP_NAME = import.meta.env.VITE_APP_NAME || 'LinguaPal'

export default function CreateProfilePage() {
  const { user, hasProfile, refreshProfile } = useAuth()
  const navigate = useNavigate()

  const [nickname, setNickname] = useState('')
  const [countryId, setCountryId] = useState<number | ''>('')
  const [selectedLanguages, setSelectedLanguages] = useState<number[]>([])
  const [languages, setLanguages] = useState<Language[]>([])
  const [countries, setCountries] = useState<Country[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (hasProfile) {
      navigate('/', { replace: true })
    }
  }, [hasProfile, navigate])

  useEffect(() => {
    const fetchMasterData = async () => {
      try {
        const [langRes, countryRes] = await Promise.all([
          masterApi.getLanguages(),
          masterApi.getCountries(),
        ])
        if (langRes.data.success) setLanguages(langRes.data.data.languages)
        if (countryRes.data.success) setCountries(countryRes.data.data.countries)
      } catch (error) {
        console.error('Failed to fetch master data:', error)
      }
    }
    fetchMasterData()
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

    if (!nickname.trim()) {
      setError('닉네임을 입력해주세요.')
      return
    }
    if (nickname.length < 2 || nickname.length > 50) {
      setError('닉네임은 2~50자 사이로 입력해주세요.')
      return
    }
    if (!countryId) {
      setError('국가를 선택해주세요.')
      return
    }
    if (selectedLanguages.length === 0) {
      setError('학습할 언어를 최소 1개 선택해주세요.')
      return
    }

    setIsLoading(true)
    try {
      const response = await userApi.createProfile({
        nickname: nickname.trim(),
        country: countryId as number,
        learning_language_ids: selectedLanguages,
      })
      if (response.data.success) {
        await refreshProfile()
        navigate('/', { replace: true })
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } }
      setError(error.response?.data?.message || '프로필 생성에 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50 to-purple-50 py-8 px-4">
      {/* Background decoration */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-indigo-200 to-purple-200 rounded-full opacity-50 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-br from-blue-200 to-indigo-200 rounded-full opacity-50 blur-3xl" />
      </div>

      <div className="relative max-w-lg mx-auto">
        {/* Logo */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            {APP_NAME}
          </h1>
        </div>

        <div className="card-elevated p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl mb-4 shadow-lg shadow-indigo-500/30">
              <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-slate-800 mb-2">프로필 설정</h2>
            <p className="text-slate-500">
              {user?.name || user?.email}님, 환영합니다!<br />
              프로필을 완성하고 학습을 시작하세요.
            </p>
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

            {/* Nickname */}
            <div>
              <label htmlFor="nickname" className="block text-sm font-semibold text-slate-700 mb-2">
                닉네임 <span className="text-indigo-500">*</span>
              </label>
              <input
                type="text"
                id="nickname"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder="사용할 닉네임을 입력하세요"
                className="input-field"
                maxLength={50}
              />
              <p className="mt-2 text-xs text-slate-400">{nickname.length}/50자</p>
            </div>

            {/* Country */}
            <div>
              <label htmlFor="country" className="block text-sm font-semibold text-slate-700 mb-2">
                국가 <span className="text-indigo-500">*</span>
              </label>
              <select
                id="country"
                value={countryId}
                onChange={(e) => setCountryId(e.target.value ? Number(e.target.value) : '')}
                className="input-field"
              >
                <option value="">국가를 선택하세요</option>
                {countries.map((country) => (
                  <option key={country.id} value={country.id}>
                    {country.name_ko} ({country.name_en})
                  </option>
                ))}
              </select>
            </div>

            {/* Languages */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-3">
                학습할 언어 <span className="text-indigo-500">*</span>
                <span className="font-normal text-slate-400 ml-2">(복수 선택 가능)</span>
              </label>
              <div className="grid grid-cols-2 gap-3">
                {languages.map((lang) => (
                  <button
                    key={lang.id}
                    type="button"
                    onClick={() => toggleLanguage(lang.id)}
                    className={`relative px-4 py-4 rounded-xl border-2 text-sm font-medium transition-all duration-200 ${
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
                  {selectedLanguages.length}개 언어 선택됨
                </p>
              )}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary"
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  처리 중...
                </span>
              ) : (
                '시작하기'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
