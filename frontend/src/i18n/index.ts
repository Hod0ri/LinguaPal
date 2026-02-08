import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import ko from './locales/ko.json'
import en from './locales/en.json'
import es from './locales/es.json'
import ja from './locales/ja.json'

// 국가 코드 → UI 언어 매핑
const COUNTRY_TO_LOCALE: Record<string, string> = {
  KR: 'ko',
  JP: 'ja',
  ES: 'es', MX: 'es', AR: 'es', CO: 'es', CL: 'es',
  PE: 'es', VE: 'es', EC: 'es', GT: 'es', CU: 'es',
  BO: 'es', DO: 'es', HN: 'es', PY: 'es', SV: 'es',
  NI: 'es', CR: 'es', PA: 'es', UY: 'es',
}

export function getLocaleFromCountry(countryCode: string | undefined): string {
  if (!countryCode) return 'ko'
  return COUNTRY_TO_LOCALE[countryCode] || 'en'
}

const savedLanguage = localStorage.getItem('i18n_language')

i18n.use(initReactI18next).init({
  resources: {
    ko: { translation: ko },
    en: { translation: en },
    es: { translation: es },
    ja: { translation: ja },
  },
  lng: savedLanguage || 'ko',
  fallbackLng: 'ko',
  interpolation: {
    escapeValue: false,
  },
})

export default i18n
