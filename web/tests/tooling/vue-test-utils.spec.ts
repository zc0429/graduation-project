import { defineComponent, h, ref } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

const CounterHarness = defineComponent({
  setup() {
    const count = ref(0)
    return () =>
      h(
        'button',
        {
          type: 'button',
          onClick: () => {
            count.value += 1
          },
        },
        `已校正 ${count.value} 次`,
      )
  },
})

describe('Vue component test harness', () => {
  it('mounts a component and handles an interaction', async () => {
    const wrapper = mount(CounterHarness)

    await wrapper.get('button').trigger('click')

    expect(wrapper.get('button').text()).toBe('已校正 1 次')
  })
})
