import { useState, useEffect } from 'react'
import { Card, Table, Button, Space, Tag, Modal, Form, Input, message, Select, InputNumber, Switch, Popconfirm, Typography, Row, Col, Statistic } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined, BankOutlined } from '@ant-design/icons'
import { banksApi, dictApi } from '../api'

const { Text } = Typography

export default function BankManagement() {
  const [loading, setLoading] = useState(false)
  const [banks, setBanks] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [keyword, setKeyword] = useState('')
  const [bankType, setBankType] = useState<string | undefined>()
  const [bankTypes, setBankTypes] = useState<any[]>([])
  const [typeStats, setTypeStats] = useState<any[]>([])
  
  // Modal
  const [modalVisible, setModalVisible] = useState(false)
  const [modalLoading, setModalLoading] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()

  // 加载机构类型
  useEffect(() => {
    loadBankTypes()
    loadTypeStats()
  }, [])

  // 加载保险机构列表
  const loadBanks = async () => {
    setLoading(true)
    try {
      const res: any = await banksApi.getList({
        page,
        page_size: pageSize,
        keyword,
        bank_type: bankType,
      })
      setBanks(res.data || [])
      setTotal(res.total || 0)
    } catch (e: any) {
      message.error(e.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadBanks()
  }, [page, pageSize, keyword, bankType])

  // 加载机构类型下拉
  const loadBankTypes = async () => {
    try {
      const res: any = await dictApi.getDataByCode('bank_type')
      setBankTypes(res.data || [])
    } catch (e) {
      console.error(e)
    }
  }

  // 加载类型统计
  const loadTypeStats = async () => {
    try {
      const res: any = await banksApi.getTypesStat()
      setTypeStats(res.data || [])
    } catch (e) {
      console.error(e)
    }
  }

  // 新增机构
  const handleAdd = () => {
    setEditingId(null)
    form.resetFields()
    form.setFieldsValue({ status: 1 })
    setModalVisible(true)
  }

  // 编辑机构
  const handleEdit = async (record: any) => {
    setEditingId(record.id)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  // 保存机构
  const handleSave = async () => {
    setModalLoading(true)
    try {
      const values = await form.validateFields()
      if (editingId) {
        await banksApi.update(editingId, values)
        message.success('更新成功')
      } else {
        await banksApi.create(values)
        message.success('创建成功')
      }
      setModalVisible(false)
      loadBanks()
      loadTypeStats()
    } catch (e: any) {
      message.error(e.message || '操作失败')
    } finally {
      setModalLoading(false)
    }
  }

  // 删除机构
  const handleDelete = async (id: number) => {
    try {
      await banksApi.delete(id)
      message.success('删除成功')
      loadBanks()
      loadTypeStats()
    } catch (e: any) {
      message.error(e.message || '删除失败')
    }
  }

  // 切换状态
  const handleToggleStatus = async (record: any) => {
    try {
      await banksApi.toggleStatus(record.id, record.status === 1 ? 0 : 1)
      message.success(record.status === 1 ? '已禁用' : '已启用')
      loadBanks()
    } catch (e: any) {
      message.error(e.message || '操作失败')
    }
  }

  // 表格列
  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { 
      title: '机构名称', 
      dataIndex: 'bank_name', 
      key: 'bank_name',
      render: (name: string, record: any) => (
        <Space direction="vertical" size={0}>
          <Text strong>{name}</Text>
          {record.short_name && <Text type="secondary" style={{ fontSize: 12 }}>{record.short_name}</Text>}
        </Space>
      )
    },
    { title: '机构代码', dataIndex: 'bank_code', key: 'bank_code', width: 100 },
    { 
      title: '类型', 
      dataIndex: 'bank_type', 
      key: 'bank_type',
      width: 120,
      render: (type: string) => {
        const typeItem = bankTypes.find(t => t.value === type)
        return typeItem ? <Tag color="blue">{typeItem.label}</Tag> : type
      }
    },
    { title: '股票代码', dataIndex: 'stock_code', key: 'stock_code', width: 100 },
    { title: '上市地', dataIndex: 'listing_market', key: 'listing_market', width: 80 },
    { 
      title: '总资产(亿元)', 
      dataIndex: 'total_assets', 
      key: 'total_assets',
      width: 120,
      render: (val: number) => val ? val.toLocaleString() : '-'
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: number, record: any) => (
        <Switch
          checked={status === 1}
          checkedChildren="正常"
          unCheckedChildren="禁用"
          onChange={() => handleToggleStatus(record)}
        />
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm title="确定删除?" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    },
  ]

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={4}>
          <Card>
            <Statistic title="机构总数" value={total} prefix={<BankOutlined />} />
          </Card>
        </Col>
        {typeStats.map((stat, idx) => (
          <Col key={idx} span={4}>
            <Card>
              <Statistic 
                title={stat.type_name} 
                value={stat.count} 
              />
            </Card>
          </Col>
        ))}
      </Row>

      {/* 保险机构列表 */}
      <Card
        title={<><BankOutlined /> 保险机构管理</>}
        extra={
          <Space>
            <Input.Search
              placeholder="搜索机构名称"
              style={{ width: 200 }}
              onSearch={setKeyword}
              allowClear
            />
            <Select
              placeholder="机构类型"
              style={{ width: 150 }}
              allowClear
              value={bankType}
              onChange={setBankType}
              options={bankTypes}
            />
            <Button icon={<ReloadOutlined />} onClick={() => { loadBanks(); loadTypeStats() }}>刷新</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新增机构
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={banks}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (p, ps) => { setPage(p); setPageSize(ps) },
          }}
          size="small"
        />
      </Card>

      {/* 新增/编辑 Modal */}
      <Modal
        title={editingId ? '编辑机构' : '新增机构'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        confirmLoading={modalLoading}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="bank_name" label="机构全称" rules={[{ required: true }]}>
            <Input placeholder="如: 中国人寿保险股份有限公司" />
          </Form.Item>
          <Form.Item name="short_name" label="机构简称">
            <Input placeholder="如: 中国人寿" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="bank_code" label="机构代码">
                <Input placeholder="如: ICBC" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="bank_type" label="机构类型" rules={[{ required: true }]}>
                <Select placeholder="请选择机构类型" options={bankTypes} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="stock_code" label="股票代码">
                <Input placeholder="如: 601398" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="listing_market" label="上市地">
                <Select placeholder="请选择上市地">
                  <Select.Option value="上海">上海</Select.Option>
                  <Select.Option value="深圳">深圳</Select.Option>
                  <Select.Option value="香港">香港</Select.Option>
                  <Select.Option value="纽约">纽约</Select.Option>
                  <Select.Option value="伦敦">伦敦</Select.Option>
                  <Select.Option value="其他">其他</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="total_assets" label="总资产(亿元)">
                <InputNumber style={{ width: '100%' }} placeholder="如: 420000" min={0} step={0.01} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="status" label="状态" initialValue={1}>
                <Select>
                  <Select.Option value={1}>正常</Select.Option>
                  <Select.Option value={0}>禁用</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="website" label="官网URL">
            <Input placeholder="如: https://www.icbc.com.cn" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
