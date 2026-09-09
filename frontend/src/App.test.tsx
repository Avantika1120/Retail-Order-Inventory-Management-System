import { render, screen } from '@testing-library/react'
import App from './App'

beforeEach(() => {
  global.fetch = jest.fn((url: RequestInfo | URL) => {
    const value = String(url)
    const body = value.includes('/products') ? [] : value.includes('/inventory') ? [] : value.includes('/orders') ? [] : []
    return Promise.resolve({ ok: true, json: () => Promise.resolve(body) } as Response)
  }) as jest.Mock
})

test('renders the retail operations control center', async () => {
  render(<App />)
  expect(screen.getByText(/Order & Inventory Control Center/i)).toBeInTheDocument()
  expect(screen.getByText(/Catalog & inventory/i)).toBeInTheDocument()
})
