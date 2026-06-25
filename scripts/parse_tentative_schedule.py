#!/usr/bin/env python3
"""
解析 Q2 2026 Tentative Auction Schedule PDF，生成 May 2026 计划日程 CSV
"""
import pdfplumber
import csv
import re
import os
from datetime import datetime

PDF_PATH = "tentative_q2_2026.pdf"
OUTPUT_CSV = "may2026_tentative_schedule.csv"

def main():
    plans = []
    
    with pdfplumber.open(PDF_PATH) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"\n{'='*60}")
            print(f"📄 Page {page_num}")
            print(f"{'='*60}")
            
            # Extract all tables
            tables = page.extract_tables()
            text = page.extract_text()
            
            print("Raw text:")
            print(text[:3000] if text else "(no text)")
            
            if tables:
                for ti, table in enumerate(tables):
                    print(f"\n--- Table {ti+1} ---")
                    for row in table:
                        print(" | ".join([str(c) if c else "" for c in row]))
                        
                        # Try to parse rows as auction entries
                        row_text = " ".join([str(c) for c in row if c])
                        # Look for date patterns and security types
                        if re.search(r'\d{1,2}/\d{1,2}/\d{4}', row_text):
                            # Check if it mentions security type
                            types = []
                            for st in ["BILL", "NOTE", "BOND", "TIPS", "FRN", "CMB",
                                       "4-Week", "8-Week", "13-Week", "17-Week", "26-Week", "52-Week",
                                       "2-Year", "3-Year", "5-Year", "7-Year", "10-Year", "20-Year", "30-Year"]:
                                if st.lower() in row_text.lower():
                                    types.append(st)
                            
                            # Extract dates
                            dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', row_text)
                            if dates and types:
                                plans.append({
                                    "dates": " / ".join(dates),
                                    "types": ", ".join(types),
                                    "raw": row_text
                                })
            
            # For text that didn't end up in tables, try extracting manually
            if text:
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    # Look for lines with date pattern and security type
                    if re.search(r'\d{1,2}/\d{1,2}/\d{2,4}', line):
                        # Check for security type keywords
                        for st in ["Bill", "Note", "Bond", "TIPS", "FRN", "CMB",
                                   "4-Week", "8-Week", "13-Week", "17-Week", "26-Week",
                                   "2-Year", "3-Year", "5-Year", "7-Year", "10-Year", "20-Year", "30-Year"]:
                            if st.lower() in line.lower():
                                plans.append({
                                    "dates": "",
                                    "types": st,
                                    "raw": line
                                })
    
    # Output parsed plans
    print(f"\n\n{'='*60}")
    print(f"📋 Parsed {len(plans)} potential auction entries")
    print(f"{'='*60}")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, OUTPUT_CSV)
    
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["rows"])
        for p in plans:
            writer.writerow([p["raw"]])
    
    print(f"Raw data saved to: {csv_path}")
    
    # Also print all the raw text for manual inspection
    with pdfplumber.open(PDF_PATH) as pdf:
        all_text = []
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                all_text.append(t)
        
        full_text = "\n".join(all_text)
        txt_path = os.path.join(script_dir, "tentative_full_text.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"Full text saved to: {txt_path}")

if __name__ == "__main__":
    main()
