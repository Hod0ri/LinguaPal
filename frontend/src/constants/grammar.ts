/**
 * Grammar property labels and descriptions for different languages
 * 문법 속성 라벨 및 설명
 */

export interface GrammarPropertyInfo {
  label: string        // 한글 라벨
  description: string  // 설명/도움말
  examples?: string    // 예시
}

// 공통 문법 속성
export const GRAMMAR_PROPERTIES: Record<string, GrammarPropertyInfo> = {
  // === 명사 관련 ===
  gender: {
    label: '성',
    description: '명사의 문법적 성별 (남성/여성/중성)',
    examples: 'masculine, feminine, neuter',
  },
  plural: {
    label: '복수형',
    description: '명사의 복수형 표기',
    examples: 'book → books, child → children',
  },
  article: {
    label: '관사',
    description: '명사와 함께 쓰이는 관사',
    examples: 'el (스페인어 남성), la (스페인어 여성)',
  },
  countable: {
    label: '가산/불가산',
    description: '셀 수 있는 명사인지 여부',
    examples: 'countable, uncountable',
  },
  case: {
    label: '격',
    description: '명사의 문법적 격 변화',
    examples: 'nominative, accusative, dative, genitive',
  },

  // === 동사 관련 ===
  conjugation: {
    label: '활용형',
    description: '동사의 활용 패턴 또는 그룹',
    examples: '1그룹, 2그룹, 불규칙 (일본어)',
  },
  transitivity: {
    label: '자동사/타동사',
    description: '목적어 필요 여부',
    examples: 'transitive (타동사), intransitive (자동사)',
  },
  irregular: {
    label: '불규칙 여부',
    description: '불규칙 활용을 하는 동사인지',
    examples: 'true, false',
  },

  // 동사 시제/형태
  past: {
    label: '과거형',
    description: '동사의 과거 시제 형태',
    examples: 'go → went, eat → ate',
  },
  past_participle: {
    label: '과거분사',
    description: '완료 시제나 수동태에 쓰이는 형태',
    examples: 'go → gone, eat → eaten',
  },
  present_participle: {
    label: '현재분사',
    description: '진행형이나 형용사로 쓰이는 형태',
    examples: 'go → going, eat → eating',
  },
  infinitive: {
    label: '원형/부정사',
    description: '동사의 기본형',
    examples: 'to go, to eat',
  },
  gerund: {
    label: '동명사',
    description: '동사가 명사처럼 쓰이는 형태',
    examples: 'swimming, reading',
  },

  // 동사 문법 범주
  tense: {
    label: '시제',
    description: '동사의 시간 표현',
    examples: 'present, past, future',
  },
  aspect: {
    label: '상',
    description: '동작의 완료/진행 상태',
    examples: 'perfective, imperfective, progressive',
  },
  mood: {
    label: '법',
    description: '화자의 태도나 의도 표현',
    examples: 'indicative, subjunctive, imperative',
  },
  voice: {
    label: '태',
    description: '능동/수동 구분',
    examples: 'active, passive',
  },
  person: {
    label: '인칭',
    description: '주어의 인칭 (1/2/3인칭)',
    examples: 'first, second, third',
  },
  number: {
    label: '수',
    description: '단수/복수 구분',
    examples: 'singular, plural',
  },

  // === 형용사/부사 관련 ===
  comparative: {
    label: '비교급',
    description: '형용사/부사의 비교급 형태',
    examples: 'big → bigger, good → better',
  },
  superlative: {
    label: '최상급',
    description: '형용사/부사의 최상급 형태',
    examples: 'big → biggest, good → best',
  },

  // === 일본어 특수 ===
  reading: {
    label: '읽기',
    description: '한자의 읽는 방법',
    examples: '音読み (온요미), 訓読み (훈요미)',
  },
  onyomi: {
    label: '음독',
    description: '한자의 중국식 읽기',
    examples: '山 → サン (san)',
  },
  kunyomi: {
    label: '훈독',
    description: '한자의 일본식 읽기',
    examples: '山 → やま (yama)',
  },
  jlpt_level: {
    label: 'JLPT 레벨',
    description: '일본어능력시험 레벨',
    examples: 'N5, N4, N3, N2, N1',
  },
  formality: {
    label: '존칭/경어',
    description: '공손함의 정도',
    examples: 'casual, polite, honorific',
  },
  te_form: {
    label: 'て형',
    description: '일본어 동사의 て형',
    examples: '食べる → 食べて',
  },
  ta_form: {
    label: 'た형',
    description: '일본어 동사의 과거형',
    examples: '食べる → 食べた',
  },
  negative: {
    label: '부정형',
    description: '부정 표현 형태',
    examples: '食べる → 食べない',
  },
  potential: {
    label: '가능형',
    description: '가능을 나타내는 형태',
    examples: '食べる → 食べられる',
  },
  passive: {
    label: '수동형',
    description: '수동을 나타내는 형태',
    examples: '食べる → 食べられる',
  },
  causative: {
    label: '사역형',
    description: '사역을 나타내는 형태',
    examples: '食べる → 食べさせる',
  },
  volitional: {
    label: '의지형',
    description: '의지/권유를 나타내는 형태',
    examples: '食べる → 食べよう',
  },
  conditional: {
    label: '조건형',
    description: '조건을 나타내는 형태',
    examples: '食べる → 食べれば',
  },

  // === 스페인어 특수 ===
  preterite: {
    label: '점과거',
    description: '스페인어 완료 과거 시제',
    examples: 'hablar → hablé',
  },
  imperfect: {
    label: '불완료과거',
    description: '스페인어 미완료 과거 시제',
    examples: 'hablar → hablaba',
  },
  subjunctive_present: {
    label: '접속법 현재',
    description: '스페인어 접속법 현재 시제',
    examples: 'hablar → hable',
  },
  subjunctive_imperfect: {
    label: '접속법 과거',
    description: '스페인어 접속법 과거 시제',
    examples: 'hablar → hablara',
  },
  imperative: {
    label: '명령형',
    description: '명령을 나타내는 형태',
    examples: 'hablar → habla (tú)',
  },

  // === 기타 ===
  auxiliary: {
    label: '조동사',
    description: '함께 쓰이는 조동사',
    examples: 'have, be, will',
  },
  prefix: {
    label: '접두사',
    description: '단어 앞에 붙는 요소',
    examples: 'un-, re-, pre-',
  },
  suffix: {
    label: '접미사',
    description: '단어 뒤에 붙는 요소',
    examples: '-tion, -ly, -ness',
  },
  root: {
    label: '어근',
    description: '단어의 핵심 의미 부분',
    examples: 'spect (보다) → inspect, spectator',
  },
  synonym: {
    label: '동의어',
    description: '비슷한 의미의 단어',
    examples: 'big = large',
  },
  antonym: {
    label: '반의어',
    description: '반대 의미의 단어',
    examples: 'big ↔ small',
  },
  usage_note: {
    label: '용법 참고',
    description: '사용 시 주의사항이나 참고사항',
    examples: '구어체에서 주로 사용',
  },
  register: {
    label: '어체/문체',
    description: '격식/비격식 등 언어 사용역',
    examples: 'formal, informal, slang, literary',
  },

  // === 추가 속성 ===
  forms: {
    label: '변화형',
    description: '성/수에 따른 단어 변화형',
    examples: 'masculine: amigo, feminine: amiga',
  },
  future: {
    label: '미래형',
    description: '동사의 미래 시제 형태',
    examples: 'ir → iré, hablar → hablaré',
  },
  present: {
    label: '현재형',
    description: '동사의 현재 시제 형태',
    examples: 'speak → speaks, go → goes',
  },
  romanji: {
    label: '로마자 표기',
    description: '일본어를 알파벳(ABC)으로 표기한 것',
    examples: 'あ → a, か → ka, こんにちは → konnichiwa',
  },
  romaji: {
    label: '로마자 표기',
    description: '일본어를 알파벳(ABC)으로 표기한 것',
    examples: 'あ → a, か → ka, こんにちは → konnichiwa',
  },
  kana: {
    label: '가나 문자',
    description: '일본어 표음문자 (히라가나/가타카나)',
    examples: 'あ, ア, か, カ',
  },
  hiragana: {
    label: '히라가나',
    description: '일본어 히라가나 문자',
    examples: 'あ, い, う, え, お',
  },
  katakana: {
    label: '가타카나',
    description: '일본어 가타카나 문자',
    examples: 'ア, イ, ウ, エ, オ',
  },
  type: {
    label: '글자 종류',
    description: '히라가나/가타카나/한자 등 문자 분류',
    examples: 'hiragana (히라가나), katakana (가타카나), kanji (한자)',
  },
  row: {
    label: '행',
    description: '일본어 가나의 행 분류',
    examples: 'あ행, か행, さ행',
  },
  third_person: {
    label: '3인칭 단수',
    description: '3인칭 단수 현재형',
    examples: 'go → goes, have → has',
  },
  perfect: {
    label: '완료형',
    description: '완료 시제 형태',
    examples: 'have gone, has eaten',
  },
  continuous: {
    label: '진행형',
    description: '진행 시제 형태',
    examples: 'is going, are eating',
  },
  definition: {
    label: '정의',
    description: '단어의 사전적 정의',
  },
  etymology: {
    label: '어원',
    description: '단어의 기원이나 유래',
    examples: 'Latin: spectare (보다)',
  },
  frequency: {
    label: '빈도',
    description: '사용 빈도 (high/medium/low)',
    examples: 'high, medium, low',
  },

  // === 성/수 변화형 (중첩 키) ===
  'm.sg': {
    label: '남성 단수',
    description: '남성 단수형',
    examples: 'bonito, alto',
  },
  'm.pl': {
    label: '남성 복수',
    description: '남성 복수형',
    examples: 'bonitos, altos',
  },
  'f.sg': {
    label: '여성 단수',
    description: '여성 단수형',
    examples: 'bonita, alta',
  },
  'f.pl': {
    label: '여성 복수',
    description: '여성 복수형',
    examples: 'bonitas, altas',
  },
  'n.sg': {
    label: '중성 단수',
    description: '중성 단수형',
  },
  'n.pl': {
    label: '중성 복수',
    description: '중성 복수형',
  },
  masculine: {
    label: '남성형',
    description: '남성 명사/형용사 형태',
    examples: 'amigo, bonito',
  },
  feminine: {
    label: '여성형',
    description: '여성 명사/형용사 형태',
    examples: 'amiga, bonita',
  },
  neuter: {
    label: '중성형',
    description: '중성 명사 형태',
  },
  singular: {
    label: '단수형',
    description: '단수 형태',
  },
  sg: {
    label: '단수',
    description: '단수 형태',
  },
  pl: {
    label: '복수',
    description: '복수 형태',
  },
}

