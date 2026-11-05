import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook
from selenium.webdriver.common.by import By

from scraper_google_maps import Business, deduplicar_empresas, enriquecer_empresa, exportar_excel


def record(url='https://www.google.com/maps/place/A', city='Test City'):
    return Business('Same business name', '', '', '', city, 'term', url)


class Element:
    def __init__(self, text):
        self.text = text

    def get_attribute(self, name):
        return None


class Driver:
    def __init__(self, title, body=''):
        self.title, self.body = title, body
        self.current_url = ''

    def get(self, url):
        self.current_url = url

    def find_elements(self, by, selector):
        if (by, selector) == (By.CSS_SELECTOR, 'h1'):
            return [Element(self.title)]
        if (by, selector) == (By.TAG_NAME, 'body'):
            return [Element(self.body)]
        return []


class FinalAuditTests(unittest.TestCase):
    def test_distinct_branches_without_addresses_are_not_merged(self):
        self.assertEqual(len(deduplicar_empresas([record(), record('https://www.google.com/maps/place/B')])), 2)

    def test_same_place_found_in_two_search_cities_is_not_duplicated(self):
        self.assertEqual(len(deduplicar_empresas([record(), record(city='Other City')])), 1)

    def test_tracking_parameters_do_not_create_duplicates(self):
        self.assertEqual(len(deduplicar_empresas([record('?unused'), record('?unused')])), 1)
        a = record('https://www.google.com/maps/place/A?entry=ttu')
        b = record('https://www.google.com/maps/place/A?entry=other')
        self.assertEqual(len(deduplicar_empresas([a, b])), 1)

    def test_details_preserve_colon_in_business_name(self):
        self.assertEqual(enriquecer_empresa(Driver('Café: Unidade A'), record()).name, 'Café: Unidade A')

    def test_human_intervention_page_is_not_exported_as_business(self):
        with self.assertRaises(RuntimeError):
            enriquecer_empresa(Driver('Unusual traffic', 'Our systems have detected unusual traffic from your computer network.'), record())

    def test_workbook_handles_invalid_xml_control_characters(self):
        row = Business('\x00=1+1', '', '', 'Address\x01', 'City', 'Term', 'url')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.xlsx'
            exportar_excel([row], path)
            book = load_workbook(path)
            self.assertEqual(book.active['A2'].value, "'=1+1")
            self.assertEqual(book.active['D2'].value, 'Address')
            book.close()
