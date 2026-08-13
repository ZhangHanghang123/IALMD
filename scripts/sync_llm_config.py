# -*- coding: utf-8 -*-
"""
LLM 配置同步 — 从 ALMD 数据库同步到 IALMD 数据库

用法：cd backend && python ../scripts/sync_llm_config.py
"""
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# 数据库连接（两个库）
ALMD_DB = "mysql+pymysql://almd:Almd%402026@127.0.0.1:3306/ALMD?charset=utf8mb4"
IALMD_DB = "mysql+pymysql://almd:Almd%402026@127.0.0.1:3306/IALMD?charset=utf8mb4"


def main():
    src = create_engine(ALMD_DB)
    dst = create_engine(IALMD_DB)

    # 1. 读取 ALMD 的 LLM 配置
    with src.connect() as conn:
        rows = conn.execute(text(
            "SELECT provider_name, provider_code, api_key, base_url, model_name, "
            "temperature, max_tokens, is_enabled, is_default, sort_order, remark, status "
            "FROM sys_llm_config WHERE status = 1"
        )).fetchall()
    print(f"ALMD LLM 配置: {len(rows)} 条")

    # 2. 同步到 IALMD（按 provider_code upsert）
    inserted = 0
    updated = 0
    with dst.connect() as conn:
        for r in rows:
            (provider_name, provider_code, api_key, base_url, model_name,
             temperature, max_tokens, is_enabled, is_default, sort_order, remark, status) = r

            exists = conn.execute(text(
                "SELECT id FROM sys_llm_config WHERE provider_code = :code"
            ), {"code": provider_code}).fetchone()

            if exists:
                conn.execute(text(
                    "UPDATE sys_llm_config SET provider_name=:pn, api_key=:ak, base_url=:bu, "
                    "model_name=:mn, temperature=:tp, max_tokens=:mt, is_enabled=:ie, "
                    "is_default=:idf, sort_order=:so, remark=:rk, status=:st, updated_at=NOW() "
                    "WHERE provider_code=:code"
                ), {"pn": provider_name, "ak": api_key, "bu": base_url, "mn": model_name,
                    "tp": temperature, "mt": max_tokens, "ie": is_enabled, "idf": is_default,
                    "so": sort_order, "rk": remark, "st": status, "code": provider_code})
                updated += 1
            else:
                conn.execute(text(
                    "INSERT INTO sys_llm_config (provider_name, provider_code, api_key, base_url, "
                    "model_name, temperature, max_tokens, is_enabled, is_default, sort_order, remark, "
                    "status, created_at, updated_at) VALUES "
                    "(:pn, :code, :ak, :bu, :mn, :tp, :mt, :ie, :idf, :so, :rk, :st, NOW(), NOW())"
                ), {"pn": provider_name, "code": provider_code, "ak": api_key, "bu": base_url,
                    "mn": model_name, "tp": temperature, "mt": max_tokens, "ie": is_enabled,
                    "idf": is_default, "so": sort_order, "rk": remark, "st": status})
                inserted += 1
        conn.commit()

    print(f"  新增: {inserted}")
    print(f"  更新: {updated}")

    # 3. 验证
    with dst.connect() as conn:
        total = conn.execute(text(
            "SELECT COUNT(*) FROM sys_llm_config WHERE status=1"
        )).scalar()
        enabled = conn.execute(text(
            "SELECT provider_name, provider_code, model_name, is_enabled, is_default "
            "FROM sys_llm_config WHERE status=1 ORDER BY id"
        )).fetchall()
    print(f"IALMD 同步后 LLM 配置: {total} 条")
    for r in enabled:
        print(f"  {r[0]}({r[1]}) model={r[2]} enabled={r[3]} default={r[4]}")
    print("=" * 60)
    print("LLM 配置同步完成！")


if __name__ == "__main__":
    main()
