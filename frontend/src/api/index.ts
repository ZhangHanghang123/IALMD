import axios from 'axios'

const rawApi = axios.create({
  baseURL: '/ialmd/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器：自动添加token
rawApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：自动解包response.data，并处理认证错误
rawApi.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    if (error.response?.status === 401 || error.response?.status === 403) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/ialmd/login') {
        window.location.href = '/ialmd/login'
      }
    }
    return Promise.reject(error)
  }
)

// 封装为 Promise<any> 返回类型，与响应拦截器解包后的实际数据结构一致
const api = {
  get: <T = any>(url: string, config?: any): Promise<T> => rawApi.get(url, config) as Promise<T>,
  post: <T = any>(url: string, data?: any, config?: any): Promise<T> => rawApi.post(url, data, config) as Promise<T>,
  put: <T = any>(url: string, data?: any, config?: any): Promise<T> => rawApi.put(url, data, config) as Promise<T>,
  delete: <T = any>(url: string, config?: any): Promise<T> => rawApi.delete(url, config) as Promise<T>,
  patch: <T = any>(url: string, data?: any, config?: any): Promise<T> => rawApi.patch(url, data, config) as Promise<T>,
}

export const authApi = {
  login: (username: string, password: string) => 
    api.post('/auth/login', { username, password }),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get('/auth/me'),
}

export const dashboardApi = {
  getDashboard: () => api.get('/dashboard'),
}

export const banksApi = {
  getList: (params?: any) => api.get('/banks', { params }),
  getTypes: () => api.get('/banks/types'),
  getTypesStat: () => api.get('/banks/types/stat'),
  getDetail: (id: number) => api.get(`/banks/${id}`),
  create: (data: any) => api.post('/banks', data),
  update: (id: number, data: any) => api.put(`/banks/${id}`, data),
  delete: (id: number) => api.delete(`/banks/${id}`),
  toggleStatus: (id: number, status: number) => api.patch(`/banks/${id}/status`, { status }),
}

export const indicatorsApi = {
  getList: (params?: any) => api.get('/indicators', { params }),
  getCategories: () => api.get('/indicators/categories'),
  getValues: (params: any) => api.get('/indicators/values', { params }),
  // 指标值维护 CRUD
  getValueList: (params?: any) => api.get('/indicators/values/list', { params }),
  getValueDetail: (id: number) => api.get(`/indicators/values/${id}`),
  createValue: (data: any) => api.post('/indicators/values', data),
  updateValue: (id: number, data: any) => api.put(`/indicators/values/${id}`, data),
  deleteValue: (id: number) => api.delete(`/indicators/values/${id}`),
  verifyValue: (id: number, data: { verify_status: string; verify_remark?: string }) =>
    api.post(`/indicators/values/${id}/verify`, data),
}

