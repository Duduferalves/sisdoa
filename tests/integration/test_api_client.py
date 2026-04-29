"""Integration tests for Open Food Facts API Gateway.

These tests use respx to mock HTTP requests and avoid making real
network calls, ensuring tests are fast and deterministic.
"""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from sisdoa.infrastructure.api_gateway import (
    OpenFoodFactsGateway,
    ProductFetchError,
    ProductNotFoundError,
)


class TestOpenFoodFactsGateway:
    """Test suite for OpenFoodFactsGateway."""

    @pytest.fixture
    def gateway(self) -> OpenFoodFactsGateway:
        """Create a gateway instance for testing."""
        return OpenFoodFactsGateway()

    @respx.mock
    def test_fetch_product_name_success(self, gateway: OpenFoodFactsGateway) -> None:
        """Test successful product name fetch (200 OK)."""
        # Arrange
        ean = "7891010101010"
        expected_name = "Arroz Integral 5kg"
        mock_response = {
            "status": 1,
            "product": {
                "product_name": expected_name,
                "code": ean,
            },
        }

        respx.get(f"https://world.openfoodfacts.org/api/v2/product/{ean}.json").mock(
            return_value=Response(200, json=mock_response)
        )

        # Act
        result = gateway.fetch_product_name(ean)

        # Assert
        assert result == expected_name

    @respx.mock
    def test_fetch_product_name_not_found_404(self, gateway: OpenFoodFactsGateway) -> None:
        """Test product not found scenario (404)."""
        # Arrange
        ean = "0000000000000"

        respx.get(f"https://world.openfoodfacts.org/api/v2/product/{ean}.json").mock(
            return_value=Response(404, json={"status": 0})
        )

        # Act & Assert
        with pytest.raises(ProductNotFoundError) as exc_info:
            gateway.fetch_product_name(ean)

        assert ean in str(exc_info.value)

    @respx.mock
    def test_fetch_product_name_status_zero(self, gateway: OpenFoodFactsGateway) -> None:
        """Test product with status=0 (not found in database)."""
        # Arrange
        ean = "1234567890123"
        mock_response = {
            "status": 0,
            "message": "Product not found",
        }

        respx.get(f"https://world.openfoodfacts.org/api/v2/product/{ean}.json").mock(
            return_value=Response(200, json=mock_response)
        )

        # Act & Assert
        with pytest.raises(ProductNotFoundError) as exc_info:
            gateway.fetch_product_name(ean)

        assert ean in str(exc_info.value)

    @respx.mock
    def test_fetch_product_name_missing_product_field(self, gateway: OpenFoodFactsGateway) -> None:
        """Test response without product field."""
        # Arrange
        ean = "9999999999999"
        mock_response = {
            "status": 1,
            # Missing "product" key
        }

        respx.get(f"https://world.openfoodfacts.org/api/v2/product/{ean}.json").mock(
            return_value=Response(200, json=mock_response)
        )

        # Act & Assert
        with pytest.raises(ProductNotFoundError) as exc_info:
            gateway.fetch_product_name(ean)

        assert ean in str(exc_info.value)

    @respx.mock
    def test_fetch_product_name_empty_product_name(self, gateway: OpenFoodFactsGateway) -> None:
        """Test product with empty/null product_name."""
        # Arrange
        ean = "5555555555555"
        mock_response = {
            "status": 1,
            "product": {
                "code": ean,
                # Missing or null product_name
                "product_name": None,
            },
        }

        respx.get(f"https://world.openfoodfacts.org/api/v2/product/{ean}.json").mock(
            return_value=Response(200, json=mock_response)
        )

        # Act & Assert
        with pytest.raises(ProductFetchError) as exc_info:
            gateway.fetch_product_name(ean)

        assert "nome não disponível" in str(exc_info.value)

    @respx.mock
    def test_fetch_product_name_timeout(self, gateway: OpenFoodFactsGateway) -> None:
        """Test timeout exception handling."""
        # Arrange
        ean = "1111111111111"

        respx.get(f"https://world.openfoodfacts.org/api/v2/product/{ean}.json").mock(
            side_effect=Exception("Timeout")
        )

        # Force a timeout by mocking the client
        import httpx

        original_get = httpx.Client.get

        def mock_timeout(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            raise httpx.TimeoutException("Request timed out")

        httpx.Client.get = mock_timeout  # type: ignore[method-assign]

        try:
            # Act & Assert
            with pytest.raises(ProductFetchError) as exc_info:
                gateway.fetch_product_name(ean)

            assert (
                "Tempo de resposta" in str(exc_info.value)
                or "timeout" in str(exc_info.value).lower()
            )
        finally:
            httpx.Client.get = original_get  # type: ignore[method-assign]

    @respx.mock
    def test_fetch_product_full_data_success(self, gateway: OpenFoodFactsGateway) -> None:
        """Test fetching full product data."""
        # Arrange
        ean = "7891010101010"
        mock_response = {
            "status": 1,
            "product": {
                "product_name": "Arroz Integral 5kg",
                "code": ean,
                "brands": "Marca Exemplo",
                "categories": "Cereais",
            },
        }

        respx.get(f"https://world.openfoodfacts.org/api/v2/product/{ean}.json").mock(
            return_value=Response(200, json=mock_response)
        )

        # Act
        result = gateway.fetch_product(ean)

        # Assert
        assert result["product_name"] == "Arroz Integral 5kg"
        assert result["code"] == ean

    @respx.mock
    def test_fetch_product_name_http_status_error(self, gateway: OpenFoodFactsGateway) -> None:
        """Test HTTP status error (non-404)."""
        # Arrange
        ean = "2222222222222"

        respx.get(f"https://world.openfoodfacts.org/api/v2/product/{ean}.json").mock(
            return_value=Response(500, json={"error": "Internal Server Error"})
        )

        # Act & Assert
        with pytest.raises(ProductFetchError) as exc_info:
            gateway.fetch_product_name(ean)

        assert "500" in str(exc_info.value)
