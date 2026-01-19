import os
import sys
from attr import dataclass
import platform
from typing import Any, Dict, Iterator, Optional, TypedDict, List

from gptcli.completion import (
    CompletionEvent,
    CompletionProvider,
    Message,
)
from gptcli.providers.google import GoogleCompletionProvider
from gptcli.providers.llama import LLaMACompletionProvider
from gptcli.providers.openai import OpenAICompletionProvider
from gptcli.providers.anthropic import AnthropicCompletionProvider
from gptcli.providers.cohere import CohereCompletionProvider
from gptcli.providers.azure_openai import AzureOpenAICompletionProvider


class AssistantConfig(TypedDict, total=False):
    messages: List[Message]
    provider: Optional[str]
    model: str
    base_url: Optional[str]
    api_key: Optional[str]
    # Legacy per-provider overrides (deprecated, use base_url/api_key instead)
    openai_base_url_override: Optional[str]
    openai_api_key_override: Optional[str]
    anthropic_base_url_override: Optional[str]
    anthropic_api_key_override: Optional[str]
    temperature: float
    top_p: float
    thinking_budget: Optional[int]


# Fallback defaults when nothing is configured
CONFIG_DEFAULTS = {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7,
    "top_p": 1.0,
}

# Valid provider names
PROVIDERS = {"openai", "anthropic", "google", "cohere", "llama", "azure-openai"}

DEFAULT_ASSISTANTS: Dict[str, AssistantConfig] = {
    "dev": {
        "messages": [
            {
                "role": "system",
                "content": f"You are a helpful assistant who is an expert in software development. \
You are helping a user who is a software developer. Your responses are short and concise. \
You include code snippets when appropriate. Code snippets are formatted using Markdown \
with a correct language tag. User's `uname`: {platform.uname()}",
            },
            {
                "role": "user",
                "content": "Your responses must be short and concise. Do not include explanations unless asked.",
            },
            {
                "role": "assistant",
                "content": "Understood.",
            },
        ],
    },
    "general": {
        "messages": [],
    },
    "bash": {
        "messages": [
            {
                "role": "system",
                "content": f"You output only valid and correct shell commands according to the user's prompt. \
You don't provide any explanations or any other text that is not valid shell commands. \
User's `uname`: {platform.uname()}. User's `$SHELL`: {os.environ.get('SHELL')}.",
            }
        ],
    },
}


def infer_provider_from_model(model: str) -> Optional[str]:
    """Infer provider from model name for backward compatibility."""
    if (
        model.startswith("gpt")
        or model.startswith("ft:gpt")
        or model.startswith("oai-compat:")
        or model.startswith("openai:")
        or model.startswith("chatgpt")
        or model.startswith("o1")
        or model.startswith("o3")
        or model.startswith("o4")
    ):
        return "openai"
    elif model.startswith("oai-azure:"):
        return "azure-openai"
    elif model.startswith("claude") or model.startswith("anthropic:"):
        return "anthropic"
    elif model.startswith("llama"):
        return "llama"
    elif model.startswith("command") or model.startswith("c4ai"):
        return "cohere"
    elif model.startswith("gemini") or model.startswith("gemma"):
        return "google"
    return None


