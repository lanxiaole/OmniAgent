<template>
  <div class="settings-card">
    <div class="card-header">
      <h2 class="card-title">关于</h2>
    </div>
    <div class="about-body">
      <div class="about-item">
        <span class="about-label">应用名称</span>
        <span class="about-value">OmniAgent</span>
      </div>
      <div class="about-item">
        <span class="about-label">版本</span>
        <span class="about-value">0.1.0</span>
      </div>
      <div class="about-item">
        <span class="about-label">框架</span>
        <span class="about-value">LangChain + FastAPI + Vue 3</span>
      </div>
      <div class="about-item">
        <span class="about-label">描述</span>
        <span class="about-value about-desc">个人智能助手，支持对话、知识库、记忆、联网搜索等功能</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 0;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.about-body {
  padding: 16px 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.about-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.about-label {
  font-size: 13px;
  color: var(--text-tertiary);
  min-width: 80px;
  flex-shrink: 0;
  padding-top: 2px;
}

.about-value {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
}

.about-desc {
  line-height: 1.6;
  color: var(--text-secondary);
  font-weight: 400;
}
</style>