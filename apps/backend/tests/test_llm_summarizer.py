import os
from unittest.mock import Mock, patch

import httpx
import pytest
from app.infrastructure.ai.openai_summarization_provider import (
    CachedSummarizationProvider,
    FallbackSummarizationProvider,
    OpenAISummarizationProvider,
    create_cached_openai_summarizer,
    create_fallback_summarizer,
)


class TestOpenAISummarizationProvider:
    """Test the OpenAI summarization provider."""

    def test_init_with_valid_config(self):
        """Test initialization with valid configuration."""
        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAISummarizationProvider()
            assert provider._api_key == "test-key"
            assert provider._model == "gpt-4o-mini"
            assert "openai.com" in provider._base_url

    def test_init_missing_api_key_raises_error(self):
        """Test that missing API key raises RuntimeError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="NC_OPENAI_API_KEY is required"):
                OpenAISummarizationProvider()

    def test_init_custom_config(self):
        """Test initialization with custom configuration."""
        provider = OpenAISummarizationProvider(
            api_key="custom-key",
            model="custom-model",
            base_url="https://custom.openai.com/v1",
        )
        assert provider._api_key == "custom-key"
        assert provider._model == "custom-model"
        assert provider._base_url == "https://custom.openai.com/v1"

    @patch("httpx.Client.post")
    def test_summarize_success(self, mock_post):
        """Test successful summarization."""
        # Mock the API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Ceci est un résumé test."}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAISummarizationProvider()
            result = provider.summarize("Ceci est un long texte à résumer.")

        assert result == "Ceci est un résumé test."
        mock_post.assert_called_once()

    def test_summarize_empty_transcript(self):
        """Test summarization of empty transcript."""
        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAISummarizationProvider()
            result = provider.summarize("")
            assert result == ""

            result = provider.summarize("   ")
            assert result == ""

    def test_summarize_long_transcript_truncation(self, caplog):
        """Test that long transcripts are truncated."""
        long_text = "a" * 150000  # Very long text

        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAISummarizationProvider()

            with patch.object(provider, "_summarize_with_model") as mock_summarize:
                mock_summarize.return_value = "Résumé"
                provider.summarize(long_text)

                # Should have truncated the text
                mock_summarize.assert_called_once()
                call_args = mock_summarize.call_args[0]
                assert len(call_args[0]) < len(long_text)  # Text was truncated
                assert "...[truncated]" in call_args[0]

                # Check warning was logged
                assert "Transcript too long" in caplog.text

    @patch("httpx.Client.post")
    def test_summarize_api_timeout(self, mock_post):
        """Test timeout handling."""
        import httpx

        mock_post.side_effect = httpx.TimeoutException("Timeout")

        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAISummarizationProvider()
            with pytest.raises(RuntimeError, match="Timeout while calling OpenAI"):
                provider.summarize("test transcript")

    @patch("httpx.Client.post")
    def test_summarize_api_error_401(self, mock_post):
        """Test API key error handling."""
        import httpx

        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )

        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAISummarizationProvider()
            with pytest.raises(RuntimeError, match="Invalid OpenAI API key"):
                provider.summarize("test transcript")

    @patch("httpx.Client.post")
    def test_summarize_api_error_429(self, mock_post):
        """Test rate limit error handling."""
        import httpx

        mock_response = Mock()
        mock_response.status_code = 429
        mock_post.side_effect = httpx.HTTPStatusError(
            "Rate limit", request=Mock(), response=mock_response
        )

        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAISummarizationProvider()
            with pytest.raises(RuntimeError, match="rate limit exceeded"):
                provider.summarize("test transcript")

    @patch("httpx.Client.post")
    def test_summarize_empty_response(self, mock_post):
        """Test handling of empty API response."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": []}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAISummarizationProvider()
            with pytest.raises(RuntimeError, match="Failed to generate summary"):
                provider.summarize("test transcript")

    @patch("httpx.Client.post")
    def test_summarize_empty_content(self, mock_post):
        """Test handling of empty content in response."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": ""}}]}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAISummarizationProvider()
            with pytest.raises(RuntimeError, match="Failed to generate summary"):
                provider.summarize("test transcript")

    @patch("httpx.Client.post")
    def test_fallback_models(self, mock_post):
        """Test fallback to different models."""
        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 429
        mock_response_success = Mock()
        mock_response_success.raise_for_status.return_value = None
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Fallback summary"}}]
        }

        # First call fails with rate limit, second succeeds
        mock_post.side_effect = [
            httpx.HTTPStatusError(
                "Rate limit", request=Mock(), response=mock_response_fail
            ),
            mock_response_success,
        ]

        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAISummarizationProvider()
            result = provider.summarize("test transcript")

        assert result == "Fallback summary"
        assert mock_post.call_count == 2  # Tried two models


class TestCachedSummarizationProvider:
    """Test the cached summarization provider."""

    def test_cache_hit(self):
        """Test that cache works for repeated summaries."""
        mock_provider = Mock()
        mock_provider.summarize.return_value = "Cached summary"

        cache = CachedSummarizationProvider(mock_provider)

        # First call should hit the provider
        result1 = cache.summarize("test transcript")
        assert result1 == "Cached summary"
        assert mock_provider.summarize.call_count == 1

        # Second call should use cache
        result2 = cache.summarize("test transcript")
        assert result2 == "Cached summary"
        assert mock_provider.summarize.call_count == 1  # Still 1 call

    def test_cache_miss(self):
        """Test that different transcripts call the provider."""
        mock_provider = Mock()
        mock_provider.summarize.return_value = "New summary"

        cache = CachedSummarizationProvider(mock_provider)

        # Different transcripts should call provider each time
        cache.summarize("transcript1")
        cache.summarize("transcript2")

        assert mock_provider.summarize.call_count == 2

    def test_cache_with_language(self):
        """Test that different languages create different cache keys."""
        mock_provider = Mock()
        mock_provider.summarize.return_value = "Summary"

        cache = CachedSummarizationProvider(mock_provider)

        # Same transcript, different languages = different cache keys
        cache.summarize("test", "fr")
        cache.summarize("test", "en")

        assert mock_provider.summarize.call_count == 2

    def test_cache_empty_transcript(self):
        """Test cache handling of empty transcripts."""
        mock_provider = Mock()
        cache = CachedSummarizationProvider(mock_provider)

        result = cache.summarize("")
        assert result == ""
        assert mock_provider.summarize.call_count == 0  # Should not call provider

    def test_provider_error_handling(self):
        """Test error handling when provider fails."""
        mock_provider = Mock()
        mock_provider.summarize.side_effect = RuntimeError("API Error")

        cache = CachedSummarizationProvider(mock_provider)

        with pytest.raises(RuntimeError, match="API Error"):
            cache.summarize("test transcript")

    def test_cache_key_generation(self):
        """Test that cache keys are generated consistently."""
        mock_provider = Mock()
        cache = CachedSummarizationProvider(mock_provider)

        # Same input should generate same key
        key1 = cache._get_cache_key("test text", "fr")
        key2 = cache._get_cache_key("test text", "fr")
        assert key1 == key2

        # Different input should generate different key
        key3 = cache._get_cache_key("different text", "fr")
        assert key1 != key3


class TestFallbackSummarizationProvider:
    """Test the fallback summarization provider."""

    def test_single_provider_success(self):
        """Test successful summarization with single provider."""
        mock_provider = Mock()
        mock_provider.summarize.return_value = "Test summary"

        fallback = FallbackSummarizationProvider([mock_provider])
        result = fallback.summarize("test transcript")

        assert result == "Test summary"
        mock_provider.summarize.assert_called_once()

    def test_provider_fallback(self):
        """Test fallback when first provider fails."""
        mock_provider1 = Mock()
        mock_provider1.summarize.side_effect = RuntimeError("Provider 1 failed")

        mock_provider2 = Mock()
        mock_provider2.summarize.return_value = "Fallback summary"

        fallback = FallbackSummarizationProvider([mock_provider1, mock_provider2])
        result = fallback.summarize("test transcript")

        assert result == "Fallback summary"
        mock_provider1.summarize.assert_called_once()
        mock_provider2.summarize.assert_called_once()

    def test_all_providers_fail(self):
        """Test when all providers fail."""
        mock_provider1 = Mock()
        mock_provider1.summarize.side_effect = RuntimeError("Provider 1 failed")

        mock_provider2 = Mock()
        mock_provider2.summarize.side_effect = RuntimeError("Provider 2 failed")

        fallback = FallbackSummarizationProvider([mock_provider1, mock_provider2])

        with pytest.raises(RuntimeError, match="All summarization providers failed"):
            fallback.summarize("test transcript")

    def test_empty_providers_list(self):
        """Test error when no providers are given."""
        with pytest.raises(ValueError, match="At least one provider is required"):
            FallbackSummarizationProvider([])


class TestSummarizationIntegration:
    """Integration tests for summarization functionality."""

    @patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"})
    def test_create_cached_provider_factory(self):
        """Test the factory function creates cached provider."""
        with patch("httpx.Client.post") as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Test summary"}}]
            }
            mock_post.return_value = mock_response

            provider = create_cached_openai_summarizer()
            assert isinstance(provider, CachedSummarizationProvider)

            result = provider.summarize("test transcript")
            assert result == "Test summary"

    @patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"})
    def test_create_fallback_provider_factory(self):
        """Test the fallback factory function."""
        with patch("httpx.Client.post") as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Fallback summary"}}]
            }
            mock_post.return_value = mock_response

            provider = create_fallback_summarizer()
            assert isinstance(provider, FallbackSummarizationProvider)

            result = provider.summarize("test transcript")
            assert result == "Fallback summary"

    @patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"})
    def test_provider_implements_domain_interface(self):
        """Test that providers implement the domain interface."""
        from app.domain.providers.summarization_provider import SummarizationProvider

        openai_provider = OpenAISummarizationProvider()
        cached_provider = CachedSummarizationProvider(openai_provider)
        fallback_provider = FallbackSummarizationProvider([openai_provider])

        assert isinstance(openai_provider, SummarizationProvider)
        assert isinstance(cached_provider, SummarizationProvider)
        assert isinstance(fallback_provider, SummarizationProvider)
