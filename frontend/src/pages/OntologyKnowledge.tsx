/** 本体知识管理 — 完整版（类/实例/关系/映射/版本/审计/机构本体） */
import { useState, useEffect, useMemo } from 'react'
import {
  Card, Tree, Table, Tabs, Button, Space, Input, Select, Tag, Badge, Drawer, Modal, Form,
  Popconfirm, message, Statistic, Row, Col, Radio, Tooltip, Descriptions, Divider,
} from 'antd'
import {
  PlusOutlined, DeleteOutlined, EditOutlined, EyeOutlined, CheckOutlined, CloseOutlined,
  ApartmentOutlined, LinkOutlined, SwapOutlined, HistoryOutlined, AuditOutlined,
  SendOutlined, ScanOutlined, BranchesOutlined, TagsOutlined, FolderOpenOutlined,
} from '@ant-design/icons'
import { ontologyApi } from '../api'
import type { DataNode } from 'antd/es/tree'

// =================== 页面入口 ===================
export default function OntologyKnowledge() {
  const [activeTab, setActiveTab] = useState('classes')
  const [stats, setStats] = useState<any>({})
  const [loading, setLoading] = useState(false)

  const refreshStats = async () => {
    try {
      const res: any = await ontologyApi.getStats()
      setStats(res.data || {})
    } catch { /* ignore */ }
  }

  useEffect(() => { refreshStats() }, [])

  return (
    <div>
      {/* 页头 + 统计卡片 */}
      <div className="page-header" style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <h2>🧠 本体知识管理</h2>
            <p style={{ color: '#8c8c8c', margin: 0 }}>保险经营指标的本体建模 · 异构指标映射 · 保险机构本体</p>
          </Col>
          <Col>
            <Space>
              <Button icon={<ScanOutlined />} onClick={async () => {
                message.loading('正在扫描报告文件夹...')
                try { const r: any = await ontologyApi.scanBankReports(); message.success(`扫描完成：新增 ${r?.data?.new_added} 条`) } catch {}
              }}>扫描报告文件夹</Button>
              <Button type="primary" icon={<SendOutlined />}
                onClick={async () => {
                  try { const r: any = await ontologyApi.publishVersion('V1.0.0', '初版发布'); message.success('版本已发布') } catch {}
                }}>发布版本</Button>
            </Space>
          </Col>
        </Row>
      </div>

      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col xs={8}><Card size="small"><Statistic title="概念 (CLASS)" value={stats.class_count || 0} prefix={<ApartmentOutlined />} /></Card></Col>
        <Col xs={8}><Card size="small"><Statistic title="银行实例" value={stats.bank_count || 47} prefix={<BranchesOutlined />} /></Card></Col>
        <Col xs={8}><Card size="small"><Statistic title="关系" value={stats.relation_count || 0} prefix={<LinkOutlined />} /></Card></Col>
        <Col xs={8}><Card size="small"><Statistic title="异构映射" value={stats.mapping_total || 0} /></Card></Col>
        <Col xs={8}><Card size="small">
          <Statistic title="待审核映射" value={stats.mapping_pending || 0}
            valueStyle={{ color: stats.mapping_pending > 0 ? '#faad14' : undefined }} />
        </Card></Col>
        <Col xs={8}><Card size="small"><Statistic title="报告关联" value={stats.report_count || 0} prefix={<HistoryOutlined />} /></Card></Col>
      </Row>

      <Card bodyStyle={{ padding: 0 }}>
        <Tabs activeKey={activeTab} onChange={setActiveTab} type="card" tabBarStyle={{ margin: 0, padding: '0 16px' }}>
          <Tabs.TabPane tab={<span><ApartmentOutlined /> 概念管理</span>} key="classes">
            <OntologyClassManager />
          </Tabs.TabPane>
          <Tabs.TabPane tab={<span><BranchesOutlined /> 机构本体</span>} key="banks">
            <BankOntologyManager />
          </Tabs.TabPane>
          <Tabs.TabPane tab={<span><LinkOutlined /> 关系管理</span>} key="relations">
            <RelationManager />
          </Tabs.TabPane>
          <Tabs.TabPane tab={<span><SwapOutlined /> 异构映射 <Badge count={stats.mapping_pending || 0} size="small" /></span>} key="mappings">
            <MappingManager />
          </Tabs.TabPane>
          <Tabs.TabPane tab={<span><HistoryOutlined /> 版本管理</span>} key="versions">
            <VersionManager />
          </Tabs.TabPane>
          <Tabs.TabPane tab={<span><AuditOutlined /> 审计日志</span>} key="audit">
            <AuditLogViewer />
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

// =================== 1. 概念管理 ===================
function OntologyClassManager() {
  const [treeData, setTreeData] = useState<DataNode[]>([])
  const [classes, setClasses] = useState<any[]>([])
  const [selected, setSelected] = useState<any>(null)
  const [editVisible, setEditVisible] = useState(false)
  const [editData, setEditData] = useState<any>({})
  const [form] = Form.useForm()
  const [filterEntityType, setFilterEntityType] = useState<string | undefined>()

  const loadTree = async () => {
    try {
      const res: any = await ontologyApi.getClassTree(filterEntityType)
      const raw = res.data || []
      const conv = (nodes: any[]): DataNode[] =>
        nodes.map((n: any) => ({
          key: String(n.id),
          title: <span>
            {n.entity_type === 'INSTANCE' ? '🏦 ' : '📊 '}
            <b>{n.class_name}</b>
            <Tag style={{ marginLeft: 6 }} color={n.entity_type === 'INSTANCE' ? 'cyan' : 'blue'}>
              {n.class_code}
            </Tag>
          </span>,
          children: n.children?.length ? conv(n.children) : undefined,
        }))
      setTreeData(conv(raw))
    } catch { /* ignore */ }
  }

  const loadAll = async () => {
    try {
      const res: any = await ontologyApi.listClasses({ entity_type: filterEntityType })
      setClasses(res.data || [])
    } catch { /* ignore */ }
  }

  useEffect(() => { loadTree(); loadAll() }, [filterEntityType])

  const handleEdit = (item?: any) => {
    const d = item || { entity_type: filterEntityType || 'CLASS', class_level: 1, parent_id: 0 }
    setEditData(d)
    form.setFieldsValue(d)
    setEditVisible(true)
  }

  const handleSave = async () => {
    const values = await form.validateFields()
    try {
      if (editData.id) {
        await ontologyApi.updateClass(editData.id, values)
      } else {
        await ontologyApi.createClass(values)
      }
      message.success(editData.id ? '已更新' : '已创建')
      setEditVisible(false)
      loadTree()
      loadAll()
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '操作失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await ontologyApi.deleteClass(id)
      message.success('已弃用')
      setSelected(null)
      loadTree()
      loadAll()
    } catch { message.error('删除失败') }
  }

  return (
    <div style={{ display: 'flex', height: 520, padding: 16, gap: 16 }}>
      {/* 左侧树 */}
      <div style={{ width: 300, overflow: 'auto', border: '1px solid #f0f0f0', borderRadius: 8, padding: 8 }}>
        <Space style={{ marginBottom: 8 }}>
          <Select allowClear value={filterEntityType} onChange={setFilterEntityType} placeholder="类型"
            size="small" style={{ width: 120 }} popupMatchSelectWidth={false}>
            <Select.Option value="CLASS">📊 类 (CLASS)</Select.Option>
            <Select.Option value="INSTANCE">🏛️ 实例 (INSTANCE)</Select.Option>
          </Select>
          <Button size="small" icon={<PlusOutlined />} onClick={() => handleEdit()}>新建</Button>
        </Space>
        <Tree treeData={treeData} defaultExpandAll showLine blockNode
          onSelect={(keys: any[]) => {
            const c = classes.find(x => String(x.id) === keys[0])
            setSelected(c || null)
          }} />
      </div>

      {/* 右侧详情 */}
      <div style={{ flex: 1, border: '1px solid #f0f0f0', borderRadius: 8, padding: 16, overflow: 'auto' }}>
        {selected ? (
          <div>
            <Space style={{ marginBottom: 12 }}>
              <Button icon={<EditOutlined />} onClick={() => handleEdit(selected)}>编辑</Button>
              <Popconfirm title="确认弃用？" onConfirm={() => handleDelete(selected.id)}>
                <Button icon={<DeleteOutlined />} danger>弃用</Button>
              </Popconfirm>
              <Tag>{selected.entity_type}</Tag>
              <Tag color={selected.publish_status === 'PUBLISHED' ? 'green' : 'orange'}>{selected.publish_status || 'PUBLISHED'}</Tag>
            </Space>
            <Descriptions size="small" column={2}>
              <Descriptions.Item label="概念编码">{selected.class_code}</Descriptions.Item>
              <Descriptions.Item label="中文名">{selected.class_name}</Descriptions.Item>
              <Descriptions.Item label="英文名">{selected.class_name_en}</Descriptions.Item>
              <Descriptions.Item label="层级">{selected.class_level}</Descriptions.Item>
              <Descriptions.Item label="父级ID">{selected.parent_id}</Descriptions.Item>
              <Descriptions.Item label="单位">{selected.unit}</Descriptions.Item>
              <Descriptions.Item label="频度">{selected.data_frequency}</Descriptions.Item>
              <Descriptions.Item label="计算公式" span={2}>{selected.calc_formula || '—'}</Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>{selected.description || '—'}</Descriptions.Item>
            </Descriptions>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: 60, color: '#bfbfbf' }}>选择左侧概念查看详情</div>
        )}
      </div>

      {/* 编辑抽屉 */}
      <Drawer title={editData.id ? '编辑概念' : '新建概念'} width={480} open={editVisible}
        destroyOnClose
        styles={{ body: { overflow: 'visible' } }}
        onClose={() => setEditVisible(false)}
        extra={<Space><Button onClick={() => setEditVisible(false)}>取消</Button><Button type="primary" onClick={handleSave}>保存</Button></Space>}>
        <Form form={form} layout="vertical" size="small" initialValues={editData}>
          <Form.Item name="class_code" label="概念编码" rules={[{ required: true }]}>
            <Input placeholder="如 NIM" /></Form.Item>
          <Form.Item name="class_name" label="中文名" rules={[{ required: true }]}>
            <Input placeholder="如 偿付能力充足率" /></Form.Item>
          <Form.Item name="class_name_en" label="英文名">
            <Input placeholder="如 Net Interest Margin" /></Form.Item>
          <Form.Item name="entity_type" label="实体类型">
            <Select popupMatchSelectWidth={false}
              getPopupContainer={(t: any) => t?.parentElement?.parentElement || document.body}>
              <Select.Option value="CLASS">类 (CLASS)</Select.Option>
              <Select.Option value="INSTANCE">实例 (INSTANCE)</Select.Option>
            </Select></Form.Item>
          <Form.Item name="class_level" label="层级">
            <Select popupMatchSelectWidth={false}
              getPopupContainer={(t: any) => t?.parentElement?.parentElement || document.body}>
              <Select.Option value={1}>1 - 大类</Select.Option>
              <Select.Option value={2}>2 - 指标</Select.Option>
              <Select.Option value={3}>3 - 子指标</Select.Option>
            </Select></Form.Item>
          <Form.Item name="parent_id" label="父类ID"><Input type="number" /></Form.Item>
          <Form.Item name="unit" label="单位"><Input placeholder="% / 亿元" /></Form.Item>
          <Form.Item name="data_frequency" label="数据频度">
            <Select popupMatchSelectWidth={false}
              getPopupContainer={(t: any) => t?.parentElement?.parentElement || document.body}>
              <Select.Option value="ANNUAL">年度</Select.Option>
              <Select.Option value="SEMI">半年度</Select.Option>
              <Select.Option value="QUARTERLY">季度</Select.Option>
              <Select.Option value="MONTHLY">月度</Select.Option>
            </Select></Form.Item>
          <Form.Item name="calc_formula" label="计算公式"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="publish_status" label="发布状态">
            <Select popupMatchSelectWidth={false}
              getPopupContainer={(t: any) => t?.parentElement?.parentElement || document.body}>
              <Select.Option value="DRAFT">草稿</Select.Option>
              <Select.Option value="PUBLISHED">已发布</Select.Option>
              <Select.Option value="DEPRECATED">已弃用</Select.Option>
            </Select></Form.Item>
        </Form>
      </Drawer>
    </div>
  )
}

