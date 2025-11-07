import axios from 'axios';

const api = axios.create({
  baseURL: '/api', // 使用相对路径，假设前端和后端在同一域名下
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// 获取最新的EEG记录
export const getLatestEEGRecord = () => {
  return api.get('/latest-eeg-record/');
};

// 获取所有EEG记录
export const getAllEEGRecords = () => {
  return api.get('/all-eeg-records/');
};

export default api;