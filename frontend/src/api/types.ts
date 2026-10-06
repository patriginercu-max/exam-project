/** 与后端 schema 一一对应的类型。字段名保持 camelCase。 */

export interface Student {
  id: string
  name: string
  login: string
  role: string
}

export interface LoginResponse {
  student: Student
}

export interface Note {
  cause: string
  content: string
  /** 从未保存过时为 null */
  updatedAt: string | null
}

export interface Course {
  id: string
  name: string
}

export type AnswerFormat = 'html' | 'text_latex'
export type GradingSource = 'AI' | 'TEACHER'

export interface WrongRecord {
  id: string
  courseId: string
  courseName: string | null
  assignmentId: string
  assignmentTitle: string | null
  questionId: string
  questionType: string

  questionText: string
  questionFormat: string

  originalAnswer: string
  answerFormat: AnswerFormat

  score: number
  maxScore: number
  /** null 表示来源没有公开评语，界面显示“暂无评语” */
  feedback: string | null
  gradingSource: GradingSource
  /** 空数组表示来源没有标注知识点，界面显示“未标注” */
  knowledgePoints: string[]

  note: Note
}

export interface RecordListResponse {
  records: WrongRecord[]
  total: number
}

export interface RecordFilters {
  courseId?: string
  knowledgePoint?: string
  keyword?: string
}