/**
 * Get grammar label by key
 */
export function getGrammarLabel(key: string): string {
  return GRAMMAR_PROPERTIES[key]?.label || key
}

/**
 * Get grammar description by key
 */
export function getGrammarDescription(key: string): string {
  return GRAMMAR_PROPERTIES[key]?.description || ''
}

/**
 * Get grammar examples by key
 */
export function getGrammarExamples(key: string): string {
  return GRAMMAR_PROPERTIES[key]?.examples || ''
}

/**
 * Common grammar templates by language and part of speech
 * 언어별, 품사별 일반적인 문법 속성 템플릿
 */
export const GRAMMAR_TEMPLATES: Record<string, Record<string, string[]>> = {
  // 영어
  en: {
    noun: ['plural', 'countable'],
    verb: ['past', 'past_participle', 'present_participle', 'irregular'],
    adjective: ['comparative', 'superlative'],
    adverb: ['comparative', 'superlative'],
  },
  // 일본어
  ja: {
    noun: ['reading', 'jlpt_level'],
    verb: ['conjugation', 'transitivity', 'te_form', 'ta_form', 'negative', 'potential', 'jlpt_level'],
    adjective: ['conjugation', 'jlpt_level'],  // い형용사, な형용사
    character: ['reading', 'onyomi', 'kunyomi'],
  },
  // 스페인어
  es: {
    noun: ['gender', 'plural', 'article'],
    verb: ['conjugation', 'irregular', 'preterite', 'imperfect', 'subjunctive_present'],
    adjective: ['gender', 'plural'],
  },
  // 한국어
  ko: {
    verb: ['conjugation', 'formality'],
    adjective: ['conjugation'],
  },
}

