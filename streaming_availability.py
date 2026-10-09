"""
TMDB API Documentation: https://developer.themoviedb.org/reference/getting-started
"""
import os
import hashlib
import json
import tmdbsimple as tmdb

from ollama import chat, ChatResponse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

os.environ['OLLAMA_KV_CACHE_TYPE'] = 'q4_0'

key = os.environ.get("API_KEY", "")
tmdb.API_KEY = key

cache_directory = "./_cache"

state = {
    "end_conversation": True,
    "disable_cached_data": False,
    "turn": 0,
    }

def get_request_hash(function_name: str, params: dict = None) -> str:
    """Creates a unique SHA-256 hash key for the API request."""
    request_signature = {
        "function_name": function_name,
        "params": params or {},
    }

    # Sort keys to ensure consistent hashing regardless of dictionary order
    serialized = json.dumps(request_signature, sort_keys=True)
    
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def parse_config(config_overrides={}) -> dict:
    with open("config/agent_config.json", mode='r', encoding='utf-8', newline='') as configfile:
        config = json.load(configfile)

    for key, value in config_overrides.items():
        config[key] = value

    state["end_conversation"] = not config["multi_turn"]
    state["disable_cached_data"] = config["disable_cached_data"]

    return config

def restore_state_defaults(config: dict):
    state["turn"] = 0
    print("!!! turn reset !!!")
    state["end_conversation"] = not config["multi_turn"]

def query_tmdb_id_by_title(title: str) -> list[dict]:
    """Query for the TMDB ID of TV shows or movies that lexically match the given `title`. Uses a cache, because this is just for testing.

    :param title: Query used for lexical matching on the titles of TV shows and movies.
    :returns: A list of results with information about the original air/release date, an overview of the media, and the TMDB id.
    """
    os.makedirs(cache_directory, exist_ok=True)
    params = { "title": title }
    file_hash = get_request_hash("query_tmdb_id_by_title", params)
    file_path = os.path.join(cache_directory, f"{file_hash}.json")

    # Check if cached response exists
    if not state["disable_cached_data"] and os.path.exists(file_path):
        print("Loading `query_tmdb_id_by_title` call from local cache...")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # If not cached, make the live API request
    print("Fetching live data for `query_tmdb_id_by_title`...")
    search = tmdb.Search()
    response = search.multi(query=title)

    if not response["results"]:
        matches = {
            "query": title,
            "error": "No movie or TV show found matching that query."
        }
    else:
        results = response["results"]

        matches = [
            {
                "name": get_name(match),
                "id": match.get("id", ""),
                "media_type": match.get("media_type", ""),
                "overview": match.get("overview", ""),
                "first_air_date": match.get("first_air_date", ""),
                "release_date": match.get("release_date", ""),
                "origin_country": match.get("origin_country", ""),
                "original_language": match.get("original_language", "")
            } for match in results
        ]

    # Save the response data locally
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=4)
    
    return matches

def get_name(result: dict) -> str:
    """Get the name from a result of the simple TMDB multi-search."""
    return result.get("name", result.get("original_name", result.get("title", result.get("original_title", "No Name Found"))))

def get_streaming_providers(tmdb_id: str, media_type: str) -> list[str]:
    """Find where a movie or TV show can be streamed, rented, or purchased in the United States
    based on the TMDB ID.
    
    :param tmdb_id: The official TMDB id of the piece of media whose providers are being searched for. Use `query_tmdb_id_by_title`
    to find this value for a given show or movie.
    :param media_type: Accepted values include "movie" or "tv". Use `query_tmdb_id_by_title` to find this information for a given
    piece of media.
    TODO: Cache results.
    """

    os.makedirs(cache_directory, exist_ok=True)
    params = { "tmdb_id": tmdb_id, "media_type": media_type }
    file_hash = get_request_hash("get_streaming_providers", params)
    file_path = os.path.join(cache_directory, f"{file_hash}.json")

    # Check if cached response exists
    if not state["disable_cached_data"] and os.path.exists(file_path):
        print("Loading `get_streaming_providers` call from local cache...")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # If not cached, make the live API request
    print("Fetching live data for `get_streaming_providers`...")

    # TODO: Currently just looking at the "US", but could set the country per query.s
    country = "US"
    
    if media_type == "movie":
        item = tmdb.Movies(tmdb_id)
        providers = item.watch_providers(
            watch_region=country
        )

    elif media_type == "tv":
        item = tmdb.TV(tmdb_id)
        providers = item.watch_providers(
            watch_region=country
        )

    else:
        providers = {"results": {"US": ["Error: Unknown media_type. No streaming providers found."]}}

    results = providers.get("results", {"US": ["Error: No results found."]})
    country_results =  results.get(country, ["Error: No results for given country."])

    # Save the response data locally
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(country_results, f, indent=4)

    return country_results

def end_conversation() -> None:
    """Invoke to end the current conversation only if the user says they are done or says good bye.
    This function will return nothing, then you will have to respond one more time with a goodbye message."""
    state["end_conversation"] = True

available_functions = {
  'query_tmdb_id_by_title': query_tmdb_id_by_title,
  'get_streaming_providers': get_streaming_providers,
  'end_conversation': end_conversation,
}

def main(config_overrides={}, utterance=None) -> list[dict]:
    config = parse_config(config_overrides=config_overrides)

    print(f"!!! config = {config} !!!")

    if config["disable_grounding"]:
        tools = [end_conversation]
    else:
        tools = [query_tmdb_id_by_title, get_streaming_providers, end_conversation]

    system_prompt = Path(config["system_prompt"]).read_text(encoding='utf-8')

    if config["verbose"]:
        print(f"!!! system prompt : {system_prompt} !!!\n\n")
    print("\nHow can I help you?")

    messages = [
        {'role': 'system', 'content': system_prompt},
        ]

    while True:
        print("")
        if state["turn"] == 0 and utterance:
            user_message = utterance
            print(f"User Input: {user_message}")
        else:        
            user_message = input("User Input: ")
        print("\n===========\n")
        messages.append({'role': 'user', 'content': user_message})
        while True:
            response: ChatResponse = chat(
                model='qwen3:4b',
                messages=messages,
                tools=tools,
                think=True,
            )
            messages.append(response.message)
            if config["show_thinking"]:
                print("\nChain of Thought: \n\n", response.message.thinking)
                print("\n===========\n")
            else:
                print("Thinking... ")
            if response.message.content:
                print("\nAgent Response: \n\n", response.message.content)
                print("\n===========\n")
            if response.message.tool_calls:
                for tc in response.message.tool_calls:
                    if tc.function.name in available_functions:
                        if config["show_tool_calls"]:
                            print(f"Calling {tc.function.name} with arguments {tc.function.arguments}\n")
                        else:
                            print("Calling tools...")
                        result = available_functions[tc.function.name](**tc.function.arguments)
                        if config["show_tool_calls"]:
                            print(f"Result: \n\n{result}")
                            print("\n===========\n")
                        else:
                            print("Analyzing results...")
                            print("\n===========\n")
                        # add the tool result to the messages
                        messages.append({'role': 'tool', 'tool_name': tc.function.name, 'content': str(result)})
            else:
                state["turn"] += 1
                # end the loop when there are no more tool calls
                break
          # continue the loop with the updated messages
        if state["end_conversation"]:
            restore_state_defaults(config=config)
            return messages

if __name__ == "__main__":
    main()