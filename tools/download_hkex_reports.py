# -*- coding: utf-8 -*-
"""
保险机构 H股报告批量下载脚本（港交所披露易）
数据来源：香港交易所披露易 (HKEXnews)
覆盖：H股/纯港股上市险企（中国太平、阳光保险、众安在线、中国再保险、人保财险、友邦保险等）

技术流程（参照 hkex-filing-scraper）：
  1. prefix.do 查询 stockId（通过股票代码）
  2. GET 搜索页提取 javax.faces.ViewState 令牌
  3. POST 表单设置会话日期范围
  4. GET titleSearchServlet.do 获取分页 JSON 公告（result 双重 JSON 编码）
  5. 按标题关键词分类，下载 PDF

存储：data/保险经营报告下载/{机构名称}/{报告类型}/{标题}.pdf（参照银行版）

用法：
  cd backend && python ../tools/download_hkex_reports.py
"""

import os
import sys
import json
import time
import re
from datetime import datetime
from pathlib import Path

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.database import SessionLocal
from app.models import IalmdBankInstitution

BASE_DIR = Path(settings.REPORTS_DIR)
LOG_FILE = BASE_DIR / "下载日志.txt"
PROGRESS_FILE = BASE_DIR / "进度记录_HKEX.json"

HKEX_BASE = "https://www1.hkexnews.hk"
SEARCH_PAGE = f"{HKEX_BASE}/search/titlesearch.xhtml"
API_ENDPOINT = f"{HKEX_BASE}/search/titleSearchServlet.do"
PREFIX_API = f"{HKEX_BASE}/search/prefix.do"

REQUEST_DELAY = 0.8
DATE_FROM = "20160101"
DATE_TO = "20261231"

# 报告类型（按标题关键词分类）
REPORT_TYPES = [
    {"name": "年度报告", "folder": "年度报告", "keys": ["年度報告", "年報", "Annual Report", "年度业绩"]},
    {"name": "半年度报告", "folder": "半年度报告", "keys": ["中期報告", "中期业绩", "Interim Report", "中報"]},
    {"name": "季度报告", "folder": "季度报告", "keys": ["季度報告", "季報", "第三季度", "第一季度", "第一季度業績"]},
    {"name": "偿付能力报告", "folder": "偿付能力报告", "keys": ["償付能力", "偿付能力", "Solvency"]},
    {"name": "保费收入公告", "folder": "保费收入公告", "keys": ["保費收入", "保费收入", "原保險保費"]},
    {"name": "社会责任报告ESG", "folder": "社会责任报告ESG", "keys": ["社會責任", "环境、社会及管治", "ESG", "可持續發展"]},
]


def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def safe_name(name):
    name = re.sub(r'<[^>]+>', '', name)
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    return re.sub(r'\s+', ' ', name).strip()


def load_progress():
    if PROGRESS_FILE.exists():
        return json.load(open(PROGRESS_FILE, encoding="utf-8"))
    return {"downloaded": []}


