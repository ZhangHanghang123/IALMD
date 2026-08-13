import { useState, useRef, useEffect } from 'react'
import {
  Input, Button, Space, Typography, Spin, Empty, message, Tag,
  Collapse, Tooltip,
} from 'antd'
import {
  SendOutlined, RobotOutlined, UserOutlined, PlusOutlined, DeleteOutlined,
  DownloadOutlined, ThunderboltOutlined, BarChartOutlined,
  ApartmentOutlined, CopyOutlined, FileMarkdownOutlined, FileTextOutlined,
  HistoryOutlined, DatabaseOutlined, LinkOutlined, FilePdfOutlined,
  FileExcelOutlined, GlobalOutlined, FundOutlined, BookOutlined,
} from '@ant-design/icons'
import { chatApi } from '../api'

const { TextArea } = Input
const { Text, Paragraph } = Typography

// ========== 内联图表渲染组件 ==========

function InlineBarChart({ title, items }: { title: string; items: Array<{ label: string; value: number; color?: string }> }) {
  const maxV = Math.max(...items.map(i => Math.abs(i.value)), 1)
  const colors = ['#1677ff', '#52c41a', '#fa8c16', '#722ed1', '#eb2f96', '#13c2c2', '#f5222d', '#2f54eb']
  return (
    <div style={{ margin: '10px 0', padding: 12, background: '#f8f9fc', borderRadius: 8, border: '1px solid #e8e8e8' }}>
      <Text strong style={{ fontSize: 13, marginBottom: 8, display: 'block' }}>{title}</Text>
      {items.map((item, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', marginBottom: 5, fontSize: 12 }}>
          <span style={{ width: 80, textAlign: 'right', marginRight: 8, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {item.label}
          </span>
          <div style={{ flex: 1, height: 18, background: '#f0f0f0', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: 4, transition: 'width 0.6s',
              width: `${Math.max((Math.abs(item.value) / maxV) * 100, 1)}%`,
              background: item.color || colors[i % colors.length],
            }} />
          </div>
          <span style={{ width: 72, textAlign: 'right', fontWeight: 600, marginLeft: 8, fontSize: 11 }}>
            {item.value.toLocaleString()}
          </span>
        </div>
      ))}
    </div>
  )
}

function InlineRankChart({ title, items }: { title: string; items: Array<{ name: string; value: number }> }) {
  const maxV = Math.max(...items.map(i => Math.abs(i.value)), 1)
  const rankColors = ['#faad14', '#bfbfbf', '#d48806', '#1677ff', '#1677ff']
  return (
    <div style={{ margin: '10px 0', padding: 12, background: '#f8f9fc', borderRadius: 8, border: '1px solid #e8e8e8' }}>
      <Text strong style={{ fontSize: 13, marginBottom: 8, display: 'block' }}>🏆 {title}</Text>
      {items.slice(0, 10).map((item, i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', marginBottom: 5, fontSize: 12 }}>
          <span style={{
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            width: 22, height: 22, borderRadius: 4, fontSize: 11, fontWeight: 700,
            color: '#fff', background: rankColors[i] || '#1677ff', marginRight: 8,
          }}>#{i + 1}</span>
          <span style={{ width: 80, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginRight: 8 }}>
            {item.name}
          </span>
          <div style={{ flex: 1, height: 16, background: '#f0f0f0', borderRadius: 3, overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: 3, transition: 'width 0.6s',
              width: `${Math.max((Math.abs(item.value) / maxV) * 100, 1)}%`,
              background: `linear-gradient(90deg, ${rankColors[i] || '#1677ff'}, ${rankColors[i] || '#1677ff'}88)`,
            }} />
          </div>
          <span style={{ width: 72, textAlign: 'right', fontWeight: 600, marginLeft: 8, fontSize: 11 }}>
            {item.value.toLocaleString()}
          </span>
        </div>
      ))}
    </div>
  )
}

function InlineLineChart({ title, data }: { title: string; data: Array<{ label: string; value: number }> }) {
  if (!data.length) return null
  const maxV = Math.max(...data.map(d => d.value), 1)
  const minV = Math.min(...data.map(d => d.value), 0)
  const range = maxV - minV || 1
  const h = 120; const w = 300; const pad = { t: 10, r: 10, b: 30, l: 30 }
  const pw = w - pad.l - pad.r; const ph = h - pad.t - pad.b
  const points = data.map((d, i) => ({
    x: pad.l + (i / Math.max(data.length - 1, 1)) * pw,
    y: pad.t + ph - ((d.value - minV) / range) * ph,
    label: d.label, value: d.value,
  }))
  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')
  return (
    <div style={{ margin: '10px 0', padding: 12, background: '#f8f9fc', borderRadius: 8, border: '1px solid #e8e8e8', overflow: 'hidden' }}>
      <Text strong style={{ fontSize: 13, marginBottom: 4, display: 'block' }}>📈 {title}</Text>
      <svg viewBox={`0 0 ${w} ${h}`} style={{ width: '100%', maxWidth: 320, height: 130 }}>
        <polyline points={pathD} fill="none" stroke="#1677ff" strokeWidth="2" />
        {points.map((p, i) => (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r="3" fill="#1677ff" />
            <text x={p.x} y={h - 5} textAnchor="middle" fontSize="10" fill="#8c8c8c">{p.label}</text>
          </g>
        ))}
      </svg>
    </div>
  )
}

/** 解析聊天内容中的图表标记并渲染 */
function renderContentWithCharts(content: string) {
  const mdToHtml = (text: string) => text.replace(
    /\|(?:.+\|)+\s*\n\|[-:\s|]+\|\s*\n(?:\|.+\|\s*\n?)+/g,
    (match: string) => {
      const lines = match.trim().split('\n')
      const thead = lines[0].split('|').filter((c: string) => c.trim()).map((c: string) =>
        '<th style="padding:4px 10px;border:1px solid #e8e8e8;text-align:left;font-size:12px;background:#f5f5f5">' + c.replace(/\*\*/g, '').trim() + '</th>'
      ).join('')
      const tbody = lines.slice(2).map((row: string) => {
        const cells = row.split('|').filter((c: string) => c.trim()).map((c: string) =>
          '<td style="padding:3px 10px;border:1px solid #f0f0f0;font-size:12px">' + c.trim() + '</td>'
        ).join('')
        return '<tr>' + cells + '</tr>'
      }).join('')
      return '<table style="border-collapse:collapse;margin:8px 0;width:100%"><thead><tr>' + thead + '</tr></thead><tbody>' + tbody + '</tbody></table>'
    }
  )

  const parts: Array<{ type: 'text' | 'chart'; content: any; isHtml?: boolean }> = []
  const chartRegex = /\[chart:(\w+)\]([\s\S]*?)\[\/chart\]/g
  let lastIdx = 0, match

  while ((match = chartRegex.exec(content)) !== null) {
    if (match.index > lastIdx) {
      parts.push({ type: 'text', content: mdToHtml(content.slice(lastIdx, match.index)), isHtml: true })
    }
    try {
      const chartData = JSON.parse(match[2].trim())
      parts.push({ type: 'chart', content: { chartType: match[1], ...chartData } })
    } catch {
      parts.push({ type: 'text', content: match[0] })
    }
    lastIdx = match.index + match[0].length
  }

  if (lastIdx < content.length) {
    parts.push({ type: 'text', content: mdToHtml(content.slice(lastIdx)), isHtml: true })
  }
  if (parts.length === 0) parts.push({ type: 'text', content: mdToHtml(content), isHtml: true })

  const tables = detectTables(content)
  const isBank = (n: string) => /保险|人寿|财险|产险|健康险|养老|再保险|平安|太保|人保|国寿|新华|泰康|太平|友邦|众安|阳光|中华联合/.test(n)
  for (const t of tables) {
    const valid = t.items.filter(i => i.name && i.name.length <= 20)
    if (valid.length < 2) continue
    const useRank = isBank(valid[0].name) || t.title.includes('排名') || t.title.includes('对比')
    parts.push({ type: 'chart', content: { chartType: useRank ? 'rank' : 'bar', title: t.title, items: valid } })
  }

  return parts.map((part, i) => {
    if (part.type === 'text') {
      return part.isHtml
        ? <span key={i} dangerouslySetInnerHTML={{__html: part.content}} style={{lineHeight: 1.7, whiteSpace: 'normal'}} />
        : <span key={i} style={{ whiteSpace: 'pre-wrap' }}>{part.content}</span>
    }
    const { chartType, title, items, data } = part.content
    if (items && items.length > 0) {
      if (chartType === 'bar' || chartType === 'rank') return <InlineRankChart key={i} title={title} items={items} />
      if (chartType === 'line' && data && data.length >= 2) return <InlineLineChart key={i} title={title} data={data} />
    }
    return null
  })
}

/** 检测文本中的 Markdown 表格并提取数据 */
function detectTables(text: string): Array<{ title: string; items: Array<{ name: string; value: number }> }> {
  const tables: Array<{ title: string; items: Array<{ name: string; value: number }> }> = []
  if (!text.includes('|')) return tables

  // 匹配所有表格
  const re = /\|(.+?)\|\n\|[-:\s|]+\|\n((?:\|.+?\|\n?)+)/g
  for (const m of text.matchAll(re)) {
    const body = m[2]
    const rows = body.split('\n').filter(r => r.trim() && r.includes('|'))
    if (rows.length < 2) continue

    // 标题取自表格前文字
    const prefix = text.slice(Math.max(0, (m.index ?? 0) - 120), m.index ?? 0)
    const titleM = prefix.match(/([^#*\n]{5,35})[：:]?\s*$/)
    const title = titleM ? titleM[1].trim().replace(/\*\*/g, '').slice(0, 30) : m[1].replace(/\|/g, '').trim().slice(0, 30)

    const items: Array<{ name: string; value: number }> = []
    for (const row of rows) {
      const cells = row.split('|').map(c => c.trim()).filter(Boolean)
      if (cells.length < 2) continue
      // 智能识别名称列：跳过纯数字列
      let nameCol = 0
      for (let c = 0; c < cells.length; c++) {
        const cc = cells[c].replace(/\*\*/g, '').replace(/[\d,.+\-%bpBP]/g, '').trim()
        if (cc.length >= 2) { nameCol = c; break }
      }
      const name = cells[nameCol].replace(/\*\*/g, '').trim()
      if (!name || name.length > 28) continue
      for (let c = 0; c < cells.length; c++) {
        if (c === nameCol) continue
        const n = parseFloat(cells[c].replace(/[**,*+]/g, '').replace(/%$/, ''))
        if (!isNaN(n)) { items.push({ name, value: n }); break }
      }
    }
    if (items.length >= 2) tables.push({ title, items })
  }
  return tables
}

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  tokens_used?: number
  trace_json?: any
  references?: ReferenceItem[]
}

// ========== 参考资料类型定义 ==========

interface ReferenceItem {
  type: 'report' | 'indicator' | 'external'
  title: string
  bank?: string
  year?: string
  value?: string
  category?: string
  reportType?: string
  source?: string
  detail?: string
}

/** 从 AI 回复中解析 [references] 标记 */
function parseReferences(content: string): { cleanContent: string; references: ReferenceItem[] } {
  const refRegex = /\[references\]([\s\S]*?)\[\/references\]/i
  const match = content.match(refRegex)
  if (!match) return { cleanContent: content, references: [] }

  try {
    const parsed = JSON.parse(match[1].trim())
    const items: ReferenceItem[] = (parsed.items || []).map((it: any) => ({
      type: it.type || 'external',
      title: it.title || '',
      bank: it.bank,
      year: it.year,
      value: it.value,
      category: it.category,
      reportType: it.reportType,
      source: it.source,
      detail: it.detail,
    }))
    const cleanContent = content.replace(match[0], '').trim()
    return { cleanContent, references: items }
  } catch {
    return { cleanContent: content, references: [] }
  }
}

/** 参考资料类型配置 */
const REF_TYPE_CONFIG = {
  report: { label: '机构报告', color: '#52c41a', icon: <FilePdfOutlined />, bg: '#f6ffed' },
  indicator: { label: '经营指标', color: '#1677ff', icon: <FundOutlined />, bg: '#e6f7ff' },
  external: { label: '外部数据', color: '#fa8c16', icon: <GlobalOutlined />, bg: '#fff7e6' },
}

const QUICK_ACTIONS = [
  { icon: <BarChartOutlined />, label: '对比六保险集团偿付能力充足率', color: '#1677ff' },
  { icon: <ApartmentOutlined />, label: '中国人寿不良率分析', color: '#52c41a' },
  { icon: <ThunderboltOutlined />, label: '招商银行ROE变化', color: '#fa8c16' },
  { icon: <BarChartOutlined />, label: '同业净利润排名', color: '#722ed1' },
]

export default function ChatAnalysis() {
  const [sessions, setSessions] = useState<any[]>([])
  const [activeSession, setActiveSession] = useState<number | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [sessionsLoading, setSessionsLoading] = useState(true)
  const [activeReferences, setActiveReferences] = useState<ReferenceItem[]>([])
  const [refPanelOpen, setRefPanelOpen] = useState(true)
  const [downloadingRef, setDownloadingRef] = useState<number | null>(null)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<any>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const streamingContentRef = useRef<string>('')

  useEffect(() => { loadSessions() }, [])
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    streamingContentRef.current = streamingContent
  }, [messages, streamingContent])
  useEffect(() => {
    if (activeSession) loadMessages(activeSession)
    else { setMessages([]); setStreamingContent('') }
  }, [activeSession])
  useEffect(() => () => { abortControllerRef.current?.abort() }, [])

  const loadSessions = async () => {
    setSessionsLoading(true)
    try {
      const res: any = await chatApi.getSessions()
      const list = res.data || []
      setSessions(list)
      // 自动选中最近一条对话
      if (list.length > 0 && !activeSession) {
        setActiveSession(list[0].id)
      }
    } catch {} finally {
      setSessionsLoading(false)
    }
  }

  const loadMessages = async (sessionId: number) => {
    try {
      const res: any = await chatApi.getMessages(sessionId)
      const msgs = (res.data || []).map((m: any) => {
        const { cleanContent, references } = parseReferences(m.content)
        return {
          id: m.id || Date.now(), role: m.role === 'USER' ? 'user' : 'assistant',
          content: cleanContent, timestamp: m.created_at || new Date().toISOString(),
          tokens_used: m.tokens_used, trace_json: m.trace_json,
          references: m.role !== 'USER' ? references : undefined,
        }
      })
      setMessages(msgs)
      // 恢复最新AI消息的参考资料
      const lastAI = msgs.filter((m: Message) => m.role === 'assistant' && m.references?.length).pop()
      setActiveReferences(lastAI?.references || [])
    } catch {}
  }

  const handleNewSession = async () => {
    try {
      const res: any = await chatApi.createSession()
      const newId = res.data.id
      setActiveSession(newId)
      setMessages([]); setStreamingContent(''); setActiveReferences([])
      loadSessions()
    } catch (e) {
      message.error('创建对话失败')
    }
  }

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: number) => {
    e.stopPropagation()
    try {
      await chatApi.deleteSession(sessionId)
      if (activeSession === sessionId) { setActiveSession(null); setMessages([]); setActiveReferences([]) }
      loadSessions()
      message.success('已删除')
    } catch {}
  }

  const handleSend = () => {
    if (!inputValue.trim() || !activeSession || loading) return

    const userMsg: Message = {
      id: Date.now(), role: 'user', content: inputValue,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    const sendText = inputValue
    setInputValue(''); setLoading(true); setStreamingContent('')
    abortControllerRef.current?.abort()

    let receivedDone = false
    const controller = chatApi.sendMessage(activeSession, sendText,
      (data) => {
        try {
          if (data.type === 'text') setStreamingContent(prev => prev + data.content)
          else if (data.type === 'error') setStreamingContent(prev => prev + '\n\n⚠️ ' + data.content)
          else if (data.type === 'done') {
            receivedDone = true
            const rawContent = streamingContentRef.current + (data.content || '')
            const { cleanContent, references } = parseReferences(rawContent)
            const assistantMsg: Message = {
              id: Date.now() + 1, role: 'assistant',
              content: cleanContent,
              timestamp: new Date().toISOString(),
              tokens_used: data.tokens_used, trace_json: data.context,
              references,
            }
            setMessages(prev => [...prev, assistantMsg])
            setStreamingContent(''); setLoading(false)
            if (references.length > 0) {
              setActiveReferences(references)
              setRefPanelOpen(true)
            }
          }
        } catch {}
      },
      (err) => { setStreamingContent(prev => prev + '\n\n⚠️ 连接中断'); setLoading(false) },
      () => { if (!receivedDone) setLoading(false) },
    )
    abortControllerRef.current = controller
  }

  const downloadMarkdown = (content: string) => {
    const blob = new Blob(['\uFEFF' + content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `银行分析_${new Date().toISOString().slice(0,10)}.md`
    document.body.appendChild(a); a.click()
    document.body.removeChild(a); URL.revokeObjectURL(url)
    message.success('报告已下载')
  }

  const formatTime = (ts: string) => {
    const d = new Date(ts)
    const now = new Date()
    const diff = now.getTime() - d.getTime()
    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return `${Math.floor(diff/60000)}分钟前`
    if (d.toDateString() === now.toDateString()) return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }

  const renderMessage = (msg: Message, idx: number) => {
    const isUser = msg.role === 'user'
    const isLastStreaming = !isUser && idx === messages.length && streamingContent

    return (
      <div key={msg.id} style={{
        display: 'flex', gap: 10, marginBottom: 16,
        flexDirection: isUser ? 'row-reverse' : 'row',
        alignItems: 'flex-start',
      }}>
        {/* 头像 */}
        <div style={{
          width: 34, height: 34, borderRadius: isUser ? '50%' : '12px',
          background: isUser ? 'linear-gradient(135deg, #667eea, #764ba2)' : 'linear-gradient(135deg, #ff6b35, #f7931e)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
        }}>
          {isUser ? <UserOutlined style={{ color: '#fff', fontSize: 16 }} /> : <RobotOutlined style={{ color: '#fff', fontSize: 16 }} />}
        </div>
        {/* 气泡 */}
        <div style={{
          maxWidth: '72%', padding: '12px 16px',
          borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
          background: isUser ? 'linear-gradient(135deg, #667eea, #764ba2)' : '#fff',
          boxShadow: isUser ? '0 2px 8px rgba(102,126,234,0.25)' : '0 1px 4px rgba(0,0,0,0.06)',
          border: isUser ? 'none' : '1px solid #f0f0f0',
        }}>
          <div style={{
            fontSize: 14, lineHeight: 1.7, whiteSpace: 'pre-wrap',
            color: isUser ? '#fff' : '#262626',
          }}>
            {isUser ? msg.content : renderContentWithCharts(msg.content)}
          </div>
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            marginTop: 6, fontSize: 11, color: isUser ? 'rgba(255,255,255,0.7)' : '#bfbfbf',
          }}>
            <span>{formatTime(msg.timestamp)}</span>
            {!isUser && msg.tokens_used && <span>Tokens: {msg.tokens_used}</span>}
          </div>
          {/* 操作按钮 */}
          {!isUser && (
            <div style={{ marginTop: 8, display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
              <Button type="text" size="small" icon={<CopyOutlined />} style={{ fontSize: 11, color: '#8c8c8c' }}
                onClick={() => { navigator.clipboard.writeText(msg.content); message.success('已复制') }}>
                复制
              </Button>
              <Button type="text" size="small" icon={<FileMarkdownOutlined />} style={{ fontSize: 11, color: '#8c8c8c' }}
                onClick={() => downloadMarkdown(`# 保险经营分析\n\n${msg.content}\n\n> IALMD V1.0 · ${new Date().toLocaleString('zh-CN')}`)}>
                MD
              </Button>
              <Button type="text" size="small" icon={<FileTextOutlined />} style={{ fontSize: 11, color: '#1677ff' }}
                onClick={async () => {
                  try {
                    const token = localStorage.getItem('token')
                  const resp = await fetch(`/ialmd/api/chat/sessions/${activeSession}/export?message_id=${msg.id}`, {
                      headers: { 'Authorization': `Bearer ${token}` }
                    })
                    const blob = await resp.blob()
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url; a.download = '智能对话分析报告.docx'
                    a.click(); URL.revokeObjectURL(url)
                    message.success('报告已下载')
                  } catch { message.error('下载失败') }
                }}>
                Word
              </Button>
              {msg.references && msg.references.length > 0 && (
                <Button type="text" size="small" icon={<BookOutlined />}
                  style={{ fontSize: 11, color: '#52c41a' }}
                  onClick={() => { setActiveReferences(msg.references!); setRefPanelOpen(true) }}>
                  参考({msg.references.length})
                </Button>
              )}
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 120px)', background: '#f7f8fa', borderRadius: 12, overflow: 'hidden' }}>

      {/* ── 左侧栏 ── */}
      <div style={{
        width: 260, flexShrink: 0, background: '#fff',
        borderRight: '1px solid #f0f0f0', display: 'flex', flexDirection: 'column',
      }}>
        {/* 新建按钮 */}
        <div style={{ padding: '16px 16px 12px' }}>
          <Button type="primary" block icon={<PlusOutlined />} onClick={handleNewSession}
            style={{ height: 40, borderRadius: 10, fontWeight: 600, fontSize: 14 }}>
            新建对话
          </Button>
        </div>

        {/* 对话历史 */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 4px 12px' }}>
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600, letterSpacing: 1 }}>
              <HistoryOutlined style={{ marginRight: 4 }} />对话历史
            </Text>
            <Text type="secondary" style={{ fontSize: 10 }}>{sessions.length} 条</Text>
          </div>

          {sessionsLoading ? (
            <div style={{ textAlign: 'center', padding: 20 }}><Spin size="small" /></div>
          ) : sessions.length === 0 ? (
            <Empty description="暂无对话" image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ padding: '20px 0' }} />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {sessions.map((item: any) => {
                const active = activeSession === item.id
                return (
                  <div key={item.id} onClick={() => setActiveSession(item.id)}
                    style={{
                      padding: '10px 12px', borderRadius: 10, cursor: 'pointer',
                      background: active ? '#f0f5ff' : 'transparent',
                      border: active ? '1px solid #d6e4ff' : '1px solid transparent',
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      transition: 'all 0.15s',
                    }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <Text ellipsis style={{ fontSize: 13, display: 'block', fontWeight: active ? 600 : 400, color: active ? '#1677ff' : '#262626' }}>
                        {item.title || '新对话'}
                      </Text>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {item.message_count || 0} 条消息
                      </Text>
                    </div>
                    <Button type="text" size="small" icon={<DeleteOutlined />}
                      style={{ opacity: 0, transition: 'opacity 0.15s' }}
                      className="session-del-btn"
                      onClick={(e) => handleDeleteSession(e, item.id)}
                      onMouseEnter={e => e.currentTarget.style.opacity = '1'}
                      onMouseLeave={e => e.currentTarget.style.opacity = '0'}
                    />
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* 底部快捷操作 */}
        <div style={{ padding: '12px 16px', borderTop: '1px solid #f0f0f0' }}>
          <Text type="secondary" style={{ fontSize: 11, fontWeight: 600, display: 'block', marginBottom: 8 }}>
            <ThunderboltOutlined /> 快捷提问
          </Text>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {QUICK_ACTIONS.map(q => (
              <div key={q.label} onClick={() => {
                if (!activeSession) { handleNewSession(); return }
                setInputValue(q.label)
                setTimeout(() => {
                  const ev = new Event('input', { bubbles: true }) as any
                  inputRef.current?.resizableTextArea?.textArea?.dispatchEvent(ev)
                }, 100)
              }}
                style={{
                  padding: '6px 10px', borderRadius: 8, cursor: 'pointer',
                  fontSize: 12, color: '#595959', background: '#fafafa',
                  border: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', gap: 6,
                  transition: 'all 0.15s',
                }}
                onMouseEnter={e => e.currentTarget.style.background = '#f0f5ff'}
                onMouseLeave={e => e.currentTarget.style.background = '#fafafa'}>
                <span style={{ color: q.color }}>{q.icon}</span>
                {q.label}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── 主对话区 ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* 顶栏 */}
        <div style={{
          padding: '12px 20px', background: '#fff', borderBottom: '1px solid #f0f0f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <Text strong style={{ fontSize: 14 }}>
            {activeSession ? (sessions.find(s => s.id === activeSession)?.title || '对话中') : '保险经营智能分析'}
          </Text>
          {messages.length > 0 && (
            <Space>
              <Button size="small" icon={<FileMarkdownOutlined />}
                onClick={() => {
                  const md = messages.map(m => `### ${m.role === 'user' ? '❓' : '🤖'} ${m.role}\n${m.content}\n`).join('\n---\n\n')
                  downloadMarkdown(`# 保险经营分析对话\n\n${md}\n\n> IALMD V1.0`)
                }}>
                导出MD
              </Button>
              <Button size="small" icon={<FileTextOutlined />}
                onClick={() => {
                  const txt = messages.map(m => `[${m.role}] ${m.content}`).join('\n\n---\n\n')
                  const blob = new Blob(['\uFEFF' + txt], { type: 'text/plain;charset=utf-8' })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url; a.download = `银行分析_${new Date().toISOString().slice(0,10)}.txt`
                  document.body.appendChild(a); a.click()
                  document.body.removeChild(a); URL.revokeObjectURL(url)
                  message.success('已下载')
                }}>
                导出TXT
              </Button>
            </Space>
          )}
        </div>

        {/* 消息列表 */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', background: '#f7f8fa' }}>
          {!activeSession || (messages.length === 0 && !streamingContent) ? (
            <div style={{ textAlign: 'center', padding: '80px 20px' }}>
              <div style={{
                width: 72, height: 72, borderRadius: '20px', margin: '0 auto 20px',
                background: 'linear-gradient(135deg, #ff6b35, #f7931e)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <RobotOutlined style={{ fontSize: 36, color: '#fff' }} />
              </div>
              <div style={{ fontSize: 18, fontWeight: 600, color: '#262626', marginBottom: 8 }}>
                {activeSession ? '开始对话' : '保险经营智能分析助手'}
              </div>
              <Text type="secondary">选择左侧快捷提问或输入分析问题</Text>
              {!activeSession && <div style={{ marginTop: 16 }}>
                <Button type="primary" icon={<PlusOutlined />} onClick={handleNewSession} size="large" style={{ borderRadius: 10 }}>开始新对话</Button>
              </div>}
            </div>
          ) : (
            <div>
              {messages.map((msg, idx) => renderMessage(msg, idx))}
              {streamingContent && (
                <div key="streaming" style={{
                  display: 'flex', gap: 10, marginBottom: 16, alignItems: 'flex-start',
                }}>
                  <div style={{
                    width: 34, height: 34, borderRadius: '12px', flexShrink: 0,
                    background: 'linear-gradient(135deg, #ff6b35, #f7931e)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <RobotOutlined style={{ color: '#fff', fontSize: 16 }} />
                  </div>
                  <div style={{
                    maxWidth: '72%', padding: '12px 16px',
                    borderRadius: '4px 16px 16px 16px', background: '#fff',
                    boxShadow: '0 1px 4px rgba(0,0,0,0.06)', border: '1px solid #f0f0f0',
                  }}>
                    <div style={{ fontSize: 14, lineHeight: 1.7, whiteSpace: 'pre-wrap', color: '#262626' }}>
                      {streamingContent}
                      <span className="cursor-blink" style={{
                        display: 'inline-block', width: 8, height: 16, background: '#1677ff',
                        marginLeft: 2, verticalAlign: 'middle', animation: 'blink 1s infinite',
                      }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* 输入框 */}
        {activeSession && (
          <div style={{ padding: '12px 20px', background: '#fff', borderTop: '1px solid #f0f0f0' }}>
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
              <TextArea
                ref={inputRef}
                value={inputValue}
                onChange={e => setInputValue(e.target.value)}
                onPressEnter={e => { if (!e.shiftKey) { e.preventDefault(); handleSend() } }}
                placeholder="输入分析问题，Enter 发送 / Shift+Enter 换行"
                autoSize={{ minRows: 1, maxRows: 4 }}
                disabled={loading}
                style={{ borderRadius: 12, border: '1px solid #e8e8e8', fontSize: 14 }}
              />
              <Button type="primary" icon={<SendOutlined />} onClick={handleSend}
                loading={loading}
                style={{
                  borderRadius: 12, height: 40, width: 40,
                  background: loading ? undefined : 'linear-gradient(135deg, #667eea, #764ba2)',
                  border: 'none', boxShadow: '0 2px 8px rgba(102,126,234,0.3)',
                }} />
            </div>
            <Text type="secondary" style={{ fontSize: 11, marginTop: 4, display: 'block', textAlign: 'center' }}>
              AI 分析仅供参考，请以原始报告为准
            </Text>
          </div>
        )}
      </div>

      {/* ── 右侧参考资料面板 ── */}
      {activeReferences.length > 0 && (
        <div style={{ width: 280, flexShrink: 0, background: '#fff', borderLeft: '1px solid #f0f0f0',
          display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* 面板标题 */}
          <div style={{ padding: '10px 14px', borderBottom: '1px solid #f0f0f0',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text strong style={{ fontSize: 13 }}><BookOutlined style={{ marginRight: 4 }} />参考资料</Text>
            <Space size={4}>
              <Tooltip title="导出Excel">
                <Button type="text" size="small" icon={<FileExcelOutlined />}
                  onClick={() => {
                    const session = sessions.find(s => s.id === activeSession)
                    chatApi.exportReferences(activeReferences, session?.title || '智能对话分析')
                      .then(() => message.success('参考资料已导出'))
                      .catch(() => message.error('导出失败'))
                  }} />
              </Tooltip>
              <Button type="text" size="small" onClick={() => setActiveReferences([])}>✕</Button>
            </Space>
          </div>

          {/* 参考项列表 */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '8px 10px' }}>
            {activeReferences.map((item, idx) => (
              <div key={idx} style={{
                padding: '8px 10px', marginBottom: 6, borderRadius: 8,
                background: REF_TYPE_CONFIG[item.type]?.bg || '#fafafa',
                border: `1px solid ${REF_TYPE_CONFIG[item.type]?.color || '#e8e8e8'}20`,
                fontSize: 12, position: 'relative',
              }}>
                {/* 类型标签 */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 4 }}>
                  <Tag color={REF_TYPE_CONFIG[item.type]?.color}
                    style={{ fontSize: 10, lineHeight: '16px', margin: 0 }}>
                    {REF_TYPE_CONFIG[item.type]?.icon}
                    <span style={{ marginLeft: 2 }}>{REF_TYPE_CONFIG[item.type]?.label}</span>
                  </Tag>
                  {item.year && <Text type="secondary" style={{ fontSize: 10 }}>{item.year}</Text>}
                </div>

                {/* 标题 */}
                <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 2, lineHeight: 1.4 }}>
                  {item.title}
                </Text>

                {/* 详情信息 */}
                <div style={{ fontSize: 11, color: '#8c8c8c', lineHeight: 1.6 }}>
                  {item.bank && <span><ApartmentOutlined style={{ marginRight: 2 }} />{item.bank} </span>}
                  {item.value && <span style={{ marginLeft: 4 }}>值: <Text strong style={{ fontSize: 11, color: '#1677ff' }}>{item.value}</Text> </span>}
                  {item.category && <span style={{ marginLeft: 4 }}>分类: {item.category} </span>}
                  {item.reportType && <span style={{ marginLeft: 4 }}>类型: {item.reportType} </span>}
                  {item.source && <span style={{ marginLeft: 4 }}>来源: {item.source} </span>}
                </div>

                {item.detail && (
                  <Text type="secondary" style={{ fontSize: 10, display: 'block', marginTop: 3, lineHeight: 1.3 }}>
                    {item.detail}
                  </Text>
                )}

                {/* 操作按钮 */}
                <div style={{ marginTop: 4 }}>
                  {item.type === 'report' && item.bank && item.year && item.reportType && (
                    <Button type="link" size="small" icon={<DownloadOutlined />}
                      loading={downloadingRef === idx}
                      style={{ fontSize: 11, padding: 0, height: 20 }}
                      onClick={async () => {
                        setDownloadingRef(idx)
                        try {
                          await chatApi.downloadReport(item.bank!, item.reportType!, item.year!)
                          message.success('报告已下载')
                        } catch (e: any) {
                          message.error(e.message || '下载失败，请确认报告目录是否存在')
                        } finally {
                          setDownloadingRef(null)
                        }
                      }}>
                      下载报告PDF
                    </Button>
                  )}
                  {item.type === 'external' && item.source && (
                    <Text type="secondary" style={{ fontSize: 10 }}>
                      <LinkOutlined style={{ marginRight: 2 }} />
                      {item.source}公开数据
                    </Text>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* 底部统计 */}
          <div style={{ padding: '8px 14px', borderTop: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between' }}>
            <Text type="secondary" style={{ fontSize: 10 }}>
              共 {activeReferences.length} 项 · 报告{activeReferences.filter(r => r.type === 'report').length}
              · 指标{activeReferences.filter(r => r.type === 'indicator').length}
              · 外部{activeReferences.filter(r => r.type === 'external').length}
            </Text>
          </div>
        </div>
      )}

      {/* 无参考时显示提示 */}
      {activeReferences.length === 0 && messages.filter(m => m.role === 'assistant').length > 0 && (
        <div style={{ width: 280, flexShrink: 0, background: '#fff', borderLeft: '1px solid #f0f0f0',
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 40 }}>
          <DatabaseOutlined style={{ fontSize: 36, color: '#d9d9d9', marginBottom: 12 }} />
          <Text type="secondary" style={{ fontSize: 12, textAlign: 'center' }}>
            AI 回复中暂未包含<br />结构化参考资料
          </Text>
          <Text type="secondary" style={{ fontSize: 10, marginTop: 4, textAlign: 'center' }}>
            向 AI 询问保险经营分析相关问题<br />将自动展示参考的数据来源
          </Text>
        </div>
      )}
    </div>
  )
}
