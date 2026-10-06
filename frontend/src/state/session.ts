import { ref } from 'vue'

import { api } from '../api/client'
import type { Student } from '../api/types'

/** 当前登录学生；null 表示未登录。 */
export const currentStudent = ref<Student | null>(null)

let pending: Promise<Student | null> | null = null

export async function ensureSession(): Promise<Student | null> {
  if (currentStudent.value) {
    return currentStudent.value
  }
  if (!pending) {
    pending = api
      .me()
      .then((response) => {
        currentStudent.value = response.student
        return response.student
      })
      .catch(() => {
        currentStudent.value = null
        return null
      })
      .finally(() => {
        pending = null
      })
  }
  return pending
}

export function setStudent(student: Student): void {
  currentStudent.value = student
}

export function clearSession(): void {
  currentStudent.value = null
}
