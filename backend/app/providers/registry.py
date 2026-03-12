from app.providers.base import LLMProvider


class ProviderRegistry:
    def __init__(self, default_provider: str) -> None:
        self._default_provider = default_provider
        self._providers: dict[str, LLMProvider] = {}

    def register(self, provider: LLMProvider) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str | None = None) -> LLMProvider:
        provider_name = name or self._default_provider
        if provider_name not in self._providers:
            raise KeyError(f"Unknown provider: {provider_name}")
        return self._providers[provider_name]

    @property
    def default_provider(self) -> str:
        return self._default_provider
