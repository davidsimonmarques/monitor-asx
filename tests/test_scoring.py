import unittest
from scoring import (
    identify_vendor,
    extract_laudo_cautelar,
    extract_history_status,
    evaluate_optionals,
    calculate_score,
)


class TestScoring(unittest.TestCase):

    def test_identify_vendor_store(self):
        info1 = identify_vendor("Lojas Carbig Seminovos", "dealership")
        self.assertEqual(info1["type"], "Loja")

        info2 = identify_vendor("Auto Shopping BH Multimarcas")
        self.assertEqual(info2["type"], "Loja")

    def test_identify_vendor_particular(self):
        info_male = identify_vendor("Carlos Alberto Silva")
        self.assertEqual(info_male["type"], "Particular")
        self.assertEqual(info_male["gender"], "Homem")

        info_female = identify_vendor("Mariana Souza")
        self.assertEqual(info_female["type"], "Particular")
        self.assertEqual(info_female["gender"], "Mulher")

        info_unknown = identify_vendor("Xyz123")
        self.assertEqual(info_unknown["type"], "Particular")
        self.assertEqual(info_unknown["gender"], "Não identificado")

    def test_extract_laudo_cautelar(self):
        txt1 = "Veículo impecável com laudo cautelar aprovado sem apontamentos"
        self.assertIn("Aprovado 100%", extract_laudo_cautelar(txt1))

        txt2 = "Carro bom para rodar, laudo com apontamento leve"
        self.assertIn("apontamento", extract_laudo_cautelar(txt2))

        txt3 = "Carro muito novo, aceito troca"
        self.assertEqual(extract_laudo_cautelar(txt3), "Não informado no anúncio")

    def test_history_status(self):
        # Leilão explícito descartado
        bad1, reason1 = extract_history_status("Passagem por leilão de seguradora")
        self.assertTrue(bad1)

        # Sinistro recuperado descartado
        bad2, reason2 = extract_history_status("Veículo recuperado no documento")
        self.assertTrue(bad2)

        # Sem leilão / Sem sinistro certificado
        good1, reason_good = extract_history_status("Sem leilão, sem sinistro, leilão não")
        self.assertFalse(good1)
        self.assertIn("Sem histórico", reason_good)

        # Não mencionado
        neutral, reason_neutral = extract_history_status("Carro excelente, segundo dono")
        self.assertFalse(neutral)
        self.assertEqual(reason_neutral, "Não informado no anúncio")

    def test_evaluate_optionals_rigor(self):
        text = "Mitsubishi ASX HPE AWD com Teto Solar Elétrico Skyview, bancos em couro, multimidia com camera de ré e sensor de estacionamento, ar condicionado digital"
        opts = evaluate_optionals(text)
        self.assertTrue(opts["sunroof"])
        self.assertTrue(opts["rear_camera"])
        self.assertTrue(opts["parking_sensor"])
        self.assertTrue(opts["multimedia"])
        self.assertTrue(opts["ac"])
        self.assertTrue(opts["awd"])

    def test_calculate_score(self):
        opts = {
            "sunroof": True,
            "rear_camera": True,
            "multimedia": True,
            "parking_sensor": True,
            "ac": True,
            "awd": True,
        }
        score, justification = calculate_score(
            price=68000.0,
            km=95000,
            year=2016,
            optionals=opts,
            laudo_status="Aprovado 100% (Sem apontamentos)",
            vendor_info={"type": "Particular", "gender": "Homem", "name": "Carlos"},
        )
        self.assertGreaterEqual(score, 7.5)
        self.assertLessEqual(score, 10.0)
        self.assertIn("Teto Solar", justification)


if __name__ == "__main__":
    unittest.main()
