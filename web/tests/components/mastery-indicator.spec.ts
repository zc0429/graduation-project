import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import MasteryIndicator from '@/components/MasteryIndicator.vue'

describe('MasteryIndicator', () => {
  it('rounds and exposes the value with progressbar semantics', () => {
    const wrapper = mount(MasteryIndicator, { props: { value: 68.6 } })

    expect(wrapper.attributes('role')).toBe('progressbar')
    expect(wrapper.attributes('aria-valuenow')).toBe('69')
    expect(wrapper.attributes('aria-valuetext')).toBe('掌握度 69%')
    expect(wrapper.classes()).toContain('is-medium')
    expect(wrapper.get('.mastery-track i').attributes('style')).toContain('width: 69%')
  })

  it('clamps out-of-range values', async () => {
    const wrapper = mount(MasteryIndicator, { props: { value: 140 } })

    expect(wrapper.attributes('aria-valuenow')).toBe('100')
    expect(wrapper.classes()).toContain('is-high')

    await wrapper.setProps({ value: -10 })
    expect(wrapper.attributes('aria-valuenow')).toBe('0')
    expect(wrapper.classes()).toContain('is-low')
  })
})