/**
 * Get suggested grammar properties for a language and part of speech
 */
export function getSuggestedGrammarProperties(languageCode: string, partOfSpeech: string): string[] {
  return GRAMMAR_TEMPLATES[languageCode]?.[partOfSpeech] || []
}

/**
 * Japanese grammar term translations to Korean
 * 일본어 문법 용어 → 한국어 번역
 */
export const JAPANESE_GRAMMAR_TERMS: Record<string, string> = {
  // 동사 유형
  '五段動詞': '5단 동사 (う동사)',
  '一段動詞': '1단 동사 (る동사)',
  'カ変動詞': '카변 동사 (来る)',
  'サ変動詞': '사변 동사 (する)',
  '五段': '5단 동사',
  '一段': '1단 동사',
  'カ変': '카변 (来る)',
  'サ変': '사변 (する)',

  // 형용사 유형
  'い形容詞': 'い형용사 (い로 끝남)',
  'な形容詞': 'な형용사 (명사형)',
  'イ形容詞': 'い형용사',
  'ナ形容詞': 'な형용사',

  // 자타동사
  '自動詞': '자동사',
  '他動詞': '타동사',

  // 기타
  '不規則': '불규칙',
  '規則': '규칙',
}

/**
 * Translate Japanese grammar terms to Korean
 * Returns the original value if no translation found
 */
export function translateGrammarValue(value: string): string {
  return JAPANESE_GRAMMAR_TERMS[value] || value
}
