<template>
  <div class="status-bar">
    <span class="status-item">
      <i class="el-icon-circle-check" style="color: green;"></i> 
      后端: 已连接
    </span>
    <span class="status-item">
      <i 
        :class="isConnected ? 'el-icon-circle-check' : 'el-icon-circle-cross'"
        :style="{color: isConnected ? 'green' : 'red'}">
      </i> 
      设备: {{ deviceStatus }}
    </span>
    <span class="status-item">
      <i 
        :class="isRecording ? 'el-icon-circle-check' : 'el-icon-circle-cross'"
        :style="{color: isRecording ? 'green' : 'red'}">
      </i> 
      数据: {{ isRecording ? '正在记录' : '未连接' }}
    </span>
    <span class="status-item">
      <i class="el-icon-circle-cross" style="color: red;"></i> 
      API: 未连接
    </span>
  </div>
</template>

<script>
export default {
  name: 'StatusBar',
  props: {
    isConnected: {
      type: Boolean,
      default: false
    },
    isRecording: {
      type: Boolean,
      default: false
    },
    deviceStatus: {
      type: String,
      default: '未连接'
    }
  }
}
</script>
