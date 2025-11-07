<template>
  <div class="app-container">
    <!-- 导入状态提示 -->
    <el-alert 
      v-if="importAlertVisible" 
      :title="importAlertMessage" 
      :type="importAlertType" 
      closable 
      @close="importAlertVisible = false"
      style="margin-bottom: 10px;"
    ></el-alert>

    <!-- 头部 -->
    <header class="header">
      <div class="logo-container">
        <img src="../assets/images/logo.jpg" alt="云梦泽 - Yun Meng Ze">
      </div>
      <h1 class="title">基于EEG与人工智能的睡眠健康评估系统 V2.0</h1>
      <p class="subtitle">实时采集 · 本地存储 · 智能分析</p>
    </header>

    <!-- 状态指示 -->
    <StatusBar 
      :is-connected="isConnected" 
      :is-recording="isRecording" 
      :device-status="deviceStatus" />

    <!-- 操作按钮 -->
    <div class="button-group">
      <el-button type="primary" @click="connectDevice">
        {{ isConnected ? '断开设备' : '连接设备' }}
      </el-button>
      <el-button type="success" @click="toggleRecording">
        {{ isRecording ? '停止记录' : '开始记录' }}
      </el-button>
      <el-button type="warning" @click="analyzeData">分析数据</el-button>
      <el-button type="info" @click="importData">导入数据</el-button>
      <el-button type="text" @click="testBackend">测试后端连接</el-button>
    </div>

    <!-- 主体内容 -->
    <div class="main-content">
      <!-- 左侧侧边栏 -->
      <div class="sidebar">
        <DeviceConnection 
          v-model="deviceAddress"
          :device-status="deviceStatus"
          @scan="scanDevices" />
        <DataRecord />  
        <AnalysisConfig 
          v-model="apiKey"
          @test-api="testAPI" />
      </div>

      <!-- 右侧主内容区 -->
      <div class="main-panel">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="实时数据" name="realtime">
            <div class="tab-content-container">
              <div class="tab-pane-content">
                <div class="data-flow">
                  <i class="el-icon-info"></i>
                  <p>{{ isConnected ? '正在采集数据...' : '未连接设备，请先连接设备开始采集数据' }}</p>
                </div>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="分析报告" name="report">
            <div class="tab-content-container">
              <div class="tab-pane-content">
                <div class="placeholder" v-if="!reportContent">分析报告内容将显示在此处</div>
                <div v-else class="report-content" v-html="reportContent"></div>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="系统日志" name="log">
            <div class="tab-content-container">
              <div class="tab-pane-content">
                <div class="placeholder" v-text="logContent || '系统日志将显示在此处'"></div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
        <div class="clear-log-btn">
          <el-button type="text" @click="clearLog">清空日志</el-button>
        </div>
      </div>
    </div>

    <!-- 底部 -->
    <footer class="footer">
      基于EEG与人工智能的睡眠健康评估系统 V1.0 | 本地数据安全存储 | 支持CSV/Excel数据分析
    </footer>
  </div>
</template>

<script>
import StatusBar from '../components/StatusBar.vue'
import DeviceConnection from '../components/DeviceConnection.vue'
import DataRecord from '../components/DataRecord.vue'
import AnalysisConfig from '../components/AnalysisConfig.vue'

