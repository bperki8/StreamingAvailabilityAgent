import csv
import json

from datetime import datetime

start_time = datetime.now()

input_file = "testing/results.tsv"
output_file = "testing/deterministic_metrics.tsv"

modified_rows = []

with open(input_file, mode='r', encoding='utf-8', newline='') as infile:
    reader = csv.reader(infile, delimiter='\t')
    
    header = next(reader)
    header.append("missing_urls_grounded")
    header.append("missing_urls_ungrounded")
    header.append("missing_providers_grounded")
    header.append("missing_providers_ungrounded")
    modified_rows.append(header)
    
    for row in reader:
        grounded_result = row[3]
        grounded_result_lower = grounded_result.lower()
        ungrounded_result = row[4]
        ungrounded_result_lower = ungrounded_result.lower()

        missing_urls_grounded = []
        missing_urls_ungrounded = []
        expected_urls = json.loads(row[1])
        for url in expected_urls:
          if url not in grounded_result_lower:
              missing_urls_grounded.append(url)
          if url not in ungrounded_result_lower:
              missing_urls_ungrounded.append(url)
        row.append(missing_urls_grounded)
        row.append(missing_urls_ungrounded)

        missing_providers_grounded = []
        missing_providers_ungrounded = []
        expected_providers = json.loads(row[2])
        for provider in expected_providers:
            print(f"!!! checking provider {provider} !!!")
            if provider not in grounded_result_lower:
                missing_providers_grounded.append(provider)
            if provider not in ungrounded_result_lower:
                missing_providers_ungrounded.append(provider)
        row.append(missing_providers_grounded)
        row.append(missing_providers_ungrounded)

        modified_rows.append(row)
        print("!!! row completed !!!")
        print(f"!!! row = {row} !!!")
        print(f"!!! elapsed time = {datetime.now() - start_time} !!!")

with open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
    writer = csv.writer(outfile, delimiter='\t')
    writer.writerows(modified_rows)

end_time = datetime.now()
print(f"!!! start time = {start_time} !!!")
print(f"!!! end time = {end_time} !!!")
print(f"!!! elapsed time = {end_time - start_time}")

# TODO: Enable this when run in verbose mode?
# with open(output_file, mode='r', encoding='utf-8', newline='') as outfile:
#     reader = csv.reader(outfile, delimiter='\t')
#     print("!!! output file formatting !!!")
#     for row in reader:
#         print("!!! here's a row, bit by bit !!!")
#         for item in row:
#             print(item)