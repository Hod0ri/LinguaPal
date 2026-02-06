import { useState } from 'react'
import { tts, LANGUAGE_CODES, type LanguageCode } from '../utils/textToSpeech'

interface TextToSpeechButtonProps {
  text: string
  language?: LanguageCode
  className?: string
}

/**
 * TTS 재생 버튼 컴포넌트
 * Web Speech API를 사용하여 완전 무료로 음성 재생
 */
export default function TextToSpeechButton({
  text,
  language = 'korean',
  className = ''
}: TextToSpeechButtonProps) {
  const [isPlaying, setIsPlaying] = useState(false)

  const handleSpeak = () => {
    if (isPlaying) {
      tts.stop()
      setIsPlaying(false)
    } else {
      const langCode = LANGUAGE_CODES[language]

      tts.speak(text, {
        lang: langCode,
        rate: 0.9, // 조금 천천히 (학습용)
        pitch: 1.0,
        volume: 1.0,
      })

      setIsPlaying(true)

      // 재생 완료 시 상태 업데이트
      setTimeout(() => {
        if (!tts.isSpeaking()) {
          setIsPlaying(false)
        }
      }, 100)
    }
  }

  return (
    <button
      onClick={handleSpeak}
      className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg transition-all ${
        isPlaying
          ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/30'
          : 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200'
      } ${className}`}
      title="발음 듣기"
    >
      {isPlaying ? (
        <>
          <svg className="w-5 h-5 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" clipRule="evenodd" />
          </svg>
          재생 중
        </>
      ) : (
        <>
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM12.293 7.293a1 1 0 011.414 0L15 8.586l1.293-1.293a1 1 0 111.414 1.414L16.414 10l1.293 1.293a1 1 0 01-1.414 1.414L15 11.414l-1.293 1.293a1 1 0 01-1.414-1.414L13.586 10l-1.293-1.293a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
          발음
        </>
      )}
    </button>
  )
}
