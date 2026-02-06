/**
 * Text-to-Speech utility using Web Speech API
 * Completely free and works in all modern browsers
 */

interface TTSOptions {
  lang?: string
  rate?: number // 0.1 ~ 10 (기본: 1)
  pitch?: number // 0 ~ 2 (기본: 1)
  volume?: number // 0 ~ 1 (기본: 1)
}

class TextToSpeech {
  private synth: SpeechSynthesis
  private currentUtterance: SpeechSynthesisUtterance | null = null

  constructor() {
    this.synth = window.speechSynthesis
  }

  /**
   * 텍스트를 음성으로 재생
   */
  speak(text: string, options: TTSOptions = {}) {
    // 이전 재생 중지
    this.stop()

    const utterance = new SpeechSynthesisUtterance(text)

    // 언어 설정 (기본값: 한국어)
    utterance.lang = options.lang || 'ko-KR'

    // 속도 (0.1 ~ 10, 기본: 1)
    utterance.rate = options.rate || 1

    // 음높이 (0 ~ 2, 기본: 1)
    utterance.pitch = options.pitch || 1

    // 볼륨 (0 ~ 1, 기본: 1)
    utterance.volume = options.volume || 1

    this.currentUtterance = utterance
    this.synth.speak(utterance)
  }

  /**
   * 재생 중지
   */
  stop() {
    if (this.synth.speaking) {
      this.synth.cancel()
    }
    this.currentUtterance = null
  }

  /**
   * 일시 정지
   */
  pause() {
    if (this.synth.speaking) {
      this.synth.pause()
    }
  }

  /**
   * 재개
   */
  resume() {
    if (this.synth.paused) {
      this.synth.resume()
    }
  }

  /**
   * 사용 가능한 음성 목록 가져오기
   */
  getVoices(): SpeechSynthesisVoice[] {
    return this.synth.getVoices()
  }

  /**
   * 특정 언어의 음성 찾기
   */
  getVoiceByLang(lang: string): SpeechSynthesisVoice | undefined {
    const voices = this.getVoices()
    return voices.find(voice => voice.lang.startsWith(lang))
  }

  /**
   * 재생 중인지 확인
   */
  isSpeaking(): boolean {
    return this.synth.speaking
  }
}

// 싱글톤 인스턴스
export const tts = new TextToSpeech()

// 언어별 코드 매핑
export const LANGUAGE_CODES = {
  korean: 'ko-KR',
  japanese: 'ja-JP',
  english: 'en-US',
  spanish: 'es-ES',
  french: 'fr-FR',
  german: 'de-DE',
  chinese: 'zh-CN',
  russian: 'ru-RU',
  italian: 'it-IT',
  portuguese: 'pt-BR',
} as const

export type LanguageCode = keyof typeof LANGUAGE_CODES

// 언어 코드 문자열을 LanguageCode로 변환하는 헬퍼 함수
export const getLanguageCode = (langCode: string): string => {
  const mapping: Record<string, string> = {
    'ko': 'ko-KR',
    'ja': 'ja-JP',
    'en': 'en-US',
    'es': 'es-ES',
    'fr': 'fr-FR',
    'de': 'de-DE',
    'zh': 'zh-CN',
    'ru': 'ru-RU',
    'it': 'it-IT',
    'pt': 'pt-BR',
  }
  return mapping[langCode] || 'ko-KR'
}
