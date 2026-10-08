import csv
import json

from datetime import datetime
from scipy.stats import mannwhitneyu, wilcoxon

def conclusion_string(p_value, alpha=0.05) -> str:
    # return (
    #     "Reject Null Hypothesis (There is a significant difference between the two samples.)"
    #     if p_value < alpha
    #     else "Do Not Reject Null Hypothesis (There is NO significant difference between the two samples.)"
    # )
    return (
        "stat-sig"
        if p_value < alpha
        else "noise"
    )

start_time = datetime.now()

input_file = "testing/results.tsv"
output_file = "testing/deterministic_metrics.tsv"
scorecard_file = "testing/scorecard.tsv"

modified_rows = []

with open(input_file, mode='r', encoding='utf-8', newline='') as infile:
    reader = csv.reader(infile, delimiter='\t')
    
    header = next(reader)
    header.append("missing_urls_control")
    header.append("missing_urls_treatment")
    header.append("number_missing_urls_control")
    header.append("number_missing_urls_treatment")
    header.append("missing_providers_control")
    header.append("missing_providers_treatment")
    header.append("number_missing_providers_control")
    header.append("number_missing_providers_treatment")
    modified_rows.append(header)

    control_missing_url_counts = []
    treatment_missing_url_counts = []
    control_missing_provider_counts = []
    treatment_missing_provider_counts = []

    for row in reader:
        control_result = row[3]
        control_result_lower = control_result.lower()
        treatment_result = row[4]
        treatment_result_lower = treatment_result.lower()

        missing_urls_control = []
        missing_urls_treatment = []
        num_missing_control = 0
        num_missing_treatment = 0
        expected_urls = json.loads(row[1])
        for url in expected_urls:
          if url not in control_result_lower:
              missing_urls_control.append(url)
              num_missing_control += 1
          if url not in treatment_result_lower:
              missing_urls_treatment.append(url)
              num_missing_treatment += 1
        row.append(missing_urls_control)
        row.append(missing_urls_treatment)
        row.append(num_missing_control)
        row.append(num_missing_treatment)
        control_missing_url_counts.append(num_missing_control)
        treatment_missing_url_counts.append(num_missing_treatment)

        missing_providers_control = []
        missing_providers_treatment = []
        num_missing_control = 0
        num_missing_treatment = 0
        expected_providers = json.loads(row[2])
        for provider in expected_providers:
            if provider not in control_result_lower:
                missing_providers_control.append(provider)
                num_missing_control += 1
            if provider not in treatment_result_lower:
                missing_providers_treatment.append(provider)
                num_missing_treatment += 1
        row.append(missing_providers_control)
        row.append(missing_providers_treatment)
        row.append(num_missing_control)
        row.append(num_missing_treatment)
        control_missing_provider_counts.append(num_missing_control)
        treatment_missing_provider_counts.append(num_missing_treatment)

        modified_rows.append(row)
        print("!!! row completed !!!")
        print(f"!!! row = {row} !!!")
        print(f"!!! elapsed time = {datetime.now() - start_time} !!!")

    

with open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
    writer = csv.writer(outfile, delimiter='\t')
    writer.writerows(modified_rows)

with open(scorecard_file, mode='w', encoding='utf-8', newline='') as scorefile:
    writer = csv.writer(scorefile, delimiter='\t')
    rows = [["metric", "stat", "p-value", "conclusion"]]

    # missing_urls
    stat, p_value = wilcoxon(control_missing_url_counts, treatment_missing_url_counts)
    conclusion = conclusion_string(p_value)
    rows.append(["missing_urls_wilcoxon", stat, p_value, conclusion])

    stat, p_value = wilcoxon(control_missing_url_counts, treatment_missing_url_counts, alternative="less")
    conclusion = conclusion_string(p_value)
    rows.append(["missing_urls_wilcoxon_less", stat, p_value, conclusion])

    stat, p_value = wilcoxon(control_missing_url_counts, treatment_missing_url_counts, alternative="greater")
    conclusion = conclusion_string(p_value)
    rows.append(["missing_urls_wilcoxon_greater", stat, p_value, conclusion])

    stat, p_value = mannwhitneyu(control_missing_url_counts, treatment_missing_url_counts)
    conclusion = conclusion_string(p_value)
    rows.append(["missing_urls_mannwhitneyu", stat, p_value, conclusion])

    stat, p_value = mannwhitneyu(control_missing_url_counts, treatment_missing_url_counts, alternative="less")
    conclusion = conclusion_string(p_value)
    rows.append(["missing_urls_mannwhitneyu_less", stat, p_value, conclusion])

    stat, p_value = mannwhitneyu(control_missing_url_counts, treatment_missing_url_counts, alternative="greater")
    conclusion = conclusion_string(p_value)
    rows.append(["missing_urls_mannwhitneyu_greater", stat, p_value, conclusion])

    # missing_providers
    stat, p_value = wilcoxon(control_missing_provider_counts, treatment_missing_provider_counts)
    conclusion = conclusion_string(p_value)
    rows.append(["missing_providers_wilcoxon", stat, p_value, conclusion])

    stat, p_value = wilcoxon(control_missing_provider_counts, treatment_missing_provider_counts, alternative="less")
    conclusion = conclusion_string(p_value)
    rows.append(["missing_providers_wilcoxon_less", stat, p_value, conclusion])

    stat, p_value = wilcoxon(control_missing_provider_counts, treatment_missing_provider_counts, alternative="greater")
    conclusion = conclusion_string(p_value)
    rows.append(["missing_providers_wilcoxon_greater", stat, p_value, conclusion])
    
    stat, p_value = mannwhitneyu(control_missing_provider_counts, treatment_missing_provider_counts)
    conclusion = conclusion_string(p_value)
    rows.append(["missing_providers_mannwhitneyu", stat, p_value, conclusion])

    stat, p_value = mannwhitneyu(control_missing_provider_counts, treatment_missing_provider_counts, alternative="less")
    conclusion = conclusion_string(p_value)
    rows.append(["missing_providers_mannwhitneyu_less", stat, p_value, conclusion])

    stat, p_value = mannwhitneyu(control_missing_provider_counts, treatment_missing_provider_counts, alternative="greater")
    conclusion = conclusion_string(p_value)
    rows.append(["missing_providers_mannwhitneyu_greater", stat, p_value, conclusion])

    writer.writerows(rows)


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