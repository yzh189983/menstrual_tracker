// pages/logs/logs.js
const app = getApp();
const api = require('../../utils/api.js');

Page({
  data: {
    // 当前tab
    currentTab: 'period', // period:月经, study:学习, work:工作
    // 数据
    periodRecords: [],
    studyRecords: [],
    workRecords: [],
    // 加载状态
    loading: false,
    // 当前年月
    currentYear: new Date().getFullYear(),
    currentMonth: new Date().getMonth() + 1
  },

  onLoad() {
    this.loadAllRecords();
  },

  onShow() {
    this.loadAllRecords();
  },

  // 加载所有记录
  async loadAllRecords() {
    this.setData({ loading: true });
    
    try {
      await Promise.all([
        this.loadPeriodRecords(),
        this.loadStudyRecords(),
        this.loadWorkRecords()
      ]);
    } catch (err) {
      console.error('加载记录失败:', err);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    }
    
    this.setData({ loading: false });
  },

  // 加载月经记录
  async loadPeriodRecords() {
    try {
      const data = await api.getPeriods(this.data.currentYear, this.data.currentMonth);
      this.setData({
        periodRecords: data.periods || []
      });
    } catch (err) {
      console.error('加载月经记录失败:', err);
    }
  },

  // 加载学习记录
  async loadStudyRecords() {
    try {
      const response = await wx.request({
        url: `${app.globalData.apiBase}/api/study_data`,
        method: 'GET'
      });
      this.setData({
        studyRecords: response.data.records || []
      });
    } catch (err) {
      console.error('加载学习记录失败:', err);
    }
  },

  // 加载工作记录
  async loadWorkRecords() {
    try {
      const response = await wx.request({
        url: `${app.globalData.apiBase}/work`,
        method: 'GET'
      });
      this.setData({
        workRecords: response.data.records || []
      });
    } catch (err) {
      console.error('加载工作记录失败:', err);
    }
  },

  // 切换tab
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ currentTab: tab });
  },

  // 选择年月
  bindDateChange(e) {
    const [year, month] = e.detail.value.split('-');
    this.setData({
      currentYear: parseInt(year),
      currentMonth: parseInt(month)
    });
    this.loadPeriodRecords();
  },

  // 删除月经记录
  deletePeriod(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: '确认',
      content: '确定要删除这条记录吗？',
      success: (res) => {
        if (res.confirm) {
          wx.request({
            url: `${app.globalData.apiBase}/delete/${id}`,
            method: 'POST',
            success: () => {
              wx.showToast({ title: '删除成功' });
              this.loadPeriodRecords();
            }
          });
        }
      }
    });
  },

  // 删除学习记录
  deleteStudy(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: '确认',
      content: '确定要删除这条学习记录吗？',
      success: (res) => {
        if (res.confirm) {
          wx.request({
            url: `${app.globalData.apiBase}/study/delete/${id}`,
            method: 'POST',
            success: () => {
              wx.showToast({ title: '删除成功' });
              this.loadStudyRecords();
            }
          });
        }
      }
    });
  },

  // 删除工作记录
  deleteWork(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: '确认',
      content: '确定要删除这条工作记录吗？',
      success: (res) => {
        if (res.confirm) {
          wx.request({
            url: `${app.globalData.apiBase}/work/delete/${id}`,
            method: 'POST',
            success: () => {
              wx.showToast({ title: '删除成功' });
              this.loadWorkRecords();
            }
          });
        }
      }
    });
  },

  // 刷新
  onPullDownRefresh() {
    this.loadAllRecords().then(() => {
      wx.stopPullDownRefresh();
    });
  }
});
