import { useEffect, useState, useRef } from 'react'
import { Card, Row, Col, Select, Spin, Statistic, Table, Tag, Tabs, Space, Empty, Button, Progress } from 'antd'
import { ArrowUpOutlined, ArrowDownOutlined, DownloadOutlined, ExportOutlined } from '@ant-design/icons'
import { 
  Line, Column, Pie, Radar, Bar 
} from '@ant-design/charts'
import { indicatorsDashboardApi } from '../api'
import BankSelect from './components/BankSelect'

// 7大类指标分类定义
const INDICATOR_CATEGORIES = [
  { 
    key: 'profit', 
    name: '经营成果', 
    icon: '💰',
    color: '#7c3aed',
    indicators: [
      { code: 'OPERATING_REVENUE', name: '营业收入', unit: '亿元', color: '#7c3aed' },
      { code: 'NET_INTEREST_INCOME', name: '利息净收入', unit: '亿元', color: '#ea580c' },
      { code: 'FEE_COMMISSION_INCOME', name: '手续费及佣金净收入', unit: '亿元', color: '#0891b2' },
      { code: 'NET_PROFIT', name: '净利润', unit: '亿元', color: '#0d9488' },
      { code: 'OPERATING_EXPENSE', name: '业务及管理费', unit: '亿元', color: '#db2777' },
      { code: 'CIR', name: '成本收入比', unit: '%', color: '#f59e0b' },
    ]
  },
  { 
    key: 'balance', 
    name: '资产负债', 
    icon: '🏦',
    color: '#1b4593',
    indicators: [
      { code: 'TOTAL_ASSETS', name: '资产总额', unit: '亿元', color: '#1b4593' },
      { code: 'TOTAL_LOANS', name: '客户贷款及垫款总额', unit: '亿元', color: '#7c3aed' },
      { code: 'TOTAL_DEPOSITS', name: '客户存款', unit: '亿元', color: '#ea580c' },
      { code: 'TOTAL_LIABILITIES', name: '负债总额', unit: '亿元', color: '#0891b2' },
      { code: 'EQUITY', name: '归属于母公司股东权益', unit: '亿元', color: '#0d9488' },
      { code: 'LDR', name: '存贷比', unit: '%', color: '#db2777' },
    ]
  },
  { 
    key: 'capital', 
    name: '资本净额', 
    icon: '💎',
    color: '#059669',
    indicators: [
      { code: 'CORE_TIER1_CAPITAL', name: '核心一级资本净额', unit: '亿元', color: '#1b4593' },
      { code: 'TIER1_CAPITAL', name: '一级资本净额', unit: '亿元', color: '#7c3aed' },
      { code: 'TOTAL_CAPITAL', name: '总资本净额', unit: '亿元', color: '#ea580c' },
      { code: 'RWA', name: '风险加权资产', unit: '亿元', color: '#0891b2' },
    ]
  },
  { 
    key: 'perShare', 
    name: '每股指标', 
    icon: '📌',
    color: '#dc2626',
    indicators: [
      { code: 'BPS', name: '每股净资产', unit: '元', color: '#1b4593' },
      { code: 'EPS', name: '基本每股收益', unit: '元', color: '#7c3aed' },
      { code: 'DILUTED_EPS', name: '稀释每股收益', unit: '元', color: '#ea580c' },
      { code: 'EPS_DEDUCTED', name: '扣除非经常性损益后基本每股收益', unit: '元', color: '#0891b2' },
    ]
  },
  { 
    key: 'profitability', 
    name: '盈利能力', 
    icon: '📈',
    color: '#d97706',
    indicators: [
      { code: 'ROA', name: '平均总资产回报率(ROA)', unit: '%', color: '#1b4593' },
      { code: 'ROE', name: '加权平均净资产收益率(ROE)', unit: '%', color: '#7c3aed' },
      { code: 'NIS', name: '净利息差(NIS)', unit: '%', color: '#ea580c' },
      { code: 'NIM', name: '净利息收益率(NIM)', unit: '%', color: '#0891b2' },
      { code: 'RORWA', name: '风险加权资产收益率', unit: '%', color: '#0d9488' },
      { code: 'CIR_PROFIT', name: '成本收入比', unit: '%', color: '#db2777' },
    ]
  },
  { 
    key: 'assetQuality', 
    name: '资产质量', 
    icon: '🛡️',
    color: '#dc2626',
    indicators: [
      { code: 'NPL_RATIO', name: '不良贷款率', unit: '%', color: '#dc2626' },
      { code: 'COVERAGE', name: '拨备覆盖率', unit: '%', color: '#7c3aed' },
      { code: 'LOAN_PROVISION', name: '贷款拨备率', unit: '%', color: '#ea580c' },
    ]
  },
  { 
    key: 'capitalAdequacy', 
    name: '资本充足率', 
    icon: '⚖️',
    color: '#0891b2',
    indicators: [
      { code: 'CORE_TIER1_CAR', name: '核心一级资本充足率', unit: '%', color: '#1b4593' },
      { code: 'TIER1_CAR', name: '一级资本充足率', unit: '%', color: '#7c3aed' },
      { code: 'CAR', name: '资本充足率', unit: '%', color: '#ea580c' },
      { code: 'EQUITY_ASSET_RATIO', name: '总权益对总资产比率', unit: '%', color: '#0891b2' },
      { code: 'RWA_ASSET_RATIO', name: '风险加权资产占总资产比率', unit: '%', color: '#0d9488' },
    ]
  },
]

