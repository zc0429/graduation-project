import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import LearningResources from '@/components/LearningResources.vue'
import { learningApi, practiceApi } from '@/api/learning'
vi.mock('@/api/learning', () => ({ learningApi: { knowledge: vi.fn(), next: vi.fn() }, practiceApi: { submit: vi.fn() } }))
const original = { questionId: 1, variantId: null, stem: '原题', answer: '答案', difficulty: 2, source: 'original' as const }
const setup = () => mount(LearningResources, { props: { questionId: 1, revision: 'a' }, global: { plugins: [ElementPlus] } })
const click = async (w: ReturnType<typeof setup>, text: string) => { await w.findAll('button').find(b => b.text() === text)!.trigger('click'); await flushPromises() }
beforeEach(() => { vi.resetAllMocks() })
describe('LearningResources', () => {
  it('does not request AI on mount and reports saved knowledge reuse', async () => {
    const w = setup(); expect(learningApi.knowledge).not.toHaveBeenCalled(); expect(learningApi.next).not.toHaveBeenCalled()
    vi.mocked(learningApi.knowledge).mockResolvedValue({ id: 2, questionId: 1, content: '知识讲解', reused: true })
    await click(w, '获取知识内容'); expect(w.text()).toContain('已复用保存的知识内容'); w.unmount()
  })
  it('ignores an old response after switching questions', async () => {
    let resolve!: (v: typeof original) => void
    vi.mocked(learningApi.next).mockImplementation(() => new Promise(r => { resolve = r }))
    const w = setup(); await click(w, '开始练习'); await w.setProps({ questionId: 2, revision: 'b' })
    resolve(original); await flushPromises(); expect(w.text()).not.toContain('优先练习本人原题'); w.unmount()
  })
  it('requires self assessment, saves a single target and allows explicit repetition', async () => {
    vi.mocked(learningApi.next).mockResolvedValue(original); vi.mocked(practiceApi.submit).mockResolvedValue(null as never)
    const w = setup(); await click(w, '开始练习'); await click(w, '保存本次练习'); expect(practiceApi.submit).not.toHaveBeenCalled()
    await w.get('input[type="radio"][value="1"]').setValue(); await click(w, '保存本次练习')
    expect(practiceApi.submit).toHaveBeenCalledWith(expect.objectContaining({ questionId: 1, isCorrect: 1 })); expect(vi.mocked(practiceApi.submit).mock.calls[0]![0]).not.toHaveProperty('variantId')
    expect(w.emitted('practiced')).toHaveLength(1); await click(w, '重新练习本题'); expect(learningApi.next).toHaveBeenCalledTimes(1)
    await w.get('input[type="radio"][value="0"]').setValue(); await click(w, '保存本次练习'); expect(w.emitted('practiced')).toHaveLength(2); w.unmount()
  })
  it('retains a question when generation fails and does not fake a successful save', async () => {
    vi.mocked(learningApi.next).mockResolvedValueOnce({ ...original, questionId: null, variantId: 7, source: 'existing' }).mockRejectedValueOnce(new Error('生成失败'))
    vi.mocked(practiceApi.submit).mockRejectedValue(new Error('保存失败'))
    const w = setup(); await click(w, '开始练习'); await click(w, '继续练习'); expect(w.text()).toContain('复用本人已有未练题'); expect(w.text()).toContain('生成失败')
    await w.get('input[type="radio"][value="1"]').setValue(); await click(w, '保存本次练习')
    expect(vi.mocked(practiceApi.submit).mock.calls[0]![0]).not.toHaveProperty('questionId'); expect(w.emitted('practiced')).toBeUndefined(); expect(w.text()).toContain('保存失败'); w.unmount()
  })
})
