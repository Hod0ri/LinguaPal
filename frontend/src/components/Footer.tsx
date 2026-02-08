import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

const APP_NAME = import.meta.env.VITE_APP_NAME || 'LinguaPal'

export default function Footer() {
  const { t } = useTranslation()
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-white/80 backdrop-blur-sm border-t border-slate-200/50 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Copyright */}
          <div className="text-sm text-slate-500">
            &copy; {currentYear} {APP_NAME}. All rights reserved.
          </div>

          {/* Links */}
          <div className="flex items-center gap-6 text-sm">
            <Link
              to="/terms"
              className="text-slate-500 hover:text-indigo-600 transition-colors"
            >
              {t('footer.termsOfService')}
            </Link>
            <Link
              to="/privacy"
              className="text-slate-500 hover:text-indigo-600 transition-colors"
            >
              {t('footer.privacyPolicy')}
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
