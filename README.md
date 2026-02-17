# 德州撲克全譜勝率運算引擎 (Poker Evaluation Engine)

這是一個極致優化的德州撲克勝率運算工具，結合了 **C++ Lookup Table (LUT)** 技術與 **Python 多進程開發**，能夠在極短時間內完成德州撲克起手牌的全譜（Full Spectrum）勝率運算。

## 🚀 核心優化技術

- **phevaluator 整合**：採用 Perfect Hash 算法，單次 7 張牌評估僅需 ~1.8μs。
- **ctypes 直接記憶體存取**：透過 C API 繞過 Python 的效能瓶頸，實現微秒級函數呼叫。
- **Integer-based API**：完全避免字串拼接與解析，數據以整數 ID 在 Python 與 C++ 間傳遞。
- **同構壓縮 (Isomorphism)**：將 1,326 種起手牌簡化為 169 種代表性組合，計算量大幅縮減。
- **多進程並行**：自動偵測 CPU 核心數並平行運算，效能隨硬體規格線性增長。

## 📂 專案結構

- `PokerFullSpectrum.py`: 主運算引擎，負責 169 手牌的全譜遞迴計算與聚合。
- `PokerQuery.py`: 查詢工具，支援將任意手牌正規化並從結果中檢索勝率。
- `poker_eval_ctypes.py`: Python ctypes 包裝層，支援 Mac (.dylib) 與 Linux (.so)。
- `evaluator/`: C++ 評估器原始碼層。
  - `poker_eval_api.cpp`: 封裝給 Python 呼叫的 C 接口。
  - `phevaluator/`: 核心 Lookup Table 函式庫。
- `cards.yaml`: 全域撲克牌與點數配置。
- `results/`: 運算結果輸出目錄（CSV 格式）。

## 🛠️ 環境架設與編譯

本專案需要編譯 C++ 函式庫以達到極限效能。

### 1. 安裝依賴 (Linux 範例)
```bash
sudo apt update && sudo apt install -y build-essential python3-pip
pip3 install pyyaml
```

### 2. 編譯核心函式庫
```bash
# 編譯 phevaluator 靜態庫
cd evaluator/phevaluator/cpp
make libpheval.a

# 編譯橋接函式庫 (針對 Linux)
cd ../..
g++ -std=c++17 -O2 -shared -fPIC -I./phevaluator/cpp/include -L./phevaluator/cpp -o libpoker_eval.so poker_eval_api.cpp ./phevaluator/cpp/libpheval.a
```
*(如果是 MacOS，請將輸出檔名改為 `libpoker_eval.dylib`)*

## 📈 使用指南

### 執行全譜運算
```bash
python3 PokerFullSpectrum.py
```
這會開始遍歷 169 種起手牌。每手牌大約需要 1-2 分鐘（視 CPU 效能而定），結果會儲存在 `results/` 資料夾。

### 查詢特定手牌勝率
使用 `PokerQuery.py` 可以自動進行手牌正規化並查詢：
```bash
# 查詢 Preflop
python3 PokerQuery.py AH KD

# 查詢特定 Flop 階段
python3 PokerQuery.py AH KD 2S 3H 4D
```

## 📊 效能表現
經過測試，整合 LUT 與 Integer API 後，每組 Board 的平均計算耗時約 **0.000038s**，相較於最初的 Pipe IPC 模式提升了 **3,600 倍** 以上。

---
*本專案由 Antigravity AI 輔助開發。*
