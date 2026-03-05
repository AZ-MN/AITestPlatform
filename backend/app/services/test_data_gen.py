"""测试数据生成服务"""
import random
import string
import uuid
from datetime import datetime, timedelta
from faker import Faker

fake = Faker("zh_CN")


def generate_data(data_type: str, count: int = 10, options: dict = None) -> list:
    """根据类型生成测试数据"""
    options = options or {}
    generators = {
        "name": lambda: fake.name(),
        "phone": lambda: fake.phone_number(),
        "id_card": lambda: fake.ssn(),
        "email": lambda: fake.email(),
        "address": lambda: fake.address(),
        "uuid": lambda: str(uuid.uuid4()),
        "amount": lambda: round(random.uniform(0.01, 99999.99), 2),
        "date": lambda: fake.date(),
        "datetime": lambda: fake.date_time().isoformat(),
        "int": lambda: random.randint(options.get("min", 0), options.get("max", 1000)),
        "string": lambda: fake.text(max_nb_chars=options.get("length", 50)),
        "username": lambda: fake.user_name(),
        "password": lambda: fake.password(),
        "url": lambda: fake.url(),
        "ip": lambda: fake.ipv4(),
        "order_no": lambda: f"ORD{datetime.now().strftime('%Y%m%d')}{random.randint(100000, 999999)}",
        "product_name": lambda: fake.company() + random.choice(["手机", "电脑", "手表", "耳机", "平板"]),
    }
    generator = generators.get(data_type, lambda: fake.text())
    return [generator() for _ in range(count)]


def generate_business_data(template: dict, count: int = 10) -> list[dict]:
    """根据业务模板生成数据"""
    results = []
    for _ in range(count):
        row = {}
        for field in template.get("fields", []):
            field_name = field["name"]
            field_type = field["type"]
            row[field_name] = generate_data(field_type, 1, field.get("options", {}))[0]
        results.append(row)
    return results


def mask_data(value: str, data_type: str) -> str:
    """数据脱敏"""
    if not value:
        return value
    if data_type == "phone":
        return value[:3] + "****" + value[-4:]
    elif data_type == "id_card":
        return value[:6] + "********" + value[-4:]
    elif data_type == "bank_card":
        return "**** **** **** " + value[-4:]
    elif data_type == "email":
        parts = value.split("@")
        if len(parts) == 2:
            return parts[0][:2] + "***@" + parts[1]
    elif data_type == "name":
        return value[0] + "*" * (len(value) - 1)
    return value
