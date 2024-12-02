# AI ChatBot

基於 Streamlit 和 Ollama 的本地 AI 聊天機器人應用。

## 功能特點

- 多模型支援（支援所有已安裝的 Ollama 模型）
- 即時串流回應
- 三種性能模式：
  - 平衡模式（預設）：適合一般對話
  - 速度優先：更快的回應速度
  - 質量優先：更高品質的回應
- 可調整參數：
  - 回應創造性（溫度）
  - 最大回應長度
  - 執行緒數量
- 聊天記錄管理：
  - 儲存對話記錄
  - 清除對話記錄
- 對話上下文記憶

## 部署說明

### 本地運行
1. 確保 Ollama 服務在本機運行（默認端口 11434）
2. 運行 `streamlit run chat_app.py`

### 使用 ngrok 連接本機 Ollama

1. 安裝 ngrok
   - 從 [ngrok 官網](https://ngrok.com/) 下載並安裝
   - 註冊一個免費帳號並獲取 authtoken

2. 設置 ngrok
   ```bash
   # Windows 用戶：
   # 1. 按 Win + R
   # 2. 輸入 cmd 並按確定
   # 3. 在命令提示字元中輸入：
   ngrok config add-authtoken 您的authtoken
   
   # Mac/Linux 用戶：
   # 1. 打開終端機
   # 2. 輸入：
   ngrok config add-authtoken 您的authtoken
   
   # 確認設置是否成功：
   ngrok config check
   ```

3. 啟動 ngrok 轉發
   ```bash
   # 將本機的 11434 端口（Ollama 服務端口）轉發出去
   ngrok http 11434
   ```

4. 獲取 URL
   - 執行後，ngrok 會顯示一個類似這樣的 URL：
   - `https://abc123def456.ngrok.io`
   - 這就是您的 OLLAMA_API_BASE_URL

5. 在 Streamlit Cloud 設置
   在 Secrets 中添加：
   ```toml
   OLLAMA_API_BASE_URL = "https://abc123def456.ngrok.io"
   ```

注意事項：
- ngrok 免費版的 URL 每次重啟都會改變
- 需要保持 ngrok 和本機 Ollama 服務持續運行
- 建議升級到 ngrok 付費版獲得固定 URL

### Streamlit Cloud 部署設置

1. 登入 [Streamlit Cloud](https://share.streamlit.io/)
2. 進入您的應用程式設置：
   - 點擊右上角的選單
   - 選擇 "Settings"
   - 切換到 "Secrets" 分頁

3. 添加環境變數：
   在 Secrets 區域添加以下配置（TOML 格式）：
   ```toml
   # 使用 ngrok 方案
   OLLAMA_API_BASE_URL = "https://your-ngrok-url.ngrok.io"

   # 或使用 SSH 通道方案
   OLLAMA_HOST = "your-ip-or-domain"
   OLLAMA_PORT = "11434"
   SSH_KEY = """
   -----BEGIN OPENSSH PRIVATE KEY-----
   您的 SSH 私鑰內容...
   -----END OPENSSH PRIVATE KEY-----
   """
   ```

4. 環境變數說明：
   - 使用 ngrok：
     - OLLAMA_API_BASE_URL：ngrok 生成的 URL
   
   - 使用 SSH 通道：
     - OLLAMA_HOST：您的本機 IP 或域名
     - OLLAMA_PORT：Ollama 服務端口
     - SSH_KEY：用於 SSH 連接的私鑰

5. 部署後檢查：
   - 確認環境變數已正確設置
   - 檢查應用日誌中的連接信息
   - 測試模型列表是否正確載入

注意事項：
- 環境變數值要用引號包裹
- SSH 私鑰需要完整複製，包含開頭和結尾標記
- 確保本機的 Ollama 服務持續運行
- 如使用 ngrok，請確保 URL 是最新的

## API 測試指南

### 本機 API 測試

1. **測試 Ollama 服務是否運行**：
   ```bash
   # 檢查服務狀態
   curl http://localhost:11434/api/tags
   ```

2. **測試模型回應**：
   ```bash
   # 發送簡單的測試請求
   curl -X POST http://localhost:11434/api/generate \
        -H 'Content-Type: application/json' \
        -d '{
          "model": "taide-8b",
          "prompt": "你好",
          "stream": false
        }'
   ```

### ngrok API 測試

1. **測試 ngrok 連接**：
   ```bash
   # 使用完整的請求標頭
   curl -H "ngrok-skip-browser-warning: true" \
        -H "Content-Type: application/json" \
        -H "User-Agent: Mozilla/5.0" \
        https://your-ngrok-url/api/tags
   ```

2. **測試 ngrok 模型回應**：
   ```bash
   # 發送帶有 ngrok 標頭的測試請求
   curl -X POST https://your-ngrok-url/api/generate \
        -H "ngrok-skip-browser-warning: true" \
        -H "Content-Type: application/json" \
        -H "User-Agent: Mozilla/5.0" \
        -d '{
          "model": "taide-8b",
          "prompt": "你好",
          "stream": false
        }'
   ```

### 常見錯誤與解決方案

1. **連接被拒絕**：
   - 確認 Ollama 服務是否運行
   - 檢查端口 11434 是否被占用
   ```bash
   # 檢查端口使用情況
   netstat -tuln | grep 11434
   ```

2. **403 Forbidden**：
   - 確認 ngrok 啟動命令正確
   ```bash
   ngrok http 11434 --host-header=rewrite
   ```

3. **超時錯誤**：
   - 增加超時時間
   ```bash
   curl --max-time 30 [其他參數...]
   ```

4. **無法解析主機名**：
   - 確認 ngrok URL 是否正確
   - 檢查網絡連接
   ```bash
   ping your-ngrok-url
   ```

### 測試檢查清單

- [ ] 本機 Ollama 服務可以訪問
- [ ] 本機 API 可以正常回應
- [ ] ngrok 隧道已建立
- [ ] ngrok API 可以正常訪問
- [ ] 請求標頭設置正確
- [ ] 回應內容符合預期