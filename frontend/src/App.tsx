import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'
import {
  clearAccessToken,
  getAccessToken,
  getCurrentUser,
  getDashboard,
  getCustomers,
  createCustomer,
  updateCustomer,
  archiveCustomer,
  restoreCustomer,
  login,
  type CurrentUser,
  type DashboardResponse,
  type Customer,
} from './services/api'

const navigation = [
  { label: 'Overview', icon: '▦' },
  { label: 'Customers', icon: '♙' },
  { label: 'Vehicles', icon: '▱' },
  { label: 'Job Cards', icon: '⚒' },
  { label: 'Service History', icon: '◷' },
  { label: 'Quotes', icon: '▤' },
  { label: 'Invoices', icon: '▧' },
  { label: 'Payments', icon: 'R' },
  { label: 'Reports', icon: '▥' },
]

const zar = new Intl.NumberFormat('en-ZA', {
  style: 'currency',
  currency: 'ZAR',
  maximumFractionDigits: 2,
})

function money(value: number | string) {
  return zar.format(Number(value) || 0)
}

function App() {
  const [activePage, setActivePage] = useState('Overview')
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [authChecking, setAuthChecking] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [customers, setCustomers] = useState<Customer[]>([])
  const [customerSearch, setCustomerSearch] = useState('')
  const [customerPage, setCustomerPage] = useState(1)
  const [customerTotal, setCustomerTotal] = useState(0)
  const [customerTotalPages, setCustomerTotalPages] = useState(0)
  const [customerLoading, setCustomerLoading] = useState(false)
  const [customerError, setCustomerError] = useState('')
  const [showCustomerForm, setShowCustomerForm] = useState(false)
  const [newCustomerFirstName, setNewCustomerFirstName] = useState('')
  const [newCustomerLastName, setNewCustomerLastName] = useState('')
  const [newCustomerEmail, setNewCustomerEmail] = useState('')
  const [newCustomerPhone, setNewCustomerPhone] = useState('')
  const [customerSaving, setCustomerSaving] = useState(false)
  const [customerSuccess, setCustomerSuccess] = useState('')
  const [editingCustomerId, setEditingCustomerId] = useState<number | null>(null)
  const [editFirstName, setEditFirstName] = useState('')
  const [editLastName, setEditLastName] = useState('')
  const [editEmail, setEditEmail] = useState('')
  const [editPhone, setEditPhone] = useState('')
  const [customerUpdating, setCustomerUpdating] = useState(false)
  const [customerRefresh, setCustomerRefresh] = useState(0)
  const [customerView, setCustomerView] = useState<'active' | 'archived'>('active')
  const [customerActionLoading, setCustomerActionLoading] = useState<number | null>(null)

  useEffect(() => {
    let cancelled = false

    async function restoreSession() {
      if (!getAccessToken()) {
        setAuthChecking(false)
        return
      }

      try {
        const currentUser = await getCurrentUser()
        if (!cancelled) setUser(currentUser)
      } catch {
        clearAccessToken()
        if (!cancelled) setError('Your session expired. Please sign in again.')
      } finally {
        if (!cancelled) setAuthChecking(false)
      }
    }

    void restoreSession()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!user) {
      setDashboard(null)
      return
    }

    let cancelled = false

    async function loadDashboard() {
      setLoading(true)
      setError('')

      try {
        const data = await getDashboard()
        if (!cancelled) setDashboard(data)
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : 'Could not load dashboard data.',
          )
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void loadDashboard()

    return () => {
      cancelled = true
    }
  }, [user])

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login({ email, password })
      const currentUser = await getCurrentUser()
      setUser(currentUser)
      setPassword('')
    } catch (err) {
      clearAccessToken()
      setError(
        err instanceof Error
          ? err.message
          : 'Sign-in failed. Check your details and try again.',
      )
    } finally {
      setLoading(false)
      setAuthChecking(false)
    }
  }

  useEffect(() => {
    if (!user || activePage !== 'Customers') return

    let cancelled = false

    async function loadCustomers() {
      setCustomerLoading(true)
      setCustomerError('')

      try {
        const data = await getCustomers({
          page: customerPage,
          page_size: 10,
          search: customerSearch,
          include_archived: customerView === 'archived',
        })

        if (cancelled) return

        setCustomers(data.items)
        setCustomerTotal(data.total)
        setCustomerTotalPages(data.total_pages)
      } catch (err) {
        if (!cancelled) {
          setCustomerError(
            err instanceof Error
              ? err.message
              : 'Could not load customers.',
          )
        }
      } finally {
        if (!cancelled) setCustomerLoading(false)
      }
    }

    void loadCustomers()

    return () => {
      cancelled = true
    }
  }, [user, activePage, customerPage, customerSearch, customerRefresh, customerView])

  async function handleCreateCustomer(
  event: React.FormEvent<HTMLFormElement>,
) {
  event.preventDefault()

  setCustomerSaving(true)
  setCustomerSuccess('')

  try {
    const createdCustomer = await createCustomer({
      first_name: newCustomerFirstName.trim(),
      last_name: newCustomerLastName.trim(),
      email: newCustomerEmail.trim() || null,
      phone: newCustomerPhone.trim(),
    })

    setCustomers((currentCustomers) => [
      createdCustomer,
      ...currentCustomers,
    ])

    setCustomerSuccess(
      `Customer ${createdCustomer.first_name} ${createdCustomer.last_name} created successfully.`,
    )

    setNewCustomerFirstName('')
    setNewCustomerLastName('')
    setNewCustomerEmail('')
    setNewCustomerPhone('')
    setShowCustomerForm(false)
  } catch (error) {
    setCustomerSuccess(
      error instanceof Error
        ? `Could not create customer: ${error.message}`
        : 'Could not create customer. Please try again.',
    )
  } finally {
    setCustomerSaving(false)
  }
}