// =================== 2. 机构本体 ===================
function BankOntologyManager() {
  const [banks, setBanks] = useState<any[]>([])
  const [selected, setSelected] = useState<any>(null)
  const [bankDetail, setBankDetail] = useState<any>(null)
  const [bankFiles, setBankFiles] = useState<any>(null)
  const [fileLoading, setFileLoading] = useState(false)
  const [currentFileDir, setCurrentFileDir] = useState<string>('')
  const [bankType, setBankType] = useState<string | undefined>()
  const [keyword, setKeyword] = useState('')

  const load = async () => {
    try {
      const res: any = await ontologyApi.listBanks({ bank_type: bankType, keyword: keyword || undefined })
      setBanks(res.data || [])
    } catch (e: any) { message.error(e?.response?.data?.detail || '加载失败') }
  }

  useEffect(() => { load() }, [bankType])

  const loadDetail = async (id: number) => {
    try {
      const res: any = await ontologyApi.getBankDetail(id)
      setBankDetail(res.data || null)
      // 同时加载文件列表
      loadFiles(id, '')
    } catch { /* ignore */ }
  }

  const loadFiles = async (id: number, subpath: string) => {
    setFileLoading(true)
    try {
      const res: any = await ontologyApi.listBankFiles(id, subpath)
      setBankFiles(res.data || null)
      setCurrentFileDir(subpath)
    } catch { setBankFiles(null) }
    setFileLoading(false)
  }

  const handleDownload = (relPath: string) => {
    const url = ontologyApi.getBankFileDownloadUrl(selected?.id || 0, relPath)
    window.open(url, '_blank')
  }

  const handleOpenFileLocation = (bankName: string, typeDir?: string, file?: string) => {
    // 复制路径到剪贴板
    const base = 'C:\\保险经营\\保险经营报告下载'
    let path = typeDir ? `${base}\\${bankName}\\${typeDir}` : `${base}\\${bankName}`
    if (file) path += `\\${file}`
    navigator.clipboard.writeText(path).then(() => message.success('路径已复制: ' + path))
  }

  const columns = [
    { title: '代码', dataIndex: 'bank_code', width: 70, render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: '机构名称', dataIndex: 'bank_name', width: 160, render: (v: string) => <b>{v}</b> },
    { title: '简称', dataIndex: 'short_name', width: 80 },
    { title: '类型', dataIndex: 'bank_type', width: 90, render: (v: string) => {
      const map: any = { GROUP:'保险集团', HEALTH:'健康险', PENSION:'养老险', LIFE:'寿险', PNC:'财险', REINSURANCE:'再保险' }
      return <Tag>{map[v] || v}</Tag>
    }},
    { title: '上市', dataIndex: 'listing_market', width: 60 },
    { title: '指标', dataIndex: 'indicator_count', width: 50, render: (v: number) => <b>{v}</b> },
    { title: '报告', dataIndex: 'report_count', width: 50, render: (v: number) => <b>{v}</b> },
    { title: '操作', width: 120, render: (_: any, r: any) => (
      <Space size={4}>
        <Button size="small" icon={<EyeOutlined />} onClick={() => { setSelected(r); loadDetail(r.id) }}>详情</Button>
        <Button size="small" icon={<FolderOpenOutlined />} onClick={() => { setSelected(r); loadFiles(r.id, '') }}>
          文件
        </Button>
      </Space>
    )},
  ]

  const typeOptions = [
    { label: '全部', value: '' },
    { label: '保险集团', value: 'GROUP' },
    { label: '健康险', value: 'HEALTH' }, { label: '养老险', value: 'PENSION' }, { label: '政策性', value: 'POLICY' }, { label: '政策性', value: 'POLICY' },
    { label: '寿险', value: 'LIFE' },
    { label: '财险', value: 'PNC' },
    { label: '再保险', value: 'REINSURANCE' },
  ]

  const formatSize = (sz: number) => sz > 1024*1024 ? `${(sz/1024/1024).toFixed(1)} MB` : `${(sz/1024).toFixed(0)} KB`

  return (
    <div style={{ padding: 16 }}>
      <Space style={{ marginBottom: 12 }}>
        <Radio.Group optionType="button" value={bankType} onChange={e => setBankType(e.target.value || undefined)} options={typeOptions} size="small" />
        <Input.Search placeholder="搜索银行" value={keyword} onChange={e => setKeyword(e.target.value)} onSearch={load} style={{ width: 180 }} size="small" />
      </Space>
      <Table dataSource={banks} columns={columns} rowKey="id" size="small" pagination={false}
        scroll={{ y: 420 }} />

      {/* 银行详情 + 文件管理 Modal */}
      <Modal title={<span>🏦 {selected?.bank_name || ''} — 本体实例详情</span>}
        open={!!bankDetail} onCancel={() => { setBankDetail(null); setBankFiles(null) }}
        footer={null} width={900}>
        {bankDetail && (
          <Tabs size="small">
            <Tabs.TabPane tab="📊 关联指标" key="mappings">
              <Table dataSource={bankDetail.mappings || []} rowKey="id" size="small" pagination={false}
                columns={[
                  { title: '本地名', dataIndex: 'local_name' },
                  { title: '本体类', dataIndex: 'ontology_class_name', render: (v: string) => <Tag color="blue">{v}</Tag> },
                  { title: '映射规则', dataIndex: 'mapping_rule', width: 80 },
                  { title: '置信度', dataIndex: 'confidence', width: 60, render: (v: number) => `${(v*100).toFixed(0)}%` },
                ]} />
            </Tabs.TabPane>
            <Tabs.TabPane tab="📑 DB 报告记录" key="reports">
              <Table dataSource={bankDetail.reports || []} rowKey="id" size="small" pagination={false}
                columns={[
                  { title: '类型', dataIndex: 'report_type', width: 100 },
                  { title: '年份', dataIndex: 'report_year', width: 60 },
                  { title: '格式', dataIndex: 'file_format', width: 50 },
                  { title: '文件名', dataIndex: 'file_name', ellipsis: true },
                  { title: '大小', dataIndex: 'file_size', width: 80, render: (v: number) => formatSize(v) },
                  { title: '抽取', dataIndex: 'extraction_status', width: 70 },
                ]} />
            </Tabs.TabPane>
            <Tabs.TabPane tab={<span><FolderOpenOutlined /> 文件浏览 (磁盘)</span>} key="files">
              <BankFileBrowser
                bankName={selected?.bank_name}
                bankFiles={bankFiles}
                fileLoading={fileLoading}
                currentDir={currentFileDir}
                onEnterDir={(dir: string) => loadFiles(selected.id, dir)}
                onBack={() => loadFiles(selected.id, '')}
                onDownload={handleDownload}
                onCopyPath={(dir: string) => handleOpenFileLocation(selected.bank_name, dir)}
              />
            </Tabs.TabPane>
          </Tabs>
        )}
      </Modal>
    </div>
  )
}