def save_progress(p):
    json.dump(p, open(PROGRESS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def query_stock_id(code):
    """通过股票代码查询 stockId"""
    url = f"{PREFIX_API}?lang=ZH&type=A&name={code}&callback=callback"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, verify=False, timeout=30)
        m = re.search(r'callback\((.*)\)', r.text, re.S)
        if m:
            data = json.loads(m.group(1))
            for info in data.get("stockInfo", []):
                if info.get("code", "").zfill(5) == code.zfill(5):
                    return info.get("stockId"), info.get("name")
            # 取第一个匹配前缀的
            if data.get("stockInfo"):
                return data["stockInfo"][0].get("stockId"), data["stockInfo"][0].get("name")
    except Exception as e:
        log(f"  查询 stockId 失败: {e}")
    return None, None


def fetch_announcements(stock_id, session):
    """分页获取某股票的全部公告（近10年）"""
    # 1. GET 搜索页提取 ViewState
    r = session.get(SEARCH_PAGE, verify=False, timeout=30)
    vs = re.search(r'ViewState[^>]*value="([^"]+)"', r.text)
    if not vs:
        log("  未找到 ViewState 令牌")
        return []
    viewstate = vs.group(1)

    # 2. POST 表单设置日期范围
    form = {
        "j_idt10": "j_idt10",
        "j_idt10:loadMoreRange": "100",
        "javax.faces.ViewState": viewstate,
        "from": DATE_FROM,
        "to": DATE_TO,
    }
    session.post(SEARCH_PAGE, data=form, verify=False, timeout=30)

    # 3. 分页获取 JSON 公告
    all_rows = []
    row_range = 100
    while True:
        params = {
            "sortDir": "0", "sortByOptions": "DateTime", "category": "0",
            "market": "SEHK", "stockId": str(stock_id), "documentType": "-1",
            "fromDate": DATE_FROM, "toDate": DATE_TO, "title": "",
            "searchType": "1", "t1code": "-2", "t2Gcode": "-2", "t2code": "-2",
            "rowRange": str(row_range), "lang": "ZH",
        }
        try:
            r = session.get(API_ENDPOINT, params=params,
                            headers={"X-Requested-With": "XMLHttpRequest",
                                     "Referer": SEARCH_PAGE, "Accept": "application/json"},
                            verify=False, timeout=30)
            d = json.loads(r.text)
            result_str = d.get("result")
            has_next = d.get("hasNextRow", False)
            if result_str and result_str != "null":
                rows = json.loads(result_str)
                new_rows = rows[len(all_rows):]
                all_rows.extend(new_rows)
                if not has_next:
                    break
                row_range += len(new_rows) if new_rows else 100
            else:
                break
            if len(all_rows) == 0 and not has_next:
                break
            time.sleep(REQUEST_DELAY)
        except Exception as e:
            log(f"  分页查询失败: {e}")
            break
    return all_rows


def classify(title):
    """按标题关键词分类"""
    for rt in REPORT_TYPES:
        for k in rt["keys"]:
            if k in title:
                return rt
    return None


def process_company(company, progress):
    """处理单个 H股险企"""
    code = company.stock_code
    name = company.bank_name
    log(f"\n{'='*60}")
    log(f"处理机构: {name} (H股 {code})")

    stock_id, hk_name = query_stock_id(code)
    if not stock_id:
        log(f"  ⚠ 未找到 stockId，跳过")
        return
    log(f"  stockId={stock_id}, 港交所名称={hk_name}")

    folder = BASE_DIR / safe_name(name)
    folder.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

    announcements = fetch_announcements(stock_id, session)
    log(f"  共获取 {len(announcements)} 条公告")

    downloaded = 0
    for ann in announcements:
        title = ann.get("TITLE", "")
        file_link = ann.get("FILE_LINK", "")
        file_type = ann.get("FILE_TYPE", "")
        date_time = ann.get("DATE_TIME", "")

        rt = classify(title)
        if not rt:
            continue

        if not file_link or file_type.upper() != "PDF":
            continue

        year = date_time.split("/")[-1][:4] if date_time else "未知"

        rtype_folder = folder / rt["folder"]
        rtype_folder.mkdir(parents=True, exist_ok=True)

        safe_title = safe_name(title)
        # 文件名：年份 + 标题（截断）
        filename = f"{year}_{safe_title[:60]}.pdf"
        filepath = rtype_folder / filename

        key = f"{name}|{rt['name']}|{ann.get('NEWS_ID', '')}|{safe_title}"
        if key in progress["downloaded"]:
            continue

        url = file_link if file_link.startswith("http") else HKEX_BASE + file_link
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, verify=False, timeout=60)
            if r.status_code == 200 and len(r.content) > 1024:
                filepath.write_bytes(r.content)
                progress["downloaded"].append(key)
                downloaded += 1
                log(f"    ✓ {rt['name']}: {filename} ({len(r.content)//1024}KB)")
            time.sleep(REQUEST_DELAY)
        except Exception as e:
            log(f"    下载失败 {title}: {e}")

    save_progress(progress)
    log(f"  机构 {name} 下载完成: {downloaded} 个文件")


def main():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    log("=" * 60)
    log("保险机构 H股报告下载脚本启动（港交所披露易）")
    log(f"时间范围: {DATE_FROM} ~ {DATE_TO}")
    log(f"输出目录: {BASE_DIR}")
    log("=" * 60)

    progress = load_progress()
    db = SessionLocal()
    try:
        companies = db.query(IalmdBankInstitution).filter(
            IalmdBankInstitution.is_deleted == 0,
            IalmdBankInstitution.status == 1,
            IalmdBankInstitution.listing_market == "H",  # 仅纯 H 股（A+H 已由巨潮下载）
            IalmdBankInstitution.stock_code != "",
        ).all()
        log(f"H股上市险企: {len(companies)} 家")
        for c in companies:
            log(f"  - {c.bank_name} ({c.stock_code})")

        for company in companies:
            try:
                process_company(company, progress)
            except Exception as e:
                log(f"  !! 处理 {company.bank_name} 异常: {e}")
    finally:
        db.close()

    log("\n" + "=" * 60)
    log(f"下载完成！累计 {len(progress['downloaded'])} 个文件")
    log("=" * 60)


if __name__ == "__main__":
    main()
