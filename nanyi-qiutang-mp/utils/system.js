/**
 * 设备与导航栏度量
 */

/**
 * 获取自定义导航栏相关尺寸
 * @returns {{statusBarHeight:number, navBarHeight:number, navTotalHeight:number, capsuleGap:number, capsuleWidth:number, windowWidth:number, windowHeight:number, safeBottom:number, rpxRatio:number}}
 */
function getNavMetrics() {
  let statusBarHeight = 20;
  let windowWidth = 375;
  let windowHeight = 667;
  let screenHeight = 667;
  let safeBottom = 0;
  let navBarHeight = 44;
  let capsuleGap = 10;
  let capsuleWidth = 95;

  try {
    const info = typeof wx.getWindowInfo === 'function' ? wx.getWindowInfo() : wx.getSystemInfoSync();
    statusBarHeight = info.statusBarHeight || statusBarHeight;
    windowWidth = info.windowWidth || windowWidth;
    windowHeight = info.windowHeight || windowHeight;
    screenHeight = info.screenHeight || windowHeight;
    if (info.safeArea && typeof info.safeArea.bottom === 'number') {
      safeBottom = Math.max(0, screenHeight - info.safeArea.bottom);
    }
    if (typeof info.safeAreaInsets === 'object' && info.safeAreaInsets && info.safeAreaInsets.bottom) {
      safeBottom = Math.max(safeBottom, info.safeAreaInsets.bottom);
    }
  } catch (e) {
    // 使用默认值
  }

  try {
    const rect = wx.getMenuButtonBoundingClientRect();
    if (rect && rect.height > 0) {
      // 胶囊上下间距对称，反推导航栏内容高度
      navBarHeight = (rect.top - statusBarHeight) * 2 + rect.height;
      capsuleGap = Math.max(0, windowWidth - rect.right);
      capsuleWidth = Math.max(0, windowWidth - rect.left + capsuleGap);
    }
  } catch (e) {
    // 部分基础库不支持，保持默认
  }

  if (!navBarHeight || navBarHeight < 32 || navBarHeight > 80) {
    navBarHeight = 44;
  }

  return {
    statusBarHeight,
    navBarHeight,
    navTotalHeight: statusBarHeight + navBarHeight,
    capsuleGap,
    capsuleWidth,
    windowWidth,
    windowHeight,
    safeBottom,
    // 1rpx 对应的 px 值
    rpxRatio: windowWidth / 750
  };
}

module.exports = { getNavMetrics };
