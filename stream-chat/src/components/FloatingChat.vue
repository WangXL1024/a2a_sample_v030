<template>
  <div class="floating-chat-container">
    <button class="chat-toggle-btn" @click="toggleChat">
      <span v-if="!isOpen">AI助手</span>
      <span v-else>×</span>
    </button>

    <div class="chat-window" :class="{ 'maximized': isMaximized }" v-if="isOpen">
      <div class="chat-header" @mousedown="startDrag">
        <span>AI助手</span>
        <div class="window-controls">
          <button @click="toggleMaximize">
            {{ isMaximized ? '还原' : '最大化' }}
          </button>
          <button @click="closeChat">×</button>
        </div>
      </div>

      <div class="chat-content" ref="chatContent">
        <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
          <div v-if="msg.role === 'assistant'" class="message-icon">
            <!-- <img src="https://via.placeholder.com/30" alt="机器人图标"> -->
          </div>
          <div class="message-content" v-html="parseMarkdown(msg.content)"></div>
        </div>
        <div v-if="isLoading" class="message assistant">
          <div class="message-icon">
            <!-- <img src="https://via.placeholder.com/30" alt="机器人图标"> -->
          </div>
          <div class="message-content typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>

      <div class="chat-input">
        <textarea
          v-model="userInput"
          placeholder="输入消息..."
          @keydown.enter.exact.prevent="sendMessage"
          :disabled="isLoading"
        ></textarea>
        <button @click="sendMessage" :disabled="!userInput || isLoading">发送</button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import * as marked from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

// 配置marked.js
(marked.setOptions as any)({
  highlight: function(code: string, lang: string | undefined) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
  gfm: true
})

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

// 状态管理
const isOpen = ref(false)
const isMaximized = ref(false)
const isDragging = ref(false)
const startPos = ref({ x: 0, y: 0 })
const currentPos = ref({ x: 0, y: 0 })
const userInput = ref('')
const messages = ref<ChatMessage[]>([])
const isLoading = ref(false)
const chatContent = ref<HTMLElement | null>(null)
const abortController = ref<AbortController | null>(null)
const session_id  = ref('')

// 定义Markdown解析函数
const parseMarkdown = (content: string) => {
  if (!content) return ''
  return marked.parse(content)
}

// 生成唯一sessionID
const generateUUID = () => {
  session_id.value = crypto.randomUUID()
  localStorage.setItem('current_session_id', session_id.value)
  return session_id.value
}

// 初始化时加载历史消息
onMounted(() => {
  // loadHistory()
})

// 切换聊天窗口
const toggleChat = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    scrollToBottom()
  }
}

// 关闭聊天窗口
const closeChat = () => {
  localStorage.removeItem("current_session_id");
  messages.value=[]
  // localStorage.removeItem("chatHistory");
  isOpen.value = false
}

// 最大化/还原窗口
const toggleMaximize = () => {
  isMaximized.value = !isMaximized.value
  scrollToBottom()
}

// 开始拖动
const startDrag = (e: MouseEvent) => {
  if (isMaximized.value) return
  isDragging.value = true
  startPos.value = {
    x: e.clientX - currentPos.value.x,
    y: e.clientY - currentPos.value.y
  }
  document.addEventListener('mousemove', handleDrag)
  document.addEventListener('mouseup', stopDrag)
}

// 处理拖动
const handleDrag = (e: MouseEvent) => {
  if (!isDragging.value) return
  currentPos.value = {
    x: e.clientX - startPos.value.x,
    y: e.clientY - startPos.value.y
  }
}

// 停止拖动
const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', stopDrag)
}

