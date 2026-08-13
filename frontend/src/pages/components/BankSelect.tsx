import React, { useState, useEffect } from 'react';
import { Select } from 'antd';
import { banksApi } from '../../api';

const { Option } = Select;

interface BankSelectProps {
  value?: string;  // bank_code
  onChange?: (value: string | undefined) => void;
  placeholder?: string;
  style?: React.CSSProperties;
  allowClear?: boolean;
  disabled?: boolean;
  mode?: 'multiple' | 'tags';
  maxTagCount?: number | 'responsive';
}

const BankSelect: React.FC<BankSelectProps> = ({
  value,
  onChange,
  placeholder = '请选择保险机构',
  style = { width: 200 },
  allowClear = true,
  disabled = false,
  mode,
  maxTagCount,
}) => {
  const [banks, setBanks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // 获取保险机构列表
  const fetchBanks = async () => {
    setLoading(true);
    try {
      const res = await banksApi.getList({ page_size: 200 });
      if (res.code === 0 || res.code === 200) {
        // 响应拦截器已解包response.data，res直接是PageResponse对象
        // res.data是机构数组
        const list = res.data || [];
        setBanks(list);
      }
    } catch (error) {
      console.error('获取保险机构列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBanks();
  }, []);

  return (
    <Select
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      style={style}
      allowClear={allowClear}
      disabled={disabled}
      loading={loading}
      showSearch
      optionFilterProp="children"
      mode={mode}
      maxTagCount={maxTagCount}
      // 支持模糊搜索
      filterOption={(input, option: any) =>
        (option?.bank_name ?? '').toLowerCase().includes(input.toLowerCase()) ||
        (option?.bank_code ?? '').toLowerCase().includes(input.toLowerCase()) ||
        (option?.short_name ?? '').toLowerCase().includes(input.toLowerCase())
      }
    >
      {banks.map((bank) => (
        <Option
          key={bank.bank_code}
          value={bank.bank_code}
          bank_name={bank.bank_name}
          bank_code={bank.bank_code}
          short_name={bank.short_name}
        >
          {bank.bank_name}
          {bank.short_name && bank.short_name !== bank.bank_name && ` (${bank.short_name})`}
        </Option>
      ))}
    </Select>
  );
};

export default BankSelect;
