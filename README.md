# Streaming Availability Agent and Test Harness

A simple RAG (Retrieval-Augmented Generation) agent that uses a local llm to answer questions about where to stream movies and TV shows along with a test harness for evaluating performance. The agent itself is very simple, but the main value is in the test harness used to ensure the proper grounding of results -- which is especially important in the streaming domain where providers for a specific TV Show / Movie change often -- and in the potential LLM-powered metrics discussed in the [Future Work](#future-work) section.

# Table of Contents <!-- omit in toc -->
- [Streaming Availability Agent and Test Harness](#streaming-availability-agent-and-test-harness)
  - [Streaming Availability Agent](#streaming-availability-agent)
    - [Setup / Run](#setup--run)
    - [Agent Config](#agent-config)
  - [Test Harness](#test-harness)
    - [`run_utterances.py`](#run_utterancespy)
      - [Setup / Run](#setup--run-1)
      - [Experiment Config](#experiment-config)
      - [Dataset](#dataset)
    - [`deterministic_metrics.py`](#deterministic_metricspy)
      - [Setup / Run](#setup--run-2)
      - [Pairwise Results Structure](#pairwise-results-structure)
      - [Statistical Analysis and Scorecard Structure](#statistical-analysis-and-scorecard-structure)
- [Future Work](#future-work)

## Streaming Availability Agent

The Streaming Availability Agent uses the `qwen3:4b` local llm through `ollama`. It can be run with or without the RAG system enabled. With RAG enabled, the agent has tools available to query the TMDB (The Movie Database) API for up-to-date streaming providers.

### Setup / Run

1. Request a TMDB API Key at https://www.themoviedb.org/settings/api/request.
1. Add that to your `.env` file as shown in [.env.example](.env.example).
1. Download and install [ollama](https://ollama.com/download).
1. Run the `qwen3:4b` model locally using the command `ollama run qwen3:4b`.
1. Check that the config at [`config/agent_config.json`](config/agent_config.json) is accurate -- see [Agent Config](#agent-config) for expected values.
1. Run the agent with the command `python streaming_availability.py`.

### Agent Config

The following properties can be set in the [agent config JSON](config/agent_config.json).

- `disable_cached_data` (default `False`): By default, the model cache's API responses from TMDB instead of querying the service live. This is great for demo / testing purposes, because it keeps the source of truth pinned to a known baseline, but it should be set to `True` in production to ensure that the model is using the most up-to-date information -- streaming availability changes often.
- `disable_grounding` (default: `False`): Disables the search tools used to query the TMDB API, without which the model can only answer from its internal knowledge at training time.
- `multi_turn` (default: `False`): Allows multi-turn conversations (with more than one user input utterance) when enabled.
- `show_thinking` (default `False`): If enabled, prints the model's chain of thought when present in the outputs. (Useful for debugging.)
- `show_tool_calls` (default `False`): If enabled, prints the actual tool calls (tool name and input parameters) and results when present. (Useful for debugging.)
- `system_prompt` (default `"prompts/system_prompt_with_tools.md"`): Path to a file containing the system prompt for the streaming agent.
- `verbose` (default `False`): Enable verbose mode for debugging.

## Test Harness

The test harness consists of two python scripts: [`run_utterances.py`](testing/run_utterances.py) and [`deterministic_metrics.py`](testing/deterministic_metrics.py).

### `run_utterances.py`

[`run_utterances.py`](testing/run_utterances.py) is used to invoke the Streaming Availability Agent across a list of user utterances (in `.tsv` format) using two separate agent configs (one for control and one for treatment). The final agent responses are recorded and saved for later evaluation/comparison. (Note: We only keep the final chat response currently, but this could easily be upgraded to include tool calls and results as well.)

#### Setup / Run

1. Request a TMDB API Key at https://www.themoviedb.org/settings/api/request.
1. Add that to your `.env` file as shown in [.env.example](.env.example).
1. Download and install [ollama](https://ollama.com/download).
1. Run the `qwen3:4b` model locally using the command `ollama run qwen3:4b`.
1. Create an experiment config in `testing/configs` -- see [Experiment Config](#experiment-config) for expected format -- or use the default config in `example_experiment.json`.
1. Create a dataset in `testing/datasets` -- see [Dataset](#dataset) for expected format -- or use the default dataset in `golden_set.tsv`.
1. Run the script from the root of this repo -- and provide names for your dataset and experiment config as necessary -- by using the command `python -m testing.run_utterances -d "golden_set.tsv" -c "example_experiment.json"`
1. Results will be output to `testing/results` in a `.tsv` file named using the same name as the provided experiment config (warning: this will overwrite any existing results file with the same name).

#### Experiment Config

See [example_experiment.json](testing/configs/example_experiment.json) for an example. (Note that the optional `experiment_name` parameter is not currently used by the scripts, it's just there for bookkeeping.)

The experiment config is a JSON file with two required properties: `control_config_overrides` and `treatment_config_overrides`. Both are expected to be a JSON dictionary containing only the properties from the agent config that should be overridden compared to the default config at [`configs/agent_config.json`](config/agent_config.json). If you would like either arm (control or treatment) to use the exact default config, simply provide an empty JSON dictionary `{}`.

#### Dataset

See [golden_set.tsv](testing/datasets/golden_set.tsv) for an example.

Datasets must consist of a `.tsv` file with three columns: `utterances`, `urls`, and `expected`.

Each row of the `utterances` column should contain a single user utterance used to test both the control and treatment configs.

Each row of the `urls` column should contain a list of quoted URL strings that the model is expected to include as citations in its final response for that utterance. An empty list can be provided `[]` or a list containing one or more quoted URL strings. These are used in a sub-string match, so you should provide the shortest acceptable URL (e.g., "https://www.themoviedb.org/tv/2352-the-nanny" instead of "https://www.themoviedb.org/tv/2352-the-nanny/watch?translate=false&locale=US" unless you want to specifically ensure that the model is including the "watch?translate=false&locale=US" part in the final response).

Each row of the `expected` column should contain a list of quoted sub-strings that are expected to be found in the model's (lowercased) response. In the case of this agent, we're using it to list specific streaming providers that the model is expected to mention.

### `deterministic_metrics.py`

[`deterministic_metrics.py`](testing/deterministic_metrics.py) takes the results of a `run_utterances.py` run and, based on the expected URLs and streaming providers, calculates the number of misses for each metric and whether any differences are statistically significant.

#### Setup / Run

1. Run at least one experiment as described in [the `run_utterances.py` section](#run_utterancespy) above.
1. Run the script from the root of this repo -- and provide a name for the result file produced by step one if not the default -- using the command `python -m testing.deterministic_metrics -r "example_experiment.tsv"`.
1. Pairwise results for each utterance will be output in the `testing/results/deterministic/results` directory in a `.tsv` file named using the same name as the provided results file (warning: this will overwrite any existing results file with the same name).
1. A scorecard with cumulative results and statistical analysis will be output in the `testing/results/deterministic/scorecards` directory in a `.tsv` file named using the same name as the provided results file (warning: this will overwite any existing scorecard file with the same name).

#### Pairwise Results Structure

The pairwise results will be output in `.tsv` format. Output consists of the original results file with eight columns added: `missing_urls_control`, `missing_urls_treatment`, `number_missing_urls_control`, `number_missing_urls_treatment`, `missing_providers_control`, `missing_providers_treatment`, `number_missing_providers_control`, and `number_missing_providers_treatment`.

The `missing_urls*` columns contain a list of the exact URLs from the `urls` column that are missing from the model's output for the given utterance.

The `number_missing_urls*` columns contain the count of URLs from the `urls` column that are missing from the model's output for the given utterance.

The `missing_providers*` columns contain a list of the sub-strings (streaming providers) from the `expected` column that are missing from the model's output for the given utterance.

The `number_missing_providers*` columns contain the count of sub-strings (streaming providers) from the `expected` column that are missing from the model's output for the given utterance.

#### Statistical Analysis and Scorecard Structure

Scorecards use the Wilcoxon signed-rank test to determine statistical significance. Since the data being compared is discrete (e.g., counts of the number of sub-strings missing from a response), we do not expect it to be normally distributed, thus Wilcoxon is preferred over the paired Student's t-test. Because the data is paired (comparing control and treatment response for the same utterance), we prefer Wilcoxon over the similar Mann-Whitney U Test which is designed for independent groups.

Scorecards consist of seven columns: `metric`, `control_value`, `treatment_value`, `difference`, `stat`, `p-value`, and `conclusion`.

The `metric` column contains the name of the metric being compared, either the `missing_urls` or the `missing_providers`.

The `*value` columns contain the total number of missing urls or providers for the entire dataset.

The `difference` column contains the result of subtracting the control value from the treatment value. For the missing URL and missing provider metrics, a negative difference (less misses) indicates that the treatment config is improving the given metric while a positive difference (more misses) indicates that the treatment config is making it worse.

The `stat` column contains the Wilcoxon test statistic. In this case it's using a two-sided test, so that's the sum of the ranks of the differences above or below zero -- whichever is smaller.

The `p-value` column contains the probability of obtaining test results at least as extreme as the result actually observed, under the assumption that the null hypothesis is correct.

The `conclusion` section contains one of two strings: `stat-sig` or `noise`. If the p-value for a given metric is less than 0.05, the result is considered statistically significant. If the p-value is greater than or equal to 0.05, it's likely that the difference is caused by statistical noise, and this metric should not be taken as a strong signal either way.

# Future Work
- Add precision calculations to the deterministic metrics. Right now, we only check against a list of specific providers that we *do* want to see in the final response. It would also be bad for the user experience if the model mentions providers where the media is not actually available. We could use an LLM to break down the final response and list which providers are mentioned, or to save money/compute, we could create a list of all providers that are likely to be mentioned and check against each using a simple sub-string search. The sub-string search would be much cheaper, but it would be prone to missing more edge cases than the LLM implementation.
- Only the final chat response is stored by `run_utterances.py`. If we update it to include the tool calls and results, those can be used for further evaluation. This would be especially useful with a complex agent that has more tools available, but with the simple Streaming Availability Agent here (which uses only two tools), the ROI doesn't justify the expense.
- Similarly, only simple, deterministic metrics are currently calculated (based on a baseline truth of specific expected URLs and provider sub-strings). For more complex agents in domains with a wider variety of potential grounding sources, we could also implement a separate script to run LLM powered metrics that measure dimensions such as the overall structure and content of the final response; the number, importance, and veracity of claims made per response; or the accuracy of citations -- whether or not they actually support a given claim--etc. Depending on the domain being evaluated, one or more of these types of metrics may be useful and worth the compute costs.
- Currently, `run_utterances.py` simply runs each utterance -- on control then treatment -- in sequence, and with a large dataset, that can take a long time. This could be sped up by parallelizing model calls (both across control and treatment and across utterances). Cacheing model calls could save compute time and tokens, too, but it's not an approach we recommend, because the model response is exactly what we're testing here.
- These scripts would benefit from user-proofing such as checking that the datasets and results files are formatted correctly and warning the user that new result files and scorecards will replace old files if one with the same name already exists -- requiring the user to confirm that they want to take a destructive action.
- This is all done through the command line. Separate UIs would be useful for interacting with the agent and viewing existing conversations, setting up experiment configs, and analyzing experiment results/scorecards.