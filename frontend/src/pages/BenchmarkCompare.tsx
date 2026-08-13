import { useEffect, useState } from 'react'
import { Row, Col, Card, Select, Table, Statistic, Spin, Empty, Tag, Button, message, Space, Upload, Input, Tabs } from 'antd'
import { SafetyOutlined, BarChartOutlined, UploadOutlined, InboxOutlined } from '@ant-design/icons'
import type { UploadProps } from 'antd'
import { benchmarkApi, indicatorsApi, banksApi } from '../api'

const { Dragger } = Upload

const typeMap: Record<string, string> = { GROUP: '保险集团', LIFE: '寿险', PNC: '财险', REINSURANCE: '再保险', HEALTH: '健康险', PENSION: '养老险', POLICY: '政策性' }
const rankColors = ['#faad14', '#bfbfbf', '#d48806', '#1677ff', '#1677ff']

function RankingBar({ ranking, unit }: { ranking: any[], unit: string }) {
  if (!ranking.length) return null
  const maxVal = Math.max(...ranking.map(r => Math.abs(r.value || 0)), 1)
  return (
    <div style={{ padding: '8px 0' }}>
      {ranking.slice(0, 15).map((r, i) => (
        <div key={r.institution_id} style={{ display: 'flex', alignItems: 'center', marginBottom: 6, fontSize: 12 }}>
          <span style={{ width: 50, textAlign: 'right', fontWeight: 600, color: rankColors[i] || '#1677ff', marginRight: 8 }}>
            #{r.rank}
          </span>
          <span style={{ width: 90, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginRight: 8 }}>
            {r.bank_name}
          </span>
          <div style={{ flex: 1, height: 18, background: '#f0f0f0', borderRadius: 4, position: 'relative', overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: 4,
              background: `linear-gradient(90deg, ${rankColors[i] || '#1677ff'}, ${rankColors[i] || '#1677ff'}88)`,
              width: `${Math.max((Math.abs(r.value || 0) / maxVal) * 100, 1)}%`,
              transition: 'width 0.5s',
            }} />
          </div>
          <span style={{ width: 80, textAlign: 'right', fontWeight: 600, marginLeft: 8, fontSize: 11 }}>
            {r.value != null ? `${r.value}${unit}` : '—'}
          </span>
        </div>
      ))}
    </div>
  )
}

