import streamlit as st
import requests
import json
from datetime import datetime
import os
import time

class ChatApp:
    def __init__(self):
        self.setup_streamlit()
        self.initialize_state()
        self.setup_ollama_connection()
        self.available_models = self.get_available_models()

    def setup_streamlit(self):
        """設置 Streamlit 頁面配置"""
        st.set_page_config(page_title="AI ChatBot", layout="wide")

    def initialize_state(self):
        """初始化聊天狀態"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "selected_model" not in st.session_state:
            st.session_state.selected_model = "taide-8b"
        if "temperature" not in st.session_state:
            st.session_state.temperature = 0.5
        if "max_tokens" not in st.session_state:
            st.session_state.max_tokens = 2048
        if "num_threads" not in st.session_state:
            st.session_state.num_threads = 4

    def setup_ollama_connection(self):
        """設置 Ollama 連接"""
        self.ollama_base_url = os.getenv('OLLAMA_API_BASE_URL', 'http://localhost:11434')
        if not self.ollama_base_url:
            st.error("未設置 OLLAMA_API_BASE_URL 環境變數")
            return
        
        # 移除不需要的設置，因為我們使用 ngrok URL
        # self.ollama_host = os.getenv('OLLAMA_HOST', 'localhost')
        # self.ollama_port = os.getenv('OLLAMA_PORT', '11434')

    def get_available_models(self):
        """獲取可用的 Ollama 模型列表"""
        try:
            api_url = f"{self.ollama_base_url}/api/tags"
            
            # 添加 ngrok 所需的標頭
            headers = {
                'Content-Type': 'application/json',
                'ngrok-skip-browser-warning': 'true',
                'User-Agent': 'Mozilla/5.0'
            }
            
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    response = requests.get(
                        api_url,
                        headers=headers,  # 使用新的標頭
                        timeout=10
                    )
                    if response.status_code == 200:
                        models = [model["name"] for model in response.json()["models"]]
                        return models
                    retry_count += 1
                except requests.exceptions.ConnectionError:
                    st.warning(f"連接到 Ollama 服務失敗 (嘗試 {retry_count + 1}/{max_retries})")
                    time.sleep(2)
                    retry_count += 1
            
            st.error(f"""
            無法連接到 Ollama 服務。請確認：
            1. Ollama 服務是否正在運行
            2. 環境變數是否正確設置
            - 當前連接 URL: {self.ollama_base_url}
            """)
            return ["taide-8b"]
            
        except Exception as e:
            st.error(f"無法獲取模型列表: {str(e)}")
            return ["taide-8b"]

    def call_ollama(self, prompt):
        """與 Ollama API 通信"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'ngrok-skip-browser-warning': 'true',
                'User-Agent': 'Mozilla/5.0'
            }
            
            api_url = f"{self.ollama_base_url}/api/generate"
            
            # 優化默認參數
            temperature = st.session_state.get('temperature', 0.5)  # 降低溫度
            max_tokens = st.session_state.get('max_tokens', 2048)  # 減少預設長度
            
            with st.chat_message("assistant"):
                with st.spinner("AI思考中..."):
                    response = requests.post(
                        api_url,
                        headers=headers,
                        json={
                            "model": st.session_state.selected_model,
                            "prompt": prompt,
                            "stream": True,
                            "context": st.session_state.get("context", []),
                            "options": {
                                "temperature": temperature,
                                "num_predict": max_tokens,
                                "num_ctx": 2048,  # 減少上下文窗口
                                "num_thread": 4,  # 減少執行緒
                                "top_k": 20,  # 降低採樣數量
                                "top_p": 0.7,  # 調整採樣機率
                                "repeat_penalty": 1.0,  # 降低重複懲罰
                                "num_gpu": 1,
                                "stop": ["User:", "Assistant:"],
                            }
                        },
                        stream=True,
                        timeout=30  # 降低超時時間
                    )
                    
                    if response.status_code == 200:
                        placeholder = st.empty()
                        full_response = ""
                        buffer = ""  # 添加緩衝區
                        
                        # 優化串流處理
                        for line in response.iter_lines():
                            if line:
                                try:
                                    json_response = json.loads(line)
                                    chunk = json_response.get("response", "")
                                    buffer += chunk
                                    full_response += chunk
                                    
                                    # 累積一定長度才更新，減少刷新頻率
                                    if len(buffer) >= 50:
                                        placeholder.markdown(full_response + "▌")
                                        buffer = ""
                                except json.JSONDecodeError:
                                    continue
                        
                        placeholder.markdown(full_response)
                        return full_response
                    else:
                        st.error(f"API 錯誤: {response.status_code}")
                        return None
                        
        except requests.exceptions.Timeout:
            st.error("請求超時，請稍後再試")
        except Exception as e:
            st.error(f"錯誤: {str(e)}")
        return None

    def save_chat_history(self):
        """保存聊天記錄"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_history_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False, indent=2)
        
        return filename

    def display_chat_interface(self):
        """顯示聊天界面"""
        try:
            st.title("AI ChatBot")

            # 側邊欄設置
            with st.sidebar:
                st.title("設置")
                
                # 模型選擇
                model_index = (
                    self.available_models.index(st.session_state.selected_model)
                    if st.session_state.selected_model in self.available_models
                    else 0
                )
                
                selected_model = st.selectbox(
                    "選擇模型",
                    self.available_models,
                    index=model_index,
                    key="model_selector"
                )
                
                if selected_model != st.session_state.selected_model:
                    st.session_state.selected_model = selected_model
                    st.session_state.context = []
                    st.rerun()
                
                # 先添加性能模式選擇
                performance_mode = st.radio(
                    "性能模式",
                    ["平衡", "速度優先", "質量優先"],
                    key="performance_mode"
                )
                
                # 根據性能模式預設參數
                if performance_mode == "速度優先":
                    default_temp = 0.8
                    default_tokens = 2048
                    default_threads = 4
                elif performance_mode == "質量優先":
                    default_temp = 0.7
                    default_tokens = 8192
                    default_threads = 8
                else:  # 平衡模式
                    default_temp = 0.5
                    default_tokens = 2048
                    default_threads = 4
                
                # 使用動態默認值的滑塊
                st.session_state.temperature = st.slider(
                    "回應創造性 (溫度)", 
                    min_value=0.0, 
                    max_value=2.0,
                    value=default_temp,
                    step=0.1,
                    key=f"temp_slider_{performance_mode}"  # 動態 key
                )
                
                st.session_state.max_tokens = st.slider(
                    "最大回應長度 (tokens)",
                    min_value=100,
                    max_value=8192,
                    value=default_tokens,
                    step=100,
                    key=f"tokens_slider_{performance_mode}"  # 動態 key
                )
                
                st.session_state.num_threads = st.slider(
                    "執行緒數量",
                    min_value=1,
                    max_value=16,
                    value=default_threads,
                    step=1,
                    key=f"threads_slider_{performance_mode}"  # 動態 key
                )
                
                st.write(f"當前使用模型: {st.session_state.selected_model}")
                
                if st.button("清除聊天記錄"):
                    st.session_state.messages = []
                    st.session_state.context = []
                    st.rerun()
                
                if st.button("保存聊天記錄"):
                    filename = self.save_chat_history()
                    st.success(f"聊天記錄已保存至: {filename}")

            # 顯示聊天記錄
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # 聊天輸入
            if prompt := st.chat_input("請輸入您的問題"):
                # 添加用戶消息
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # 獲取 AI 回應
                response = self.call_ollama(prompt)
                
                if response:
                    # 保存回應
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
        except Exception as e:
            st.error(f"顯示界面錯誤: {str(e)}")


def main():
    try:
        app = ChatApp()
        app.display_chat_interface()
    except Exception as e:
        st.error(f"程序運行錯誤: {str(e)}")


if __name__ == "__main__":
    main()