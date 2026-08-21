import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Avatar, Dropdown, Space, Typography } from 'antd'
import {
  DashboardOutlined, MessageOutlined, ExperimentOutlined,
  DatabaseOutlined, ApartmentOutlined, SettingOutlined,
  UserOutlined, BankOutlined, LogoutOutlined,
} from '@ant-design/icons'

// 新增图标
const IndicatorDashboardIcon = () => (
  <svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor">
    <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>
  </svg>
)

const { Header, Sider, Content, Footer } = Layout
const { Text } = Typography

const menuItems = [
  {
    key: '/group-home', label: '首页概览', icon: <DashboardOutlined />,
    children: [
      { key: '/dashboard', label: '系统仪表盘' },
      { key: '/indicator-dashboard', icon: <IndicatorDashboardIcon />, label: '指标仪表盘' },
    ],
  },
  {
    key: '/group-analysis', label: '智能分析', icon: <MessageOutlined />,
    children: [
      { key: '/chat', label: '智能对话分析' },
      { key: '/benchmark', label: '同业对比分析' },
    ],
  },
  {
    key: '/group-liquidity', label: '偿付能力管理', icon: <ExperimentOutlined />,
    children: [
      { key: '/liquidity-stress', label: '偿付能力分析' },
    ],
  },
  {
    key: '/group-data', label: '数据管理', icon: <DatabaseOutlined />,
    children: [
      { key: '/reports', label: '报告采集管理' },
      { key: '/banks', label: '保险机构管理' },
      { key: '/indicators', label: '经营指标库' },
      { key: '/indicator-values', label: '指标值维护' },
    ],
  },
  {
    key: '/group-knowledge', label: '知识引擎', icon: <ApartmentOutlined />,
    children: [
      { key: '/ontology', label: '本体知识管理' },
      { key: '/workflow', label: '工作流编排' },
    ],
  },
  {
    key: '/group-system', label: '系统管理', icon: <SettingOutlined />,
    children: [
      { key: '/dict', label: '字典管理' },
      { key: '/settings', label: '系统设置' },
    ],
  },
]

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [openKeys, setOpenKeys] = useState<string[]>(['/group-home'])
  const navigate = useNavigate()
  const location = useLocation()
  const userDisplayName = (() => {
    try {
      const u = JSON.parse(localStorage.getItem('user') || '{}')
      return u.real_name || u.username || '用户'
    } catch { return '用户' }
  })()

  // Auto-open parent menu when navigating between pages
  useEffect(() => {
    const path = location.pathname
    for (const item of menuItems) {
      if (item.children?.some((c: any) => path.startsWith(c.key))) {
        setOpenKeys(prev => {
          if (!prev.includes(item.key)) return [...prev, item.key]
          return prev
        })
        return
      }
    }
  }, [location.pathname])

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
        width={220}
        style={{ boxShadow: '2px 0 8px rgba(0,0,0,0.06)' }}
      >
        <div style={{
          height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}>
          <BankOutlined style={{ fontSize: collapsed ? 24 : 28, color: '#1677ff' }} />
          {!collapsed && (
            <Text strong style={{ color: '#fff', marginLeft: 10, fontSize: 16, whiteSpace: 'nowrap' }}>
              IALMD 保险经营分析
            </Text>
          )}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          openKeys={openKeys}
          onOpenChange={setOpenKeys}
          items={menuItems}
          onClick={({ key }) => { if (!key.startsWith('/group-')) navigate(key) }}
          style={{ marginTop: 8 }}
        />
      </Sider>

      <Layout>
        <Header style={{
          background: '#fff', padding: '0 24px', display: 'flex',
          alignItems: 'center', justifyContent: 'flex-end',
          borderBottom: '1px solid #f0f0f0', height: 56,
        }}>
          <Dropdown menu={{
            onClick: ({ key }) => {
              if (key === 'logout') {
                localStorage.removeItem('token')
                localStorage.removeItem('user')
                navigate('/login')
              }
            },
            items: [
              { key: 'profile', icon: <UserOutlined />, label: '个人信息' },
              { type: 'divider' },
              { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true },
            ],
          }}>
            <Space style={{ cursor: 'pointer' }}>
              <Avatar size="small" icon={<UserOutlined />} />
              <Text>{userDisplayName}</Text>
            </Space>
          </Dropdown>
        </Header>

        <Content style={{ margin: 16, padding: 24, background: '#fff', borderRadius: 8, minHeight: 360 }}>
          <Outlet />
        </Content>

        <Footer style={{
          textAlign: 'center',
          padding: '16px 24px',
          background: 'transparent',
          color: '#999',
          fontSize: 12,
          borderTop: '1px solid #f0f0f0',
        }}>
          <Space size={12} wrap style={{ justifyContent: 'center', display: 'flex' }}>
            <span>
              <svg viewBox="0 0 16 16" width="12" height="12" style={{ verticalAlign: '-2px', marginRight: 4 }} fill="currentColor">
                <path d="M8 1l6 2v4c0 4.418-2.866 8.418-6 9-3.134-.582-6-4.582-6-9V3l6-2zm0 2.236L4 4.618V7c0 3.314 2.068 6.34 4 7.022 1.932-.682 4-3.708 4-7.022V4.618L8 3.236zM7 9V7h2v2H7zm0 3v-1h2v1H7z"/>
              </svg>
              <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer" style={{ color: '#999' }}>
                京ICP备2026054150号-1
              </a>
            </span>
            <span style={{ color: '#ddd' }}>|</span>
            <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer" style={{ color: '#999' }}>
              京ICP备2026054150号
            </a>
          </Space>
        </Footer>
      </Layout>
    </Layout>
  )
}
