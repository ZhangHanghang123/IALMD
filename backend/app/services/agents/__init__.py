"""Agent 注册表 — 统一管理所有 Agent 类型的映射

Agent 类型与 node_type 的对应关系:
  EXTRACT      → 指标抽取 Agent — 从PDF/HTML提取指标值
  ONTOLOGY_MAP → 本体映射 Agent — 建立银行→指标→本体的关系链
  CALC         → 指标计算 Agent
  BENCHMARK    → 对标分析 Agent — 多银行指标排名
  ATTRIBUTE    → 差异归因 Agent
  REPORT       → 报告生成 Agent
"""
from .extract_agent import ExtractAgent
from .calc_agent import CalcAgent
from .benchmark_agent import BenchmarkAgent
from .attribute_agent import AttributeAgent
from .report_agent import ReportAgent
from .collect_agent import CollectAgent

AGENT_REGISTRY = {
    "EXTRACT": ExtractAgent,
    "ONTOLOGY_MAP": ExtractAgent,  # 复用基类，实际由 workflow_executor 处理
    "CALC": CalcAgent,
    "BENCHMARK": BenchmarkAgent,
    "ATTRIBUTE": AttributeAgent,
    "REPORT": ReportAgent,
    "COLLECT": CollectAgent,
}

AGENT_METADATA = [
    {
        "type": "EXTRACT",
        "name": "指标抽取 Agent",
        "description": "从银行公开报告(PDF/HTML)中提取经营指标数据，支持正则匹配提取",
        "color": "#1677ff",
        "icon": "SearchOutlined",
        "inputs": ["bank_id", "years"],
        "outputs": ["extracted_values"],
    },
    {
        "type": "ONTOLOGY_MAP",
        "name": "本体映射 Agent",
        "description": "将提取的指标值映射到本体概念，建立银行→指标→本体的关系链",
        "color": "#8b5cf6",
        "icon": "ApartmentOutlined",
        "inputs": ["bank_id"],
        "outputs": ["new_mappings", "new_relations"],
    },
    {
        "type": "CALC",
        "name": "指标计算 Agent",
        "description": "基于原始指标计算衍生指标(ROE/ROA/成本收入比)和变化率",
        "color": "#52c41a",
        "icon": "CalculatorOutlined",
        "inputs": ["extracted_data"],
        "outputs": ["calc_results"],
    },
    {
        "type": "BENCHMARK",
        "name": "对标分析 Agent",
        "description": "跨银行指标排名、分位数计算、领先/落后识别、统计分析",
        "color": "#fa8c16",
        "icon": "BarChartOutlined",
        "inputs": ["indicator", "year", "bank_type", "top_n"],
        "outputs": ["rankings", "statistics"],
    },
    {
        "type": "ATTRIBUTE",
        "name": "差异归因 Agent",
        "description": "因子分解(杜邦/瀑布)、根因识别、量化各因子贡献度",
        "color": "#722ed1",
        "icon": "ApartmentOutlined",
        "inputs": ["benchmark_results"],
        "outputs": ["attribution_results"],
    },
    {
        "type": "REPORT",
        "name": "报告生成 Agent",
        "description": "汇总全部分析结果，生成结构化 Markdown 经营分析报告",
        "color": "#f5222d",
        "icon": "FileTextOutlined",
        "inputs": ["all_stages"],
        "outputs": ["report", "title"],
    },
    {
        "type": "COLLECT",
        "name": "报告采集 Agent",
        "description": "从巨潮资讯网采集保险公司10年经营报告，参照银行目录结构存储",
        "color": "#13c2c2",
        "icon": "CloudDownloadOutlined",
        "inputs": ["institution_codes"],
        "outputs": ["download_summary"],
    },
]


def get_agent(node_type: str):
    agent_class = AGENT_REGISTRY.get(node_type)
    if not agent_class:
        raise ValueError(f"未知 Agent 类型: {node_type}，支持: {list(AGENT_REGISTRY.keys())}")
    return agent_class()
