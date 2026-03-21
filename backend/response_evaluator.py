# utils/response_evaluator.py
# -*- coding: utf-8 -*-
"""
Gemini JSON 응답 품질 평가기.
규칙 기반으로 스케줄 JSON을 채점하고,
저점수 시 구체적 피드백을 생성해서 재생성을 유도한다.

비용: 0원 (규칙 기반, 외부 API 호출 없음)
"""

import re
from typing import Dict, List, Tuple

# ── 허용된 type 값 ──
VALID_TYPES = {
    "MORNING_BRIEFING", "NIGHT_WRAPUP", "GENERAL", "ROUTINE",
    "COOKING", "MEAL", "HEALTH", "CLOTHING", "LEISURE", "REST",
}

# ── HH:MM 정규식 ──
TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

# ── 존댓말 패턴 (문장 끝) ──
POLITE_ENDINGS = re.compile(r"(요|니다|세요|해요|어요|아요|겠어요|합니다|입니다|볼까요|할게요|드려요|줄게요)[.!?]?$")


def evaluate_schedule(schedule_items: List[Dict], user_input: str = "") -> Tuple[float, List[str]]:
    """
    스케줄 JSON 품질을 0~100점으로 채점.

    Returns:
        (score, issues): 점수와 발견된 문제 목록
    """
    issues: List[str] = []

    if not schedule_items:
        return 0.0, ["schedule 배열이 비어있음"]

    total_points = 0.0
    max_points = 0.0

    # ── 1. 전체 구조 평가 (20점) ──
    max_points += 20

    # 아이템 수 적절성 (최소 1개, 보통 3~10개)
    n = len(schedule_items)
    if n >= 2:
        total_points += 10
    elif n == 1:
        total_points += 5
        issues.append(f"일정이 {n}개뿐임 (보통 3개 이상 기대)")

    # 시간순 정렬 확인
    times = [item.get("time", "") for item in schedule_items]
    if times == sorted(times):
        total_points += 5
    else:
        issues.append("시간순 정렬이 안 되어있음")

    # 중복 시간 확인
    if len(set(times)) == len(times):
        total_points += 5
    else:
        dupes = [t for t in times if times.count(t) > 1]
        issues.append(f"중복 시간 존재: {set(dupes)}")

    # ── 2. 개별 아이템 평가 (아이템당 80/n 점) ──
    per_item_max = 80.0 / max(n, 1)

    for i, item in enumerate(schedule_items):
        item_points = 0.0
        item_max = per_item_max
        prefix = f"[{i}] {item.get('time', '??:??')}"

        # 2-1. 필수 필드 존재 (25%)
        field_weight = item_max * 0.25
        required = ["time", "type", "task", "guide_script"]
        missing = [f for f in required if f not in item or not item[f]]
        if not missing:
            item_points += field_weight
        else:
            issues.append(f"{prefix}: 필수 필드 누락 {missing}")

        # 2-2. time 형식 (15%)
        time_weight = item_max * 0.15
        time_val = str(item.get("time", ""))
        if TIME_RE.match(time_val):
            item_points += time_weight
        else:
            issues.append(f"{prefix}: time 형식 오류 '{time_val}' (HH:MM 필요)")

        # 2-3. type 유효성 (15%)
        type_weight = item_max * 0.15
        type_val = str(item.get("type", "")).upper().strip()
        if type_val in VALID_TYPES:
            item_points += type_weight
        else:
            issues.append(f"{prefix}: 잘못된 type '{type_val}'")

        # 2-4. task 품질 (15%)
        task_weight = item_max * 0.15
        task = str(item.get("task", ""))
        if 2 <= len(task) <= 50:
            item_points += task_weight
        elif len(task) > 50:
            item_points += task_weight * 0.5
            issues.append(f"{prefix}: task가 너무 길음 ({len(task)}자)")
        else:
            issues.append(f"{prefix}: task가 비어있거나 너무 짧음")

        # 2-5. guide_script 품질 (30%)
        gs_weight = item_max * 0.30
        guide = item.get("guide_script", [])
        if not isinstance(guide, list):
            guide = [str(guide)] if guide else []

        gs_score = 0.0

        # 최소 1개 문장
        if len(guide) >= 1:
            gs_score += 0.2
        else:
            issues.append(f"{prefix}: guide_script가 비어있음")

        # 각 문장 검사
        good_sentences = 0
        for j, sentence in enumerate(guide):
            s = str(sentence).strip()
            slen = len(s)

            # 길이 적절성 (5~50자)
            if 5 <= slen <= 50:
                good_sentences += 1
            elif slen > 50:
                issues.append(f"{prefix}: guide_script[{j}] 너무 길음 ({slen}자, 45자 이내 권장)")
            elif slen < 5:
                issues.append(f"{prefix}: guide_script[{j}] 너무 짧음 ({slen}자)")

            # 존댓말 확인
            if POLITE_ENDINGS.search(s):
                good_sentences += 0.5

        if guide:
            gs_score += 0.8 * (good_sentences / (len(guide) * 1.5))

        item_points += gs_weight * min(gs_score, 1.0)

        total_points += item_points
        max_points += 0  # already counted in per_item_max

    max_points += 80
    score = (total_points / max_points) * 100 if max_points > 0 else 0

    # ── 3. 입력 대비 완성도 보너스 체크 ──
    if user_input:
        # 입력에서 시간 패턴 수 vs 출력 아이템 수 비교
        input_times = re.findall(r"\d{1,2}:\d{2}", user_input)
        if input_times and n < len(input_times) * 0.7:
            issues.append(f"입력에 시간 {len(input_times)}개인데 출력이 {n}개뿐 (누락 가능)")
            score *= 0.9  # 10% 감점

    return round(min(score, 100), 1), issues


