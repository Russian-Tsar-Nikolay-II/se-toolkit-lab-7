from __future__ import annotations

import json
import os
import sys
from typing import Any
from urllib.parse import urlparse

import httpx

from services.lms_client import LMSClient, load_env

load_env()

SYSTEM_PROMPT = """You are SE Toolkit Bot, an analytics assistant for an LMS backend.

Rules:
- For factual questions about labs, learners, scores, pass rates, timeline, groups, top learners, completion, or sync status, use tools instead of guessing.
- You may call multiple tools. Multi-step reasoning is expected.
- For comparison questions, do not stop after inspecting only a subset of relevant entities. Keep calling tools until you have enough data to answer correctly.
- If the user asks which lab has the lowest or worst pass rate, first discover the labs with get_items, then call get_pass_rates for each relevant lab, compare average task pass rates, and name the specific lab in the final answer.
- If the user asks for scores for a lab, prefer get_pass_rates for per-task percentages unless they explicitly ask for score distribution buckets, histogram, or buckets.
- If the user asks which group is best in a lab, use get_groups and compare the best available score metric from the tool result.
- If the user asks who the top students are, use get_top_learners.
- If the user says only something ambiguous like "lab 4", ask a brief clarifying question.
- For greetings, respond warmly and mention a few things you can do.
- For nonsense or unclear messages, say you did not understand and give 3 concrete examples of supported questions.
- Never invent numbers. Base the answer only on tool results.
- Do not describe future steps. If more data is needed, call the next tool immediately.
- Keep answers concise and user-facing.
"""

FINAL_SUMMARY_PROMPT = """You already have all necessary tool results in the conversation.
Do not call tools. Do not describe future steps.
Write the final user-facing answer now using only the available tool results.
If the question is comparative, name the specific winner/loser and include the key number.
If the question is unclear or unsupported, reply helpfully and briefly.
"""

LAB_PARAMETER = {
    "type": "string",
    "description": "Lab identifier such as 'lab-01', 'lab-02', or 'lab-04'.",
}

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_items",
            "description": "List LMS items including labs and tasks. Use this to discover which labs exist.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_learners",
            "description": "Get enrolled learners and their groups.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_scores",
            "description": "Get score distribution buckets for a lab. Use this for score distribution or bucket questions, not per-task pass rates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": LAB_PARAMETER,
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pass_rates",
            "description": "Get per-task average scores or pass rates and attempt counts for a lab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": LAB_PARAMETER,
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_timeline",
            "description": "Get submissions per day for a lab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": LAB_PARAMETER,
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_groups",
            "description": "Get per-group performance for a lab, including group-level scores and student counts when available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": LAB_PARAMETER,
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_learners",
            "description": "Get top learners by score. Use a lab when the user asks about a specific lab. Otherwise omit lab for overall top learners if supported.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": LAB_PARAMETER,
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of learners to return. Usually 5.",
                        "default": 5,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_completion_rate",
            "description": "Get the completion rate percentage for a lab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": LAB_PARAMETER,
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_sync",
            "description": "Trigger an ETL sync from the autochecker to refresh backend data.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


