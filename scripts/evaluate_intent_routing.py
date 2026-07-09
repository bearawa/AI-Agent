# -*- coding: utf-8 -*-
"""
AIZS 意图路由准确率评测脚本。
默认使用规则匹配（不依赖真实 API Key）。
使用 --use-llm 参数启用大模型兜底。
"""
import sys
import os
import csv
import argparse
from pathlib import Path
from collections import defaultdict

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

# 解决 Windows 命令行下打印 Emoji 的编码问题
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from services.intent_service import IntentService
from utils.logger import logger


def run_evaluation(use_llm: bool = False):
    csv_path = Path(__file__).resolve().parent.parent / "tests" / "intent_test_set.csv"
    if not csv_path.exists():
        print(f"评测集文件不存在: {csv_path}")
        return

    print("=" * 70)
    print("          AIZS｜校园智能咨询平台 — 意图路由准确率评测工具")
    print("=" * 70)
    print(f"评测模式: {'规则匹配 + LLM 兜底' if use_llm else '仅规则匹配（不调用 API）'}")
    print()

    # 临时禁用后台详细日志以保持控制台整洁
    logger.setLevel("WARNING")

    intent_service = IntentService()

    # 如果不使用 LLM，禁用 API Key 以强制走规则
    if not use_llm:
        intent_service.api_key = ""

    total = 0
    correct = 0
    results = []
    category_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    errors = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            query = row["question"] if "question" in row else row.get("query", "")
            true_intent = row["expected_intent"] if "expected_intent" in row else row.get("intent", "")

            if not query or not true_intent:
                continue

            # 分类预测
            pred = intent_service.classify_intent(query)
            pred_intent = pred["intent"]
            confidence = pred["confidence"]
            reason = pred["reason"]

            is_correct = (pred_intent == true_intent)
            total += 1
            if is_correct:
                correct += 1

            category_stats[true_intent]["total"] += 1
            if is_correct:
                category_stats[true_intent]["correct"] += 1
            else:
                errors.append({
                    "query": query,
                    "true": true_intent,
                    "pred": pred_intent,
                    "reason": reason
                })

            results.append({
                "query": query,
                "true": true_intent,
                "pred": pred_intent,
                "confidence": confidence,
                "reason": reason,
                "status": "正确" if is_correct else "错误"
            })

    accuracy = (correct / total) * 100 if total > 0 else 0.0

    # 打印详细预测日志
    print(f"{'序号':<4}{'用户提问':<28}{'真实意图':<14}{'预测意图':<14}{'置信度':<8}{'状态':<6}{'识别原因'}")
    print("-" * 120)
    for idx, res in enumerate(results, 1):
        q_truncated = res["query"][:22] + "..." if len(res["query"]) > 22 else res["query"]
        print(f"{idx:<4}{q_truncated:<28}{res['true']:<14}{res['pred']:<14}{res['confidence']:<8.2f}{res['status']:<6}{res['reason']}")

    # 总体统计
    print()
    print("=" * 70)
    print(f"评估完成！")
    print(f"总测试样本数: {total}")
    print(f"正确分类数:   {correct}")
    print(f"总体准确率:   {accuracy:.2f}%")
    print("=" * 70)

    # 各分类准确率
    print()
    print("各分类准确率:")
    print(f"{'分类':<16}{'样本数':<8}{'正确数':<8}{'准确率'}")
    print("-" * 50)
    for cat in ["admission", "academic", "logistics", "campus_life", "other"]:
        stats = category_stats.get(cat, {"total": 0, "correct": 0})
        cat_acc = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0.0
        print(f"{cat:<16}{stats['total']:<8}{stats['correct']:<8}{cat_acc:.1f}%")

    # 错误样例
    if errors:
        print()
        print(f"错误样例 (共 {len(errors)} 条):")
        print("-" * 70)
        for err in errors[:10]:  # 最多显示 10 条
            print(f"  提问: {err['query']}")
            print(f"  真实: {err['true']}  预测: {err['pred']}  原因: {err['reason']}")
            print()

    print("=" * 70)
    if accuracy >= 80.0:
        print("✅ 恭喜！意图路由准确率达到目标指标（> 80%）")
    else:
        print("⚠️ 警告：意图路由准确率未达到 80%，请优化关键词规则或启用 --use-llm")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIZS 意图路由准确率评测")
    parser.add_argument("--use-llm", action="store_true", help="启用大模型兜底分类（需要配置 API Key）")
    args = parser.parse_args()
    run_evaluation(use_llm=args.use_llm)
