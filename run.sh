#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Paper AI Reader — 一键运行脚本
# ============================================================
# 用法:
#   bash run.sh          # 执行完整流程: fetch → read
#   bash run.sh fetch    # 仅抓取
#   bash run.sh read     # 仅筛选
#   bash run.sh download # 单独下载 PDF
#   bash run.sh all      # fetch → read → download
#   bash run.sh list     # 查看支持的会议列表
# ============================================================

# ---------- 配置区（按需修改）----------

# 要抓取的会议（用空格分隔）
CONFERENCES=(cvpr iccv eccv nips icml iclr)

# 目标年份
YEAR=2025

# 每个会议最多抓取论文数
LIMIT_PER_CONF=5300

# AI 筛选用的研究兴趣描述
INTEREST="我关注控制决策算法在机器人和自动驾驶领域中的应用，尤其是强化学习和模仿学习方面的最新进展。"

# 最低兴趣分数（0-100）
MIN_SCORE=70

# 数据目录
DATA_DIR="data/control_decision_papers"

# 抓取结果输出路径
FETCH_OUTPUT="${DATA_DIR}/fetched_papers_${YEAR}.jsonl"

# 筛选结果输出路径
READ_OUTPUT="${DATA_DIR}/selected_papers_${YEAR}.jsonl"

# CSV 输出路径（留空则自动推导）
CSV_OUTPUT="${DATA_DIR}/papers_${YEAR}.csv"

# Markdown 报告输出路径（留空则自动推导）
REPORT_OUTPUT="${DATA_DIR}/papers_${YEAR}_report.md"

# PDF 下载配置
DOWNLOAD_PDFS=false        # 是否下载 PDF（true/false）
PDF_DIR="downloads/papers"
PDF_LOG_OUTPUT=""          # 下载日志路径（留空则不输出）

# CSV / 报告开关
EXPORT_CSV=true
GENERATE_REPORT=true

# ---------- 初始化 ----------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 激活虚拟环境
if [ -d ".venv" ]; then
    # shellcheck disable=SC1091
    source ".venv/bin/activate"
fi

PYTHON="python3"

# ---------- 工具函数 ----------

timestamp() {
    date "+%Y-%m-%d %H:%M:%S"
}

log() {
    echo "[$(timestamp)] $*"
}

# ---------- 命令函数 ----------

cmd_fetch() {
    log "开始抓取论文..."
    $PYTHON main.py fetch \
        --conferences "${CONFERENCES[@]}" \
        --year "$YEAR" \
        --limit-per-conf "$LIMIT_PER_CONF" \
        --output "$FETCH_OUTPUT"
    log "抓取完成: $FETCH_OUTPUT"
}

cmd_read() {
    log "开始 AI 筛选..."

    local args=(
        --input "$FETCH_OUTPUT"
        --interest "$INTEREST"
        --min-score "$MIN_SCORE"
        --output "$READ_OUTPUT"
    )

    if [ "$EXPORT_CSV" = true ]; then
        args+=(--export-csv --csv-output "$CSV_OUTPUT")
    fi

    if [ "$GENERATE_REPORT" = true ]; then
        args+=(--generate-report --report-output "$REPORT_OUTPUT")
    fi

    if [ "$DOWNLOAD_PDFS" = true ]; then
        args+=(--download-pdfs --pdf-dir "$PDF_DIR")
        if [ -n "$PDF_LOG_OUTPUT" ]; then
            args+=(--pdf-log-output "$PDF_LOG_OUTPUT")
        fi
    fi

    $PYTHON main.py read "${args[@]}"
    log "筛选完成: $READ_OUTPUT"
}

cmd_download() {
    log "开始下载 PDF..."
    $PYTHON main.py download \
        --input "$READ_OUTPUT" \
        --output-dir "$PDF_DIR"
    log "下载完成"
}

cmd_list() {
    $PYTHON main.py fetch --list-conferences
}

print_help() {
    cat <<'EOF'
用法:
  bash run.sh         执行完整流程: fetch → read
  bash run.sh fetch   仅抓取论文
  bash run.sh read    仅 AI 筛选
  bash run.sh download 单独下载 PDF
  bash run.sh all     fetch → read → download
  bash run.sh list    查看支持的会议列表
  bash run.sh help    显示此帮助

习惯用法:
  1. 编辑 run.sh 顶部的"配置区"变量
  2. bash run.sh fetch     # 抓取论文
  3. bash run.sh read      # AI 筛选
EOF
}

# ---------- 主入口 ----------

case "${1:-}" in
    fetch)
        cmd_fetch
        ;;
    read)
        cmd_read
        ;;
    download)
        cmd_download
        ;;
    all)
        cmd_fetch
        cmd_read
        cmd_download
        ;;
    list)
        cmd_list
        ;;
    help|--help|-h)
        print_help
        ;;
    "")
        # 默认: fetch → read
        cmd_fetch
        cmd_read
        ;;
    *)
        echo "未知命令: $1"
        echo "支持的命令: fetch, read, download, all, list, help"
        exit 1
        ;;
esac
