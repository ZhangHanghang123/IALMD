# -*- coding: utf-8 -*-
"""
保险机构经营报告批量下载脚本
数据来源：巨潮资讯网 (cninfo.com.cn) - A股上市保险公司公告披露平台
存储方式：参照银行版（data/保险经营报告下载/{机构名称}/{报告类型}/{年份}年{报告类型}.pdf/.html）

从数据库读取保险机构（ialmd_bank_institution），对 A 股上市险企下载近 10 年报告。
非上市/仅港股机构跳过（需从官网/行业协会单独获取）。

用法：
  cd backend && python ../tools/download_insurance_reports.py
"""

import os
import sys
import json
import time
import re
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from pathlib import Path

# 引入后端环境（数据库访问）
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.database import SessionLocal
from app.models import IalmdBankInstitution

# ============================================================
# 配置
# ============================================================
BASE_DIR = Path(settings.REPORTS_DIR)  # data/保险经营报告下载
LOG_FILE = BASE_DIR / "下载日志.txt"
ERROR_LOG = BASE_DIR / "下载失败记录.txt"
PROGRESS_FILE = BASE_DIR / "进度记录.json"

# 下载参数
REQUEST_DELAY = 1.0        # 请求间隔(秒)，避免被限流
MAX_RETRIES = 3            # 单个文件最大重试次数
DOWNLOAD_TIMEOUT = 120     # 下载超时(秒)
PAGE_SIZE = 50             # 每页结果数

# 时间范围：近 10 年
DATE_START = "2016-01-01"
DATE_END = "2026-12-31"

# ============================================================
# 保险报告类型定义
# 每个报告类型: 搜索关键词列表, cninfo分类代码(可选), 文件夹名
# ============================================================
REPORT_TYPES = [
    {
        "name": "年度报告",
        "folder": "年度报告",
        "category": "category_ndbg_szsh",
        "search_keys": ["年度报告"],
        "exclude_keywords": ["摘要", "英文版", "H股", "港股", "更正", "补充", "取消"],
    },
    {
        "name": "半年度报告",
        "folder": "半年度报告",
        "category": "category_bndbg_szsh",
        "search_keys": ["半年度报告"],
        "exclude_keywords": ["摘要", "英文版", "H股", "港股", "更正", "补充", "取消"],
    },
    {
        "name": "一季度报告",
        "folder": "季度报告",
        "category": "category_yjdbg_szsh",
        "search_keys": ["一季度报告", "第一季度报告"],
        "exclude_keywords": ["摘要", "更正", "补充", "取消"],
    },
    {
        "name": "三季度报告",
        "folder": "季度报告",
        "category": "category_sjdbg_szsh",
        "search_keys": ["三季度报告", "第三季度报告"],
        "exclude_keywords": ["摘要", "更正", "补充", "取消"],
    },
    {
        "name": "偿付能力报告",
        "folder": "偿付能力报告",
        "category": None,
        "search_keys": ["偿付能力报告", "偿付能力"],
        "exclude_keywords": ["更正", "补充", "摘要"],
    },
    {
        "name": "精算报告",
        "folder": "精算报告",
        "category": None,
        "search_keys": ["精算报告", "内含价值报告"],
        "exclude_keywords": ["更正", "补充"],
    },
    {
        "name": "保费收入公告",
        "folder": "保费收入公告",
        "category": None,
        "search_keys": ["保费收入", "原保险保费收入"],
        "exclude_keywords": ["更正", "补充"],
    },
    {
        "name": "分红实现率公告",
        "folder": "分红实现率公告",
        "category": None,
        "search_keys": ["分红实现率", "红利实现率"],
        "exclude_keywords": ["更正", "补充"],
    },
    {
        "name": "社会责任报告ESG",
        "folder": "社会责任报告ESG",
        "category": None,
        "search_keys": ["社会责任报告", "ESG", "可持续发展报告"],
        "exclude_keywords": ["更正", "补充"],
    },
    {
        "name": "消费者权益保护工作报告",
        "folder": "消费者权益保护工作报告",
        "category": None,
        "search_keys": ["消费者权益保护", "消保"],
        "exclude_keywords": ["更正", "补充"],
    },
]


# ============================================================
# 工具函数
# ============================================================
def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def safe_filename(name):
    """生成安全的文件名，去除HTML标签"""
    name = re.sub(r'</?em>', '', name)
    name = re.sub(r'<[^>]+>', '', name)
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def log_message(msg, log_file=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    if log_file:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"downloaded": [], "failed": [], "skipped": []}


def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


# ============================================================
# cninfo API 查询
# ============================================================
CNINFO_QUERY_URL = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
CNINFO_STATIC_URL = "http://static.cninfo.com.cn/"


