import re
import pdfplumber

# ==========================================
# 1. DOMAIN DICTIONARY (C1-C6, P1-P7, A1-A5)
# ==========================================
DOMAIN_KEYWORDS = {
    # COGNITIVE
    "C1": ["define", "identify", "describe", "label", "list", "name", "state", "match", "recognize", "select", "examine", "locate", "memorize", "quote", "recall", "reproduce", "tabulate", "tell", "copy", "discover", "duplicate", "enumerate", "listen", "observe", "omit", "read", "recite", "record", "repeat", "retell", "visualize", "knowledge"],
    "C2": ["explain", "describe", "interpret", "paraphrase", "summarize", "classify", "compare", "differentiate", "discuss", "distinguish", "extend", "predict", "associate", "contrast", "convert", "demonstrate", "estimate", "express", "identify", "indicate", "infer", "relate", "restate", "select", "translate", "ask", "cite", "discover", "generalize", "group", "illustrate", "judge", "observe", "order", "report", "represent", "research", "review", "rewrite", "show", "trace", "comprehension", "understand"],
    "C3": ["solve", "apply", "illustrate", "modify", "use", "calculate", "change", "choose", "demonstrate", "discover", "experiment", "relate", "show", "sketch", "complete", "construct", "dramatize", "interpret", "manipulate", "paint", "prepare", "teach", "act", "collect", "compute", "explain", "list", "operate", "practice", "simulate", "transfer", "write", "application"],
    "C4": ["analyze", "compare", "classify", "contrast", "distinguish", "infer", "separate", "explain", "select", "categorize", "connect", "differentiate", "divide", "order", "prioritize", "survey", "calculate", "conclude", "correlate", "deduce", "devise", "diagram", "dissect", "estimate", "evaluate", "experiment", "focus", "illustrate", "organize", "outline", "plan", "question", "test", "analysis"],
    "C5": ["evaluate", "criticize", "reframe", "assess", "appraise", "judge", "support", "compare", "decide", "discriminate", "recommend", "summarize", "choose", "convince", "defend", "estimate", "grade", "measure", "predict", "rank", "score", "select", "test", "argue", "conclude", "consider", "critique", "debate", "distinguish", "editorialize", "justify", "persuade", "rate", "weigh", "evaluation"],
    "C6": ["create", "design", "compose", "plan", "combine", "formulate", "invent", "hypothesize", "substitute", "write", "compile", "construct", "develop", "generalize", "integrate", "modify", "organize", "prepare", "produce", "rearrange", "rewrite", "adapt", "anticipate", "arrange", "assemble", "choose", "collaborate", "facilitate", "imagine", "intervene", "make", "manage", "originate", "propose", "simulate", "solve", "support", "test", "validate", "synthesis"],
    
    # PSYCHOMOTOR
    "P1": ["perceive", "detect", "listen", "observe"], "P2": ["set", "start", "begin", "display", "show"],
    "P3": ["imitate", "copy", "trace", "follow"], "P4": ["manipulate", "perform", "execute", "construct"],
    "P5": ["articulate", "adapt", "alter", "change"], "P6": ["naturalize", "design", "specify", "manage"],
    "P7": ["originate", "create", "compose", "construct"],
    
    # AFFECTIVE
    "A1": ["receive", "ask", "choose", "listen"], "A2": ["respond", "answer", "assist", "participate"],
    "A3": ["value", "complete", "demonstrate", "differentiate", "justify"],
    "A4": ["organize", "adhere", "alter", "arrange", "formulate"],
    "A5": ["characterize", "act", "discriminate", "display", "influence"]
}

def clean_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', str(text)).strip()

def detect_bt_level(text, explicit_level=None):
    # 1. Check Explicit Column (Priority)
    if explicit_level:
        match = re.search(r'([CPA][-\s]?\d)', str(explicit_level), re.IGNORECASE)
        if match:
            return match.group(1).upper().replace("-", "").replace(" ", "")
    
    # 2. Check Text Keywords
    words = re.findall(r'\b\w+\b', text.lower())
    for word in words:
        for level, keywords in DOMAIN_KEYWORDS.items():
            if word in keywords:
                return level
    return None

