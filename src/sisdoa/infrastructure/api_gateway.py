"""API Gateway for external service integrations."""

from __future__ import annotations

import httpx


class ProductNotFoundError(Exception):
    """Raised when a product is not found in the API."""

    def __init__(self, ean: str) -> None:
        self.ean = ean
        super().__init__(f"Produto com código de barras {ean} não foi encontrado.")


class ProductFetchError(Exception):
    """Raised when there is an error fetching product data from the API."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class OpenFoodFactsGateway:
    """Gateway for Open Food Facts API integration.

    This class provides methods to fetch product information from the
    Open Food Facts API using a barcode (EAN).

    API Documentation: https://world.openfoodfacts.org/api
    """

    BASE_URL = "https://world.openfoodfacts.org/api/v2/product"
    TIMEOUT_SECONDS = 10

    def __init__(self, client: httpx.Client | None = None) -> None:
        """Initialize the gateway with an optional HTTP client.

        Args:
            client: Optional httpx.Client instance. If not provided,
                a new client will be created for each request.
        """
        self._client = client

    def _get_client(self) -> httpx.Client:
        """Get or create an HTTP client.

        Returns:
            httpx.Client instance configured with timeout.
        """
        if self._client is not None:
            return self._client
        return httpx.Client(timeout=self.TIMEOUT_SECONDS)

    def fetch_product_name(self, ean: str) -> str:
        """Fetch product name from Open Food Facts API.

        Args:
            ean: The barcode (EAN-13 or EAN-8) of the product.

        Returns:
            The product name if found.

        Raises:
            ProductNotFoundError: If the product is not found (404).
            ProductFetchError: If there is a network error or timeout.
        """
        url = f"{self.BASE_URL}/{ean}.json"
        client = self._get_client()

        try:
            response = client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ProductNotFoundError(ean) from e
            raise ProductFetchError(
                f"Erro ao buscar produto: {e.response.status_code} {e.response.reason_phrase}"
            ) from e
        except httpx.TimeoutException as e:
            raise ProductFetchError(
                "Tempo de resposta da API excedido. Verifique sua conexão e tente novamente."
            ) from e
        except httpx.RequestError as e:
            raise ProductFetchError(
                f"Erro de conexão: {e}. Verifique sua internet e tente novamente."
            ) from e

        data = response.json()

        # Check if product exists in response
        if data.get("status") == 0 or "product" not in data:
            raise ProductNotFoundError(ean)

        product = data.get("product", {})
        product_name = product.get("product_name")

        if not product_name:
            raise ProductFetchError(
                f"Produto encontrado, mas nome não disponível para o código {ean}."
            )

        return str(product_name)

    def fetch_product(self, ean: str) -> dict:
        """Fetch full product data from Open Food Facts API.

        Args:
            ean: The barcode (EAN-13 or EAN-8) of the product.

        Returns:
            Dictionary with product data.

        Raises:
            ProductNotFoundError: If the product is not found (404).
            ProductFetchError: If there is a network error or timeout.
        """
        url = f"{self.BASE_URL}/{ean}.json"
        client = self._get_client()

        try:
            response = client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ProductNotFoundError(ean) from e
            raise ProductFetchError(
                f"Erro ao buscar produto: {e.response.status_code} {e.response.reason_phrase}"
            ) from e
        except httpx.TimeoutException as e:
            raise ProductFetchError(
                "Tempo de resposta da API excedido. Verifique sua conexão e tente novamente."
            ) from e
        except httpx.RequestError as e:
            raise ProductFetchError(
                f"Erro de conexão: {e}. Verifique sua internet e tente novamente."
            ) from e

        data = response.json()

        if data.get("status") == 0 or "product" not in data:
            raise ProductNotFoundError(ean)

        return data.get("product", {})
