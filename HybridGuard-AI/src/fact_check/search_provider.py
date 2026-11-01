"""Web Evidence Search Providers for HybridGuard AI.
Integrates genuine external knowledge retrieval (Wikipedia REST API & DuckDuckGo)
with strict adherence to verifiable URLs, real publication context, and zero hallucinated citations.
"""

from __future__ import annotations

import logging
import urllib.parse
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("hybridguard.search_provider")

DEFAULT_USER_AGENT = "HybridGuardAI/1.0 (academic-research-fact-check; contact@hybridguard.ai)"


class EvidenceDocument:
    """Represents an authentic retrieved evidence snippet with verified provenance."""

    def __init__(
        self,
        title: str,
        url: str,
        snippet: str,
        source: str,
        published_date: Optional[str] = None,
        confidence_score: float = 0.8,
    ):
        self.title = title.strip()
        self.url = url.strip()
        self.snippet = snippet.strip()
        self.source = source.strip()
        self.published_date = published_date
        self.confidence_score = confidence_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "published_date": self.published_date,
            "confidence_score": self.confidence_score,
        }


class SearchProvider(ABC):
    """Abstract interface for external search and knowledge retrieval providers."""

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[EvidenceDocument]:
        """Execute search query and return list of evidence documents."""
        pass


class WikipediaSearchProvider(SearchProvider):
    """Retrieves authoritative encyclopedia excerpts and verified citations from Wikipedia REST APIs."""

    def __init__(self, user_agent: str = DEFAULT_USER_AGENT, timeout: float = 8.0):
        self.user_agent = user_agent
        self.timeout = timeout
        self.headers = {"User-Agent": self.user_agent}

    def search(self, query: str, max_results: int = 4) -> List[EvidenceDocument]:
        """Search Wikipedia API for query and fetch page extracts."""
        logger.info("Executing Wikipedia search for query: '%s'", query)
        documents = []

        try:
            # 1. Search for matching page titles
            search_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "utf8": 1,
                "format": "json",
                "srlimit": max_results,
            }

            with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                resp = client.get(search_url, params=params)
                if resp.status_code != 200:
                    logger.warning("Wikipedia search returned HTTP %d", resp.status_code)
                    return []

                data = resp.json()
                search_hits = data.get("query", {}).get("search", [])

                for hit in search_hits:
                    title = hit.get("title")
                    snippet_raw = hit.get("snippet", "")
                    # Strip basic HTML tags from snippet
                    snippet_clean = snippet_raw.replace('<span class="searchmatch">', "").replace("</span>", "")

                    # 2. Fetch page summary for fuller context
                    encoded_title = urllib.parse.quote(title.replace(" ", "_"))
                    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"

                    try:
                        sum_resp = client.get(summary_url)
                        if sum_resp.status_code == 200:
                            sum_data = sum_resp.json()
                            extract = sum_data.get("extract", snippet_clean)
                            page_url = sum_data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{encoded_title}")
                            timestamp = sum_data.get("timestamp")
                        else:
                            extract = snippet_clean
                            page_url = f"https://en.wikipedia.org/wiki/{encoded_title}"
                            timestamp = None
                    except Exception as e:
                        logger.debug("Failed fetching summary for %s: %s", title, e)
                        extract = snippet_clean
                        page_url = f"https://en.wikipedia.org/wiki/{encoded_title}"
                        timestamp = None

                    if extract:
                        documents.append(
                            EvidenceDocument(
                                title=title,
                                url=page_url,
                                snippet=extract,
                                source="Wikipedia (Verified Wikimedia API)",
                                published_date=timestamp,
                                confidence_score=0.90,
                            )
                        )

        except Exception as e:
            logger.error("Wikipedia search provider error: %s", e)

        return documents


class DuckDuckGoSearchProvider(SearchProvider):
    """Retrieves web evidence and instant answers via DuckDuckGo."""

    def __init__(self, user_agent: str = DEFAULT_USER_AGENT, timeout: float = 8.0):
        self.user_agent = user_agent
        self.timeout = timeout
        self.headers = {"User-Agent": self.user_agent}

    def search(self, query: str, max_results: int = 4) -> List[EvidenceDocument]:
        """Search DuckDuckGo API for instant answers and topic links."""
        logger.info("Executing DuckDuckGo search for query: '%s'", query)
        documents = []

        try:
            api_url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "0",
            }

            with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                resp = client.get(api_url, params=params)
                if resp.status_code != 200:
                    return []

                data = resp.json()
                
                # Check Abstract
                abstract = data.get("AbstractText", "")
                abstract_url = data.get("AbstractURL", "")
                abstract_source = data.get("AbstractSource", "DuckDuckGo Knowledge")
                heading = data.get("Heading", query)

                if abstract and abstract_url:
                    documents.append(
                        EvidenceDocument(
                            title=heading,
                            url=abstract_url,
                            snippet=abstract,
                            source=abstract_source,
                            confidence_score=0.85,
                        )
                    )

                # Check Related Topics
                related_topics = data.get("RelatedTopics", [])
                for topic in related_topics:
                    if len(documents) >= max_results:
                        break
                    if "Text" in topic and "FirstURL" in topic:
                        documents.append(
                            EvidenceDocument(
                                title=topic.get("Text", "")[:60] + "...",
                                url=topic.get("FirstURL", ""),
                                snippet=topic.get("Text", ""),
                                source="DuckDuckGo Topic Search",
                                confidence_score=0.80,
                            )
                        )

        except Exception as e:
            logger.error("DuckDuckGo search provider error: %s", e)

        return documents


class MockSearchProvider(SearchProvider):
    """Deterministic mock search provider for unit tests and offline testing."""

    def __init__(self, mock_documents: Optional[List[EvidenceDocument]] = None):
        self.mock_documents = mock_documents or []

    def search(self, query: str, max_results: int = 5) -> List[EvidenceDocument]:
        if self.mock_documents:
            return self.mock_documents[:max_results]
        return [
            EvidenceDocument(
                title=f"Verified Reference for: {query[:30]}",
                url="https://example.org/verified-reference",
                snippet=f"Authoritative report confirming facts regarding {query}.",
                source="Academic Research Library",
                published_date="2024-01-15T00:00:00Z",
                confidence_score=0.95,
            )
        ]


def get_search_provider(provider_name: str = "wikipedia") -> SearchProvider:
    """Factory function for instantiating search provider by name."""
    provider_name = provider_name.lower().strip()
    if provider_name == "wikipedia":
        return WikipediaSearchProvider()
    elif provider_name in ("duckduckgo", "ddg"):
        return DuckDuckGoSearchProvider()
    elif provider_name == "mock":
        return MockSearchProvider()
    else:
        logger.warning("Unknown search provider '%s', defaulting to Wikipedia", provider_name)
        return WikipediaSearchProvider()

