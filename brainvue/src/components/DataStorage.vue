<template>
  <div class="card">
    <h3><i class="el-icon-document"></i> 数据保存</h3>
    <div class="data-status">
      <p>{{ dataStatus }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DataStorage',
  props: {
    dataStatus: {
      type: String,
      default: '未保存数据'
    }
  },
  mounted() {
    this.fetchRecordingCount();
  },
  methods: {
    async fetchRecordingCount() {
      try {
        const response = await fetch('/api/recording/count', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.apiKey}` // 如果需要认证
          }
        });

        if (response.ok) {
          const count = await response.json();
          this.$emit('update-data-status', `已保存 ${count} 次记录`);
        } else {
          console.error('Failed to fetch recording count');
          this.$emit('update-data-status', '无法获取记录数量');
        }
      } catch (error) {
        console.error('Error:', error);
        this.$emit('update-data-status', '网络错误');
      }
    }
  },
  computed: {
    apiKey() {
      return this.$store.state.apiKey; // 假设 API 密钥存储在 Vuex 中
    }
  }
}
</script>