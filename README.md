# Streaming Availability Agent and Test Harness
A simple llm agent that answers questions about where to stream movies and TV shows along with a test harness used to evaluate the benefit of system upgrades and prompt improvements.

## Streaming Availability Agent
The Streaming Availability Agent runs using the `qwen3:4b` local llm through `ollama`. It can be run with or without the RAG system enabled. With RAG enabled, the agent has tools available to query the TMDB (The Movie Database) API for up-to-date streaming providers.

### Setup / Run
1. Download and install [ollama](https://ollama.com/download).
2. Run the `qwen3:4b` model locally using the command `ollama run qwen3:4b`.
