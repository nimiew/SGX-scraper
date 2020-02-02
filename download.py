import os
import re
import cgi
import logging
import sys
import argparse
from tqdm import tqdm
import urllib.request
from datetime import date, datetime, timedelta

def get_WEBPXTICK_DT_url(code):
    return f"https://links.sgx.com/1.0.0/derivatives-historical/{code}/WEBPXTICK_DT.zip"

def get_TC_url(code):
    return f"https://links.sgx.com/1.0.0/derivatives-historical/{code}/TC.txt"

def assert_WEBPXTICK_DT_filename(filename):
    if filename == None:
        return False
    return re.match(r"^WEBPXTICK_DT-\d{8}.(zip|gz)$", filename)

def assert_TC_filename(filename):
    if filename == None:
        return False
    return re.match(r"^TC_\d{8}.txt$", filename)

def make_dirs():
    os.makedirs("log", exist_ok=True)
    os.makedirs("TickData_structure", exist_ok=True)
    os.makedirs("TC_structure", exist_ok=True)
    os.makedirs("WEBPXTICK_DT", exist_ok=True)
    os.makedirs("TC", exist_ok=True)

def get_date_string(filename):
    return re.findall(r"\d{8}", filename)[0]

def get_date(filename):
    date_string = get_date_string(filename)
    return datetime.strptime(date_string, "%Y%m%d").date()

def get_filename(source_url, retry_count):
    try_count = retry_count + 1
    while try_count != 0:
        try:
            try_count -= 1
            file = urllib.request.urlopen(source_url)
            content_disposition = file.info()['Content-Disposition']
            if content_disposition == None:
                return None
            _, params = cgi.parse_header(content_disposition)
            filename = params["filename"]
            return filename
        except Exception:
            if try_count == 0:
                logging.exception(f" Exception at source_url: {source_url}")
            else:
                logging.debug(f" Retrying for {try_count} times..")

def download(source_url, destination_dir, filename, retry_count):
    try_count = retry_count + 1 # for original dl
    while try_count != 0:
        try:
            try_count -= 1
            destination_path = os.path.join(destination_dir, filename)
            if os.path.exists(destination_path):
                logging.debug(f" Already downloaded {destination_path}")
                return
            logging.debug(f" Source: {source_url}")
            urllib.request.urlretrieve(source_url, destination_path)
            logging.debug(f" Successfully downloaded to {destination_path}")
            return
        except Exception:
            if try_count == 0:
                logging.exception(f" Exception at source_url: {source_url}")
            else:
                logging.debug(f" Retrying for {try_count} times..")

