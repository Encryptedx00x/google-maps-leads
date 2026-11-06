import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from openpyxl import load_workbook
from selenium.webdriver.common.by import By
from scraper_google_maps import (
    Business,
    caminho_saida_unico,
    coletar_buscas,
    deduplicar_empresas,
    exportar_excel,
    extrair_empresa,
    formatar_telefone,
    enriquecer_empresa,
    encontrar_caixa_pesquisa,
)


class FakeElement:
    def __init__(self, *, href="", aria="", text="", children=None):
        self.href = href
        self.aria = aria
        self.text = text
        self.children = children or {}

    def get_attribute(self, name):
        return {"href": self.href, "aria-label": self.aria}.get(name)

    def find_elements(self, by, selector):
        return self.children.get(selector, [])


class FakeSearchInput(FakeElement):
    def is_displayed(self):
        return True

    def is_enabled(self):
        return True


class FakeWait:
    def until(self, condition):
        return condition(self.driver)

    def __init__(self, driver):
        self.driver = driver


class FakeSearchDriver:
    def __init__(self, inputs):
        self.inputs = inputs

    def find_elements(self, by, selector):
        return self.inputs.get((by, selector), [])


class MapsParsingTests(unittest.TestCase):
    def test_search_uses_accessible_combobox_before_legacy_id(self):
        current = FakeSearchInput()
        legacy = FakeSearchInput()
        driver = FakeSearchDriver({
            (By.CSS_SELECTOR, 'input[role="combobox"]'): [current],
            (By.ID, "searchboxinput"): [legacy],
        })
        self.assertIs(encontrar_caixa_pesquisa(driver, FakeWait(driver)), current)
    def test_phone_formats_brazilian_numbers_and_preserves_unrecognized_values(self):
        self.assertEqual(formatar_telefone("+55 (47) 99999-1234"), "(47) 99999-1234")
        self.assertEqual(formatar_telefone("4733331234"), "(47) 3333-1234")
        self.assertEqual(formatar_telefone("abc"), "abc")

    def test_extracts_accessible_name_phone_type_address_and_url(self):
        labels = [
            FakeElement(aria="Telefone: +55 47 99999-1234"),
            FakeElement(aria="Categoria: Padaria"),
            FakeElement(aria="Endereço: Rua Teste, 10"),
        ]
        link = FakeElement(href="https://www.google.com/maps/place/Padaria+Teste", aria="Padaria Teste")
        card = FakeElement(text="Padaria Teste\nPadaria · Aberto", children={
            'a[href*="/maps/place/"]': [link],
            "[aria-label]": labels,
        })
        business = extrair_empresa(card, "Navegantes", "padaria")
        self.assertEqual(business.name, "Padaria Teste")
        self.assertEqual(business.phone, "(47) 99999-1234")
        self.assertEqual(business.business_type, "Padaria")
        self.assertEqual(business.address, "Rua Teste, 10")
        self.assertEqual(business.maps_url, link.href)

    def test_details_page_enriches_fields_from_accessible_labels(self):
        business = Business("Padaria Teste", "", "", "", "Navegantes", "padaria", "https://maps.example/place")
        elements = {
            (By.CSS_SELECTOR, "h1"): [FakeElement(text="Padaria Teste Ltda")],
            (By.CSS_SELECTOR, "[aria-label]"): [
                FakeElement(aria="Endereço: Avenida Central, 55"),
                FakeElement(aria="Telefone: +55 47 3333-1234"),
            ],
            (By.CSS_SELECTOR, ".DkEaL"): [FakeElement(text="Cafeteria")],
        }
        class FakeDetailsDriver:
            def get(self, _url):
                pass
            def find_elements(self, by, selector):
                return elements.get((by, selector), [])
        enriched = enriquecer_empresa(FakeDetailsDriver(), business)
        self.assertEqual(enriched.name, "Padaria Teste Ltda")
        self.assertEqual(enriched.address, "Avenida Central, 55")
        self.assertEqual(enriched.phone, "(47) 3333-1234")
        self.assertEqual(enriched.business_type, "Cafeteria")
    def test_missing_name_or_place_url_is_skipped(self):
        card = FakeElement(text="Sem link de lugar")
        self.assertIsNone(extrair_empresa(card, "Navegantes", "teste"))

    def test_duplicate_results_are_removed_case_insensitively(self):
        first = Business("Padaria Teste", "", "", "Rua A", "Navegantes", "padaria", "url-1")
        duplicate = Business("  PADARIA teste ", "47 3333-1234", "Padaria", "Rua A", "NAVEGANTES", "pão", "url-2")
        other_address = Business("Padaria Teste", "", "", "Rua B", "Navegantes", "padaria", "url-3")
        self.assertEqual(deduplicar_empresas([first, duplicate, other_address]), [first, other_address])

    def test_search_plan_respects_global_result_cap_and_deduplicates_between_queries(self):
        shared = Business("Empresa", "", "", "Rua A", "Navegantes", "termo 1", "url")
        second = Business("Empresa B", "", "", "Rua B", "Navegantes", "termo 2", "url2")
        calls = []
        def search(city, term, _driver, max_results):
            calls.append((city, term, max_results))
            return [shared] if term == "termo 1" else [shared, second]
        with patch("scraper_google_maps.buscar_empresas", side_effect=search):
            results = coletar_buscas(object(), ["Navegantes"], ["termo 1", "termo 2"], 2)
        self.assertEqual([item.name for item in results], ["Empresa", "Empresa B"])
        self.assertEqual(calls, [("Navegantes", "termo 1", 2), ("Navegantes", "termo 2", 1)])


class WorkbookTests(unittest.TestCase):
    def test_xlsx_is_readable_and_formula_like_text_is_stored_as_text(self):
        record = Business("=HYPERLINK(\"https://bad\")", "+47", "@type", "-address", "Navegantes", "+term", "https://maps.example/place")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "leads.xlsx"
            self.assertEqual(exportar_excel([record], path), 1)
            workbook = load_workbook(path, data_only=False)
            sheet = workbook["Empresas"]
            self.assertEqual(sheet.max_row, 2)
            self.assertEqual(sheet["A2"].value, "'=HYPERLINK(\"https://bad\")")
            self.assertNotEqual(sheet["A2"].data_type, "f")
            self.assertEqual(sheet["C2"].value, "'@type")
            self.assertEqual(sheet["A1"].value, "Nome")
            self.assertEqual(sheet.freeze_panes, "A2")
            self.assertEqual(sheet.auto_filter.ref, "A1:G2")

    def test_unique_output_path_avoids_overwriting_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.xlsx"
            path.touch()
            self.assertEqual(caminho_saida_unico(path), path.with_name("results_1.xlsx"))
            self.assertEqual(caminho_saida_unico(path, overwrite=True), path)


if __name__ == "__main__":
    unittest.main()
