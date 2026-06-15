import os
import re

SAVE_ROOT = r"C:\Users\skatb\Desktop\dev\research-data"
RAW_DIR = os.path.join(SAVE_ROOT, "raw")
PROCESSED_DIR = os.path.join(SAVE_ROOT, "processed")

TICKERS = ["MSFT", "GOOG", "AMZN"]


def read_file(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def write_file(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def basic_clean(text):
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Remove multiple spaces
    text = re.sub(r"[ \t]+", " ", text)
    # Normalize newlines
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def collapse_text(text):
    # Collapse to single line-ish text
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_section(text, patterns, next_patterns=None):
    """
    Hybrid section finder:
    - patterns: list of regexes for start
    - next_patterns: list of regexes for where the next section begins
    """
    start_idx = None
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            start_idx = m.start()
            break

    if start_idx is None:
        return None

    if not next_patterns:
        return text[start_idx:].strip()

    end_idx = None
    for pat in next_patterns:
        m = re.search(pat, text[start_idx + 1 :], flags=re.IGNORECASE)
        if m:
            end_idx = start_idx + 1 + m.start()
            break

    if end_idx is None:
        return text[start_idx:].strip()
    else:
        return text[start_idx:end_idx].strip()


def extract_10k_sections(text):
    sections = {}

    # Strict + flexible patterns
    item1 = [r"ITEM\s+1[^A].{0,40}BUSINESS", r"\bBusiness\b"]
    item1a = [r"ITEM\s+1A\.?\s+RISK\s+FACTORS", r"\bRisk\s+Factors\b"]
    item7 = [r"ITEM\s+7\.?\s+MANAGEMENT.?DISCUSSION", r"\bMD&A\b", r"Management.?s\s+Discussion"]
    item8 = [r"ITEM\s+8\.?\s+FINANCIAL\s+STATEMENTS", r"\bFinancial\s+Statements\b"]
    item9a = [r"ITEM\s+9A\.?\s+CONTROLS", r"\bControls\s+and\s+Procedures\b"]

    # Next-section anchors (rough)
    next_items = [r"ITEM\s+1A", r"ITEM\s+7", r"ITEM\s+8", r"ITEM\s+9A", r"ITEM\s+10"]

    sections["business"] = find_section(text, item1, next_items)
    sections["risk_factors"] = find_section(text, item1a, [r"ITEM\s+1B", r"ITEM\s+2", r"ITEM\s+7"])
    sections["mdna"] = find_section(text, item7, [r"ITEM\s+7A", r"ITEM\s+8"])
    sections["financials"] = find_section(text, item8, [r"ITEM\s+9", r"ITEM\s+9A"])
    sections["controls"] = find_section(text, item9a, [r"ITEM\s+10", r"ITEM\s+11"])

    return sections


def extract_10q_sections(text):
    sections = {}

    item1 = [r"ITEM\s+1\.?\s+FINANCIAL\s+STATEMENTS", r"\bFinancial\s+Statements\b"]
    item2 = [r"ITEM\s+2\.?\s+MANAGEMENT.?DISCUSSION", r"\bMD&A\b", r"Management.?s\s+Discussion"]
    item1a = [r"ITEM\s+1A\.?\s+RISK\s+FACTORS", r"\bRisk\s+Factors\b"]
    item4 = [r"ITEM\s+4\.?\s+CONTROLS", r"\bControls\s+and\s+Procedures\b"]

    sections["financials"] = find_section(text, item1, [r"ITEM\s+2", r"ITEM\s+3"])
    sections["mdna"] = find_section(text, item2, [r"ITEM\s+3", r"ITEM\s+4"])
    sections["risk_factors"] = find_section(text, item1a, [r"ITEM\s+2", r"ITEM\s+3", r"ITEM\s+4"])
    sections["controls"] = find_section(text, item4, [r"ITEM\s+5", r"ITEM\s+6"])

    return sections


def extract_8k_sections(text):
    sections = {}

    item202 = [r"ITEM\s+2\.02", r"\bResults\s+of\s+Operations\b", r"\bEarnings\b"]
    item701 = [r"ITEM\s+7\.01", r"\bRegulation\s+FD\b"]
    item801 = [r"ITEM\s+8\.01", r"\bOther\s+Events\b"]

    sections["earnings"] = find_section(text, item202, [r"ITEM\s+7\.01", r"ITEM\s+8\.01"])
    sections["regfd"] = find_section(text, item701, [r"ITEM\s+8\.01", r"ITEM\s+9\.01"])
    sections["other_events"] = find_section(text, item801, [r"ITEM\s+9\.01", r"SIGNATURES"])

    return sections


def process_single_filing(ticker, filename):
    raw_path = os.path.join(RAW_DIR, ticker, filename)
    text = read_file(raw_path)

    cleaned = basic_clean(text)
    collapsed = collapse_text(cleaned)

    base_name = os.path.splitext(filename)[0]
    processed_dir = os.path.join(PROCESSED_DIR, ticker)

    # Save cleaned full + collapsed
    cleaned_path = os.path.join(processed_dir, f"{base_name}_cleaned.txt")
    collapsed_path = os.path.join(processed_dir, f"{base_name}_collapsed.txt")

    write_file(cleaned_path, cleaned)
    write_file(collapsed_path, collapsed)

    # Decide type by filename
    lower_name = filename.lower()
    sections = {}

    if "10-k" in lower_name:
        sections = extract_10k_sections(cleaned)
    elif "10-q" in lower_name:
        sections = extract_10q_sections(cleaned)
    elif "8-k" in lower_name:
        sections = extract_8k_sections(cleaned)

    # Save sections
    for key, sec_text in sections.items():
        if not sec_text:
            continue
        sec_path = os.path.join(processed_dir, f"{base_name}_section_{key}.txt")
        write_file(sec_path, sec_text)


def main():
    for ticker in TICKERS:
        raw_ticker_dir = os.path.join(RAW_DIR, ticker)
        if not os.path.isdir(raw_ticker_dir):
            print(f"No raw dir for {ticker}")
            continue

        for fname in os.listdir(raw_ticker_dir):
            if not fname.lower().endswith(".txt"):
                continue
            print(f"Processing {ticker} - {fname}")
            process_single_filing(ticker, fname)


if __name__ == "__main__":
    main()
