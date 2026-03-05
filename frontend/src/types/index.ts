// All TypeScript interfaces matching the backend schemas

export interface User {
  id: number
  username: string
  full_name?: string
  email?: string
  phone?: string
  role_id?: number
  role_name?: string
  is_active: boolean
  is_superuser: boolean
  last_login?: string
  created_at: string
}

export interface Role {
  id: number
  name: string
  code: string
  description?: string
  is_system: boolean
  created_at: string
}

export interface Project {
  id: number
  name: string
  description?: string
  owner_id?: number
  status: string
  env_config?: Record<string, any>
  created_at: string
}

export interface Iteration {
  id: number
  project_id: number
  name: string
  version?: string
  start_date?: string
  end_date?: string
  status: string
  description?: string
  created_at: string
}

export interface Requirement {
  id: number
  project_id: number
  iteration_id?: number
  title: string
  description?: string
  module?: string
  priority: string
  status: string
  source_type?: string
  parsed_content?: ParsedContent
  creator_id?: number
  created_at: string
}

export interface ParsedContent {
  功能点列表: string[]
  业务规则: string[]
  可测性问题: string[]
  测试点清单: string[]
}

export interface TestCase {
  id: number
  project_id: number
  requirement_id?: number
  iteration_id?: number
  module?: string
  sub_module?: string
  title: string
  preconditions?: string
  steps?: TestStep[]
  expected_result?: string
  case_type: string
  priority: string
  status: string
  is_ai_generated: boolean
  tags?: string[]
  creator_id?: number
  created_at: string
}

export interface TestStep {
  step: string
  expected: string
}

export interface ApiDefinition {
  id: number
  project_id: number
  module?: string
  name: string
  method: string
  path: string
  description?: string
  headers?: Record<string, any>
  query_params?: Record<string, any>
  body_schema?: Record<string, any>
  response_schema?: Record<string, any>
  source: string
  creator_id?: number
  created_at: string
}

export interface ApiCase {
  id: number
  project_id: number
  api_definition_id?: number
  name: string
  description?: string
  headers?: Record<string, any>
  query_params?: Record<string, any>
  body?: Record<string, any>
  env: string
  assertions?: Assertion[]
  case_type?: string
  is_ai_generated: boolean
  creator_id?: number
  created_at: string
}

export interface Assertion {
  type: 'status_code' | 'json_field' | 'contains'
  field?: string
  operator: 'eq' | 'gt' | 'lt' | 'contains' | 'not_null'
  value: any
}

export interface Defect {
  id: number
  project_id: number
  iteration_id?: number
  title: string
  description?: string
  environment?: string
  version?: string
  module?: string
  severity: string
  priority: string
  reproduce_rate?: string
  steps_to_reproduce?: string
  actual_result?: string
  expected_result?: string
  status: string
  assignee_id?: number
  reporter_id: number
  tags?: string[]
  ai_category?: string
  ai_root_cause?: string
  ai_suggestion?: string
  similar_defect_ids?: number[]
  created_at: string
}

export interface Script {
  id: number
  project_id: number
  name: string
  description?: string
  script_type: string
  language: string
  content: string
  is_ai_generated: boolean
  version: number
  creator_id?: number
  created_at: string
}

export interface LLMConfig {
  id: number
  name: string
  provider: string
  endpoint?: string
  model_name?: string
  max_tokens: number
  timeout: number
  is_default: boolean
  is_active: boolean
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  size: number
}

export interface ApiResponse<T = any> {
  data: T
  message?: string
  code?: number
}
