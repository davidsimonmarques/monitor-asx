import unittest
from unittest.mock import patch
from validator import (
    extract_price_from_text,
    extract_km_from_text,
    extract_year_from_text,
    validate_ad_live,
)


class TestValidator(unittest.TestCase):

    def test_extract_price(self):
        self.assertEqual(extract_price_from_text("Valor: R$ 69.900,00"), 69900.0)
        self.assertEqual(extract_price_from_text("R$ 74.500"), 74500.0)
        self.assertEqual(extract_price_from_text("Preço 65.000 à vista"), 65000.0)

    def test_extract_km(self):
        self.assertEqual(extract_km_from_text("Apenas 112.500 km rodados"), 112500)
        self.assertEqual(extract_km_from_text("98000 km"), 98000)

    def test_extract_year(self):
        self.assertEqual(extract_year_from_text("ASX 2.0 2016 Completa"), 2016)
        self.assertEqual(extract_year_from_text("Modelo 15/16"), 2016)
        self.assertEqual(extract_year_from_text("Ano 2014"), 2014)
        self.assertIsNone(extract_year_from_text("Ano 2011"))

    @patch("validator.fetch_live_page")
    def test_validate_ad_live_success(self, mock_fetch):
        html_content = """
        <html>
            <title>Mitsubishi ASX 2.0 AWD CVT 2015</title>
            <body>
                <h1>Mitsubishi ASX 2.0 4x4 CVT 2015</h1>
                <p>Preço: R$ 68.000,00</p>
                <p>Quilometragem: 110.000 km</p>
                <p>Câmbio Automático CVT</p>
                <p>Bancos de couro legítimo</p>
                <p>Teto solar panorâmico, ar condicionado, câmera de ré e sensor de estacionamento</p>
                <p>Laudo cautelar aprovado 100%</p>
                <p>Localização: Buritis, Belo Horizonte - MG</p>
                <p>Vendedor: Carlos Eduardo</p>
            </body>
        </html>
        """
        mock_fetch.return_value = (200, "https://exemplo.com/anuncio-123", html_content)

        ad = {
            "id": "test_1",
            "url": "https://exemplo.com/anuncio-123",
            "title": "Mitsubishi ASX 2015",
            "price": 68000.0,
            "year": 2015,
            "source": "OLX",
        }

        res = validate_ad_live(ad)
        self.assertNotNull = self.assertIsNotNone(res)
        self.assertTrue(res["is_eligible"])
        self.assertEqual(res["year"], 2015)
        self.assertEqual(res["price"], 68000.0)
        self.assertTrue(res["leather_seats"])
        self.assertEqual(res["vendor"]["type"], "Particular")
        self.assertEqual(res["vendor"]["gender"], "Homem")

    @patch("validator.fetch_live_page")
    def test_validate_ad_live_disqualify_manual_and_no_leather(self, mock_fetch):
        # Falta couro e câmbio é manual
        html_bad = """
        <html>
            <body>
                <h1>Mitsubishi ASX 2015</h1>
                <p>Preço: R$ 60.000,00</p>
                <p>Câmbio: Manual</p>
                <p>Bancos em tecido</p>
                <p>Belo Horizonte - MG</p>
            </body>
        </html>
        """
        mock_fetch.return_value = (200, "https://exemplo.com/bad", html_bad)
        ad = {"url": "https://exemplo.com/bad"}
        res = validate_ad_live(ad)
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
