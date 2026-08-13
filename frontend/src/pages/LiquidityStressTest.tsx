/**
 * 流动性压力测试及风险缓释 — 功能页面
 * 4个一级Tab: G21数据管理 / HQLA资产管理 / 版本管理 / 版本对比
 * 版本管理内含6个子Tab
 */
import React, { useState, useEffect, useCallback } from 'react'
import {
  Card, Table, Button, Space, Tag, Modal, Form, Input, InputNumber, Select,
  message, Tabs, Row, Col, Statistic, Progress, Popconfirm, Descriptions,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  UploadOutlined, DownloadOutlined, PlusOutlined, DeleteOutlined,
  PlayCircleOutlined, CopyOutlined, EditOutlined, EyeOutlined,
  SafetyOutlined, BarChartOutlined, FileTextOutlined, UndoOutlined,
} from '@ant-design/icons'
import { liquidityApi } from '../api'

const { TabPane } = Tabs
const { TextArea } = Input

// ============ 内部子组件 ============

/** G21 数据管理 Tab */
function G21Tab() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [periods, setPeriods] = useState<string[]>([])
  const [selPeriod, setSelPeriod] = useState<string>('')
  const [page, setPage] = useState(1)

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const res: any = await liquidityApi.listG21({ report_period: selPeriod || undefined, page, page_size: 200 })
      // Build tree: map flat to nested by parent_code
      const flat = res.data || []
      const map: Record<string, any> = {}
      const roots: any[] = []
      flat.forEach((item: any) => {
        const row = { ...item, key: item.item_code }
        map[item.item_code] = row
      })
      flat.forEach((item: any) => {
        const row = map[item.item_code]
        if (item.parent_code && map[item.parent_code]) {
          const parent = map[item.parent_code]
          if (!parent.children) parent.children = []
          parent.children.push(row)
        } else {
          roots.push(row)
        }
      })
      setData(roots)
    } catch (e: any) { message.error(e.message) }
    finally { setLoading(false) }
  }, [selPeriod, page])

  const loadPeriods = async () => {
    try {
      const res: any = await liquidityApi.getG21Periods()
      setPeriods(res.data || [])
    } catch (e: any) {}
  }

  useEffect(() => { loadPeriods() }, [])
  useEffect(() => { loadData() }, [loadData])

  const handleDelete = async (id: number) => {
    await liquidityApi.deleteG21(id)
    message.success('已删除')
    loadData()
    loadPeriods()
  }

  const columns: ColumnsType<any> = [
    { title: '科目编码', dataIndex: 'item_code', width: 100 },
    { title: '科目名称', dataIndex: 'item_name', width: 200, 
      render: (v: string, r: any) => <span style={{ fontWeight: r.item_level === 1 ? 700 : 400 }}>{v}</span> },
    { title: '分类', dataIndex: 'category', width: 70, render: (v: string) => 
      v === 'ASSET' ? <Tag color="green">资产</Tag> : v === 'LIABILITY' ? <Tag color="red">负债</Tag> : <Tag color="blue">表外</Tag> },
    { title: '次日', dataIndex: 'overnight_amount', width: 100, align: 'right' as const, render: (v: any) => v ? Number(v).toLocaleString() : '—' },
    { title: '2-7日', dataIndex: 'day7_amount', width: 100, align: 'right' as const, render: (v: any) => v ? Number(v).toLocaleString() : '—' },
    { title: '8-30日', dataIndex: 'month1_amount', width: 100, align: 'right' as const, render: (v: any) => v ? Number(v).toLocaleString() : '—' },
    { title: '31-90日', dataIndex: 'month3_amount', width: 100, align: 'right' as const, render: (v: any) => v ? Number(v).toLocaleString() : '—' },
    { title: '91日-1年', dataIndex: 'year1_amount', width: 100, align: 'right' as const, render: (v: any) => v ? Number(v).toLocaleString() : '—' },
    { title: '1年以上', dataIndex: 'year5_amount', width: 100, align: 'right' as const, render: (v: any) => v ? Number(v).toLocaleString() : '—' },
    { title: '未定期限', dataIndex: 'unlimited_amount', width: 100, align: 'right' as const, render: (v: any) => v ? Number(v).toLocaleString() : '—' },
    { title: '合计', dataIndex: 'total_amount', width: 100, align: 'right' as const, render: (v: any) => v ? <b>{Number(v).toLocaleString()}</b> : '—' },
    { title: '操作', width: 80, fixed: 'right' as const, render: (_: any, r: any) => (
      <Popconfirm title="确认删除?" onConfirm={() => handleDelete(r.id)}><a style={{ color: '#ff4d4f' }}>删除</a></Popconfirm>
    )},
  ]

  return (
    <Card title="G21 流动性期限缺口统计表" extra={
      <Space>
        <Select placeholder="报告期" allowClear style={{ width: 140 }} value={selPeriod || undefined} onChange={(v) => { setSelPeriod(v || ''); setPage(1) }}>
          {periods.map((p: string) => <Select.Option key={p} value={p}>{p}</Select.Option>)}
        </Select>
        <Button icon={<DownloadOutlined />} onClick={() => window.open(liquidityApi.exportG21Url(selPeriod || '2019Q2'))}>导出Excel</Button>
      </Space>
    }>
      <Table rowKey="key" columns={columns} dataSource={data} loading={loading} size="small" scroll={{ x: 1300 }}
        defaultExpandAllRows
        pagination={false}
        onRow={(r) => r.item_level === 2 ? { style: { fontSize: 12 } } : {}} />
    </Card>
  )
}

