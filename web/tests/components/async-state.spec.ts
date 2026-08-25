import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AsyncState from '@/components/AsyncState.vue'

describe('AsyncState', () => {
  it('announces loading without exposing a retry action', () => {
    const wrapper = mount(AsyncState, { props: { status: 'loading' } })

    expect(wrapper.attributes('role')).toBe('status')
    expect(wrapper.attributes('aria-busy')).toBe('true')
    expect(wrapper.text()).toContain('正在整理内容')
    expect(wrapper.find('button').exists()).toBe(false)
  })

  it('uses alert semantics and emits retry for an error', async () => {
    const wrapper = mount(AsyncState, {
      props: { status: 'error', title: '周报加载失败', retryLabel: '再试一次' },
    })

    expect(wrapper.attributes('role')).toBe('alert')
    expect(wrapper.text()).toContain('周报加载失败')
    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })
})
