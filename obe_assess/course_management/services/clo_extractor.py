import re
from course_management.utils import extract_text_from_file


class OBECourseExtractor:
    _CLO_RE = re.compile(r"\bCLO\s*[-:]?\s*(\d+)\b", re.IGNORECASE)
    _PLO_RE = re.compile(r"\b(?:SO\s*\(\s*PLO\s*\)|PLO)\s*[-:)]?\s*(\d+)\b", re.IGNORECASE)
    _BT_RE = re.compile(r"\b([CPA])\s*[-:]?\s*(\d+)\b", re.IGNORECASE)

    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.filename = file_obj.name

    def _clean_cell(self, value):
        text = str(value or "")
        text = text.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"_([^_]+)_", r"\1", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _split_markdown_row(self, line):
        row = line.strip()
        if not row.startswith("|"):
            return []
        if row.endswith("|"):
            row = row[1:-1]
        else:
            row = row[1:]
        return [self._clean_cell(cell) for cell in row.split("|")]

    def _is_separator_row(self, cells):
        if not cells:
            return False
        return all(re.fullmatch(r"[:\-\s]+", cell or "") for cell in cells)

    def _find_header_index(self, rows):
        best_idx = 0
        best_score = -1
        header_terms = [
            "no",
            "course learning outcome",
            "learning outcome",
            "plo",
            "bt level",
            "bloom",
            "cognitive",
            "assessment",
            "teaching",
        ]
        for i, cells in enumerate(rows):
            joined = " ".join(cells).lower()
            # Header row should not itself be a CLO data row.
            if self._extract_code(joined):
                continue
            score = 0
            for term in header_terms:
                if term in joined:
                    score += 1
            if score > best_score:
                best_score = score
                best_idx = i
        if best_score >= 1:
            return best_idx
        return 0

    def _column_index(self, header_cells, names):
        for idx, col in enumerate(header_cells):
            c = col.lower()
            if any(name in c for name in names):
                return idx
        return None

    def _column_indices(self, header_cells, names):
        indices = []
        for idx, col in enumerate(header_cells):
            c = col.lower()
            if any(name in c for name in names):
                indices.append(idx)
        return indices

    def _extract_code(self, text):
        m = self._CLO_RE.search(text or "")
        if not m:
            return ""
        return f"CLO-{m.group(1)}"

    def _extract_code_num(self, code):
        m = re.search(r"(\d+)", code or "")
        return m.group(1) if m else ""

    def _segment_text_for_code(self, text, code):
        """
        If OCR/table extraction merges multiple CLO statements into one cell,
        keep only the segment belonging to the current CLO code.
        """
        value = self._clean_cell(text)
        if not value:
            return ""

        matches = list(self._CLO_RE.finditer(value))
        if len(matches) <= 1:
            return value

        target_num = self._extract_code_num(code)
        target_idx = 0
        if target_num:
            for idx, m in enumerate(matches):
                if m.group(1) == target_num:
                    target_idx = idx
                    break

        start = matches[target_idx].start()
        end = matches[target_idx + 1].start() if target_idx + 1 < len(matches) else len(value)
        return value[start:end].strip()

    def _plo_prefix_for_header(self, header_text):
        h = (header_text or "").lower()
        if "cs" in h or "so(plo)" in h or "so (plo)" in h:
            return "PLO(CS)"
        if "se" in h:
            return "PLO(SE)"
        return "PLO"

    def _extract_plos(self, text, allow_numeric=False, prefix="PLO"):
        plos = []
        seen = set()
        source = text or ""
        for num in self._PLO_RE.findall(source):
            value = f"{prefix}-{num}"
            if value not in seen:
                seen.add(value)
                plos.append(value)
        if allow_numeric and not plos:
            numeric_tokens = re.findall(r"\b\d{1,2}\b", source)
            for token in numeric_tokens:
                if int(token) > 20:
                    continue
                value = f"{prefix}-{token}"
                if value not in seen:
                    seen.add(value)
                    plos.append(value)
        if len(plos) > 2:
            return plos[:2]
        return plos

    def _extract_bt(self, text):
        m = self._BT_RE.search(text or "")
        if not m:
            return ""
        return f"{m.group(1).upper()}-{m.group(2)}"

    def _normalize_clo_text(self, text, code):
        value = self._clean_cell(text)
        value = re.sub(r"^\s*[-:]", "", value).strip()
        if code:
            value = re.sub(rf"^\s*{re.escape(code)}\s*[:\-.]?\s*", "", value, flags=re.IGNORECASE).strip()
        return value

    def _record_score(self, record):
        return (
            1 if record.get("bloom") else 0,
            len(record.get("mapped_plos", [])),
            min(len(record.get("text", "")), 220),
        )

    def _table_blocks(self, text):
        blocks = []
        current = []
        for raw in (text or "").splitlines():
            line = raw.strip()
            if line.startswith("|") and line.count("|") >= 2:
                current.append(line)
            else:
                if current:
                    blocks.append(current)
                    current = []
        if current:
            blocks.append(current)
        return blocks

    def _extract_from_tables(self, text):
        clos_by_code = {}

        for block in self._table_blocks(text):
            rows = [self._split_markdown_row(line) for line in block]
            rows = [r for r in rows if r and not self._is_separator_row(r)]
            if len(rows) < 2:
                continue

            header_idx = self._find_header_index(rows)
            header = rows[header_idx]
            data_rows = rows[header_idx + 1 :]
            if not data_rows:
                continue

            code_idx = self._column_index(header, ["no", "clo"])
            text_idx = self._column_index(header, ["course learning outcome", "learning outcome", "outcome"])
            plo_indices = self._column_indices(header, ["plo"])
            bt_idx = self._column_index(header, ["bt", "bloom", "cognitive"])

            for row in data_rows:
                row_text = " | ".join(row)
                code_source = row[code_idx] if code_idx is not None and code_idx < len(row) else row_text
                code = self._extract_code(code_source) or self._extract_code(row_text)
                if not code:
                    continue

                if text_idx is not None and text_idx < len(row):
                    clo_text_raw = row[text_idx]
                elif code_idx is not None and len(row) > code_idx + 1:
                    clo_text_raw = row[code_idx + 1]
                elif len(row) > 1:
                    clo_text_raw = row[1]
                else:
                    clo_text_raw = row_text

                merged_multi_clo = len(list(self._CLO_RE.finditer(clo_text_raw or ""))) > 1
                clo_text_raw = self._segment_text_for_code(clo_text_raw, code)

                clo_text = self._normalize_clo_text(clo_text_raw, code)
                if not clo_text:
                    continue
                if self._extract_code(clo_text):
                    clo_text = self._normalize_clo_text(self._segment_text_for_code(clo_text, code), code)
                if self._extract_code(clo_text):
                    continue

                plo_values = []
                if plo_indices:
                    seen_plo = set()
                    for pidx in plo_indices:
                        if pidx >= len(row):
                            continue
                        prefix = self._plo_prefix_for_header(header[pidx] if pidx < len(header) else "")
                        cell_plos = self._extract_plos(row[pidx], allow_numeric=True, prefix=prefix)
                        for value in cell_plos:
                            if value not in seen_plo:
                                seen_plo.add(value)
                                plo_values.append(value)
                if not plo_values:
                    plo_values = self._extract_plos(row_text)
                if merged_multi_clo and len(plo_values) > 1:
                    plo_values = [plo_values[0]]
                bt_source = row[bt_idx] if bt_idx is not None and bt_idx < len(row) else row_text

                record = {
                    "code": code,
                    "text": clo_text,
                    "bloom": self._extract_bt(bt_source),
                    "mapped_plos": plo_values,
                }

                existing = clos_by_code.get(code)
                if not existing or self._record_score(record) > self._record_score(existing):
                    clos_by_code[code] = record

        return list(clos_by_code.values())

    def _extract_from_lines(self, text):
        clos_by_code = {}
        lines = [self._clean_cell(line) for line in (text or "").splitlines() if line.strip()]

        i = 0
        while i < len(lines):
            line = lines[i]
            code = self._extract_code(line)
            if not code:
                i += 1
                continue

            desc = re.sub(r"\bCLO\s*[-:]?\s*\d+\b\s*[:\-.]?\s*", "", line, flags=re.IGNORECASE).strip()

            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if self._extract_code(nxt):
                    break
                if self._PLO_RE.search(nxt) or self._BT_RE.search(nxt):
                    break
                if len(nxt) < 4:
                    break
                desc = f"{desc} {nxt}".strip()
                if len(desc) > 500:
                    break
                j += 1

            evidence_window = " ".join(lines[i : min(i + 4, len(lines))])
            record = {
                "code": code,
                "text": self._normalize_clo_text(desc, code),
                "bloom": self._extract_bt(evidence_window),
                "mapped_plos": self._extract_plos(evidence_window),
            }

            if record["text"]:
                existing = clos_by_code.get(code)
                if not existing or self._record_score(record) > self._record_score(existing):
                    clos_by_code[code] = record

            i = j

        return list(clos_by_code.values())

    def _sort_clos(self, clos):
        def sort_key(item):
            m = self._CLO_RE.search(item.get("code", ""))
            return int(m.group(1)) if m else 10 ** 9

        return sorted(clos, key=sort_key)

    def extract(self):
        # Deterministic extraction from full parsed text: no LLM, no guessing.
        text_content = extract_text_from_file(self.file_obj, self.filename, only_clo_relevant=False)
        if not text_content:
            raise Exception("Could not read any text from the file.")

        clos = self._extract_from_tables(text_content)
        if not clos:
            clos = self._extract_from_lines(text_content)

        result = []
        for clo in self._sort_clos(clos):
            result.append(
                {
                    "code": clo.get("code", ""),
                    "text": clo.get("text", ""),
                    "bloom": clo.get("bloom", ""),
                    "mapped_plos": clo.get("mapped_plos", []),
                }
            )

        print(f"DEBUG: Deterministic extractor found {len(result)} CLOs")
        return result
