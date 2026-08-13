import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import Dashboard from './pages/Dashboard'
import ChatAnalysis from './pages/ChatAnalysis'
import BenchmarkCompare from './pages/BenchmarkCompare'
import ReportManager from './pages/ReportManager'
import BankManagement from './pages/BankManagement'
import IndicatorLibrary from './pages/IndicatorLibrary'
import IndicatorValueManage from './pages/IndicatorValueManage'
import OntologyKnowledge from './pages/OntologyKnowledge'
import WorkflowEditor from './pages/WorkflowEditor'
import DictManagement from './pages/DictManagement'
import SystemSettings from './pages/SystemSettings'
import IndicatorDashboard from './pages/IndicatorDashboard'
import LiquidityStressTest from './pages/LiquidityStressTest'
import Login from './pages/Login'

function AuthGuard({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<AuthGuard><MainLayout /></AuthGuard>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="chat" element={<ChatAnalysis />} />
        <Route path="benchmark" element={<BenchmarkCompare />} />
        <Route path="reports" element={<ReportManager />} />
        <Route path="banks" element={<BankManagement />} />
        <Route path="indicators" element={<IndicatorLibrary />} />
        <Route path="indicator-values" element={<IndicatorValueManage />} />
        <Route path="ontology" element={<OntologyKnowledge />} />
        <Route path="workflow" element={<WorkflowEditor />} />
        <Route path="dict" element={<DictManagement />} />
        <Route path="settings" element={<SystemSettings />} />
        <Route path="indicator-dashboard" element={<IndicatorDashboard />} />
        <Route path="liquidity-stress" element={<LiquidityStressTest />} />
      </Route>
    </Routes>
  )
}
