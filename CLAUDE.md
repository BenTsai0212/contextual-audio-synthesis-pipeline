# CLAUDE.md — Contextual Audio Synthesis Pipeline (CASP)

## 專案概覽

CASP 是一套基於 **Multi-Agent 協作**的自動化 Podcast 內容生產系統，將非結構化文本（心理、歷史、敘事類）轉化為具備「戲劇化結構」與「高保真音訊」的 Podcast 內容。

**技術棧：** Python 3.11 · LangGraph · Claude (Anthropic) · ElevenLabs · Typer CLI · pydantic v2

---

## 系統架構

三個串聯的 Pipeline 階段：

```
原始文本 → [Stage 1: Data Ingestion] → ContextPayload
         → [Stage 2: Dramatic Engine] → scenes.json
         → [Stage 3: Audio Synthesis] → episode.mp3
```

### Stage 1 — Data Ingestion Layer (`casp/ingestion/`)

| 模組 | 功能 |
|---|---|
| `loader.py` | 支援 text file / JSON / URL / RSS 輸入，auto-detect 類型 |
| `denoiser.py` | Claude LLM 去噪：過濾廣告，提取 `CoreFact` + `pivot_point` |

**輸出：** `ContextPayload`（含 `core_facts` 陣列與情緒權重）

### Stage 2 — Dramatic Processing Engine (`casp/dramatic/`) ← MVP 核心

LangGraph `StateGraph` 遞迴循環，三個 Agent 輪流處理：

```
START → [Tension Architect] → [Sensory Renderer] → [Subtext Editor]
                                                          │
                    quality_score < 7.5 ←─────────────────┤  (最多 3 次)
                    帶 revision_notes 重跑                  │
                                                          ↓ quality_score ≥ 7.5
                                                   [Audio Tagger] → END
```

| Agent | 職責 | 輸出 |
|---|---|---|
| **Tension Architect** | 建立「資訊不對稱」，生成 5 幕劇張力地圖 | `TensionMap`（每分鐘壓力值 1-10） |
| **Sensory Renderer** | 消除抽象概念，轉化為具象動作與環境音標記 | `SensoryScript`（含 `ambient_tags`, `physical_actions`） |
| **Subtext Editor** | 品質閘門：檢測 AI 語氣、潛台詞不足 | `SubtextReview`（`quality_score` ≥ 7.5 通過） |
| **Audio Tagger** | 純結構轉換（無 LLM 呼叫）：SensoryScript → Scene JSON | `list[Scene]` |

### Stage 3 — Acoustic Synthesis Gateway (`casp/synthesis/`)

| 模組 | 功能 |
|---|---|
| `parameter_mapper.py` | `EmotionTag` → ElevenLabs `VibeParameters` 映射表 |
| `elevenlabs_client.py` | ElevenLabs API 封裝（`eleven_multilingual_v2`，支援中文） |
| `audio_assembler.py` | pydub 拼接分段音訊 + 匯出 MP3 |

---

## 目錄結構

```
casp/
├── cli.py                      # Typer CLI (casp run / validate / voices / emotion-map)
├── config.py                   # pydantic-settings，讀取 .env
├── models/
│   ├── ingestion.py            # ContextPayload, CoreFact, RawInput
│   ├── dramatic.py             # TensionMap, SensoryScript, SubtextReview
│   ├── scene.py                # Scene, DialogueLayer, SFXLayer, VibeParameters
│   └── pipeline_state.py      # LangGraph PipelineState TypedDict
├── ingestion/
│   ├── loader.py
│   └── denoiser.py
├── dramatic/
│   ├── graph.py                # build_dramatic_graph()
│   ├── state.py                # route_after_editor() 路由函數
│   ├── agents/
│   │   ├── tension_architect.py
│   │   ├── sensory_renderer.py
│   │   └── subtext_editor.py
│   └── prompts/
│       ├── tension_architect.txt
│       ├── sensory_renderer.txt
│       └── subtext_editor.txt
├── synthesis/
│   ├── parameter_mapper.py
│   ├── elevenlabs_client.py
│   └── audio_assembler.py
└── utils/
    ├── llm.py                  # Anthropic client 單例 + CASP_TEST_MODE 攔截
    ├── json_parser.py          # LLM 輸出 JSON 強健解析
    └── logging.py              # Rich 結構化日誌

tests/
├── conftest.py                 # autouse: CASP_TEST_MODE=1（零 API 呼叫）
├── fixtures/                   # 所有 LLM 回應的靜態 fixture JSON
├── unit/                       # 模型、json_parser、parameter_mapper、subtext_editor
└── integration/                # 完整 LangGraph 圖執行測試

examples/
└── psychology_input.json       # 史丹佛監獄實驗範例輸入（完整 ContextPayload）
```

