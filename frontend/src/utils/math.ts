import katex from 'katex'

/** 同时匹配 $$...$$（块级）与 $...$（行内）。 */
const MATH_PATTERN = /\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$/g

export function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function fallback(tex: string, displayMode: boolean): string {
  const raw = displayMode ? `$$${tex}$$` : `$${tex}$`
  return `<span class="math-fallback">${escapeHtml(raw)}</span>`
}

function renderMath(tex: string, displayMode: boolean): string {
  try {
    return katex.renderToString(tex, {
      displayMode,
      // 语法错误时 KaTeX 自己会用红色标出原文，而不是抛异常
      throwOnError: false,
      strict: 'ignore',
      trust: false,
      output: 'html',
    })
  } catch {
    // 兜底：KaTeX 仍可能因极端输入抛错，退回可读原文，绝不丢整段内容
    return fallback(tex, displayMode)
  }
}

/**
 * 把 markdown_latex / text_latex 文本转成可安全 v-html 的 HTML。
 *
 * 非公式部分先做 HTML 转义，因此原始文本里的标签不会被执行。
 */
export function renderRichText(source: string, options: { math?: boolean } = {}): string {
  const text = source ?? ''
  const useMath = options.math !== false
  let html = ''
  let cursor = 0

  if (useMath) {
    MATH_PATTERN.lastIndex = 0
    let match: RegExpExecArray | null
    while ((match = MATH_PATTERN.exec(text)) !== null) {
      html += escapeHtml(text.slice(cursor, match.index)).replace(/\n/g, '<br>')
      const isDisplay = match[1] !== undefined
      html += renderMath(isDisplay ? match[1] : match[2], isDisplay)
      cursor = match.index + match[0].length
    }
  }

  html += escapeHtml(text.slice(cursor)).replace(/\n/g, '<br>')
  return html
}
