// public/script.js
// 全局变量 - 在所有函数中共享
let currentGame = 'infinity';
let codeList, loading, content, tabShining, tabInfinity, tabDeepspace, currentTimeElement, toast;

// 显示加载状态
function showLoading() {
  loading.style.display = 'flex';
  content.style.display = 'none';
}

// 隐藏加载状态
function hideLoading() {
  loading.style.display = 'none';
  content.style.display = 'block';
}

// 显示提示信息
function showToast(message) {
  toast.textContent = message;
  toast.classList.add('show');
  
  setTimeout(() => {
    toast.classList.remove('show');
  }, 2000);
}

// 更新时钟函数
function updateClock() {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + 1;
  const day = now.getDate();
  const hours = now.getHours().toString().padStart(2, '0');
  const minutes = now.getMinutes().toString().padStart(2, '0');
  const seconds = now.getSeconds().toString().padStart(2, '0');
  
  currentTimeElement.textContent = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

// 加载兑换码数据
async function loadCodes(gameType) {
  showLoading();
  
  try {
    const response = await fetch(`/api/codes/${gameType}`);
    const codes = await response.json();
    
    codeList.innerHTML = '';
    
    if (codes.length === 0) {
      codeList.innerHTML = '<p class="no-codes">暂无兑换码</p>';
    } else {
      // 按日期降序排序兑换码
      codes.sort((a, b) => new Date(b.date) - new Date(a.date));
      
      codes.forEach((item, index) => {
        const codeItem = document.createElement('div');
        codeItem.className = 'code-item';
        
        const date = new Date(item.date);
        const formattedDate = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        
        // 检查兑换码是否生效中
        let status = '';
        let statusClass = '';
        
        if (item.end) {
          const now = new Date();
          const endDate = new Date(item.end);
          
          if (now > endDate) {
            status = '已过期';
            statusClass = 'status-expired';
          } else {
            status = '生效中';
            statusClass = 'status-active';
          }
        } else {
          status = '未知';
          statusClass = 'status-unknown';
        }
        
        codeItem.innerHTML = `
          <div class="code-index">${index + 1}</div>
          <div class="code-text">
            <div class="code-status"><strong>📊 状态:</strong> <span class="${statusClass}">${status}</span></div>
            <div class="code-key"><strong>🎮 兑换码:</strong> ${item.code}</div>
            <div class="code-reward"><strong>🎁 奖励:</strong> ${item.reward || '未知'}</div>
            <div class="code-validity"><strong>📅 生效时间:</strong> <span class="validity-period">${item.start || '未知'} 至 ${item.end || '未知'}</span></div>
            <div class="code-source"><strong>🔗 源链接:</strong> <a href="${item.url}" target="_blank">${item.url}</a></div>
            <div class="code-date">⏱️ 发布时间: ${formattedDate}</div>
          </div>
          <button class="copy-btn" data-code="${item.code}">
            <i class="fas fa-copy"></i> 复制
          </button>
        `;
        
        codeList.appendChild(codeItem);
      });
      
      // 添加复制按钮事件
      document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', function() {
          const code = this.getAttribute('data-code');
          navigator.clipboard.writeText(code)
            .then(() => {
              showToast('复制成功!');
            })
            .catch(err => {
              showToast('复制失败，请手动复制');
              console.error('复制失败:', err);
            });
        });
      });
    }
  } catch (error) {
    console.error('加载兑换码失败:', error);
    codeList.innerHTML = '<p class="error">加载失败，请刷新重试</p>';
  }
  
  hideLoading();
}

// 当DOM加载完成后初始化页面
document.addEventListener('DOMContentLoaded', function() {
  // 初始化DOM元素引用
  codeList = document.getElementById('code-list');
  loading = document.getElementById('loading');
  content = document.getElementById('content');
  tabShining = document.getElementById('tab-shining');
  tabInfinity = document.getElementById('tab-infinity');
  tabDeepspace = document.getElementById('tab-deepspace');
  currentTimeElement = document.getElementById('current-time');
  toast = document.getElementById('toast');
  
  // 初始化并每秒更新时钟
  updateClock();
  setInterval(updateClock, 1000);
  
  // 初始加载
  loadCodes(currentGame);
    
  // 标签切换事件
  tabShining.addEventListener('click', function() {
    if (currentGame !== 'shining') {
      tabShining.classList.add('active');
      tabInfinity.classList.remove('active');
      tabDeepspace.classList.remove('active');
      currentGame = 'shining';
      loadCodes(currentGame);
    }
  });
  
  tabInfinity.addEventListener('click', function() {
    if (currentGame !== 'infinity') {
      tabInfinity.classList.add('active');
      tabShining.classList.remove('active');
      tabDeepspace.classList.remove('active');
      currentGame = 'infinity';
      loadCodes(currentGame);
    }
  });
  
  tabDeepspace.addEventListener('click', function() {
    if (currentGame !== 'deepspace') {
      tabDeepspace.classList.add('active');
      tabInfinity.classList.remove('active');
      tabShining.classList.remove('active');
      currentGame = 'deepspace';
      loadCodes(currentGame);
    }
  });
});