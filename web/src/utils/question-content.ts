import DOMPurify from 'dompurify'

// No links, images, inline styles or arbitrary attributes in a question stem.
const tags = ['p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'strike', 'del', 'ul', 'ol', 'li', 'sub', 'sup']
const markup = /<\s*\/?\s*(?:p|br|strong|b|em|i|u|s|strike|del|ul|ol|li|sub|sup|script|style|img|svg|math|iframe|object|embed|div|span)\b[^>]*>/i

export function plainTextToHtml(value: string): string {
  const escaped = value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  return `<p>${escaped.replace(/\r\n?/g, '\n').replace(/\n/g, '<br>')}</p>`
}

export function questionHtml(value: string | null | undefined): string {
  if (!value) return ''
  return DOMPurify.sanitize(markup.test(value) ? value : plainTextToHtml(value), {
    ALLOWED_TAGS: tags,
    ALLOWED_ATTR: [],
    ALLOW_DATA_ATTR: false,
    ALLOW_ARIA_ATTR: false,
  })
}

export function questionText(value: string | null | undefined): string {
  if (!value) return ''
  if (!markup.test(value)) return value.replace(/\r\n?/g, '\n').trim()
  const element = document.createElement('div')
  element.innerHTML = questionHtml(value)
  element.querySelectorAll('sup, sub').forEach((node) => {
    node.replaceWith(`${node.tagName === 'SUP' ? '^' : '_'}(${node.textContent})`)
  })
  element.querySelectorAll('br').forEach((node) => node.replaceWith('\n'))
  element.querySelectorAll('p, li, ul, ol').forEach((node) => node.append('\n'))
  return (element.textContent || '').replace(/\u00a0/g, ' ').replace(/\n{3,}/g, '\n\n').trim()
}
