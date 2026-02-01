import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Footer from '../components/Footer'
import { policyApi, type PolicyDocument } from '../services/api'

export default function PrivacyPolicyPage() {
  const [policy, setPolicy] = useState<PolicyDocument | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchPolicy = async () => {
      try {
        const response = await policyApi.getPrivacyPolicy()
        if (response.data.success) {
          setPolicy(response.data.data)
        } else {
          setError('개인정보처리방침을 불러오는데 실패했습니다.')
        }
      } catch (err) {
        console.error('Failed to fetch privacy policy:', err)
        setError('개인정보처리방침을 불러오는데 실패했습니다.')
      } finally {
        setIsLoading(false)
      }
    }

    fetchPolicy()
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-indigo-50 to-purple-50">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
          <p className="text-slate-500 animate-pulse">로딩 중...</p>
        </div>
      </div>
    )
  }

  if (error || !policy) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-indigo-50 to-purple-50">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || '개인정보처리방침을 찾을 수 없습니다.'}</p>
          <Link to="/" className="text-indigo-600 hover:underline">
            홈으로 돌아가기
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-slate-700 hover:text-indigo-600 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span>돌아가기</span>
          </Link>
          <h1 className="text-lg font-semibold text-slate-800">개인정보처리방침</h1>
          <div className="w-20" /> {/* Spacer for centering */}
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 max-w-4xl mx-auto px-4 py-8 w-full">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 sm:p-8">
          {/* Last updated */}
          <div className="text-sm text-slate-500 mb-6">
            최종 수정일: {new Date(policy.updated_at).toLocaleDateString('ko-KR')}
          </div>

          {/* Policy content */}
          <div
            className="prose prose-slate max-w-none prose-headings:font-semibold prose-h1:text-2xl prose-h2:text-xl prose-h2:border-b prose-h2:border-slate-200 prose-h2:pb-2 prose-h2:mt-8 prose-h2:mb-4 prose-h3:text-lg prose-h3:mt-6 prose-p:text-slate-600 prose-li:text-slate-600 prose-table:text-sm prose-th:bg-slate-100 prose-th:p-2 prose-td:p-2 prose-td:border prose-td:border-slate-200"
            dangerouslySetInnerHTML={{ __html: policy.content_html }}
          />
        </div>
      </main>

      <Footer />
    </div>
  )
}
