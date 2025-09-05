import os
from unittest.mock import Mock, patch

import pytest
from app.infrastructure.ai.openai_embeddings_provider import (
    CachedEmbeddingsProvider,
    OpenAIEmbeddingsProvider,
    create_cached_openai_embeddings_provider,
)


class TestOpenAIEmbeddingsProvider:
    """Test the OpenAI embeddings provider."""

    def test_init_with_valid_config(self):
        """Test initialization with valid configuration."""
        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAIEmbeddingsProvider()
            assert provider._api_key == "test-key"
            assert provider._model == "text-embedding-3-small"
            assert "openai.com" in provider._base_url

    def test_init_missing_api_key_raises_error(self):
        """Test that missing API key raises RuntimeError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="NC_OPENAI_API_KEY is required"):
                OpenAIEmbeddingsProvider()

    def test_init_custom_config(self):
        """Test initialization with custom configuration."""
        provider = OpenAIEmbeddingsProvider(
            api_key="custom-key",
            model="custom-model",
            base_url="https://custom.openai.com/v1",
        )
        assert provider._api_key == "custom-key"
        assert provider._model == "custom-model"
        assert provider._base_url == "https://custom.openai.com/v1"

    @patch("httpx.Client.post")
    def test_embed_texts_success(self, mock_post):
        """Test successful embedding generation."""
        # Mock the API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}, {"embedding": [0.4, 0.5, 0.6]}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAIEmbeddingsProvider()
            result = provider.embed_texts(["text1", "text2"])

        assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_post.assert_called_once()

    def test_embed_texts_empty_list(self):
        """Test embedding empty list returns empty list."""
        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAIEmbeddingsProvider()
            result = provider.embed_texts([])
            assert result == []

    def test_embed_texts_invalid_input(self):
        """Test that invalid input raises ValueError."""
        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAIEmbeddingsProvider()

            with pytest.raises(ValueError, match="All texts must be non-empty strings"):
                provider.embed_texts([""])

            with pytest.raises(ValueError, match="All texts must be non-empty strings"):
                provider.embed_texts(["valid", ""])

    @patch("httpx.Client.post")
    def test_embed_texts_api_timeout(self, mock_post):
        """Test timeout handling."""
        import httpx

        mock_post.side_effect = httpx.TimeoutException("Timeout")

        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAIEmbeddingsProvider()
            with pytest.raises(RuntimeError, match="Timeout while calling OpenAI"):
                provider.embed_texts(["test"])

    @patch("httpx.Client.post")
    def test_embed_texts_api_error_401(self, mock_post):
        """Test API key error handling."""
        import httpx

        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )

        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAIEmbeddingsProvider()
            with pytest.raises(RuntimeError, match="Invalid OpenAI API key"):
                provider.embed_texts(["test"])

    @patch("httpx.Client.post")
    def test_embed_texts_api_error_429(self, mock_post):
        """Test rate limit error handling."""
        import httpx

        mock_response = Mock()
        mock_response.status_code = 429
        mock_post.side_effect = httpx.HTTPStatusError(
            "Rate limit", request=Mock(), response=mock_response
        )

        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAIEmbeddingsProvider()
            with pytest.raises(RuntimeError, match="rate limit exceeded"):
                provider.embed_texts(["test"])

    @patch("httpx.Client.post")
    def test_embed_texts_empty_embedding_response(self, mock_post):
        """Test handling of empty embeddings in response."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": [{"embedding": []}]}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAIEmbeddingsProvider()
            with pytest.raises(RuntimeError, match="Failed to generate embeddings"):
                provider.embed_texts(["test"])

    @patch("httpx.Client.post")
    def test_embed_texts_mismatched_response_length(self, mock_post):
        """Test handling of mismatched response length."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1, 0.2]}]  # Only 1 embedding for 2 texts
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"}):
            provider = OpenAIEmbeddingsProvider()
            with pytest.raises(RuntimeError, match="Failed to generate embeddings"):
                provider.embed_texts(["text1", "text2"])


class TestCachedEmbeddingsProvider:
    """Test the cached embeddings provider."""

    def test_cache_hit(self):
        """Test that cache works for repeated texts."""
        mock_provider = Mock()
        mock_provider.embed_texts.return_value = [[0.1, 0.2, 0.3]]

        cache = CachedEmbeddingsProvider(mock_provider)

        # First call should hit the provider
        result1 = cache.embed_texts(["test text"])
        assert result1 == [[0.1, 0.2, 0.3]]
        assert mock_provider.embed_texts.call_count == 1

        # Second call should use cache
        result2 = cache.embed_texts(["test text"])
        assert result2 == [[0.1, 0.2, 0.3]]
        assert mock_provider.embed_texts.call_count == 1  # Still 1 call

    def test_cache_miss(self):
        """Test that different texts call the provider."""
        mock_provider = Mock()
        mock_provider.embed_texts.return_value = [[0.1, 0.2, 0.3]]

        cache = CachedEmbeddingsProvider(mock_provider)

        # Different texts should call provider each time
        cache.embed_texts(["text1"])
        cache.embed_texts(["text2"])

        assert mock_provider.embed_texts.call_count == 2

    def test_mixed_cache_hit_miss(self):
        """Test mixed cache hits and misses."""
        mock_provider = Mock()
        # Return embedding for new text
        mock_provider.embed_texts.return_value = [[0.3, 0.4]]

        cache = CachedEmbeddingsProvider(mock_provider)

        # First, cache a text
        cache.embed_texts(["cached text"])
        mock_provider.reset_mock()

        # Mixed request: one cached, one new
        result = cache.embed_texts(["cached text", "new text"])

        # Should call provider only for "new text"
        assert mock_provider.embed_texts.call_count == 1
        mock_provider.embed_texts.assert_called_with(["new text"])

        # Check results
        assert len(result) == 2
        assert result[1] == [0.3, 0.4]  # New text gets new embedding

    def test_provider_error_handling(self):
        """Test error handling when provider fails."""
        mock_provider = Mock()
        mock_provider.embed_texts.side_effect = RuntimeError("API Error")

        cache = CachedEmbeddingsProvider(mock_provider)

        with pytest.raises(RuntimeError, match="API Error"):
            cache.embed_texts(["test"])

    def test_cache_key_generation(self):
        """Test that cache keys are generated consistently."""
        mock_provider = Mock()
        cache = CachedEmbeddingsProvider(mock_provider)

        # Same text should generate same key
        key1 = cache._get_cache_key("test text")
        key2 = cache._get_cache_key("test text")
        assert key1 == key2

        # Different text should generate different key
        key3 = cache._get_cache_key("different text")
        assert key1 != key3


class TestEmbeddingsIntegration:
    """Integration tests for embeddings functionality."""

    @patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"})
    def test_create_cached_provider_factory(self):
        """Test the factory function creates cached provider."""
        with patch("httpx.Client.post") as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"data": [{"embedding": [0.1, 0.2]}]}
            mock_post.return_value = mock_response

            provider = create_cached_openai_embeddings_provider()
            assert isinstance(provider, CachedEmbeddingsProvider)

            result = provider.embed_texts(["test"])
            assert result == [[0.1, 0.2]]

    @patch.dict(os.environ, {"NC_OPENAI_API_KEY": "test-key"})
    def test_provider_implements_domain_interface(self):
        """Test that providers implement the domain interface."""
        from app.domain.providers.embeddings_provider import EmbeddingsProvider

        openai_provider = OpenAIEmbeddingsProvider()
        cached_provider = CachedEmbeddingsProvider(openai_provider)

        assert isinstance(openai_provider, EmbeddingsProvider)
        assert isinstance(cached_provider, EmbeddingsProvider)