export const benchmarkApi = {
  compare: (params: any) => api.get('/benchmark/compare', { params }),
  getAvailableYears: (indicatorCode: string, reportPeriod?: string) =>
    api.get('/benchmark/available-years', { params: { indicator_code: indicatorCode, report_period: reportPeriod || 'FY' } }),
  saveCompare: (indicatorCode: string, reportYear: number, bankIds: string, reportPeriod?: string) =>
    api.post('/benchmark/save', undefined, { params: { indicator_code: indicatorCode, report_year: reportYear, bank_ids: bankIds, report_period: reportPeriod || 'FY' } }),
  getHistory: (params?: any) => api.get('/benchmark/history', { params }),
  uploadOwnReport: (file: File, reportYear: number, bankType: string, bankName: string) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('report_year', String(reportYear))
    fd.append('bank_type', bankType)
    fd.append('bank_name', bankName)
    return api.post('/benchmark/upload-report', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
}

export const chatApi = {
  getSessions: () => api.get('/chat/sessions'),
  createSession: () => api.post('/chat/sessions'),
  getMessages: (sessionId: number) => api.get(`/chat/messages/${sessionId}`),
  deleteSession: (sessionId: number) => api.delete(`/chat/sessions/${sessionId}`),
  // 发送消息并接收 SSE 流式响应（用 fetch + ReadableStream 实现，支持自定义请求头）
  sendMessage: (sessionId: number, message: string, onChunk: (data: any) => void, onError: (err: any) => void, onDone: () => void): AbortController => {
    const controller = new AbortController()
    const url = `/ialmd/api/chat/messages/${sessionId}/send`

    const token = localStorage.getItem('token')
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message }),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          // HTTP 错误状态码（如 401/403/404/500）
          let errorBody = ''
          try { errorBody = await response.text() } catch {}
          onError({
            type: 'http_error',
            status: response.status,
            statusText: response.statusText,
            body: errorBody.slice(0, 500),
          })
          return
        }
        if (!response.body) {
          onError({ type: 'no_body', message: '响应没有 body 流' })
          return
        }

        // 逐块读取 SSE 流
        const reader = response.body.getReader()
        const decoder = new TextDecoder('utf-8')
        let buffer = ''
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })

          // SSE 协议以 \n\n 分隔事件
          const events = buffer.split('\n\n')
          buffer = events.pop() || ''
          for (const evt of events) {
            const lines = evt.split('\n')
            for (const line of lines) {
              if (line.startsWith('data:')) {
                const payload = line.slice(5).trim()
                if (!payload) continue
                try {
                  onChunk(JSON.parse(payload))
                } catch (e) {
                  console.warn('[SSE] 解析 chunk 失败:', payload, e)
                }
              }
            }
          }
        }
        onDone()
      })
      .catch((err) => {
        if (err.name === 'AbortError') {
          console.log('[SSE] 用户主动取消')
          return
        }
        onError({
          type: 'network_error',
          message: err?.message || String(err),
          name: err?.name,
        })
      })

    return controller
  },

  // 参考资料导出为Excel
  exportReferences: async (items: any[], sessionTitle: string) => {
    const token = localStorage.getItem('token')
    const resp = await fetch('/ialmd/api/chat/references/export', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ items, session_title: sessionTitle }),
    })
    if (!resp.ok) throw new Error('导出失败')
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `参考资料_${sessionTitle}.xlsx`
    document.body.appendChild(a); a.click()
    document.body.removeChild(a); URL.revokeObjectURL(url)
  },

  // 检查报告是否可下载
  checkReport: (bank: string, reportType: string, year: string) =>
    api.get('/chat/references/report-check', { params: { bank, report_type: reportType, year } }),

  // 下载报告PDF（返回下载URL）
  downloadReport: async (bank: string, reportType: string, year: string) => {
    const token = localStorage.getItem('token')
    const resp = await fetch(
      `/ialmd/api/chat/references/report-download?bank=${encodeURIComponent(bank)}&report_type=${encodeURIComponent(reportType)}&year=${encodeURIComponent(year)}`,
      { headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) } }
    )
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: '下载失败' }))
      throw new Error(err.detail || '下载失败')
    }
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${bank}${year}年${reportType}.pdf`
    document.body.appendChild(a); a.click()
    document.body.removeChild(a); URL.revokeObjectURL(url)
  },
}

export const workflowApi = {
  getAgents: () => api.get('/workflows/agents'),
  getTemplates: () => api.get('/workflows/templates'),
  initTemplates: () => api.post('/workflows/templates/init'),
  getList: (params?: any) => api.get('/workflows', { params }),
  getDetail: (id: number) => api.get(`/workflows/${id}`),
  create: (data: any) => api.post('/workflows', data),
  update: (id: number, data: any) => api.put(`/workflows/${id}`, data),
  delete: (id: number) => api.delete(`/workflows/${id}`),
  execute: (id: number, params: any) => api.post(`/workflows/${id}/execute`, params, { timeout: 120000 }),
  getExecutions: (id: number, params?: any) => api.get(`/workflows/${id}/executions`, { params }),
  getNodeExecutions: (execId: number) => api.get(`/workflows/executions/${execId}/nodes`),
}

export const llmConfigApi = {
  getList: (params?: any) => api.get('/llm-config', { params }),
  getDetail: (id: number) => api.get(`/llm-config/${id}`),
  create: (data: any) => api.post('/llm-config', data),
  update: (id: number, data: any) => api.put(`/llm-config/${id}`, data),
  delete: (id: number) => api.delete(`/llm-config/${id}`),
  toggle: (id: number, isEnabled: number) => api.patch(`/llm-config/${id}/toggle`, { is_enabled: isEnabled }),
  test: (id: number) => api.post(`/llm-config/${id}/test`),
}

export const dictApi = {
  // 字典类型
  getTypes: (params?: any) => api.get('/dict/types', { params }),
  getType: (id: number) => api.get(`/dict/types/${id}`),
  getTypeWithData: (id: number) => api.get(`/dict/types/${id}/with-data`),
  createType: (data: any) => api.post('/dict/types', data),
  updateType: (id: number, data: any) => api.put(`/dict/types/${id}`, data),
  deleteType: (id: number) => api.delete(`/dict/types/${id}`),
  // 字典数据
  getData: (params?: any) => api.get('/dict/data', { params }),
  getDataByCode: (code: string) => api.get(`/dict/codes/${code}`),
  getDataItem: (id: number) => api.get(`/dict/data/${id}`),
  createData: (data: any) => api.post('/dict/data', data),
  updateData: (id: number, data: any) => api.put(`/dict/data/${id}`, data),
  deleteData: (id: number) => api.delete(`/dict/data/${id}`),
}

export const indicatorsDashboardApi = {
  // 获取仪表盘概览数据
  getDashboard: (params?: any) => api.get('/indicators-dashboard', { params }),
  // 获取指标趋势数据
  getTrends: (indicatorCode: string, years?: number) => 
    api.get('/indicators-dashboard/trends', { params: { indicator_code: indicatorCode, years } }),
  // 获取机构排名数据
  getRankings: (indicatorCode: string, year?: number, bankType?: string, topN?: number) =>
    api.get('/indicators-dashboard/rankings', { params: { indicator_code: indicatorCode, year, bank_type: bankType, top_n: topN } }),
  // 对比多个指标
  compare: (indicatorCodes: string, year?: number) =>
    api.get('/indicators-dashboard/comparison', { params: { indicator_codes: indicatorCodes, year } }),
  // 获取指标分布数据
  getDistribution: (indicatorCode: string, year?: number, buckets?: number) =>
    api.get('/indicators-dashboard/distribution', { params: { indicator_code: indicatorCode, year, buckets } }),
  // 获取指标详情
  getDetail: (indicatorCode: string, year?: number) =>
    api.get(`/indicators-dashboard/detail/${indicatorCode}`, { params: { year } }),
}

// ==================== 本体管理 API ====================

export const ontologyApi = {
  // 统计概览
  getStats: () => api.get('/ontology/stats'),
  // 概念 (Class/Instance)
  listClasses: (params?: any) => api.get('/ontology/classes', { params }),
  getClassTree: (entityType?: string) => api.get('/ontology/classes/tree', { params: entityType ? { entity_type: entityType } : {} }),
  getClassDetail: (id: number) => api.get(`/ontology/classes/${id}`),
  createClass: (data: any) => api.post('/ontology/classes', data),
  updateClass: (id: number, data: any) => api.put(`/ontology/classes/${id}`, data),
  deleteClass: (id: number) => api.delete(`/ontology/classes/${id}`),
  // 关系
  listRelations: (params?: any) => api.get('/ontology/relations', { params }),
  createRelation: (data: any) => api.post('/ontology/relations', data),
  deleteRelation: (id: number) => api.delete(`/ontology/relations/${id}`),
  // 异构映射
  listMappings: (params?: any) => api.get('/ontology/mappings', { params }),
  createMapping: (data: any) => api.post('/ontology/mappings', data),
  approveMapping: (id: number) => api.post(`/ontology/mappings/${id}/approve`),
  rejectMapping: (id: number, remark?: string) =>
    api.post(`/ontology/mappings/${id}/reject`, null, { params: { remark } }),
  // 映射候选
  listMappingCandidates: (params?: any) => api.get('/ontology/mapping-candidates', { params }),
  approveCandidate: (id: number) => api.post(`/ontology/mapping-candidates/${id}/approve`),
  // 机构本体
  listBanks: (params?: any) => api.get('/ontology/banks', { params }),
  getBankDetail: (id: number) => api.get(`/ontology/banks/${id}`),
  // 机构文件管理
  listBankFiles: (id: number, subpath?: string) =>
    api.get(`/ontology/banks/${id}/files`, { params: subpath ? { subpath } : {} }),
  getBankFileDownloadUrl: (id: number, relPath: string) =>
    `/ialmd/api/ontology/banks/${id}/files/download?rel_path=${encodeURIComponent(relPath)}`,
  // 机构报告
  listBankReports: (params?: any) => api.get('/ontology/bank-reports', { params }),
  scanBankReports: (baseDir?: string) =>
    api.post('/ontology/bank-reports/scan', null, { params: baseDir ? { base_dir: baseDir } : {} }),
  // 关系类型 / 标签
  listRelationTypes: () => api.get('/ontology/relation-types'),
  listTags: () => api.get('/ontology/tags'),
  // 版本
  listVersions: () => api.get('/ontology/versions'),
  publishVersion: (versionCode: string, versionDesc?: string) =>
    api.post('/ontology/versions/publish', null, { params: { version_code: versionCode, version_desc: versionDesc || '' } }),
  // 审计日志
  listAuditLogs: (params?: any) => api.get('/ontology/audit-logs', { params }),
}

// ==================== 报告采集 API ====================

export const reportCollectApi = {
  // 统计
  getStats: () => api.get('/report-collect/stats'),
  // 采集任务
  listTasks: (params?: any) => api.get('/report-collect/tasks', { params }),
  // 触发采集
  triggerCollect: (bankIds: string, reportTypes?: string, years?: string) =>
    api.post('/report-collect/collect', null, { params: { bank_ids: bankIds, report_types: reportTypes || '', years: years || '' } }),
  triggerSingleCollect: (bankId: number, reportTypes?: string, years?: string) =>
    api.post(`/report-collect/collect/${bankId}`, null, { params: { report_types: reportTypes || '', years: years || '' } }),
  // 触发提取
  triggerExtract: (bankId: number, years?: string) =>
    api.post(`/report-collect/extract/${bankId}`, null, { params: { years: years || '' } }),
  triggerExtractAll: (bankType?: string) =>
    api.post('/report-collect/extract-all', null, { params: { bank_type: bankType || '' } }),
  // 提取结果
  listExtractResults: (params?: any) => api.get('/report-collect/extract-results', { params }),
  // 上传
  uploadReport: (bankId: number, formData: FormData, params: any) =>
    api.post(`/report-collect/upload/${bankId}`, formData, { params, headers: { 'Content-Type': 'multipart/form-data' } }),
  // 下载
  getDownloadUrl: (bankId: number, linkId: number) =>
    `/ialmd/api/report-collect/download/${bankId}?link_id=${linkId}`,
}

// ==================== 流动性压力测试 API ====================

export const liquidityApi = {
  // G21 数据
  listG21: (params?: any) => api.get('/liquidity/g21', { params }),
  getG21Periods: () => api.get('/liquidity/g21/periods'),
  getG21: (id: number) => api.get(`/liquidity/g21/${id}`),
  createG21: (data: any) => api.post('/liquidity/g21', data),
  updateG21: (id: number, data: any) => api.put(`/liquidity/g21/${id}`, data),
  deleteG21: (id: number) => api.delete(`/liquidity/g21/${id}`),
  importG21: (data: any) => api.post('/liquidity/g21/import', data),
  deleteG21Period: (period: string) => api.delete(`/liquidity/g21/period/${period}`),
  exportG21Url: (period: string) => `/ialmd/api/liquidity/g21/export?report_period=${period}`,

  // HQLA 资产
  listHqla: (params?: any) => api.get('/liquidity/hqla', { params }),
  getHqlaSummary: (period: string) => api.get('/liquidity/hqla/summary', { params: { report_period: period } }),
  getHqlaPeriods: () => api.get('/liquidity/hqla/periods'),
  getHqla: (id: number) => api.get(`/liquidity/hqla/${id}`),
  createHqla: (data: any) => api.post('/liquidity/hqla', data),
  updateHqla: (id: number, data: any) => api.put(`/liquidity/hqla/${id}`, data),
  deleteHqla: (id: number) => api.delete(`/liquidity/hqla/${id}`),
  importHqla: (data: any) => api.post('/liquidity/hqla/import', data),
  deleteHqlaPeriod: (period: string) => api.delete(`/liquidity/hqla/period/${period}`),
  exportHqlaUrl: (period: string) => `/ialmd/api/liquidity/hqla/export?report_period=${period}`,

  // 版本管理
  listVersions: (params?: any) => api.get('/liquidity/versions', { params }),
  getVersion: (id: number) => api.get(`/liquidity/versions/${id}`),
  createVersion: (data: any) => api.post('/liquidity/versions', data),
  updateVersion: (id: number, data: any) => api.put(`/liquidity/versions/${id}`, data),
  deleteVersion: (id: number) => api.delete(`/liquidity/versions/${id}`),
  publishVersion: (id: number) => api.put(`/liquidity/versions/${id}/publish`),
  recallVersion: (id: number) => api.put(`/liquidity/versions/${id}/recall`),
  archiveVersion: (id: number) => api.put(`/liquidity/versions/${id}/archive`),
  copyVersion: (id: number) => api.post(`/liquidity/versions/${id}/copy`),
  runStressTest: (id: number) => api.post(`/liquidity/versions/${id}/run`),
  updateScenarioParams: (id: number, data: any) => api.put(`/liquidity/versions/${id}/scenario-params`, data),
  compareVersions: (data: any) => api.post('/liquidity/versions/compare', data),
  downloadReportUrl: (id: number) => `/ialmd/api/liquidity/versions/${id}/report`,
}

export default api
