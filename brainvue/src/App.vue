<template>
  <div id="app">
    <Home />
  </div>
</template>

<script>
import Home from './views/Home.vue'

export default {
  name: 'App',
  components: {
    Home
  }
}
</script>

<style>
/* 全局样式 */
body { 
  margin: 0;
}

#app {
  font-family: 'Microsoft YaHei', sans-serif;
  margin: 0;
  padding: 20px;
  background: linear-gradient(to right, rgba(0, 0, 70, 0.3), rgba(28, 181, 224, 0.3)), url('./assets/images/背景鲸鱼.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  background-attachment: fixed;
  min-height: 100vh;
  color: #fff;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.logo-container {
  width: 120px;
  height: 120px;
  margin: 50px auto 0px auto;
  display: block;
}

.logo-container img {
  width: 120px;
  height: auto;
  border-radius: 50%;
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
}

.title {
  color: #ffd000;
  font-size: 1.8rem;
  margin: 10px 0;
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.7);
}



/* .custom-input {
  border: none;
  background-color: transparent;
  outline: none;
} */


.el-input__inner{
  margin-top: 5px;
  border: 2px solid #00ffff ;
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.7) !important;
  border-radius: 8px !important;
  background-color: rgba(51, 128, 158, 0.9) ;
  color: #ffffff !important;
  font-size: 14px;
}
.el-input__wrapper{
  background-color: transparent ;
  border-color: transparent ;
  box-shadow:none;
}
.el-input__wrapper:hover{
  box-shadow:none;
}

.subtitle {
  color: #99ccff;
  font-size: 0.9rem;
  margin-top: 5px;
}

.status-bar {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 20px;
  font-size: 0.9rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 20px;
}

.el-icon-circle-check {
  color: #00ff00;
  animation: pulse 2s infinite;
}

.el-icon-circle-cross {
  color: #ff0000;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.button-group {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-bottom: 20px;
}


.el-button {
  border: 1px solid #00ffff;
  border-radius: 8px;
  padding: 10px 20px;
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
  transition: all 0.3s ease;
  background: transparent;
  color: #00ffff;
  font-size: 20px;
}

#scann_button{
  margin-top: 8px;
  font-size: 16px;
}

.el-button:hover {
  transform: scale(1.05);
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
}

.el-button[type="primary"] {
  background: transparent;
  color: #00ffff;
}

.el-button[type="success"] {
  background: transparent;
  color: #00ff00;
}

.el-button[type="warning"] {
  background: transparent;
  color: #ffcc00;
}

.el-button[type="info"] {
  background: transparent;
  color: #00ccff;
}

.main-content {  
  margin-left: 12.5%;
  width: 75%;
  display: flex;
  gap: 20px;
}

/* 固定标签页内容区域 */
.tab-content-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 600px;
  max-height: 800px;
  height: 700px;
}

.tab-pane-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: rgba(0, 20, 40, 0.6);
  border-radius: 8px;
  border: 1px solid #00aaff;
  box-shadow: 0 0 10px rgba(51, 142, 253, 0.301);
}

.sidebar {
  width: 350px;
  background: rgba(47, 99, 242, 0.297);
  border: 1px solid #00ffff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
}

.card {
  margin-bottom: 20px;
  border-bottom: 1px solid #00ffff;
  padding-bottom: 16px;
}

.card h3 {
  margin-top: 0;
  font-size: 1rem;
  color: #00ffff;
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-group {
  margin: 10px 0;
}

.status-info {
  margin-top: 10px;
  font-size: 0.9rem;
  color: #99ccff;
}

.data-status {
  padding: 10px;
  background: rgba(104, 104, 111, 0.506);
  border-radius: 4px;
  margin-top: 10px;
  color: #00ffff;
}

.history-file {
  margin-top: 10px;
  font-size: 0.9rem;
  color: #99ccff;
}

/* 主内容 */
.main-panel {
  flex: 1;
  background: rgba(27, 27, 82, 0.5);
  border: 1px solid #00ffff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 0 20px rgba(63, 109, 158, 0.2);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.main-panel .el-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.main-panel .el-tabs__content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.main-panel .el-tab-pane {
  flex: 1;
  overflow-y: auto;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.data-flow {
  text-align: center;
  padding: 40px;
  color: #99ccff;
  font-size: 1rem;
  flex: 1;
  overflow-y: auto;
}

.placeholder {
  height: 100%;
  overflow-y: auto;
  text-align: left;
  white-space: pre-wrap;
  color: #00ffff;
  font-family: monospace;
  line-height: 1.5;
  background: rgba(28, 48, 74, 0.345);
  padding: 10px;
  border-radius: 8px;
  flex: 1;
}

/* 主内容 */

.clear-log-btn {
  text-align: right;
  margin-top: 10px;
}

.footer {
  text-align: center;
  margin-top: 30px;
  color: #99ccff;
  font-size: 0.8rem;
  text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
}

/* 标签页样式 */
.el-tabs__item {
  color: #99ccff !important;
  font-weight: bold;
}

.el-tabs__item.is-active {
  color: #00ffff !important;
  border-bottom: 2px solid #00ffff;
}

.el-tabs__nav {
  border-bottom: none;
}
</style>