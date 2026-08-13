import { useState, useEffect } from 'react'
import { Card, Table, Button, Space, Tag, Modal, Form, Input, message, Switch, Select, Popconfirm, Typography } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined, DatabaseOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { dictApi } from '../api'

const { Text } = Typography

// 字典选择组件 - 供其他页面使用
interface DictSelectProps {
  dictCode: string
  value?: string
  onChange?: (value: string) => void
  placeholder?: string
  disabled?: boolean
}

export function DictSelect({ dictCode, value, onChange, placeholder, disabled }: DictSelectProps) {
  const [options, setOptions] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (dictCode) {
      setLoading(true)
      dictApi.getDataByCode(dictCode)
        .then((res: any) => {
          setOptions(res.data || [])
        })
        .finally(() => setLoading(false))
    }
  }, [dictCode])

  return (
    <Select
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled}
      loading={loading}
      options={options.map(opt => ({
        label: opt.label,
        value: opt.value,
      }))}
      allowClear
    />
  )
}

export default function DictManagement() {
  const [loading, setLoading] = useState(false)
  const [types, setTypes] = useState<any[]>([])
  const [typeModalVisible, setTypeModalVisible] = useState(false)
  const [typeModalLoading, setTypeModalLoading] = useState(false)
  const [typeForm] = Form.useForm()
  const [editingTypeId, setEditingTypeId] = useState<number | null>(null)

  // 字典数据相关状态
  const [dataLoading, setDataLoading] = useState(false)
  const [dictData, setDictData] = useState<any[]>([])
  const [selectedTypeId, setSelectedTypeId] = useState<number | null>(null)
  const [selectedTypeName, setSelectedTypeName] = useState<string>('')
  const [dataModalVisible, setDataModalVisible] = useState(false)
  const [dataForm] = Form.useForm()
  const [editingDataId, setEditingDataId] = useState<number | null>(null)
  const [dataModalLoading, setDataModalLoading] = useState(false)

  // 加载字典类型
  const loadTypes = async () => {
    setLoading(true)
    try {
      const res: any = await dictApi.getTypes({ page_size: 100 })
      setTypes(res.data || [])
    } catch (e: any) {
      message.error(e.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTypes()
  }, [])

  // 选择字典类型，加载字典数据
  const handleSelectType = async (record: any) => {
    setSelectedTypeId(record.id)
    setSelectedTypeName(record.dict_name)
    loadDictData(record.id)
  }

  // 加载字典数据
  const loadDictData = async (typeId: number) => {
    setDataLoading(true)
    try {
      const res: any = await dictApi.getData({ dict_type_id: typeId })
      setDictData(res.data || [])
    } catch (e: any) {
      message.error(e.message || '加载失败')
    } finally {
      setDataLoading(false)
    }
  }

  // 切换字典类型状态
  const handleToggleTypeStatus = async (record: any) => {
    try {
      await dictApi.updateType(record.id, { status: record.status === 1 ? 0 : 1 })
      message.success(record.status === 1 ? '已禁用' : '已启用')
      loadTypes()
    } catch (e: any) {
      message.error(e.message || '操作失败')
    }
  }

  // 切换字典数据状态
  const handleToggleDataStatus = async (record: any) => {
    try {
      await dictApi.updateData(record.id, { status: record.status === 1 ? 0 : 1 })
      message.success(record.status === 1 ? '已禁用' : '已启用')
      if (selectedTypeId) {
        loadDictData(selectedTypeId)
      }
    } catch (e: any) {
      message.error(e.message || '操作失败')
    }
  }

  // 新增/编辑字典类型
  const handleSaveType = async () => {
    setTypeModalLoading(true)
    try {
      const values = await typeForm.validateFields()
      if (editingTypeId) {
        await dictApi.updateType(editingTypeId, values)
        message.success('更新成功')
      } else {
        await dictApi.createType(values)
        message.success('创建成功')
      }
      setTypeModalVisible(false)
      typeForm.resetFields()
      setEditingTypeId(null)
      loadTypes()
    } catch (e: any) {
      message.error(e.message || '操作失败')
    } finally {
      setTypeModalLoading(false)
    }
  }

  // 删除字典类型
  const handleDeleteType = async (id: number) => {
    try {
      await dictApi.deleteType(id)
      message.success('删除成功')
      loadTypes()
      if (selectedTypeId === id) {
        setSelectedTypeId(null)
        setDictData([])
      }
    } catch (e: any) {
      message.error(e.message || '删除失败')
    }
  }

  // 编辑字典类型
  const handleEditType = async (record: any) => {
    setEditingTypeId(record.id)
    typeForm.setFieldsValue(record)
    setTypeModalVisible(true)
  }

  // 新增字典数据
  const handleAddData = () => {
    if (!selectedTypeId) {
      message.warning('请先选择字典类型')
      return
    }
    setEditingDataId(null)
    dataForm.resetFields()
    setDataModalVisible(true)
  }

  // 编辑字典数据
  const handleEditData = (record: any) => {
    setEditingDataId(record.id)
    dataForm.setFieldsValue(record)
    setDataModalVisible(true)
  }

  // 保存字典数据
  const handleSaveData = async () => {
    setDataModalLoading(true)
    try {
      const values = await dataForm.validateFields()
      if (editingDataId) {
        await dictApi.updateData(editingDataId, values)
        message.success('更新成功')
      } else {
        await dictApi.createData({ ...values, dict_type_id: selectedTypeId })
        message.success('创建成功')
      }
      setDataModalVisible(false)
      dataForm.resetFields()
      setEditingDataId(null)
      if (selectedTypeId) {
        loadDictData(selectedTypeId)
      }
    } catch (e: any) {
      message.error(e.message || '操作失败')
    } finally {
      setDataModalLoading(false)
    }
  }

  // 删除字典数据
  const handleDeleteData = async (id: number) => {
    try {
      await dictApi.deleteData(id)
      message.success('删除成功')
      if (selectedTypeId) {
        loadDictData(selectedTypeId)
      }
    } catch (e: any) {
      message.error(e.message || '删除失败')
    }
  }

  // 字典类型表格列
  const typeColumns = [
    { title: '字典名称', dataIndex: 'dict_name', key: 'dict_name', width: 150 },
    { title: '字典编码', dataIndex: 'dict_code', key: 'dict_code', width: 150 },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: 80 },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 80,
      render: (status: number, record: any) => (
        <Switch
          checked={status === 1}
          checkedChildren="正常"
          unCheckedChildren="禁用"
          onChange={() => handleToggleTypeStatus(record)}
        />
      )
    },
    {
      title: '操作', key: 'action', width: 150,
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEditType(record)}>
            编辑
          </Button>
          <Popconfirm title="确定删除?" onConfirm={() => handleDeleteType(record.id)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    },
  ]

  // 字典数据表格列
  const dataColumns = [
    { title: '字典标签', dataIndex: 'dict_label', key: 'dict_label', width: 150,
      render: (label: string, record: any) => (
        <Space>
          <Text>{label}</Text>
          {record.status === 0 && <Tag color="default">禁用</Tag>}
        </Space>
      )
    },
    { title: '字典键值', dataIndex: 'dict_value', key: 'dict_value', width: 150,
      render: (value: string) => <Tag color="blue">{value}</Tag>
    },
    { title: '字典键名', dataIndex: 'dict_key', key: 'dict_key', width: 150 },
    { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: 80 },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 80,
      render: (status: number, record: any) => (
        <Switch
          checked={status === 1}
          checkedChildren="正常"
          unCheckedChildren="禁用"
          onChange={() => handleToggleDataStatus(record)}
        />
      )
    },
    {
      title: '操作', key: 'action', width: 150,
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEditData(record)}>
            编辑
          </Button>
          <Popconfirm title="确定删除?" onConfirm={() => handleDeleteData(record.id)}>
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
      <Card
        title={<><DatabaseOutlined /> 字典管理</>}
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={loadTypes}>刷新</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingTypeId(null); typeForm.resetFields(); setTypeModalVisible(true) }}>
              新增类型
            </Button>
          </Space>
        }
      >
        <Table
          columns={typeColumns}
          dataSource={types}
          rowKey="id"
          loading={loading}
          pagination={false}
          size="small"
          onRow={(record) => ({
            onClick: () => handleSelectType(record),
            style: { cursor: 'pointer', background: selectedTypeId === record.id ? '#e6f4ff' : undefined }
          })}
        />
      </Card>

      {/* 字典数据面板 */}
      {selectedTypeId && (
        <Card
          style={{ marginTop: 16 }}
          title={<>{selectedTypeName} - 字典数据</>}
          extra={
            <Space>
              <Button icon={<ReloadOutlined />} onClick={() => loadDictData(selectedTypeId)}>刷新</Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleAddData}>
                新增数据
              </Button>
            </Space>
          }
        >
          <Table
            columns={dataColumns}
            dataSource={dictData}
            rowKey="id"
            loading={dataLoading}
            pagination={false}
            size="small"
          />
        </Card>
      )}

      {/* 字典类型 Modal */}
      <Modal
        title={editingTypeId ? '编辑字典类型' : '新增字典类型'}
        open={typeModalVisible}
        onOk={handleSaveType}
        onCancel={() => { setTypeModalVisible(false); typeForm.resetFields(); setEditingTypeId(null) }}
        confirmLoading={typeModalLoading}
      >
        <Form form={typeForm} layout="vertical">
          <Form.Item name="dict_name" label="字典名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="dict_code" label="字典编码" rules={[{ required: true }]}>
            <Input placeholder="如: exec_status" disabled={!!editingTypeId} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="sort_order" label="排序号" initialValue={0}>
            <Input type="number" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 字典数据 Modal */}
      <Modal
        title={editingDataId ? '编辑字典数据' : '新增字典数据'}
        open={dataModalVisible}
        onOk={handleSaveData}
        onCancel={() => { setDataModalVisible(false); dataForm.resetFields(); setEditingDataId(null) }}
        confirmLoading={dataModalLoading}
      >
        <Form form={dataForm} layout="vertical">
          <Form.Item name="dict_label" label="字典标签" rules={[{ required: true }]}>
            <Input placeholder="显示名称，如: 执行中" />
          </Form.Item>
          <Form.Item name="dict_value" label="字典键值" rules={[{ required: true }]}>
            <Input placeholder="存储值，如: RUNNING" />
          </Form.Item>
          <Form.Item name="dict_key" label="字典键名" rules={[{ required: true }]}>
            <Input placeholder="键名，如: RUNNING" disabled={!!editingDataId} />
          </Form.Item>
          <Form.Item name="sort_order" label="排序号" initialValue={0}>
            <Input type="number" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