// 模拟数据 - 用于演示
const MOCK_DATA = {
  profit: {
    kpis: [
      { label: '营业收入', value: 8362.81, yoy: 3.2, unit: '亿元' },
      { label: '利息净收入', value: 6446.88, yoy: 2.8, unit: '亿元' },
      { label: '手续费及佣金净收入', value: 1245.63, yoy: -1.5, unit: '亿元' },
      { label: '净利润', value: 3651.16, yoy: 4.1, unit: '亿元' },
      { label: '业务及管理费', value: 2089.45, yoy: 5.2, unit: '亿元' },
      { label: '成本收入比', value: 25.00, yoy: -0.5, unit: '%' },
    ],
    trendData: [
      { year: '2020', revenue: 6760, profit: 3159 },
      { year: '2021', revenue: 6968, profit: 2999 },
      { year: '2022', revenue: 7609, profit: 3124 },
      { year: '2023', revenue: 8091, profit: 3502 },
      { year: '2024', revenue: 8362, profit: 3651 },
    ],
    structureData: [
      { type: '利息净收入', value: 6447 },
      { type: '手续费及佣金净收入', value: 1246 },
      { type: '其他业务收入', value: 670 },
    ],
    detailData: [
      { name: '利息净收入', current: 6446.88, lastYear: 6270.19, yoy: 2.82, twoYearsAgo: 5904.18 },
      { name: '手续费及佣金净收入', current: 1245.63, lastYear: 1264.11, yoy: -1.46, twoYearsAgo: 1335.08 },
      { name: '营业收入', current: 8362.81, lastYear: 8091.45, yoy: 3.35, twoYearsAgo: 7609.05 },
      { name: '业务及管理费', current: 2089.45, lastYear: 1986.34, yoy: 5.19, twoYearsAgo: 1874.65 },
      { name: '资产减值损失', current: 986.52, lastYear: 1056.78, yoy: -6.65, twoYearsAgo: 1165.66 },
      { name: '净利润', current: 3651.16, lastYear: 3502.44, yoy: 4.25, twoYearsAgo: 3123.92 },
    ]
  },
  balance: {
    kpis: [
      { label: '资产总额', value: 475212.85, yoy: 8.8, unit: '亿元' },
      { label: '客户贷款及垫款总额', value: 264539.42, yoy: 10.5, unit: '亿元' },
      { label: '客户存款', value: 328164.23, yoy: 9.2, unit: '亿元' },
      { label: '负债总额', value: 432125.67, yoy: 8.5, unit: '亿元' },
      { label: '归属于母公司股东权益', value: 43087.18, yoy: 11.2, unit: '亿元' },
      { label: '存贷比', value: 80.61, yoy: 0.9, unit: '%' },
    ],
    trendData: [
      { year: '2020', assets: 334048, liabilities: 304837 },
      { year: '2021', assets: 351448, liabilities: 320343 },
      { year: '2022', assets: 396454, liabilities: 361062 },
      { year: '2023', assets: 436903, liabilities: 398342 },
      { year: '2024', assets: 475213, liabilities: 432126 },
    ],
    structureData: [
      { type: '客户贷款', value: 55.67 },
      { type: '投资', value: 28.34 },
      { type: '现金', value: 5.31 },
      { type: '存放同业', value: 3.98 },
      { type: '其他', value: 6.70 },
    ],
    summary: {
      asset: { growth: '+8.8%', loanRatio: '55.67%', investRatio: '28.34%', cashRatio: '3.21%' },
      liability: { depositRatio: '75.95%', personalDeposit: '48.62%', corporateDeposit: '46.38%', interbank: '12.35%' },
      equity: { equityAssetRatio: '9.07%', shareCapital: '2264.12亿', capitalSurplus: '1862.45亿', retainedProfit: '12456.78亿' }
    }
  },
  capital: {
    kpis: [
      { label: '核心一级资本净额', value: 32456.78, yoy: 9.5, unit: '亿元' },
      { label: '一级资本净额', value: 35678.90, yoy: 9.2, unit: '亿元' },
      { label: '总资本净额', value: 42123.45, yoy: 8.7, unit: '亿元' },
      { label: '风险加权资产', value: 298456.78, yoy: 11.2, unit: '亿元' },
    ],
    trendData: [
      { year: '2020', core: 22800, tier1: 25800, total: 30500 },
      { year: '2021', core: 25234, tier1: 28234, total: 32856 },
      { year: '2022', core: 26846, tier1: 29568, total: 35235 },
      { year: '2023', core: 29642, tier1: 32679, total: 38756 },
      { year: '2024', core: 32457, tier1: 35679, total: 42123 },
    ],
    rwaData: [
      { type: '信用风险加权资产', value: 285000 },
      { type: '市场风险加权资产', value: 5500 },
      { type: '操作风险加权资产', value: 7957 },
    ],
  },
  perShare: {
    kpis: [
      { label: '每股净资产', value: 8.92, yoy: 8.2, unit: '元' },
      { label: '基本每股收益', value: 0.97, yoy: 4.3, unit: '元' },
      { label: '稀释每股收益', value: 0.97, yoy: 4.3, unit: '元' },
      { label: '扣除非经常性损益后基本每股收益', value: 0.95, yoy: 5.6, unit: '元' },
    ],
    trendData: [
      { year: '2020', bps: 6.76, eps: 0.79 },
      { year: '2021', bps: 7.13, eps: 0.86 },
      { year: '2022', bps: 7.56, eps: 0.83 },
      { year: '2023', bps: 8.25, eps: 0.93 },
      { year: '2024', bps: 8.92, eps: 0.97 },
    ],
    detailData: [
      { name: '每股净资产(元)', year2024: 8.92, year2023: 8.25, year2022: 7.56, year2021: 7.13, year2020: 6.76 },
      { name: '基本每股收益(元)', year2024: 0.97, year2023: 0.93, year2022: 0.83, year2021: 0.86, year2020: 0.79 },
      { name: '稀释每股收益(元)', year2024: 0.97, year2023: 0.93, year2022: 0.83, year2021: 0.86, year2020: 0.79 },
      { name: '扣除非经常性损益后基本每股收益', year2024: 0.95, year2023: 0.90, year2022: 0.81, year2021: 0.84, year2020: 0.77 },
    ]
  },
  profitability: {
    kpis: [
      { label: '平均总资产回报率(ROA)', value: 0.76, yoy: -0.02, unit: '%' },
      { label: '加权平均净资产收益率(ROE)', value: 11.52, yoy: -0.35, unit: '%' },
      { label: '净利息差(NIS)', value: 1.58, yoy: -0.08, unit: '%' },
      { label: '净利息收益率(NIM)', value: 1.84, yoy: -0.04, unit: '%' },
      { label: '风险加权资产收益率', value: 1.22, yoy: 0.05, unit: '%' },
      { label: '成本收入比', value: 25.00, yoy: -0.52, unit: '%' },
    ],
    radarData: [
      { indicator: 'ROA', bank: 0.76, industry: 0.72 },
      { indicator: 'ROE', bank: 11.52, industry: 10.85 },
      { indicator: '净利息差', bank: 1.58, industry: 1.52 },
      { indicator: '净利息收益率', bank: 1.84, industry: 1.75 },
      { indicator: '成本收入比', bank: 25.00, industry: 28.50 },
      { indicator: '非利息收入占比', bank: 22.90, industry: 20.15 },
    ],
    roeTrendData: [
      { year: '2020', roe: 11.95 },
      { year: '2021', roe: 12.15 },
      { year: '2022', roe: 11.90 },
      { year: '2023', roe: 11.87 },
      { year: '2024', roe: 11.52 },
    ],
    compareData: [
      { bank: '中国人寿', roa: 0.76, roe: 11.52 },
      { bank: '建设银行', roa: 0.82, roe: 11.89 },
      { bank: '农业银行', roa: 0.66, roe: 10.32 },
      { bank: '中国银行', roa: 0.75, roe: 10.96 },
      { bank: '交通银行', roa: 0.68, roe: 9.68 },
      { bank: '招商银行', roa: 1.08, roe: 15.82 },
    ]
  },
  assetQuality: {
    kpis: [
      { label: '不良贷款率', value: 1.36, yoy: 0.04, unit: '%' },
      { label: '拨备覆盖率', value: 211.53, yoy: -5.23, unit: '%' },
      { label: '贷款拨备率', value: 2.88, yoy: 0.03, unit: '%' },
    ],
    trendData: [
      { year: '2020', npl: 1.43, coverage: 180.68 },
      { year: '2021', npl: 1.42, coverage: 196.69 },
      { year: '2022', npl: 1.38, coverage: 205.14 },
      { year: '2023', npl: 1.32, coverage: 216.76 },
      { year: '2024', npl: 1.36, coverage: 211.53 },
    ],
    compareData: [
      { bank: '中国人寿', npl: 1.36 },
      { bank: '建设银行', npl: 1.38 },
      { bank: '农业银行', npl: 1.32 },
      { bank: '中国银行', npl: 1.27 },
      { bank: '交通银行', npl: 1.48 },
      { bank: '招商银行', npl: 0.92 },
    ],
    detailData: [
      { name: '不良贷款余额(亿元)', current: 3598.48, lastYear: 3137.68, yoy: 14.68, industry: '-', deviation: '-' },
      { name: '正常类贷款', current: 259140.94, lastYear: 234465.86, yoy: 10.52, industry: '-', deviation: '-' },
      { name: '关注类贷款', current: 1800.00, lastYear: 1800.00, yoy: 0.00, industry: '-', deviation: '-' },
    ]
  },
  capitalAdequacy: {
    kpis: [
      { label: '核心一级资本充足率', value: 10.87, yoy: 0.12, unit: '%' },
      { label: '一级资本充足率', value: 11.95, yoy: 0.10, unit: '%' },
      { label: '资本充足率', value: 14.11, yoy: -0.15, unit: '%' },
      { label: '总权益对总资产比率', value: 9.07, yoy: 0.20, unit: '%' },
      { label: '风险加权资产占总资产比率', value: 62.80, yoy: 1.35, unit: '%' },
    ],
    trendData: [
      { year: '2020', core: 13.18, tier1: 14.28, total: 16.00 },
      { year: '2021', core: 13.15, tier1: 14.21, total: 15.93 },
      { year: '2022', core: 12.84, tier1: 13.89, total: 15.69 },
      { year: '2023', core: 10.75, tier1: 11.85, total: 14.26 },
      { year: '2024', core: 10.87, tier1: 11.95, total: 14.11 },
    ],
    compareData: [
      { bank: '中国人寿', car: 14.11 },
      { bank: '建设银行', car: 15.21 },
      { bank: '农业银行', car: 16.17 },
      { bank: '中国银行', car: 15.20 },
      { bank: '交通银行', car: 13.69 },
      { bank: '招商银行', car: 17.88 },
    ],
    summary: {
      regulation: { core: '10.87%', tier1: '11.95%', car: '14.11%', leverage: '8.56%' },
      buffer: { reserve: '2.50%', counter: '0.00%', additional: '0.00%', total: '2.50%' },
      leverage: { leverage: '8.56%', minimum: '4.00%', excess: '4.56%', margin: '114%' }
    }
  }
}