def generate_retry_feedback(score: float, issues: List[str]) -> str:
    """
    평가 결과를 바탕으로 Gemini에게 줄 재생성 피드백을 생성.
    """
    if not issues:
        return ""

    feedback_lines = [
        "이전 응답에 다음 문제가 있었습니다. 수정해서 다시 생성해주세요:",
    ]

    # 중요도 높은 이슈만 최대 5개
    for issue in issues[:5]:
        feedback_lines.append(f"- {issue}")

    if score < 50:
        feedback_lines.append("\n특히 주의: JSON 스키마를 정확히 지켜주세요.")
    if any("존댓말" in i or "guide_script" in i for i in issues):
        feedback_lines.append("guide_script는 존댓말(~해요, ~합니다)로, 20~45자 이내로 작성해주세요.")

    return "\n".join(feedback_lines)


def evaluate_youtube_queries(queries: List[str]) -> Tuple[float, List[str]]:
    """유튜브 검색 쿼리 품질 평가."""
    issues = []

    if not queries:
        return 0.0, ["쿼리가 비어있음"]

    score = 100.0

    for i, q in enumerate(queries):
        q = str(q).strip()
        if len(q) < 3:
            issues.append(f"쿼리[{i}] 너무 짧음: '{q}'")
            score -= 15
        if len(q) > 40:
            issues.append(f"쿼리[{i}] 너무 길음: '{q}' ({len(q)}자)")
            score -= 10

        # 부적절한 키워드 감지
        bad_keywords = ["먹방", "asmr", "shorts", "쇼츠", "광고", "리뷰"]
        for kw in bad_keywords:
            if kw.lower() in q.lower():
                issues.append(f"쿼리[{i}]에 부적절한 키워드 '{kw}' 포함")
                score -= 20

    # 쿼리 간 다양성
    if len(queries) > 1:
        unique_words = set()
        for q in queries:
            unique_words.update(q.split())
        diversity = len(unique_words) / sum(len(q.split()) for q in queries)
        if diversity < 0.3:
            issues.append("쿼리 간 다양성 부족 (비슷한 쿼리 반복)")
            score -= 15

    return round(max(score, 0), 1), issues
