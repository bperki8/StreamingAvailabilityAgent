"""
TMDB API Documentation: https://developer.themoviedb.org/reference/getting-started
"""
import os
import argparse
import tmdbsimple as tmdb

from ollama import chat, ChatResponse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv() 

key = os.environ.get("API_KEY", "")
tmdb.API_KEY = key

state = {
    "end_conversation": True,
    "show_thinking": False,
    "show_tool_calls": False,
    "turn": 0,
    }

def parse_args(args_list=None):
    parser = argparse.ArgumentParser(
        description="Local LLM agent for finding where to stream movies and TV shows.",
    )
    parser.add_argument("-u", "--utterance", type=str, help="the first user utterance to pass to the agent")
    parser.add_argument("-m", "--multi_turn", action="store_true", help="enable multi-turn conversations")
    parser.add_argument("-d", "--disable_grounding", action="store_true", help="disable tools used for searching TMDB")
    parser.add_argument("-t", "--show_thinking", action="store_true", help="show model's chain of thought before response")
    parser.add_argument("-tool", "--show_tool_calls", action="store_true", help="show tool calls and results")
    parser.add_argument("-sp", "--system_prompt", type=str, help="path to the system prompt", default="prompts/system_prompt_with_tools.md")

    args = parser.parse_args(args_list)

    state["end_conversation"] = not args.multi_turn
    state["show_thinking"] = args.show_thinking
    state["show_tool_calls"] = args.show_tool_calls

    return args

def restore_state_defaults(args):
    state["turn"] = 0
    state["end_conversation"] = not args.multi_turn

def query_tmdb_id_by_title(title: str) -> list[dict]:
    """Query for the TMDB ID of TV shows or movies that lexically match the given `title`.

    :param title: Query used for lexical matching on the titles of TV shows and movies.
    :returns: A list of results with information about the original air/release date, an overview of the media, and the TMDB id.
    TODO: Cache results.
    """
    search = tmdb.Search()
    response = search.multi(query=title)

    if not response["results"]:
        return {
            "query": title,
            "error": "No movie or TV show found matching that query."
        }

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
    return results.get(country, ["Error: No results for given country."])

def end_conversation() -> None:
    """Invoke to end the current conversation only if the user says they are done or says good bye.
    This function will return nothing, then you will have to respond one more time with a goodbye message."""
    state["end_conversation"] = True

available_functions = {
  'query_tmdb_id_by_title': query_tmdb_id_by_title,
  'get_streaming_providers': get_streaming_providers,
  'end_conversation': end_conversation,
}

def main(args_list=None) -> list[dict]:
    args = parse_args(args_list)

    if args.disable_grounding:
        tools = [end_conversation]
    else:
        tools = [query_tmdb_id_by_title, get_streaming_providers, end_conversation]

    system_prompt = Path(args.system_prompt).read_text(encoding='utf-8')

    print(f"!!! system prompt : {system_prompt} !!!\n\n")

    print("\nHow can I help you?")

    messages = [
        {'role': 'system', 'content': system_prompt},
        ]

    while True:
        print("")
        if state["turn"] == 0 and args.utterance:
            user_message = args.utterance
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
            if state["show_thinking"]:
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
                        if state["show_tool_calls"]:
                            print(f"Calling {tc.function.name} with arguments {tc.function.arguments}\n")
                        else:
                            print("Calling tools...")
                        result = available_functions[tc.function.name](**tc.function.arguments)
                        if state["show_tool_calls"]:
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
            restore_state_defaults(args=args)
            return messages

if __name__ == "__main__":
    main()