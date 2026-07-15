from langchain_tavily import TavilySearch

from config.settings import get_env


def create_search_tools(max_results: int = 2) -> list:
    tavily_api_key = get_env("TAVILY_API_KEY")
    if not tavily_api_key:
        raise ValueError(
            "Missing TAVILY_API_KEY. Add it to .env or export it in your shell."
        )

    return [
        TavilySearch(
            max_results=max_results,
            tavily_api_key=tavily_api_key,
        )
    ]
