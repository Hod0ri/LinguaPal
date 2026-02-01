import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Layout from '../components/Layout'
import { policyApi, type PolicyDocument } from '../services/api'

type PolicyType = 'terms' | 'privacy'

const POLICY_LABELS: Record<PolicyType, string> = {
  terms: '이용약관',
  privacy: '개인정보처리방침',
}

export default function AdminPoliciesPage() {
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyType>('terms')
  const [policy, setPolicy] = useState<PolicyDocument | null>(null)
  const [editContent, setEditContent] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [isPreview, setIsPreview] = useState(false)

  // Fetch policy when selection changes
  useEffect(() => {
    const fetchPolicy = async () => {
      setIsLoading(true)
      setError(null)
      setSuccessMessage(null)

      try {
        const response = selectedPolicy === 'terms'
          ? await policyApi.getTermsOfService()
          : await policyApi.getPrivacyPolicy()

        if (response.data.success) {
          setPolicy(response.data.data)
          setEditContent(response.data.data.content)
        } else {
          setError('정책 문서를 불러오는데 실패했습니다.')
        }
      } catch (err) {
        console.error('Failed to fetch policy:', err)
        setError('정책 문서를 불러오는데 실패했습니다.')
      } finally {
        setIsLoading(false)
      }
    }

    fetchPolicy()
  }, [selectedPolicy])

  const handleSave = async () => {
    setIsSaving(true)
    setError(null)
    setSuccessMessage(null)

    try {
      const response = await policyApi.updatePolicy(selectedPolicy, editContent)

      if (response.data.success) {
        setPolicy(response.data.data)
        setSuccessMessage('정책 문서가 저장되었습니다.')
        setTimeout(() => setSuccessMessage(null), 3000)
      } else {
        setError('저장에 실패했습니다.')
      }
    } catch (err) {
      console.error('Failed to save policy:', err)
      setError('저장에 실패했습니다. 관리자 권한이 필요합니다.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleReset = () => {
    if (policy) {
      setEditContent(policy.content)
    }
  }

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-sm text-slate-500 mb-2">
            <Link to="/admin/dashboard" className="hover:text-indigo-600 transition-colors">
              관리자 대시보드
            </Link>
            <span>/</span>
            <span className="text-slate-700">정책 관리</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-800">정책 문서 관리</h1>
          <p className="text-slate-500 mt-1">이용약관과 개인정보처리방침을 편집합니다.</p>
        </div>

        {/* Policy Tabs */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 mb-6">
          <div className="flex border-b border-slate-200">
            {(['terms', 'privacy'] as PolicyType[]).map((type) => (
              <button
                key={type}
                onClick={() => setSelectedPolicy(type)}
                className={`flex-1 px-6 py-4 text-sm font-medium transition-colors ${
                  selectedPolicy === type
                    ? 'text-indigo-600 border-b-2 border-indigo-600 bg-indigo-50/50'
                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                }`}
              >
                {POLICY_LABELS[type]}
              </button>
            ))}
          </div>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
            {error}
          </div>
        )}
        {successMessage && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl text-green-700 text-sm">
            {successMessage}
          </div>
        )}

        {/* Loading State */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Editor */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between bg-slate-50">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  <span className="text-sm font-medium text-slate-700">마크다운 편집</span>
                </div>
                <div className="text-xs text-slate-400">
                  {policy && `최종 수정: ${new Date(policy.updated_at).toLocaleDateString('ko-KR')}`}
                </div>
              </div>
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full h-[500px] p-4 font-mono text-sm text-slate-700 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-inset"
                placeholder="마크다운 형식으로 작성하세요..."
              />
            </div>

            {/* Preview */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between bg-slate-50">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  <span className="text-sm font-medium text-slate-700">미리보기</span>
                </div>
                <a
                  href={`/${selectedPolicy === 'terms' ? 'terms' : 'privacy'}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-indigo-600 hover:underline"
                >
                  새 탭에서 보기
                </a>
              </div>
              <div className="p-4 h-[500px] overflow-y-auto">
                {policy ? (
                  <div
                    className="prose prose-sm prose-slate max-w-none prose-headings:font-semibold prose-h1:text-xl prose-h2:text-lg prose-h2:border-b prose-h2:border-slate-200 prose-h2:pb-2 prose-h2:mt-6 prose-h2:mb-3 prose-h3:text-base prose-p:text-slate-600 prose-li:text-slate-600 prose-table:text-xs"
                    dangerouslySetInnerHTML={{ __html: policy.content_html }}
                  />
                ) : (
                  <p className="text-slate-400 text-sm">미리보기할 내용이 없습니다.</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        {!isLoading && (
          <div className="mt-6 flex items-center justify-end gap-3">
            <button
              onClick={handleReset}
              disabled={isSaving || editContent === policy?.content}
              className="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              초기화
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || editContent === policy?.content}
              className="px-6 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  저장 중...
                </>
              ) : (
                '저장'
              )}
            </button>
          </div>
        )}

        {/* Help Text */}
        <div className="mt-8 p-4 bg-amber-50 border border-amber-200 rounded-xl">
          <div className="flex gap-3">
            <svg className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="text-sm text-amber-800">
              <p className="font-medium mb-1">마크다운 문법 안내</p>
              <ul className="list-disc list-inside space-y-1 text-amber-700">
                <li><code className="bg-amber-100 px-1 rounded"># 제목</code> - 제목 (h1)</li>
                <li><code className="bg-amber-100 px-1 rounded">## 소제목</code> - 소제목 (h2)</li>
                <li><code className="bg-amber-100 px-1 rounded">**굵게**</code> - 굵은 글씨</li>
                <li><code className="bg-amber-100 px-1 rounded">- 항목</code> - 목록</li>
                <li><code className="bg-amber-100 px-1 rounded">| 표 |</code> - 표 형식</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
