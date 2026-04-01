// pages/index/index.js
const app = getApp();
const api = require('../../utils/api.js');

Page({
  data: {
    // 语音状态
    isRecording: false,
    isSpeaking: false,
    // 对话内容
    messages: [],
    userInput: '',
    // 连接状态
    isBluetoothConnected: false,
    // 动画
    waveAnimating: false
  },

  onLoad() {
    // 检查蓝牙连接状态
    this.checkBluetoothStatus();
  },

  onShow() {
    // 每次显示页面时检查蓝牙状态
    this.checkBluetoothStatus();
  },

  // 检查蓝牙连接状态
  checkBluetoothStatus() {
    const deviceId = wx.getStorageSync('bluetooth_deviceId');
    this.setData({
      isBluetoothConnected: !!deviceId
    });
  },

  // 开始语音输入
  startRecording() {
    if (!this.data.isBluetoothConnected) {
      wx.showModal({
        title: '提示',
        content: '请先连接蓝牙设备',
        confirmText: '去连接',
        success: (res) => {
          if (res.confirm) {
            wx.switchTab({
              url: '/pages/bluetooth/bluetooth'
            });
          }
        }
      });
      return;
    }

    this.setData({
      isRecording: true,
      waveAnimating: true
    });

    // 调用语音识别
    this.doSpeechRecognition();
  },

  // 停止语音输入
  stopRecording() {
    this.setData({
      isRecording: false,
      waveAnimating: false
    });
  },

  // 执行语音识别
  doSpeechRecognition() {
    const plugin = requirePlugin("WechatSI");
    let manager = plugin.getRecordRecognitionManager();

    manager.onRecognize = (res) => {
      console.log("识别中:", res.result);
    };

    manager.onStop = (res) => {
      const text = res.result;
      if (text && text.trim()) {
        this.handleVoiceInput(text);
      } else {
        wx.showToast({
          title: '未识别到内容',
          icon: 'none'
        });
      }
      this.setData({
        isRecording: false,
        waveAnimating: false
      });
    };

    manager.onError = (err) => {
      console.error("语音识别错误:", err);
      wx.showToast({
        title: '识别失败，请重试',
        icon: 'none'
      });
      this.setData({
        isRecording: false,
        waveAnimating: false
      });
    };

    // 开始识别
    manager.start({
      lang: "zh_CN",
      duration: 30000
    });
  },

  // 处理语音输入
  async handleVoiceInput(text) {
    // 添加用户消息
    const userMsg = {
      type: 'user',
      content: text,
      time: new Date().toLocaleTimeString()
    };

    this.setData({
      messages: [...this.data.messages, userMsg],
      isSpeaking: true
    });

    try {
      // 调用日历网站的AI对话接口
      const response = await api.voiceChat(text);
      
      const aiMsg = {
        type: 'ai',
        content: response.reply || response.message || '收到你的消息了',
        time: new Date().toLocaleTimeString()
      };

      this.setData({
        messages: [...this.data.messages, aiMsg],
        isSpeaking: false
      });

      // 播放语音回复
      if (response.reply) {
        this.playVoiceReply(response.reply);
      }

      // 保存到本地存储
      this.saveMessage(userMsg);
      this.saveMessage(aiMsg);

    } catch (err) {
      console.error("API调用失败:", err);
      
      const errorMsg = {
        type: 'ai',
        content: '抱歉，连接日历网站失败了。请检查网络或确认日历网站已开启。',
        time: new Date().toLocaleTimeString()
      };

      this.setData({
        messages: [...this.data.messages, errorMsg],
        isSpeaking: false
      });
    }
  },

  // 播放语音回复
  async playVoiceReply(text) {
    const plugin = requirePlugin("WechatSI");
    
    plugin.textToSpeech({
      lang: "zh_CN",
      content: text,
      success: (res) => {
        const audioContext = wx.createInnerAudioContext();
        audioContext.src = res.filename;
        audioContext.play();
      },
      fail: (err) => {
        console.error("语音合成失败:", err);
      }
    });
  },

  // 手动输入文字
  onInput(e) {
    this.setData({
      userInput: e.detail.value
    });
  },

  // 发送文字消息
  async sendMessage() {
    const text = this.data.userInput.trim();
    if (!text) return;

    this.setData({
      userInput: ''
    });

    await this.handleVoiceInput(text);
  },

  // 保存消息到本地
  saveMessage(msg) {
    let messages = wx.getStorageSync('chat_messages') || [];
    messages.push(msg);
    // 只保留最近100条
    if (messages.length > 100) {
      messages = messages.slice(-100);
    }
    wx.setStorageSync('chat_messages', messages);
  },

  // 清除对话记录
  clearMessages() {
    wx.showModal({
      title: '确认',
      content: '确定要清除对话记录吗？',
      success: (res) => {
        if (res.confirm) {
          this.setData({
            messages: []
          });
          wx.removeStorageSync('chat_messages');
        }
      }
    });
  },

  // 快捷指令
  quickCommand(e) {
    const command = e.currentTarget.dataset.command;
    this.handleVoiceInput(command);
  }
});
