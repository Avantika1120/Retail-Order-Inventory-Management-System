import { FormEvent, useEffect, useMemo, useState } from 'react'

type Product = { id:number; sku:string; name:string; category:string; price:number }
type Customer = { id:number; name:string; email:string }
type Inventory = { product_id:number; quantity_on_hand:number; reorder_level:number }
type Order = { id:number; customer_id:number; status:string; total_amount:number }
type Review = { id:string; product_id:number; customer_id?:number; rating:number; title:string; body:string }

const API = (window as Window & { __RETAIL_API_URL__?: string }).__RETAIL_API_URL__ || 'http://localhost:8000'

export default function App() {
  const [products, setProducts] = useState<Product[]>([])
  const [customers, setCustomers] = useState<Customer[]>([])
  const [inventory, setInventory] = useState<Inventory[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [selectedProduct, setSelectedProduct] = useState<number | null>(null)
  const [reviews, setReviews] = useState<Review[]>([])
  const [summary, setSummary] = useState('')
  const [busy, setBusy] = useState(false)

  const load = async () => {
    const [p, c, i, o] = await Promise.all([
      fetch(`${API}/api/products`).then(r => r.json()),
      fetch(`${API}/api/customers`).then(r => r.json()),
      fetch(`${API}/api/inventory`).then(r => r.json()),
      fetch(`${API}/api/orders`).then(r => r.json())
    ])
    setProducts(p); setCustomers(c); setInventory(i); setOrders(o)
    if (!selectedProduct && p.length) setSelectedProduct(p[0].id)
  }

  useEffect(() => { load().catch(console.error) }, [])
  useEffect(() => {
    if (!selectedProduct) return
    fetch(`${API}/api/products/${selectedProduct}/reviews`)
      .then(r => r.json()).then(setReviews).catch(console.error)
  }, [selectedProduct])

  const lowStock = useMemo(() => inventory.filter(x => x.quantity_on_hand <= x.reorder_level), [inventory])
  const revenue = useMemo(() => orders.filter(x => x.status !== 'cancelled').reduce((sum, x) => sum + Number(x.total_amount), 0), [orders])

  const addProduct = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault(); setBusy(true)
    const data = new FormData(e.currentTarget)
    await fetch(`${API}/api/products`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({
      sku:data.get('sku'), name:data.get('name'), category:data.get('category'), price:Number(data.get('price')), opening_stock:Number(data.get('stock')), reorder_level:5
    }) })
    e.currentTarget.reset(); await load(); setBusy(false)
  }

  const addCustomer = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const data = new FormData(e.currentTarget)
    await fetch(`${API}/api/customers`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ name:data.get('name'), email:data.get('email') }) })
    e.currentTarget.reset(); await load()
  }

  const addOrder = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const data = new FormData(e.currentTarget)
    const response = await fetch(`${API}/api/orders`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({
      customer_id:Number(data.get('customer_id')), items:[{ product_id:Number(data.get('product_id')), quantity:Number(data.get('quantity')) }]
    }) })
    if (!response.ok) alert((await response.json()).detail || 'Could not create order')
    else { e.currentTarget.reset(); await load() }
  }

  const advanceOrder = async (order: Order) => {
    const next: Record<string,string> = { created:'processing', processing:'shipped', shipped:'completed' }
    if (!next[order.status]) return
    await fetch(`${API}/api/orders/${order.id}/status`, { method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({status:next[order.status]}) })
    await load()
  }

  const restock = async (productId: number) => {
    await fetch(`${API}/api/inventory/${productId}/restock`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({quantity:10}) })
    await load()
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
      <article><span>Customers</span><strong>{customers.length}</strong></article>
      <article><span>Order revenue</span><strong>${revenue.toFixed(2)}</strong></article>
      <article><span>Low stock SKUs</span><strong>{lowStock.length}</strong></article>
    </section>

    <section className="grid two">
      <article className="card"><h2>Catalog & inventory</h2><div className="tableWrap"><table><thead><tr><th>SKU</th><th>Product</th><th>Category</th><th>Price</th><th>Stock</th><th></th></tr></thead><tbody>{products.map(p => {
        const inv = inventory.find(i => i.product_id === p.id)
        return <tr key={p.id}><td>{p.sku}</td><td>{p.name}</td><td>{p.category}</td><td>${Number(p.price).toFixed(2)}</td><td className={inv && inv.quantity_on_hand <= inv.reorder_level ? 'danger':''}>{inv?.quantity_on_hand ?? 0}</td><td><button className="mini" onClick={() => restock(p.id)}>+10</button></td></tr>
      })}</tbody></table></div></article>

      <article className="card"><h2>Add product</h2><form onSubmit={addProduct} className="form"><input name="sku" placeholder="SKU" required/><input name="name" placeholder="Product name" required/><input name="category" placeholder="Category" required/><input name="price" type="number" step="0.01" placeholder="Price" required/><input name="stock" type="number" placeholder="Opening stock" required/><button disabled={busy}>{busy ? 'Saving...' : 'Create product'}</button></form></article>
    </section>

    <section className="grid two">
      <article className="card"><h2>Customers</h2><form onSubmit={addCustomer} className="form compact"><input name="name" placeholder="Customer name" required/><input name="email" type="email" placeholder="Email" required/><button>Create customer</button></form><div className="list">{customers.slice(-5).map(c => <div className="listItem" key={c.id}><strong>{c.name}</strong><span>{c.email}</span></div>)}</div></article>
      <article className="card"><h2>Create order</h2><form onSubmit={addOrder} className="form"><select name="customer_id" required defaultValue=""><option value="" disabled>Choose customer</option>{customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select><select name="product_id" required defaultValue=""><option value="" disabled>Choose product</option>{products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select><input name="quantity" type="number" min="1" placeholder="Quantity" required/><button>Create order & reserve stock</button></form></article>
    </section>

    <section className="grid two">
      <article className="card"><h2>Order fulfillment</h2>{orders.length ? <div className="tableWrap"><table><thead><tr><th>Order</th><th>Customer</th><th>Status</th><th>Total</th><th></th></tr></thead><tbody>{orders.map(o => <tr key={o.id}><td>#{o.id}</td><td>{customers.find(c => c.id === o.customer_id)?.name || o.customer_id}</td><td><span className={`pill ${o.status}`}>{o.status}</span></td><td>${Number(o.total_amount).toFixed(2)}</td><td>{['created','processing','shipped'].includes(o.status) && <button className="mini" onClick={() => advanceOrder(o)}>Advance</button>}</td></tr>)}</tbody></table></div> : <p className="muted">Create a customer and order to start the fulfillment workflow.</p>}</article>

      <article className="card"><div className="row"><h2>Product reviews</h2><select value={selectedProduct ?? ''} onChange={e => setSelectedProduct(Number(e.target.value))}>{products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></div>
        <div className="reviews">{reviews.map(r => <div className="review" key={r.id}><strong>{'★'.repeat(r.rating)}{'☆'.repeat(5-r.rating)} {r.title}</strong><p>{r.body}</p></div>)}</div>
        <form onSubmit={addReview} className="form compact"><input name="rating" type="number" min="1" max="5" placeholder="Rating 1-5" required/><input name="title" placeholder="Review title" required/><textarea name="body" placeholder="Review text" required/><button>Add review</button></form>
        <button className="secondary" onClick={summarize}>Generate ChatGPT Review Insights</button>
        {summary && <pre className="summary">{summary}</pre>}
      </article>
    </section>
  </main>
}