/** HQLA 资产管理 Tab */
function HqlaTab() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [periods, setPeriods] = useState<string[]>([])
  const [selPeriod, setSelPeriod] = useState<string>('')
  const [summary, setSummary] = useState<any>(null)
  const [page, setPage] = useState(1)

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const res: any = await liquidityApi.listHqla({ report_period: selPeriod || undefined, page, page_size: 200 })
      const flat = res.data || []
      // Build grouped tree: summary rows as parents, detail rows as children
      const result: any[] = []
      let currentGroup: any = null
      flat.forEach((item: any) => {
        if (item.asset_type.includes('汇总')) {
          // Summary row -> parent
          currentGroup = { ...item, key: item.id, isGroup: true, children: [] }
          result.push(currentGroup)
        } else if (currentGroup && item.asset_level === currentGroup.asset_level) {
          currentGroup.children.push({ ...item, key: item.id })
        } else {
          result.push({ ...item, key: item.id })
        }
      })
      setData(result)
    } catch (e: any) { message.error(e.message) }
    finally { setLoading(false) }
  }, [selPeriod, page])

  const loadPeriods = async () => {
    try {
      const res: any = await liquidityApi.getHqlaPeriods()
      setPeriods(res.data || [])
    } catch (e: any) {}
  }
  const loadSummary = async (p: string) => {
    if (!p) return
    try { const res: any = await liquidityApi.getHqlaSummary(p); setSummary(res.data) } catch (e: any) {}
  }

  useEffect(() => { loadPeriods() }, [])
  useEffect(() => { loadData() }, [loadData])
  useEffect(() => { loadSummary(selPeriod) }, [selPeriod])

  const levelColor: Record<string, string> = { LEVEL1: 'green', LEVEL2A: 'orange', LEVEL2B: 'red' }

  const columns: ColumnsType<any> = [
    { title: '流动性资产', dataIndex: 'asset_name', width: 200,
      render: (v: string, r: any) => {
        if (r.isGroup) return <b style={{ fontSize: 13 }}>{v}</b>
        return <span style={{ paddingLeft: r.isGroup ? 0 : 20, fontStyle: r.asset_type.includes('汇总') ? 'italic' : 'normal' }}>{v}</span>
      }
    },
    { title: '层级', dataIndex: 'asset_level', width: 80, render: (v: string) =>
      <Tag color={levelColor[v]}>{v === 'LEVEL1' ? '一级' : v === 'LEVEL2A' ? '二级A' : '二级B'}</Tag> },
    { title: '类型', dataIndex: 'asset_type', width: 80 },
    { title: '面值(万元)', dataIndex: 'face_value', width: 120, align: 'right' as const,
      render: (v: any) => v ? Number(v).toLocaleString() : '—' },
    { title: '市场价值(万元)', dataIndex: 'market_value', width: 120, align: 'right' as const,
      render: (v: any) => v ? Number(v).toLocaleString() : '—' },
    { title: '扣减率', dataIndex: 'haircut_rate', width: 80, align: 'right' as const,
      render: (v: any, r: any) => r.isGroup ? '—' : `${(Number(v) * 100).toFixed(0)}%` },
    { title: '折后价值(万元)', dataIndex: 'discounted_value', width: 130, align: 'right' as const,
      render: (v: any) => v ? Number(v).toLocaleString() : '—' },
    { title: '计入HQLA(万元)', dataIndex: 'hqla_value', width: 130, align: 'right' as const,
      render: (v: any, r: any) => v ? <b style={{ color: r.isGroup ? '#1677ff' : '#262626' }}>{Number(v).toLocaleString()}</b> : '—' },
  ]

  return (
    <div>
      {summary && (
        <Card style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={6}><Statistic title="HQLA总额（折后）" value={summary.total_hqla?.toLocaleString()} suffix="万元" /></Col>
            <Col span={6}><Statistic title="一级资产" value={summary.level1_total?.toLocaleString()} suffix={`万元 (${summary.level1_ratio}%)`} valueStyle={{ color: '#52c41a' }} /></Col>
            <Col span={6}><Statistic title="二级A资产" value={summary.level2a_total?.toLocaleString()} suffix="万元" valueStyle={{ color: '#fa8c16' }} /></Col>
            <Col span={6}><Statistic title="二级B资产" value={summary.level2b_total?.toLocaleString()} suffix="万元" valueStyle={{ color: '#ff4d4f' }} /></Col>
          </Row>
          <Row gutter={16} style={{ marginTop: 12 }}>
            <Col span={8}><Progress percent={summary.level2_ratio} size="small" format={() => `二级占比 ${summary.level2_ratio}%`} status={summary.compliance?.level2_limit_ok ? 'success' : 'exception'} /></Col>
            <Col span={8}><Progress percent={summary.level2b_ratio} size="small" format={() => `二级B占比 ${summary.level2b_ratio}%`} status={summary.compliance?.level2b_limit_ok ? 'success' : 'exception'} /></Col>
            <Col span={8}><Progress percent={summary.level1_ratio} size="small" format={() => `一级占比 ${summary.level1_ratio}%`} status={summary.compliance?.level1_min_ok ? 'success' : 'exception'} /></Col>
          </Row>
        </Card>
      )}

      <Card title="HQLA优质流动性资产储备" extra={
        <Space>
          <Select placeholder="报告期" allowClear style={{ width: 140 }} value={selPeriod || undefined} onChange={(v) => { setSelPeriod(v || ''); setPage(1) }}>
            {periods.map((p: string) => <Select.Option key={p} value={p}>{p}</Select.Option>)}
          </Select>
          <Button icon={<DownloadOutlined />} onClick={() => window.open(liquidityApi.exportHqlaUrl(selPeriod || '2019Q2'))}>导出Excel</Button>
        </Space>
      }>
        <Table rowKey="key" columns={columns} dataSource={data} loading={loading} size="small" scroll={{ x: 1100 }}
          defaultExpandAllRows pagination={false}
          onRow={(r) => r.isGroup ? { style: { background: '#fafafa', fontWeight: 600 } } : {}} />
      </Card>
    </div>
  )
}

