import type { TestingLibraryMatchers } from '@testing-library/jest-dom/matchers'

declare global {
  namespace Vi {
    interface Matchers extends TestingLibraryMatchers<any, any> {}
  }
}

export {}
