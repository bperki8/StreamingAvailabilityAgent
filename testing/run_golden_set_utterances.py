import streaming_availability
import csv

from datetime import datetime

start_time = datetime.now()

input_file = "testing/golden_set.tsv"
output_file = "testing/results.tsv"

modified_rows = []

with open(input_file, mode='r', encoding='utf-8', newline='') as infile:
    reader = csv.reader(infile, delimiter='\t')
    
    header = next(reader)
    header.append("grounded")
    header.append("ungrounded")
    modified_rows.append(header)
    
    for row in reader:
        user_utterance = row[0]

        # TODO: Could run these two in parallel to save time.
        arguments = ["--utterance", user_utterance ]
        grounded_result = streaming_availability.main(arguments)
        arguments.append("-d")
        non_grounded_result = streaming_availability.main(arguments)

        row.append(grounded_result[-1]["content"].encode())
        row.append(non_grounded_result[-1]["content"].encode())

        modified_rows.append(row)
        print("!!! row completed !!!")
        print(f"!!! elapsed time = {datetime.now() - start_time} !!!")

with open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
    writer = csv.writer(outfile, delimiter='\t')
    writer.writerows(modified_rows)

end_time = datetime.now()
print(f"!!! start time = {start_time} !!!")
print(f"!!! end time = {end_time} !!!")
print(f"!!! elapsed time = {end_time - start_time}")

# TODO: Enable this when run in verbose mode?
with open(output_file, mode='r', encoding='utf-8', newline='') as outfile:
    reader = csv.reader(outfile, delimiter='\t')
    print("!!! output file formatting !!!")
    for row in reader:
        print("!!! here's a row, bit by bit !!!")
        for item in row:
            print(item)