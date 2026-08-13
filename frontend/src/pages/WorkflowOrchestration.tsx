/** 工作流编排 — 全链路串联：报告采集→指标提取→本体映射→同业对比→报告生成→智能对话 */
import { useState, useEffect } from 'react'
import {
  Card, Table, Tag, Button, Space, Tabs, Modal, Form, Input, Select, Row, Col,
  Statistic, message, Popconfirm, Drawer, Descriptions, Timeline, Tooltip,
} from 'antd'
import {
  PlusOutlined, PlayCircleOutlined, DeleteOutlined, ApartmentOutlined,
  SearchOutlined, BarChartOutlined, FileTextOutlined, HistoryOutlined,
  ReloadOutlined, ThunderboltOutlined, RetweetOutlined, NodeIndexOutlined,
  LoadingOutlined, CheckCircleOutlined, ExclamationCircleOutlined,
} from '@ant-design/icons'
import { ontologyApi } from '../api'
import api from '../api'

// Agent 颜色映射
const AGENT_COLORS: Record<string, string> = {
  EXTRACT: '#1677ff', ONTOLOGY_MAP: '#8b5cf6', BENCHMARK: '#fa8c16',
  CALC: '#52c41a', ATTRIBUTE: '#722ed1', REPORT: '#f5222d',
}
const AGENT_NAMES: Record<string, string> = {
  EXTRACT: '指标抽取', ONTOLOGY_MAP: '本体映射', BENCHMARK: '同业对比',
  CALC: '指标计算', ATTRIBUTE: '差异归因', REPORT: '报告生成',
}

