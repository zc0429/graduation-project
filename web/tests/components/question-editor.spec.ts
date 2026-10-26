import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { describe, expect, it } from 'vitest'
import QuestionEditor from '@/components/QuestionEditor.vue'
import QuestionContent from '@/components/QuestionContent.vue'

describe('rich question editor', () => {
  it('loads legacy text and updates externally supplied recognition candidates', async () => {
    const wrapper = mount(QuestionEditor, { props: { modelValue: '旧题 1 < 2\n下一行' } })
    await nextTick()
    await nextTick()
    await nextTick()
    expect(wrapper.get('[role=textbox]').text()).toContain('旧题 1 < 2')
    expect(wrapper.find('br').exists()).toBe(true)
    await wrapper.setProps({ modelValue: '<p>候选 x<sup>2</sup></p>' })
    expect(wrapper.get('[role=textbox] sup').text()).toBe('2')
    await wrapper.setProps({ disabled: true })
    expect(wrapper.get('[role=textbox]').attributes('contenteditable')).toBe('false')
    wrapper.unmount()
  })

  it('reopens saved formats and filters hostile historical content for display', async () => {
    const wrapper = mount(QuestionEditor, { props: { modelValue: '<p><strong>加粗</strong><sub>1</sub></p><ul><li>条件</li></ul>' } })
    await nextTick()
    await nextTick()
    await nextTick()
    expect(wrapper.get('[role=textbox] strong').text()).toBe('加粗')
    expect(wrapper.get('[role=textbox] sub').text()).toBe('1')
    expect(wrapper.get('[role=textbox] li').text()).toBe('条件')
    wrapper.unmount()
    const view = mount(QuestionContent, { props: { content: '<p onmouseover="x()">历史题<img src=x onerror="x()"></p>' } })
    expect(view.find('img').exists()).toBe(false)
    expect(view.html()).not.toContain('onmouseover')
    view.unmount()
  })
})
