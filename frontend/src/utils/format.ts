/** 得分按原值显示，去掉浮点噪声，不做四舍五入到整数。 */
export function formatScore(value: number): string {
  if (!Number.isFinite(value)) {
    return String(value)
  }
  if (Number.isInteger(value)) {
    return String(value)
  }
  return String(Number(value.toFixed(4)))
}

export function formatDateTime(value: string | null): string {
  if (!value) {
    return ''
  }
  const parsed = new Date(value.endsWith('Z') ? value : `${value}Z`)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  const pad = (input: number) => String(input).padStart(2, '0')
  return (
    `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())} ` +
    `${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`
  )
}

export function gradingSourceLabel(source: string): string {
  if (source === 'AI') return 'AI 评分'
  if (source === 'TEACHER') return '教师评分'
  return source
}

export function questionTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    CALCULATION: '计算题',
    SINGLE_CHOICE: '单选题',
    PROOF: '证明题',
    SHORT_ANSWER: '简答题',
  }
  return labels[type] ?? type
}

/** 列表里的题干摘要：去掉公式标记，避免列表里出现大片 LaTeX 源码。 */
export function plainPreview(source: string, maxLength = 60): string {
  const text = (source ?? '')
    .replace(/\$\$[\s\S]*?\$\$/g, ' ')
    .replace(/\$[^$\n]*?\$/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  return text.length > maxLength ? `${text.slice(0, maxLength)}…` : text
}
