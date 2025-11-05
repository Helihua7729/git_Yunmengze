<template>
  <div class="card">
    <h3><i class="el-icon-mobile-phone"></i> 设备连接</h3>
    <div class="form-group">
      <label>蓝牙设备地址</label>
      <el-input 
        
        :value="value" 
        @input="$emit('input', $event)"
        placeholder="例如: JDY-18">
      </el-input>
      <el-button 
        id="scann_button" 
        type="primary" 
        size="small" 
        @click="$emit('scan')">
        扫描
      </el-button>
    </div>
    <div class="status-info">
      <p>连接状态: 
        <span :style="{color: deviceStatus === '已连接' ? 'green' : 'red'}">
          {{ deviceStatus }}
        </span>
      </p>
      <p>信号质量: <span>-- /200</span></p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DeviceConnection',
  props: {
    value: {
      type: String,
      default: ''
    },
    deviceStatus: {
      type: String,
      default: '未连接'
    }
  }
}
</script>