async function handleUpdateCustomer(event: FormEvent<HTMLFormElement>) {
  event.preventDefault()

  if (editingCustomerId === null) return

  const firstName = editFirstName.trim()
  const lastName = editLastName.trim()
  const phone = editPhone.trim()
  const emailValue = editEmail.trim()

  if (!firstName || !lastName || !phone) {
    setCustomerError('First name, last name and phone are required.')
    return
  }

  setCustomerUpdating(true)
  setCustomerError('')
  setCustomerSuccess('')

  try {
    await updateCustomer(editingCustomerId, {
      first_name: firstName,
      last_name: lastName,
      email: emailValue || null,
      phone,
    })

    setCustomerSuccess('Customer updated successfully.')
    setEditingCustomerId(null)

    // Refresh the customer list using the existing loading effect.
    setCustomerRefresh((count) => count + 1)
  } catch (err) {
    setCustomerError(
      err instanceof Error
        ? `Could not update customer: ${err.message}`
        : 'Could not update customer. Please try again.',
    )
  } finally {
    setCustomerUpdating(false)
  }
}

async function handleArchiveCustomer(customer: Customer) {
  const confirmed = window.confirm(
    `Archive ${customer.first_name} ${customer.last_name}? Their vehicles and service history will be preserved.`,
  )

  if (!confirmed) return

  setCustomerActionLoading(customer.id)
  setCustomerError('')
  setCustomerSuccess('')

  try {
    await archiveCustomer(customer.id)

    setCustomerSuccess(
      `${customer.first_name} ${customer.last_name} archived successfully.`,
    )

    setCustomerRefresh((count) => count + 1)
  } catch (err) {
    setCustomerError(
      err instanceof Error
        ? `Could not archive customer: ${err.message}`
        : 'Could not archive customer.',
    )
  } finally {
    setCustomerActionLoading(null)
  }
}