/** 本地文件浏览器组件 */
function BankFileBrowser({ bankName, bankFiles, fileLoading, currentDir, onEnterDir, onBack, onDownload, onCopyPath }: {
  bankName: string, bankFiles: any, fileLoading: boolean, currentDir: string,
  onEnterDir: (dir: string) => void, onBack: () => void, onDownload: (relPath: string) => void, onCopyPath: (dir: string) => void,
}) {
  if (fileLoading) return <div style={{ textAlign: 'center', padding: 30 }}>⏳ 读取文件中...</div>
  if (!bankFiles || !bankFiles.exists) return (
    <div style={{ textAlign: 'center', padding: 30, color: '#bfbfbf' }}>
      <p>📂 报告目录未找到</p>
      <p style={{ fontSize: 11 }}>
        <Button size="small" onClick={() => onCopyPath('')}>📋 复制预期路径</Button>
      </p>
    </div>
  )

  const items = bankFiles.items || []
  const isFileList = currentDir !== ''

  return (
    <div>
      <Space style={{ marginBottom: 8 }}>
        <Button size="small" onClick={() => onCopyPath(currentDir)}>📋 复制路径</Button>
        {isFileList && <Button size="small" onClick={onBack}>⬅ 返回上级</Button>}
        <Tag>{bankName} / {currentDir || '(根目录)'}</Tag>
        <span style={{ fontSize: 11, color: '#8c8c8c' }}>{items.length} 项</span>
      </Space>

      {isFileList ? (
        <Table dataSource={items} rowKey="name" size="small" pagination={{ pageSize: 15 }}
          columns={[
            { title: '文件名', dataIndex: 'name', ellipsis: true, render: (v: string, r: any) => (
              <span>
                {r.ext === '.pdf' ? '📕' : r.ext === '.html' ? '🌐' : '📄'} {v}
              </span>
            )},
            { title: '大小', dataIndex: 'size_fmt', width: 90 },
            { title: '格式', dataIndex: 'ext', width: 50, render: (v: string) => <Tag>{v}</Tag> },
            { title: '操作', width: 120, render: (_: any, r: any) => (
              <Space size={4}>
                <Button size="small" type="link" onClick={() => onDownload(r.rel_path)}>⬇ 下载</Button>
                <Button size="small" type="link" onClick={() => onCopyPath(`${currentDir}/${r.name}`)}>📋 路径</Button>
              </Space>
            )},
          ]} />
      ) : (
        <Row gutter={[8, 8]}>
          {items.map((item: any) => (
            <Col xs={12} sm={8} md={6} key={item.name}>
              <Card
                size="small"
                hoverable
                onClick={() => onEnterDir(item.name)}
                style={{ cursor: 'pointer', textAlign: 'center' }}
              >
                <div style={{ fontSize: 24 }}>📁</div>
                <div style={{ fontSize: 12, fontWeight: 600, margin: '4px 0' }}>{item.name}</div>
                <div style={{ fontSize: 11, color: '#8c8c8c' }}>{item.file_count} 个文件</div>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </div>
  )
}

// =================== 3. 关系管理 ===================
function RelationManager() {
  const [relations, setRelations] = useState<any[]>([])
  const [relationTypes, setRelationTypes] = useState<any[]>([])
  const [classes, setClasses] = useState<any[]>([])
  const [addVisible, setAddVisible] = useState(false)
  const [addForm] = Form.useForm()
  const [filters, setFilters] = useState<any>({})

  const load = async () => {
    try {
      const [rRes, rtRes, clsRes]: any = await Promise.all([
        ontologyApi.listRelations(filters),
        ontologyApi.listRelationTypes(),
        ontologyApi.listClasses(),
      ])
      setRelations(rRes.data || [])
      setRelationTypes(rtRes.data || [])
      setClasses(clsRes.data || [])
    } catch { /* ignore */ }
  }

  useEffect(() => { load() }, [filters])

  // ID → 名称 映射表
  const classNameMap = useMemo(() => {
    const m: Record<number, string> = {}
    classes.forEach((c: any) => { m[c.id] = c.class_name })
    return m
  }, [classes])

  const handleAdd = async () => {
    const values = await addForm.validateFields()
    try {
      await ontologyApi.createRelation(values)
      message.success('关系已创建')
      setAddVisible(false)
      load()
    } catch (e: any) { message.error(e?.response?.data?.detail || '失败') }
  }

  const handleDelete = async (id: number) => {
    try { await ontologyApi.deleteRelation(id); message.success('已删除'); load() } catch { message.error('失败') }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 50 },
    { title: '类型', dataIndex: 'relation_type', width: 130,
      render: (v: string) => {
        const rt: any = relationTypes.find((x: any) => x.type_code === v)
        return <Tag color={rt?.color_hex}>{rt?.type_name || v}</Tag>
      }
    },
    { title: '源概念', dataIndex: 'source_class_id', width: 120,
      render: (v: number) => <Tag color="blue">{classNameMap[v] || `ID:${v}`}</Tag>
    },
    { title: '目标概念', dataIndex: 'target_class_id', width: 120,
      render: (v: number) => <Tag color="cyan">{classNameMap[v] || `ID:${v}`}</Tag>
    },
    { title: '描述', dataIndex: 'description', ellipsis: true },
    { title: '权重', dataIndex: 'weight', width: 60 },
    { title: '置信度', dataIndex: 'confidence', width: 70, render: (v: number) => `${(v * 100).toFixed(0)}%` },
    { title: '层级', dataIndex: 'is_instance', width: 70, render: (v: number) => v ? '实例级' : '类级' },
    { title: '操作', width: 60, render: (_: any, r: any) =>
      <Popconfirm title="确认删除？" onConfirm={() => handleDelete(r.id)}>
        <Button size="small" icon={<DeleteOutlined />} danger /></Popconfirm>
    },
  ]

  const selectProps = {
    popupMatchSelectWidth: false,
    getPopupContainer: (triggerNode: HTMLElement) =>
      triggerNode.closest('.ant-drawer-body') as HTMLElement || document.body,
  }

  return (
    <div style={{ padding: 16 }}>
      <Space style={{ marginBottom: 12 }}>
        <Select allowClear placeholder="关系类型" size="small" style={{ width: 140 }}
          onChange={(v: string) => setFilters((f: any) => ({ ...f, relation_type: v || undefined }))}>
          {relationTypes.map((rt: any) => (
            <Select.Option key={rt.type_code} value={rt.type_code}>{rt.type_name}</Select.Option>
          ))}
        </Select>
        <Select allowClear placeholder="类/实例级" size="small" style={{ width: 100 }}
          onChange={(v: number) => setFilters((f: any) => ({ ...f, is_instance: v }))}>
          <Select.Option value={0}>类级</Select.Option>
          <Select.Option value={1}>实例级</Select.Option>
        </Select>
        <Button icon={<PlusOutlined />} size="small" type="primary"
          onClick={() => { addForm.resetFields(); setAddVisible(true) }}>新建关系</Button>
      </Space>

      <Table dataSource={relations} columns={columns} rowKey="id" size="small" pagination={{ pageSize: 20 }} />

      <Drawer title="新建关系" open={addVisible} destroyOnClose
        onClose={() => setAddVisible(false)} width={420}
        styles={{ body: { overflow: 'visible' } }}
        extra={<Space><Button onClick={() => setAddVisible(false)}>取消</Button><Button type="primary" onClick={handleAdd}>创建</Button></Space>}>
        <Form form={addForm} layout="vertical" size="small">
          <Form.Item name="source_class_id" label="源概念" rules={[{ required: true }]}>
            <Select {...selectProps} showSearch allowClear placeholder="选择源概念"
              filterOption={(input, option) => (option?.children as string || '').includes(input)}>
              {classes.map((c: any) => (
                <Select.Option key={c.id} value={c.id}>{c.class_name} ({c.class_code})</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="target_class_id" label="目标概念" rules={[{ required: true }]}>
            <Select {...selectProps} showSearch allowClear placeholder="选择目标概念"
              filterOption={(input, option) => (option?.children as string || '').includes(input)}>
              {classes.map((c: any) => (
                <Select.Option key={c.id} value={c.id}>{c.class_name} ({c.class_code})</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="relation_type" label="关系类型" rules={[{ required: true }]}>
            <Select {...selectProps} placeholder="选择关系类型">
              {relationTypes.map((rt: any) => (
                <Select.Option key={rt.type_code} value={rt.type_code}>
                  <Tag color={rt.color_hex}>{rt.type_name}</Tag> {rt.type_desc}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="weight" label="权重"><Input type="number" step={0.1} /></Form.Item>
          <Form.Item name="confidence" label="置信度"><Input type="number" step={0.01} min={0} max={1} /></Form.Item>
          <Form.Item name="is_instance" label="是否实例级">
            <Select {...selectProps} placeholder="选择层级">
              <Select.Option value={0}>类级</Select.Option>
              <Select.Option value={1}>实例级</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  )
}

// =================== 4. 异构映射 ===================
function MappingManager() {
  const [mappings, setMappings] = useState<any[]>([])
  const [classes, setClasses] = useState<any[]>([])
  const [banks, setBanks] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [addVisible, setAddVisible] = useState(false)
  const [addForm] = Form.useForm()
  const [filters, setFilters] = useState<any>({})

  const load = async () => {
    setLoading(true)
    try {
      const [mRes, clsRes, bRes]: any = await Promise.all([
        ontologyApi.listMappings({ page, page_size: 20, ...filters }),
        ontologyApi.listClasses(),
        ontologyApi.listBanks(),
      ])
      setMappings(mRes.data || [])
      setTotal(mRes.total || 0)
      setClasses(clsRes.data || [])
      setBanks(bRes.data || [])
    } catch { /* ignore */ }
    setLoading(false)
  }

  useEffect(() => { load() }, [page, filters])

  // ID → 名称 映射表
  const classNameMap = useMemo(() => {
    const m: Record<number, string> = {}
    classes.forEach((c: any) => { m[c.id] = c.class_name })
    return m
  }, [classes])

  const bankNameMap = useMemo(() => {
    const m: Record<number, string> = {}
    banks.forEach((b: any) => { m[b.id] = b.bank_name })
    return m
  }, [banks])

  const handleApprove = async (id: number) => {
    try { await ontologyApi.approveMapping(id); message.success('已通过'); load() } catch { message.error('失败') }
  }

  const handleReject = async (id: number) => {
    try { await ontologyApi.rejectMapping(id); message.success('已驳回'); load() } catch { message.error('失败') }
  }

  const handleAdd = async () => {
    const values = await addForm.validateFields()
    try { await ontologyApi.createMapping(values); message.success('已创建'); setAddVisible(false); load() } catch (e: any) { message.error(e?.response?.data?.detail || '失败') }
  }

  const selectProps = {
    popupMatchSelectWidth: false,
    getPopupContainer: (triggerNode: HTMLElement) =>
      triggerNode.closest('.ant-drawer-body') as HTMLElement || document.body,
  }

  const columns = [
    { title: '机构', dataIndex: 'institution_id', width: 100,
      render: (v: number) => <Tag color="orange">{bankNameMap[v] || `ID:${v}`}</Tag>
    },
    { title: '本地指标名', dataIndex: 'local_name', width: 140, ellipsis: { showTitle: true },
      render: (v: string) => <span style={{ wordBreak: 'break-all', whiteSpace: 'normal' }}>{v}</span>
    },
    { title: '本体类', dataIndex: 'ontology_class_id', width: 110,
      render: (v: number) => <Tag color="blue">{classNameMap[v] || `ID:${v}`}</Tag>
    },
    { title: '映射规则', dataIndex: 'mapping_rule', width: 90, render: (v: string) => <Tag>{v}</Tag> },
    { title: '置信度', dataIndex: 'confidence', width: 65, render: (v: number) => `${(v * 100).toFixed(0)}%` },
    { title: '状态', dataIndex: 'verify_status', width: 80,
      render: (v: string) => <Tag color={v === 'APPROVED' ? 'green' : v === 'REJECTED' ? 'red' : 'orange'}>{v}</Tag> },
    { title: '操作', width: 120, render: (_: any, r: any) => (
      <Space>
        {r.verify_status === 'PENDING' && (
          <>
            <Button size="small" icon={<CheckOutlined />} type="link" onClick={() => handleApprove(r.id)}>通过</Button>
            <Button size="small" icon={<CloseOutlined />} type="link" danger onClick={() => handleReject(r.id)}>驳回</Button>
          </>
        )}
      </Space>
    )},
  ]

  return (
    <div style={{ padding: 16 }}>
      <Space style={{ marginBottom: 12 }}>
        <Select allowClear placeholder="映射规则" size="small" style={{ width: 120 }}
          onChange={(v: string) => setFilters((f: any) => ({ ...f, mapping_rule: v || undefined }))}>
          <Select.Option value="EXACT">EXACT</Select.Option>
          <Select.Option value="REGEX">REGEX</Select.Option>
          <Select.Option value="LLM">LLM</Select.Option>
          <Select.Option value="MANUAL">MANUAL</Select.Option>
        </Select>
        <Select allowClear placeholder="审核状态" size="small" style={{ width: 120 }}
          onChange={(v: string) => setFilters((f: any) => ({ ...f, verify_status: v || undefined }))}>
          <Select.Option value="PENDING">待审核</Select.Option>
          <Select.Option value="APPROVED">已审核</Select.Option>
          <Select.Option value="REJECTED">已驳回</Select.Option>
        </Select>
        <Select allowClear placeholder="银行" size="small" style={{ width: 120 }}
          showSearch
          filterOption={(input, option) => (option?.children as string || '').includes(input)}
          onChange={(v: number) => setFilters((f: any) => ({ ...f, institution_id: v || undefined }))}>
          {banks.map((b: any) => (
            <Select.Option key={b.id} value={b.id}>{b.bank_name}</Select.Option>
          ))}
        </Select>
        <Button icon={<PlusOutlined />} size="small" type="primary"
          onClick={() => { addForm.resetFields(); setAddVisible(true) }}>新增映射</Button>
      </Space>

      <Table dataSource={mappings} columns={columns} rowKey="id" size="small" loading={loading}
        pagination={{ current: page, total, pageSize: 20, onChange: setPage, showTotal: t => `共 ${t} 条` }} />

      <Drawer title="新增映射" open={addVisible} destroyOnClose
        onClose={() => setAddVisible(false)} width={420}
        styles={{ body: { overflow: 'visible' } }}
        extra={<Space><Button onClick={() => setAddVisible(false)}>取消</Button><Button type="primary" onClick={handleAdd}>创建</Button></Space>}>
        <Form form={addForm} layout="vertical" size="small">
          <Form.Item name="institution_id" label="保险机构" rules={[{ required: true }]}>
            <Select {...selectProps} showSearch allowClear placeholder="选择保险机构"
              filterOption={(input, option) => (option?.children as string || '').includes(input)}>
              {banks.map((b: any) => (
                <Select.Option key={b.id} value={b.id}>{b.bank_name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="local_name" label="本地指标名" rules={[{ required: true }]}><Input placeholder="如 净利差_NIM" /></Form.Item>
          <Form.Item name="ontology_class_id" label="本体类" rules={[{ required: true }]}>
            <Select {...selectProps} showSearch allowClear placeholder="选择本体类"
              filterOption={(input, option) => (option?.children as string || '').includes(input)}>
              {classes.map((c: any) => (
                <Select.Option key={c.id} value={c.id}>{c.class_name} ({c.class_code})</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="mapping_rule" label="映射规则">
            <Select {...selectProps} placeholder="选择映射规则">
              <Select.Option value="EXACT">EXACT</Select.Option>
              <Select.Option value="REGEX">REGEX</Select.Option>
              <Select.Option value="LLM">LLM</Select.Option>
              <Select.Option value="MANUAL">MANUAL</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="confidence" label="置信度"><Input type="number" step={0.01} min={0} max={1} /></Form.Item>
          <Form.Item name="source_context" label="原文片段"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="mapping_reason" label="映射理由"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Drawer>
    </div>
  )
}

// =================== 5. 版本管理 ===================
function VersionManager() {
  const [versions, setVersions] = useState<any[]>([])

  const load = async () => {
    try {
      const res: any = await ontologyApi.listVersions()
      setVersions(res.data || [])
    } catch { /* ignore */ }
  }

  useEffect(() => { load() }, [])

  const columns = [
    { title: '版本号', dataIndex: 'version_code', render: (v: string) => <b>{v}</b> },
    { title: '描述', dataIndex: 'version_desc', ellipsis: true },
    { title: '状态', dataIndex: 'publish_status', width: 100, render: (v: string) => <Tag color={v === 'PUBLISHED' ? 'green' : 'blue'}>{v}</Tag> },
    { title: '当前', dataIndex: 'is_current', width: 60, render: (v: number) => v ? <Tag color="red">当前</Tag> : '' },
    { title: '概念数', dataIndex: 'class_count', width: 70 },
    { title: '关系数', dataIndex: 'relation_count', width: 70 },
    { title: '映射数', dataIndex: 'mapping_count', width: 70 },
    { title: '发布时间', dataIndex: 'published_at', width: 160 },
  ]

  return (
    <div style={{ padding: 16 }}>
      <Table dataSource={versions} columns={columns} rowKey="id" size="small" pagination={false} />
    </div>
  )
}

// =================== 6. 审计日志 ===================
function AuditLogViewer() {
  const [logs, setLogs] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<any>({})

  const load = async () => {
    try {
      const res: any = await ontologyApi.listAuditLogs({ page, page_size: 30, ...filters })
      setLogs(res.data || [])
      setTotal(res.total || 0)
    } catch { /* ignore */ }
  }

  useEffect(() => { load() }, [page, filters])

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 50 },
    { title: '时间', dataIndex: 'created_at', width: 160, render: (v: string) => v?.replace('T', ' ').slice(0, 19) },
    { title: '操作人', dataIndex: 'operator_name', width: 80 },
    { title: '动作', dataIndex: 'action', width: 80, render: (v: string) => <Tag>{v}</Tag> },
    { title: '对象类型', dataIndex: 'entity_type', width: 100, render: (v: string) => <Tag>{v}</Tag> },
    { title: '对象ID', dataIndex: 'entity_id', width: 70 },
    { title: '说明', dataIndex: 'remark', ellipsis: true },
  ]

  return (
    <div style={{ padding: 16 }}>
      <Space style={{ marginBottom: 12 }}>
        <Select allowClear placeholder="操作" size="small" style={{ width: 100 }}
          onChange={(v: string) => setFilters((f: any) => ({ ...f, action: v || undefined }))}>
          <Select.Option value="CREATE">CREATE</Select.Option>
          <Select.Option value="UPDATE">UPDATE</Select.Option>
          <Select.Option value="DELETE">DELETE</Select.Option>
          <Select.Option value="PUBLISH">PUBLISH</Select.Option>
        </Select>
        <Select allowClear placeholder="对象类型" size="small" style={{ width: 100 }}
          onChange={(v: string) => setFilters((f: any) => ({ ...f, entity_type: v || undefined }))}>
          <Select.Option value="CLASS">CLASS</Select.Option>
          <Select.Option value="RELATION">RELATION</Select.Option>
          <Select.Option value="MAPPING">MAPPING</Select.Option>
          <Select.Option value="VERSION">VERSION</Select.Option>
        </Select>
      </Space>

      <Table dataSource={logs} columns={columns} rowKey="id" size="small"
        pagination={{ current: page, total, pageSize: 30, onChange: setPage, showTotal: t => `共 ${t} 条` }} />
    </div>
  )
}