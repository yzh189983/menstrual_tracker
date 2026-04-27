// app.js
App({
  globalData: {
    userInfo: null,
    // 日历网站API地址 - 部署时修改为实际地址
    apiBase: 'http://127.0.0.1:5000',
    // 蓝牙设备信息
    deviceId: null,
    serviceId: null,
    characteristicId: null,
    // 语音识别结果
    recognizedText: '',
    // 语音回复
    replyText: ''
  },

  onLaunch() {
    // 检查系统权限
    this.checkSystemInfo();
  },

  checkSystemInfo() {
    const systemInfo = wx.getSystemInfoSync();
    // 检查蓝牙是否可用
    if (!wx.openBluetoothAdapter) {
      wx.showModal({
        title: '提示',
        content: '当前微信版本过低，无法使用蓝牙功能'
      });
    }
  },

  // 提示消息
  showToast(title, icon = 'none') {
    wx.showToast({
      title,
      icon,
      duration: 2000
    });
  },

  // 显示加载中
  showLoading(title = '加载中') {
    wx.showLoading({
      title,
      mask: true
    });
  },

  // 隐藏加载中
  hideLoading() {
    wx.hideLoading();
  }
});
