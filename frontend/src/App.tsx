import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
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
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