export default {
  name: 'Home',
  components: {
    StatusBar,
    DeviceConnection,
    DataRecord,
    AnalysisConfig
  },
  data() {
    return {
      // 导入提示
      importAlertVisible: false,
      importAlertMessage: '',
      importAlertType: 'error',
      
      // 核心变量
      deviceAddress: '',
      apiKey: '51e09aa5-d2dd-41ab-bf91-51ef798844e7',
      activeTab: 'realtime',
      websocket: null,
      isConnected: false,
      isRecording: false,
      deviceStatus: '未连接',
      logContent: '',
      reportContent: '',
      importedFileName: '',
      currentRecordingId: '',
      fileInput: null,
      importedFileHashes: new Set()
    }
  },
  created() {
    this.fileInput = document.createElement('input')
    this.fileInput.type = 'file'
    this.fileInput.accept = '.csv,.xlsx,.xls,.txt'
    this.fileInput.addEventListener('change', (event) => {
      this.handleFileSelected(event)
    })
  },
  methods: {
    /**
     * 计算文件哈希
     */
    async calculateFileHash(file) {
      return new Promise((resolve) => {
        const reader = new FileReader()
        reader.onload = (e) => {
          const arrayBuffer = e.target.result
          const hash = Array.from(new Uint8Array(arrayBuffer))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('')
          resolve(hash)
        }
        reader.readAsArrayBuffer(file.slice(0, 1024 * 1024))
      })
    },

    /**
     * 处理选择的文件
     */
    async handleFileSelected(event) {
      const file = event.target.files[0]
      if (!file) {
        this.$message.info('未选择文件')
        return
      }

      const originalFileName = file.name
      
      const fileHash = await this.calculateFileHash(file)
      if (this.importedFileHashes.has(fileHash)) {
        this.showImportAlert('该文件已导入，请勿重复上传', 'warning')
        return
      }

      const maxSize = 100 * 1024 * 1024
      if (file.size > maxSize) {
        this.showImportAlert('文件过大，请选择100MB以内的文件', 'error')
        return
      }

      this.$message.info(`正在上传文件：${originalFileName}...`)
      this.logContent += `[${new Date().toLocaleTimeString()}] 开始上传文件：${originalFileName}\n`
      
      const formData = new FormData()
      formData.append('file', file)
      formData.append('file_hash', fileHash)
      formData.append('original_filename', originalFileName)
      
      fetch('/api/import-eeg-data/', {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': this.getCSRFToken()
        },
        timeout: 30000
      })
        .then(response => {
          if (response.status === 500) {
            throw new Error(`服务器内部错误，请稍后重试`)
          }
          if (!response.ok) {
            return response.text().then(text => {
              throw new Error(`上传失败（${response.status}）: ${text}`)
            })
          }
          return response.json()
        })
        .then(data => {
          this.logContent += `[${new Date().toLocaleTimeString()}] 后端返回完整数据: ${JSON.stringify(data)}\n`
          
          if (data.status === 'success') {
            if (!data.recording_id || !/^\d+$/.test(data.recording_id)) {
              throw new Error(`后端返回的recording_id无效：${data.recording_id}`)
            }

            this.importedFileHashes.add(fileHash)
            this.$message.success(`文件上传成功：${originalFileName}（记录ID：${data.recording_id}）`)
            this.logContent += `[${new Date().toLocaleTimeString()}] 导入成功，记录ID：${data.recording_id}\n`
            this.importedFileName = originalFileName
            this.currentRecordingId = data.recording_id
            this.analyzeExistingData()
          } else {
            throw new Error(data.message || '上传失败，后端返回非成功状态')
          }
        })
        .catch(error => {
          this.showImportAlert(error.message, 'error')
          this.logContent += `[${new Date().toLocaleTimeString()}] 处理失败: ${error.message}\n`
          this.currentRecordingId = ''
          this.importedFileName = ''
        })
    },

    /**
     * 导入数据函数
     */
    importData() {
      this.fileInput.value = ''
      this.fileInput.click()
    },

    /**
     * 分析数据入口
     */
    analyzeData() {
      if (this.reportContent.includes('正在分析数据')) {
        this.$message.warning('正在分析中，请稍候...')
        return
      }

      if (this.currentRecordingId && this.importedFileName) {
        this.$confirm(
          `检测到已导入文件：${this.importedFileName}（记录ID：${this.currentRecordingId}），是否直接分析该文件？`,
          '选择分析文件',
          {
            confirmButtonText: '分析已导入文件',
            cancelButtonText: '选择新文件',
            type: 'question'
          }
        ).then(() => {
          this.analyzeExistingData()
        }).catch(() => {
          this.importData()
        })
      } else {
        this.importData()
      }
    },

    /**
     * 分析已有数据（核心修复：解决响应体重复读取问题）
     */
    analyzeExistingData() {
      if (!this.currentRecordingId || !this.importedFileName) {
        this.$message.error('缺少记录ID或文件名，无法分析')
        this.reportContent = `<p style="color: #F56C6C">请重新导入文件</p>`
        return
      }

      this.reportContent = `<p style="color: #409EFF">正在分析数据（${this.importedFileName}），请稍候...</p>`
      this.activeTab = 'report'
      
      // 构造请求参数
      const requestData = {
        recording_id: parseInt(this.currentRecordingId, 10),
        original_filename: this.importedFileName,
        api_key: this.apiKey.trim()
      }

      this.logContent += `[${new Date().toLocaleTimeString()}] 分析请求参数: ${JSON.stringify(requestData)}\n`
      this.logContent += `[${new Date().toLocaleTimeString()}] 分析请求URL: /api/analyze-existing-data/\n`
      
      fetch('/api/analyze-existing-data/', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json;charset=UTF-8',
          'X-CSRFToken': this.getCSRFToken(),
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestData),
        timeout: 60000
      })
        .then(response => {
          // 关键修复：克隆响应体避免重复读取
          const clonedResponse = response.clone()
          
          if (response.status === 400) {
            // 先尝试解析JSON
            return clonedResponse.json()
              .then(errorData => {
                throw new Error(`分析请求参数错误（400）: ${errorData.message || JSON.stringify(errorData)}`)
              })
              .catch(() => {
                // JSON解析失败再尝试文本
                return clonedResponse.text().then(text => {
                  throw new Error(`分析请求参数错误（400）: ${text}`)
                })
              })
          }
          if (response.status === 500) {
            throw new Error(`服务器内部错误（500）`)
          }
          if (!response.ok) {
            throw new Error(`分析失败（${response.status}）`)
          }
          return response.json()
        })
        .then(data => {
          if (data.status === 'success') {
            this.$message.success(data.message)
            this.logContent += `[${new Date().toLocaleTimeString()}] ${data.message}\n`
            this.loadReport(data.report_filename)
          } else {
            throw new Error(data.message || '分析失败，后端返回非成功状态')
          }
        })
        .catch(error => {
          this.reportContent = `<p style="color: #F56C6C">分析出错: ${error.message}</p>`
          this.logContent += `[${new Date().toLocaleTimeString()}] 分析出错: ${error.message}\n`
        })
    },

    /**
     * 显示导入提示
     */
    showImportAlert(message, type = 'error') {
      this.importAlertMessage = message
      this.importAlertType = type
      this.importAlertVisible = true
      setTimeout(() => {
        this.importAlertVisible = false
      }, 3000)
    },

    /**
     * 获取CSRF Token
     */
    getCSRFToken() {
      const cookies = document.cookie.split(';')
      for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=')
        if (name === 'csrftoken') {
          return value
        }
      }
      return ''
    },

    /**
     * 测试后端连接
     */
    testBackend() {
      fetch('/api/latest-eeg-record/')
        .then(response => {
          if (response.ok) {
            this.$message.success('后端连接正常')
            this.logContent += `[${new Date().toLocaleTimeString()}] 后端连接测试成功\n`
          } else {
            throw new Error(`连接异常（状态码：${response.status}）`)
          }
        })
        .catch(error => {
          this.$message.error('后端连接失败: ' + error.message)
          this.logContent += `[${new Date().toLocaleTimeString()}] 后端连接测试失败: ${error.message}\n`
        })
    },

    /**
     * 其他方法保持不变
     */
    connectDevice() {
      if (this.isConnected) {
        this.$message.info('设备已连接')
        return
      }
      
      try {
        const wsUrl = 'ws://localhost:8000/ws/eeg/'
        console.log('尝试连接到WebSocket:', wsUrl)
        
        this.websocket = new WebSocket(wsUrl)
        
        this.websocket.onopen = () => {
          console.log('WebSocket连接成功')
          this.isConnected = true
          this.deviceStatus = '已连接'
          this.$message.success('设备连接成功')
        }
        
        this.websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleWebSocketMessage(data)
          } catch (e) {
            this.$message.error('解析WebSocket数据失败')
            this.logContent += `[${new Date().toLocaleTimeString()}] WebSocket数据解析错误: ${e.message}\n`
          }
        }
        
        this.websocket.onclose = () => {
          this.isConnected = false
          this.isRecording = false
          this.deviceStatus = '未连接'
          this.$message.info('设备连接已断开')
        }
        
        this.websocket.onerror = (error) => {
          console.error('WebSocket连接错误:', error)
          this.$message.error('连接发生错误: ' + error.message)
        }
      } catch (error) {
        console.error('WebSocket连接异常:', error)
        this.$message.error('连接失败: ' + error.message)
      }
    },

    toggleRecording() {
      this.isRecording = !this.isRecording
      
      if (this.isRecording) {
        if (!this.isConnected) {
          this.$message.warning('请先连接设备')
          this.isRecording = false
          return
        }
        
        this.$message.success('开始记录数据')
        this.sendEEGData()
      } else {
        this.$message.info('已停止记录数据')
      }
    },

    sendEEGData() {
      if (!this.isRecording || !this.isConnected) return
      
      const eegData = {
        type: 'eeg_data',
        timestamp: new Date().toISOString(),
        data: this.generateMockEEGData()
      }
      
      try {
        this.websocket.send(JSON.stringify(eegData))
      } catch (error) {
        this.$message.error('发送数据失败: ' + error.message)
        this.logContent += `[${new Date().toLocaleTimeString()}] 发送数据失败: ${error.message}\n`
      }
      
      if (this.isRecording) {
        setTimeout(() => this.sendEEGData(), 1000)
      }
    },

    generateMockEEGData() {
      const bands = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']
      return bands.map(b => `${b} ${Math.floor(Math.random() * 100)}`).join(' ')
    },

    loadReport(filename) {
      if (!filename) {
        this.$message.error('报告文件名为空')
        return
      }
      
      const reportUrl = `/reports/${filename}`
      this.logContent += `[${new Date().toLocaleTimeString()}] 加载报告: ${reportUrl}\n`
      
      fetch(reportUrl)
        .then(response => {
          if (!response.ok) {
            throw new Error(`报告加载失败（${response.status}）`)
          }
          return response.text()
        })
        .then(html => {
          this.reportContent = html
          this.activeTab = 'report'
        })
        .catch(error => {
          this.$message.error(`加载报告失败: ${error.message}`)
          this.logContent += `[${new Date().toLocaleTimeString()}] 加载报告失败: ${error.message}\n`
        })
    },

    scanDevices() {
      if (!this.checkBluetoothSupport()) return
     
      this.$message.info('正在扫描蓝牙设备...')
      navigator.bluetooth.requestDevice({
        acceptAllDevices: true,
        optionalServices: ['battery_service', 'generic_access', 'device_information']
      })
        .then(device => {
          this.$message.success(`找到设备: ${device.name || '未知设备'}`)
          this.deviceAddress = device.id
          return device.gatt.connect()
        })
        .then(server => {
          this.$message.success('蓝牙设备配对成功')
        })
        .catch(error => {
          this.$message.error(`扫描失败: ${error.message}`)
        })
    },

    checkBluetoothSupport() {
      const supportInfo = {
        bluetooth: !!navigator.bluetooth,
        secureContext: window.isSecureContext,
        https: window.location.protocol === 'https:',
        localhost: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
        chrome: /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor)
      }
      
      console.log('环境信息:', supportInfo)
      
      if (!supportInfo.bluetooth) {
        let message = '您的浏览器不支持Web Bluetooth API。'
        if (!supportInfo.chrome) message += '建议使用最新版Google Chrome浏览器。'
        else if (!supportInfo.secureContext) message += 'Web Bluetooth需要HTTPS环境或本地环境(localhost)。'
        this.$message.warning(message)
        return false
      }
      
      if (!supportInfo.secureContext) {
        this.$message.warning('Web Bluetooth需要安全环境（HTTPS或localhost）。')
        return false
      }
      
      return true
    },

    testAPI() {
      if (!this.apiKey) {
        this.$message.warning('请输入API密钥')
        return
      }
      
      const loading = this.$loading({
        lock: true,
        text: '测试中...',
        spinner: 'el-icon-loading',
        background: 'rgba(0, 0, 0, 0.7)'
      })
      
      fetch('/api/test-api-key/', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken()
        },
        body: JSON.stringify({ api_key: this.apiKey })
      })
        .then(response => response.json())
        .then(data => {
          loading.close()
          if (data.status === 'success') {
            this.$message.success(data.message)
          } else {
            this.$message.error(data.message)
          }
        })
        .catch(error => {
          loading.close()
          this.$message.error('测试请求失败: ' + error.message)
        })
    },

    clearLog() {
      this.logContent = ''
      this.$message.success('日志已清空')
    },

    handleWebSocketMessage(data) {
      switch (data.type) {
        case 'data_received':
          this.logContent += `[${new Date().toLocaleTimeString()}] 数据已接收: ${data.timestamp}\n`
          break
        case 'data_error':
          this.$message.error('数据处理错误: ' + data.error)
          this.logContent += `[${new Date().toLocaleTimeString()}] 错误: ${data.error}\n`
          break
        case 'import_success':
          this.$message.success('导入数据已成功保存到服务器')
          this.logContent += `[${new Date().toLocaleTimeString()}] 导入数据已保存\n`
          break
        case 'analysis_result':
          if (data.success) {
            if (data.path) this.loadReport(data.path)
            else if (data.content) {
              this.reportContent = data.content
              this.activeTab = 'report'
            }
            this.$message.success('分析完成')
          } else {
            this.$message.error('分析失败: ' + data.error)
          }
          break
        case 'error':
          this.$message.error('服务器错误: ' + data.message)
          break
      }
      
      this.$nextTick(() => {
        const logPanel = document.querySelector('.el-tab-pane[name="log"] .placeholder')
        if (logPanel) logPanel.scrollTop = logPanel.scrollHeight
      })
    }
  },
  
  beforeDestroy() {
    if (this.websocket) {
      this.websocket.close()
    }
    if (this.fileInput) {
      this.fileInput.removeEventListener('change', this.handleFileSelected)
    }
  },
  
  mounted() {
    this.testBackend()
  }
}
</script>