async function handleRestoreCustomer(customer: Customer) {
  setCustomerActionLoading(customer.id)
  setCustomerError('')
  setCustomerSuccess('')

  try {
    await restoreCustomer(customer.id)

    setCustomerSuccess(
      `${customer.first_name} ${customer.last_name} restored successfully.`,
    )

    setCustomerRefresh((count) => count + 1)
  } catch (err) {
    setCustomerError(
      err instanceof Error
        ? `Could not restore customer: ${err.message}`
        : 'Could not restore customer.',
    )
  } finally {
    setCustomerActionLoading(null)
  }
}

  function handleLogout() {
    clearAccessToken()
    setUser(null)
    setDashboard(null)
    setPassword('')
    setError('')
    setActivePage('Overview')
  }

  if (authChecking) {
    return <div className="auth-screen"><p>Checking your session…</p></div>
  }

  if (!user) {
    return (
      <main className="auth-screen">
        <form className="auth-card" onSubmit={handleLogin}>
          <div className="brand auth-brand">
            <div className="brand-mark">8</div>
            <div>
              <strong>HRN CLOUD</strong>
              <span>AUTOVAULT</span>
            </div>
          </div>

          <div className="eyebrow">BUSINESS MANAGEMENT</div>
          <h1>Welcome back.</h1>
          <p>Sign in to access your automotive workspace.</p>

          {error && <div className="auth-error" role="alert">{error}</div>}

          <label htmlFor="email">Email address</label>
          <input
            id="email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@business.co.za"
            required
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter your password"
            required
          />

          <button className="primary-button auth-submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>

          <p className="auth-note">
            Use an existing AutoVault account. New business registration
            will be connected in a later stage.
          </p>
        </form>
      </main>
    )
  }

  const summary = dashboard?.summary

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">8</div>
          <div><strong>HRN CLOUD</strong><span>AUTOVAULT</span></div>
        </div>

        <div className="workspace-label">WORKSPACE</div>
        <nav className="navigation">
          {navigation.map((item) => (
            <button
              key={item.label}
              className={`nav-item ${activePage === item.label ? 'active' : ''}`}
              onClick={() => setActivePage(item.label)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
              {activePage === item.label && <span className="active-indicator" />}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="secure-badge">
            <span className="secure-dot" />
            <div><strong>Authenticated</strong><span>API connected</span></div>
          </div>
          <div className="profile">
            <div className="avatar">{user.name.slice(0, 2).toUpperCase()}</div>
            <div className="profile-info">
              <strong>{user.name}</strong><span>{user.role}</span>
            </div>
            <button className="profile-menu" onClick={handleLogout} title="Sign out">
              ↪
            </button>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumbs">
            <span>Workspace</span><span className="breadcrumb-divider">/</span>
            <strong>{activePage}</strong>
          </div>
          <div className="topbar-right">
            <span className="environment"><span className="secure-dot" />Connected</span>
            <div className="topbar-avatar">{user.name.slice(0, 2).toUpperCase()}</div>
          </div>
        </header>

        <div className="page-content">
          <section className="welcome-section">
            <div>
              <div className="eyebrow">BUSINESS MANAGEMENT</div>
              <h1>{activePage === 'Overview' ? `Welcome, ${user.name.split(' ')[0]}.` : activePage}</h1>
              <p>Your automotive business, all in one place.</p>
            </div>
            <button className="primary-button" onClick={() => setActivePage('Customers')}>
              <span>＋</span> Explore customers
            </button>
          </section>

          {error && (
            <div className="auth-error" role="alert">
              {error}
            </div>
          )}

          {activePage === 'Overview' ? (
            <>
              <section className="stats-grid">
                <article className="stat-card">
                  <div className="stat-top"><span className="stat-label">CUSTOMERS</span><span className="stat-icon purple">♙</span></div>
                  <div className="stat-value">{summary?.total_customers ?? '—'}</div>
                  <div className="stat-foot">Active customer records</div>
                </article>
                <article className="stat-card">
                  <div className="stat-top"><span className="stat-label">VEHICLES</span><span className="stat-icon blue">▱</span></div>
                  <div className="stat-value">{summary?.total_vehicles ?? '—'}</div>
                  <div className="stat-foot">Registered vehicles</div>
                </article>
                <article className="stat-card">
                  <div className="stat-top"><span className="stat-label">OPEN JOB CARDS</span><span className="stat-icon orange">⚒</span></div>
                  <div className="stat-value">{summary?.open_job_cards ?? '—'}</div>
                  <div className="stat-foot">Jobs not yet closed</div>
                </article>
                <article className="stat-card">
                  <div className="stat-top"><span className="stat-label">OUTSTANDING INVOICES</span><span className="stat-icon green">R</span></div>
                  <div className="stat-value">{summary ? money(summary.outstanding_invoices) : '—'}</div>
                  <div className="stat-foot">Balance outstanding</div>
                </article>
              </section>

              <section className="content-grid">
                <article className="panel">
                  <div className="panel-heading">
                    <div><h2>Workshop overview</h2><p>Work moving through your business.</p></div>
                    <span className="panel-symbol">↗️</span>
                  </div>
                  {loading && <p>Loading workshop data…</p>}
                  {!loading && dashboard && (
                    <div className="quick-actions">
                      {dashboard.job_cards_by_status.length === 0
                        ? <p>No job cards have been recorded yet.</p>
                        : dashboard.job_cards_by_status.map((item) => (
                          <div className="system-row" key={item.status}>
                            <strong>{item.status.replaceAll('_', ' ')}</strong>
                            <span className="status-text">{item.count}</span>
                          </div>
                        ))}
                    </div>
                  )}
                  {!loading && !dashboard && <p>Workshop data is not available.</p>}
                </article>

                <article className="panel">
                  <div className="panel-heading">
                    <div><h2>Quick actions</h2><p>Go to your main tools.</p></div>
                  </div>
                  <div className="quick-actions">
                    {['Customers', 'Vehicles', 'Job Cards', 'Invoices'].map((page) => (
                      <button key={page} onClick={() => setActivePage(page)}>
                        <span className="action-copy"><strong>{page}</strong><small>Open {page.toLowerCase()} module</small></span>
                        <span className="action-arrow">→</span>
                      </button>
                    ))}
                  </div>
                </article>
              </section>

              <section className="panel system-panel">
                <div className="panel-heading">
                  <div><h2>Business snapshot</h2><p>Live figures from your authenticated workspace.</p></div>
                  <span className="status-pill">{dashboard ? 'API connected' : loading ? 'Loading' : 'Unavailable'}<span className="secure-dot" /></span>
                </div>
                <div className="system-row">
                  <div><strong>Quotes awaiting approval</strong><span>Quotes marked as sent</span></div>
                  <span className="status-text">{summary?.quotes_awaiting_approval ?? '—'}</span>
                </div>
                <div className="system-row">
                  <div><strong>Monthly revenue</strong><span>Collected payments this month</span></div>
                  <span className="status-text">{summary ? money(summary.monthly_revenue) : '—'}</span>
                </div>
                <div className="system-row">
                  <div><strong>Signed in as</strong><span>{user.email}</span></div>
                  <span className="status-text">{user.role}</span>
                </div>
              </section>
            </>
          ) : activePage === 'Customers' ? (
            <section className="panel customers-panel">
              <div className="panel-heading">
              <div>
                <h2>
                  {customerView === 'active' ? 'Customer directory' : 'Archived customers'}
                </h2>
                <p>
                  {customerView === 'active' ? 'Manage customers registered with your business.' 
                  : 'Review and restore previously archived customers.'}
                </p>
                <div className="customer-view-tabs">
                  <button
                    type="button"
                    className={customerView === 'active' ? 'active' : ''}
                    onClick={() => {
                      setCustomerView('active')
                      setCustomerPage(1)
                      setCustomerError('')
                      setCustomerSuccess('')
                      setEditingCustomerId(null)
                    }}
                  >
                    Active customers
                  </button>

                  {(user.role === 'OWNER' || user.role === 'ADMIN') && (
                    <button
                      type="button"
                      className={customerView === 'archived' ? 'active' : ''}
                      onClick={() => {
                        setCustomerView('archived')
                        setCustomerPage(1)
                        setCustomerError('')
                        setCustomerSuccess('')
                        setEditingCustomerId(null)
                      }}
                    >
                      Archived customers
                    </button>
                  )}
                </div>
              </div>
              <div className="customer-heading-actions">
                <span className="status-pill">
                  {customerTotal}{customerView === 'active' ? ' customers' : ' archived customers'}
                </span>
                <button
                  type="button"
                  className="primary-button"
                  onClick={() => {
                    setCustomerSuccess('')
                    setShowCustomerForm((visible) => !visible)
                  }}
                >
                  {showCustomerForm ? 'Cancel' : '+ New customer'}
                </button>
              </div>
            </div>

            {editingCustomerId !== null && (
              <form
                className="customer-create-form"
                onSubmit={handleUpdateCustomer}
              >
                <h3>Edit customer #{editingCustomerId}</h3>

                <div className="customer-form-grid">
                  <div>
                    <label htmlFor="edit-customer-first-name">First name</label>
                    <input
                      id="edit-customer-first-name"
                      value={editFirstName}
                      onChange={(event) => setEditFirstName(event.target.value)}
                      required
                      maxLength={100}
                      autoComplete="given-name"
                    />
                  </div>

                  <div>
                    <label htmlFor="edit-customer-last-name">Last name</label>
                    <input
                      id="edit-customer-last-name"
                      value={editLastName}
                      onChange={(event) => setEditLastName(event.target.value)}
                      required
                      maxLength={100}
                      autoComplete="family-name"
                    />
                  </div>

                  <div>
                    <label htmlFor="edit-customer-email">Email (optional)</label>
                    <input
                      id="edit-customer-email"
                      type="email"
                      value={editEmail}
                      onChange={(event) => setEditEmail(event.target.value)}
                      autoComplete="email"
                    />
                  </div>

                  <div>
                    <label htmlFor="edit-customer-phone">Phone</label>
                    <input
                      id="edit-customer-phone"
                      type="tel"
                      value={editPhone}
                      onChange={(event) => setEditPhone(event.target.value)}
                      required
                      maxLength={30}
                      autoComplete="tel"
                    />
                  </div>
                </div>

                <div className="customer-heading-actions">
                  <button
                    type="submit"
                    className="primary-button"
                    disabled={customerUpdating}
                  >
                    {customerUpdating ? 'Saving changes…' : 'Save changes'}
                  </button>

                  <button
                    type="button"
                    className="secondary-button"
                    disabled={customerUpdating}
                    onClick={() => setEditingCustomerId(null)}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
            {showCustomerForm && (
                <form
                  className="customer-create-form"
                  onSubmit={handleCreateCustomer}
                >
                  <h3>Add a customer</h3>

                  <div className="customer-form-grid">
                    <div>
                      <label htmlFor="new-customer-first-name">First name</label>
                      <input
                        id="new-customer-first-name"
                        value={newCustomerFirstName}
                        onChange={(event) => setNewCustomerFirstName(event.target.value)}
                        required
                        maxLength={100}
                        autoComplete="given-name"
                      />
                    </div>

                    <div>
                      <label htmlFor="new-customer-last-name">Last name</label>
                      <input
                        id="new-customer-last-name"
                        value={newCustomerLastName}
                        onChange={(event) => setNewCustomerLastName(event.target.value)}
                        required
                        maxLength={100}
                        autoComplete="family-name"
                      />
                    </div>

                    <div>
                      <label htmlFor="new-customer-email">Email (optional)</label>
                      <input
                        id="new-customer-email"
                        type="email"
                        value={newCustomerEmail}
                        onChange={(event) => setNewCustomerEmail(event.target.value)}
                        autoComplete="email"
                      />
                    </div>

                    <div>
                      <label htmlFor="new-customer-phone">Phone</label>
                      <input
                        id="new-customer-phone"
                        type="tel"
                        value={newCustomerPhone}
                        onChange={(event) => setNewCustomerPhone(event.target.value)}
                        required
                        maxLength={30}
                        autoComplete="tel"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="primary-button"
                    disabled={customerSaving}
                  >
                    {customerSaving ? 'Saving customer…' : 'Save customer'}
                  </button>
                </form>
              )}

              {customerSuccess && (
                <div className="customer-success" role="status">
                  {customerSuccess}
                </div>
              )}

              <form
                className="customer-search"
                onSubmit={(event) => {
                  event.preventDefault()
                  setCustomerPage(1)
                }}
              >
                <input
                  type="search"
                  aria-label="Search customers"
                  placeholder="Search name, email or phone..."
                  value={customerSearch}
                  onChange={(event) => {
                    setCustomerSearch(event.target.value)
                    setCustomerPage(1)
                  }}
                />
              </form>

              {customerLoading && <p>Loading customers...</p>}

              {customerError && (
                <div className="auth-error" role="alert">
                  {customerError}
                </div>
              )}

              {!customerLoading && !customerError && customers.length === 0 && (
                <div className="customer-empty">
                  <h3>No customers found</h3>
                  <p>
                    {customerSearch
                      ? 'Try another search term.'
                      : 'Customer records will appear here when available.'}
                  </p>
                </div>
              )}

              {!customerLoading && !customerError && customers.length > 0 && (
                <>
                  <div className="customer-table-wrap">
                    <table className="customer-table">
                      <thead>
                        <tr>
                          <th>Customer</th>
                          <th>Email</th>
                          <th>Phone</th>
                          <th>Customer ID</th>
                          <th>Actions</th>
                        </tr>
                      </thead>  
                      <tbody>
                        {customers.map((customer) => (
                          <tr key={customer.id}>
                            <td>
                              <strong>
                                {customer.first_name} {customer.last_name}
                              </strong>
                            </td>

                            <td>{customer.email || '—'}</td>

                            <td>{customer.phone}</td>

                            <td>#{customer.id}</td>

                            <td>
                              <div className="customer-row-actions">
                                {customerView === 'active' ? (
                                  <>
                                    {['OWNER', 'ADMIN', 'MANAGER'].includes(user.role) && (
                                      <button
                                        type="button"
                                        className="secondary-button"
                                        disabled={customerActionLoading === customer.id}
                                        onClick={() => {
                                          setCustomerError('')
                                          setCustomerSuccess('')
                                          setEditingCustomerId(customer.id)
                                          setEditFirstName(customer.first_name)
                                          setEditLastName(customer.last_name)
                                          setEditEmail(customer.email ?? '')
                                          setEditPhone(customer.phone)
                                        }}
                                      >
                                        Edit
                                      </button>
                                    )}

                                    {['OWNER', 'ADMIN'].includes(user.role) && (
                                      <button
                                        type="button"
                                        className="danger-button"
                                        disabled={customerActionLoading === customer.id}
                                        onClick={() => handleArchiveCustomer(customer)}
                                      >
                                        {customerActionLoading === customer.id
                                          ? 'Archiving...'
                                          : 'Archive'}
                                      </button>
                                    )}
                                  </>
                                ) : (
                                  <button
                                    type="button"
                                    className="secondary-button"
                                    disabled={customerActionLoading === customer.id}
                                    onClick={() => handleRestoreCustomer(customer)}
                                  >
                                    {customerActionLoading === customer.id
                                      ? 'Restoring...'
                                      : 'Restore'}
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="customer-pagination">
                    <span>
                      Page {customerPage} of {customerTotalPages}
                    </span>
                    <div>
                      <button
                        type="button"
                        className="secondary-button"
                        disabled={customerPage <= 1 || customerLoading}
                        onClick={() => setCustomerPage((page) => page - 1)}
                      >
                        Previous
                      </button>
                      <button
                        type="button"
                        className="secondary-button"
                        disabled={
                          customerPage >= customerTotalPages || customerLoading
                        }
                        onClick={() => setCustomerPage((page) => page + 1)}
                      >
                        Next
                      </button>
                    </div>
                  </div>
                </>
              )}
            </section>
          ) : (
            <section className="panel module-panel">
              <div className="module-icon">▦</div>
              <h2>{activePage}</h2>
              <p>This module's data table and actions will be connected in a subsequent stage.</p>
              <button
                className="secondary-button"
                onClick={() => setActivePage('Overview')}
              >
                ← Back to overview
              </button>
            </section>
          )}

          <footer className="footer">
            <span>HRN Cloud AutoVault</span>
            <span>Automotive business management · Development</span>
          </footer>
        </div>
      </main>
    </div>
  )
}

export default App