class LLMRouter:
    def __init__(self, client: LMSClient | None = None) -> None:
        self.client = client or LMSClient()
        base_url = os.getenv("LLM_API_BASE_URL", "http://127.0.0.1:42005/v1").strip()
        if base_url and not base_url.startswith(("http://", "https://")):
            base_url = f"http://{base_url}"
        self.base_url = base_url.rstrip("/")
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.model = os.getenv("LLM_API_MODEL", "qwen3-coder-plus").strip()

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _host_port(self) -> str:
        parsed = urlparse(self.base_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        return f"{host}:{port}"

    def _llm_error_message(self, exc: Exception) -> str:
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            reason = exc.response.reason_phrase
            if status == 401:
                return f"LLM error: HTTP 401 {reason}. The Qwen proxy token may have expired. Restart the proxy."
            return f"LLM error: HTTP {status} {reason}."
        if isinstance(exc, httpx.ConnectError):
            return f"LLM error: connection refused ({self._host_port()}). Check that the Qwen proxy is running."
        if isinstance(exc, httpx.TimeoutException):
            return f"LLM error: request timed out while contacting {self._host_port()}."
        if isinstance(exc, httpx.RequestError):
            return f"LLM error: request error while contacting {self._host_port()}: {exc}."
        return f"LLM error: {exc}"

    def _extract_text(self, message: dict[str, Any]) -> str:
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, dict):
                    text = part.get("text") or part.get("content")
                    if isinstance(text, str):
                        parts.append(text)
            return "".join(parts).strip()
        return ""

    def _extract_tool_calls(self, message: dict[str, Any]) -> list[dict[str, Any]]:
        tool_calls = message.get("tool_calls")
        if isinstance(tool_calls, list):
            return tool_calls

        legacy = message.get("function_call")
        if isinstance(legacy, dict):
            return [
                {
                    "id": "legacy-function-call",
                    "type": "function",
                    "function": {
                        "name": legacy.get("name", ""),
                        "arguments": legacy.get("arguments", "{}"),
                    },
                }
            ]
        return []

    def _parse_arguments(self, raw_arguments: Any) -> dict[str, Any]:
        if raw_arguments is None:
            return {}
        if isinstance(raw_arguments, dict):
            return raw_arguments
        if isinstance(raw_arguments, str):
            raw_arguments = raw_arguments.strip()
            if not raw_arguments:
                return {}
            try:
                parsed = json.loads(raw_arguments)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return {}
        return {}

    def _chat(self, messages: list[dict[str, Any]], use_tools: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.0,
        }

        if use_tools:
            payload["tools"] = TOOLS
            payload["tool_choice"] = "auto"

        with httpx.Client(timeout=90.0, follow_redirects=True) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("LLM response has no choices")

        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise ValueError("LLM response has no message")

        return message

    def _coerce_limit(self, value: Any, default: int = 5) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _call_tool(self, name: str, args: dict[str, Any]) -> Any:
        if name == "get_items":
            return self.client.get_items()
        if name == "get_learners":
            return self.client.get_learners()
        if name == "get_scores":
            return self.client.get_scores(str(args.get("lab", "")))
        if name == "get_pass_rates":
            return self.client.get_pass_rates(str(args.get("lab", "")))
        if name == "get_timeline":
            return self.client.get_timeline(str(args.get("lab", "")))
        if name == "get_groups":
            return self.client.get_groups(str(args.get("lab", "")))
        if name == "get_top_learners":
            lab = args.get("lab")
            lab_value = str(lab) if isinstance(lab, str) and lab.strip() else None
            limit = self._coerce_limit(args.get("limit", 5), default=5)
            return self.client.get_top_learners(lab=lab_value, limit=limit)
        if name == "get_completion_rate":
            return self.client.get_completion_rate(str(args.get("lab", "")))
        if name == "trigger_sync":
            return self.client.trigger_sync()
        return {"error": f"Unknown tool: {name}"}

    def _result_summary(self, result: Any) -> str:
        if isinstance(result, dict):
            if "error" in result:
                return f"error: {result['error']}"
            return f"object with keys: {', '.join(sorted(result.keys())) or '(none)'}"
        if isinstance(result, list):
            return f"{len(result)} item(s)"
        return type(result).__name__

    def _looks_like_premature_step(self, text: str) -> bool:
        lowered = text.strip().lower()
        if not lowered:
            return False

        bad_starts = (
            "now that i know",
            "let me ",
            "i'll ",
            "i will ",
            "i need to ",
            "to answer this,",
            "next, ",
            "first, ",
        )
        if lowered.startswith(bad_starts):
            return True

        bad_phrases = (
            "i'll check",
            "i will check",
            "let me check",
            "let me start by",
            "i'll start by",
            "i will start by",
            "i need to check",
            "i need to inspect",
            "i need to look at",
        )
        return any(phrase in lowered for phrase in bad_phrases)

    def _finalize_from_tool_results(self, messages: list[dict[str, Any]]) -> str:
        final_messages = list(messages)
        final_messages.append({"role": "system", "content": FINAL_SUMMARY_PROMPT})

        try:
            message = self._chat(final_messages, use_tools=False)
        except Exception as exc:
            return self._llm_error_message(exc)

        text = self._extract_text(message)
        if text:
            return text

        return (
            "I couldn't produce a final answer from the model. "
            "Try rephrasing the question or ask something like "
            "'what labs are available?' or 'which lab has the lowest pass rate?'."
        )

    def route(self, user_text: str) -> str:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text.strip()},
        ]

        tool_result_count = 0
        nudges_used = 0

        for _ in range(20):
            try:
                message = self._chat(messages, use_tools=True)
            except Exception as exc:
                return self._llm_error_message(exc)

            assistant_text = self._extract_text(message)
            tool_calls = self._extract_tool_calls(message)

            assistant_message: dict[str, Any] = {
                "role": "assistant",
                "content": assistant_text,
            }
            if tool_calls:
                assistant_message["tool_calls"] = tool_calls
            messages.append(assistant_message)

            if tool_calls:
                for tool_call in tool_calls:
                    function = tool_call.get("function", {})
                    if not isinstance(function, dict):
                        function = {}

                    name = str(function.get("name", "")).strip()
                    args = self._parse_arguments(function.get("arguments", "{}"))

                    print(
                        f"[tool] LLM called: {name}({json.dumps(args, ensure_ascii=False)})",
                        file=sys.stderr,
                        flush=True,
                    )

                    result = self._call_tool(name, args)

                    print(
                        f"[tool] Result: {self._result_summary(result)}",
                        file=sys.stderr,
                        flush=True,
                    )

                    tool_result_count += 1
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.get("id", f"tool-call-{tool_result_count}"),
                            "name": name,
                            "content": json.dumps(result, ensure_ascii=False),
                        }
                    )

                print(
                    f"[summary] Feeding {tool_result_count} tool result(s) back to LLM",
                    file=sys.stderr,
                    flush=True,
                )
                continue

            if assistant_text:
                if tool_result_count > 0 and self._looks_like_premature_step(assistant_text) and nudges_used < 4:
                    nudges_used += 1
                    print(
                        "[summary] Model stopped early with a plan; nudging it to continue with tools",
                        file=sys.stderr,
                        flush=True,
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Do not describe future steps. Either call the next needed tool now, "
                                "or give the final answer now using only the tool results already available."
                            ),
                        }
                    )
                    continue

                return assistant_text

            if tool_result_count > 0 and nudges_used < 4:
                nudges_used += 1
                print(
                    "[summary] Model returned an empty response; nudging it to continue",
                    file=sys.stderr,
                    flush=True,
                )
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your last response was empty. Continue by calling the next needed tool now, "
                            "or give the final answer now using only the tool results already available."
                        ),
                    }
                )
                continue

            break

        if tool_result_count > 0:
            print(
                "[summary] Falling back to final summarization pass without tools",
                file=sys.stderr,
                flush=True,
            )
            return self._finalize_from_tool_results(messages)

        return (
            "I couldn't produce a final answer from the model. "
            "Try rephrasing the question or ask something like "
            "'what labs are available?' or 'which lab has the lowest pass rate?'."
        )
