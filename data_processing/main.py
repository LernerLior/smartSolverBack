from crawler import *

if __name__ == "__main__":
    target_company = "santander"
    collect_complaints(target_company, complaint_number=6, wait_seconds=10)