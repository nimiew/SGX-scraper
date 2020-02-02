Tested on Python 3.7.5

To download dependencies (using conda):
1.	conda create -n SGX --file requirements.txt -c conda-forge
2.	conda activate SGX
3.	Run the scripts

Explanation of design:

1.	Obtaining the mapping from code to filenames\
Code refers to XXXX in https://links.sgx.com/1.0.0/derivatives-historical/XXXX/WEBPXTICK_DT.zip or https://links.sgx.com/1.0.0/derivatives-historical/XXXX/TC.txt \
When the script first starts, it updates mapping.txt. Mapping.txt maps valid codes to their filenames (this indirectly maps to date as we can obtain date from filename). A mapping is valid if the url is valid and gives a valid WEBPXTICK_DT filename and TC filename. Refer to the functions - assert_WEBPXTICK_DT_filename and assert_TC_filename.\
This step is useful and important because obtaining the filename can be expensive (need to make a request to server). Storing the filename makes it easy to check for its existence (so no need to re-download).\
Each time the script starts, it updates mapping.txt to latest version.

2.	Arguments\
'-t', '--type', choices=['all', 'WEBPXTICK_DT', 'TC'] - "Choose to download only TC or only WEBPXTICK_DT or both")\
'-ad', '--after_date' - "Download data including and after this date, format: YYYYMMDD")\
'-bd', '--before_date' - "Download data including and before this date, format: YYYYMMDD")\
'-l', '--last' - "Download latest x documents")\
'-r', '--retry_count' - "Number of times to retry if download fails")\
'-c', '--cooldown' - "Number of consecutive urls to try before concluding max_code reached. Important for updating mapping. Use a large value such as 100 if re-generating the entire mapping and a small value if updating"

The user has 2 modes of operation in general - download latest x documents or download within after_date and before_date, both inclusive. Retry_count is the number of time to retry request to server if error occurs.\
Example usages:\
python download.py  # Use sensible defaults\
python download.py -ad 20170204 -bd 20180306 -t WEBPXTIC_DT -r 2\
python download.py -l 100

3.	Logic Flow\
mapping.txt is updated, then read into an array of tuples and sorted based on date. Each tuple is (code, date, WEBPXTICK_DT_filename, TC_filename). We use binary search to find the largest index <= after_date (denoted as first_index) and smallest index >= before_date (denoted as last_index).\
We can obtain the relevant filenames and their urls (from code) and download them or check if they are already downloaded.

4. Testing\
python -m unittest test_download.py