def query_cninfo(searchkey, column, category=None, page=1, org_id=None, sec_code=None):
    """查询巨潮资讯网公告"""
    params = {
        "pageNum": str(page),
        "pageSize": str(PAGE_SIZE),
        "column": column,
        "tabName": "fulltext",
        "searchkey": searchkey,
        "seDate": f"{DATE_START}~{DATE_END}",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true",
    }
    if category:
        params["category"] = category
    if org_id and sec_code:
        params["stock"] = f"{sec_code},{org_id}"

    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(CNINFO_QUERY_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    req.add_header("Accept", "application/json, text/javascript, */*; q=0.01")
    req.add_header("X-Requested-With", "XMLHttpRequest")
    req.add_header("Origin", "http://www.cninfo.com.cn")
    req.add_header("Referer", "http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search")

    try:
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read().decode("utf-8"))
        return result
    except Exception as e:
        log_message(f"  查询失败: {e}", LOG_FILE)
        return None


def get_org_id(short_name, sec_code, column):
    """通过搜索获取机构 orgId"""
    result = query_cninfo(short_name, column, page=1)
    if result and result.get("announcements"):
        for ann in result["announcements"]:
            if ann.get("secCode") == sec_code:
                return ann.get("orgId")
        for ann in result["announcements"]:
            if short_name in (ann.get("secName") or "") or short_name in (ann.get("announcementTitle") or ""):
                return ann.get("orgId")
    return None


def fetch_all_announcements(short_name, sec_code, column, report_type):
    """获取某机构某类报告的所有公告"""
    all_announcements = []
    category = report_type.get("category")
    search_keys = report_type.get("search_keys", [])
    exclude_keywords = report_type.get("exclude_keywords", [])

    org_id = get_org_id(short_name, sec_code, column)

    for search_key in search_keys:
        full_searchkey = f"{short_name} {search_key}"
        page = 1
        while True:
            result = query_cninfo(
                searchkey=full_searchkey, column=column, category=category,
                page=page, org_id=org_id, sec_code=sec_code,
            )
            if not result or not result.get("announcements"):
                break
            announcements = result["announcements"]
            for ann in announcements:
                if sec_code and ann.get("secCode") != sec_code:
                    continue
                title = ann.get("announcementTitle", "")
                should_exclude = any(ex_kw in title for ex_kw in exclude_keywords)
                if should_exclude:
                    continue
                key_matched = any(sk in title for sk in search_keys)
                if not key_matched:
                    continue
                ann_id = ann.get("announcementId")
                if ann_id and ann_id not in [a.get("announcementId") for a in all_announcements]:
                    all_announcements.append(ann)
            total_pages = result.get("totalpages", 1)
            if page >= total_pages:
                break
            page += 1
            time.sleep(REQUEST_DELAY)
    return all_announcements


# ============================================================
# 文件下载
# ============================================================
def download_file(url, filepath, retries=MAX_RETRIES):
    if os.path.exists(filepath):
        if os.path.getsize(filepath) > 1024:
            return "skipped"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            resp = urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT)
            data = resp.read()
            if len(data) < 100:
                return "failed"
            with open(filepath, "wb") as f:
                f.write(data)
            return "downloaded"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return "not_found"
            log_message(f"    HTTP错误 {e.code} (尝试 {attempt+1}/{retries})", LOG_FILE)
        except Exception as e:
            log_message(f"    下载失败: {e} (尝试 {attempt+1}/{retries})", LOG_FILE)
        if attempt < retries - 1:
            time.sleep(2 * (attempt + 1))
    return "failed"


def try_download_html(adjunct_url, filepath, sec_code, ann_id, title, ann_time_str):
    """尝试获取HTML版本（直接下载或生成跳转链接）"""
    for ext in [".HTML", ".html"]:
        html_url = CNINFO_STATIC_URL + adjunct_url.replace(".PDF", ext)
        try:
            req = urllib.request.Request(html_url)
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            resp = urllib.request.urlopen(req, timeout=10)
            data = resp.read()
            if len(data) > 200:
                with open(filepath, "wb") as f:
                    f.write(data)
                return "html_downloaded"
        except Exception:
            pass

    viewer_url = f"http://www.cninfo.com.cn/new/disclosure/detail?stockCode={sec_code}&announcementId={ann_id}"
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>{title}</title></head>
<body><h1>{title}</h1><p>公告日期: {ann_time_str}</p>
<p><a href="{viewer_url}" target="_blank">点击查看HTML版本（巨潮资讯网）</a></p></body></html>"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    return "html_link"


