from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.models.user import User
from app.services.test_data_gen import generate_data, generate_business_data, mask_data
from app.schemas.testdata import GenerateDataRequest, GenerateBusinessDataRequest, MaskDataRequest

router = APIRouter()


@router.post("/generate")
async def generate_test_data(data: GenerateDataRequest, current_user: User = Depends(get_current_user)):
    """生成通用测试数据"""
    result = generate_data(data.data_type, data.count, data.options)
    return {"data_type": data.data_type, "count": len(result), "data": result}


@router.post("/generate/business")
async def generate_business_test_data(data: GenerateBusinessDataRequest, current_user: User = Depends(get_current_user)):
    """根据业务模板生成数据"""
    if not data.template:
        return {"error": "请提供模板定义"}
    result = generate_business_data(data.template, data.count)
    return {"count": len(result), "data": result}


@router.post("/mask")
async def mask_sensitive_data(data: MaskDataRequest, current_user: User = Depends(get_current_user)):
    """数据脱敏"""
    masked = mask_data(data.value, data.data_type)
    return {"original": data.value, "masked": masked}


@router.get("/types")
async def get_data_types(current_user: User = Depends(get_current_user)):
    """获取支持的数据类型列表"""
    return {
        "types": [
            {"code": "name", "label": "姓名", "category": "个人信息"},
            {"code": "phone", "label": "手机号", "category": "个人信息"},
            {"code": "id_card", "label": "身份证号", "category": "个人信息"},
            {"code": "email", "label": "邮箱", "category": "个人信息"},
            {"code": "address", "label": "地址", "category": "个人信息"},
            {"code": "uuid", "label": "UUID", "category": "标识符"},
            {"code": "amount", "label": "金额", "category": "数字"},
            {"code": "int", "label": "整数", "category": "数字"},
            {"code": "date", "label": "日期", "category": "时间"},
            {"code": "datetime", "label": "日期时间", "category": "时间"},
            {"code": "username", "label": "用户名", "category": "账户"},
            {"code": "password", "label": "密码", "category": "账户"},
            {"code": "order_no", "label": "订单号", "category": "业务"},
            {"code": "product_name", "label": "商品名称", "category": "业务"},
            {"code": "url", "label": "URL", "category": "网络"},
            {"code": "ip", "label": "IP地址", "category": "网络"},
        ]
    }
