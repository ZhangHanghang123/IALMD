import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  DatePicker,
  message,
  Tag,
  Popconfirm,
  Row,
  Col,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckOutlined,
  CloseOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { indicatorsApi } from '../api';
import BankSelect from './components/BankSelect';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Option } = Select;
const { TextArea } = Input;

interface IndicatorValue {
  id: number;
  indicator_id: number;
  indicator_name: string;
  bank_name: string;
  report_type: string;
  report_date: string;
  value: number | null;
  unit: string;
  verify_status: string;
  verify_remark?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

const IndicatorValueManage: React.FC = () => {
  const [form] = Form.useForm();
  const [data, setData] = useState<IndicatorValue[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [modalVisible, setModalVisible] = useState(false);
  const [modalTitle, setModalTitle] = useState('新增指标值');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [indicators, setIndicators] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [filters, setFilters] = useState({
    category: undefined as string | undefined,
    indicator_id: undefined as number | undefined,
    bank_code: undefined as string | undefined,
    verify_status: undefined as string | undefined,
    date_range: undefined as [string, string] | undefined,
  });

  // 报告类型选项
  const reportTypes = [
    { value: '年报', label: '年报' },
    { value: '半年报', label: '半年报' },
    { value: '一季报', label: '一季报' },
    { value: '三季报', label: '三季报' },
    { value: '业绩快报', label: '业绩快报' },
  ];

  // 审核状态选项
  const verifyStatusOptions = [
    { value: 'PENDING', label: '待审核', color: 'orange' },
    { value: 'APPROVED', label: '已通过', color: 'green' },
    { value: 'REJECTED', label: '已驳回', color: 'red' },
  ];

  // 获取指标列表
  const fetchIndicators = async () => {
    try {
      const res = await indicatorsApi.getList({ page_size: 200 });
      // axios拦截器已解包response.data，所以res = {code, data: [...], total, page, page_size, message}
      // res.data直接是指标数组，不需要再访问res.data.data
      if (res.code === 0 || res.code === 200) {
        setIndicators(res.data || []);
      }
    } catch (error) {
      console.error('获取指标列表失败:', error);
    }
  };

  // 获取指标分类（从后端API）
  const fetchCategories = async () => {
    try {
      const res = await indicatorsApi.getCategories();
      if (res.code === 0 || res.code === 200) {
        setCategories(res.data || []);
      }
    } catch (error) {
      console.error('获取指标分类失败:', error);
    }
  };

  // 获取指标值列表
  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {
        page: pagination.current,
        page_size: pagination.pageSize,
        ...filters,
      };
      const res = await indicatorsApi.getValueList(params);
      // axios拦截器已解包response.data，所以res = {code, data: [...], total, page, page_size, message}
      // res.data直接是数组，res.total是总数
      if (res.code === 0 || res.code === 200) {
        setData(res.data || []);
        setPagination({
          ...pagination,
          total: res.total || 0,
        });
      }
    } catch (error) {
      console.error('获取指标值列表失败:', error);
      message.error('获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIndicators();
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchData();
  }, [pagination.current, pagination.pageSize]);

  // 处理表格分页变化
  const handleTableChange = (newPagination: any) => {
    setPagination({
      ...pagination,
      current: newPagination.current,
      pageSize: newPagination.pageSize,
    });
  };

  // 处理筛选变化
  const handleFilterChange = (key: string, value: any) => {
    setFilters({ ...filters, [key]: value });
    setPagination({ ...pagination, current: 1 });
  };

  // 应用筛选
  const handleSearch = () => {
    setPagination({ ...pagination, current: 1 });
    fetchData();
  };

  // 重置筛选
  const handleReset = () => {
    setFilters({
      category: undefined,
      indicator_id: undefined,
      bank_code: undefined,
      verify_status: undefined,
      date_range: undefined,
    });
    setPagination({ ...pagination, current: 1 });
    fetchData();
  };

  // 打开新增弹窗
  const handleAdd = () => {
    setEditingId(null);
    setModalTitle('新增指标值');
    form.resetFields();
    setModalVisible(true);
  };

  // 打开编辑弹窗
  const handleEdit = async (record: IndicatorValue) => {
    setEditingId(record.id);
    setModalTitle('编辑指标值');
    try {
      const res = await indicatorsApi.getValueDetail(record.id);
      if (res.code === 0 || res.code === 200) {
        const detail = res.data;
        form.setFieldsValue({
          indicator_id: detail.indicator_id,
          bank_name: detail.bank_name,
          report_type: detail.report_type,
          report_date: detail.report_date ? dayjs(detail.report_date) : null,
          value: detail.value,
          unit: detail.unit,
          verify_remark: detail.verify_remark,
        });
        setModalVisible(true);
      }
    } catch (error) {
      message.error('获取详情失败');
    }
  };

  // 删除指标值
  const handleDelete = async (id: number) => {
    try {
      const res = await indicatorsApi.deleteValue(id);
      if (res.code === 0 || res.code === 200) {
        message.success('删除成功');
        fetchData();
      } else {
        message.error(res.message || '删除失败');
      }
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const params = {
        ...values,
        report_date: values.report_date ? values.report_date.format('YYYY-MM-DD') : undefined,
      };

      if (editingId) {
        const res = await indicatorsApi.updateValue(editingId, params);
        if (res.code === 0 || res.code === 200) {
          message.success('更新成功');
          setModalVisible(false);
          fetchData();
        } else {
          message.error(res.message || '更新失败');
        }
      } else {
        const res = await indicatorsApi.createValue(params);
        if (res.code === 0 || res.code === 200) {
          message.success('创建成功');
          setModalVisible(false);
          fetchData();
        } else {
          message.error(res.message || '创建失败');
        }
      }
    } catch (error) {
      console.error('提交失败:', error);
    }
  };

  // 审核通过
  const handleApprove = async (record: IndicatorValue) => {
    try {
      const res = await indicatorsApi.verifyValue(record.id, {
        verify_status: 'APPROVED',
        verify_remark: '审核通过',
      });
      if (res.code === 0 || res.code === 200) {
        message.success('审核通过');
        fetchData();
      } else {
        message.error(res.message || '操作失败');
      }
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 审核驳回
  const handleReject = async (record: IndicatorValue) => {
    try {
      const res = await indicatorsApi.verifyValue(record.id, {
        verify_status: 'REJECTED',
        verify_remark: '数据有误',
      });
      if (res.code === 0 || res.code === 200) {
        message.success('已驳回');
        fetchData();
      } else {
        message.error(res.message || '操作失败');
      }
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 表格列定义
  const columns: ColumnsType<IndicatorValue> = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
    },
    {
      title: '指标名称',
      dataIndex: 'indicator_name',
      width: 180,
      ellipsis: true,
    },
    {
      title: '机构',
      dataIndex: 'bank_name',
      width: 120,
    },
    {
      title: '报告类型',
      dataIndex: 'report_type',
      width: 90,
    },
    {
      title: '报告期',
      dataIndex: 'report_date',
      width: 100,
    },
    {
      title: '数值',
      dataIndex: 'value',
      width: 120,
      render: (value: number | null, record: IndicatorValue) => {
        if (value === null || value === undefined) return '-';
        return `${value.toLocaleString()} ${record.unit || ''}`;
      },
    },
    {
      title: '状态',
      dataIndex: 'verify_status',
      width: 90,
      render: (status: string) => {
        const statusItem = verifyStatusOptions.find((s) => s.value === status);
        return <Tag color={statusItem?.color || 'default'}>{statusItem?.label || status}</Tag>;
      },
    },
    {
      title: '审核备注',
      dataIndex: 'verify_remark',
      width: 120,
      ellipsis: true,
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      width: 160,
      render: (text: string) => text ? dayjs(text).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      fixed: 'right',
      render: (_: any, record: IndicatorValue) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          {record.verify_status === 'PENDING' && (
            <>
              <Button
                type="link"
                size="small"
                icon={<CheckOutlined />}
                onClick={() => handleApprove(record)}
                style={{ color: '#52c41a' }}
              >
                通过
              </Button>
              <Button
                type="link"
                size="small"
                icon={<CloseOutlined />}
                onClick={() => handleReject(record)}
                style={{ color: '#ff4d4f' }}
              >
                驳回
              </Button>
            </>
          )}
          <Popconfirm
            title="确定删除这条记录吗?"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title="指标值维护"
        extra={
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新增
            </Button>
            <Button icon={<ReloadOutlined />} onClick={fetchData}>
              刷新
            </Button>
          </Space>
        }
      >
        {/* 筛选区域 */}
        <div style={{ marginBottom: 16 }}>
          <Row gutter={16} style={{ marginBottom: 8 }}>
            <Col span={4}>
              <Select
                placeholder="选择分类"
                style={{ width: '100%' }}
                allowClear
                value={filters.category}
                onChange={(value) => handleFilterChange('category', value)}
              >
                {categories.map((cat: any) => (
                  <Option key={cat.category_code} value={cat.category_code}>
                    {cat.category_name}
                  </Option>
                ))}
              </Select>
            </Col>
            <Col span={4}>
              <Select
                placeholder="选择指标"
                style={{ width: '100%' }}
                allowClear
                value={filters.indicator_id}
                onChange={(value) => handleFilterChange('indicator_id', value)}
                showSearch
                optionFilterProp="children"
              >
                {indicators.map((ind: any) => (
                  <Option key={ind.id} value={ind.id}>
                    {ind.indicator_name}
                  </Option>
                ))}
              </Select>
            </Col>
            <Col span={4}>
              <BankSelect
                value={filters.bank_code}
                onChange={(value) => handleFilterChange('bank_code', value)}
                placeholder="选择保险机构"
                style={{ width: '100%' }}
                allowClear
              />
            </Col>
            <Col span={4}>
              <Select
                placeholder="审核状态"
                style={{ width: '100%' }}
                allowClear
                value={filters.verify_status}
                onChange={(value) => handleFilterChange('verify_status', value)}
              >
                {verifyStatusOptions.map((status) => (
                  <Option key={status.value} value={status.value}>
                    {status.label}
                  </Option>
                ))}
              </Select>
            </Col>
            <Col span={4}>
              <DatePicker.RangePicker
                style={{ width: '100%' }}
                onChange={(dates) => {
                  if (dates && dates[0] && dates[1]) {
                    handleFilterChange('date_range', [
                      dates[0].format('YYYY-MM-DD'),
                      dates[1].format('YYYY-MM-DD'),
                    ]);
                  } else {
                    handleFilterChange('date_range', undefined);
                  }
                }}
              />
            </Col>
            <Col span={4}>
              <Space>
                <Button type="primary" onClick={handleSearch}>
                  查询
                </Button>
                <Button onClick={handleReset}>重置</Button>
              </Space>
            </Col>
          </Row>
        </div>

        {/* 数据表格 */}
        <Table
          columns={columns}
          dataSource={data}
          loading={loading}
          rowKey="id"
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 新增/编辑弹窗 */}
      <Modal
        title={modalTitle}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            report_type: '年报',
            verify_status: 'PENDING',
          }}
        >
          <Form.Item
            name="indicator_id"
            label="指标"
            rules={[{ required: true, message: '请选择指标' }]}
          >
            <Select
              placeholder="请选择指标"
              showSearch
              optionFilterProp="children"
            >
              {indicators.map((ind: any) => (
                <Option key={ind.id} value={ind.id}>
                  {ind.indicator_name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="bank_name"
            label="银行"
            rules={[{ required: true, message: '请输入机构名称' }]}
          >
            <Input placeholder="请输入机构名称" />
          </Form.Item>

          <Form.Item
            name="report_type"
            label="报告类型"
            rules={[{ required: true, message: '请选择报告类型' }]}
          >
            <Select placeholder="请选择报告类型">
              {reportTypes.map((type) => (
                <Option key={type.value} value={type.value}>
                  {type.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="report_date"
            label="报告期"
            rules={[{ required: true, message: '请选择报告期' }]}
          >
            <DatePicker
              picker="month"
              style={{ width: '100%' }}
              placeholder="选择报告期"
              format="YYYY-MM"
            />
          </Form.Item>

          <Form.Item name="value" label="数值">
            <InputNumber
              style={{ width: '100%' }}
              placeholder="请输入数值"
              precision={2}
            />
          </Form.Item>

          <Form.Item name="unit" label="单位">
            <Input placeholder="如：亿元、%" />
          </Form.Item>

          <Form.Item name="verify_remark" label="审核备注">
            <TextArea rows={2} placeholder="请输入审核备注" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default IndicatorValueManage;
