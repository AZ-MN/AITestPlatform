"""Prompt 模板管理"""

PROMPTS = {
    "requirement_parse": """你是一名资深测试工程师，请分析以下需求文档，提取结构化信息。

需求文档内容：
{content}

请以JSON格式返回以下信息：
{{
  "功能点列表": ["功能点1", "功能点2", ...],
  "业务规则": ["规则1", "规则2", ...],
  "可测性问题": ["缺失信息1", "缺失信息2", ...],
  "测试点清单": ["测试点1", "测试点2", ...]
}}
""",

    "testcase_generate": """你是一名资深测试工程师，请根据以下需求信息生成完整的测试用例。

需求信息：
{requirement}

请生成覆盖功能、异常、边界、性能、安全等多种类型的测试用例，以JSON格式返回：
{{
  "test_cases": [
    {{
      "title": "用例标题",
      "module": "所属模块",
      "case_type": "功能|异常|边界|性能|安全",
      "priority": "P0|P1|P2|P3",
      "preconditions": "前置条件",
      "steps": [
        {{"step": "操作步骤", "expected": "预期结果"}}
      ],
      "expected_result": "整体预期结果"
    }}
  ]
}}

要求：
1. 每个功能点至少生成3个用例（正常、异常、边界）
2. P0为核心主流程，P1为重要功能，P2为一般功能，P3为边缘场景
3. 步骤要具体、可执行
""",

    "api_case_generate": """你是一名API测试专家，请根据以下接口定义生成全面的测试用例。

接口信息：
- 名称：{name}
- 方法：{method}
- 路径：{path}
- 描述：{description}
- 参数定义：{params}
- 请求体：{body_schema}
- 响应体：{response_schema}

请生成覆盖以下场景的测试用例，以JSON格式返回：
{{
  "cases": [
    {{
      "name": "用例名称",
      "case_type": "normal|boundary|error|security",
      "description": "用例描述",
      "body": {{}},
      "query_params": {{}},
      "assertions": [
        {{"type": "status_code|json_field|contains", "field": "字段路径", "operator": "eq|gt|lt|contains|not_null", "value": "期望值"}}
      ]
    }}
  ]
}}

必须包含：
1. 正常场景（必填参数齐全）
2. 必填参数缺失（每个必填参数单独缺失）
3. 空值/null 测试
4. 类型不匹配
5. 边界值（最大长度、最小值、最大值）
6. 特殊字符（SQL注入、XSS）
7. 枚举值：合法值与非法值
""",

    "script_generate_pytest": """你是一名自动化测试工程师，请根据以下API用例信息生成可直接运行的 Python + Pytest + Requests 测试脚本。

接口信息：
- 接口名：{api_name}
- 方法：{method}
- 基础URL：{base_url}
- 路径：{path}
- 用例列表：{cases}

要求：
1. 使用 pytest 框架
2. 包含 conftest.py 的 fixture 示例
3. 每个用例一个 test 函数
4. 包含完整的断言
5. 处理 token 认证
6. 生成可直接运行的完整代码

以JSON格式返回：
{{
  "filename": "test_xxx.py",
  "content": "完整Python代码"
}}
""",

    "script_generate_playwright": """你是一名UI自动化测试工程师，请根据以下操作步骤生成 Playwright Python 测试脚本。

页面URL：{url}
操作步骤：
{steps}

要求：
1. 使用 playwright.sync_api
2. 包含截图on failure逻辑
3. 使用 Page Object 模式
4. 包含等待和重试机制
5. 代码可直接运行

以JSON格式返回：
{{
  "filename": "test_ui_xxx.py",
  "content": "完整Python代码"
}}
""",

    "defect_analyze": """你是一名资深测试工程师，请对以下缺陷描述进行分析。

缺陷描述：
{description}

请以JSON格式返回分析结果：
{{
  "structured": {{
    "title": "结构化标题（简洁描述问题）",
    "steps_to_reproduce": "复现步骤（如原描述中有）",
    "actual_result": "实际结果",
    "expected_result": "预期结果"
  }},
  "category": "functional|ui|performance|security|compatibility|logic|data",
  "severity_suggestion": "blocker|critical|normal|minor|trivial",
  "root_cause_analysis": "可能的根因分析（代码逻辑/配置/数据/需求理解偏差）",
  "fix_suggestion": "修复建议和排查方向",
  "keywords": ["关键词1", "关键词2"]
}}
""",

    "report_generate": """你是一名测试经理，请根据以下测试数据生成专业的测试报告。

测试数据：
- 项目：{project_name}
- 迭代：{iteration_name}
- 测试范围：{test_scope}
- 执行数据：{execution_data}
- 缺陷数据：{defect_data}

请生成专业的测试报告，以JSON格式返回：
{{
  "summary": "执行摘要（2-3句话）",
  "test_scope": "测试范围描述",
  "execution_result": "执行结果描述",
  "risk_points": ["风险点1", "风险点2"],
  "quality_conclusion": "质量结论（通过/有条件通过/不通过）",
  "suggestions": ["后续建议1", "后续建议2"]
}}
""",
}


def get_prompt(name: str, **kwargs) -> str:
    template = PROMPTS.get(name, "")
    return template.format(**kwargs)
