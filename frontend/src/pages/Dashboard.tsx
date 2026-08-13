import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Table, Spin, Tag, Progress, Space, Typography } from 'antd'
import {
  BankOutlined, FundOutlined, FileTextOutlined, CheckCircleOutlined,
  RiseOutlined, FallOutlined, ThunderboltOutlined, ApiOutlined,
  DatabaseOutlined, NodeIndexOutlined, MessageOutlined, BarChartOutlined,
  ClusterOutlined, LinkOutlined, ExperimentOutlined, PieChartOutlined,
  ReloadOutlined, StockOutlined, TeamOutlined,
} from '@ant-design/icons'
import { dashboardApi } from '../api'

const { Text, Title } = Typography

const CAT_COLORS: Record<string, string> = {
  '保险集团': '#1677ff', '再保险银行': '#52c41a', '寿险': '#fa8c16',
  '财险': '#722ed1', '再保险': '#eb2f96',
  '年报': '#1677ff', '半年报': '#52c41a', '一季报': '#13c2c2', '三季报': '#fa8c16',
  '规模类': '#1677ff', '盈利类': '#52c41a', '风险类': '#ff4d4f',
  '资本类': '#722ed1', '流动性': '#13c2c2', 'ESG': '#fa8c16',
}

function MiniBarChart({ data, height = 120, color = '#1677ff', unit = '%' }: {
  data: { period: string; value: number }[]; height?: number; color?: string; unit?: string;
}) {
  if (!data.length) return <EmptyPlaceholder text="暂无数据" />
  const max = Math.max(...data.map(d => d.value), 0.01)
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 20, height, paddingTop: 8, justifyContent: 'center' }}>
      {data.map((item) => (
        <div key={item.period} style={{ textAlign: 'center', flex: 1 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color, marginBottom: 4 }}>{item.value}{unit}</div>
          <div style={{ height: Math.max(4, (item.value / max) * (height - 38)), minWidth: 36,
            background: `linear-gradient(180deg, ${color}, ${color}66)`, borderRadius: '4px 4px 0 0', margin: '0 auto' }} />
          <div style={{ marginTop: 6, fontSize: 11, color: '#8c8c8c' }}>{item.period}</div>
        </div>
      ))}
    </div>
  )
}

