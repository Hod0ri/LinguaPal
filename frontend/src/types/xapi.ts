/**
 * xAPI (Experience API) Types
 *
 * Types for xAPI statements and LRS integration.
 * Based on xAPI 1.0.3 specification.
 */

// xAPI Verbs
export const XAPIVerbs = {
  INITIALIZED: 'http://adlnet.gov/expapi/verbs/initialized',
  TERMINATED: 'http://adlnet.gov/expapi/verbs/terminated',
  ANSWERED: 'http://adlnet.gov/expapi/verbs/answered',
  PROGRESSED: 'http://adlnet.gov/expapi/verbs/progressed',
  COMPLETED: 'http://adlnet.gov/expapi/verbs/completed',
  PASSED: 'http://adlnet.gov/expapi/verbs/passed',
  FAILED: 'http://adlnet.gov/expapi/verbs/failed',
} as const

export type XAPIVerbId = (typeof XAPIVerbs)[keyof typeof XAPIVerbs]

// xAPI Actor (Agent)
export interface XAPIActor {
  objectType: 'Agent'
  mbox: string // mailto:email@example.com
  name?: string
}

// xAPI Verb
export interface XAPIVerb {
  id: string
  display: Record<string, string>
}

// xAPI Activity Definition
export interface XAPIActivityDefinition {
  type?: string
  name?: Record<string, string>
  description?: Record<string, string>
}

// xAPI Object (Activity)
export interface XAPIObject {
  objectType: 'Activity'
  id: string
  definition?: XAPIActivityDefinition
}

// xAPI Score
export interface XAPIScore {
  scaled?: number // -1 to 1
  raw?: number
  min?: number
  max?: number
}

// xAPI Result
export interface XAPIResult {
  success?: boolean
  completion?: boolean
  response?: string
  score?: XAPIScore
  duration?: string // ISO 8601 duration
}

// xAPI Context
export interface XAPIContext {
  registration?: string // UUID
  extensions?: Record<string, unknown>
}

// xAPI Statement
export interface XAPIStatement {
  id?: string
  actor: XAPIActor
  verb: XAPIVerb
  object: XAPIObject
  result?: XAPIResult
  context?: XAPIContext
  timestamp?: string
}

// Quiz Session for tracking xAPI registration
export interface QuizSession {
  quizId: number
  quizType: 'gana' | 'word'
  registration: string // UUID
  startedAt: string
  totalQuestions: number
  currentQuestion: number
  correctCount: number
}

// LRS API Response types
export interface LRSStatementResponse {
  id: string
}

export interface LRSAboutResponse {
  version: string[]
  extensions?: Record<string, unknown>
}

// Quiz Event Types for middleware
export type QuizEventType =
  | 'quiz_start'
  | 'question_answered'
  | 'quiz_completed'
  | 'quiz_abandoned'

export interface QuizEvent {
  type: QuizEventType
  quizId: number
  quizType: 'gana' | 'word'
  registration?: string
  data?: Record<string, unknown>
}

// Activity Types
export const XAPIActivityTypes = {
  ASSESSMENT: 'http://adlnet.gov/expapi/activities/assessment',
  QUESTION: 'http://adlnet.gov/expapi/activities/question',
  COURSE: 'http://adlnet.gov/expapi/activities/course',
  MODULE: 'http://adlnet.gov/expapi/activities/module',
} as const
