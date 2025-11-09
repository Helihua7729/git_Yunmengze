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
        <DataRecord @record-selected="onRecordSelected"/>  
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
      importAlertVisible: false, // 导入提示框是否可见
      importAlertMessage: '',    // 导入提示信息内容
      importAlertType: 'error',  // 导入提示类型（error/success/warning/info等）
      
      // 核心变量
      deviceAddress: '',         // 设备地址
      apiKey: '51e09aa5-d2dd-41ab-bf91-51ef798844e7', // API密钥，用于设备认证
      activeTab: 'realtime',     // 当前激活的标签页（realtime表示实时数据页面）
      websocket: null,           // WebSocket连接对象
      isConnected: false,        // 设备连接状态标识
      isRecording: false,        // 数据录制状态标识
      deviceStatus: '未连接',     // 设备状态文本描述
      logContent: '',            // 日志内容
      reportContent: '',         // 报告内容
      importedFileName: '',      // 已导入文件的名称
      currentRecordingId: '',    // 当前录制会话的ID
      fileInput: null,           // 文件输入元素引用
      importedFileHashes: new Set(), // 已导入文件的哈希值集合，用于避免重复导入
      
      // 蓝牙相关变量
      bluetoothDevice: null,     // 蓝牙设备对象
      bluetoothServer: null,     // 蓝牙服务对象
      bluetoothCharacteristic: null, // 蓝牙特征值对象
      bluetoothBuffer: new Uint8Array(), // 蓝牙数据缓冲区
      eegDataBuffer: [],          // EEG数据缓冲区
      
      // 选中的记录信息
      selectedRecord: null       // DataRecord组件中用户选择的记录
    }
  },
  created() {
    this.fileInput = document.createElement('input')
    this.fileInput.type = 'file'
    this.fileInput.accept = '.csv,.xlsx,.xls,.txt'
    this.fileInput.addEventListener('change', (event) => {
      this.handleFileSelected(event)
    })
    
    // 初始化WebSocket连接
    this.initWebSocket()
  },
  methods: {
    /**
     * 初始化WebSocket连接
     */
    initWebSocket() {
      try {
        const wsUrl = 'ws://localhost:8000/ws/eeg/'
        console.log('尝试连接到WebSocket:', wsUrl)
        
        this.websocket = new WebSocket(wsUrl)
        
        this.websocket.onopen = () => {
          console.log('WebSocket连接成功')
          this.logContent += `[${new Date().toLocaleTimeString()}] WebSocket连接成功\n`
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
          this.logContent += `[${new Date().toLocaleTimeString()}] WebSocket连接已断开\n`
          // 如果是意外断开，尝试重新连接
          if (this.isConnected || this.isRecording) {
            this.logContent += `[${new Date().toLocaleTimeString()}] 尝试重新连接WebSocket...\n`
            setTimeout(() => {
              this.initWebSocket()
            }, 3000)
          }
        }
        
        this.websocket.onerror = (error) => {
          console.error('WebSocket连接错误:', error)
          this.logContent += `[${new Date().toLocaleTimeString()}] WebSocket连接错误: ${error.message}\n`
        }
      } catch (error) {
        console.error('WebSocket连接异常:', error)
        this.logContent += `[${new Date().toLocaleTimeString()}] WebSocket连接异常: ${error.message}\n`
      }
    },

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
            // 修复验证逻辑，支持UUID格式的recording_id
            if (!data.recording_id) {
              throw new Error(`后端未返回recording_id`)
            }

            // 验证UUID格式 (标准UUID格式)
            const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
            // 或者验证更宽松的格式（包括您数据库中的格式）
            const looseUuidRegex = /^[0-9a-f\-]+$/i;
            
            if (!uuidRegex.test(data.recording_id) && !looseUuidRegex.test(data.recording_id)) {
              throw new Error(`后端返回的recording_id无效：${data.recording_id}`)
            }

            this.importedFileHashes.add(fileHash)
            this.$message.success(`文件上传成功：${originalFileName}（记录ID：${data.recording_id}）`)
            this.logContent += `[${new Date().toLocaleTimeString()}] 导入成功，记录ID：${data.recording_id}\n`
            this.importedFileName = originalFileName
            this.currentRecordingId = data.recording_id

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
     * 处理DataRecord组件中选中的记录
     */
    onRecordSelected(record) {
      this.selectedRecord = record;
    },
    
    /**
     * 分析数据入口
     */
    analyzeData() {
      if (this.reportContent.includes('正在分析数据')) {
        this.$message.warning('正在分析中，请稍候...')
        return
      }

      // 如果用户在DataRecord组件中选择了记录，则使用该记录进行分析
      if (this.selectedRecord) {
        // 构造分析所需的数据
        const recordingId = this.selectedRecord.recording_id;
        const fileName = this.selectedRecord.name;
        
        this.$confirm(
          `是否分析选中的记录：${fileName}（记录ID：${recordingId}）？`,
          '确认分析',
          {
            confirmButtonText: '确认分析',
            cancelButtonText: '取消',
            type: 'question'
          }
        ).then(() => {
          // 设置当前记录ID和文件名，然后调用分析方法
          this.currentRecordingId = recordingId;
          this.importedFileName = fileName;
          this.analyzeExistingData();
        }).catch(() => {
          // 用户取消操作
          this.$message.info('已取消分析');
        });
        return;
      }

      // 如果有已导入的文件，则询问是否分析该文件
      if ( this.importedFileName) {
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
      
      // 构造请求参数 - 修复：保持recording_id为原始格式
      const requestData = {
        recording_id: this.currentRecordingId,  // 修复：不再转换为整数
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
     * 检查蓝牙支持
     */
    checkBluetoothSupport() {
      if (!navigator.bluetooth) {
        this.$message.error('当前浏览器不支持蓝牙功能')
        return false
      }
      return true
    },

    /**
     * 扫描蓝牙设备
     */
    async scanDevices() {
      if (!this.checkBluetoothSupport()) return
     
      try {
        this.$message.info('正在扫描蓝牙设备...')
        this.logContent += `[${new Date().toLocaleTimeString()}] 开始扫描蓝牙设备\n`
        
        const device = await navigator.bluetooth.requestDevice({
          acceptAllDevices: true,
          optionalServices: ['0000ffe0-0000-1000-8000-00805f9b34fb'] // JDY-18蓝牙模块的服务UUID
        })
        
        this.bluetoothDevice = device
        this.$message.success(`找到设备: ${device.name || '未知设备'}`)
        this.logContent += `[${new Date().toLocaleTimeString()}] 找到蓝牙设备: ${device.name || device.id}\n`
        this.deviceAddress = device.id
      } catch (error) {
        this.$message.error(`扫描失败: ${error.message}`)
        this.logContent += `[${new Date().toLocaleTimeString()}] 蓝牙设备扫描失败: ${error.message}\n`
      }
    },

    /**
     * 连接蓝牙设备
     */
    async connectBluetoothDevice() {
      if (!this.bluetoothDevice) {
        this.$message.warning('请先扫描并选择蓝牙设备')
        return
      }

      try {
        this.$message.info('正在连接蓝牙设备...')
        this.logContent += `[${new Date().toLocaleTimeString()}] 尝试连接蓝牙设备\n`
        
        // 连接GATT服务器
        this.bluetoothServer = await this.bluetoothDevice.gatt.connect()
        
        // 获取服务
        const service = await this.bluetoothServer.getPrimaryService('0000ffe0-0000-1000-8000-00805f9b34fb')
        
        // 获取特征值
        this.bluetoothCharacteristic = await service.getCharacteristic('0000ffe1-0000-1000-8000-00805f9b34fb')
        
        // 订阅通知
        await this.bluetoothCharacteristic.startNotifications()
        
        // 添加数据接收事件监听器
        this.bluetoothCharacteristic.addEventListener('characteristicvaluechanged', this.handleBluetoothData)
        
        this.isConnected = true
        this.deviceStatus = '已连接'
        this.$message.success('蓝牙设备连接成功')
        this.logContent += `[${new Date().toLocaleTimeString()}] 蓝牙设备连接成功\n`
      } catch (error) {
        this.$message.error(`连接失败: ${error.message}`)
        this.logContent += `[${new Date().toLocaleTimeString()}] 蓝牙设备连接失败: ${error.message}\n`
      }
    },

    /**
     * 断开蓝牙设备连接
     */
    async disconnectBluetoothDevice() {
      try {
        if (this.bluetoothCharacteristic) {
          await this.bluetoothCharacteristic.stopNotifications()
          this.bluetoothCharacteristic.removeEventListener('characteristicvaluechanged', this.handleBluetoothData)
        }
        
        if (this.bluetoothServer && this.bluetoothServer.connected) {
          await this.bluetoothServer.disconnect()
        }
        
        this.isConnected = false
        this.deviceStatus = '未连接'
        this.$message.info('蓝牙设备已断开')
        this.logContent += `[${new Date().toLocaleTimeString()}] 蓝牙设备已断开连接\n`
      } catch (error) {
        this.$message.error(`断开连接失败: ${error.message}`)
        this.logContent += `[${new Date().toLocaleTimeString()}] 蓝牙设备断开连接失败: ${error.message}\n`
      }
    },

    /**
     * 处理蓝牙数据
     */
    handleBluetoothData(event) {
      try {
        const value = event.target.value
        const data = new Uint8Array(value.buffer)
        
        // 将新数据添加到缓冲区
        const newBuffer = new Uint8Array(this.bluetoothBuffer.length + data.length)
        newBuffer.set(this.bluetoothBuffer)
        newBuffer.set(data, this.bluetoothBuffer.length)
        this.bluetoothBuffer = newBuffer
        
        // 处理缓冲区中的数据
        this.processBluetoothBuffer()
      } catch (error) {
        this.$message.error(`处理蓝牙数据出错: ${error.message}`)
        this.logContent += `[${new Date().toLocaleTimeString()}] 处理蓝牙数据出错: ${error.message}\n`
      }
    },

    /**
     * 处理蓝牙数据缓冲区
     */
    processBluetoothBuffer() {
      try {
        while (this.bluetoothBuffer.length >= 32) {
          // 查找同步头 (AA AA 20)
          let syncPos = -1
          for (let i = 0; i <= this.bluetoothBuffer.length - 3; i++) {
            if (this.bluetoothBuffer[i] === 0xAA && 
                this.bluetoothBuffer[i + 1] === 0xAA && 
                this.bluetoothBuffer[i + 2] === 0x20) {
              syncPos = i
              break
            }
          }
          
          // 如果没有找到同步头
          if (syncPos === -1) {
            // 如果缓冲区太大，清空它
            if (this.bluetoothBuffer.length > 100) {
              this.bluetoothBuffer = new Uint8Array()
            }
            return
          }
          
          // 如果同步头不在开头，删除前面的数据
          if (syncPos > 0) {
            this.bluetoothBuffer = this.bluetoothBuffer.slice(syncPos)
            continue
          }
          
          // 检查是否有完整数据包
          if (this.bluetoothBuffer.length < 32) {
            return
          }
          
          // 提取数据包
          const packet = this.bluetoothBuffer.slice(0, 32)
          this.bluetoothBuffer = this.bluetoothBuffer.slice(32)
          
 
          // 解析数据包
          const parsedData = this.parseBluetoothPacket(packet)
          if (parsedData) {
            // 只有在录制状态下才将解析后的数据发送到后端
            if (this.isRecording) {
              this.sendEEGDataToBackend(parsedData)
              // 将数据添加到录制缓冲区
              this.eegDataBuffer.push(parsedData)
            }
          }
        }
      } catch (error) {
        this.$message.error(`处理蓝牙数据缓冲区出错: ${error.message}`)
        this.logContent += `[${new Date().toLocaleTimeString()}] 处理蓝牙数据缓冲区出错: ${error.message}\n`
        this.bluetoothBuffer = new Uint8Array()
      }
    },

    /**
     * 解析蓝牙数据包
     */
    parseBluetoothPacket(packet) {
      try {
        // 检查数据包长度和同步头
        if (packet.length < 32 || 
            packet[0] !== 0xAA || 
            packet[1] !== 0xAA || 
            packet[2] !== 0x20) {
          return null
        }
        
        // 解析信号质量 (索引4)
        const signalQuality = packet[4]
        
        // 检查EEG功率开始标记 (索引5)
        if (packet[5] !== 0x83) {
          console.warn("缺少EEG功率开始标记")
          return null
        }
        
        // 解析EEG功率谱 (索引6-29, 8个频段×3字节)
        const eegBands = [
          'Delta', 'Theta',
          'Low Alpha', 'High Alpha',
          'Low Beta', 'High Beta',
          'Low Gamma', 'Middle Gamma'
        ]
        
        const eegPower = {}
        let index = 6
        
        for (const band of eegBands) {
          // 每个频段3个字节 (高位->低位)
          const value = (packet[index] << 16) | (packet[index + 1] << 8) | packet[index + 2]
          eegPower[band] = value
          index += 3
        }
        
        // 解析专注度 (0x04) 和放松度 (0x05)
        let attention = 0
        let meditation = 0
        
        while (index < 30) {
          const code = packet[index]
          if (code === 0x04) {
            attention = packet[index + 1]
            index += 2
          } else if (code === 0x05) {
            meditation = packet[index + 1]
            index += 2
          } else {
            index += 1
          }
        }
        
        return {
          timestamp: new Date().toISOString(),
          signalQuality: signalQuality,
          attention: attention,
          meditation: meditation,
          ...eegPower
        }
      } catch (error) {
        console.error(`解析蓝牙数据包出错: ${error.message}`)
        return null
      }
    },

    /**
     * 发送EEG数据到后端
     */
    sendEEGDataToBackend(data) {
      // 检查WebSocket连接状态
      if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
        // 如果WebSocket未连接，尝试重新连接
        this.initWebSocket()
        // 即使重新连接，当前这次数据也发送不了，所以直接返回
        return
      }
      
      const eegData = {
        type: 'eeg_data',
        timestamp: data.timestamp,
        data: data
      }
      
      try {
        this.websocket.send(JSON.stringify(eegData))
        console.log('数据已发送到后端:', eegData)
      } catch (error) {
        this.$message.error('发送数据失败: ' + error.message)
        this.logContent += `[${new Date().toLocaleTimeString()}] 发送数据失败: ${error.message}\n`
      }
    },

    /**
     * 连接设备函数（修改为仅支持蓝牙设备）
     */
    async connectDevice() {
      // 如果已经连接，断开连接
      if (this.isConnected) {
        if (this.bluetoothDevice) {
          await this.disconnectBluetoothDevice()
        } else {
          this.isConnected = false
          this.$message.info('设备已断开')
        }
        return
      }
      
      // 检查蓝牙支持
      if (!this.checkBluetoothSupport()) {
        this.$message.error('当前浏览器不支持蓝牙功能，无法连接设备')
        return
      }
      
      // 尝试连接蓝牙设备
      if (this.bluetoothDevice) {
        await this.connectBluetoothDevice()
        return
      }
      
      // 如果没有蓝牙设备，拒绝连接
      this.$message.error('未找到蓝牙设备，请先扫描并连接蓝牙设备')
      this.logContent += `[${new Date().toLocaleTimeString()}] 尝试连接但未找到蓝牙设备\n`
    },

    toggleRecording() {
      this.isRecording = !this.isRecording
      
      if (this.isRecording) {
        if (!this.isConnected) {
          this.$message.warning('请先连接设备')
          this.isRecording = false
          return
        }
        
        // 确保WebSocket连接正常
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
          this.$message.warning('WebSocket连接未建立，请重新连接设备')
          this.isRecording = false
          return
        }
        
        // 发送开始记录指令到后端
        const startRecordMsg = {
          type: 'start_recording',
          name: `EEG_Recording_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}`,
          description: '实时EEG数据记录'
        };
        
        try {
          this.websocket.send(JSON.stringify(startRecordMsg));
          this.$message.success('开始记录数据')
        } catch (error) {
          this.$message.error('发送开始记录指令失败: ' + error.message)
          this.logContent += `[${new Date().toLocaleTimeString()}] 发送开始记录指令失败: ${error.message}\n`
          this.isRecording = false
        }
      } else {
        // 发送停止记录指令到后端
        const stopRecordMsg = {
          type: 'stop_recording'
        };
        
        try {
          if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(stopRecordMsg));
            this.$message.info('已停止记录数据')
          } else {
            this.$message.error('WebSocket连接未建立，无法停止记录')
          }
          // 清空数据缓冲区
          this.eegDataBuffer = []
        } catch (error) {
          this.$message.error('发送停止记录指令失败: ' + error.message)
          this.logContent += `[${new Date().toLocaleTimeString()}] 发送停止记录指令失败: ${error.message}\n`
        }
      }
    },

    handleWebSocketMessage(data) {
      switch (data.type) {
        case 'data_received':
          // 数据接收确认，无需特殊处理
          break;
          
        case 'recording_status':
          if (data.status === 'started') {
            this.currentRecordingId = data.recording_id;
            this.logContent += `[${new Date().toLocaleTimeString()}] 开始记录，记录ID: ${data.recording_id}\n`;
          } else if (data.status === 'stopped') {
            this.logContent += `[${new Date().toLocaleTimeString()}] 停止记录，记录ID: ${data.recording_id}\n`;
            this.currentRecordingId = '';
          } else if (data.status === 'error') {
            this.$message.error(data.message);
            this.logContent += `[${new Date().toLocaleTimeString()}] 记录错误: ${data.message}\n`;
            this.isRecording = false;
          }
          break;
          
        case 'error':
          this.$message.error('WebSocket错误: ' + data.message);
          this.logContent += `[${new Date().toLocaleTimeString()}] WebSocket错误: ${data.message}\n`;
          break;
          
        default:
          this.logContent += `[${new Date().toLocaleTimeString()}] 接收到未知类型消息: ${JSON.stringify(data)}\n`;
      }
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
          this.$message.error('报告加载失败: ' + error.message)
          this.logContent += `[${new Date().toLocaleTimeString()}] 报告加载失败: ${error.message}\n`
        })
    },

    clearLog() {
      this.logContent = ''
      this.$message.success('日志已清空')
    },

    testAPI() {
      const testUrl = '/api/test-api-key/'
      const requestData = {
        api_key: this.apiKey.trim()
      }

      fetch(testUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken()
        },
        body: JSON.stringify(requestData)
      })
        .then(response => response.json())
        .then(data => {
          if (data.status === 'success') {
            this.$message.success(data.message)
            this.logContent += `[${new Date().toLocaleTimeString()}] API密钥测试成功\n`
          } else {
            this.$message.error(data.message)
            this.logContent += `[${new Date().toLocaleTimeString()}] API密钥测试失败: ${data.message}\n`
          }
        })
        .catch(error => {
          this.$message.error('API密钥测试失败: ' + error.message)
          this.logContent += `[${new Date().toLocaleTimeString()}] API密钥测试失败: ${error.message}\n`
        })
    }
  }
}
</script>

<style scoped>
.report-content * {
  color: black !important;
}
/* ... existing styles ... */
</style>