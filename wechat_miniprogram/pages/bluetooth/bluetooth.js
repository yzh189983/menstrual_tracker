// pages/bluetooth/bluetooth.js
const app = getApp();

Page({
  data: {
    // 蓝牙状态
    isBluetoothOpen: false,
    isSearching: false,
    isConnecting: false,
    // 设备列表
    devices: [],
    connectedDevice: null,
    // 搜索状态
    searchStatus: 'idle', // idle, searching, found
    // 服务和特征值
    services: [],
    characteristics: [],
    // 日志
    logs: []
  },

  onLoad() {
    this.initBluetooth();
  },

  onUnload() {
    // 页面卸载时停止搜索
    this.stopSearch();
    wx.stopBluetoothDevicesDiscovery();
  },

  // 初始化蓝牙
  initBluetooth() {
    wx.openBluetoothAdapter({
      success: () => {
        this.setData({
          isBluetoothOpen: true,
          logs: [...this.data.logs, { time: this.getTime(), msg: '蓝牙适配器已打开' }]
        });
        this.startSearch();
      },
      fail: (err) => {
        console.error('打开蓝牙失败:', err);
        wx.showModal({
          title: '提示',
          content: '请打开手机蓝牙',
          showCancel: false
        });
        this.setData({
          isBluetoothOpen: false,
          logs: [...this.data.logs, { time: this.getTime(), msg: '打开蓝牙失败: ' + err.errMsg }]
        });
      }
    });
  },

  // 开始搜索设备
  startSearch() {
    if (this.data.isSearching) return;

    this.setData({
      isSearching: true,
      searchStatus: 'searching',
      devices: [],
      logs: [...this.data.logs, { time: this.getTime(), msg: '开始搜索周边设备...' }]
    });

    wx.startBluetoothDevicesDiscovery({
      allowDuplicatesKey: false,
      success: () => {
        this.onDeviceFound();
      },
      fail: (err) => {
        console.error('搜索失败:', err);
        this.setData({
          logs: [...this.data.logs, { time: this.getTime(), msg: '搜索失败: ' + err.errMsg }]
        });
      }
    });

    // 10秒后自动停止
    setTimeout(() => {
      if (this.data.isSearching) {
        this.stopSearch();
      }
    }, 10000);
  },

  // 停止搜索
  stopSearch() {
    wx.stopBluetoothDevicesDiscovery();
    this.setData({
      isSearching: false,
      searchStatus: this.data.devices.length > 0 ? 'found' : 'idle'
    });
  },

  // 设备被发现回调
  onDeviceFound() {
    wx.onBluetoothDeviceFound((res) => {
      res.devices.forEach(device => {
        // 过滤掉没有设备名称的
        if (!device.name && !device.localName) {
          return;
        }

        // 过滤掉重复的
        const index = this.data.devices.findIndex(d => d.deviceId === device.deviceId);
        if (index === -1) {
          this.setData({
            devices: [...this.data.devices, device]
          });
        } else {
          // 更新信号强度
          const devices = this.data.devices;
          devices[index] = device;
          this.setData({ devices });
        }
      });
    });
  },

  // 连接设备
  connect(e) {
    const device = e.currentTarget.dataset.device;
    const deviceId = device.deviceId;

    this.setData({
      isConnecting: true,
      logs: [...this.data.logs, { time: this.getTime(), msg: '正在连接: ' + (device.name || device.localName) }]
    });

    wx.createBLEConnection({
      deviceId,
      success: () => {
        this.setData({
          connectedDevice: device,
          isConnecting: false,
          logs: [...this.data.logs, { time: this.getTime(), msg: '连接成功: ' + (device.name || device.localName) }]
        });

        // 保存设备ID到本地
        wx.setStorageSync('bluetooth_deviceId', deviceId);
        wx.setStorageSync('bluetooth_deviceName', device.name || device.localName);

        // 停止搜索
        this.stopSearch();

        // 获取服务
        this.getServices(deviceId);
      },
      fail: (err) => {
        console.error('连接失败:', err);
        this.setData({
          isConnecting: false,
          logs: [...this.data.logs, { time: this.getTime(), msg: '连接失败: ' + err.errMsg }]
        });
        wx.showToast({
          title: '连接失败',
          icon: 'none'
        });
      }
    });
  },

  // 获取服务
  getServices(deviceId) {
    wx.getBLEDeviceServices({
      deviceId,
      success: (res) => {
        const services = res.services.filter(s => s.isPrimary);
        this.setData({
          services,
          logs: [...this.data.logs, { time: this.getTime(), msg: '获取到 ' + services.length + ' 个服务' }]
        });

        // 遍历服务获取特征值
        if (services.length > 0) {
          this.getCharacteristics(deviceId, services[0].uuid);
        }
      }
    });
  },

  // 获取特征值
  getCharacteristics(deviceId, serviceId) {
    wx.getBLEDeviceCharacteristics({
      deviceId,
      serviceId,
      success: (res) => {
        const characteristics = res.characteristics;
        this.setData({
          characteristics,
          logs: [...this.data.logs, { time: this.getTime(), msg: '获取到 ' + characteristics.length + ' 个特征值' }]
        });

        // 开启通知
        characteristics.forEach(char => {
          if (char.properties.notify || char.properties.indicate) {
            wx.notifyBLECharacteristicValueChange({
              deviceId,
              serviceId,
              characteristicId: char.uuid,
              state: true
            });
          }
        });

        // 保存服务ID和特征值ID
        wx.setStorageSync('bluetooth_serviceId', serviceId);
        wx.setStorageSync('bluetooth_characteristicId', characteristics[0]?.uuid);
      }
    });
  },

  // 断开连接
  disconnect() {
    const deviceId = wx.getStorageSync('bluetooth_deviceId');
    if (!deviceId) return;

    wx.closeBLEConnection({
      deviceId,
      success: () => {
        this.setData({
          connectedDevice: null,
          devices: [],
          services: [],
          characteristics: [],
          logs: [...this.data.logs, { time: this.getTime(), msg: '已断开连接' }]
        });

        wx.removeStorageSync('bluetooth_deviceId');
        wx.removeStorageSync('bluetooth_deviceName');
        wx.removeStorageSync('bluetooth_serviceId');
        wx.removeStorageSync('bluetooth_characteristicId');

        wx.showToast({
          title: '已断开连接',
          icon: 'success'
        });
      }
    });
  },

  // 重新搜索
  restartSearch() {
    this.disconnect();
    this.setData({
      devices: [],
      searchStatus: 'idle'
    });
    this.initBluetooth();
  },

  // 获取当前时间
  getTime() {
    const now = new Date();
    return now.toLocaleTimeString();
  },

  // 刷新设备列表
  refreshDevices() {
    this.setData({
      devices: []
    });
    this.startSearch();
  }
});
