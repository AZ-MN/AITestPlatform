"""上传文件名规范化与按大小限制的流式写入。"""
import os
import re
from typing import Iterable

import aiofiles
from fastapi import HTTPException, UploadFile


def sanitize_upload_filename(original: str, allowed_extensions: Iterable[str]) -> str:
    """返回仅含 basename 的安全文件名，扩展名必须在白名单中。"""
    allowed = {e.lower().lstrip(".") for e in allowed_extensions}
    base = os.path.basename(original or "") or "upload"
    base = base.replace("\x00", "").strip()
    stem, ext = os.path.splitext(base)
    ext_clean = ext.lower().lstrip(".")
    if ext_clean not in allowed:
        raise ValueError(f"不支持的扩展名: {ext_clean or '(空)'}")
    safe_stem = re.sub(r"[^\w\u4e00-\u9fff\u3000-\u303f\uff00-\uffef.\-]", "_", stem)
    safe_stem = safe_stem.strip("._") or "file"
    if len(safe_stem) > 200:
        safe_stem = safe_stem[:200]
    return f"{safe_stem}.{ext_clean}"


async def save_upload_with_limit(
    file: UploadFile,
    dest_path: str,
    max_bytes: int,
    chunk_size: int = 1024 * 1024,
) -> None:
    """分块写入磁盘；超过 max_bytes 则删除部分文件并抛出 400。"""
    written = 0
    try:
        async with aiofiles.open(dest_path, "wb") as out:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    raise HTTPException(
                        status_code=400,
                        detail=f"文件大小超过限制（最大 {max_bytes // (1024 * 1024)}MB）",
                    )
                await out.write(chunk)
    except HTTPException:
        if os.path.isfile(dest_path):
            try:
                os.unlink(dest_path)
            except OSError:
                pass
        raise
    except Exception:
        if os.path.isfile(dest_path):
            try:
                os.unlink(dest_path)
            except OSError:
                pass
        raise
