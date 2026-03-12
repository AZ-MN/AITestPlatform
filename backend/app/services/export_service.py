"""
导出服务：支持 Excel / Markdown / CSV 格式
"""
import io
import csv
from typing import List, Tuple
from app.models.testcase import TestCase


def export_cases(cases: List[TestCase], fmt: str) -> Tuple[bytes, str, str]:
    """返回 (文件字节, media_type, filename)"""
    if fmt == "excel":
        return _export_excel(cases)
    elif fmt == "markdown":
        return _export_markdown(cases)
    elif fmt == "postman":
        return _export_postman(cases)
    elif fmt == "jmeter":
        return _export_jmeter(cases)
    else:
        return _export_csv(cases)


def _export_excel(cases: List[TestCase]) -> Tuple[bytes, str, str]:
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        raise RuntimeError("openpyxl 未安装")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "测试用例"

    headers = ["用例ID", "所属模块", "用例标题", "优先级", "测试类型",
               "适用阶段", "前置条件", "操作步骤", "预期结果", "状态", "备注"]
    col_widths = [14, 16, 40, 8, 12, 12, 30, 50, 40, 10, 20]

    # 表头样式
    header_fill = PatternFill("solid", fgColor="4472C4")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    thin = Side(style="thin")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for col_idx, (header, width) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
        ws.column_dimensions[cell.column_letter].width = width

    ws.row_dimensions[1].height = 28

    # 优先级颜色映射
    level_colors = {"P0": "FF4444", "P1": "FF8800", "P2": "FFCC00", "P3": "88CC44"}

    for row_idx, case in enumerate(cases, 2):
        steps_text = _steps_to_text(case.steps or [])
        expected_text = "\n".join(
            f"{i+1}. {s.get('expected', '')}"
            for i, s in enumerate(case.steps or [])
        )
        row_data = [
            case.case_id or "",
            case.module or "",
            case.title or "",
            case.case_level or "P1",
            _type_label(case.test_type),
            _stage_label(case.stage),
            case.preconditions or "",
            steps_text,
            expected_text,
            _status_label(case.status),
            case.remarks or "",
        ]
        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = border
            if col_idx == 4:  # 优先级列着色
                color = level_colors.get(str(value), "FFFFFF")
                cell.fill = PatternFill("solid", fgColor=color)
                cell.font = Font(bold=True, color="FFFFFF")
        ws.row_dimensions[row_idx].height = max(30, len(steps_text.split("\n")) * 15)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "test_cases.xlsx"


def _export_markdown(cases: List[TestCase]) -> Tuple[bytes, str, str]:
    lines = ["# 测试用例清单\n"]
    current_module = None
    for case in cases:
        if case.module != current_module:
            current_module = case.module
            lines.append(f"\n## {current_module or '通用'}\n")
        lines.append(f"### [{case.case_id}] {case.title}\n")
        lines.append(f"- **优先级**：{case.case_level}")
        lines.append(f"- **类型**：{_type_label(case.test_type)}")
        lines.append(f"- **阶段**：{_stage_label(case.stage)}")
        lines.append(f"- **前置条件**：{case.preconditions or '无'}\n")
        lines.append("**操作步骤**\n")
        for s in (case.steps or []):
            lines.append(f"{s.get('step', '')}.  {s.get('action', '')}")
            lines.append(f"   - 预期：{s.get('expected', '')}")
        if case.remarks:
            lines.append(f"\n> 备注：{case.remarks}")
        lines.append("")
    content = "\n".join(lines)
    return content.encode("utf-8"), "text/markdown; charset=utf-8", "test_cases.md"


def _export_csv(cases: List[TestCase]) -> Tuple[bytes, str, str]:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["用例ID", "所属模块", "用例标题", "优先级", "测试类型",
                     "适用阶段", "前置条件", "操作步骤", "预期结果", "状态", "备注"])
    for case in cases:
        writer.writerow([
            case.case_id or "",
            case.module or "",
            case.title or "",
            case.case_level or "P1",
            case.test_type or "",
            case.stage or "",
            case.preconditions or "",
            _steps_to_text(case.steps or []),
            "; ".join(s.get("expected", "") for s in (case.steps or [])),
            case.status or "",
            case.remarks or "",
        ])
    return buf.getvalue().encode("utf-8-sig"), "text/csv; charset=utf-8", "test_cases.csv"


def _export_postman(cases: List[TestCase]) -> Tuple[bytes, str, str]:
    import json
    collection = {
        "info": {
            "name": "AI Test Cases Collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [],
    }
    for c in cases:
        collection["item"].append({
            "name": f"{c.case_id or c.id} {c.title}",
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{base_url}}/api/example",
                    "host": ["{{base_url}}"],
                    "path": ["api", "example"],
                },
                "description": _steps_to_text(c.steps or []),
            },
            "response": [],
        })
    content = json.dumps(collection, ensure_ascii=False, indent=2)
    return content.encode("utf-8"), "application/json; charset=utf-8", "test_cases_postman.json"


def _export_jmeter(cases: List[TestCase]) -> Tuple[bytes, str, str]:
    from xml.sax.saxutils import escape
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">',
        '  <hashTree>',
        '    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="AI Test Cases Plan" enabled="true">',
        '      <stringProp name="TestPlan.comments">Generated by AI Test Platform</stringProp>',
        '    </TestPlan>',
        '    <hashTree>',
        '      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group" enabled="true"/>',
        '      <hashTree>',
    ]
    for c in cases:
        name = escape(f"{c.case_id or c.id} {c.title}")
        comment = escape(_steps_to_text(c.steps or []))
        lines.extend([
            f'        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="{name}" enabled="true">',
            '          <stringProp name="HTTPSampler.method">GET</stringProp>',
            '          <stringProp name="HTTPSampler.domain">${__P(host,localhost)}</stringProp>',
            '          <stringProp name="HTTPSampler.path">/api/example</stringProp>',
            f'          <stringProp name="TestPlan.comments">{comment}</stringProp>',
            '        </HTTPSamplerProxy>',
            '        <hashTree/>',
        ])
    lines.extend([
        '      </hashTree>',
        '    </hashTree>',
        '  </hashTree>',
        '</jmeterTestPlan>',
    ])
    content = "\n".join(lines)
    return content.encode("utf-8"), "application/xml; charset=utf-8", "test_cases_jmeter.jmx"


def _steps_to_text(steps: list) -> str:
    return "\n".join(f"{s.get('step', i+1)}. {s.get('action', '')}" for i, s in enumerate(steps))


def _type_label(t: str) -> str:
    return {"functional": "功能测试", "api": "接口测试", "unit": "单元测试",
            "regression": "回归测试"}.get(t or "", t or "")


def _stage_label(s: str) -> str:
    return {"smoke": "冒烟测试", "integration": "集成测试", "system": "系统测试",
            "regression": "回归测试"}.get(s or "", s or "")


def _status_label(s: str) -> str:
    return {"draft": "草稿", "pending_review": "待评审", "reviewed": "已评审",
            "deprecated": "已作废"}.get(s or "", s or "")
