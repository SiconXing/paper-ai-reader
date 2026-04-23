# Paper AI Reader

快速抓取公开的重要计算机顶会论文题目和摘要，并用 AI 按你的兴趣进行筛选。

## 功能

- 从 `DBLP` 抓取顶会论文标题、年份、链接等基础信息
- 从 `OpenAlex` 按标题补全摘要
- 用 OpenAI 兼容接口对论文进行兴趣匹配打分和简评
- 支持导出 `JSON`
- 可选导出 `CSV`
- 可选生成 `Markdown` 摘要报告

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

在 `.env` 中配置：

```bash
OPENAI_API_KEY=your_api_key
# 可选，默认就是 OpenAI 官方接口
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
```

## 用法

先抓取并按兴趣筛选：

```bash
python3 main.py \
  --conferences cvpr iccv iclr nips \
  --year 2025 \
  --limit-per-conf 50 \
  --interest "我关注多模态大模型、Agent、RAG、长上下文、文档理解和高质量评测方法" \
  --min-score 70 \
  --export-csv \
  --generate-report \
  --output data/selected_papers_2025.json
```

如果只想先抓数据、不调用 AI：

```bash
python3 main.py \
  --conferences acl emnlp naacl \
  --year 2024 \
  --limit-per-conf 30 \
  --skip-ai \
  --export-csv \
  --output data/nlp_papers_2024.json
```

如果你想自定义增强项输出路径：

```bash
python3 main.py \
  --conferences iclr icml nips \
  --year 2025 \
  --interest "我关注 Agent、代码智能、推理和高效训练" \
  --export-csv \
  --csv-output data/papers_2025.csv \
  --generate-report \
  --report-output data/papers_2025_report.md \
  --output data/papers_2025.json
```

查看支持的会议缩写：

```bash
python3 main.py --list-conferences
```

## 输出字段

输出 JSON 中每篇论文会包含：

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

开启增强项后：

- `--export-csv` 会生成方便筛选和排序的表格文件
- `--generate-report` 会生成一份 Markdown 报告，包含统计摘要、会议分布、Top 论文和推荐阅读列表

## 实现思路

1. 用 `DBLP` 公开 API 通过 `streamid` 获取某个会议某年的论文列表
2. 用 `OpenAlex` 按标题和年份检索，并把 `abstract_inverted_index` 还原成摘要
3. 调用 LLM 返回结构化筛选结果

## 注意

- `DBLP` 和 `OpenAlex` 都是公开数据源，但不同会议的收录完整度可能略有差异
- 某些论文可能查不到摘要，这类论文仍会保留，只是 AI 评分会更保守
- 如果你之后想接入更多会议，只需要在代码里的会议映射表补充 `DBLP stream id`
