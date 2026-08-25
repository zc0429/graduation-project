import { afterEach, vi } from 'vitest'

class ResizeObserverMock {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}

Object.defineProperty(window, 'matchMedia', {
  configurable: true,
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

Object.defineProperty(globalThis, 'ResizeObserver', {
  configurable: true,
  writable: true,
  value: ResizeObserverMock,
})

class MemoryStorage implements Storage {
  private readonly values = new Map<string, string>()

  get length() {
    return this.values.size
  }

  clear() {
    this.values.clear()
  }

  getItem(key: string) {
    return this.values.get(key) ?? null
  }

  key(index: number) {
    return [...this.values.keys()][index] ?? null
  }

  removeItem(key: string) {
    this.values.delete(key)
  }

  setItem(key: string, value: string) {
    this.values.set(key, String(value))
  }
}

const browserLocalStorage = new MemoryStorage()
const browserSessionStorage = new MemoryStorage()

Object.defineProperty(window, 'localStorage', {
  configurable: true,
  value: browserLocalStorage,
})

Object.defineProperty(window, 'sessionStorage', {
  configurable: true,
  value: browserSessionStorage,
})

Object.defineProperty(globalThis, 'localStorage', {
  configurable: true,
  value: browserLocalStorage,
})

Object.defineProperty(globalThis, 'sessionStorage', {
  configurable: true,
  value: browserSessionStorage,
})

afterEach(() => {
  document.body.innerHTML = ''
  browserLocalStorage.clear()
  browserSessionStorage.clear()
})