def set_up_logging():
    logging_filepath = os.path.join("log", f"{datetime.now():%Y%m%d_%H%M%S}.log")
    open(logging_filepath, 'a').close()
    logging.basicConfig(filename=logging_filepath,
                        level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def write_to_mapping(lines):
    logging.info(" writing to file..")
    with open("mapping.txt", 'a') as f:
        for line in lines:
            f.write(line)

def update_code_to_date_mapping(retry_count, max_countdown): # assume they come in a pair for a code
    if not os.path.exists("mapping.txt"):
        open("mapping.txt", 'a').close()
    with open("mapping.txt") as f:
        lines = [x.strip() for x in f.readlines()]
        lines = [x for x in lines if len(x) > 0]
    if len(lines) != 0:
        code = int(lines[-1].split(" ")[0]) + 1
    else:
        code = 1
    countdown = max_countdown
    write_lines = []
    while countdown != 0:
        logging.debug(f" countdown: {countdown}")
        countdown -= 1
        WEBPXTICK_DT_url = get_WEBPXTICK_DT_url(code)
        TC_url = get_TC_url(code)
        WEBPXTICK_DT_filename = get_filename(WEBPXTICK_DT_url, retry_count)
        TC_filename = get_filename(TC_url, retry_count)
        while WEBPXTICK_DT_filename != None or TC_filename != None:
            countdown = max_countdown
            logging.debug(f" {WEBPXTICK_DT_url}")
            logging.debug(f" {WEBPXTICK_DT_filename}")
            logging.debug(f" {TC_url}")
            logging.debug(f" {TC_filename}")
            if assert_WEBPXTICK_DT_filename(WEBPXTICK_DT_filename) and assert_TC_filename(TC_filename):
                write_lines.append(f"{code} {WEBPXTICK_DT_filename} {TC_filename}\n")
            logging.debug(f" buffer_size = {len(write_lines)}")
            if len(write_lines) == 100:
                write_to_mapping(write_lines)
                write_lines = []
            code += 1
            WEBPXTICK_DT_url = get_WEBPXTICK_DT_url(code)
            TC_url = get_TC_url(code)
            WEBPXTICK_DT_filename = get_filename(WEBPXTICK_DT_url, retry_count)
            TC_filename = get_filename(TC_url, retry_count)
        code += 1
    write_to_mapping(write_lines)

def get_code_to_date_mapping():
    with open("mapping.txt") as f:
        lines = [x.strip() for x in f.readlines()]
        lines = [x for x in lines if len(x) > 0]
    mapping = []
    for line in lines:
        code, WEBPXTICK_DT_filename, TC_filename = line.split(" ")
        WEBPXTICK_DT_date_string = get_date_string(WEBPXTICK_DT_filename)
        TC_date_string = get_date_string(TC_filename)
        assert(WEBPXTICK_DT_date_string == TC_date_string)
        mapping.append((code, datetime.strptime(TC_date_string, "%Y%m%d").date(), WEBPXTICK_DT_filename, TC_filename))
    mapping.sort(key=lambda x: x[1])
    return mapping

def find_index(date, mapping, return_larger):
    left, right = 0, len(mapping) - 1
    while left <= right:
        mid = left + (right - left) // 2
        logging.debug(f" left: {mapping[left][1]}")
        logging.debug(f" right: {mapping[right][1]}")
        if mapping[mid][1] == date:
            break
        if mapping[mid][1] > date:
            right = mid - 1
        else:
            left = mid + 1
    if return_larger and mapping[mid][1] < date:
        mid = min(mid + 1, len(mapping) - 1)
    if not return_larger and  mapping[mid][1] > date:
        mid = max(mid - 1, 0)
    return mid

def download_structures(retry_count):
    download("https://links.sgx.com/1.0.0/derivatives-historical/4182/TickData_structure.dat", "TickData_structure", "TickData_structure.dat", retry_count)
    download("https://links.sgx.com/1.0.0/derivatives-historical/4433/TC_structure.dat", "TC_structure", "TC_structure.dat", retry_count)

def download_all(document_type, mapping, first_index, last_index, last, retry_count):
    download_structures(retry_count)

    first_index = max(first_index, last_index - last + 1) # account for last
    for i in tqdm(range(last_index, first_index-1, -1)):
        WEBPXTICK_DT_filename = mapping[i][2]
        TC_filename = mapping[i][3]
        code = mapping[i][0]
        WEBPXTICK_DT_url = get_WEBPXTICK_DT_url(code)
        TC_url = get_TC_url(code)
        
        if document_type == "WEBPXTICK_DT":
            download(WEBPXTICK_DT_url, "WEBPXTICK_DT", WEBPXTICK_DT_filename, retry_count)
        elif document_type == "TC":
            download(TC_url, "TC", TC_filename, retry_count)
        else:
            download(WEBPXTICK_DT_url, "WEBPXTICK_DT", WEBPXTICK_DT_filename, retry_count)
            download(TC_url, "TC", TC_filename, retry_count)
    return last_index - first_index + 1

def get_arguments(args):
    logging.debug(args)
    parser = argparse.ArgumentParser(description="Download SGX data")
    parser.add_argument('-t', '--type', default='all', choices=['all', 'WEBPXTICK_DT', 'TC'], help="Choose to download only TC or only WEBPXTICK_DT or both")
    parser.add_argument('-ad', '--after_date', required=False, help="Download data including and after this date, format: YYYYMMDD")
    parser.add_argument('-bd', '--before_date', required=False, help="Download data including and before this date, format: YYYYMMDD")
    parser.add_argument('-l', '--last', required=False, type=int, help="Download latest x documents")
    parser.add_argument('-r', '--retry_count', default=3, type=int, help="Number of times to retry if download fails")
    parser.add_argument('-c', '--countdown', default=5, type=int, help="Number of consecutive urls to try before concluding max_code reached.\
                                                                        Important for updating mapping. Use a large value such as 100 if\
                                                                        re-generating the entire mapping and a small value if updating")
    args = parser.parse_args(args)

    if args.last != None:
        if args.last <= 0:
            parser.error("last must be > 0")
        if args.after_date != None or args.before_date != None:
            parser.error("Either use last or (after_date and before_date) but not both")

    if args.after_date == None:
        after_date = datetime.strptime("19000101", "%Y%m%d").date()
    else:
        try:
            after_date = datetime.strptime(args.after_date, "%Y%m%d").date()
        except Exception:
            parser.error("after_date format must be YYYYMMDD")

    if args.before_date == None:
        before_date = date.today()
    else:
        try:
            before_date = datetime.strptime(args.before_date, "%Y%m%d").date()
        except Exception:
            parser.error("before_date format must be YYYYMMDD")
    
    if before_date < after_date:
        parser.error("before_date must be equal to or after after_date")

    if args.retry_count < 0:
        parser.error("retry_count must be >= 0")

    if args.countdown <= 0:
        parser.error("countdown must be > 0")
    return args.type, after_date, before_date, args.last, args.retry_count, args.countdown

def main():
    make_dirs()
    set_up_logging()
    document_type, after_date, before_date, last, retry_count, countdown = get_arguments(sys.argv[1:])
    logging.info(" Updating code_to_date_mapping..")
    update_code_to_date_mapping(retry_count, countdown)
    mapping = get_code_to_date_mapping()
    first_index = find_index(after_date, mapping, return_larger=False)
    last_index = find_index(before_date, mapping, return_larger=True)
    logging.info(f" Type of documents to download: {document_type}")
    if last == None:
        last = last_index
        logging.info(f" Downloading data between {after_date} and {before_date}")
    else:
        if last > last_index:
            logging.error(f" last must be < max_index ({last_index})")
        logging.info(f" Downloading data from the last {last} days")
    logging.info(f" Retry count: {retry_count}")    
    count = download_all(document_type, mapping, first_index, last_index, last, retry_count)
    logging.info(f" COMPLETED: {count} days of data obtained")

if __name__ == "__main__":
    main()