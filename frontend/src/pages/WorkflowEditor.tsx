import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Card, Row, Col, Tag, Button, Space, Table, Modal, Input, Select,
  message, Spin, Empty, Divider, InputNumber, Tooltip, Badge, Typography, Collapse, Steps
} from 'antd'
import {
  PlayCircleOutlined, PlusOutlined, DeleteOutlined, SaveOutlined,
  ReloadOutlined, NodeIndexOutlined, CheckCircleOutlined, CloseCircleOutlined,
  ClockCircleOutlined, ExclamationCircleOutlined, FileTextOutlined,
  SearchOutlined, CalculatorOutlined, BarChartOutlined, ApartmentOutlined,
} from '@ant-design/icons'
import { workflowApi } from '../api'

const { TextArea } = Input
const { Text, Title, Paragraph } = Typography

// Agent 图标映射
const agentIcons: Record<string, any> = {
  EXTRACT: SearchOutlined,
  CALC: CalculatorOutlined,
  BENCHMARK: BarChartOutlined,
  ATTRIBUTE: ApartmentOutlined,
  REPORT: FileTextOutlined,
}

// 执行状态映射
const statusMap: Record<string, { color: string; text: string; icon: any }> = {
  PENDING: { color: 'default', text: '待执行', icon: ClockCircleOutlined },
  RUNNING: { color: 'processing', text: '执行中', icon: ReloadOutlined },
  COMPLETED: { color: 'success', text: '已完成', icon: CheckCircleOutlined },
  FAILED: { color: 'error', text: '失败', icon: CloseCircleOutlined },
  CANCELLED: { color: 'default', text: '已取消', icon: ExclamationCircleOutlined },
}

interface WorkflowNode {
  id: string
  type: string
  label: string
  config: Record<string, any>
  x?: number
  y?: number
}

interface WorkflowEdge {
  source: string
  target: string
}