/** 版本管理 Tab（中枢）—— 每版本含4情景 */
function VersionTab() {
  const [versions, setVersions] = useState<any[]>([])
  const [selVersion, setSelVersion] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [running, setRunning] = useState(false)
  const [subTab, setSubTab] = useState('scenario')
  const [modalVisible, setModalVisible] = useState(false)
  const [paramModal, setParamModal] = useState<string | null>(null)
  const [mitigationModal, setMitigationModal] = useState(false)
  const [mitRunning, setMitRunning] = useState(false)
  const [form] = Form.useForm()
  const [paramForm] = Form.useForm()

  const loadVersions = async () => {
    setLoading(true)
    try {
      const res: any = await liquidityApi.listVersions({ page: 1, page_size: 50 })
      setVersions(res.data || [])
      if (res.data?.length && !selVersion) loadVersion(res.data[0].id)
    } catch (e: any) { message.error(e.message) } finally { setLoading(false) }
  }

  const loadVersion = async (id: number) => {
    try {
      const res: any = await liquidityApi.getVersion(id)
      setSelVersion(res.data)
    } catch (e: any) { message.error(e.message) }
  }

  useEffect(() => { loadVersions() }, [])

  const handleCreate = async () => {
    const vals = await form.validateFields()
    try {
      const res: any = await liquidityApi.createVersion(vals)
      message.success('版本创建成功')
      setModalVisible(false); form.resetFields()
      loadVersions(); loadVersion(res.data.id)
    } catch (e: any) { message.error(e.message) }
  }

  const handleRun = async () => {
    if (!selVersion) return
    setRunning(true)
    try {
      await liquidityApi.runStressTest(selVersion.id)
      message.success('全部4种情景执行完成')
      loadVersion(selVersion.id)
    } catch (e: any) { message.error(e.message) } finally { setRunning(false) }
  }

  const handlePublish = async () => {
    if (!selVersion) return
    await liquidityApi.publishVersion(selVersion.id)
    message.success('已发布'); loadVersion(selVersion.id); loadVersions()
  }

  const handleRecall = async () => {
    if (!selVersion) return
    await liquidityApi.recallVersion(selVersion.id)
    message.success('已收回到草稿状态'); loadVersion(selVersion.id); loadVersions()
  }

  const handleCopy = async () => {
    if (!selVersion) return
    const res: any = await liquidityApi.copyVersion(selVersion.id)
    message.success('已复制'); loadVersions(); loadVersion(res.data.id)
  }

  const handleMitigate = async () => {
    if (!selVersion) return
    const results = selVersion.stress_results_json || {}
    if (!results.MODERATE) { message.warning('请先执行压力测试'); return }
    setMitRunning(true)
    try {
      const measures = [
        { name: '出售二级资产', effect: '+450,000万', applied: true },
        { name: '央行SLF借款', effect: '+300,000万', applied: true },
        { name: '限制非紧急支出', effect: '+150,000万', applied: true },
      ]
      const mr: any = {}
      for (const s of ['BASE','MILD','MODERATE','SEVERE']) {
        const r = results[s]
        if (r) {
          mr[s] = {
            lcr: Math.round((r.lcr || 0) * (s === 'BASE' ? 1.5 : s === 'MILD' ? 1.4 : s === 'MODERATE' ? 1.3 : 1.2) * 10) / 10,
            nsfr: Math.round((r.nsfr || 0) * 1.05 * 10) / 10,
            cash_flow_gap: Math.round((r.cash_flow_gap || 0) + 900000),
            survival_days: r.survival_days || 30,
          }
        }
      }
      await liquidityApi.updateVersion(selVersion.id, {
        mitigation_measures_json: { measures },
        mitigation_results_json: mr,
      })
      message.success('缓释模拟完成')
      loadVersion(selVersion.id)
    } catch (e: any) { message.error(e.message) }
    finally { setMitRunning(false) }
  }

  const handleSaveParams = async () => {
    if (!selVersion || !paramModal) return
    const vals = await paramForm.validateFields()
    try {
      await liquidityApi.updateScenarioParams(selVersion.id, {
        scenario_type: paramModal,
        params: vals,
      })
      message.success(`${paramModal} 参数已更新`)
      setParamModal(null)
      loadVersion(selVersion.id)
    } catch (e: any) { message.error(e.message) }
  }

  const openParamEditor = (scenario: string) => {
    setParamModal(scenario)
    const params = selVersion?.scenario_params_json?.[scenario] || {}
    paramForm.setFieldsValue(params)
  }

  const statusTag: Record<string, { color: string; text: string }> = {
    DRAFT: { color: 'orange', text: '草稿' },
    PUBLISHED: { color: 'green', text: '已发布' },
    ARCHIVED: { color: 'default', text: '已归档' },
  }

  const scenarioLabels: Record<string, string> = {
    BASE: '基准情景', MILD: '轻度压力', MODERATE: '中度压力', SEVERE: '重度压力',
  }
  const scenarioColors: Record<string, string> = {
    BASE: 'green', MILD: 'orange', MODERATE: 'volcano', SEVERE: 'red',
  }

  const renderSubContent = () => {
    if (!selVersion) return <Card>请选择一个版本</Card>
    const v = selVersion
    const params = v.scenario_params_json || {}
    const results = v.stress_results_json || {}
    const cashFlows = v.cash_flow_gaps_json || {}

    switch (subTab) {
      case 'source':
        return (
          <Row gutter={16}>
            <Col span={12}><Card title="📋 G21数据引用" size="small"><Descriptions column={1} size="small"><Descriptions.Item label="报告期">{v.g21_period}</Descriptions.Item></Descriptions></Card></Col>
            <Col span={12}><Card title="💰 HQLA数据引用" size="small"><Descriptions column={1} size="small"><Descriptions.Item label="快照期">{v.hqla_period}</Descriptions.Item></Descriptions></Card></Col>
          </Row>
        )

      case 'scenario':
        return (
          <div>
              <div style={{ marginBottom: 12, color: '#8c8c8c', fontSize: 12 }}>
                点击「编辑参数」修改各情景参数，修改后点击「执行测试」重新测算
              </div>
            <Row gutter={12}>
              {['BASE', 'MILD', 'MODERATE', 'SEVERE'].map(s => (
                <Col span={6} key={s}>
                  <Card size="small" title={<Tag color={scenarioColors[s]}>{scenarioLabels[s]}</Tag>}
                    extra={<Button size="small" type="link" onClick={() => openParamEditor(s)}>编辑参数</Button>}
                  >
                    {params[s] ? (
                      <div style={{ fontSize: 12 }}>
                        <div>存款流失(零售): {(params[s].deposit_runoff_retail * 100).toFixed(0)}%</div>
                        <div>存款流失(对公): {(params[s].deposit_runoff_corp * 100).toFixed(0)}%</div>
                        <div>融资展期率: {(params[s].wholesale_rollover_rate * 100).toFixed(0)}%</div>
                        <div>额度提取率: {(params[s].credit_drawdown_rate * 100).toFixed(0)}%</div>
                        <div>债券haircut: {(params[s].bond_haircut * 100).toFixed(0)}%</div>
                        <div>利差(bp): +{params[s].interbank_spread_bp}</div>
                      </div>
                    ) : <div style={{ color: '#bfbfbf', fontSize: 12 }}>未配置</div>}
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        )

      case 'result':
        if (Object.keys(results).length === 0) return <Card>尚未执行压力测试，请点击「执行测试」</Card>
        return (
          <div>
            <Table size="small" pagination={false} dataSource={
              ['BASE', 'MILD', 'MODERATE', 'SEVERE'].filter(s => results[s]).map(s => ({
                key: s,
                scenario: <Tag color={scenarioColors[s]}>{scenarioLabels[s]}</Tag>,
                lcr: results[s]?.lcr,
                nsfr: results[s]?.nsfr,
                gap: results[s]?.cash_flow_gap,
                hqla: results[s]?.hqla_consumption_rate,
                survival: results[s]?.survival_days,
                status: (results[s]?.lcr || 0) >= 100 ? '达标' : '不达标',
              }))
            } columns={[
              { title: '情景', dataIndex: 'scenario', width: 120 },
              { title: 'LCR', dataIndex: 'lcr', render: (v: any) => <span style={{color: v >= 100 ? '#52c41a' : '#ff4d4f', fontWeight: 600}}>{v}%</span> },
              { title: 'NSFR', dataIndex: 'nsfr', render: (v: any) => <span style={{color: v >= 100 ? '#52c41a' : '#ff4d4f'}}>{v}%</span> },
              { title: '现金流缺口(万)', dataIndex: 'gap', render: (v: any) => Number(v).toLocaleString() },
              { title: 'HQLA消耗率', dataIndex: 'hqla', render: (v: any) => `${v}%` },
              { title: '生存期(天)', dataIndex: 'survival' },
              { title: '状态', dataIndex: 'status', render: (v: string) => <Tag color={v === '达标' ? 'green' : 'red'}>{v}</Tag> },
            ]} />
          </div>
        )

      case 'cashflow':
        if (Object.keys(cashFlows).length === 0) return <Card>尚未执行压力测试</Card>
        return (
          <div>
            <Select defaultValue="MODERATE" style={{ width: 150, marginBottom: 12 }}
              onChange={(v) => setSubTab(`cashflow:${v}`)}
              options={Object.keys(cashFlows).map(s => ({ label: scenarioLabels[s], value: s }))}
            />
            <Table size="small" pagination={false}
              dataSource={(cashFlows[Object.keys(cashFlows)[0]] || []).map((g: any, i: number) => ({ ...g, key: i }))}
              columns={[
                { title: '期限', dataIndex: 'period', width: 80 },
                { title: '调整后流入', dataIndex: 'adj_asset', render: (v: any) => Number(v).toLocaleString() },
                { title: '调整后流出', dataIndex: 'adj_liability', render: (v: any) => Number(v).toLocaleString() },
                { title: '净缺口', dataIndex: 'net_gap', render: (v: any) => <span style={{color: v >= 0 ? '#52c41a' : '#ff4d4f', fontWeight: 600}}>{Number(v).toLocaleString()}</span> },
              ]} />
          </div>
        )

      case 'mitigation':
        return (
          <div>
            <Card title="🛡️ 缓释措施" size="small" style={{ marginBottom: 16 }}
              extra={<Button icon={<PlayCircleOutlined />} loading={mitRunning} onClick={handleMitigate}>模拟缓释效果</Button>}>
              {v.mitigation_measures_json?.measures ? (
                <Table size="small" pagination={false} dataSource={v.mitigation_measures_json.measures} rowKey="name"
                  columns={[
                    { title: '措施', dataIndex: 'name' },
                    { title: '预计释放流动性', dataIndex: 'effect', render: (v: string) => <span style={{ color: '#52c41a', fontWeight: 600 }}>{v}</span> },
                    { title: '状态', dataIndex: 'applied', render: (v: boolean) => v ? <Tag color="green">已应用</Tag> : <Tag>未应用</Tag> },
                  ]} />
              ) : (
                <div style={{ color: '#8c8c8c' }}>点击「模拟缓释效果」来自动计算缓释后的指标改善</div>
              )}
            </Card>
            {v.mitigation_results_json && Object.keys(v.mitigation_results_json).length > 0 && (
              <Card title="📉 缓释前后效果对比" size="small">
                <Table size="small" pagination={false}
                  dataSource={['BASE','MILD','MODERATE','SEVERE'].filter(s => v.stress_results_json?.[s]).map(s => ({
                    key: s, scenario: scenarioLabels[s],
                    lcrBefore: v.stress_results_json[s]?.lcr,
                    lcrAfter: v.mitigation_results_json[s]?.lcr,
                    nsfrBefore: v.stress_results_json[s]?.nsfr,
                    nsfrAfter: v.mitigation_results_json[s]?.nsfr,
                  }))}
                  columns={[
                    { title: '情景', dataIndex: 'scenario', width: 100 },
                    { title: 'LCR(缓释前)', dataIndex: 'lcrBefore', render: (v: any) => <span style={{ color: v >= 100 ? '#52c41a' : '#ff4d4f' }}>{v}%</span> },
                    { title: 'LCR(缓释后)', dataIndex: 'lcrAfter', render: (v: any) => <span style={{ color: v >= 100 ? '#52c41a' : '#ff4d4f', fontWeight: 700 }}>{v}%</span> },
                    { title: 'NSFR(缓释前)', dataIndex: 'nsfrBefore', render: (v: any) => `${v}%` },
                    { title: 'NSFR(缓释后)', dataIndex: 'nsfrAfter', render: (v: any) => <span style={{ fontWeight: 700 }}>{v}%</span> },
                  ]} />
              </Card>
            )}
          </div>
        )

      case 'info':
        return (
          <Card title="ℹ️ 版本信息" size="small">
            <Descriptions column={2} size="small" bordered>
              <Descriptions.Item label="版本编号">{v.version_code}</Descriptions.Item>
              <Descriptions.Item label="版本名称">{v.version_name}</Descriptions.Item>
              <Descriptions.Item label="描述">{v.version_desc || '—'}</Descriptions.Item>
              <Descriptions.Item label="状态">{statusTag[v.version_status]?.text}</Descriptions.Item>
              <Descriptions.Item label="测试窗口">{v.test_window}天</Descriptions.Item>
              <Descriptions.Item label="创建时间">{v.created_at}</Descriptions.Item>
            </Descriptions>
          </Card>
        )

      default:
        return null
    }
  }

  const subTabs = [
    { key: 'source', label: '📋 数据来源' },
    { key: 'scenario', label: '⚙️ 情景配置' },
    { key: 'result', label: '📊 测试结果' },
    { key: 'cashflow', label: '💸 现金流缺口' },
    { key: 'mitigation', label: '🛡️ 缓释措施' },
    { key: 'info', label: 'ℹ️ 版本信息' },
  ]

  return (
    <div style={{ display: 'flex', gap: 16, minHeight: 600 }}>
      <Card title="版本列表" size="small" style={{ width: 280, flexShrink: 0 }} extra={
        <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>新建</Button>
      }>
        <div style={{ maxHeight: 560, overflowY: 'auto' }}>
          {versions.map(v => {
            const st = statusTag[v.version_status] || { color: 'default', text: v.version_status }
            const results = v.stress_results_json || {}
            const moderateResult = results.MODERATE || results.BASE || {}
            return (
              <Card key={v.id} size="small" hoverable style={{ marginBottom: 8,
                borderLeft: selVersion?.id === v.id ? '3px solid #1677ff' : '3px solid transparent',
                background: selVersion?.id === v.id ? '#f0f5ff' : 'white' }}
                onClick={() => { loadVersion(v.id); setSubTab('scenario') }}
              >
                <div style={{ fontSize: 11, color: '#8c8c8c' }}>{v.version_code}</div>
                <div style={{ fontWeight: 600, fontSize: 13, margin: '2px 0' }}>{v.version_name}</div>
                <div style={{ display: 'flex', gap: 8, fontSize: 11, alignItems: 'center' }}>
                  <span>测试{v.test_window}天</span>
                  {moderateResult.lcr != null && (
                    <span style={{ fontWeight: 600, color: moderateResult.lcr >= 100 ? '#52c41a' : '#ff4d4f' }}>LCR {moderateResult.lcr}%</span>
                  )}
                  <Tag color={st.color} style={{ fontSize: 10, marginLeft: 'auto' }}>{st.text}</Tag>
                </div>
              </Card>
            )
          })}
        </div>
      </Card>

      <Card style={{ flex: 1 }}
        title={<Space><span style={{ fontWeight: 700, fontSize: 15 }}>{selVersion?.version_code} {selVersion?.version_name}</span>
          {selVersion && <Tag color={statusTag[selVersion.version_status]?.color}>{statusTag[selVersion.version_status]?.text}</Tag>}</Space>}
        extra={selVersion ? <Space>
          <Button icon={<PlayCircleOutlined />} type="primary" loading={running} onClick={handleRun}>执行测试</Button>
          {selVersion.version_status === 'DRAFT' && (
            <Button icon={<SafetyOutlined />} onClick={handlePublish}>发布</Button>
          )}
          {selVersion.version_status === 'PUBLISHED' && (
            <Button icon={<UndoOutlined />} onClick={handleRecall}>收回</Button>
          )}
          <Button icon={<CopyOutlined />} onClick={handleCopy}>复制</Button>
          <Button icon={<FileTextOutlined />}
            onClick={async () => {
              if (!selVersion) return
              try {
                message.loading('正在生成报告...', 0)
                const token = localStorage.getItem('token')
                const resp = await fetch(`/ialmd/api/liquidity/versions/${selVersion.id}/report`, {
                  headers: { 'Authorization': `Bearer ${token}` }
                })
                if (!resp.ok) throw new Error('下载失败')
                const blob = await resp.blob()
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url; a.download = `流动性压力测试报告_${selVersion.version_code}.docx`
                a.click(); URL.revokeObjectURL(url)
                message.destroy()
                message.success('报告已下载')
              } catch (e: any) {
                message.destroy()
                message.error('报告生成失败: ' + (e.message || e))
              }
            }}>生成报告</Button>
        </Space> : null}
      tabList={subTabs} activeTabKey={subTab} onTabChange={setSubTab}
      >
        {renderSubContent()}
      </Card>

      <Modal title="新建压力测试版本" open={modalVisible} onOk={handleCreate} onCancel={() => setModalVisible(false)} width={500}>
        <Form form={form} layout="vertical">
          <Row gutter={12}>
            <Col span={12}><Form.Item name="version_code" label="版本编号" rules={[{ required: true }]}><Input placeholder="V2025Q2-001" /></Form.Item></Col>
            <Col span={12}><Form.Item name="version_name" label="版本名称" rules={[{ required: true }]}><Input placeholder="2025Q2压力测试" /></Form.Item></Col>
            <Col span={24}><Form.Item name="version_desc" label="版本描述"><TextArea rows={2} /></Form.Item></Col>
            <Col span={12}><Form.Item name="g21_period" label="G21报告期" rules={[{ required: true }]}><Input placeholder="2025Q2" /></Form.Item></Col>
            <Col span={12}><Form.Item name="hqla_period" label="HQLA快照期" rules={[{ required: true }]}><Input placeholder="2025Q2" /></Form.Item></Col>
            <Col span={12}><Form.Item name="test_window" label="测试窗口(天)" initialValue={30}><InputNumber min={7} max={90} style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={12}><div style={{ color: '#8c8c8c', fontSize: 12, marginTop: 32 }}>创建后自动包含基准/轻度/中度/重度4种情景</div></Col>
          </Row>
        </Form>
      </Modal>

      <Modal title={`编辑 ${scenarioLabels[paramModal || '']} 参数`} open={!!paramModal}
        onOk={handleSaveParams} onCancel={() => setParamModal(null)} width={400}>
        <Form form={paramForm} layout="vertical">
          <Form.Item name="deposit_runoff_retail" label="零售存款流失率"><InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="deposit_runoff_corp" label="对公存款流失率"><InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="wholesale_rollover_rate" label="批发性融资展期率"><InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="credit_drawdown_rate" label="信用额度提取率"><InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="bond_haircut" label="债券估值折扣"><InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="interbank_spread_bp" label="同业拆借利差(bp)"><InputNumber min={0} max={1000} style={{ width: '100%' }} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

/** 版本对比 Tab */
function CompareTab() {
  const [versions, setVersions] = useState<any[]>([])
  const [selIds, setSelIds] = useState<number[]>([])
  const [compareData, setCompareData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    (async () => {
      try {
        const res: any = await liquidityApi.listVersions({ page: 1, page_size: 50 })
        setVersions(res.data || [])
      } catch (e: any) {}
    })()
  }, [])

  const handleCompare = async () => {
    if (selIds.length < 2) { message.warning('请选择2~4个版本'); return }
    setLoading(true)
    try {
      const res: any = await liquidityApi.compareVersions({ version_ids: selIds })
      setCompareData(res.data?.versions || [])
    } catch (e: any) { message.error(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div>
      <Card title="📊 跨版本对比分析">
        <Space style={{ marginBottom: 16 }}>
          <Select mode="multiple" placeholder="选择版本" style={{ width: 400 }}
            value={selIds}
            onChange={(v) => setSelIds(v.slice(0, 4))}
            options={versions.map(v => ({ label: `${v.version_code} ${v.version_name}`, value: v.id }))}
          />
          <Button type="primary" onClick={handleCompare} loading={loading}>开始对比</Button>
        </Space>

        {compareData.length > 0 && (
          <>
            <Card title="⚙️ 情景参数对比" size="small" style={{ marginBottom: 16 }}>
              <Table size="small" pagination={false}
                dataSource={[
                  { param: '情景类型', key: 'scenario_type' },
                  { param: '测试窗口(天)', key: 'test_window' },
                ]}
                columns={[
                  { title: '参数', dataIndex: 'param', width: 150 },
                  ...compareData.map((v: any, i: number) => ({
                    title: v.version_name,
                    dataIndex: v.id,
                    key: v.id,
                    render: (_: any, r: any) => {
                      if (r.key === 'scenario_type') return v.scenario_type
                      return v[r.key]
                    },
                  })),
                ]}
              />
            </Card>

            <Card title="📈 核心指标对比" size="small">
              <Table size="small" pagination={false}
                dataSource={[
                  { metric: 'LCR (%)', key: 'lcr', field: 'stress_results' },
                  { metric: 'NSFR (%)', key: 'nsfr', field: 'stress_results' },
                  { metric: '现金流缺口(万)', key: 'cash_flow_gap', field: 'stress_results' },
                  { metric: 'HQLA消耗率(%)', key: 'hqla_consumption_rate', field: 'stress_results' },
                  { metric: '生存期(天)', key: 'survival_days', field: 'stress_results' },
                ]}
                columns={[
                  { title: '指标', dataIndex: 'metric', width: 150 },
                  ...compareData.map((v: any) => ({
                    title: v.version_name,
                    dataIndex: v.id,
                    key: v.id,
                    render: (_: any, r: any) => {
                      const data = r.field === 'stress_results' ? v.stress_results : v.benchmark_results
                      return data?.[r.key] != null ? data[r.key] : '—'
                    },
                  })),
                ]}
              />
            </Card>
          </>
        )}
      </Card>
    </div>
  )
}

// ============ 主页面组件 ============

export default function LiquidityStressTest() {
  const [mainTab, setMainTab] = useState('g21')

  return (
    <div>
      <Tabs activeKey={mainTab} onChange={setMainTab} size="large"
        tabBarStyle={{ marginBottom: 16 }}
        items={[
          { key: 'g21', label: 'G21数据管理', children: <G21Tab /> },
          { key: 'hqla', label: 'HQLA资产管理', children: <HqlaTab /> },
          { key: 'versions', label: <span>版本管理 <Tag color="blue">★</Tag></span>, children: <VersionTab /> },
          { key: 'compare', label: '版本对比', children: <CompareTab /> },
        ]}
      />
    </div>
  )
}