function OwnReportTab() {
  const [file, setFile] = useState<File | null>(null)
  const [reportYear, setReportYear] = useState(2025)
  const [bankType, setBankType] = useState('LIFE')
  const [bankName, setBankName] = useState('本机构')
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.pdf,.html,.PDF,.HTML',
    beforeUpload: (f) => { setFile(f); return false },
    onRemove: () => setFile(null),
    maxCount: 1,
  }

  const handleUpload = async () => {
    if (!file) { message.warning('请选择年报文件'); return }
    setUploading(true)
    try {
      const res: any = await benchmarkApi.uploadOwnReport(file, reportYear, bankType, bankName)
      setResult(res.data || res)
      message.success(res.message || '提取完成')
    } catch (e: any) { message.error('上传失败: ' + (e.message || e)) }
    finally { setUploading(false) }
  }

  const typeMap: Record<string, string> = { GROUP: '保险集团', LIFE: '寿险公司', PNC: '财险', REINSURANCE: '再保险', HEALTH: '健康险', PENSION: '养老险', POLICY: '政策性' }

  return (
    <div>
      <Card title="📤 上传本机构年报" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={6}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 12 }}>本机构名称</label>
            <Input value={bankName} onChange={e => setBankName(e.target.value)} placeholder="本机构" />
          </Col>
          <Col xs={12} sm={4}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 12 }}>年报年份</label>
            <Select value={reportYear} onChange={setReportYear} style={{ width: '100%' }}
              options={[2025, 2024, 2023, 2022, 2021].map(y => ({ label: `${y}年`, value: y }))} />
          </Col>
          <Col xs={12} sm={5}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 12 }}>机构类型</label>
            <Select value={bankType} onChange={setBankType} style={{ width: '100%' }}
              options={Object.entries(typeMap).map(([v, l]) => ({ label: l, value: v }))} />
          </Col>
          <Col xs={24}>
            <Dragger {...uploadProps}>
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p className="ant-upload-text">点击或拖拽年报文件到此处</p>
              <p className="ant-upload-hint">支持 PDF / HTML 格式的年报文件</p>
            </Dragger>
          </Col>
          <Col xs={24}>
            <Button type="primary" icon={<UploadOutlined />} loading={uploading} onClick={handleUpload} size="large" block disabled={!file}>
              上传并开始对比分析
            </Button>
          </Col>
        </Row>
      </Card>

      {result && (
        <Card title={`📊 ${bankName} ${reportYear}年报 对比分析 (提取${result.indicators_found}个指标)`}>
          <Table
            size="small"
            pagination={false}
            rowKey="indicator_code"
            dataSource={result.comparison || []}
            columns={[
              { title: '指标', dataIndex: 'indicator_name', width: 160, fixed: 'left' as const },
              { title: '本机构', dataIndex: 'own_value', width: 100, align: 'right' as const,
                render: (v: any, r: any) => <b>{v}{r.unit === '%' ? '%' : ''}</b> },
              { title: '系统均值', dataIndex: 'sys_avg', width: 100, align: 'right' as const,
                render: (v: any, r: any) => v ? `${v}${r.unit === '%' ? '%' : ''}` : '—' },
              { title: 'vs均值', dataIndex: 'vs_avg_pct', width: 80, align: 'right' as const,
                render: (v: any) => v != null ? <span style={{ color: v >= 0 ? '#52c41a' : '#ff4d4f', fontWeight: 600 }}>{v > 0 ? '+' : ''}{v}%</span> : '—' },
              { title: `同类型均值(${typeMap[bankType] || bankType})`, dataIndex: 'type_avg', width: 130, align: 'right' as const,
                render: (v: any, r: any) => v ? `${v}${r.unit === '%' ? '%' : ''}` : '—' },
              { title: '先进对标(Top3)', dataIndex: 'top3', width: 200,
                render: (v: any[]) => v ? v.map((t: any, i: number) => (
                  <div key={i} style={{ fontSize: 11 }}>
                    <Tag color={i === 0 ? 'gold' : i === 1 ? 'default' : 'orange'}>{i + 1}</Tag>
                    {t.name}: <b>{t.value}</b>
                  </div>
                )) : '—' },
            ]}
            scroll={{ x: 800 }}
          />
        </Card>
      )}
    </div>
  )
}

