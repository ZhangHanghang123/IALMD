/** 报告采集管理 — 自动下载/上传/指标提取/结果查看 */
import { useState, useEffect } from 'react'
import {
  Card, Table, Tag, Button, Space, Input, Select, Row, Col, Modal, Tabs,
  Statistic, Upload, message, Tooltip,
} from 'antd'
import {
  DownloadOutlined, ReloadOutlined, UploadOutlined,
  ScanOutlined, CloudDownloadOutlined, RobotOutlined,
} from '@ant-design/icons'
import { ontologyApi, reportCollectApi } from '../api'

const REPORT_TYPES: Record<string, string> = {
  ANNUAL: '年度报告', HALF: '半年度报告', QREPORT: '季度报告',
  SOLVENCY: '偿付能力报告', ACTUARIAL: '精算报告',
  PREMIUM: '保费收入公告', DIVIDEND: '分红实现率公告',
  ESG: 'ESG报告', CONSUMER: '消费者保护',
}

export default function ReportManager() {
  const [activeTab, setActiveTab] = useState('tasks')
  const [tasks, setTasks] = useState<any[]>([])
  const [tasksTotal, setTasksTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<any>({})
  const [filters, setFilters] = useState<any>({})
  const [selectedBanks, setSelectedBanks] = useState<string>('')
  const [collectLoading, setCollectLoading] = useState(false)
  const [extractResults, setExtractResults] = useState<any[]>([])
  const [extractTotal, setExtractTotal] = useState(0)
  const [bankOptions, setBankOptions] = useState<any[]>([])

  const loadStats = async () => {
    try {
      const r: any = await reportCollectApi.getStats()
      setStats(r.data || {})
    } catch {}
  }

  const loadTasks = async () => {
    setLoading(true)
    try {
      const r: any = await reportCollectApi.listTasks({
        page, page_size: 20, ...filters,
        institution_ids: selectedBanks || undefined,
      })
      setTasks(r.data || [])
      setTasksTotal(r.total || 0)
    } catch {}
    setLoading(false)
  }

  const loadBanks = async () => {
    try {
      const r: any = await ontologyApi.listBanks({})
      setBankOptions((r.data || []).map((b: any) => ({
        label: `${b.bank_name} (${b.bank_code})`,
        value: String(b.id),
      })))
    } catch {}
  }

  const loadExtractResults = async () => {
    try {
      const r: any = await reportCollectApi.listExtractResults({ page: 1, page_size: 50 })
      setExtractResults(r.data || [])
      setExtractTotal(r.total || 0)
    } catch {}
  }

  useEffect(() => { loadStats(); loadBanks() }, [])
  useEffect(() => {
    if (activeTab === 'tasks') loadTasks()
    if (activeTab === 'results') loadExtractResults()
  }, [activeTab, page, filters, selectedBanks])

  const handleCollect = async () => {
    if (!selectedBanks) { message.warning('请选择保险机构'); return }
    setCollectLoading(true)
    try {
      const r: any = await reportCollectApi.triggerCollect(selectedBanks)
      message.success(`采集完成: ${r.data?.banks_processed || 0} 家保险机构`)
      loadStats(); loadTasks()
    } catch (e: any) { message.error(e?.response?.data?.detail || '采集失败') }
    setCollectLoading(false)
  }

  const handleExtract = async (bankId: number) => {
    message.loading('正在提取指标...')
    try {
      const r: any = await reportCollectApi.triggerExtract(bankId, '2015,2016')
      message.success(`提取完成: ${r.data?.extracted || 0} 个指标值`)
      loadStats(); loadTasks(); loadExtractResults()
    } catch { message.error('提取失败') }
  }

  const handleExtractAll = async () => {
    message.loading({ content: '批量提取所有银行指标...', duration: 0 })
    try {
      const r: any = await reportCollectApi.triggerExtractAll()
      const d = r.data || {}
      message.success(`完成: ${d.total_extracted || 0} 个指标值 (${d.total_banks || 0} 家保险机构)`)
      loadStats(); loadExtractResults()
    } catch { message.error('提取失败') }
  }

  const taskColumns = [
    { title: '机构', dataIndex: 'bank_name', width: 130, fixed: 'left' as any },
    { title: '代码', dataIndex: 'bank_code', width: 60 },
    { title: '报告类型', dataIndex: 'report_type', width: 100,
      render: (v: string) => <Tag>{REPORT_TYPES[v] || v}</Tag> },
    { title: '年份', dataIndex: 'report_year', width: 60 },
    { title: '文件名', dataIndex: 'file_name', ellipsis: true, width: 220 },
    { title: '格式', dataIndex: 'file_format', width: 50 },
    { title: '大小', dataIndex: 'file_size', width: 80,
      render: (v: number) => v > 1024*1024 ? `${(v/1024/1024).toFixed(1)}M` : `${(v/1024).toFixed(0)}K` },
    { title: '状态', dataIndex: 'extraction_status', width: 90,
      render: (v: string) => {
        const m: any = {PENDING:{color:'orange',text:'待提取'},PARSED:{color:'green',text:'已提取'},FAILED:{color:'red',text:'失败'}}
        return <Tag color={m[v]?.color}>{m[v]?.text || v}</Tag>
      }},
    { title: '操作', width: 120, render: (_: any, r: any) => (
      <Space size={4}>
        <Button size="small" icon={<DownloadOutlined />}
          onClick={() => window.open(reportCollectApi.getDownloadUrl(r.institution_id, r.id))} />
        <Button size="small" icon={<RobotOutlined />} onClick={() => handleExtract(r.institution_id)}>提取</Button>
      </Space>
    )},
  ]

  const resultColumns = [
    { title: '机构', dataIndex: 'bank_name', width: 110 },
    { title: '指标', dataIndex: 'indicator_name', width: 140, render: (v: string) => <Tag color="purple">{v}</Tag> },
    { title: '值', dataIndex: 'value', width: 110, render: (v: any) => v ? Number(v).toLocaleString() : '-' },
    { title: '单位', dataIndex: 'unit', width: 50 },
    { title: '年份', dataIndex: 'year', width: 60 },
    { title: '置信度', dataIndex: 'confidence', width: 70,
      render: (v: number) => `${((v||0)*100).toFixed(0)}%` },
    { title: '状态', dataIndex: 'verify_status', width: 80,
      render: (v: string) => <Tag color={v==='APPROVED'?'green':'orange'}>{v}</Tag> },
  ]

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <h2>📋 报告采集管理</h2>
          <p style={{ color: '#8c8c8c', margin: 0 }}>自动/手动采集保险经营报告 → 存入知识库 → 提取指标</p>
        </Col>
        <Col>
          <Space>
            <Button icon={<ScanOutlined />} onClick={handleExtractAll}>批量提取指标</Button>
            <Button type="primary" icon={<CloudDownloadOutlined />} loading={collectLoading} onClick={handleCollect}>一键采集</Button>
          </Space>
        </Col>
      </Row>

      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col xs={6}><Card size="small"><Statistic title="报告文档" value={stats.total_reports || 0} suffix="份" /></Card></Col>
        <Col xs={6}><Card size="small"><Statistic title="已提取" value={stats.parsed || 0} valueStyle={{ color: '#3f8600' }} /></Card></Col>
        <Col xs={6}><Card size="small"><Statistic title="待提取" value={stats.pending || 0} valueStyle={{ color: '#faad14' }} /></Card></Col>
        <Col xs={6}><Card size="small"><Statistic title="指标值" value={stats.extracted_indicators || 0} valueStyle={{ color: '#1677ff' }} /></Card></Col>
      </Row>

      <Card size="small" style={{ marginBottom: 12 }}>
        <Row gutter={[12, 8]} align="middle">
          <Col flex="auto">
            <Select mode="multiple" placeholder="选择保险机构（不选=全部）" style={{ width: '100%' }}
              options={bankOptions} value={selectedBanks ? selectedBanks.split(',').filter(Boolean) : []}
              onChange={(vals: string[]) => setSelectedBanks(vals.join(','))} showSearch
              filterOption={(input, option: any) => option?.label?.includes(input)} />
          </Col>
          <Col>
            <Select allowClear placeholder="报告类型" style={{ width: 140 }}
              onChange={(v: string) => setFilters((f: any) => ({ ...f, report_type: v || undefined }))}>
              {Object.entries(REPORT_TYPES).map(([k, v]) => <Select.Option key={k} value={k}>{v}</Select.Option>)}
            </Select>
          </Col>
          <Col>
            <Select allowClear placeholder="状态"
              onChange={(v: string) => setFilters((f: any) => ({ ...f, extraction_status: v || undefined }))}>
              <Select.Option value="PENDING">待提取</Select.Option>
              <Select.Option value="DONE">已提取</Select.Option>
            </Select>
          </Col>
          <Col><Button icon={<ReloadOutlined />} onClick={loadTasks}>刷新</Button></Col>
        </Row>
      </Card>

      <Card bodyStyle={{ padding: 0 }}>
        <Tabs activeKey={activeTab} onChange={setActiveTab} type="card">
          <Tabs.TabPane tab="📑 采集记录" key="tasks">
            <Table dataSource={tasks} columns={taskColumns} rowKey="id" size="small"
              loading={loading} scroll={{ x: 1100 }}
              pagination={{ current: page, total: tasksTotal, pageSize: 20, onChange: setPage,
                showTotal: (t: number) => `共 ${t} 条` }} />
          </Tabs.TabPane>
          <Tabs.TabPane tab={`📊 提取结果 (${extractTotal})`} key="results">
            <Table dataSource={extractResults} columns={resultColumns} rowKey="id" size="small"
              pagination={{ pageSize: 30, showTotal: (t: number) => `共 ${t} 条` }} />
          </Tabs.TabPane>
          <Tabs.TabPane tab="📂 手动上传" key="upload">
            <UploadSection bankOptions={bankOptions} onUploaded={() => { loadTasks(); loadStats() }} />
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

function UploadSection({ bankOptions, onUploaded }: { bankOptions: any[], onUploaded: () => void }) {
  const [bankId, setBankId] = useState<number>()
  const [rtype, setRtype] = useState('ANNUAL')
  const [year, setYear] = useState(new Date().getFullYear() - 1)

  return (
    <div style={{ padding: 24, maxWidth: 600 }}>
      <h4>📂 手动上传报告文件</h4>
      <Row gutter={[12, 12]} style={{ marginTop: 12 }}>
        <Col span={24}>
          <Select showSearch placeholder="选择保险机构" style={{ width: '100%' }}
            filterOption={(input, option: any) => option?.label?.includes(input)}
            options={bankOptions} value={bankId} onChange={(v: number) => setBankId(v)} />
        </Col>
        <Col span={12}>
          <Select style={{ width: '100%' }} value={rtype} onChange={setRtype}>
            <Select.Option value="ANNUAL">年度报告</Select.Option>
            <Select.Option value="HALF">半年度报告</Select.Option>
            <Select.Option value="QREPORT">季度报告</Select.Option>
            <Select.Option value="SOLVENCY">偿付能力报告</Select.Option>
            <Select.Option value="ACTUARIAL">精算报告</Select.Option>
            <Select.Option value="PREMIUM">保费收入公告</Select.Option>
            <Select.Option value="ESG">ESG报告</Select.Option>
          </Select>
        </Col>
        <Col span={12}>
          <Input type="number" value={year} onChange={e => setYear(Number(e.target.value))} placeholder="报告年份" />
        </Col>
        <Col span={24}>
          <Upload.Dragger
            name="file"
            action={bankId ? `/ialmd/api/report-collect/upload/${bankId}?report_type=${rtype}&report_year=${year}` : ''}
            beforeUpload={file => { if (!bankId) { message.warning('请先选择保险机构'); return false }; return true }}
            onChange={info => {
              if (info.file.status === 'done') { message.success('上传成功'); onUploaded() }
              if (info.file.status === 'error') { message.error('上传失败') }
            }}
            accept=".pdf,.html,.PDF,.HTML"
          >
            <p className="ant-upload-drag-icon"><UploadOutlined style={{ fontSize: 36 }} /></p>
            <p>点击或拖拽 PDF/HTML 文件到此处上传</p>
            <p style={{ fontSize: 11, color: '#8c8c8c' }}>存入：保险经营报告下载/{'{银行名}'}/{'{报告类型}'}/</p>
          </Upload.Dragger>
        </Col>
      </Row>
    </div>
  )
}