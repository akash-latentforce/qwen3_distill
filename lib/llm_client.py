"""
LLM client for dependency extraction via OpenAI-compatible APIs (vLLM, OpenRouter).
Handles API calls, retries, and JSON response parsing.
"""

import json
import time

from openai import OpenAI, APIStatusError, APITimeoutError, APIConnectionError


def _parse_json_response(raw: str) -> dict | None:
    """Parse JSON from LLM response, handling markdown fences and preamble."""
    text = raw.strip()

    # Strip markdown fences
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            inner = text[first_newline + 1:]
            close = inner.rfind("```")
            if close != -1:
                inner = inner[:close]
            text = inner.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find first JSON object
    for open_ch, close_ch in [('{', '}'), ('[', ']')]:
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

    return None


def llm_extract(
    prompt: str,
    model: str,
    base_url: str,
    api_key: str = "",
    max_retries: int = 3,
    timeout: int = 120,
    max_tokens: int = None,
    extra_body: dict = None,
    extra_headers: dict = None,
) -> dict | None:
    """
    Send a prompt to an OpenAI-compatible endpoint and return parsed JSON.

    Args:
        prompt: The full prompt to send
        model: Model identifier (HF ID for vLLM, or model path)
        base_url: API endpoint (e.g. http://localhost:8000/v1)
        api_key: API key (empty string for local vLLM)
        max_tokens: Cap on generated tokens
        extra_body: Extra fields for the request (e.g. vLLM chat_template_kwargs)

    Returns:
        Parsed JSON dict, or None if all attempts fail
    """
    client = OpenAI(
        base_url=base_url,
        api_key=api_key or "no-key",
        timeout=timeout,
        default_headers=extra_headers or {},
    )

    for attempt in range(max_retries):
        try:
            kwargs = dict(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            if extra_body:
                kwargs["extra_body"] = extra_body

            response = client.chat.completions.create(**kwargs)

            if not response.choices:
                time.sleep((attempt + 1) * 2)
                continue

            content = response.choices[0].message.content
            if content is None:
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 2)
                    continue
                return None

            parsed = _parse_json_response(content)
            if parsed is None:
                print(f"  JSON parse error. Raw: {content[:200]}...")
                return None

            return parsed

        except APITimeoutError:
            time.sleep((attempt + 1) * 5)
        except APIStatusError as e:
            print(f"  API error {e.status_code}: {e.message}")
            time.sleep((attempt + 1) * 5)
        except APIConnectionError as e:
            print(f"  Connection error: {e}")
            time.sleep((attempt + 1) * 5)

    return None
