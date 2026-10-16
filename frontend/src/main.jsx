import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const API = '/api/items'

const EMPTY_FORM = {
  name: '',
  sku: '',
  category: 'general',
  quantity: 0,
  unit_price: 0,
  reorder_level: 0,
}

function money(value) {
  return value.toLocaleString(undefined, { style: 'currency', currency: 'USD' })
}

function StatCard({ label, value, tone }) {
  return (
    <div className={`card card--${tone}`}>
      <span className="card__label">{label}</span>
      <span className="card__value">{value}</span>
    </div>
  )
}

function ItemForm({ onSubmit, onClose, busy }) {
  const [form, setForm] = useState(EMPTY_FORM)

  function change(field, value) {
    setForm((old) => ({ ...old, [field]: value }))
  }

  function submit(event) {
    event.preventDefault()
    onSubmit({
      ...form,
      quantity: Number(form.quantity),
      unit_price: Number(form.unit_price),
      reorder_level: Number(form.reorder_level),
    })
  }

  return (
    <div className="modal" role="dialog" aria-label="Add an item">
      <form className="modal__panel" onSubmit={submit}>
        <h2>Add an item</h2>
        <label>
          Name
          <input required value={form.name} onChange={(e) => change('name', e.target.value)} />
        </label>
        <label>
          SKU
          <input required value={form.sku} onChange={(e) => change('sku', e.target.value)} />
        </label>
        <label>
          Category
          <input value={form.category} onChange={(e) => change('category', e.target.value)} />
        </label>
        <div className="modal__row">
          <label>
            Quantity
            <input type="number" min="0" value={form.quantity} onChange={(e) => change('quantity', e.target.value)} />
          </label>
          <label>
            Unit price
            <input type="number" min="0" step="0.01" value={form.unit_price} onChange={(e) => change('unit_price', e.target.value)} />
          </label>
          <label>
            Reorder level
            <input type="number" min="0" value={form.reorder_level} onChange={(e) => change('reorder_level', e.target.value)} />
          </label>
        </div>
        <div className="modal__actions">
          <button type="button" className="btn btn--ghost" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn btn--primary" disabled={busy}>Save item</button>
        </div>
      </form>
    </div>
  )
}

