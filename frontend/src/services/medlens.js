import api from './api'

export const patientService = {
  async createPatient(data) {
    const res = await api.post('/patients', data)
    return res.data.data
  },

  async getPatients() {
    const res = await api.get('/patients')
    return res.data.data
  },

  async getPatient(patientId) {
    const res = await api.get(`/patients/${patientId}`)
    return res.data.data
  },

  async updatePatient(patientId, data) {
    const res = await api.put(`/patients/${patientId}`, data)
    return res.data.data
  },

  async getTests(patientId) {
    const res = await api.get(`/patients/${patientId}/tests`)
    return res.data.data
  },

  async getSummary(patientId) {
    const res = await api.get(`/patients/${patientId}/summary`)
    return res.data.data
  },

  async generateSummary(patientId) {
    const res = await api.post(`/patients/${patientId}/summary`)
    return res.data.data
  },

  async getClarifications(patientId) {
    const res = await api.get(`/patients/${patientId}/clarifications`)
    return res.data.data
  },
}

export const reportService = {
  async uploadReport(patientId, file, reportType = 'other', reportDate = null) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('report_type', reportType)
    if (reportDate) formData.append('report_date', reportDate)
    formData.append('auto_process', 'true')
    const res = await api.post(`/patients/${patientId}/reports`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data.data
  },

  async uploadTextReport(patientId, text, reportType = 'lab', reportDate = null) {
    const formData = new FormData()
    formData.append('text', text)
    formData.append('report_type', reportType)
    if (reportDate) formData.append('report_date', reportDate)
    const res = await api.post(`/patients/${patientId}/reports/text`, formData)
    return res.data.data
  },

  async getReports(patientId) {
    const res = await api.get(`/patients/${patientId}/reports`)
    return res.data.data
  },

  async getReport(reportId) {
    const res = await api.get(`/reports/${reportId}`)
    return res.data.data
  },

  async reprocessReport(reportId) {
    const res = await api.post(`/reports/${reportId}/process`)
    return res.data
  },
}

export const testService = {
  async updateTest(testId, data) {
    const res = await api.put(`/tests/${testId}`, data)
    return res.data.data
  },

  async verifyTest(testId) {
    const res = await api.post(`/tests/${testId}/verify`)
    return res.data.data
  },

  async correctTest(testId, data) {
    const res = await api.post(`/tests/${testId}/correct`, data)
    return res.data.data
  },
}
