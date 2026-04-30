"""
convert_csv.py
--------------
구 형식 map.csv → 신 형식 map.csv 변환 스크립트

구 형식 links:  [{"링크이름": "URL"}, ...]
신 형식 links:  [{"name": "링크이름", "url": "URL", "class": "pdf"}, ...]

class 값은 URL을 분석해 자동 추론합니다.
  vid   → YouTube, Vimeo
  sheet → Google Sheets, .xls/.xlsx/.csv
  ppt   → Google Slides, .ppt/.pptx
  doc   → Google Docs, .doc/.docx
  pdf   → .pdf
  ""    → 그 외 (기본 web 아이콘)

사용법:
  python convert_csv.py                         # map.csv → map_new.csv
  python convert_csv.py input.csv               # 입력 파일 지정
  python convert_csv.py input.csv output.csv    # 입출력 파일 모두 지정
"""

import csv
import json
import re
import sys
from pathlib import Path


# ── 자동 추론 (inferClass JS 로직과 동일) ──────────────────────────────────
def infer_class(url: str) -> str:
    if not url:
        return ""
    lower = url.lower()

    if "youtube.com" in lower or "youtu.be" in lower or "vimeo.com" in lower:
        return "vid"
    if "docs.google.com/spreadsheets" in lower or "sheets.google.com" in lower:
        return "sheet"
    if "docs.google.com/presentation" in lower or "slides.google.com" in lower:
        return "ppt"
    if "docs.google.com" in lower:
        return "doc"
    if re.search(r"\.pdf(\?|$)", lower):
        return "pdf"
    if re.search(r"\.(doc|docx)(\?|$)", lower):
        return "doc"
    if re.search(r"\.(ppt|pptx)(\?|$)", lower):
        return "ppt"
    if re.search(r"\.(xls|xlsx|csv)(\?|$)", lower):
        return "sheet"

    return "web"


# ── 구 형식 링크 객체 → 신 형식 변환 ──────────────────────────────────────
def normalize_link(link_obj: dict) -> dict:
    # 이미 신 형식인 경우 (name + url 키가 있으면)
    if "name" in link_obj and "url" in link_obj:
        return {
            "name":  link_obj["name"],
            "url":   link_obj["url"],
            "class": link_obj.get("class", infer_class(link_obj["url"])),
        }

    # 구 형식: {"링크이름": "URL"}
    items = [(k, v) for k, v in link_obj.items()]
    if not items:
        return {}

    name, url = items[0]
    return {
        "name":  name,
        "url":   url,
        "class": infer_class(url),
    }


# ── CSV 한 행의 links 컬럼 파싱 ───────────────────────────────────────────
def parse_links_column(raw: str) -> list:
    raw = raw.strip()
    if not raw:
        return []

    # 끝에 trailing comma 가 있으면 제거 후 파싱
    # 예: [{"a":"b"},{"c":"d"},]  →  [{"a":"b"},{"c":"d"}]
    cleaned = re.sub(r",\s*]", "]", raw)

    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    return []


# ── 메인 변환 로직 ─────────────────────────────────────────────────────────
def convert(input_path: Path, output_path: Path) -> None:
    rows_in  = input_path.read_text(encoding="utf-8").splitlines()
    header   = rows_in[0]   # 헤더 그대로 유지
    data_rows = rows_in[1:]

    converted = [header]
    stats = {"total": 0, "links_converted": 0, "already_new": 0, "no_links": 0}

    for raw_row in data_rows:
        raw_row = raw_row.strip()
        if not raw_row:
            continue

        stats["total"] += 1

        # links JSON 은 [ 로 시작하는 첫 번째 위치부터
        json_start = raw_row.find("[")

        if json_start == -1:
            # links 없음 → 그대로
            converted.append(raw_row)
            stats["no_links"] += 1
            continue

        base  = raw_row[:json_start].rstrip(",")
        links_raw = raw_row[json_start:]

        link_objs = parse_links_column(links_raw)

        if not link_objs:
            converted.append(raw_row)
            stats["no_links"] += 1
            continue

        # 이미 신 형식인지 확인 (첫 번째 항목 기준)
        first = link_objs[0]
        already_new = "name" in first and "url" in first

        new_links = [normalize_link(obj) for obj in link_objs if obj]

        links_str = json.dumps(new_links, ensure_ascii=False, separators=(",", ":"))
        converted.append(f"{base},{links_str}")

        if already_new:
            stats["already_new"] += 1
        else:
            stats["links_converted"] += 1

    output_path.write_text("\n".join(converted), encoding="utf-8")

    # 결과 리포트
    print(f"✅ 변환 완료: {output_path}")
    print(f"   총 행 수         : {stats['total']}")
    print(f"   구 형식 → 신 형식 : {stats['links_converted']}행")
    print(f"   이미 신 형식      : {stats['already_new']}행")
    print(f"   링크 없음         : {stats['no_links']}행")


# ── 엔트리포인트 ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]

    input_path  = Path(args[0]) if len(args) >= 1 else Path("map.csv")
    output_path = Path(args[1]) if len(args) >= 2 else input_path.with_name(
        input_path.stem + "_new" + input_path.suffix
    )

    if not input_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {input_path}")
        sys.exit(1)

    convert(input_path, output_path)