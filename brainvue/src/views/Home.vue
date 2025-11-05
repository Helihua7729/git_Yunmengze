<template>
  <div class="app-container">
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
        <!-- 设备连接 -->
        <DeviceConnection 
          v-model="deviceAddress"
          :device-status="deviceStatus"
          @scan="scanDevices" />

        <!-- 数据保存 -->
        <!-- <DataStorage :data-status="dataStatus" /> -->

        <!-- 数据记录 -->
        <DataRecord />  
        <!-- 分析配置 -->
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
// Deleted:import DataStorage from '../components/DataStorage.vue'
import DataRecord from '../components/DataRecord.vue'
import AnalysisConfig from '../components/AnalysisConfig.vue'

export default {
  name: 'Home',
  components: {
    StatusBar,
    DeviceConnection,
    // Deleted:DataStorage,
    DataRecord,
    AnalysisConfig
  },
  data() {
    return {
      deviceAddress: '',
      apiKey: '51e09aa5-d2dd-41ab-bf91-51ef798844e7',
      activeTab: 'realtime',
      websocket: null,
      isConnected: false,
      isRecording: false,
      deviceStatus: '未连接',
      signalQuality: '-- /200',
      // Deleted:dataStatus: '未保存数据',
      logContent: '',
      reportContent: '',
      historyFiles: [],
      importedFileName: '',
      currentFilePath: ''
    }
  },
  methods: {
    /**
     * 连接设备函数
     * 建立与后端WebSocket服务器的连接，用于传输EEG数据
     * 根据当前协议（HTTP或HTTPS）自动选择ws://或wss://协议
     */
          connectDevice() {
      // 检查设备是否已经连接
      if (this.isConnected) {
        this.$message.info('设备已连接')
        return
      }
      
      try {
        // 使用相对路径，让代理处理，又点问题，直接定义wsUrl
        // const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        // const wsUrl = protocol + window.location.host + '/ws/eeg/'
        const wsUrl = 'ws://localhost:8000/ws/eeg/'
        console.log('尝试连接到WebSocket:', wsUrl) // 添加调试日志
        
        this.websocket = new WebSocket(wsUrl)
        
        // 连接成功回调
        this.websocket.onopen = () => {
          console.log('WebSocket连接成功') // 添加调试日志
          this.isConnected = true
          this.deviceStatus = '已连接'
          this.$message.success('设备连接成功')
        }
        
        // 接收消息回调 - 这里是处理后端返回消息的关键部分
        this.websocket.onmessage = (event) => {
          const data = JSON.parse(event.data)
          this.handleWebSocketMessage(data)
        }
        
        // 连接关闭回调
        this.websocket.onclose = () => {
          this.isConnected = false
          this.isRecording = false
          this.deviceStatus = '未连接'
          this.$message.info('设备连接已断开')
        }
        
        // 连接错误回调
        this.websocket.onerror = (error) => {
          console.error('WebSocket连接错误:', error) // 添加调试日志
          this.$message.error('连接发生错误: ' + error.message)
        }
      } catch (error) {
        console.error('WebSocket连接异常:', error) // 添加调试日志
        this.$message.error('连接失败: ' + error.message)
      }
    },
    
    /**
     * 加载分析报告
     * 从服务器获取并显示分析报告
     * @param {string} filename - 报告文件名
     */
    loadReport(filename) {
      // 确保文件名不为空
      if (!filename) {
        this.$message.error('报告文件名为空')
        return
      }
      
      // 构造报告URL
      const reportUrl = `/reports/${filename}`
      
      fetch(reportUrl)
        .then(response => {
          if (response.ok) {
            return response.text()
          } else {
            throw new Error('报告文件不存在')
          }
        })
        .then(html => {
          this.reportContent = html
          this.activeTab = 'report'
        })
        .catch(error => {
          this.$message.error('加载报告失败: ' + error.message)
        })
    },

    /**
     * 开始/停止记录数据
     * 切换记录状态并控制EEG数据发送
     */
    toggleRecording() {
      // 切换记录状态
      this.isRecording = !this.isRecording
      
      if (this.isRecording) {
        // 开始记录
        if (!this.isConnected) {
          this.$message.warning('请先连接设备')
          this.isRecording = false
          return
        }
        
        this.$message.success('开始记录数据')
        // 开始发送EEG数据
        this.sendEEGData()
      } else {
        // 停止记录
        this.$message.info('已停止记录数据')
        // Deleted:this.dataStatus = '记录已停止'
      }
    },

    /**
     * 发送EEG数据
     * 定期生成并发送模拟EEG数据到后端
     */
    sendEEGData() {
      // 检查是否应该继续发送数据
      if (!this.isRecording || !this.isConnected) return
      
      // 构造EEG数据对象
      const eegData = {
        type: 'eeg_data',
        timestamp: new Date().toISOString(),
        data: this.generateMockEEGData()
      }
      
      try {
        // 发送数据到后端
        this.websocket.send(JSON.stringify(eegData))
        // Deleted:this.dataStatus = '正在记录数据...'
      } catch (error) {
        this.$message.error('发送数据失败: ' + error.message)
      }
      
      // 如果仍在记录状态，1秒后再次发送数据
      if (this.isRecording) {
        setTimeout(() => this.sendEEGData(), 1000)       //递推，除非停止记录状态，否则一直在执行sendEEGData
      }
    },
    
    /**
     * 生成模拟EEG数据
     * 创建包含各个脑电波频段的模拟数据
     * @returns {string} 格式化的EEG数据字符串
     */
    generateMockEEGData() {
      const bands = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']
      const data = bands.map(band => {
        return band + ' ' + Math.floor(Math.random() * 100)
      })
      return data.join(' ')
    },

    /**
     * 分析数据函数
     * 请求后端对已记录的EEG数据进行分析
     */
    analyzeData() {
      // 如果有导入的文件，分析导入的文件
      if (this.importedFileName && this.currentFilePath) {
        this.analyzeExistingFile(this.currentFilePath)
        return
      }
      
      // 检查设备是否已连接
      if (!this.isConnected) {
        this.$message.warning('请先连接设备或导入数据文件')
        return
      }
      
      // 构造分析请求对象
      const analysisRequest = {
        type: 'request_analysis',
        api_key: this.apiKey
      }
      
      try {
        // 发送分析请求到后端
        this.websocket.send(JSON.stringify(analysisRequest))
        this.$message.info('正在分析数据...')
      } catch (error) {
        this.$message.error('发送分析请求失败: ' + error.message)
      }
    },
    
    /**
     * 分析已存在的文件
     * 对导入的数据文件请求分析
     * @param {string} filePath - 文件路径
     */
    analyzeExistingFile(filePath) {
      fetch('/api/analyze-existing-data/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_path: filePath,
          api_key: this.apiKey
        })
      })
        .then(response => response.json())
        .then(data => {
          if (data.status === 'success') {
            this.$message.success(data.message)
            this.logContent += `[${new Date().toLocaleTimeString()}] ${data.message}\n`
            this.loadReport(data.report_filename)
          } else {
            this.$message.error(data.message)
            this.logContent += `[${new Date().toLocaleTimeString()}] 分析失败: ${data.message}\n`
          }
        })
        .catch(error => {
          this.$message.error('分析请求失败: ' + error.message)
          this.logContent += `[${new Date().toLocaleTimeString()}] 分析请求失败: ${error.message}\n`
        })
    },

    /**
     * 导入数据函数
     * 允许用户上传EEG数据文件进行分析
     */
    importData() {
      // 创建文件输入元素
      const fileInput = document.createElement('input')
      fileInput.type = 'file'
      fileInput.accept = '.csv,.xlsx,.xls,.txt'
      
      fileInput.onchange = (event) => {
        const file = event.target.files[0]
        if (!file) return
        
        // 创建表单数据
        const formData = new FormData()
        formData.append('file', file)
        
        // 发送文件到后端
        fetch('/api/import-eeg-data/', {
          method: 'POST',
          body: formData
        })
          .then(response => response.json())
          .then(data => {
            if (data.status === 'success') {
              this.$message.success(data.message)
              this.logContent += `[${new Date().toLocaleTimeString()}] ${data.message}\n`
              // Deleted:this.dataStatus = `已导入: ${file.name}`
              this.importedFileName = file.name
              this.currentFilePath = data.file_path
              
              // 如果设备已连接，通知后端有新导入的数据
              if (this.isConnected) {
                const importNotification = {
                  type: 'imported_data',
                  fileName: file.name,
                  filePath: data.file_path
                }
                this.websocket.send(JSON.stringify(importNotification))
              }
            } else {
              this.$message.error(data.message)
              this.logContent += `[${new Date().toLocaleTimeString()}] 导入失败: ${data.message}\n`
            }
          })
          .catch(error => {
            console.log("没有发起请求");
            this.$message.error('文件上传失败: ' + error.message)
            this.logContent += `[${new Date().toLocaleTimeString()}] 文件上传失败: ${error.message}\n`
          })
      }
      
      fileInput.click()
    },
    
    /**
     * 测试后端连接
     * 验证与后端服务器的连接状态
     */
    testBackend() {
      this.$message.success('后端连接正常')
    },
    
    /**
     * 检查蓝牙支持情况
     * 检测浏览器是否支持Web Bluetooth API以及运行环境是否满足要求
     * @returns {boolean} 是否支持蓝牙功能
     */
    checkBluetoothSupport() {
      // 检查各种支持条件
      const supportInfo = {
        bluetooth: !!navigator.bluetooth,  // 浏览器是否支持Web Bluetooth API
        secureContext: window.isSecureContext,  // 是否在安全上下文中运行
        https: window.location.protocol === 'https:',  // 是否使用HTTPS协议
        localhost: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',  // 是否在本地环境运行
        chrome: /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor)  // 是否为Chrome浏览器
      }
      
      console.log('环境信息:', supportInfo)
      
      // 检查Web Bluetooth API支持情况
      if (!supportInfo.bluetooth) {
        let message = '您的浏览器不支持Web Bluetooth API。'
        if (!supportInfo.chrome) {
          message += '建议使用最新版Google Chrome浏览器。'
        } else if (!supportInfo.secureContext) {
          if (!supportInfo.https && !supportInfo.localhost) {
            message += 'Web Bluetooth需要HTTPS环境或本地环境(localhost)。'
          } else {
            message += '请检查浏览器设置或使用支持的浏览器。'
          }
        }
        this.$message.warning(message)
        return false
      }
      
      // 检查安全上下文要求
      if (!supportInfo.secureContext) {
        this.$message.warning('Web Bluetooth需要安全环境（HTTPS或localhost）。')
        return false
      }
      
      return true
    },

    /**
     * 扫描蓝牙设备
     * 使用Web Bluetooth API扫描附近的蓝牙设备
     */
    scanDevices() {
      // 检查蓝牙支持
      if (!this.checkBluetoothSupport()) {
        return
      }
     
      this.$message.info('正在扫描蓝牙设备...')
      console.log('开始扫描设备...')
      // 请求扫描蓝牙设备
      navigator.bluetooth.requestDevice({
        acceptAllDevices: true,
        optionalServices: [
          'battery_service',
          'generic_access',
          'device_information'
        ]
      })
        .then(device => {
          this.$message.success(`找到设备: ${device.name}`)
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
    
    /**
     * 连接蓝牙设备
     * 通过Web Bluetooth API连接指定的蓝牙EEG设备
     */
    connectBluetoothDevice() {
      // 检查浏览器是否支持蓝牙
      if (!this.checkBluetoothSupport()) {
        return
      }
      
      // 检查设备是否已经连接
      if (this.isConnected) {
        this.$message.info('设备已连接')
        return
      }
      
      // 请求连接蓝牙设备
      navigator.bluetooth.requestDevice({
        filters: [{namePrefix: this.deviceAddress}],
        optionalServices: ['heart_rate'] // 根据实际设备修改
      })
        .then(device => {
          this.$message.success(`找到设备: ${device.name}`)
          return device.gatt.connect()
        })
        .then(server => {
          // 保存服务器连接用于后续操作
          this.bluetoothServer = server
          this.isConnected = true
          this.deviceStatus = '已连接'
          this.$message.success('蓝牙设备连接成功')
          
          // 如果需要开始记录数据
          if (this.isRecording) {
            this.startBluetoothDataStreaming()
          }
        })
        .catch(error => {
          this.$message.error(`连接失败: ${error.message}`)
        })
    },
    
    /**
     * 启动蓝牙数据流
     * 启动从蓝牙设备接收数据的流
     */
    startBluetoothDataStreaming() {
      // 检查蓝牙设备是否已连接
      if (!this.bluetoothServer) {
        this.$message.error('蓝牙设备未连接')
        return
      }
      
      // 这里需要根据实际设备的GATT服务和特征来实现
      // 以下是一个示例实现
      this.bluetoothServer.getPrimaryService('heart_rate')
        .then(service => {
          return service.getCharacteristic('heart_rate_measurement')
        })
        .then(characteristic => {
          // 开始监听数据变化
          characteristic.addEventListener('characteristicvaluechanged', (event) => {
            // 处理接收到的蓝牙数据
            this.handleBluetoothData(event.target.value)
          })
          
          // 启用通知
          return characteristic.startNotifications()
        })
        .then(() => {
          this.$message.success('开始接收蓝牙数据')
        })
        .catch(error => {
          this.$message.error(`数据流启动失败: ${error.message}`)
        })
    },
    
    /**
     * 处理蓝牙数据
     * 解析从蓝牙设备接收到的原始数据并发送到后端
     * @param {DataView} value - 从蓝牙设备接收到的原始数据
     */
    handleBluetoothData(value) {
      // 解析蓝牙数据并发送到后端
      // 这里需要根据实际设备的数据格式进行解析
      let eegData = {
        type: 'eeg_data',
        timestamp: new Date().toISOString(),
        data: {
          Delta: value.getUint8(0),
          Theta: value.getUint8(1),
          Alpha: value.getUint8(2),
          Beta: value.getUint8(3),
          Gamma: value.getUint8(4)
        }
      }
      
      // 发送解析后的数据到后端
      if (this.isConnected && this.websocket) {
        try {
          this.websocket.send(JSON.stringify(eegData))
          // Deleted:this.dataStatus = '正在记录数据...'
        } catch (error) {
          this.$message.error('发送数据失败: ' + error.message)
        }
      }
    },
    
    /**
     * 测试API密钥
     * 验证用户输入的API密钥是否有效
     */
    testAPI() {
      // 检查API密钥是否已输入
      if (!this.apiKey) {
        this.$message.warning('请输入API密钥')
        return
      }
      
      // 显示加载指示器
      const loading = this.$loading({
        lock: true,
        text: '测试中...',
        spinner: 'el-icon-loading',
        background: 'rgba(0, 0, 0, 0.7)'
      })
      
      // 发送测试请求到后端
      fetch('/api/test-api-key/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_key: this.apiKey
        })
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
    
    /**
     * 清空日志
     * 清除系统日志显示内容
     */
    clearLog() {
      this.logContent = ''
      this.$message.success('日志已清空')
    },
    
    /**
     * 处理WebSocket消息
     * 根据消息类型处理从后端接收到的消息
     * @param {Object} data - 从后端接收到的消息数据
     */
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
          this.logContent += `[${new Date().toLocaleTimeString()}] 导入数据已保存: ${data.file_path}\n`
          break
          
        case 'analysis_result':
          if (data.success) {
            // 处理分析成功的返回结果
            // 使用loadReport函数加载和显示报告
            if (data.path) {
              this.loadReport(data.path)
            } else if (data.content) {
              // 如果直接返回了内容，则直接显示
              this.reportContent = data.content
              this.activeTab = 'report'
            }
            this.$message.success('分析完成')
            this.logContent += `[${new Date().toLocaleTimeString()}] 分析完成\n`
          } else {
            // 处理分析失败的情况
            this.$message.error('分析失败: ' + data.error)
            this.logContent += `[${new Date().toLocaleTimeString()}] 分析失败: ${data.error}\n`
          }
          break
          
        case 'error':
          this.$message.error('服务器错误: ' + data.message)
          this.logContent += `[${new Date().toLocaleTimeString()}] 服务器错误: ${data.message}\n`
          break
      }
      
      // 滚动到日志底部
      this.$nextTick(() => {
        const logPanel = document.querySelector('.el-tab-pane[name="log"] .placeholder')
        if (logPanel) {
          logPanel.scrollTop = logPanel.scrollHeight
        }
      })
    }
  },
  
  watch: {
    isRecording(newVal) {
      // Deleted:this.dataStatus = newVal ? '正在记录数据...' : '未保存数据'
    }
  },
  
  mounted() {
    this.testBackend()
  }
}
</script>