export default function WorkflowEditor() {
  const [agents, setAgents] = useState<any[]>([])
  const [workflows, setWorkflows] = useState<any[]>([])
  const [currentWorkflow, setCurrentWorkflow] = useState<any>(null)
  const [nodes, setNodes] = useState<WorkflowNode[]>([])
  const [edges, setEdges] = useState<WorkflowEdge[]>([])
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null)
  const [executions, setExecutions] = useState<any[]>([])
  const [nodeExecDetails, setNodeExecDetails] = useState<any[]>([])
  const [execResult, setExecResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [showReportModal, setShowReportModal] = useState(false)
  const [reportContent, setReportContent] = useState('')
  const [newWorkflowName, setNewWorkflowName] = useState('')
  const [newWorkflowCode, setNewWorkflowCode] = useState('')
  const [execParams, setExecParams] = useState({
    bank_ids: [1, 2, 3, 4, 5, 6],
    report_year: 2025,
    report_period: 'FY',
    indicator_codes: [] as string[],
  })
  const [selectedExecId, setSelectedExecId] = useState<number | null>(null)
  const canvasRef = useRef<HTMLDivElement>(null)
  const [draggingNode, setDraggingNode] = useState<string | null>(null)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const [connecting, setConnecting] = useState<string | null>(null)
  const nextIdRef = useRef(1)

  // 加载 Agent 元数据和工作流列表
  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [agentsRes, wfRes] = await Promise.all([
        workflowApi.getAgents(),
        workflowApi.getList({ page: 1, page_size: 100 }),
      ])
      setAgents(agentsRes.data || [])
      setWorkflows(wfRes.data || [])
    } catch (e) {
      console.error('Load data error:', e)
    }
    setLoading(false)
  }, [])

  useEffect(() => { loadData() }, [loadData])

  // 加载工作流详情
  const loadWorkflow = useCallback(async (id: number) => {
    try {
      const res = await workflowApi.getDetail(id)
      if (res.data) {
        const wf = res.data
        setCurrentWorkflow(wf)
        const nj = wf.node_json || { nodes: [], edges: [] }
        // 为节点添加默认位置
        const positionedNodes = (nj.nodes || []).map((n: any, i: number) => ({
          ...n,
          x: n.x ?? 80 + (i % 3) * 220,
          y: n.y ?? 40 + Math.floor(i / 3) * 140,
        }))
        setNodes(positionedNodes)
        setEdges(nj.edges || [])
        // 加载执行历史
        const execRes = await workflowApi.getExecutions(id, { page: 1, page_size: 10 })
        setExecutions(execRes.data || [])
      }
    } catch (e) {
      console.error('Load workflow error:', e)
    }
  }, [])

  // 添加节点到画布
  const addNode = (agentType: string) => {
    const agent = agents.find(a => a.type === agentType)
    if (!agent) return
    const id = `n${nextIdRef.current++}`
    const newNode: WorkflowNode = {
      id,
      type: agentType,
      label: agent.name,
      config: {},
      x: 60 + (nodes.length % 3) * 240,
      y: 40 + Math.floor(nodes.length / 3) * 150,
    }
    setNodes([...nodes, newNode])
    setSelectedNode(newNode)
  }

  // 删除节点
  const deleteNode = (nodeId: string) => {
    setNodes(nodes.filter(n => n.id !== nodeId))
    setEdges(edges.filter(e => e.source !== nodeId && e.target !== nodeId))
    if (selectedNode?.id === nodeId) setSelectedNode(null)
  }

  // 连接节点
  const connectNodes = (source: string, target: string) => {
    if (source === target) return
    if (edges.some(e => e.source === source && e.target === target)) return
    setEdges([...edges, { source, target }])
  }

  // 拖拽节点
  const handleMouseDown = (e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation()
    const node = nodes.find(n => n.id === nodeId)
    if (!node || !canvasRef.current) return
    const rect = canvasRef.current.getBoundingClientRect()
    setDraggingNode(nodeId)
    setDragOffset({
      x: e.clientX - rect.left - (node.x || 0),
      y: e.clientY - rect.top - (node.y || 0),
    })
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!draggingNode || !canvasRef.current) return
    const rect = canvasRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left - dragOffset.x
    const y = e.clientY - rect.top - dragOffset.y
    setNodes(nodes.map(n => n.id === draggingNode ? { ...n, x: Math.max(0, x), y: Math.max(0, y) } : n))
  }

  const handleMouseUp = () => { setDraggingNode(null) }

  // 节点点击（选择或连接）
  const handleNodeClick = (nodeId: string) => {
    if (connecting) {
      connectNodes(connecting, nodeId)
      setConnecting(null)
    } else {
      const node = nodes.find(n => n.id === nodeId)
      setSelectedNode(node || null)
    }
  }

  // 保存工作流
  const saveWorkflow = async () => {
    if (!newWorkflowName || !newWorkflowCode) {
      message.warning('请填写工作流名称和编码')
      return
    }
    const data = {
      workflow_name: newWorkflowName,
      workflow_code: newWorkflowCode,
      description: '自定义工作流',
      node_json: { nodes, edges },
      trigger_type: 'MANUAL',
    }
    try {
      await workflowApi.create(data)
      message.success('工作流保存成功')
      setShowSaveModal(false)
      setNewWorkflowName('')
      setNewWorkflowCode('')
      loadData()
    } catch (e) {
      message.error('保存失败')
    }
  }

  // 更新现有工作流
  const updateWorkflow = async () => {
    if (!currentWorkflow) return
    try {
      await workflowApi.update(currentWorkflow.id, {
        node_json: { nodes, edges },
      })
      message.success('工作流已更新')
    } catch (e) {
      message.error('更新失败')
    }
  }

  // 执行工作流
  const executeWorkflow = async () => {
    if (!currentWorkflow) {
      message.warning('请先选择或创建工作流')
      return
    }
    setExecuting(true)
    setExecResult(null)
    setNodeExecDetails([])
    try {
      const res = await workflowApi.execute(currentWorkflow.id, execParams)
      setExecResult(res.data)
      if (res.data?.report_content) {
        setReportContent(res.data.report_content)
      }
      // 加载节点执行详情
      if (res.data?.exec_id) {
        setSelectedExecId(res.data.exec_id)
        const nodesRes = await workflowApi.getNodeExecutions(res.data.exec_id)
        setNodeExecDetails(nodesRes.data || [])
      }
      // 刷新执行历史
      const execRes = await workflowApi.getExecutions(currentWorkflow.id, { page: 1, page_size: 10 })
      setExecutions(execRes.data || [])
      message.success(res.data?.status === 'COMPLETED' ? '工作流执行完成' : '工作流执行失败')
    } catch (e) {
      message.error('执行失败: ' + (e as any)?.message || '未知错误')
    }
    setExecuting(false)
  }

  // 初始化模板
  const initTemplates = async () => {
    try {
      const res = await workflowApi.initTemplates()
      message.success(`已创建 ${res.data?.count || 0} 个预置模板`)
      loadData()
    } catch (e) {
      message.error('初始化失败')
    }
  }

  // 查看执行节点详情
  const viewExecDetails = async (execId: number) => {
    setSelectedExecId(execId)
    try {
      const res = await workflowApi.getNodeExecutions(execId)
      setNodeExecDetails(res.data || [])
    } catch (e) {
      console.error(e)
    }
  }

  // 清空画布
  const clearCanvas = () => {
    setNodes([])
    setEdges([])
    setSelectedNode(null)
    setCurrentWorkflow(null)
    setExecResult(null)
    setNodeExecDetails([])
    setExecutions([])
  }

  // 计算节点状态（基于执行结果）
  const getNodeStatus = (nodeId: string): string => {
    if (!execResult?.node_outputs) return ''
    return execResult.node_outputs[nodeId] ? 'COMPLETED' : ''
  }

  // 生成 SVG 连接线
  const renderEdges = () => {
    return edges.map((edge, i) => {
      const source = nodes.find(n => n.id === edge.source)
      const target = nodes.find(n => n.id === edge.target)
      if (!source || !target) return null
      const sx = (source.x || 0) + 90
      const sy = (source.y || 0) + 35
      const tx = (target.x || 0) + 90
      const ty = (target.y || 0) + 35
      const midY = (sy + ty) / 2
      return (
        <path
          key={i}
          d={`M ${sx} ${sy} C ${sx} ${midY}, ${tx} ${midY}, ${tx} ${ty}`}
          stroke="#1677ff"
          strokeWidth={2}
          fill="none"
          markerEnd="url(#arrowhead)"
          style={{ pointerEvents: 'none' }}
        />
      )
    })
  }

  const execColumns = [
    { title: '执行ID', dataIndex: 'id', width: 70 },
    { title: '状态', dataIndex: 'exec_status', width: 100,
      render: (v: string) => {
        const s = statusMap[v] || statusMap.PENDING
        return <Tag color={s.color} icon={<s.icon />}>{s.text}</Tag>
      },
    },
    { title: '开始时间', dataIndex: 'started_at', width: 160 },
    { title: '完成时间', dataIndex: 'finished_at', width: 160 },
    { title: '操作', width: 100,
      render: (_: any, record: any) => (
        <a onClick={() => viewExecDetails(record.id)}>详情</a>
      ),
    },
  ]

  const nodeExecColumns = [
    { title: '节点', dataIndex: 'node_id', width: 60 },
    { title: 'Agent类型', dataIndex: 'agent_type', width: 120,
      render: (v: string) => {
        const agent = agents.find(a => a.type === v)
        const Icon = agentIcons[v] || NodeIndexOutlined
        return <Space><Icon style={{ color: agent?.color }} /><span>{agent?.name || v}</span></Space>
      },
    },
    { title: '状态', dataIndex: 'exec_status', width: 90,
      render: (v: string) => {
        const s = statusMap[v] || statusMap.PENDING
        return <Tag color={s.color}>{s.text}</Tag>
      },
    },
    { title: '耗时', width: 80,
      render: (_: any, record: any) => {
        if (!record.started_at || !record.finished_at) return '—'
        const diff = new Date(record.finished_at).getTime() - new Date(record.started_at).getTime()
        return diff < 1000 ? `${diff}ms` : `${(diff / 1000).toFixed(1)}s`
      },
    },
    { title: '输出摘要', ellipsis: true,
      render: (_: any, record: any) => {
        const out = record.output_json?.output || {}
        if (out.indicators) return `${out.indicators.length} 个指标`
        if (out.rankings) return `${out.rankings.length} 个排名`
        if (out.decomposition) return `${out.decomposition.length} 个因子`
        if (out.report_content) return `报告 ${out.report_length || 0} 字`
        if (out.calc_results) return `${out.calc_results?.length || 0} 个计算`
        return '—'
      },
    },
  ]

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>工作流编排</h2>
          <p style={{ color: '#888', margin: 0 }}>
            基于 LangGraph 的多 Agent DAG 工作流引擎 — 拖拽编排 · 可视化执行 · 实时监控
          </p>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadData}>刷新</Button>
          <Button icon={<PlusOutlined />} onClick={initTemplates}>初始化模板</Button>
          <Button icon={<SaveOutlined />} onClick={() => setShowSaveModal(true)} disabled={nodes.length === 0}>另存为</Button>
          {currentWorkflow && (
            <Button icon={<SaveOutlined />} onClick={updateWorkflow}>更新</Button>
          )}
          <Button type="primary" icon={<PlayCircleOutlined />} onClick={executeWorkflow}
            loading={executing} disabled={!currentWorkflow}>
            执行工作流
          </Button>
        </Space>
      </div>

      {/* 当前工作流信息 */}
      {currentWorkflow && (
        <Card size="small" style={{ marginBottom: 12, background: '#e6f4ff' }}>
          <Space>
            <Badge status="processing" text={`当前工作流: ${currentWorkflow.workflow_name}`} />
            <Tag>{currentWorkflow.workflow_code}</Tag>
            <Text type="secondary">{nodes.length} 节点 · {edges.length} 连接</Text>
          </Space>
        </Card>
      )}

      <Row gutter={[12, 12]}>
        {/* 左侧: Agent 组件库 + 工作流列表 */}
        <Col span={4}>
          <Card title="Agent 组件库" size="small" style={{ marginBottom: 12 }}>
            {agents.map(a => {
              const Icon = agentIcons[a.type] || NodeIndexOutlined
              return (
                <Tooltip key={a.type} title={a.description}>
                  <div
                    onClick={() => addNode(a.type)}
                    style={{
                      padding: '8px 10px', margin: '4px 0', borderRadius: 6, cursor: 'pointer',
                      border: `1px solid ${a.color}30`, background: `${a.color}08`,
                      transition: 'all 0.2s', display: 'flex', alignItems: 'center', gap: 8,
                    }}
                    onMouseEnter={e => { e.currentTarget.style.background = `${a.color}15` }}
                    onMouseLeave={e => { e.currentTarget.style.background = `${a.color}08` }}
                  >
                    <Icon style={{ color: a.color, fontSize: 16 }} />
                    <span style={{ fontSize: 12 }}>{a.name}</span>
                  </div>
                </Tooltip>
              )
            })}
          </Card>

          <Card title="工作流列表" size="small" extra={
            <Button size="small" type="link" icon={<DeleteOutlined />} onClick={clearCanvas}>新建</Button>
          }>
            {workflows.length === 0 ? (
              <Empty description="暂无工作流" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            ) : (
              workflows.map(wf => (
                <div key={wf.id}
                  onClick={() => loadWorkflow(wf.id)}
                  style={{
                    padding: '6px 10px', margin: '2px 0', borderRadius: 4, cursor: 'pointer',
                    background: currentWorkflow?.id === wf.id ? '#e6f4ff' : 'transparent',
                    fontSize: 12,
                  }}
                >
                  <div style={{ fontWeight: 500 }}>{wf.workflow_name}</div>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {wf.node_count || 0} 节点 · {wf.workflow_code}
                  </Text>
                </div>
              ))
            )}
          </Card>
        </Col>

        {/* 中间: DAG 画布 */}
        <Col span={14}>
          <Card
            title={
              <Space>
                <NodeIndexOutlined />
                <span>DAG 工作流画布</span>
                {connecting && <Tag color="warning">点击目标节点连接</Tag>}
              </Space>
            }
            size="small"
            extra={
              <Space>
                {selectedNode && (
                  <Button size="small" danger icon={<DeleteOutlined />}
                    onClick={() => deleteNode(selectedNode.id)}>删除节点</Button>
                )}
                {selectedNode && (
                  <Button size="small" type="dashed"
                    onClick={() => { setConnecting(selectedNode.id); message.info('点击目标节点完成连接') }}>
                    连接到...
                  </Button>
                )}
                <Button size="small" onClick={clearCanvas}>清空</Button>
              </Space>
            }
          >
            <Spin spinning={loading || executing} tip={executing ? '工作流执行中...' : '加载中'}>
              <div
                ref={canvasRef}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                style={{
                  width: '100%', height: 420, position: 'relative', overflow: 'hidden',
                  background: '#fafafa', backgroundImage: 'radial-gradient(circle, #e0e0e0 1px, transparent 1px)',
                  backgroundSize: '20px 20px', borderRadius: 6, border: '1px solid #f0f0f0',
                }}
                onClick={() => { if (!connecting) setSelectedNode(null) }}
              >
                {/* SVG 连接线层 */}
                <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
                  <defs>
                    <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
                      <polygon points="0 0, 8 3, 0 6" fill="#1677ff" />
                    </marker>
                  </defs>
                  {renderEdges()}
                </svg>

                {/* 节点层 */}
                {nodes.map(node => {
                  const agent = agents.find(a => a.type === node.type)
                  const color = agent?.color || '#1677ff'
                  const Icon = agentIcons[node.type] || NodeIndexOutlined
                  const isSelected = selectedNode?.id === node.id
                  const nodeStatus = getNodeStatus(node.id)
                  const statusColor = nodeStatus === 'COMPLETED' ? '#52c41a' : ''
                  return (
                    <div
                      key={node.id}
                      onMouseDown={e => handleMouseDown(e, node.id)}
                      onClick={e => { e.stopPropagation(); handleNodeClick(node.id) }}
                      style={{
                        position: 'absolute', left: node.x || 0, top: node.y || 0,
                        width: 180, padding: '8px 12px', borderRadius: 8,
                        background: '#fff', border: `2px solid ${isSelected ? color : color + '40'}`,
                        boxShadow: isSelected ? `0 0 8px ${color}40` : '0 2px 4px rgba(0,0,0,0.06)',
                        cursor: 'move', userSelect: 'none', transition: 'box-shadow 0.2s',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Icon style={{ color, fontSize: 14 }} />
                        <span style={{ fontSize: 12, fontWeight: 600, flex: 1 }}>{node.label}</span>
                        {nodeStatus === 'COMPLETED' && (
                          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 14 }} />
                        )}
                      </div>
                      <div style={{ fontSize: 10, color: '#999', marginTop: 2 }}>
                        {node.id} · {node.type}
                      </div>
                      {node.config && Object.keys(node.config).length > 0 && (
                        <div style={{ fontSize: 10, color: color, marginTop: 2 }}>
                          {Object.entries(node.config).map(([k, v]) => `${k}=${v}`).join(', ')}
                        </div>
                      )}
                    </div>
                  )
                })}

                {nodes.length === 0 && !loading && (
                  <div style={{
                    position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
                    textAlign: 'center', color: '#bbb',
                  }}>
                    <NodeIndexOutlined style={{ fontSize: 48, marginBottom: 12 }} />
                    <div style={{ fontSize: 14 }}>点击左侧 Agent 组件添加节点</div>
                    <div style={{ fontSize: 12, marginTop: 4 }}>拖拽节点移动位置 · 选择节点后点击"连接到"建立边</div>
                  </div>
                )}
              </div>
            </Spin>
          </Card>

          {/* 执行结果 */}
          {execResult && (
            <Card title="执行结果" size="small" style={{ marginTop: 12 }}
              extra={execResult.report_content && (
                <Button type="link" size="small" onClick={() => setShowReportModal(true)}>查看报告</Button>
              )}
            >
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic title="状态" value={statusMap[execResult.status]?.text || execResult.status}
                    valueStyle={{ color: execResult.status === 'COMPLETED' ? '#52c41a' : '#ff4d4f' }} />
                </Col>
                <Col span={6}>
                  <Statistic title="执行ID" value={execResult.exec_id} />
                </Col>
                <Col span={6}>
                  <Statistic title="节点数" value={Object.keys(execResult.node_outputs || {}).length} />
                </Col>
                <Col span={6}>
                  <Statistic title="错误数" value={execResult.errors?.length || 0}
                    valueStyle={{ color: (execResult.errors?.length || 0) > 0 ? '#ff4d4f' : '#52c41a' }} />
                </Col>
              </Row>
            </Card>
          )}
        </Col>

        {/* 右侧: 属性面板 + 执行参数 */}
        <Col span={6}>
          {selectedNode ? (
            <Card title="节点属性" size="small" style={{ marginBottom: 12 }}>
              <div style={{ marginBottom: 8 }}>
                <Text type="secondary">节点ID</Text>
                <div><Tag>{selectedNode.id}</Tag></div>
              </div>
              <div style={{ marginBottom: 8 }}>
                <Text type="secondary">Agent类型</Text>
                <div>
                  <Tag color={agents.find(a => a.type === selectedNode.type)?.color}>
                    {selectedNode.type}
                  </Tag>
                </div>
              </div>
              <div style={{ marginBottom: 8 }}>
                <Text type="secondary">节点名称</Text>
                <Input size="small" value={selectedNode.label}
                  onChange={e => {
                    const updated = { ...selectedNode, label: e.target.value }
                    setSelectedNode(updated)
                    setNodes(nodes.map(n => n.id === selectedNode.id ? updated : n))
                  }} />
              </div>
              <div style={{ marginBottom: 8 }}>
                <Text type="secondary">配置参数 (JSON)</Text>
                <TextArea rows={3} size="small"
                  value={JSON.stringify(selectedNode.config, null, 2)}
                  onChange={e => {
                    try {
                      const config = JSON.parse(e.target.value)
                      const updated = { ...selectedNode, config }
                      setSelectedNode(updated)
                      setNodes(nodes.map(n => n.id === selectedNode.id ? updated : n))
                    } catch {}
                  }} />
              </div>
              <Button danger size="small" icon={<DeleteOutlined />} block onClick={() => deleteNode(selectedNode.id)}>
                删除此节点
              </Button>
            </Card>
          ) : (
            <Card title="执行参数" size="small" style={{ marginBottom: 12 }}>
              <div style={{ marginBottom: 8 }}>
                <Text type="secondary">银行ID列表</Text>
                <Select mode="tags" style={{ width: '100%' }} size="small"
                  value={execParams.bank_ids}
                  onChange={v => setExecParams({ ...execParams, bank_ids: v })} />
              </div>
              <div style={{ marginBottom: 8 }}>
                <Text type="secondary">报告年份</Text>
                <InputNumber style={{ width: '100%' }} size="small"
                  value={execParams.report_year}
                  onChange={v => setExecParams({ ...execParams, report_year: v || 2025 })} />
              </div>
              <div style={{ marginBottom: 8 }}>
                <Text type="secondary">报告周期</Text>
                <Select style={{ width: '100%' }} size="small"
                  value={execParams.report_period}
                  onChange={v => setExecParams({ ...execParams, report_period: v })}
                  options={[
                    { value: 'FY', label: '全年 (FY)' },
                    { value: 'H1', label: '半年报 (H1)' },
                    { value: 'Q1', label: '一季报 (Q1)' },
                    { value: 'Q3', label: '三季报 (Q3)' },
                  ]} />
              </div>
              <Button type="primary" icon={<PlayCircleOutlined />} block onClick={executeWorkflow}
                loading={executing} disabled={!currentWorkflow}>
                执行工作流
              </Button>
              {!currentWorkflow && (
                <div style={{ marginTop: 8, fontSize: 11, color: '#999', textAlign: 'center' }}>
                  请先选择或创建工作流
                </div>
              )}
            </Card>
          )}

          {/* Agent 描述 */}
          {selectedNode && agents.find(a => a.type === selectedNode.type) && (
            <Card title="Agent 说明" size="small" style={{ marginBottom: 12 }}>
              <Paragraph style={{ fontSize: 12, color: '#666', margin: 0 }}>
                {agents.find(a => a.type === selectedNode.type)?.description}
              </Paragraph>
              <Divider style={{ margin: '8px 0' }} />
              <div style={{ fontSize: 11 }}>
                <Text type="secondary">输入: </Text>
                <code>{agents.find(a => a.type === selectedNode.type)?.inputs.join(', ')}</code>
              </div>
              <div style={{ fontSize: 11, marginTop: 4 }}>
                <Text type="secondary">输出: </Text>
                <code>{agents.find(a => a.type === selectedNode.type)?.outputs.join(', ')}</code>
              </div>
            </Card>
          )}
        </Col>
      </Row>

      {/* 执行历史 + 节点详情 */}
      <Row gutter={[12, 12]} style={{ marginTop: 12 }}>
        <Col span={12}>
          <Card title="执行历史" size="small">
            <Table dataSource={executions} rowKey="id" size="small" pagination={false}
              columns={execColumns} scroll={{ y: 200 }}
              onRow={record => ({ onClick: () => viewExecDetails(record.id), style: { cursor: 'pointer' } })}
              locale={{ emptyText: <Empty description="暂无执行记录" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title={`节点执行详情 ${selectedExecId ? `(Exec #${selectedExecId})` : ''}`} size="small">
            <Table dataSource={nodeExecDetails} rowKey="id" size="small" pagination={false}
              columns={nodeExecColumns} scroll={{ y: 200 }}
              locale={{ emptyText: <Empty description="选择执行记录查看详情" image={Empty.PRESENTED_IMAGE_SIMPLE} /> }}
            />
          </Card>
        </Col>
      </Row>

      {/* 保存工作流 Modal */}
      <Modal title="保存工作流" open={showSaveModal} onCancel={() => setShowSaveModal(false)}
        onOk={saveWorkflow} okText="保存">
        <div style={{ marginBottom: 12 }}>
          <Text type="secondary">工作流名称</Text>
          <Input value={newWorkflowName} onChange={e => setNewWorkflowName(e.target.value)}
            placeholder="如: 六保险集团偿付能力充足率对标分析" />
        </div>
        <div>
          <Text type="secondary">工作流编码</Text>
          <Input value={newWorkflowCode} onChange={e => setNewWorkflowCode(e.target.value)}
            placeholder="如: BENCHMARK_NIM" />
        </div>
        <Divider style={{ margin: '12px 0' }} />
        <Text type="secondary">节点: {nodes.length} · 连接: {edges.length}</Text>
      </Modal>

      {/* 报告查看 Modal */}
      <Modal title="经营分析报告" open={showReportModal} onCancel={() => setShowReportModal(false)}
        footer={null} width={800} style={{ top: 20 }}>
        <div style={{ maxHeight: '70vh', overflow: 'auto', padding: '0 8px' }}>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: 14, lineHeight: 1.8 }}>
            {reportContent}
          </pre>
        </div>
      </Modal>
    </div>
  )
}

// Statistic 组件（避免额外导入）
function Statistic({ title, value, valueStyle }: { title: string; value: any; valueStyle?: any }) {
  return (
    <div>
      <div style={{ fontSize: 12, color: '#999' }}>{title}</div>
      <div style={{ fontSize: 20, fontWeight: 600, ...valueStyle }}>{value}</div>
    </div>
  )
}
