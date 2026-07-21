# Candidate B r003 diagnostics run_001 incident root-cause report

## 結論

run_001 的 196 TimeoutError 與 2 WorkerProcessExit 不可用於 L4/L5 分類；usable classifications = 0。確認的是 protocol/IPC failure，而不是 196 個 model programs 的共同 runtime failure。

## 九項調查

1. 舊 timeout 在 `process.start()` 後立刻開始，沒有 ready handshake；12 秒同時涵蓋 fork/startup、candidate module exec、全部 base+plus inputs、序列化、Queue flush 與 child finalization。
2. EvalPlus dataset 只在 parent 載入一次；child 沒有重載 dataset，也沒有建立 expected outputs。重複 dataset initialization 不是根因。
3. 舊 runner 明確使用 `get_context("fork")`，因此 Python 3.14 的 POSIX 預設 forkserver 變更沒有直接生效；但 receipt 未記錄 Python/WSL版本，且 explicit fork 未做 single-threaded/known-pass calibration。
4. parent 先 `process.join(12)`，之後才 `queue.get()`。Python 官方文件明示 child put Queue 後會等待 feeder flush，先 join、後 get 可能 deadlock。
5. 196 rows 沒有任何 worker payload；父程序在 join timeout 後 terminate，故無法區分 candidate timeout、Queue feeder/finalization block 或 startup cost。
6. worker 的 module/call/outer exception 都以同一 Queue 回傳；catch 本身存在，但 parent 的讀取順序不能保證 payload 被消費。
7. 舊 10 CPU/12 wall 秒沒有正常 worker startup 或 known-pass full-workload calibration，不能證明 timeout 大於正常成本。
8. 兩個 WorkerProcessExit 是 child 在沒有 Queue payload時先退出；舊 runner未保存 exitcode/signal。兩者同屬 Mbpp/119，source可見 non-progress風險，但事故資料不足以作 L4 結論。
9. 舊 synthetic tests只覆蓋 parser、privacy、deterministic bytes與預設不執行；未覆蓋 production dataset load、worker-ready、full inputs、Queue drain-before-join、signal exit或 known-pass calibration。

官方依據：

- https://docs.python.org/3/library/multiprocessing.html#joining-processes-that-use-queues
- https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods

## r002 修正

r002 使用 one-way Pipe、ready/go handshake、startup與candidate timeout分離、收到result後才join、粗粒度duration buckets、exit/EOF fail-closed。先凍結8格不同task的development known-pass cohort；任一格不能正常 returned，即禁止正式198格。diagnostic結果不得成為Healer runtime input或rule evidence。
