"""
TMDB API Documentation: https://developer.themoviedb.org/reference/getting-started
"""
import os
import tmdbsimple as tmdb

from ollama import chat, ChatResponse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv() 

key = os.environ.get("API_KEY", "")
tmdb.API_KEY = key

def query_tmdb_id_by_title(title: str) -> list[dict]:
    """Query for the TMDB ID of TV shows or movies that lexically match the given `title`.

    :param title: Query used for lexical matching on the titles of TV shows and movies.
    :returns: A list of results with information about the original air/release date, an overview of the media, and the TMDB id.
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

available_functions = {
  'query_tmdb_id_by_title': query_tmdb_id_by_title,
  'get_streaming_providers': get_streaming_providers,
}



print("How can I help you?")
message = input()

system_prompt = Path("prompts/streaming_availability_system_prompt.md").read_text(encoding="utf-8")

messages = [
    {'role': 'system', 'content': system_prompt},
    {'role': 'user', 'content': message}
    ]
while True:
    response: ChatResponse = chat(
        model='qwen3:4b',
        messages=messages,
        tools=[query_tmdb_id_by_title, get_streaming_providers],
        think=True,
    )
    messages.append(response.message)
    print("Thinking: ", response.message.thinking)
    print("Content: ", response.message.content)
    if response.message.tool_calls:
        for tc in response.message.tool_calls:
            if tc.function.name in available_functions:
                print(f"Calling {tc.function.name} with arguments {tc.function.arguments}")
                result = available_functions[tc.function.name](**tc.function.arguments)
                print(f"Result: {result}")
                # add the tool result to the messages
                messages.append({'role': 'tool', 'tool_name': tc.function.name, 'content': str(result)})
    else:
        # end the loop when there are no more tool calls
        break
  # continue the loop with the updated messages