const sendMessage = async () => {
  const current_session_id = localStorage.getItem("current_session_id") == null;
  if (current_session_id) {
    generateUUID()
  } 

  if (!userInput.value.trim() || isLoading.value) return;

  const userMessage = userInput.value;
  userInput.value = '';

  // 添加用户消息到消息列表
  messages.value.push({ role: 'user', content: userMessage });
  scrollToBottom(); // 滚动到最新消息

  // 为AI响应预留位置
  const aiMessageIndex = messages.value.length;
  messages.value.push({ role: 'assistant', content: '' });

  isLoading.value = true;

  try {
    abortController.value = new AbortController();
    const response = await fetch('http://localhost:9001/stream-query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_input: userMessage, session_id: session_id.value}),
      signal: abortController.value.signal,
    });

    if (!response.ok) throw new Error(`HTTP错误: ${response.status}`);

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';

    // 处理SSE流式响应
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      // 解码当前块
      const chunk = decoder.decode(value, { stream: true });
      fullResponse += chunk;

      // 按行分割SSE消息
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        const trimmedLine = line.trim();
        if (!trimmedLine) continue;
        
        // 提取data字段内容
        if (trimmedLine.startsWith('data:')) {
          const dataStr = trimmedLine.slice(5).trim();
          if (dataStr) {
            try {
              // 解析JSON数据
              const data = JSON.parse(dataStr);
              // 累加状态消息文本
              if (data.type === 'status' && typeof data.text === 'string') {
                messages.value[aiMessageIndex].content += data.text;
                scrollToBottom();
              }
            } catch (e) {
              console.error('解析SSE数据失败:', e);
            }
          }
        }
      }
    }

    console.log('完整响应:', fullResponse);

  } catch (error: unknown) {
    // 统一错误处理
    const errorMsg = (error instanceof Error ? error.message : '未知错误') + '';
    console.error('请求处理失败:', errorMsg);
    messages.value[aiMessageIndex].content = '错误: ' + errorMsg;
  } finally {
    isLoading.value = false;
    abortController.value = null;
    saveHistory();
  }
};

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatContent.value) {
      chatContent.value.scrollTop = chatContent.value.scrollHeight
    }
  })
}

// 加载历史记录
const loadHistory = () => {
  const history = localStorage.getItem('chatHistory')
  if (history) {
    messages.value = JSON.parse(history)
  }
}

// 保存历史记录
const saveHistory = () => {
  localStorage.setItem('chatHistory', JSON.stringify(messages.value))
}

// 组件卸载时取消请求
onUnmounted(() => {
  if (abortController.value) {
    abortController.value.abort()
  }
})
</script>

<style scoped>
/* 样式部分保持不变 */
.floating-chat-container {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 1000;
}

.chat-toggle-btn {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: #4CAF50;
  color: white;
  border: none;
  font-size: 16px;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.chat-toggle-btn:hover {
  background-color: #45a049;
  transform: scale(1.1);
}

.chat-window {
  position: absolute;
  right: 0;
  bottom: 70px;
  width: 350px;
  height: 500px;
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.3s;
}

.chat-window.maximized {
  width: 80vw;
  height: 80vh;
  right: 10vw;
  bottom: 10vh;
}

.chat-header {
  padding: 12px 15px;
  background-color: #4CAF50;
  color: white;
  font-weight: bold;
  cursor: move;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.window-controls button {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  margin-left: 10px;
  font-size: 14px;
}

.window-controls button:hover {
  opacity: 0.8;
}

.chat-content {
  flex: 1;
  padding: 15px;
  overflow-y: auto;
  background-color: #f5f5f5;
  display: flex;
  flex-direction: column;
}

.message {
  margin-bottom: 15px;
  display: flex;
  align-items: flex-start;
}

.message-icon {
  margin-right: 10px;
}

.message-icon img {
  width: 30px;
  height: 30px;
  border-radius: 50%;
}

.message-content {
  padding: 8px 12px;
  border-radius: 5px;
  line-height: 1.5;
  max-width: 80%;
  word-wrap: break-word;
}

.message.user .message-content {
  background-color: #e3f2fd;
  margin-left: auto;
}

.message.assistant .message-content {
  background-color: #f1f1f1;
}

.typing-indicator span {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #666;
  margin-right: 3px;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-5px); }
}

.chat-input {
  padding: 10px;
  border-top: 1px solid #ddd;
  background-color: white;
  display: flex;
}

.chat-input textarea {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: none;
  height: 50px;
  margin-right: 10px;
}

.chat-input button {
  padding: 0 15px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.chat-input button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

/* Markdown渲染样式 */
.message-content h1, .message-content h2, .message-content h3 {
  margin-top: 1em;
  margin-bottom: 0.5em;
  font-weight: bold;
}

.message-content ul, .message-content ol {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.message-content code {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(175, 184, 193, 0.2);
  border-radius: 6px;
}

.message-content pre {
  padding: 1em;
  margin: 0.5em 0;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 6px;
}

.message-content blockquote {
  margin: 0.5em 0;
  padding: 0 1em;
  color: #57606a;
  border-left: 0.25em solid #d0d7de;
}

.message-content a {
  color: #0969da;
  text-decoration: none;
}

.message-content a:hover {
  text-decoration: underline;
}
</style>