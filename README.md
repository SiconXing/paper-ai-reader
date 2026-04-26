# Paper AI Reader

快速抓取公开的重要计算机顶会论文题目和摘要，并用 AI 按你的兴趣进行筛选。

流程被划分成了三个阶段：
- `fetch/` 负责抓取论文信息并补全摘要
- `read/` 负责接入 AI 进行兴趣筛选
每个阶段默认都使用 `JSONL` 逐条写入结果，能明显降低大批量处理时的内存占用。
- `load/` 负责下载 PDF 文件，支持从 arXiv 和其他公开链接下载。

## 功能

- 从 `DBLP` 抓取顶会论文标题、年份、链接等基础信息
- 从 `OpenAlex` 按标题补全摘要
- 用 OpenAI 兼容接口对论文进行兴趣匹配打分和简评
- 支持逐条导出 `JSONL`
- 可选导出 `CSV`
- 可选生成 `Markdown` 摘要报告
- 可选下载筛选后的论文 PDF

## 支持的会议

默认内置这些常见顶会：

- `cvpr`
- `iccv`
- `eccv`
- `nips`
- `icml`
- `iclr`
- `acl`
- `emnlp`
- `naacl`
- `aaai`
- `ijcai`
- `kdd`
- `www`
- `sigir`
- `sigmod`
- `vldb`
- `icse`
- `fse`
- `sosp`
- `osdi`
- `nsdi`
- `sigcomm`
- `chi`
- `mm`

## 环境变量

在 `.env` 中按照OPENAI架构配置环境变量，以防API Key泄露：

```bash
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
```

## 用法

先抓取论文数据：

```bash
python3 main.py fetch \
  --conferences cvpr iccv iclr nips \
  --year 2025 \
  --limit-per-conf 50 \
  --output data/fetched_papers_2025.jsonl
```

再基于抓取结果做 AI 筛选：

```bash
python3 main.py read \
  --input data/fetched_papers_2025.jsonl \
  --interest "我关注多模态大模型、Agent、RAG、长上下文、文档理解和高质量评测方法" \
  --min-score 70 \
  --export-csv \
  --generate-report \
  --output data/selected_papers_2025.jsonl
```

如果只想抓数据：

```bash
python3 main.py fetch \
  --conferences acl emnlp naacl \
  --year 2024 \
  --limit-per-conf 30 \
  --output data/nlp_papers_2024.jsonl
```

如果你想自定义筛选阶段的输出路径：

```bash
python3 main.py read \
  --input data/fetched_papers_2025.jsonl \
  --interest "我关注 Agent、代码智能、推理和高效训练" \
  --export-csv \
  --csv-output data/papers_2025.csv \
  --generate-report \
  --report-output data/papers_2025_report.md \
  --output data/papers_2025.jsonl
```

查看支持的会议缩写：

```bash
python3 main.py fetch --list-conferences
```

下载筛选后的论文 PDF：

```bash
python3 main.py read \
  --input data/fetched_papers_2025.jsonl \
  --interest "我关注 Agent、多模态和文档理解" \
  --download-pdfs \
  --pdf-dir downloads/papers \
  --output data/papers.jsonl
```

也可以基于已有结果文件单独下载：

```bash
python3 main.py download \
  --input data/selected_papers_2025.jsonl \
  --output-dir downloads/papers \
  --log-output data/download_log.json
```

## 输出字段

输出 `JSONL` 中每篇论文会包含：

- `conference`
- `year`
- `title`
- `abstract`
- `dblp_url`
- `doi`
- `openalex_url`
- `interest_score`
- `recommendation`
- `reason`
- `paper_url`
- `arxiv_id`
- `arxiv_url`
- `arxiv_pdf_url`
- `pdf_url`

开启增强项后：

- `--export-csv` 会生成方便筛选和排序的表格文件
- `--generate-report` 会生成一份 Markdown 报告，包含统计摘要、会议分布、Top 论文和推荐阅读列表
- `--download-pdfs` 会尝试下载筛选后的公开 PDF 到本地目录

下载优先级：

- 优先使用 `arxiv_pdf_url`
- 如果没有可用的 arXiv PDF，再回退到 `pdf_url`
- 如果 `paper_url` 本身是 arXiv 论文页，也会自动推导 PDF 链接

## 目录结构

- `fetch/`
- `read/`
- `load/`
- `common/`

其中：

- `fetch/` 负责抓取与富集
- `read/` 负责 AI 筛选与结果输出
- `load/` 负责下载 PDF
- `common/` 放共享模型、HTTP 工具和流式读写逻辑

## 实现思路

1. `fetch` 用 `DBLP` 公开 API 通过 `streamid` 获取某个会议某年的论文列表
2. `fetch` 用 `OpenAlex` 按标题和年份检索，并把 `abstract_inverted_index` 还原成摘要
3. `read` 逐条读取抓取结果，调用 LLM 返回结构化筛选结果
4. 每条记录处理完成后立即写入输出文件，减少峰值内存占用

## 注意

- `DBLP` 和 `OpenAlex` 都是公开数据源，但不同会议的收录完整度可能略有差异
- 某些论文可能查不到摘要，这类论文仍会保留，只是 AI 评分会更保守
- `download` 同时兼容旧的 `JSON` 数组文件和新的 `JSONL` 文件