export default function BenchmarkCompare() {
  const [tab, setTab] = useState('peer')
  const [indicators, setIndicators] = useState<any[]>([])
  const [banks, setBanks] = useState<any[]>([])
  const [indicatorCode, setIndicatorCode] = useState('PROFIT_REVENUE')
  const [year, setYear] = useState(2025)
  const [bankType, setBankType] = useState<string | undefined>(undefined)
  const [period, setPeriod] = useState('FY')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [ranking, setRanking] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [indicatorInfo, setIndicatorInfo] = useState<any>(null)
  const [years, setYears] = useState<number[]>([])
  const [history, setHistory] = useState<any[]>([])

  useEffect(() => { loadIndicators(); loadBanks() }, [])
  useEffect(() => { loadCompare() }, [indicatorCode, year, bankType, period])
  useEffect(() => { if (indicatorCode) loadYears() }, [indicatorCode, period])
  useEffect(() => { loadHistory() }, [])

  const loadIndicators = async () => {
    try {
      const res: any = await indicatorsApi.getCategories()
      const all: any[] = []
      res.data?.forEach((cat: any) => cat.indicators?.forEach((ind: any) => all.push(ind)))
      setIndicators(all)
    } catch (e: any) { message.error('加载指标失败: ' + (e.message || e)) }
  }

  const loadBanks = async () => {
    try {
      const res: any = await banksApi.getList({ page_size: 200 })
      setBanks(res.data || [])
    } catch (e: any) {}
  }

  const loadYears = async () => {
    try {
      const res: any = await benchmarkApi.getAvailableYears(indicatorCode, period)
      setYears(res.data || [])
    } catch (e: any) {}
  }

  const loadHistory = async () => {
    try {
      const res: any = await benchmarkApi.getHistory({ page_size: 10 })
      setHistory(res.data?.items || [])
    } catch (e: any) {}
  }

  const loadCompare = async () => {
    setLoading(true)
    try {
      const params: any = { indicator_code: indicatorCode, report_year: year, report_period: period, top_n: 47 }
      if (bankType) params.bank_type = bankType
      const res: any = await benchmarkApi.compare(params)
      setRanking(res.data?.ranking || [])
      setStats(res.data?.stats || null)
      setIndicatorInfo(res.data?.indicator || null)
    } catch (e: any) {
      message.error('加载对比数据失败: ' + (e.message || e))
      setRanking([]); setStats(null)
    } finally { setLoading(false) }
  }

  const handleSave = async () => {
    if (!ranking.length) return
    setSaving(true)
    try {
      const ids = ranking.map(r => r.institution_id).join(',')
      await benchmarkApi.saveCompare(indicatorCode, year, ids, period)
      message.success('对比记录已保存')
      loadHistory()
    } catch (e: any) { message.error((e.message || e)) }
    finally { setSaving(false) }
  }

  return (
    <div>
      <div className="page-header">
        <h2><BarChartOutlined /> 同业对比分析</h2>
        <p>跨机构、跨指标、跨年度的经营数据对标</p>
      </div>

      <Tabs activeKey={tab} onChange={setTab} size="large"
        items={[
          { key: 'peer', label: '🏦 同业对标', children: (
            <div>

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} sm={5}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 12 }}>对比指标</label>
            <Select value={indicatorCode} onChange={setIndicatorCode} style={{ width: '100%' }} showSearch
              filterOption={(input, option: any) =>
                (option?.label || '').toLowerCase().includes(input.toLowerCase())}
              options={indicators.map(ind => ({
                label: `${ind.indicator_name} (${ind.indicator_code})`, value: ind.indicator_code,
              }))} />
          </Col>
          <Col xs={12} sm={3}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 12 }}>数据年</label>
            <Select value={year} onChange={setYear} style={{ width: '100%' }}
              options={(years.length ? years : [2025, 2024, 2023, 2022]).map(y => ({ label: `${y}年`, value: y }))} />
          </Col>
          <Col xs={12} sm={3}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 12 }}>报告期</label>
            <Select value={period} onChange={setPeriod} style={{ width: '100%' }}
              options={[{ label: '年报', value: 'FY' }, { label: '半年报', value: 'H1' }, { label: '三季报', value: 'Q3' }]} />
          </Col>
          <Col xs={12} sm={3}>
            <label style={{ display: 'block', marginBottom: 4, fontWeight: 500, fontSize: 12 }}>机构类型</label>
            <Select value={bankType} onChange={setBankType} style={{ width: '100%' }} allowClear placeholder="全部"
              options={[
                { label: '保险集团', value: 'GROUP' }, { label: '寿险公司', value: 'LIFE' },
                { label: '财险', value: 'PNC' }, { label: '再保险', value: 'REINSURANCE' },
                { label: '健康险', value: 'HEALTH' }, { label: '养老险', value: 'PENSION' }, { label: '政策性', value: 'POLICY' }, { label: '政策性', value: 'POLICY' },
              ]} />
          </Col>
        </Row>
      </Card>

      <Spin spinning={loading}>
        {stats && (
          <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
            <Col xs={12} sm={4}><Card size="small"><Statistic title="最高" value={stats.max} suffix={indicatorInfo?.unit} valueStyle={{ color: '#52c41a' }} /></Card></Col>
            <Col xs={12} sm={4}><Card size="small"><Statistic title="最低" value={stats.min} suffix={indicatorInfo?.unit} valueStyle={{ color: '#ff4d4f' }} /></Card></Col>
            <Col xs={12} sm={4}><Card size="small"><Statistic title="平均" value={stats.avg} suffix={indicatorInfo?.unit} /></Card></Col>
            <Col xs={12} sm={4}><Card size="small"><Statistic title="中位数" value={stats.median} suffix={indicatorInfo?.unit} /></Card></Col>
            <Col xs={12} sm={4}><Card size="small"><Statistic title="P25" value={stats.p25} suffix={indicatorInfo?.unit} /></Card></Col>
            <Col xs={12} sm={4}><Card size="small"><Statistic title="P75" value={stats.p75} suffix={indicatorInfo?.unit} /></Card></Col>
          </Row>
        )}

        <Row gutter={16}>
          <Col xs={24} lg={14}>
            <Card title={`${indicatorInfo?.name || indicatorCode} 排名 (${year}年${period === 'FY' ? '年报' : period})`}
              extra={<Space>
                <Button icon={<SafetyOutlined />} loading={saving} onClick={handleSave} size="small" disabled={!ranking.length}>保存对比</Button>
              </Space>}>
              {ranking.length > 0 ? (
                <Table dataSource={ranking.map(r => ({ ...r, key: r.institution_id, unit: indicatorInfo?.unit }))}
                  columns={[
                    { title: '排名', dataIndex: 'rank', width: 60, render: (v: number) => (
                      <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                        width: 24, height: 24, borderRadius: 4, fontSize: 12, fontWeight: 700,
                        color: '#fff', background: rankColors[v - 1] || '#1677ff' }}>{v}</span>) },
                    { title: '机构', dataIndex: 'bank_name', width: 120 },
                    { title: '类型', dataIndex: 'bank_type', width: 80, render: (v: string) => <Tag>{typeMap[v] || v}</Tag> },
                    { title: `指标值 (${indicatorInfo?.unit || ''})`, dataIndex: 'value', width: 120,
                      render: (v: number | null) => v != null ? <span style={{ fontWeight: 600 }}>{v}</span> : <span style={{ color: '#bfbfbf' }}>—</span> },
                  ]}
                  pagination={false} size="small" scroll={{ y: 500 }} />
              ) : (
                <Empty description="暂无对比数据，请先在指标库中导入数据" />
              )}
            </Card>
          </Col>
          <Col xs={24} lg={10}>
            <Card title="📊 排名分布图" style={{ marginBottom: 16 }}>
              <RankingBar ranking={ranking.slice(0, 15)} unit={indicatorInfo?.unit || ''} />
            </Card>
            {history.length > 0 && (
              <Card title="📋 历史对比记录" size="small">
                {history.slice(0, 5).map((h: any) => (
                  <div key={h.id} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0', fontSize: 12 }}>
                    <span style={{ color: '#8c8c8c', marginRight: 8 }}>{h.report_year}年</span>
                    <span>{h.report_period === 'FY' ? '年报' : h.report_period}</span>
                    <span style={{ color: '#8c8c8c', margin: '0 8px' }}>·</span>
                    <span>{h.result_json?.ranking?.length || 0}家保险机构</span>
                    <span style={{ color: '#8c8c8c', marginLeft: 8 }}>{h.created_at?.slice(0, 10)}</span>
                  </div>
                ))}
              </Card>
            )}
          </Col>
        </Row>
      </Spin>
          </div>
          )},
          { key: 'own', label: '📤 本机构对比', children: <OwnReportTab /> },
        ]}
      />
    </div>
  )
}