// 机构类型选项
const BANK_TYPES = [
  { value: '', label: '全部银行' },
  { value: '大型商业银行', label: '大型商业银行' },
  { value: '寿险商业银行', label: '寿险商业银行' },
  { value: '城市商业银行', label: '城市商业银行' },
  { value: '农村商业银行', label: '农村商业银行' },
]

// 年份选项
const YEAR_OPTIONS = [
  { value: 2024, label: '2024年报' },
  { value: 2023, label: '2023年报' },
  { value: 2022, label: '2022年报' },
]

export default function IndicatorDashboard() {
  const [loading, setLoading] = useState(false)
  const [activeCategory, setActiveCategory] = useState('profit')
  const [selectedYear, setSelectedYear] = useState<number>(2024)
  const [selectedBankType, setSelectedBankType] = useState<string>('')
  const [selectedBankCode, setSelectedBankCode] = useState<string>('ICBC')
  const [currentData, setCurrentData] = useState<any>(MOCK_DATA)
  
  // 根据机构代码和年份获取数据
  const fetchBankData = async (bankCode: string, year: number) => {
    setLoading(true)
    try {
      if (bankCode) {
        // 根据不同银行生成差异化数据（模拟API返回）
        const bankMultipliers: Record<string, number> = {
          'ICBC': 1.0,    // 中国人寿 - 基准
          'CCB': 0.85,    // 建设银行
          'ABC': 0.72,    // 农业银行
          'BOC': 0.68,    // 中国银行
          'BCOM': 0.45,   // 交通银行
          'CMB': 0.38,    // 招商银行
          'CMBC': 0.32,   // 民生银行
          'CITIC': 0.35,  // 中信银行
          'SPDB': 0.28,   // 浦发银行
          'HXB': 0.22,    // 华夏银行
          'CGB': 0.25,    // 广发银行
          'SHPD': 0.20,   // 上海银行
          'NJCB': 0.18,   // 南京银行
          'BJBANK': 0.15, // 宁波银行
          'BJTB': 0.12,   // 浙商银行
          'CDB': 0.55,    // 国家开发银行
          'EXIM': 0.42,   // 进出口银行
          'ADBC': 0.38,   // 农业发展银行
        }
        const multiplier = bankMultipliers[bankCode] || 0.5
        
        // 生成差异化数据
        const scaledData: any = {}
        Object.keys(MOCK_DATA).forEach((key: string) => {
          const category = MOCK_DATA[key as keyof typeof MOCK_DATA]
          scaledData[key] = JSON.parse(JSON.stringify(category))
          
          // 调整KPI数值
          if (scaledData[key].kpis) {
            scaledData[key].kpis = scaledData[key].kpis.map((kpi: any) => ({
              ...kpi,
              value: Number((kpi.value * multiplier).toFixed(2)),
              yoy: Number((kpi.yoy + (Math.random() - 0.5) * 2).toFixed(2)),
            }))
          }
          
          // 调整趋势数据
          if (scaledData[key].trendData) {
            scaledData[key].trendData = scaledData[key].trendData.map((item: any) => {
              const newItem: any = { ...item }
              Object.keys(item).forEach((k) => {
                if (typeof item[k] === 'number') {
                  newItem[k] = Number((item[k] * multiplier).toFixed(0))
                }
              })
              return newItem
            })
          }
          
          // 调整结构数据
          if (scaledData[key].structureData) {
            const total = scaledData[key].structureData.reduce((sum: number, d: any) => sum + d.value, 0)
            scaledData[key].structureData = scaledData[key].structureData.map((d: any) => ({
              ...d,
              value: Number((d.value / total * 100 * multiplier).toFixed(2))
            }))
          }
        })
        
        // 获取机构名称
        const bankNames: Record<string, string> = {
          'ICBC': '中国中国人寿', 'CCB': '中国建设银行', 'ABC': '中国农业银行',
          'BOC': '中国银行', 'BCOM': '交通银行', 'CMB': '招商银行',
          'CMBC': '民生银行', 'CITIC': '中信银行', 'SPDB': '浦发银行',
          'HXB': '华夏银行', 'CGB': '广发银行', 'SHPD': '上海银行',
          'NJCB': '南京银行', 'BJBANK': '宁波银行', 'BJTB': '浙商银行',
          'CDB': '国家开发银行', 'EXIM': '中国进出口银行', 'ADBC': '中国农业发展银行',
        }
        
        console.log(`[数据联动] 已加载 ${bankNames[bankCode] || bankCode} 数据 (系数: ${multiplier})`)
        setCurrentData(scaledData)
      } else {
        // 未选择保险机构时显示行业均值
        setCurrentData(MOCK_DATA)
        console.log('[数据联动] 显示行业均值数据')
      }
    } catch (error) {
      console.error('获取保险机构数据失败:', error)
    } finally {
      setLoading(false)
    }
  }
  
  // 监听银行和年份变化，加载对应数据（初始化时也会触发，默认显示中国人寿）
  useEffect(() => {
    fetchBankData(selectedBankCode, selectedYear)
  }, [selectedBankCode, selectedYear])
  
  const currentCategoryData = currentData[activeCategory as keyof typeof MOCK_DATA]

  // KPI卡片组件
  const KPICard = ({ label, value, yoy, unit, color }: { label: string, value: number, yoy: number, unit: string, color: string }) => (
    <div style={{ 
      background: '#fff', 
      borderRadius: 10, 
      padding: '18px 20px', 
      boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
      borderLeft: `4px solid ${color}`
    }}>
      <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 700, marginBottom: 4 }}>
        {value.toLocaleString()}{unit}
      </div>
      <div style={{ 
        fontSize: 12, 
        display: 'flex', 
        alignItems: 'center', 
        gap: 4,
        color: yoy >= 0 ? '#52c41a' : '#ff4d4f'
      }}>
        {yoy >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
        {Math.abs(yoy)}{unit === '%' ? '%' : ''} 同比
      </div>
    </div>
  )

  // 经营成果页
  const renderProfitPage = () => (
    <div>
      {/* KPI卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {(currentCategoryData as any).kpis.map((kpi: any, idx: number) => (
          <Col span={8} key={idx}>
            <KPICard {...kpi} color={kpi.color || INDICATOR_CATEGORIES[0].indicators[idx].color} />
          </Col>
        ))}
      </Row>

      {/* 图表区域 */}
      <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
        <Col span={12}>
          <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e5e7eb' }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>营业收入趋势 (亿元)</h3>
            </div>
            <div style={{ padding: 20, height: 320 }}>
              <Line
                data={(currentCategoryData as any).trendData}
                xField="year"
                yField="revenue"
                seriesField="type"
                color="#7c3aed"
                smooth
                areaStyle={{ fill: 'rgba(124, 58, 237, 0.1)' }}
                point={{ size: 4, shape: 'circle' }}
                yAxis={{ label: { formatter: (v: string) => `${v}` } }}
                legend={{ position: 'top' }}
              />
            </div>
          </div>
        </Col>
        <Col span={12}>
          <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e5e7eb' }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>收入结构占比</h3>
            </div>
            <div style={{ padding: 20, height: 320 }}>
              <Pie
                data={(currentCategoryData as any).structureData}
                angleField="value"
                colorField="type"
                radius={0.8}
                innerRadius={0.6}
                color={['#1b4593', '#ea580c', '#0891b2']}
                label={{ type: 'inner', content: '{percentage}', style: { fill: '#fff' } }}
                legend={{ position: 'right' }}
                statistic={{
                  title: { content: '总收入', style: { fontSize: '14px' } },
                  content: { content: '8,363亿', style: { fontSize: '20px', fontWeight: 600 } },
                }}
              />
            </div>
          </div>
        </Col>
      </Row>

      {/* 数据表格 */}
      <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>经营成果明细</h3>
          <Button size="small" type="link">查看历史</Button>
        </div>
        <Table
          dataSource={(currentCategoryData as any).detailData}
          rowKey="name"
          size="small"
          pagination={false}
          columns={[
            { title: '指标名称', dataIndex: 'name', key: 'name' },
            { title: '2024年报', dataIndex: 'current', key: 'current', render: (v: number) => <span style={{ fontFamily: 'monospace' }}>{v?.toLocaleString()}</span> },
            { title: '2023年报', dataIndex: 'lastYear', key: 'lastYear', render: (v: number) => <span style={{ fontFamily: 'monospace' }}>{v?.toLocaleString()}</span> },
            { title: '同比', dataIndex: 'yoy', key: 'yoy', render: (v: number) => <span style={{ color: v >= 0 ? '#52c41a' : '#ff4d4f' }}>{v >= 0 ? '↑' : '↓'} {Math.abs(v)}%</span> },
            { title: '2022年报', dataIndex: 'twoYearsAgo', key: 'twoYearsAgo', render: (v: number) => <span style={{ fontFamily: 'monospace' }}>{v?.toLocaleString()}</span> },
            { title: '趋势', key: 'trend', render: (_: any, record: any) => <span style={{ color: record.yoy >= 0 ? '#ff4d4f' : '#52c41a' }}>{record.yoy >= 0 ? '↗' : '↘'}</span> },
          ]}
        />
      </div>
    </div>
  )

  // 资产负债页
  const renderBalancePage = () => (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {(currentCategoryData as any).kpis.map((kpi: any, idx: number) => (
          <Col span={8} key={idx}>
            <KPICard {...kpi} color={kpi.color || INDICATOR_CATEGORIES[1].indicators[idx].color} />
          </Col>
        ))}
      </Row>

      <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
        <Col span={12}>
          <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e5e7eb' }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>资产结构变化趋势</h3>
            </div>
            <div style={{ padding: 20, height: 320 }}>
              <Column
                data={(currentCategoryData as any).trendData}
                xField="year"
                yField="assets"
                color="#1b4593"
                label={{ position: 'top', style: { fill: '#1b4593' } }}
                yAxis={{ label: { formatter: (v: string) => `${(Number(v)/10000).toFixed(1)}万亿` } }}
              />
            </div>
          </div>
        </Col>
        <Col span={12}>
          <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e5e7eb' }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>资产负债结构</h3>
            </div>
            <div style={{ padding: 20, height: 320 }}>
              <Pie
                data={(currentCategoryData as any).structureData}
                angleField="value"
                colorField="type"
                radius={0.8}
                color={['#1b4593', '#7c3aed', '#0d9488', '#ea580c', '#6b7280']}
                label={{ type: 'inner', content: '{percentage}', style: { fill: '#fff' } }}
                legend={{ position: 'right' }}
              />
            </div>
          </div>
        </Col>
      </Row>

      {/* 摘要卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
        <Col span={8}>
          <div style={{ background: '#fff', borderRadius: 10, padding: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', borderTop: '3px solid #1b4593' }}>
            <h4 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>📊 资产要点</h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>总资产增长率 <span style={{ fontWeight: 500, color: '#1a2332' }}>+8.8%</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>贷款占比 <span style={{ fontWeight: 500, color: '#1a2332' }}>55.67%</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>投资占比 <span style={{ fontWeight: 500, color: '#1a2332' }}>28.34%</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', display: 'flex', justifyContent: 'space-between' }}>现金占比 <span style={{ fontWeight: 500, color: '#1a2332' }}>3.21%</span></li>
            </ul>
          </div>
        </Col>
        <Col span={8}>
          <div style={{ background: '#fff', borderRadius: 10, padding: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', borderTop: '3px solid #7c3aed' }}>
            <h4 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>💰 负债要点</h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>存款负债率 <span style={{ fontWeight: 500, color: '#1a2332' }}>75.95%</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>个人存款占比 <span style={{ fontWeight: 500, color: '#1a2332' }}>48.62%</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>公司存款占比 <span style={{ fontWeight: 500, color: '#1a2332' }}>46.38%</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', display: 'flex', justifyContent: 'space-between' }}>同业存放占比 <span style={{ fontWeight: 500, color: '#1a2332' }}>12.35%</span></li>
            </ul>
          </div>
        </Col>
        <Col span={8}>
          <div style={{ background: '#fff', borderRadius: 10, padding: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', borderTop: '3px solid #ea580c' }}>
            <h4 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>⚖️ 权益结构</h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>权益资产率 <span style={{ fontWeight: 500, color: '#1a2332' }}>9.07%</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>股本 <span style={{ fontWeight: 500, color: '#1a2332' }}>2,264.12亿</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>资本公积 <span style={{ fontWeight: 500, color: '#1a2332' }}>1,862.45亿</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', display: 'flex', justifyContent: 'space-between' }}>未分配利润 <span style={{ fontWeight: 500, color: '#1a2332' }}>12,456.78亿</span></li>
            </ul>
          </div>
        </Col>
      </Row>
    </div>
  )

  // 资本净额页
  const renderCapitalPage = () => (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {(currentCategoryData as any).kpis.map((kpi: any, idx: number) => (
          <Col span={6} key={idx}>
            <KPICard {...kpi} color={kpi.color || INDICATOR_CATEGORIES[2].indicators[idx].color} />
          </Col>
        ))}
      </Row>

      <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
        <Col span={12}>
          <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e5e7eb' }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>资本净额变化趋势</h3>
            </div>
            <div style={{ padding: 20, height: 320 }}>
              <Line
                data={[
                  ...(currentCategoryData as any).trendData.map((d: any) => ({ year: d.year, value: d.core, type: '核心一级资本净额' })),
                  ...(currentCategoryData as any).trendData.map((d: any) => ({ year: d.year, value: d.tier1, type: '一级资本净额' })),
                  ...(currentCategoryData as any).trendData.map((d: any) => ({ year: d.year, value: d.total, type: '总资本净额' })),
                ]}
                xField="year"
                yField="value"
                seriesField="type"
                color={['#1b4593', '#7c3aed', '#0d9488']}
                smooth
                areaStyle={{ fill: 'rgba(27, 69, 147, 0.1)' }}
                yAxis={{ label: { formatter: (v: string) => `${v}` } }}
                legend={{ position: 'top' }}
              />
            </div>
          </div>
        </Col>
        <Col span={12}>
          <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e5e7eb' }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>风险加权资产结构</h3>
            </div>
            <div style={{ padding: 20, height: 320 }}>
              <Pie
                data={(currentCategoryData as any).rwaData}
                angleField="value"
                colorField="type"
                radius={0.8}
                innerRadius={0.6}
                color={['#1b4593', '#ea580c', '#0891b2']}
                label={{ type: 'inner', content: '{percentage}', style: { fill: '#fff' } }}
                legend={{ position: 'right' }}
              />
            </div>
          </div>
        </Col>
      </Row>
    </div>
  )

  // 每股指标页
  const renderPerSharePage = () => (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {(currentCategoryData as any).kpis.map((kpi: any, idx: number) => (
          <Col span={6} key={idx}>
            <KPICard {...kpi} color={kpi.color || INDICATOR_CATEGORIES[3].indicators[idx].color} />
          </Col>
        ))}
      </Row>

      <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', marginBottom: 20 }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #e5e7eb' }}>
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>每股指标历史趋势</h3>
        </div>
        <div style={{ padding: 20, height: 400 }}>
          <Line
            data={[
              ...(currentCategoryData as any).trendData.map((d: any) => ({ year: d.year, value: d.bps, type: '每股净资产(元)' })),
              ...(currentCategoryData as any).trendData.map((d: any) => ({ year: d.year, value: d.eps, type: '每股收益(元)' })),
            ]}
            xField="year"
            yField="value"
            seriesField="type"
            color={['#1b4593', '#ea580c']}
            smooth
            yAxis={{ label: { formatter: (v: string) => `${v}元` } }}
            legend={{ position: 'top' }}
          />
        </div>
      </div>
    </div>
  )

  // 盈利能力页
  const renderProfitabilityPage = () => (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {(currentCategoryData as any).kpis.map((kpi: any, idx: number) => (
          <Col span={8} key={idx}>
            <KPICard {...kpi} color={kpi.color || INDICATOR_CATEGORIES[4].indicators[idx].color} />
          </Col>
        ))}
      </Row>

      <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
        <Col span={12}>
          <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e5e7eb' }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>盈利能力雷达图</h3>
            </div>
            <div style={{ padding: 20, height: 320, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <Radar
                data={(currentCategoryData as any).radarData}
                xField="indicator"
                yField="bank"
                seriesField="bank"
                color={['#1b4593', '#6b7280']}
                legend={{ position: 'top' }}
                areaStyle={{ fill: 'rgba(27, 69, 147, 0.2)' }}
              />
            </div>
          </div>
        </Col>
        <Col span={12}>
          <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e5e7eb' }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>ROE变化趋势</h3>
            </div>
            <div style={{ padding: 20, height: 320 }}>
              <Line
                data={(currentCategoryData as any).roeTrendData}
                xField="year"
                yField="roe"
                color="#7c3aed"
                smooth
                areaStyle={{ fill: 'rgba(124, 58, 237, 0.1)' }}
                yAxis={{ min: 10, max: 13, label: { formatter: (v: string) => `${v}%` } }}
              />
            </div>
          </div>
        </Col>
      </Row>

      <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #e5e7eb' }}>
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>盈利能力同业对比</h3>
        </div>
        <div style={{ padding: 20, height: 320 }}>
          <Bar
            data={[
              ...(currentCategoryData as any).compareData.map((d: any) => ({ bank: d.bank, value: d.roa, type: 'ROA' })),
              ...(currentCategoryData as any).compareData.map((d: any) => ({ bank: d.bank, value: d.roe, type: 'ROE' })),
            ]}
            xField="value"
            yField="bank"
            seriesField="type"
            color={['#1b4593', '#ea580c']}
            legend={{ position: 'top' }}
            yAxis={{ label: { formatter: (v: string) => v }}
            }
          />
        </div>
      </div>
    </div>
  )

  // 资产质量页
  const renderAssetQualityPage = () => (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {(currentCategoryData as any).kpis.map((kpi: any, idx: number) => (
          <Col span={8} key={idx}>
            <KPICard {...kpi} color={kpi.color || INDICATOR_CATEGORIES[5].indicators[idx].color} />
          </Col>
        ))}
      </Row>

      {/* 仪表盘风格展示 */}
      <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', padding: 30, marginBottom: 20, display: 'flex', justifyContent: 'space-around', flexWrap: 'wrap', gap: 40 }}>
        <div style={{ textAlign: 'center' }}>
          <Progress type="circle" percent={1.36} size={120} strokeColor="#dc2626" format={p => `${p}%`} />
          <div style={{ marginTop: 8, fontSize: 13, color: '#6b7280' }}>不良贷款率</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <Progress type="circle" percent={211.53} size={120} strokeColor="#059669" format={p => `${p}%`} />
          <div style={{ marginTop: 8, fontSize: 13, color: '#6b7280' }}>拨备覆盖率</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <Progress type="circle" percent={2.88} size={120} strokeColor="#1b4593" format={p => `${p}%`} />
          <div style={{ marginTop: 8, fontSize: 13, color: '#6b7280' }}>贷款拨备率</div>
        </div>
      </div>

      <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
        <Col span={12}>
          <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e5e7eb' }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>不良贷款率趋势</h3>
            </div>
            <div style={{ padding: 20, height: 320 }}>
              <Line
                data={[
                  ...(currentCategoryData as any).trendData.map((d: any) => ({ year: d.year, value: d.npl, type: '不良贷款率' })),
                ]}
                xField="year"
                yField="value"
                color="#dc2626"
                smooth
                areaStyle={{ fill: 'rgba(220, 38, 38, 0.1)' }}
                yAxis={{ min: 1, max: 1.6, label: { formatter: (v: string) => `${v}%` } }}
              />
            </div>
          </div>
        </Col>
        <Col span={12}>
          <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e5e7eb' }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>资产质量同业对比</h3>
            </div>
            <div style={{ padding: 20, height: 320 }}>
              <Bar
                data={(currentCategoryData as any).compareData}
                xField="npl"
                yField="bank"
                color="#dc2626"
                legend={{ position: 'top' }}
                yAxis={{ label: { formatter: (v: string) => v }}
                }
              />
            </div>
          </div>
        </Col>
      </Row>
    </div>
  )

  // 资本充足率页
  const renderCapitalAdequacyPage = () => (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {(currentCategoryData as any).kpis.map((kpi: any, idx: number) => (
          <Col span={8} key={idx}>
            <KPICard {...kpi} color={kpi.color || INDICATOR_CATEGORIES[6].indicators[idx].color} />
          </Col>
        ))}
      </Row>

      <Row gutter={[20, 20]} style={{ marginBottom: 20 }}>
        <Col span={12}>
          <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e5e7eb' }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>资本充足率趋势</h3>
            </div>
            <div style={{ padding: 20, height: 320 }}>
              <Line
                data={[
                  ...(currentCategoryData as any).trendData.map((d: any) => ({ year: d.year, value: d.core, type: '核心一级资本充足率' })),
                  ...(currentCategoryData as any).trendData.map((d: any) => ({ year: d.year, value: d.tier1, type: '一级资本充足率' })),
                  ...(currentCategoryData as any).trendData.map((d: any) => ({ year: d.year, value: d.total, type: '资本充足率' })),
                ]}
                xField="year"
                yField="value"
                seriesField="type"
                color={['#1b4593', '#7c3aed', '#0d9488']}
                smooth
                areaStyle={{ fill: 'rgba(27, 69, 147, 0.1)' }}
                yAxis={{ min: 8, max: 18, label: { formatter: (v: string) => `${v}%` } }}
                legend={{ position: 'top' }}
              />
            </div>
          </div>
        </Col>
        <Col span={12}>
          <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e5e7eb' }}>
              <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>资本充足率同业对比</h3>
            </div>
            <div style={{ padding: 20, height: 320 }}>
              <Bar
                data={(currentCategoryData as any).compareData}
                xField="car"
                yField="bank"
                color="#1b4593"
                legend={{ position: 'top' }}
                yAxis={{ label: { formatter: (v: string) => v }}
                }
              />
            </div>
          </div>
        </Col>
      </Row>

      {/* 摘要卡片 */}
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <div style={{ background: '#fff', borderRadius: 10, padding: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', borderTop: '3px solid #1b4593' }}>
            <h4 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>🎯 监管要求对照</h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>核心一级资本充足率 <span style={{ fontWeight: 500, color: '#1a2332' }}>10.87%</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>一级资本充足率 <span style={{ fontWeight: 500, color: '#1a2332' }}>11.95%</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>资本充足率 <span style={{ fontWeight: 500, color: '#1a2332' }}>14.11%</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', display: 'flex', justifyContent: 'space-between' }}>杠杆率 <span style={{ fontWeight: 500, color: '#1a2332' }}>8.56%</span></li>
            </ul>
          </div>
        </Col>
        <Col span={8}>
          <div style={{ background: '#fff', borderRadius: 10, padding: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', borderTop: '3px solid #7c3aed' }}>
            <h4 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>📊 资本缓冲</h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>储备资本 <span style={{ fontWeight: 500, color: '#1a2332' }}>2.50%</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>逆周期资本 <span style={{ fontWeight: 500, color: '#1a2332' }}>0.00%</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>附加资本 <span style={{ fontWeight: 500, color: '#1a2332' }}>0.00%</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', display: 'flex', justifyContent: 'space-between' }}>总缓冲资本 <span style={{ fontWeight: 500, color: '#1a2332' }}>2.50%</span></li>
            </ul>
          </div>
        </Col>
        <Col span={8}>
          <div style={{ background: '#fff', borderRadius: 10, padding: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', borderTop: '3px solid #ea580c' }}>
            <h4 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>⚖️ 杠杆率</h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>杠杆率 <span style={{ fontWeight: 500, color: '#1a2332' }}>8.56%</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>最低要求 <span style={{ fontWeight: 500, color: '#1a2332' }}>4.00%</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', borderBottom: '1px dashed #e5e7eb', display: 'flex', justifyContent: 'space-between' }}>超额资本 <span style={{ fontWeight: 500, color: '#1a2332' }}>4.56%</span></li>
              <li style={{ padding: '6px 0', fontSize: 13, color: '#6b7280', display: 'flex', justifyContent: 'space-between' }}>安全边际 <span style={{ fontWeight: 500, color: '#1a2332' }}>114%</span></li>
            </ul>
          </div>
        </Col>
      </Row>
    </div>
  )

  // 渲染当前分类页面
  const renderCurrentPage = () => {
    switch (activeCategory) {
      case 'profit': return renderProfitPage()
      case 'balance': return renderBalancePage()
      case 'capital': return renderCapitalPage()
      case 'perShare': return renderPerSharePage()
      case 'profitability': return renderProfitabilityPage()
      case 'assetQuality': return renderAssetQualityPage()
      case 'capitalAdequacy': return renderCapitalAdequacyPage()
      default: return renderProfitPage()
    }
  }

  return (
    <div style={{ background: '#f0f4f8', minHeight: '100vh', padding: 20 }}>
      {/* 页面头部 */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>📊 保险经营指标仪表盘</h1>
        <p style={{ color: '#6b7280', fontSize: 14, margin: 0 }}>7大类指标深度分析 - 按指标分类查看银行核心经营数据</p>
      </div>

      {/* 分类Tab导航 */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
        {INDICATOR_CATEGORIES.map(cat => (
          <div
            key={cat.key}
            onClick={() => setActiveCategory(cat.key)}
            style={{
              padding: '10px 20px',
              background: activeCategory === cat.key ? '#1b4593' : '#fff',
              border: `1px solid ${activeCategory === cat.key ? '#1b4593' : '#e5e7eb'}`,
              borderRadius: 8,
              fontSize: 13,
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              color: activeCategory === cat.key ? '#fff' : '#1a2332',
              transition: 'all 0.15s',
            }}
          >
            <span>{cat.icon}</span>
            <span>{cat.name}</span>
          </div>
        ))}
      </div>

      {/* 筛选条件栏 */}
      <div style={{ background: '#fff', padding: '16px 20px', borderRadius: 10, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13, color: '#6b7280' }}>银行:</span>
          <BankSelect
            value={selectedBankCode}
            onChange={(value) => setSelectedBankCode(value || '')}
            placeholder="请选择保险机构"
            style={{ width: 220 }}
          />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13, color: '#6b7280' }}>报告期:</span>
          <Select
            value={selectedYear}
            onChange={setSelectedYear}
            style={{ width: 140 }}
            options={YEAR_OPTIONS}
          />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13, color: '#6b7280' }}>对比:</span>
          <Select
            defaultValue="none"
            style={{ width: 140 }}
            options={[
              { value: 'none', label: '无对比' },
              { value: 'yoy', label: '与上年同期' },
              { value: 'industry', label: '与行业均值' },
            ]}
          />
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <Button type="primary" style={{ background: '#1b4593' }}>查询</Button>
          <Button icon={<ExportOutlined />}>导出</Button>
        </div>
      </div>

      {/* 主内容区域 */}
      <Spin spinning={loading}>
        {renderCurrentPage()}
      </Spin>
    </div>
  )
}
