import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

interface AdminProtectedRouteProps {
  children: React.ReactNode
}

export default function AdminProtectedRoute({ children }: AdminProtectedRouteProps) {
  const { isAuthenticated, user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // Check if user is staff or admin
  const isStaffOrAdmin = user?.role === 'admin' || user?.role === 'staff'
  if (!isStaffOrAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-slate-800 mb-2">접근 권한이 없습니다</h2>
          <p className="text-slate-500 mb-4">관리자 또는 스태프 권한이 필요합니다.</p>
          <a href="/" className="text-indigo-600 hover:text-indigo-800 font-medium">
            홈으로 돌아가기
          </a>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