---

## EmotionTag → ElevenLabs 參數映射

| EmotionTag | stability | similarity_boost | style_exaggeration | speed |
|---|---|---|---|---|
| `tension_suspense` | 0.25 | 0.75 | 0.45 | 0.90 |
| `professional_narration` | 0.80 | 0.85 | 0.05 | 1.00 |
| `intimate_confession` | 0.50 | 0.90 | 0.20 | 0.95 |
| `confrontation` | 0.20 | 0.70 | 0.60 | 1.05 |
| `revelation` | 0.35 | 0.80 | 0.40 | 0.92 |

定義於 `casp/synthesis/parameter_mapper.py`，勿在 Agent prompt 中硬編碼。

---

## 環境設定

```bash
# 1. 安裝依賴
pip install -e ".[dev]"

# 2. 設定 API Keys
cp .env.example .env
# 編輯 .env，填入 ANTHROPIC_API_KEY 與 ELEVENLABS_API_KEY

# 3. 執行測試（不需要 API Key）
CASP_TEST_MODE=1 pytest tests/ -v
```

### .env 必要變數

```
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...
DEFAULT_MODEL=claude-opus-4-6
MAX_ITERATIONS=3
OUTPUT_DIR=./output
```

---

## CLI 使用方式

```bash
# MVP 模式：靜態 JSON 輸入，只輸出劇本（不呼叫 ElevenLabs）
casp run examples/psychology_input.json --no-audio

# 完整模式：文本輸入 → 劇本 → 音訊
casp run my_article.txt --output ./my_episode

# 驗證劇本 JSON 格式
casp validate output/scenes.json

# 查看 EmotionTag 參數映射表
casp emotion-map

# 列出可用 ElevenLabs 聲音
casp voices
```

---

## 測試架構

- **`CASP_TEST_MODE=1`**：`casp/utils/llm.py` 改讀 `tests/fixtures/` 而非呼叫 Claude API
- **Fixture 路由**：依 Agent prompt 首行識別（`"You are the Tension Architect"` 等）
- **品質閘門測試**：手動構造低分 `SubtextReview`，驗證圖路由回 `tension_architect`
- **迭代上限測試**：mock subtext editor 永遠拒絕，驗證 `max_iterations` 強制退出

**目前測試狀態：26/26 通過 ✅**

---

## 目前進度

### ✅ 已完成
- [x] 完整專案架構與目錄結構
- [x] 所有 Pydantic 資料模型（ingestion / dramatic / scene / pipeline_state）
- [x] LangGraph `StateGraph` 遞迴循環（三個 Agent + Audio Tagger）
- [x] 三個 Agent 節點實作（含 prompt 文件）
- [x] 品質閘門邏輯（`quality_score` 閾值 7.5，最多 3 次迭代）
- [x] Data Ingestion Layer（loader + LLM denoiser）
- [x] Acoustic Synthesis Gateway（ElevenLabs client + parameter mapper + audio assembler）
- [x] Typer CLI（`run`, `validate`, `voices`, `emotion-map`）
- [x] 測試套件（26 個 unit + integration 測試，`CASP_TEST_MODE` 零 API 呼叫）

### 🔲 待完成（後續迭代）
- [ ] **真實 API 端對端測試**：配置 `ANTHROPIC_API_KEY` 後執行完整 pipeline
- [ ] **SFX 音效庫整合**：目前 `audio_assembler.py` 對無對應檔案的 SFX 插入靜音
- [ ] **RSS / URL 爬取完善**：`feedparser` 目前僅取前 10 則，需加入分頁與去重
- [ ] **聲音設定檔 (Voice Profile)**：YAML 設定檔，支援多角色聲音映射
- [ ] **排程整合**：cron / Airflow 定時執行 pipeline
- [ ] **雲端儲存輸出**：自動上傳至 S3 / GCS 並產生可分享連結
- [ ] **RSS Podcast Feed 生成**：自動產生可訂閱的 RSS feed

---

## 關鍵設計決策

1. **LangGraph 遞迴循環**：使用 `add_conditional_edges` + `_increment` reducer 管理迭代計數，確保最多 `max_iterations` 次後強制退出
2. **品質閘門閾值 7.5/10**：低於此分數時，`revision_notes` 作為 context 回饋給 Tension Architect 重新架構，而非只修改表層措辭
3. **Fixture 攔截模式**：`CASP_TEST_MODE=1` 讓所有 CI 測試零成本，不消耗 API token
4. **`eleven_multilingual_v2`**：支援繁體中文，標準英語模型對 CJK 字元發音錯誤
5. **EmotionTag 集中映射**：所有 ElevenLabs 參數定義於 `parameter_mapper.py`，Agent prompt 中絕不硬編碼數值
