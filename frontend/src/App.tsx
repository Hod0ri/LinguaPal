import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import AdminProtectedRoute from './components/AdminProtectedRoute'
import LoginPage from './pages/LoginPage'
import CreateProfilePage from './pages/CreateProfilePage'
import MainPage from './pages/MainPage'
import ProfilePage from './pages/ProfilePage'
import QuizPage from './pages/QuizPage'
import QuizResultPage from './pages/QuizResultPage'
import QuizDashboardPage from './pages/QuizDashboardPage'
import WordQuizPage from './pages/WordQuizPage'
import WordQuizResultPage from './pages/WordQuizResultPage'
import WordQuizDashboardPage from './pages/WordQuizDashboardPage'
import FlashcardPage from './pages/FlashcardPage'
import WordBrowsePage from './pages/WordBrowsePage'
import VocabularyPage from './pages/VocabularyPage'
import LearnedWordsPage from './pages/LearnedWordsPage'
import AdminDashboardPage from './pages/AdminDashboardPage'
import AdminPoliciesPage from './pages/AdminPoliciesPage'
import WordManagementPage from './pages/WordManagementPage'
import TermsOfServicePage from './pages/TermsOfServicePage'
import PrivacyPolicyPage from './pages/PrivacyPolicyPage'

function App() {
  const { isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/create-profile"
        element={
          <ProtectedRoute requireProfile={false}>
            <CreateProfilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/quiz/dashboard"
        element={
          <ProtectedRoute>
            <QuizDashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/quiz/result/:quizId"
        element={
          <ProtectedRoute>
            <QuizResultPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/quiz/:quizId"
        element={
          <ProtectedRoute>
            <QuizPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/word-quiz/dashboard"
        element={
          <ProtectedRoute>
            <WordQuizDashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/word-quiz/result/:quizId"
        element={
          <ProtectedRoute>
            <WordQuizResultPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/word-quiz/:quizId"
        element={
          <ProtectedRoute>
            <WordQuizPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/flashcard"
        element={
          <ProtectedRoute>
            <FlashcardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/words"
        element={
          <ProtectedRoute>
            <WordBrowsePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/vocabulary"
        element={
          <ProtectedRoute>
            <VocabularyPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/learned-words"
        element={
          <ProtectedRoute>
            <LearnedWordsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/dashboard"
        element={
          <AdminProtectedRoute>
            <AdminDashboardPage />
          </AdminProtectedRoute>
        }
      />
      <Route
        path="/admin/words"
        element={
          <AdminProtectedRoute>
            <WordManagementPage />
          </AdminProtectedRoute>
        }
      />
      <Route
        path="/admin/policies"
        element={
          <AdminProtectedRoute>
            <AdminPoliciesPage />
          </AdminProtectedRoute>
        }
      />
      {/* Public pages - no authentication required */}
      <Route path="/terms" element={<TermsOfServicePage />} />
      <Route path="/privacy" element={<PrivacyPolicyPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
