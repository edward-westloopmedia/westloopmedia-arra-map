import csv
import json
import re

# ── 헬퍼 함수 ────────────────────────────────────────────────

def starts_with_digit(value: str) -> bool:
    return bool(value) and value.strip()[0].isdigit()

def is_yes(value: str) -> bool:
    return value.strip().upper() == "YES"

def is_all_english_words(value: str) -> bool:
    """숫자로 시작하지 않고, 영문/숫자/공백/특수문자로 구성된 경우"""
    return not starts_with_digit(value) and bool(value.strip())

def to_title_case(value: str) -> str:
    return ' '.join(word.capitalize() for word in value.strip().split())

def extract_markdown_link(value: str):
    """[text](url) 형태면 (text, url) 반환, 아니면 None"""
    m = re.match(r'^\[(.+?)\]\((https?://[^\)]+)\)$', value.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None

def build_name(col_name: str, value: str) -> str:
    v = value.strip()
    if is_yes(v):
        return col_name
    elif starts_with_digit(v):
        return f"{col_name} : Spec {v}"
    elif is_all_english_words(v):
        return f"{col_name} : {to_title_case(v)}"
    else:
        return f"{col_name} : {v}"

def get_class(url: str) -> str:
    return "pdf" if url.strip().lower().endswith(".pdf") else "web"

def parse_map_csv(filepath: str):
    """
    map.csv 를 줄 단위로 읽어서 파싱.
    links 컬럼의 JSON 배열([...]) 안에 콤마가 있어도 안전하게 처리.
    전략: 각 줄에서 '[' 시작 위치를 찾아 그 앞은 csv 파싱, 그 뒤는 JSON으로 처리.
    """
    with open(filepath, encoding="utf-8-sig") as f:
        lines = f.readlines()

    if not lines:
        return [], []

    # 헤더 파싱
    header_line = lines[0].rstrip("\r\n")
    headers = [h.strip() for h in next(csv.reader([header_line]))]
    headers = [h for h in headers if h]

    links_idx = headers.index("links") if "links" in headers else -1
    parsed_rows = []

    for line in lines[1:]:
        line = line.rstrip("\r\n")
        if not line.strip():
            continue

        # links 컬럼이 없으면 그냥 csv 파싱
        if links_idx == -1:
            row_vals = next(csv.reader([line]))
            row_dict = {headers[i]: row_vals[i].strip() if i < len(row_vals) else "" for i in range(len(headers))}
            parsed_rows.append(row_dict)
            continue

        # links 컬럼 시작 위치 찾기: '[' 또는 빈 값(줄 끝 콤마 이후)
        # links 이전 컬럼 수만큼 콤마를 세어서 분리
        # 정규식으로 앞부분(links 이전) 추출
        # links 이전 컬럼들은 콤마로 구분된 단순 값이라고 가정
        bracket_match = re.search(r'(\[.*\])\s*$', line)
        if bracket_match:
            links_json = bracket_match.group(1).strip()
            before = line[:bracket_match.start()].rstrip(",").rstrip()
        else:
            # links 가 비어있는 경우 — 마지막 콤마 이후가 빈 값
            before = line.rstrip(",").rstrip()
            links_json = ""

        # before 부분을 csv 파싱
        before_vals = next(csv.reader([before]))
        row_dict = {}
        for i in range(min(links_idx, len(headers))):
            row_dict[headers[i]] = before_vals[i].strip() if i < len(before_vals) else ""

        row_dict["links"] = links_json
        parsed_rows.append(row_dict)

    return headers, parsed_rows

# ── spec.csv 읽기 ────────────────────────────────────────────

SPEC_COLS = ["FDR", "CIR", "Soil Cement", "Cement Treated Base", "CCPR", "Lime"]

spec_data: dict = {}

with open("spec.csv", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    print(f"📋 spec.csv 컬럼명: {reader.fieldnames}")
    for row in reader:
        location = row["Location"].strip().upper()
        url_val = ""
        for k in row:
            if k and k.strip().upper() == "URL":
                url_val = (row[k] or "").strip()
                break
        row["_url"] = url_val
        spec_data[location] = row

# ── map.csv 읽기 + 병합 ──────────────────────────────────────

fieldnames, input_rows = parse_map_csv("map.csv")
output_rows = []

for row in input_rows:
    name_upper = row.get("name", "").strip().upper()

    if name_upper in spec_data:
        spec_row = spec_data[name_upper]
        url = spec_row.get("_url", "").strip()
        cls = get_class(url) if url else "web"

        print(f"  🔗 {name_upper} URL: '{url}'")

        new_entries = []
        for col in SPEC_COLS:
            val = (spec_row.get(col) or "").strip()
            if not val:
                continue

            # 마크다운 링크 [text](url) 형태 처리
            md = extract_markdown_link(val)
            if md:
                md_name, md_url = md
                md_cls = get_class(md_url)
                new_entries.append({
                    "name": md_name,
                    "url": md_url,
                    "class": md_cls
                })
                continue

            entry_name = build_name(col, val)
            new_entries.append({
                "name": entry_name,
                "url": url,
                "class": cls
            })

        links_raw = row.get("links", "").strip()
        existing_links = []
        if links_raw:
            try:
                existing_links = json.loads(links_raw)
                print(f"  ✅ 기존 links 파싱 성공: {len(existing_links)}개")
            except json.JSONDecodeError as e:
                print(f"  ⚠️ links 파싱 실패: {e} | 원본: {links_raw[:60]}")

        existing_links.extend(new_entries)
        row["links"] = json.dumps(existing_links, ensure_ascii=False)

    output_rows.append(row)

# ── map_merged.csv 쓰기 ──────────────────────────────────────

with open("map_merged.csv", "w", newline="", encoding="utf-8") as f:
    # 헤더 쓰기
    f.write(",".join(fieldnames) + "\n")
    for row in output_rows:
        parts = []
        for h in fieldnames:
            val = row.get(h, "")
            # links 컬럼은 따옴표 없이 그대로, 나머지는 콤마 포함 시 따옴표로 감싸기
            if h == "links":
                parts.append(val)
            elif "," in str(val):
                parts.append(f'"{val}"')
            else:
                parts.append(str(val))
        f.write(",".join(parts) + "\n")

print("\n✅ 완료! map_merged.csv 파일이 생성됐어요.")