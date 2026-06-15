import os
import requests

# -----------------------------
# CONFIGURATION
# -----------------------------
SAVE_ROOT = r"C:\Users\skatb\Desktop\dev\research-data"
TICKERS = ["MSFT", "GOOG", "AMZN"]

SEC_HEADERS = {
    "User-Agent": "YourName Contact@Email.com",
}

# Filing types we want for each company
TARGET_FORMS = ["10-K", "10-Q", "8-K"]


def get_company_cik(ticker):
    """Fetch CIK for a given ticker."""
    url = "https://www.sec.gov/files/company_tickers.json"
    data = requests.get(url, headers=SEC_HEADERS).json()

    for entry in data.values():
        if entry["ticker"].upper() == ticker.upper():
            return str(entry["cik_str"]).zfill(10)

    return None


def get_latest_filings_by_type(cik):
    """Return the most recent 10-K, 10-Q, and 8-K for this CIK."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    data = requests.get(url, headers=SEC_HEADERS).json()

    forms = data["filings"]["recent"]["form"]
    dates = data["filings"]["recent"]["filingDate"]
    accession = data["filings"]["recent"]["accessionNumber"]
    primary_docs = data["filings"]["recent"]["primaryDocument"]

    results = {}

    for form_type in TARGET_FORMS:
        for i, f in enumerate(forms):
            if f == form_type:
                results[form_type] = {
                    "form": f,
                    "date": dates[i],
                    "accession": accession[i].replace("-", ""),
                    "primary_doc": primary_docs[i],
                }
                break

    return results


def download_filing(cik, meta, ticker):
    """Download and save a filing."""
    accession = meta["accession"]
    primary_doc = meta["primary_doc"]

    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{primary_doc}"
    response = requests.get(url, headers=SEC_HEADERS)

    if response.status_code != 200:
        print(f"Failed to download {meta['form']} for {ticker}")
        return

    save_dir = os.path.join(SAVE_ROOT, "raw", ticker)
    os.makedirs(save_dir, exist_ok=True)

    filename = f"{meta['date']}_{meta['form']}_{ticker}.txt"
    filepath = os.path.join(save_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"Saved: {filepath}")


def main():
    for ticker in TICKERS:
        print(f"\n=== Fetching filings for {ticker} ===")

        cik = get_company_cik(ticker)
        if not cik:
            print(f"Could not find CIK for {ticker}")
            continue

        filings = get_latest_filings_by_type(cik)

        for form_type in TARGET_FORMS:
            if form_type in filings:
                download_filing(cik, filings[form_type], ticker)
            else:
                print(f"No {form_type} found for {ticker}")


if __name__ == "__main__":
    main()
