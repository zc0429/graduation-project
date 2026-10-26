import { describe, expect, it } from 'vitest'
import { plainTextToHtml, questionHtml, questionText } from '@/utils/question-content'

describe('question content boundary', () => {
  it('keeps legacy plain text, mathematical comparisons and line breaks', () => {
    const text = '已知 0 < x < 3，A & B\n求 x²。'
    expect(questionText(text)).toBe(text)
    expect(questionText(questionHtml(text))).toBe(text)
    expect(questionHtml(text)).toContain('&lt;')
  })

  it('removes scripts, event handlers, links, styles and embedded resources', () => {
    const html = questionHtml('<p onclick="alert(1)" style="color:red">题<strong>干</strong>'
      + '<img src=x onerror="alert(1)"><script>alert(1)</script>'
      + '<a href="javascript:alert(1)">链接文字</a><svg onload="alert(1)"></svg></p>')
    expect(html).toContain('<strong>干</strong>')
    expect(html).not.toMatch(/script|onclick|onerror|style=|href=|<img|<svg/)
    expect(questionText(html)).toBe('题干链接文字')
  })

  it('normalizes paragraphs, lists and superscripts without HTML in AI text', () => {
    const html = '<p>求 x<sup>2</sup> + H<sub>2</sub>O</p><ol><li>A</li><li>B<br>C</li></ol>'
    expect(questionText(html)).toBe('求 x^(2) + H_(2)O\nA\nB\nC')
    expect(questionText('<p><br></p>')).toBe('')
  })

  it('treats recognition results as plain text even when they contain markup', () => {
    const candidate = '判断 <strong>是否为标签</strong>，2 < 3'
    expect(questionText(plainTextToHtml(candidate))).toBe(candidate)
    expect(questionHtml(plainTextToHtml(candidate))).not.toContain('<strong>')
  })
})
