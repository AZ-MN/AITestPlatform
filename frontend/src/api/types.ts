// 通用类型定义
export interface User {
  id: number
  username: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  avatar?: string
  created_at: string
}

export interface Project {
  id: number
  name: string
  description?: string
  status: string
  icon: string
  created_by: number
  created_at: string
  updated_at: string
  member_count?: number
  case_count?: number
  req_count?: number
}

export interface ProjectMember {
  id: number
  user_id: number
  username: string
  full_name: string
  role: string
  joined_at: string
}

export interface RequirementPoint {
  id: string
  title: string
  description: string
  priority: string
  module: string
  conditions: string[]
  rules: string[]
}

export interface Requirement {
  id: number
  project_id: number
  title: string
  content?: string
  source_type: string
  source_filename?: string
  status: string
  parse_result?: RequirementPoint[]
  req_points_count: number
  created_at: string
  updated_at: string
  creator_name?: string
}

export interface TestCaseStep {
  step: number
  action: string
  expected: string
}

export interface TestCase {
  id: number
  project_id: number
  requirement_id?: number
  case_id?: string
  module?: string
  title: string
  case_level: string
  test_type: string
  stage: string
  preconditions?: string
  steps?: TestCaseStep[]
  expected_results?: string[]
  remarks?: string
  status: string
  ai_generated: number
  generation_batch?: string
  exec_status?: string
  rating?: number
  feedback?: string
  created_at: string
  updated_at: string
  creator_name?: string
}

export interface CaseReviewLog {
  id: number
  case_id: number
  action: string
  from_status?: string
  to_status?: string
  comment?: string
  detail?: any
  created_by: number
  created_by_name?: string
  created_at: string
}

export interface AIModelConfig {
  id: number
  name?: string
  provider: string
  model_name: string
  api_base_url?: string
  temperature: string
  max_tokens: number
  is_default: number
  is_active: number
  created_at: string
}

export interface GenerateRequest {
  project_id: number
  requirement_id?: number
  req_points?: RequirementPoint[]
  test_type?: string
  granularity?: string
  cover_scenarios?: string[]
  ai_provider?: string
  temperature?: number
  case_prompt?: string
  module_filter?: string
}

export interface PageResult<T> {
  total: number
  page: number
  page_size: number
  items: T[]
}