def extract_plos_from_string(text):
    matches = re.findall(r'(?:PLO|PO|SO)[-\s]?(\d+)', str(text), re.IGNORECASE)
    return [f"PLO-{m}" for m in matches]

class OBECourseExtractor:
    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.clos = {}     
        self.mappings = {} 

    def extract(self):
        try:
            print(f"DEBUG: Starting extraction for {self.file_obj}")
            with pdfplumber.open(self.file_obj) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += (page.extract_text() or "") + "\n"
                    tables = page.extract_tables()
                    for table in tables:
                        self._analyze_and_process_table(table)
                
                # Fallback: If tables failed, scan raw text
                if not self.clos:
                    print("DEBUG: No CLOs from tables. Trying text fallback.")
                    self._process_raw_text(full_text)
                
            return self._finalize_data()
        except Exception as e:
            print(f"DEBUG: Extractor Error: {e}")
            return []

    def _analyze_and_process_table(self, table):
        """
        Smartly determines if a table is a CLO table by checking DATA patterns, not just headers.
        """
        if not table or len(table) < 2: return
        
        # 1. Check for Transposed Mapping Table (Special Case for CP Outline)
        # Check Row 0 headers for "CLO 1", "CLO 2"
        headers = [str(h).lower() for h in table[0] if h]
        if any(re.search(r'clo[-\s]?\d', h) for h in headers):
            self._process_transposed_mapping(table, headers)
            return

        # 2. Score Columns based on CONTENT (ignoring headers)
        col_scores = {
            "code": -1, # "CLO-1"
            "bt": -1,   # "C-2", "C4"
            "text": -1, # Long text
            "plo": -1   # "PLO-1", "1", "2"
        }
        
        # Analyze first 5 rows to guess column types
        num_cols = len(table[0])
        # Track matches per column index
        col_matches = {i: {"bt": 0, "code": 0, "plo": 0, "text_len": 0} for i in range(num_cols)}
        
        row_count = 0
        for row in table:
            # Skip empty or header-like rows
            if not row or all(c is None for c in row): continue
            
            clean_row = [clean_text(c) for c in row]
            
            for idx, cell in enumerate(clean_row):
                if idx >= num_cols: continue
                
                # Check BT Pattern (C-2, P3, etc)
                if re.search(r'\b[CPA][-\s]?\d\b', cell, re.IGNORECASE):
                    col_matches[idx]["bt"] += 1
                
                # Check Code Pattern (CLO-1)
                if re.search(r'(CLO|CO|LO)[-\s]?\d+', cell, re.IGNORECASE):
                    col_matches[idx]["code"] += 1
                
                # Check PLO Pattern (Explicit or just digits in context)
                if re.search(r'(PLO|PO)[-\s]?\d+', cell, re.IGNORECASE) or (cell.isdigit() and len(cell) < 3):
                    col_matches[idx]["plo"] += 1
                
                # Check Text Length
                col_matches[idx]["text_len"] += len(cell)
            row_count += 1

        if row_count == 0: return

        # Assign Columns based on best scores
        for idx, stats in col_matches.items():
            if stats["bt"] >= 1: col_scores["bt"] = idx
            if stats["code"] >= 1: col_scores["code"] = idx
            
            # PLO is valid if it has matches AND isn't the code column
            if stats["plo"] >= 1 and idx != col_scores["code"]: 
                col_scores["plo"] = idx
            
            # Text is the column with longest average length
            if stats["text_len"] / row_count > 30: # Avg chars > 30 implies description
                col_scores["text"] = idx

        # 3. Decision: Is this a CLO table?
        # Must have Text AND (Code OR BT OR PLO)
        is_clo_table = (col_scores["text"] != -1) and (
            col_scores["code"] != -1 or col_scores["bt"] != -1 or col_scores["plo"] != -1
        )

        if is_clo_table:
            self._extract_from_identified_table(table, col_scores)

    def _extract_from_identified_table(self, table, cols):
        """
        Extracts data knowing which columns are which.
        """
        generated_index = 1
        
        for row in table:
            row = [clean_text(c) for c in row]
            if not row or len(row) <= max(cols.values()): continue

            # --- 1. Get Code ---
            raw_code = ""
            if cols["code"] != -1:
                match = re.search(r'((?:CLO|CO|LO)?[-\s]?\d+)', row[cols["code"]], re.IGNORECASE)
                if match: 
                    raw_code = match.group(1).upper().replace(" ", "-")
            
            # Auto-Generate if code missing (The "Smart" part for CS330)
            # Only generate if the Text column actually has text
            if not raw_code and cols["text"] != -1 and len(row[cols["text"]]) > 10:
                raw_code = f"CLO-{generated_index}"
                generated_index += 1

            if not raw_code: continue
            
            # Normalize Code
            if not raw_code.startswith(("CLO", "CO")):
                raw_code = f"CLO-{raw_code}"

            # --- 2. Get Data ---
            text = row[cols["text"]] if cols["text"] != -1 else ""
            
            explicit_bt = row[cols["bt"]] if cols["bt"] != -1 else ""
            bt_val = detect_bt_level(text, explicit_bt)
            
            plos = []
            if cols["plo"] != -1:
                val = row[cols["plo"]]
                # Handle "1", "2" implicit PLOs
                raw_nums = re.findall(r'\b\d+\b', val)
                plos = [f"PLO-{n}" for n in raw_nums]
                plos.extend(extract_plos_from_string(val))

            # Store (Avoid overwriting with bad data)
            if raw_code not in self.clos or len(text) > len(self.clos[raw_code]["text"]):
                self.clos[raw_code] = {
                    "text": text,
                    "bloom": bt_val,
                    "plos": list(set(plos))
                }

    def _process_transposed_mapping(self, table, headers):
        # Handles CP Outline mapping (Cols = CLO 1, CLO 2)
        clo_cols = {} 
        for idx, h in enumerate(headers):
            m = re.search(r'(?:CLO|CO)[-\s]?(\d+)', h, re.IGNORECASE)
            if m: clo_cols[idx] = f"CLO-{m.group(1)}"
            
        plo_col_idx = 0 # Default to first col
        # find column with PLO numbers
        for idx, h in enumerate(headers):
            if "outcome" in h or "plo" in h or "no" in h:
                plo_col_idx = idx
                break

        for row in table[1:]:
            row = [clean_text(c) for c in row]
            if len(row) <= max(clo_cols.keys(), default=0): continue

            plo_match = re.search(r'\b\d+\b', row[plo_col_idx])
            if not plo_match: continue
            
            current_plo = f"PLO-{plo_match.group(0)}"

            for idx, clo_code in clo_cols.items():
                cell_val = row[idx].lower()
                if any(x in cell_val for x in ["x", "yes", "√", "*", "v"]):
                    if clo_code not in self.mappings: self.mappings[clo_code] = []
                    self.mappings[clo_code].append(current_plo)

    def _process_raw_text(self, text):
        lines = text.split('\n')
        for line in lines:
            match = re.search(r'((?:CLO|CO)[-\s]?\d+)[:\.\-\s]+(.+)', line, re.IGNORECASE)
            if match:
                code = match.group(1).upper().replace(" ", "-")
                if code in self.clos: continue

                content = match.group(2).strip()
                bt_match = re.search(r'[\(\[]([CPA][-\s]?\d)[\)\]]', content)
                explicit_bt = bt_match.group(1) if bt_match else None
                
                self.clos[code] = {
                    "text": re.sub(r'[\(\[].*?[\)\]]', '', content).strip(),
                    "bloom": detect_bt_level(content, explicit_bt),
                    "plos": extract_plos_from_string(content)
                }

    def _finalize_data(self):
        results = []
        all_codes = set(self.clos.keys()) | set(self.mappings.keys())
        
        for code in all_codes:
            data = self.clos.get(code, {"text": "Mapped only", "bloom": None, "plos": []})
            if code in self.mappings:
                data['plos'] = list(set(data['plos'] + self.mappings[code]))
            
            results.append({
                "code": code,
                "text": data['text'],
                "bloom": data['bloom'],
                "mapped_plos": sorted(list(set(data['plos'])))
            })
            
        def natural_keys(text):
            return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', text['code'])]
            
        return sorted(results, key=natural_keys)