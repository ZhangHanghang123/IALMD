import { useState, useEffect, useCallback } from 'react'
import {
  Card, Table, Tag, Space, Button, Tabs, Modal, Form, Input, Select,
  InputNumber, Switch, Popconfirm, message, Tooltip
} from 'antd'
import { PlusOutlined, ReloadOutlined, ApiOutlined, EditOutlined, DeleteOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { llmConfigApi } from '../api'

// ==================== 用户管理 Tab ====================
const userColumns = [
  { title: 'ID', dataIndex: 'id', width: 50 },
  { title: '用户名', dataIndex: 'username', width: 120 },
  { title: '真实姓名', dataIndex: 'realName', width: 120 },
  { title: '角色', dataIndex: 'role', width: 120, render: (v: string) => <Tag color="blue">{v}</Tag> },
  { title: '所属机构', dataIndex: 'org', width: 160 },
  { title: '状态', dataIndex: 'status', width: 80, render: (v: string) => <Tag color={v === '启用' ? 'green' : 'red'}>{v}</Tag> },
  { title: '最后登录', dataIndex: 'lastLogin', width: 160 },
  { title: '操作', width: 120, render: () => <Space><a href="#">编辑</a><a href="#" style={{ color: '#ff4d4f' }}>停用</a></Space> },
]

const userData = [
  { id: 1, username: 'admin', realName: '系统管理员', role: '系统管理员', org: '—', status: '启用', lastLogin: '2026-07-30 09:00' },
  { id: 2, username: 'analyst01', realName: '张分析师', role: '高级分析师', org: '中国人寿', status: '启用', lastLogin: '2026-07-29 15:30' },
  { id: 3, username: 'demo', realName: '演示用户', role: '演示用户', org: '—', status: '启用', lastLogin: '2026-07-28 10:00' },
]

const dsColumns = [
  { title: '数据源名称', dataIndex: 'name', width: 150 },
  { title: '类型', dataIndex: 'type', width: 100, render: (v: string) => <Tag>{v}</Tag> },
  { title: '连接地址', dataIndex: 'host', width: 200 },
  { title: '状态', dataIndex: 'status', width: 80, render: (v: string) => <Tag color={v === '正常' ? 'green' : 'red'}>{v}</Tag> },
  { title: '最后同步', dataIndex: 'lastSync', width: 160 },
]

const dsData = [
  { name: 'MySQL 主库', type: 'MySQL', host: '127.0.0.1:3306/IALMD', status: '正常', lastSync: '2026-07-30 09:00' },
  { name: 'Redis 缓存', type: 'Redis', host: '127.0.0.1:6379', status: '正常', lastSync: '—' },
]

function UserTab() {
  return (
    <>
      <Card title="用户权限管理" style={{ marginBottom: 16 }}
        extra={<Space><Button icon={<PlusOutlined />}>新增用户</Button><Button type="primary">批量导入</Button></Space>}
      >
        <Table dataSource={userData} columns={userColumns} rowKey="id" pagination={false} size="middle" />
      </Card>
      <Card title="数据源配置">
        <Table dataSource={dsData} columns={dsColumns} rowKey="name" pagination={false} size="middle" />
      </Card>
    </>
  )
}

// ==================== LLM 配置 Tab ====================

interface LlmConfig {
  id: number
  provider_name: string
  provider_code: string
  api_key: string
  base_url: string
  model_name: string
  temperature: number
  max_tokens: number
  is_enabled: number
  is_default: number
  sort_order: number
  remark: string
}

function LlmConfigTab() {
  const [data, setData] = useState<LlmConfig[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [testing, setTesting] = useState<number | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const res: any = await llmConfigApi.getList({ page_size: 100 })
      setData(res?.data || res || [])
    } catch {
      message.error('加载 LLM 配置失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const handleOpen = (row?: LlmConfig) => {
    if (row) {
      setEditingId(row.id)
      form.setFieldsValue(row)
    } else {
      setEditingId(null)
      form.resetFields()
      form.setFieldsValue({
        temperature: 0.1,
        max_tokens: 4096,
        is_enabled: 0,
        is_default: 0,
        sort_order: 10,
      })
    }
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingId) {
        await llmConfigApi.update(editingId, values)
        message.success('更新成功')
      } else {
        await llmConfigApi.create(values)
        message.success('新增成功')
      }
      setModalOpen(false)
      fetchData()
    } catch (e: any) {
      if (e?.response?.data?.detail) {
        message.error(e.response.data.detail)
      }
    }
  }

  const handleToggle = async (id: number, enabled: number) => {
    try {
      await llmConfigApi.toggle(id, enabled)
      message.success(enabled ? '已启用' : '已禁用')
      fetchData()
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '操作失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await llmConfigApi.delete(id)
      message.success('删除成功')
      fetchData()
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '删除失败')
    }
  }

  const handleTest = async (id: number) => {
    setTesting(id)
    try {
      const res: any = await llmConfigApi.test(id)
      message.success(res?.message || '连接成功')
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '连接失败')
    } finally {
      setTesting(null)
    }
  }

  const maskApiKey = (key: string) => {
    if (!key) return <Tag color="default">未配置</Tag>
    if (key.length <= 8) return <Tag color="orange">{key.substring(0, 2) + '***' + key.slice(-2)}</Tag>
    return <Tag color="green">{key.substring(0, 4) + '****' + key.slice(-4)}</Tag>
  }

  const columns = [
    {
      title: '服务商', dataIndex: 'provider_name', width: 120,
      render: (v: string, r: LlmConfig) => (
        <Space>
          <ApiOutlined style={{ color: r.provider_code === 'mock' ? '#999' : '#1677ff' }} />
          {v}
          {r.is_default === 1 && <Tag color="blue" style={{ marginLeft: 4 }}>默认</Tag>}
        </Space>
      ),
    },
    { title: '编码', dataIndex: 'provider_code', width: 90, render: (v: string) => <Tag>{v}</Tag> },
    {
      title: 'API Key', dataIndex: 'api_key', width: 140,
      render: (v: string) => maskApiKey(v),
    },
    { title: '模型', dataIndex: 'model_name', width: 130, render: (v: string) => v || <Tag color="default">—</Tag> },
    {
      title: '温度', dataIndex: 'temperature', width: 70,
    },
    {
      title: '状态', dataIndex: 'is_enabled', width: 90,
      render: (v: number) => v === 1
        ? <Tag icon={<CheckCircleOutlined />} color="success">已启用</Tag>
        : <Tag icon={<CloseCircleOutlined />} color="default">已禁用</Tag>,
    },
    { title: '备注', dataIndex: 'remark', ellipsis: true, width: 180 },
    {
      title: '操作', width: 240,
      render: (_: any, r: LlmConfig) => (
        <Space size="small">
          <Button size="small" icon={<EditOutlined />} onClick={() => handleOpen(r)}>编辑</Button>
          <Switch
            checked={r.is_enabled === 1}
            checkedChildren="启用"
            unCheckedChildren="禁用"
            disabled={r.provider_code === 'mock'}
            onChange={(checked) => handleToggle(r.id, checked ? 1 : 0)}
          />
          <Tooltip title="测试连接">
            <Button
              size="small"
              loading={testing === r.id}
              disabled={r.provider_code === 'mock' || !r.api_key}
              onClick={() => handleTest(r.id)}
            >
              测试
            </Button>
          </Tooltip>
          {r.provider_code !== 'mock' && (
            <Popconfirm title="确定删除该配置？" onConfirm={() => handleDelete(r.id)}>
              <Button size="small" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  return (
    <Card
      title="LLM / AI 服务商配置"
      extra={
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchData}>刷新</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpen()}>
            新增配置
          </Button>
        </Space>
      }
    >
      <div style={{ marginBottom: 16, padding: '12px 16px', background: '#f6f8fa', borderRadius: 8, fontSize: 13, color: '#666', lineHeight: 1.8 }}>
        <strong>使用说明：</strong>
        <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
          <li>填写 API Key 并<strong>启用</strong>后，系统自动使用真实大模型；未启用则使用<strong>模拟模式</strong>兜底</li>
          <li>多个配置启用时，<strong>默认</strong>标记的优先使用；修改配置保存后立即生效</li>
          <li>支持 DeepSeek / 通义千问 / OpenAI 等兼容 OpenAI 接口格式的服务商</li>
        </ul>
      </div>

      <Table
        dataSource={data}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={false}
        size="middle"
      />

      <Modal
        title={editingId ? '编辑 LLM 配置' : '新增 LLM 配置'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={560}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="provider_name" label="服务商名称" rules={[{ required: true, message: '请输入' }]}>
            <Input placeholder="如 DeepSeek / 通义千问" />
          </Form.Item>
          <Form.Item name="provider_code" label="服务商编码" rules={[{ required: true, message: '请输入' }]}>
            <Input placeholder="如 deepseek / qwen" disabled={!!editingId} />
          </Form.Item>
          <Form.Item name="api_key" label="API Key">
            <Input.Password placeholder="sk-xxxxxxxx" />
          </Form.Item>
          <Form.Item name="base_url" label="API 地址">
            <Input placeholder="https://ialmd/api.deepseek.com/v1" />
          </Form.Item>
          <Form.Item name="model_name" label="模型名称">
            <Input placeholder="deepseek-chat" />
          </Form.Item>
          <Space size="large">
            <Form.Item name="temperature" label="温度">
              <InputNumber min={0} max={2} step={0.1} style={{ width: 120 }} />
            </Form.Item>
            <Form.Item name="max_tokens" label="最大Token">
              <InputNumber min={1} max={131072} step={256} style={{ width: 140 }} />
            </Form.Item>
            <Form.Item name="sort_order" label="排序号">
              <InputNumber min={0} max={999} style={{ width: 100 }} />
            </Form.Item>
          </Space>
          <Space size="large">
            <Form.Item name="is_enabled" label="启用状态" valuePropName="checked">
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            </Form.Item>
            <Form.Item name="is_default" label="设为默认" valuePropName="checked">
              <Switch checkedChildren="默认" unCheckedChildren="普通" />
            </Form.Item>
          </Space>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} placeholder="备注信息" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

// ==================== 主组件 ====================

export default function SystemSettings() {
  const tabItems = [
    { key: 'users', label: '用户与数据源', children: <UserTab /> },
    { key: 'llm', label: 'LLM 配置', children: <LlmConfigTab /> },
  ]

  return (
    <div>
      <div className="page-header"><h2>系统设置</h2><p>管理数据源连接、用户权限、LLM服务商配置</p></div>
      <Tabs items={tabItems} />
    </div>
  )
}