export default function WorkflowOrchestration() {
  const [activeTab, setActiveTab] = useState('templates')
  const [templates, setTemplates] = useState<any[]>([])
  const [workflows, setWorkflows] = useState<any[]>([])
  const [executions, setExecutions] = useState<any[]>([])
  const [selectedWf, setSelectedWf] = useState<any>(null)
  const [execDetail, setExecDetail] = useState<any>(null)
  const [nodeExecs, setNodeExecs] = useState<any[]>([])
  const [execLoading, setExecLoading] = useState(false)

  const loadTemplates = async () => {
    try {
      const r: any = await api.get('/workflows/templates')
      setTemplates(r.data || [])
    } catch {}
  }

  const loadWorkflows = async () => {
    try {
      const r: any = await api.get('/workflows', { params: { page_size: 50 } })
      setWorkflows(r.data || [])
    } catch {}
  }

  const loadExecutions = async (wfId: number) => {
    try {
      const r: any = await api.get(`/workflows/${wfId}/executions`, { params: { page_size: 30 } })
      setExecutions(r.data || [])
    } catch {}
  }

  useEffect(() => { loadTemplates(); loadWorkflows() }, [])

  const initTemplate = async (code: string) => {
    try {
      const r: any = await api.post('/workflows/templates/init')
      message.success(`模板已初始化`)
      loadWorkflows()
    } catch (e: any) { message.error(e?.response?.data?.detail || '初始化失败') }
  }

  const executeWorkflow = async (wfId: number) => {
    setExecLoading(true)
    try {
      const r: any = await api.post(`/workflows/${wfId}/execute`, {
        bank_id: 1, indicator: '净利润', year: 2024, bank_type: '', top_n: 10,
      })
      const d = r.data || {}
      message.success(`执行完成: ${d.status || 'OK'} | 节点: ${d.nodes_executed || 0}`)
      loadExecutions(wfId)
    } catch (e: any) { message.error(e?.response?.data?.detail || '执行失败') }
    setExecLoading(false)
  }

  const viewExecDetail = async (wfId: number, execId: number) => {
    try {
      const r: any = await api.get(`/workflows/executions/${execId}/nodes`)
      setNodeExecs(r.data || [])
      setExecDetail({ wfId, execId })
    } catch {}
  }

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <h2>⚙️ 工作流编排</h2>
          <p style={{ color: '#8c8c8c', margin: 0 }}>
            串联 报告采集 → 指标提取 → 本体映射 → 同业对比 → 报告生成 → 智能对话分析
          </p>
        </Col>
        <Col>
          <Space>
            <Button icon={<ReloadOutlined />} onClick={loadWorkflows}>刷新</Button>
          </Space>
        </Col>
      </Row>

      <Card bodyStyle={{ padding: 0 }}>
        <Tabs activeKey={activeTab} onChange={setActiveTab} type="card" tabBarStyle={{ margin: 0, padding: '0 16px' }}>
          {/* === 工作流模板 === */}
          <Tabs.TabPane tab={<span><ThunderboltOutlined /> 预置模板 (4)</span>} key="templates">
            <div style={{ padding: 20 }}>
              <Row gutter={[16, 16]}>
                {templates.map(t => (
                  <Col xs={24} md={12} key={t.workflow_code}>
                    <Card
                      size="small"
                      hoverable
                      title={<span style={{ fontSize: 14 }}>{t.workflow_name}</span>}
                      extra={t.exists
                        ? <Tag color="green">已导入</Tag>
                        : <Button size="small" type="link" onClick={() => initTemplate(t.workflow_code)}>导入</Button>
                      }
                    >
                      <p style={{ fontSize: 12, color: '#8c8c8c', marginBottom: 12 }}>{t.description}</p>
                      <PipelineFlow nodes={(t.node_json?.nodes || []).map((n: any) => ({
                        label: n.label, type: n.type,
                      }))} />
                    </Card>
                  </Col>
                ))}
              </Row>
            </div>
          </Tabs.TabPane>

          {/* === 工作流列表 === */}
          <Tabs.TabPane tab={<span><ApartmentOutlined /> 工作流 ({workflows.length})</span>} key="workflows">
            <Table dataSource={workflows} rowKey="id" size="small" pagination={false}
              onRow={(record) => ({
                onClick: () => { setSelectedWf(record); loadExecutions(record.id) },
                style: { cursor: 'pointer', background: selectedWf?.id === record.id ? '#eff6ff' : undefined },
              })}
              columns={[
                { title: '名称', dataIndex: 'workflow_name', render: (v: string) => <b>{v}</b> },
                { title: '编码', dataIndex: 'workflow_code', width: 140 },
                { title: '描述', dataIndex: 'description', ellipsis: true },
                { title: '触发', dataIndex: 'trigger_type', width: 80,
                  render: (v: string) => <Tag>{v === 'MANUAL' ? '手动' : '定时'}</Tag> },
                { title: '操作', width: 160, render: (_: any, r: any) => (
                  <Space size={4}>
                    <Button size="small" type="primary" icon={<PlayCircleOutlined />} loading={execLoading}
                      onClick={(e) => { e.stopPropagation(); executeWorkflow(r.id) }}>执行</Button>
                    <Button size="small" icon={<HistoryOutlined />}
                      onClick={(e) => { e.stopPropagation(); loadExecutions(r.id); setSelectedWf(r) }}>历史</Button>
                  </Space>
                )},
              ]} />
          </Tabs.TabPane>

          {/* === 执行历史 === */}
          <Tabs.TabPane tab={<span><HistoryOutlined /> 执行历史</span>} key="history">
            {selectedWf ? (
              <div>
                <div style={{ padding: '12px 16px', background: '#fafbfc', borderBottom: '1px solid #f0f0f0' }}>
                  <b>{selectedWf.workflow_name}</b> 的执行记录
                </div>
                <Table dataSource={executions} rowKey="id" size="small" pagination={{ pageSize: 15 }}
                  columns={[
                    { title: 'ID', dataIndex: 'id', width: 50 },
                    { title: '状态', dataIndex: 'exec_status', width: 90,
                      render: (v: string) => {
                        const m: any = { COMPLETED: { color: 'green', icon: <CheckCircleOutlined /> },
                          RUNNING: { color: 'blue', icon: <LoadingOutlined /> },
                          FAILED: { color: 'red', icon: <ExclamationCircleOutlined /> } }
                        return <Tag color={m[v]?.color}>{m[v]?.icon} {v}</Tag>
                      }},
                    { title: '开始', dataIndex: 'started_at', width: 140,
                      render: (v: string) => v?.replace('T', ' ').slice(0, 19) },
                    { title: '结束', dataIndex: 'finished_at', width: 140,
                      render: (v: string) => v?.replace('T', ' ').slice(0, 19) },
                    { title: '操作', width: 80, render: (_: any, r: any) => (
                      <Button size="small" onClick={() => viewExecDetail(selectedWf.id, r.id)}>详情</Button>
                    )},
                  ]} />
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 60, color: '#bfbfbf' }}>
                请先在「工作流」Tab 中选择一个工作流查看执行历史
              </div>
            )}
          </Tabs.TabPane>
        </Tabs>
      </Card>

      {/* 执行详情 Drawer */}
      <Drawer
        title={`执行详情 #${execDetail?.execId || ''}`}
        open={!!execDetail}
        onClose={() => { setExecDetail(null); setNodeExecs([]) }}
        width={560}
      >
        <Timeline
          items={nodeExecs.map((n: any) => ({
            color: n.exec_status === 'COMPLETED' ? 'green' : n.exec_status === 'FAILED' ? 'red' : 'blue',
            children: (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <b>{AGENT_NAMES[n.node_type] || n.node_type}</b>
                  <Tag color={AGENT_COLORS[n.node_type]}>{n.node_type}</Tag>
                </div>
                <div style={{ color: '#8c8c8c', fontSize: 11 }}>节点: {n.node_id}</div>
                {n.output_json && (
                  <div style={{
                    marginTop: 8, padding: 8, background: '#f9fafb', borderRadius: 4,
                    fontSize: 11, maxHeight: 120, overflow: 'auto', fontFamily: 'monospace',
                  }}>
                    {JSON.stringify(n.output_json, null, 2).slice(0, 500)}
                  </div>
                )}
                {n.error_msg && (
                  <div style={{ color: '#dc2626', fontSize: 11, marginTop: 4 }}>❌ {n.error_msg}</div>
                )}
                <div style={{ color: '#8c8c8c', fontSize: 10, marginTop: 4 }}>
                  {n.started_at?.replace('T', ' ').slice(0, 19)} → {n.finished_at?.replace('T', ' ').slice(0, 19)}
                </div>
              </div>
            ),
          }))}
        />
      </Drawer>
    </div>
  )
}

/** 流水线可视化组件 — 展示节点串行流程 */
function PipelineFlow({ nodes }: { nodes: { label: string; type: string }[] }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, padding: '8px 0', overflowX: 'auto' }}>
      {nodes.map((n, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{
            padding: '6px 12px', borderRadius: 6, background: AGENT_COLORS[n.type] + '15',
            border: `1px solid ${AGENT_COLORS[n.type]}40`, textAlign: 'center', whiteSpace: 'nowrap',
          }}>
            <div style={{ fontSize: 10, color: AGENT_COLORS[n.type], fontWeight: 600 }}>
              {AGENT_NAMES[n.type] || n.type}
            </div>
            <div style={{ fontSize: 11, fontWeight: 500 }}>{n.label}</div>
          </div>
          {i < nodes.length - 1 && (
            <div style={{ margin: '0 4px', color: '#cbd5e1', fontSize: 16 }}>→</div>
          )}
        </div>
      ))}
    </div>
  )
}