function HorizontalBar({ data, height = 200, maxLabelLen = 6 }: {
  data: { label: string; count: number; color: string }[]; height?: number; maxLabelLen?: number;
}) {
  if (!data.length) return <EmptyPlaceholder text="暂无数据" />
  const max = Math.max(...data.map(d => d.count), 1)
  const barH = Math.max(22, Math.min(32, (height - 40) / data.length))
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, paddingTop: 8, height }}>
      {data.map((item, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Text style={{ fontSize: 12, width: 60, textAlign: 'right', flexShrink: 0, color: '#595959' }}>
            {item.label.slice(0, maxLabelLen)}
          </Text>
          <div style={{ flex: 1, background: '#f5f5f5', borderRadius: 4, overflow: 'hidden', height: barH }}>
            <div style={{ height: '100%', width: `${(item.count / max) * 100}%`, background: CAT_COLORS[item.label] || item.color || '#1677ff',
              borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', paddingRight: 8, minWidth: 28 }}>
              <Text style={{ color: '#fff', fontSize: 11, fontWeight: 600 }}>{item.count}</Text>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function EmptyPlaceholder({ text }: { text: string }) {
  return <div style={{ textAlign: 'center', padding: '40px 0', color: '#bfbfbf', fontSize: 14 }}>{text}</div>
}

const TYPE_TAGS: Record<string, { label: string; color: string }> = {
  ANNUAL: { label: '年报', color: 'blue' }, HALF: { label: '半年报', color: 'cyan' },
  Q1: { label: '一季报', color: 'green' }, Q3: { label: '三季报', color: 'orange' },
  EXPRESS: { label: '快报', color: 'purple' },
  CAPITAL: { label: '资本', color: 'geekblue' }, LIQUIDITY: { label: '流动性', color: 'lime' },
  ESG: { label: 'ESG', color: 'gold' },
}
const STATUS_COLOR: Record<string, string> = { PARSED: 'success', DOWNLOADING: 'processing', FAILED: 'error', PENDING: 'default' }
const STATUS_LABEL: Record<string, string> = { PARSED: '已解析', DOWNLOADING: '采集中', FAILED: '失败', PENDING: '待采集' }

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<any>({})
  const [refreshTime, setRefreshTime] = useState('')

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res: any = await dashboardApi.getDashboard()
      setData(res.data || {})
      setRefreshTime(new Date().toLocaleTimeString('zh-CN'))
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return (
    <div style={{ textAlign: 'center', padding: 120 }}>
      <Spin size="large" /><div style={{ marginTop: 16, color: '#8c8c8c' }}>加载经营数据中...</div>
    </div>
  )

  const kpi = data.kpi || {}
  const reports = data.recent_reports || []
  const parsedCount = (data.recent_reports || []).filter((r: any) => r.collect_status === 'PARSED').length

  return (
    <div style={{ height: 'calc(100vh - 64px)', overflowY: 'auto', padding: '0 24px 24px' }}>

      {/* 标题栏 */}
      <div style={{ marginBottom: 20, padding: '20px 0 0', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Title level={3} style={{ margin: 0 }}>经营分析概览</Title>
          <a href="/ialmd/chat" title="AI经营分析助手" style={{ display: 'inline-flex', textDecoration: 'none' }}>
            <div style={{
              width: 44, height: 44, borderRadius: '50%',
              background: 'linear-gradient(135deg, #ff9a56, #ff6b35, #d4380d)',
              boxShadow: '0 2px 12px rgba(212,56,13,0.35)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              animation: 'cowPulse 2s ease-in-out infinite',
              transition: 'transform 0.15s',
            }} onMouseEnter={e => { e.currentTarget.style.animation = 'none'; e.currentTarget.style.transform = 'scale(1.2)'; }}
               onMouseLeave={e => { e.currentTarget.style.animation = 'cowPulse 2s ease-in-out infinite'; e.currentTarget.style.transform = 'scale(1)'; }}>
              <svg viewBox="0 0 64 64" width="30" height="30">
                <ellipse cx="32" cy="30" rx="20" ry="17" fill="#FFF8E7" stroke="#D4A574" strokeWidth="1.5"/>
                <ellipse cx="13" cy="16" rx="5.5" ry="4.5" fill="#FFF8E7" stroke="#D4A574" strokeWidth="1.2" transform="rotate(-18,13,16)"/>
                <ellipse cx="13" cy="16" rx="3" ry="2.5" fill="#FFE0C0"/>
                <ellipse cx="51" cy="16" rx="5.5" ry="4.5" fill="#FFF8E7" stroke="#D4A574" strokeWidth="1.2" transform="rotate(18,51,16)"/>
                <ellipse cx="51" cy="16" rx="3" ry="2.5" fill="#FFE0C0"/>
                <path d="M16 14 Q13 4 10 2" fill="none" stroke="#8B6914" strokeWidth="2.5" strokeLinecap="round"/>
                <circle cx="10" cy="2" r="2.5" fill="#D4A017"/>
                <path d="M48 14 Q51 4 54 2" fill="none" stroke="#8B6914" strokeWidth="2.5" strokeLinecap="round"/>
                <circle cx="54" cy="2" r="2.5" fill="#D4A017"/>
                <ellipse cx="25" cy="25" rx="4.5" ry="5" fill="#fff"/>
                <circle cx="26" cy="25" r="2.5" fill="#2c1810"/><circle cx="27" cy="24" r="1" fill="#fff"/>
                <ellipse cx="39" cy="25" rx="4.5" ry="5" fill="#fff"/>
                <circle cx="38" cy="25" r="2.5" fill="#2c1810"/><circle cx="39" cy="24" r="1" fill="#fff"/>
                <circle cx="25" cy="25" r="7" fill="none" stroke="#D4A017" strokeWidth="1.2"/>
                <circle cx="39" cy="25" r="7" fill="none" stroke="#D4A017" strokeWidth="1.2"/>
                <ellipse cx="29" cy="33" rx="2" ry="1.5" fill="#D4A574"/>
                <ellipse cx="35" cy="33" rx="2" ry="1.5" fill="#D4A574"/>
                <path d="M27 37 Q32 40 37 37" fill="none" stroke="#D4A574" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
          </a>
        </div>
          <Text type="secondary">覆盖 {kpi.bank_count || 0} 家保险机构 · {kpi.indicator_count || 0} 项指标 · {kpi.value_count?.toLocaleString() || 0} 条数据</Text>
        </div>
        <Space>
          {data.last_value_time && <Text type="secondary" style={{ fontSize: 12 }}>最新数据: {new Date(data.last_value_time).toLocaleDateString('zh-CN')}</Text>}
          <a onClick={loadData}><ReloadOutlined /> 刷新</a>
        </Space>
      </div>

      {/* ── KPI 卡片第一行：核心指标 ── */}
      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        {[
          { icon: <BankOutlined />, title: '覆盖银行', value: kpi.bank_count, color: '#1677ff', bg: '#e6f4ff' },
          { icon: <FundOutlined />, title: '经营指标', value: kpi.indicator_count, color: '#52c41a', bg: '#f6ffed' },
          { icon: <DatabaseOutlined />, title: '指标数据量', value: (kpi.value_count || 0).toLocaleString(), color: '#fa8c16', bg: '#fff7e6' },
          { icon: <FileTextOutlined />, title: '报告记录', value: kpi.report_count, color: '#722ed1', bg: '#f9f0ff' },
          { icon: <FileTextOutlined />, title: '报告文件', value: kpi.report_file_count, color: '#13c2c2', bg: '#e6fffb' },
          { icon: <CheckCircleOutlined />, title: '准确率', value: `${kpi.accuracy_rate || 0}%`, color: '#eb2f96', bg: '#fff0f6' },
        ].map(item => (
          <Col xs={12} sm={8} md={4} key={item.title}>
            <Card hoverable size="small" style={{ borderTop: `3px solid ${item.color}`, background: item.bg }}>
              <Statistic title={item.title} value={item.value}
                prefix={React.cloneElement(item.icon, { style: { color: item.color } })}
                valueStyle={{ color: item.color, fontSize: 24 }} />
            </Card>
          </Col>
        ))}
      </Row>

      {/* ── KPI 卡片第二行：本体/对话/工作流 ── */}
      <Row gutter={[12, 12]} style={{ marginBottom: 24 }}>
        {[
          { icon: <ClusterOutlined />, title: '本体概念', value: kpi.ontology_class_count, color: '#1677ff' },
          { icon: <LinkOutlined />, title: '本体关系', value: kpi.ontology_relation_count, color: '#52c41a' },
          { icon: <NodeIndexOutlined />, title: '指标映射', value: kpi.mapping_count, color: '#722ed1' },
          { icon: <MessageOutlined />, title: '对话会话', value: kpi.session_count, color: '#fa8c16' },
          { icon: <MessageOutlined />, title: '对话消息', value: kpi.message_count?.toLocaleString(), color: '#13c2c2' },
          { icon: <ThunderboltOutlined />, title: '工作流执行成功率', value: `${kpi.exec_success_rate || 0}%`, color: '#eb2f96' },
        ].map(item => (
          <Col xs={12} sm={8} md={4} key={item.title}>
            <Card size="small" style={{ textAlign: 'center' }}>
              <Statistic title={item.title} value={item.value}
                prefix={React.cloneElement(item.icon, { style: { color: item.color } })}
                valueStyle={{ color: item.color, fontSize: 22 }} />
            </Card>
          </Col>
        ))}
      </Row>

      {/* ── 趋势图 + 排行 ── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title={<Space><BarChartOutlined />偿付能力充足率 NIM 年度趋势</Space>}
            extra={<Text type="secondary" style={{ fontSize: 12 }}>全银行均值</Text>}>
            <MiniBarChart data={data.nim_trend || []} height={150} color="#1677ff" />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title={<Space><StockOutlined />ROE 年度趋势</Space>}
            extra={<Text type="secondary" style={{ fontSize: 12 }}>全银行均值</Text>}>
            <MiniBarChart data={data.roe_trend || []} height={150} color="#52c41a" />
          </Card>
        </Col>
      </Row>

      {/* ── NPL 排行 + 机构类型分布 ── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={10}>
          <Card title={<Space><ThunderboltOutlined />不良贷款率 NPL 最低排名</Space>}
            extra={<Text type="secondary" style={{ fontSize: 12 }}>2025 FY</Text>}>
            {data.npl_ranking?.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {(data.npl_ranking || []).map((item: any, idx: number) => (
                  <div key={item.bank_code} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '6px 12px', background: idx % 2 === 0 ? '#fafafa' : '#fff', borderRadius: 6,
                    borderLeft: `3px solid ${idx < 3 ? '#52c41a' : '#d9d9d9'}` }}>
                    <Space>
                      <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                        width: 22, height: 22, borderRadius: '50%',
                        background: ['#f5222d', '#fa8c16', '#faad14', '#8c8c8c', '#8c8c8c'][idx] || '#8c8c8c',
                        color: idx < 3 ? '#fff' : '#595959', fontSize: 11, fontWeight: 700 }}>
                        {item.rank}
                      </span>
                      <Text style={{ fontSize: 13 }}>{item.bank_name}</Text>
                    </Space>
                    <Space>
                      {item.value > 2 ? <RiseOutlined style={{ color: '#ff4d4f' }} /> : <FallOutlined style={{ color: '#52c41a' }} />}
                      <Text strong style={{ color: item.value > 2 ? '#ff4d4f' : '#52c41a', fontSize: 14 }}>{item.value}%</Text>
                    </Space>
                  </div>
                ))}
              </div>
            ) : <EmptyPlaceholder text="暂无不���率数据" />}
          </Card>
        </Col>

        <Col xs={12} lg={7}>
          <Card title={<Space><TeamOutlined />机构类型分布</Space>}>
            <HorizontalBar data={(data.bank_type_dist || []).map((d: any) => ({ label: d.label, count: d.count, color: CAT_COLORS[d.label] || '#1677ff' }))} height={200} maxLabelLen={4} />
          </Card>
        </Col>

        <Col xs={12} lg={7}>
          <Card title={<Space><PieChartOutlined />指标分类分布</Space>}>
            <HorizontalBar data={(data.indicator_cat_dist || []).map((d: any) => ({ label: d.label, count: d.count, color: CAT_COLORS[d.label] || '#1677ff' }))} height={200} maxLabelLen={4} />
          </Card>
        </Col>
      </Row>

      {/* ── 报告类型分布 + 最近报告 ── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} lg={6}>
          <Card title={<Space><FileTextOutlined />报告类型分布</Space>}>
            <HorizontalBar data={(data.report_type_dist || []).slice(0, 8).map((d: any) =>
              ({ label: d.label, count: d.count, color: CAT_COLORS[d.label] || '#1677ff' }))} height={220} maxLabelLen={5} />
          </Card>
        </Col>
        <Col xs={12} lg={6}>
          <Card title={<Space><ApiOutlined />采集状态</Space>}>
            <div style={{ padding: '12px 0' }}>
              <Progress type="dashboard" percent={reports.length > 0 ? Math.round((parsedCount / reports.length) * 100) : 0}
                strokeColor="#52c41a" size={140} format={() => `${parsedCount}/${reports.length}`} />
              <div style={{ textAlign: 'center', marginTop: 8 }}>
                <Tag color={parsedCount > 0 ? 'success' : 'default'}>已解析: {parsedCount}</Tag>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title={<Space><DatabaseOutlined />最近采集报告</Space>}>
            <Table dataSource={reports} rowKey="id" pagination={false} size="small"
              locale={{ emptyText: '暂无采集数据' }}
              columns={[
                { title: '机构', dataIndex: 'bank_name', width: 80, render: (v: string) => <Text strong>{v}</Text> },
                { title: '类型', dataIndex: 'report_type', width: 80, render: (v: string) => {
                  const t = TYPE_TAGS[v] || { label: v, color: 'default' }
                  return <Tag color={t.color}>{t.label}</Tag>
                }},
                { title: '年度', dataIndex: 'report_year', width: 60 },
                { title: '状态', dataIndex: 'collect_status', width: 80,
                  render: (v: string) => <Tag color={STATUS_COLOR[v] || 'default'}>{STATUS_LABEL[v] || v}</Tag> },
                { title: '发布日', dataIndex: 'publish_date', width: 90, render: (v: string) => v ? v.slice(0, 10) : '-' },
              ]} />
          </Card>
        </Col>
      </Row>

    </div>
  )
}
