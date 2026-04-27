// utils/api.js - 日历网站API调用

const app = getApp();

/**
 * 语音对话接口 - 调用日历网站的AI对话功能
 * @param {string} text - 用户语音识别后的文字
 * @returns {Promise}
 */
export async function voiceChat(text) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.apiBase}/api/voice/chat`,
      method: 'POST',
      header: {
        'Content-Type': 'application/json'
      },
      data: {
        message: text,
        // 如果有用户登录状态，可以传递session
        // session: wx.getStorageSync('session')
      },
      success(res) {
        if (res.statusCode === 200) {
          resolve(res.data);
        } else {
          reject(res.data);
        }
      },
      fail(err) {
        reject(err);
      }
    });
  });
}

/**
 * 语音识别接口（使用微信小程序自带能力）
 * @returns {Promise} 返回识别结果
 */
export function recognizeSpeech() {
  return new Promise((resolve, reject) => {
    // 检查版本是否支持插件
    const plugin = requirePlugin("WechatSI");
    
    if (!plugin) {
      reject({ errMsg: '插件未安装' });
      return;
    }

    let manager = plugin.getRecordRecognitionManager();

    manager.onRecognize = function(res) {
      console.log("识别中:", res.result);
    };

    manager.onStop = function(res) {
      const text = res.result;
      if (text == '') {
        reject({ errMsg: '未识别到内容' });
        return;
      }
      resolve(text);
    };

    manager.onError = function(err) {
      reject(err);
    };

    // 开始识别
    manager.start({ lang: "zh_CN", duration: 30000 });
  });
}

/**
 * 文字转语音（TTS）
 * @param {string} text - 要转换的文字
 * @returns {Promise} 返回音频文件路径
 */
export function textToSpeech(text) {
  return new Promise((resolve, reject) => {
    const plugin = requirePlugin("WechatSI");
    
    if (!plugin) {
      reject({ errMsg: '插件未安装' });
      return;
    }

    plugin.textToSpeech({
      lang: "zh_CN",
      content: text,
      success(res) {
        resolve(res.filename);
      },
      fail(err) {
        reject(err);
      }
    });
  });
}

/**
 * 播放音频
 * @param {string} filePath - 音频文件路径
 */
export function playAudio(filePath) {
  const audioContext = wx.createInnerAudioContext();
  audioContext.src = filePath;
  audioContext.play();
  
  audioContext.onEnded(() => {
    audioContext.destroy();
  });
}

/**
 * 添加月经记录
 * @param {Object} data - 记录数据
 */
export async function addPeriod(data) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.apiBase}/add`,
      method: 'POST',
      header: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      data: {
        start_date: data.startDate,
        end_date: data.endDate,
        flow: data.flow || 'medium',
        pain_level: data.painLevel || 0,
        symptoms: data.symptoms || '',
        notes: data.notes || ''
      },
      success(res) {
        resolve(res.data);
      },
      fail(err) {
        reject(err);
      }
    });
  });
}

/**
 * 查询月经记录
 * @param {number} year - 年份
 * @param {number} month - 月份
 */
export async function getPeriods(year, month) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.apiBase}/api/data`,
      method: 'GET',
      data: {
        year,
        month
      },
      success(res) {
        if (res.statusCode === 200) {
          resolve(res.data);
        } else {
          reject(res.data);
        }
      },
      fail(err) {
        reject(err);
      }
    });
  });
}

/**
 * 添加学习记录
 * @param {Object} data - 学习记录数据
 */
export async function addStudyRecord(data) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.apiBase}/study/add`,
      method: 'POST',
      header: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      data: {
        date: data.date,
        subject: data.subject,
        duration: data.duration,
        plan: data.plan || '',
        notes: data.notes || ''
      },
      success(res) {
        resolve(res.data);
      },
      fail(err) {
        reject(err);
      }
    });
  });
}

/**
 * 添加工作记录
 * @param {Object} data - 工作记录数据
 */
export async function addWorkRecord(data) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.apiBase}/work/add`,
      method: 'POST',
      header: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      data: {
        date: data.date,
        task: data.task,
        task_duration: data.taskDuration || 0,
        work_start: data.workStart || '',
        work_end: data.workEnd || '',
        overtime: data.overtime || 0
      },
      success(res) {
        resolve(res.data);
      },
      fail(err) {
        reject(err);
      }
    });
  });
}

/**
 * 获取聊天记录
 */
export async function getChatHistory() {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.apiBase}/chat`,
      method: 'GET',
      success(res) {
        resolve(res.data);
      },
      fail(err) {
        reject(err);
      }
    });
  });
}

module.exports = {
  voiceChat,
  recognizeSpeech,
  textToSpeech,
  playAudio,
  addPeriod,
  getPeriods,
  addStudyRecord,
  addWorkRecord,
  getChatHistory
};
