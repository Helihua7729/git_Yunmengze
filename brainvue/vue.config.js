const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        pathRewrite: {
          '^/api': '/api'
        }
      },
      '/reports': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        pathRewrite: {
          '^/reports': '/reports'
        }
      },
      '/ws/eeg/': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
        pathRewrite: {
          '^/ws/eeg/': '/ws/eeg/'
        }
      }
    }
  },
  configureWebpack: {
    optimization: {
      splitChunks: {
        chunks: 'all'
      }
    }
  },
  chainWebpack: config => {
    // 确保只生成一个index.html文件
    config.plugin('html')
      .tap(args => {
        args[0].filename = 'index.html';
        return args;
      });
  }
})