<template>
  <div class="card">
    <h3><i class="el-icon-setting"></i> 分析配置</h3>
    <div class="form-group">
      <label>API密钥</label>
      <el-input 
        class="custom-input" 
        :value="value" 
        @input="$emit('input', $event)"
        placeholder="请输入API密钥">
      </el-input>
    </div>
    <el-button type="primary" size="small" @click="$emit('test-api')">测试API</el-button>
    <div class="history-file">
      <p>历史数据文件</p>
      <p style="color: #99ccff;">暂无历史数据</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AnalysisConfig',
  props: {
    value: {
      type: String,
      default: '51e09aa5-d2dd-41ab-bf91-51ef798844e7'
    }
  }
}
</script>