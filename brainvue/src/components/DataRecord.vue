<template>
  <div class="card">
    <h3><i class="el-icon-document"></i> 数据记录</h3>
    <div class="data-status">
      <p v-if="latestRecord">记录名称: {{ latestRecord.name }}</p>
      <p v-if="latestRecord">开始时间: {{ formatDate(latestRecord.start_time) }}</p>
      <p v-if="latestRecord">结束时间: {{ formatDate(latestRecord.end_time) }}</p>
      <p v-if="latestRecord">数据点数: {{ latestRecord.data_count }}</p>
      <p v-if="!latestRecord && loaded">暂无记录</p>
    </div>

    <!-- 更多按钮 -->
    <button @click="loadAllRecords" class="more-btn">更多</button>

    <!-- 下拉框展示所有记录 -->
    <div v-if="showAllRecords" class="dropdown-container">
      <select v-model="selectedRecord" class="record-dropdown" @change="onRecordSelect">
        <option value="">请选择一条记录</option>
        <option
          v-for="record in allRecords"
          :key="record.recording_id"
          :value="record.recording_id"
        >
          {{ record.name }} ({{ formatDate(record.start_time) }})
        </option>
      </select>
      
      <!-- 显示选中记录的详细信息 -->
      <div v-if="selectedRecordDetails" class="record-details">
        <h4>记录详情:</h4>
        <p>记录ID: {{ selectedRecordDetails.recording_id }}</p>
        <p>记录名称: {{ selectedRecordDetails.name }}</p>
        <p>开始时间: {{ formatDate(selectedRecordDetails.start_time) }}</p>
        <p>结束时间: {{ formatDate(selectedRecordDetails.end_time) }}</p>
        <p>描述: {{ selectedRecordDetails.description }}</p>
        <p>数据点数: {{ selectedRecordDetails.data_count }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { getLatestEEGRecord, getAllEEGRecords } from '@/utils/api';

export default {
  name: 'DataRecord',
  data() {
    return {
      latestRecord: null,
      allRecords: [],
      showAllRecords: false,
      selectedRecord: '',
      selectedRecordDetails: null,
      loaded: false
    };
  },
  mounted() {
    this.fetchLatestRecord();
  },
  methods: {
    async fetchLatestRecord() {
      try {
        const response = await getLatestEEGRecord();
        this.latestRecord = response.data;
        this.loaded = true;
      } catch (error) {
        console.error('Error fetching latest record:', error);
        this.loaded = true;
      }
    },

    async loadAllRecords() {
      try {
        const response = await getAllEEGRecords();
        this.allRecords = response.data;
        this.showAllRecords = true;
      } catch (error) {
        console.error('Error loading all records:', error);
        alert('无法加载历史记录');
      }
    },

    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN');
    },

    onRecordSelect() {
      if (this.selectedRecord) {
        this.selectedRecordDetails = this.allRecords.find(
          record => record.recording_id === this.selectedRecord
        );
      } else {
        this.selectedRecordDetails = null;
      }
    }
  }
};
</script>

<style scoped>
.card {
  background: rgba(0, 0, 0, 0.6);
  border-radius: 10px;
  padding: 15px;
  margin: 10px;
  color: white;
}

.data-status p {
  margin: 5px 0;
}

.more-btn {
  background-color: #00bfff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
  margin-top: 10px;
}

.more-btn:hover {
  background-color: #0077cc;
}

.dropdown-container {
  margin-top: 10px;
}

.record-dropdown {
  width: 100%;
  padding: 8px;
  border: 1px solid #00bfff;
  border-radius: 5px;
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  margin-bottom: 10px;
}

.record-details {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 5px;
  padding: 10px;
  margin-top: 10px;
}

.record-details h4 {
  margin-top: 0;
  color: #00bfff;
}

.record-details p {
  margin: 5px 0;
  font-size: 14px;
}
</style>