function App() {
  const [items, setItems] = useState([])
  const [stats, setStats] = useState(null)
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [formOpen, setFormOpen] = useState(false)

  async function load() {
    try {
      setError(null)
      const [itemsResponse, statsResponse] = await Promise.all([
        fetch(API),
        fetch(`${API}/stats`),
      ])
      if (!itemsResponse.ok || !statsResponse.ok) {
        throw new Error('the backend answered with an error')
      }
      setItems(await itemsResponse.json())
      setStats(await statsResponse.json())
    } catch (problem) {
      setError(problem.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function createItem(payload) {
    setBusy(true)
    try {
      const response = await fetch(API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body.detail || 'the item was not saved')
      }
      setFormOpen(false)
      await load()
    } catch (problem) {
      setError(problem.message)
    } finally {
      setBusy(false)
    }
  }

  async function adjust(item, delta) {
    const next = Math.max(0, item.quantity + delta)
    await fetch(`${API}/${item.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantity: next }),
    })
    await load()
  }

  async function remove(item) {
    await fetch(`${API}/${item.id}`, { method: 'DELETE' })
    await load()
  }

  const visible = useMemo(() => {
    const text = search.trim().toLowerCase()
    return items.filter((item) => {
      if (filter === 'low' && !item.low_stock) return false
      if (filter === 'ok' && item.low_stock) return false
      if (!text) return true
      return (
        item.name.toLowerCase().includes(text) ||
        item.sku.toLowerCase().includes(text) ||
        item.category.toLowerCase().includes(text)
      )
    })
  }, [items, filter, search])

  const categories = useMemo(
    () => [...new Set(items.map((item) => item.category))].sort(),
    [items],
  )

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand__mark">SR</span>
          <span className="brand__name">StockRoom</span>
        </div>
        <nav className="nav">
          <span className="nav__item nav__item--active">Inventory</span>
          <span className="nav__item">Suppliers</span>
          <span className="nav__item">Orders</span>
          <span className="nav__item">Reports</span>
        </nav>
        <div className="sidebar__foot">
          <p className="sidebar__label">Categories</p>
          {categories.length === 0 && <p className="sidebar__muted">No data</p>}
          {categories.map((name) => (
            <p key={name} className="sidebar__muted">{name}</p>
          ))}
        </div>
      </aside>

      <main className="main">
        <header className="header">
          <div>
            <h1>Inventory</h1>
            <p className="header__sub">Live stock levels across the warehouse, deployed by Argo CD</p>
          </div>
          <button className="btn btn--primary" onClick={() => setFormOpen(true)}>Add item</button>
        </header>

        {error && (
          <div className="banner banner--error">
            <strong>The backend is not available.</strong> {error}
            <button className="btn btn--ghost" onClick={load}>Try again</button>
          </div>
        )}

        <section className="cards">
          <StatCard label="Items" value={stats ? stats.total_items : '—'} tone="blue" />
          <StatCard label="Units in stock" value={stats ? stats.total_units.toLocaleString() : '—'} tone="green" />
          <StatCard label="Stock value" value={stats ? money(stats.total_value) : '—'} tone="violet" />
          <StatCard label="Low stock" value={stats ? stats.low_stock_items : '—'} tone="amber" />
        </section>

        <section className="toolbar">
          <div className="filters">
            {[
              ['all', 'All'],
              ['low', 'Low stock'],
              ['ok', 'In stock'],
            ].map(([key, label]) => (
              <button
                key={key}
                className={`chip ${filter === key ? 'chip--active' : ''}`}
                onClick={() => setFilter(key)}
              >
                {label}
              </button>
            ))}
          </div>
          <input
            className="search"
            placeholder="Search by name, SKU or category"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </section>

        <section className="panel">
          {loading && <p className="panel__empty">The data is loading.</p>}
          {!loading && visible.length === 0 && <p className="panel__empty">No item matches the filter.</p>}
          {!loading && visible.length > 0 && (
            <table className="table">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>SKU</th>
                  <th>Category</th>
                  <th className="num">Quantity</th>
                  <th className="num">Unit price</th>
                  <th className="num">Value</th>
                  <th>State</th>
                  <th className="num">Actions</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((item) => (
                  <tr key={item.id}>
                    <td data-label="Item"><strong>{item.name}</strong></td>
                    <td data-label="SKU"><code>{item.sku}</code></td>
                    <td data-label="Category">{item.category}</td>
                    <td data-label="Quantity" className="num">{item.quantity}</td>
                    <td data-label="Unit price" className="num">{money(item.unit_price)}</td>
                    <td data-label="Value" className="num">{money(item.stock_value)}</td>
                    <td data-label="State">
                      <span className={`badge ${item.low_stock ? 'badge--low' : 'badge--ok'}`}>
                        {item.low_stock ? 'Reorder' : 'In stock'}
                      </span>
                    </td>
                    <td data-label="Actions" className="num actions">
                      <button className="btn btn--tiny" onClick={() => adjust(item, -1)}>−</button>
                      <button className="btn btn--tiny" onClick={() => adjust(item, +1)}>+</button>
                      <button className="btn btn--tiny btn--danger" onClick={() => remove(item)}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <footer className="footer">
          <span>StockRoom · DevOps capstone</span>
          <span className="pipeline">
            <span className="dot dot--ok" /> API
            <span className="dot dot--ok" /> Database
            <span className="dot dot--ok" /> Metrics
          </span>
        </footer>
      </main>

      {formOpen && (
        <ItemForm onSubmit={createItem} onClose={() => setFormOpen(false)} busy={busy} />
      )}
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
