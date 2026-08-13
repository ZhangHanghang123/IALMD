import { useEffect, useState } from 'react'
import { Card, Tree, Table, Descriptions, Tag, Spin } from 'antd'
import { indicatorsApi } from '../api'

export default function IndicatorLibrary() {
  const [categories, setCategories] = useState<any[]>([])
  const [selectedInd, setSelectedInd] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadCategories()
  }, [])

  const loadCategories = async () => {
    try {
      const res: any = await indicatorsApi.getCategories()
      setCategories(res.data || [])
      if (res.data?.[0]?.indicators?.[0]) {
        setSelectedInd(res.data[0].indicators[0])
      }
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const treeData = categories.map((cat) => ({
    title: `${cat.category_name} (${cat.count})`,
    key: cat.category_code,
    children: cat.indicators.map((ind: any) => ({
      title: ind.indicator_name,
      key: `${cat.category_code}-${ind.indicator_code}`,
      isLeaf: true,
      icon: <Tag style={{ fontSize: 10 }}>{ind.unit}</Tag>,
    })),
  }))

  return (
    <div>
      <div className="page-header"><h2>经营指标库</h2><p>管理保险经营指标体系，包含 6 大类 20+ 核心指标</p></div>
      <Spin spinning={loading}>
        <div style={{ display: 'flex', gap: 16 }}>
          <Card title="指标分类" style={{ width: 280, flexShrink: 0 }}>
            <Tree
              treeData={treeData}
              defaultExpandAll
              onSelect={(keys, info: any) => {
                if (info.node.isLeaf) {
                  const catCode = keys[0]?.toString().split('-')[0]
                  const cat = categories.find((c) => c.category_code === catCode)
                  const ind = cat?.indicators.find((i: any) => `${catCode}-${i.indicator_code}` === keys[0])
                  if (ind) setSelectedInd(ind)
                }
              }}
            />
          </Card>
          <Card title="指标详情" style={{ flex: 1 }}>
            {selectedInd ? (
              <Descriptions column={2} bordered size="small">
                <Descriptions.Item label="指标编码">{selectedInd.indicator_code}</Descriptions.Item>
                <Descriptions.Item label="指标名称">{selectedInd.indicator_name}</Descriptions.Item>
                <Descriptions.Item label="别名">{selectedInd.indicator_alias || '—'}</Descriptions.Item>
                <Descriptions.Item label="分类">
                  <Tag>{selectedInd.category_code}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="单位">{selectedInd.unit}</Descriptions.Item>
                <Descriptions.Item label="小数位">{selectedInd.decimal_places}</Descriptions.Item>
                <Descriptions.Item label="计算公式" span={2}>{selectedInd.calc_formula || '—'}</Descriptions.Item>
                <Descriptions.Item label="排序号">{selectedInd.sort_order}</Descriptions.Item>
              </Descriptions>
            ) : <div style={{ textAlign: 'center', padding: 40, color: '#bfbfbf' }}>请从左侧选择一个指标</div>}
          </Card>
        </div>
      </Spin>
    </div>
  )
}
