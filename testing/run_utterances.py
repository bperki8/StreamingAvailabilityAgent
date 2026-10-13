import argparse
import csv
import json
import streaming_availability

from datetime import datetime

start_time = datetime.now()

parser = argparse.ArgumentParser(
    description="Simples test harness for the Streaming Availability Agent used to run multiple utterances from a .tsv file."
)

parser.add_argument("-c", "--config", type=str, help="Name of the config to use for the experiment.", default="example_experiment.json")
parser.add_argument("-d", "--dataset", type=str, help="Name of the file containging the dataset.", default="golden_set.tsv")

args = parser.parse_args()

config_name = args.config
config_file = f"testing/configs/{config_name}"
dataset_name = args.dataset
dataset_file = f"testing/datasets/{dataset_name}"
output_file = f"testing/results/{config_name[:-5]}.tsv"

modified_rows = []
control_args = []
treatment_args = []

with open(config_file, mode='r', encoding='utf-8', newline='') as configfile:
    config_data = json.load(configfile)
    control_config_overrides = config_data["control_config_overrides"]
    treatment_config_overrides = config_data["treatment_config_overrides"]
    print(f"!!! control_config_overrides = {control_config_overrides} !!!")
    print(f"!!! treatment_config_overrides = {treatment_config_overrides} !!!")
    

with open(dataset_file, mode='r', encoding='utf-8', newline='') as infile:
    reader = csv.reader(infile, delimiter='\t')
    
    header = next(reader)
    utterance_urls_providers = header[:3]
    utterance_urls_providers.append("control")
    utterance_urls_providers.append("treatment")
    modified_rows.append(utterance_urls_providers)
    
    for row in reader:
        user_utterance = row[0]

        # TODO: Could run these two in parallel to save time.
        print(f"!!! control_config_overrides = {control_config_overrides} !!!")
        control_result = streaming_availability.main(control_config_overrides, user_utterance)
        print(f"!!! treatment_config_overrides = {treatment_config_overrides} !!!")
        treatment_result = streaming_availability.main(treatment_config_overrides, user_utterance)

        utterance_urls_providers = row[:3]
        # TODO: This only takes the content of the final message right now. If we want more have to be smarter.
        utterance_urls_providers.append(control_result[-1]["content"].encode())
        utterance_urls_providers.append(treatment_result[-1]["content"].encode())

        modified_rows.append(utterance_urls_providers)
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