# ============================================================
# 主下载逻辑
# ============================================================
def process_company(company, progress):
    """处理单个保险机构的所有报告下载"""
    name = company.bank_name
    sec_code = company.stock_code
    market = company.listing_market or ""
    short = company.short_name or name

    # 确定交易所板块
    if market == "A" or market == "A+H":
        column = "szse" if sec_code.startswith("0") or sec_code.startswith("3") else "sse"
    else:
        log_message(f"\n{'='*60}", LOG_FILE)
        log_message(f"机构: {name} — 未在A股上市({market})，跳过巨潮下载", LOG_FILE)
        progress["skipped"].append({"company": name, "reason": f"未A股上市({market})"})
        return

    folder = BASE_DIR / safe_filename(name)
    log_message(f"\n{'='*60}", LOG_FILE)
    log_message(f"处理机构: {name} (简称: {short})", LOG_FILE)
    log_message(f"  股票代码: {sec_code}, 交易所: {column}", LOG_FILE)
    ensure_dir(folder)

    total_downloaded = 0
    total_skipped = 0
    total_failed = 0
    total_not_found = 0

    for report_type in REPORT_TYPES:
        report_folder = folder / report_type["folder"]
        ensure_dir(report_folder)
        log_message(f"\n  查询报告类型: {report_type['name']}", LOG_FILE)
        announcements = fetch_all_announcements(short, sec_code, column, report_type)
        log_message(f"    找到 {len(announcements)} 条公告", LOG_FILE)

        for ann in announcements:
            title = ann.get("announcementTitle", "")
            adjunct_url = ann.get("adjunctUrl", "")
            ann_id = ann.get("announcementId", "")
            ann_time = ann.get("announcementTime", 0)
            if not adjunct_url:
                continue

            if ann_time:
                ann_date = datetime.fromtimestamp(ann_time / 1000).strftime("%Y-%m-%d")
                year = ann_date[:4]
            else:
                ann_date = "未知日期"
                year = "未知年份"

            safe_title = safe_filename(title)
            pdf_path = report_folder / f"{safe_title}.pdf"
            html_path = report_folder / f"{safe_title}.html"
            pdf_url = CNINFO_STATIC_URL + adjunct_url

            file_key = f"{name}|{report_type['name']}|{ann_id}|{safe_title}"
            if file_key in progress["downloaded"]:
                total_skipped += 1
                continue

            log_message(f"    下载PDF: {safe_title}", LOG_FILE)
            result = download_file(pdf_url, str(pdf_path))
            if result == "downloaded":
                total_downloaded += 1
                progress["downloaded"].append(file_key)
                log_message(f"    ✓ PDF下载成功 ({os.path.getsize(str(pdf_path))/1024:.0f}KB)", LOG_FILE)
            elif result == "skipped":
                total_skipped += 1
                progress["downloaded"].append(file_key)
            elif result == "not_found":
                total_not_found += 1
            else:
                total_failed += 1
                progress["failed"].append({"company": name, "report": report_type["name"], "title": title, "url": pdf_url})

            try_download_html(adjunct_url, str(html_path), sec_code, ann_id, safe_title, ann_date)
            time.sleep(REQUEST_DELAY)

    log_message(f"\n  机构 {name} 汇总: 下载{total_downloaded}, 跳过{total_skipped}, 失败{total_failed}, 不存在{total_not_found}", LOG_FILE)
    save_progress(progress)


def main():
    ensure_dir(BASE_DIR)
    log_message("=" * 60, LOG_FILE)
    log_message("保险机构经营报告批量下载脚本启动", LOG_FILE)
    log_message(f"时间范围: {DATE_START} ~ {DATE_END}", LOG_FILE)
    log_message(f"输出目录: {BASE_DIR}", LOG_FILE)
    log_message("=" * 60, LOG_FILE)

    progress = load_progress()

    # 从数据库读取保险机构
    db = SessionLocal()
    try:
        companies = db.query(IalmdBankInstitution).filter(
            IalmdBankInstitution.is_deleted == 0,
            IalmdBankInstitution.status == 1,
        ).order_by(IalmdBankInstitution.id).all()
        log_message(f"数据库机构总数: {len(companies)}", LOG_FILE)

        a_share = [c for c in companies if (c.listing_market or "") in ("A", "A+H") and c.stock_code]
        log_message(f"A股上市险企(可下载): {len(a_share)} 家", LOG_FILE)
        for c in a_share:
            log_message(f"  - {c.bank_name} ({c.stock_code})", LOG_FILE)

        for company in a_share:
            try:
                process_company(company, progress)
            except Exception as e:
                log_message(f"  !! 处理 {company.bank_name} 异常: {e}", LOG_FILE)

    finally:
        db.close()

    log_message("\n" + "=" * 60, LOG_FILE)
    log_message("下载完成！最终统计:", LOG_FILE)
    log_message(f"  成功下载/跳过: {len(progress['downloaded'])} 个文件", LOG_FILE)
    log_message(f"  下载失败: {len(progress['failed'])} 个文件", LOG_FILE)
    log_message(f"  跳过机构(非A股): {len(progress['skipped'])} 家", LOG_FILE)
    log_message("=" * 60, LOG_FILE)


if __name__ == "__main__":
    main()