def get_completion_provider(
    provider: str,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> CompletionProvider:
    """Get completion provider by name."""
    if provider == "openai":
        return OpenAICompletionProvider(base_url, api_key)
    elif provider == "azure-openai":
        return AzureOpenAICompletionProvider()
    elif provider == "anthropic":
        return AnthropicCompletionProvider(base_url, api_key)
    elif provider == "llama":
        return LLaMACompletionProvider()
    elif provider == "cohere":
        return CohereCompletionProvider()
    elif provider == "google":
        return GoogleCompletionProvider()
    else:
        raise ValueError(f"Unknown provider: {provider}. Valid providers: {', '.join(sorted(PROVIDERS))}")


class Assistant:
    def __init__(self, config: AssistantConfig):
        self.config = config

    @classmethod
    def from_config(cls, name: str, config: AssistantConfig):
        config = config.copy()
        if name in DEFAULT_ASSISTANTS:
            # Merge the config with the default config
            # If a key is in both, use the value from the config
            default_config = DEFAULT_ASSISTANTS[name]
            for key in [*config.keys(), *default_config.keys()]:
                if config.get(key) is None:
                    config[key] = default_config[key]

        return cls(config)

    def init_messages(self) -> List[Message]:
        return self.config.get("messages", [])[:]

    def _param(self, param: str) -> Any:
        # Use the value from the config if exists
        # Otherwise, use the default value
        return self.config.get(param, CONFIG_DEFAULTS.get(param, None))

    def _resolve_provider(self, model: str) -> str:
        """Resolve provider from config or infer from model name."""
        # 1. Explicit provider in config
        provider = self.config.get("provider")
        if provider:
            return provider
        
        # 2. Try to infer from model name (backward compatibility)
        inferred = infer_provider_from_model(model)
        if inferred:
            return inferred
        
        # 3. Fall back to default
        return CONFIG_DEFAULTS["provider"]

    def _resolve_base_url(self, provider: str) -> Optional[str]:
        """Resolve base_url from config."""
        # New unified field takes precedence
        if self.config.get("base_url"):
            return self.config.get("base_url")
        # Legacy per-provider fields for backward compatibility
        if provider == "openai":
            return self.config.get("openai_base_url_override")
        elif provider == "anthropic":
            return self.config.get("anthropic_base_url_override")
        return None

    def _resolve_api_key(self, provider: str) -> Optional[str]:
        """Resolve api_key from config."""
        # New unified field takes precedence
        if self.config.get("api_key"):
            return self.config.get("api_key")
        # Legacy per-provider fields for backward compatibility
        if provider == "openai":
            return self.config.get("openai_api_key_override")
        elif provider == "anthropic":
            return self.config.get("anthropic_api_key_override")
        return None

    def complete_chat(self, messages, stream: bool = True) -> Iterator[CompletionEvent]:
        model = self._param("model")
        provider = self._resolve_provider(model)
        
        completion_provider = get_completion_provider(
            provider,
            self._resolve_base_url(provider),
            self._resolve_api_key(provider),
        )

        args = {
            "model": model,
            "temperature": float(self._param("temperature")),
            "top_p": float(self._param("top_p")),
        }

        # Add thinking budget if it's specified and we're using Claude 3.7
        thinking_budget = self.config.get("thinking_budget")
        if thinking_budget is not None and "claude-3-7" in model:
            args["thinking_budget"] = thinking_budget

        return completion_provider.complete(
            messages,
            args,
            stream,
        )


@dataclass
class AssistantGlobalArgs:
    assistant_name: str
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    thinking_budget: Optional[int] = None


@dataclass
class GlobalDefaults:
    provider: Optional[str] = None
    model: Optional[str] = None


def init_assistant(
    args: AssistantGlobalArgs,
    custom_assistants: Dict[str, AssistantConfig],
    global_defaults: Optional[GlobalDefaults] = None,
) -> Assistant:
    name = args.assistant_name
    if name in custom_assistants:
        assistant = Assistant.from_config(name, custom_assistants[name])
    elif name in DEFAULT_ASSISTANTS:
        assistant = Assistant.from_config(name, DEFAULT_ASSISTANTS[name])
    else:
        print(f"Unknown assistant: {name}")
        sys.exit(1)

    # Apply global defaults if not set in assistant config
    if global_defaults:
        if global_defaults.provider and assistant.config.get("provider") is None:
            assistant.config["provider"] = global_defaults.provider
        if global_defaults.model and assistant.config.get("model") is None:
            assistant.config["model"] = global_defaults.model

    # Override config with command line arguments (highest priority)
    if args.provider is not None:
        assistant.config["provider"] = args.provider
    if args.model is not None:
        assistant.config["model"] = args.model
    if args.temperature is not None:
        assistant.config["temperature"] = args.temperature
    if args.top_p is not None:
        assistant.config["top_p"] = args.top_p
    if args.thinking_budget is not None:
        assistant.config["thinking_budget"] = args.thinking_budget
    return assistant
