import { FormEvent, useEffect, useMemo, useState } from 'react'

type Product = { id:number; sku:string; name:string; category:string; price:number }
type Inventory = { product_id:number; quantity_on_hand:number; reorder_level:number }
type Order = { id:number; customer_id:number; status:string; total_amount:number }
type Review = { id:string; product_id:number; customer_id?:number; rating:number; title:string; body:string }

const API = (window as Window & { __RETAIL_API_URL__?: string }).__RETAIL_API_URL__ || 'http://localhost:8000'

export default function App() {
  const [products, setProducts] = useState<Product[]>([])
  const [inventory, setInventory] = useState<Inventory[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [selectedProduct, setSelectedProduct] = useState<number | null>(null)
  const [reviews, setReviews] = useState<Review[]>([])
  const [summary, setSummary] = useState('')
  const [busy, setBusy] = useState(false)

  const load = async () => {
    const [p, i, o] = await Promise.all([
      fetch(`${API}/api/products`).then(r => r.json()),
      fetch(`${API}/api/inventory`).then(r => r.json()),
      fetch(`${API}/api/orders`).then(r => r.json())
    ])
    setProducts(p); setInventory(i); setOrders(o)
    if (!selectedProduct && p.length) setSelectedProduct(p[0].id)
  }

  useEffect(() => { load().catch(console.error) }, [])
  useEffect(() => {
    if (!selectedProduct) return
    fetch(`${API}/api/products/${selectedProduct}/reviews`)
      .then(r => r.json()).then(setReviews).catch(console.error)
  }, [selectedProduct])

  const lowStock = useMemo(() => inventory.filter(x => x.quantity_on_hand <= x.reorder_level), [inventory])
  const revenue = useMemo(() => orders.reduce((sum, x) => sum + Number(x.total_amount), 0), [orders])

  const addProduct = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault(); setBusy(true)
    const data = new FormData(e.currentTarget)
    await fetch(`${API}/api/products`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({
      sku:data.get('sku'), name:data.get('name'), category:data.get('category'), price:Number(data.get('price')), opening_stock:Number(data.get('stock')), reorder_level:5
    }) })
    e.currentTarget.reset(); await load(); setBusy(false)
  }

  const addReview = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault(); if (!selectedProduct) return
    const data = new FormData(e.currentTarget)
    await fetch(`${API}/api/reviews`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({
      product_id:selectedProduct, rating:Number(data.get('rating')), title:data.get('title'), body:data.get('body')
    }) })
    e.currentTarget.reset()
    setReviews(await fetch(`${API}/api/products/${selectedProduct}/reviews`).then(r => r.json()))
  }

  const summarize = async () => {
    if (!selectedProduct) return
    setSummary('Generating ChatGPT review insights...')
    const r = await fetch(`${API}/api/products/${selectedProduct}/review-summary`, { method:'POST' })
    const body = await r.json()
    setSummary(r.ok ? body.summary : body.detail)
  }

  return <main className="shell">
    <header className="hero">
      <div><p className="eyebrow">FULL-STACK RETAIL OPERATIONS</p><h1>Order & Inventory Control Center</h1><p>React + TypeScript frontend backed by FastAPI, PostgreSQL, MongoDB and optional ChatGPT review insights.</p></div>
      <div className="status">● API-connected</div>
    </header>

    <section className="kpis">
      <article><span>Products</span><strong>{products.length}</strong></article>
      <article><span>Orders</span><strong>{orders.length}</strong></article>
      <article><span>Order revenue</span><strong>${revenue.toFixed(2)}</strong></article>
      <article><span>Low stock SKUs</span><strong>{lowStock.length}</strong></article>
    </section>

    <section className="grid two">
      <article className="card"><h2>Catalog & inventory</h2><div className="tableWrap"><table><thead><tr><th>SKU</th><th>Product</th><th>Category</th><th>Price</th><th>Stock</th></tr></thead><tbody>{products.map(p => {
        const inv = inventory.find(i => i.product_id === p.id)
        return <tr key={p.id}><td>{p.sku}</td><td>{p.name}</td><td>{p.category}</td><td>${Number(p.price).toFixed(2)}</td><td className={inv && inv.quantity_on_hand <= inv.reorder_level ? 'danger':''}>{inv?.quantity_on_hand ?? 0}</td></tr>
      })}</tbody></table></div></article>

      <article className="card"><h2>Add product</h2><form onSubmit={addProduct} className="form"><input name="sku" placeholder="SKU" required/><input name="name" placeholder="Product name" required/><input name="category" placeholder="Category" required/><input name="price" type="number" step="0.01" placeholder="Price" required/><input name="stock" type="number" placeholder="Opening stock" required/><button disabled={busy}>{busy ? 'Saving...' : 'Create product'}</button></form></article>
    </section>

    <section className="grid two">
      <article className="card"><h2>Recent orders</h2>{orders.length ? <div className="tableWrap"><table><thead><tr><th>Order</th><th>Customer</th><th>Status</th><th>Total</th></tr></thead><tbody>{orders.map(o => <tr key={o.id}><td>#{o.id}</td><td>{o.customer_id}</td><td>{o.status}</td><td>${Number(o.total_amount).toFixed(2)}</td></tr>)}</tbody></table></div> : <p className="muted">No orders yet. Use the FastAPI Swagger UI or API endpoints to create customers and orders.</p>}</article>

      <article className="card"><div className="row"><h2>Product reviews</h2><select value={selectedProduct ?? ''} onChange={e => setSelectedProduct(Number(e.target.value))}>{products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></div>
        <div className="reviews">{reviews.map(r => <div className="review" key={r.id}><strong>{'★'.repeat(r.rating)}{'☆'.repeat(5-r.rating)} {r.title}</strong><p>{r.body}</p></div>)}</div>
        <form onSubmit={addReview} className="form compact"><input name="rating" type="number" min="1" max="5" placeholder="Rating 1-5" required/><input name="title" placeholder="Review title" required/><textarea name="body" placeholder="Review text" required/><button>Add review</button></form>
        <button className="secondary" onClick={summarize}>Generate ChatGPT Review Insights</button>
        {summary && <pre className="summary">{summary}</pre>}
      </article>
    </section>
  </main>
}
