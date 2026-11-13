const API_BASE_URL = '/api'
const TOKEN_KEY = 'hrn_autovault_access_token'

export interface LoginCredentials {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface DashboardSummary {
  total_customers: number
  total_vehicles: number
  open_job_cards: number
  quotes_awaiting_approval: number
  outstanding_invoices: number | string
  monthly_revenue: number | string
}

export interface DashboardStatusCount {
  status: string
  count: number
}

export interface DashboardRecentActivity {
  id: number
  action: string
  entity_type: string
  entity_id: number | null
  details: string | null
  created_at: string
}

export interface DashboardResponse {
  summary: DashboardSummary
  job_cards_by_status: DashboardStatusCount[]
  quotes_by_status: DashboardStatusCount[]
  invoices_by_status: DashboardStatusCount[]
  recent_activity: DashboardRecentActivity[]
}

export interface CurrentUser {
  id: number
  business_id: number
  name: string
  email: string
  role: string
  created_at: string
}

export function getAccessToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY)
}

function saveAccessToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token)
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(TOKEN_KEY)
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers)
  const token = getAccessToken()

  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    if (response.status === 401 && path !== '/auth/login') {
      clearAccessToken()
    }

    const message = await response.text()
    throw new Error(
      message || `Request failed with status ${response.status}`,
    )
  }

  return response.json() as Promise<T>
}

export async function login(
  credentials: LoginCredentials,
): Promise<TokenResponse> {
  const result = await request<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  })

  saveAccessToken(result.access_token)
  return result
}

export function getCurrentUser(): Promise<CurrentUser> {
  return request<CurrentUser>('/auth/me')
}

export function getDashboard(): Promise<DashboardResponse> {
  return request<DashboardResponse>('/dashboard')
}

export interface Customer {
  id: number
  business_id: number
  first_name: string
  last_name: string
  email: string | null
  phone: string
}

export interface CustomerListResponse {
  items: Customer[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface CustomerListParams {
  page?: number
  page_size?: number
  search?: string
  include_archived?: boolean
}

export function getCustomers(
  params: CustomerListParams = {},
): Promise<CustomerListResponse> {
  const query = new URLSearchParams()

  query.set('page', String(params.page ?? 1))
  query.set('page_size', String(params.page_size ?? 10))

  if (params.search?.trim()) {
    query.set('search', params.search.trim())
  }

  if (params.include_archived) {
    query.set('include_archived', 'true')
  }

  return request<CustomerListResponse>(
    `/customers/?${query.toString()}`,
  )
}

export interface CustomerCreate {
  first_name: string
  last_name: string
  email: string | null
  phone: string
}

export async function createCustomer(
  customer: CustomerCreate,
): Promise<Customer> {
  return request<Customer>('/customers/', {
    method: 'POST',
    body: JSON.stringify(customer),
  })
}

export interface CustomerUpdate {
  first_name?: string
  last_name?: string
  email?: string | null
  phone?: string
}

export function updateCustomer(
  customerId: number,
  updates: CustomerUpdate,
): Promise<Customer> {
  return request<Customer>(`/customers/${customerId}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  })
}

export function archiveCustomer(customerId: number): Promise<unknown> {
  return request<unknown>(`/customers/${customerId}`, {
    method: 'DELETE',
  })
}

export function restoreCustomer(customerId: number): Promise<Customer> {
  return request<Customer>(`/customers/${customerId}/restore`, {
    method: 'POST',
  })
}