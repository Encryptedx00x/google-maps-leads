"""Small Selenium PoC for manually initiated Google Maps searches."""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse, urlunparse

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

DEFAULT_TERMS = (
    "Transportadora", "CD", "Centro de Distribuição", "Logística", "Galpão",
    "Transportes", "Importação", "Exportação", "Armazéns gerais", "Distribuidora",
)
DEFAULT_CITIES = ("Navegantes", "Itajaí", "Blumenau")
MAX_RESULTS = 50
MAX_SCROLL_STALLS = 3


@dataclass(frozen=True)
class Business:
    name: str
    phone: str
    business_type: str
    address: str
    city: str
    search_term: str
    maps_url: str


def iniciar_navegador(headless: bool = False) -> webdriver.Chrome:
    """Create Chrome using Selenium Manager; no separate driver download is needed."""
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1280,1000")
    options.add_argument("--lang=pt-BR")
    options.add_argument("--disable-notifications")
    if headless:
        options.add_argument("--headless=new")
    return webdriver.Chrome(options=options)


def formatar_telefone(telefone: str) -> str:
    original = (telefone or "").strip()
    digits = re.sub(r"\D", "", original)
    if digits.startswith("55") and len(digits) in (12, 13):
        digits = digits[2:]
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    return original


def _normalizar(texto: str) -> str:
    folded = unicodedata.normalize("NFKD", (texto or "").casefold())
    return " ".join("".join(c for c in folded if not unicodedata.combining(c)).split())


def _label_value(labels: Iterable[str], prefixes: tuple[str, ...]) -> str:
    for label in labels:
        normalized = _normalizar(label)
        for prefix in prefixes:
            if normalized.startswith(_normalizar(prefix)):
                return label.split(":", 1)[-1].strip()
    return ""


def _element_text(driver, selectors: tuple[str, ...]) -> str:
    for selector in selectors:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            value = (element.get_attribute("aria-label") or element.text or "").strip()
            if value:
                return value.split(":", 1)[-1].strip() if ":" in value else value
    return ""


def enriquecer_empresa(driver, business: Business, timeout: int = 10) -> Business:
    """Read public labels from a result's Maps details panel/page, without interacting with controls."""
    driver.get(business.maps_url)
    try:
        WebDriverWait(driver, timeout).until(
            lambda browser: browser.find_elements(By.CSS_SELECTOR, "h1")
        )
    except TimeoutException:
        body = " ".join(element.text for element in driver.find_elements(By.TAG_NAME, "body"))
        if re.search(r"captcha|unusual traffic|automated queries|tráfego incomum|prove que você é humano", body, re.IGNORECASE):
            raise RuntimeError("O Maps pediu intervenção humana; a PoC encerrou sem tentar contornar o bloqueio.")
        return business

    labels = [
        element.get_attribute("aria-label") or ""
        for element in driver.find_elements(By.CSS_SELECTOR, "[aria-label]")
    ]
    name = _element_text(driver, ("h1",)) or business.name
    address = (
        _label_value(labels, ("Address:", "Endereço:"))
        or _element_text(driver, ('[data-item-id="address"]',))
        or business.address
    )
    phone = (
        _label_value(labels, ("Phone:", "Telefone:"))
        or _element_text(driver, ('[data-item-id^="phone"]',))
        or business.phone
    )
    business_type = (
        _label_value(labels, ("Category:", "Categoria:", "Business type:", "Tipo:"))
        or _element_text(driver, ('button[jsaction*="pane.rating.category"]',))
        or _element_text(driver, (".DkEaL",))
        or business.business_type
    )
    return replace(
        business,
        name=name,
        phone=formatar_telefone(phone),
        business_type=business_type,
        address=address,
    )


def extrair_empresa(card, cidade: str, termo_busca: str) -> Business | None:
    """Read one visible Maps result card using accessibility labels where available."""
    try:
        links = card.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
    except (AttributeError, WebDriverException):
        links = []
    link = links[0] if links else card
    try:
        maps_url = (link.get_attribute("href") or "").strip()
        link_label = (link.get_attribute("aria-label") or "").strip()
        card_text = (card.text or "").strip()
        aria_elements = card.find_elements(By.CSS_SELECTOR, "[aria-label]")
        labels = [element.get_attribute("aria-label") or "" for element in aria_elements]
    except (AttributeError, WebDriverException):
        maps_url, link_label, card_text, labels = "", "", "", []

    name = link_label or next((line.strip() for line in card_text.splitlines() if line.strip()), "")
    if not name or not maps_url:
        return None

    phone = _label_value(labels, ("Phone:", "Telefone:"))
    if not phone:
        match = re.search(r"(?<!\d)(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?\d{4,5}[\s-]?\d{4}(?!\d)", card_text)
        phone = match.group(0) if match else ""
    phone = formatar_telefone(phone)

    business_type = _label_value(labels, ("Category:", "Categoria:", "Business type:", "Tipo:"))
    address = _label_value(labels, ("Address:", "Endereço:"))
    return Business(
        name=name,
        phone=phone,
        business_type=business_type,
        address=address,
        city=cidade.strip(),
        search_term=termo_busca.strip(),
        maps_url=maps_url,
    )


def deduplicar_empresas(empresas: Iterable[Business]) -> list[Business]:
    unique: list[Business] = []
    seen: set[tuple[str, str, str]] = set()
    for business in empresas:
        key = (_normalizar(business.name), _normalizar(business.address), _normalizar(business.city))
        if key in seen:
            continue
        seen.add(key)
        unique.append(business)
    return unique


def _result_links(feed):
    try:
        return feed.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
    except StaleElementReferenceException:
        return []


def encontrar_caixa_pesquisa(driver, wait: WebDriverWait):
    """Prefer the current accessible combobox, with the older Maps ID as fallback."""
    locators = (
        (By.CSS_SELECTOR, 'input[role="combobox"]'),
        (By.ID, "searchboxinput"),
    )

    def visible_input(browser):
        for locator in locators:
            for element in browser.find_elements(*locator):
                if element.is_displayed() and element.is_enabled():
                    return element
        return False

    return wait.until(visible_input)


def buscar_empresas(cidade: str, termo_busca: str, driver, max_results: int = 10) -> list[Business]:
    if not cidade.strip() or not termo_busca.strip():
        raise ValueError("Cidade e termo de busca são obrigatórios.")
    if not 1 <= max_results <= MAX_RESULTS:
        raise ValueError(f"max_results deve estar entre 1 e {MAX_RESULTS}.")

    driver.get("https://www.google.com/maps")
    wait = WebDriverWait(driver, 20)
    search_box = encontrar_caixa_pesquisa(driver, wait)
    search_box.clear()
    search_box.send_keys(f"{termo_busca} em {cidade}")
    search_box.send_keys(Keys.ENTER)
    try:
        feed = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="feed"]')))
    except TimeoutException:
        if driver.find_elements(By.XPATH, "//*[contains(., 'No results') or contains(., 'Nenhum resultado')]"):
            return []
        raise RuntimeError("Lista de resultados não apareceu; a interface pode ter mudado ou pedido intervenção.")

    businesses: list[Business] = []
    seen: set[tuple[str, str, str]] = set()
    stalled = 0
    while len(businesses) < max_results and stalled < MAX_SCROLL_STALLS:
        links = _result_links(feed)
        before_count = len(links)
        for link in links:
            try:
                card = link.find_element(By.XPATH, './ancestor::*[@role="article"][1]')
            except (NoSuchElementException, WebDriverException):
                try:
                    card = link.find_element(By.XPATH, "./..").find_element(By.XPATH, "./..")
                except WebDriverException:
                    card = link
            business = extrair_empresa(card, cidade, termo_busca)
            if business is None:
                continue
            key = (_normalizar(business.name), _normalizar(business.address), _normalizar(business.city))
            if key not in seen:
                seen.add(key)
                businesses.append(business)
                if len(businesses) >= max_results:
                    break
        if len(businesses) >= max_results:
            break

        try:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
            WebDriverWait(driver, 2).until(lambda _driver: len(_result_links(feed)) > before_count)
            stalled = 0
        except TimeoutException:
            stalled += 1
            try:
                feed = driver.find_element(By.CSS_SELECTOR, '[role="feed"]')
            except WebDriverException:
                break
        except StaleElementReferenceException:
            try:
                feed = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[role="feed"]'))
                )
            except TimeoutException:
                break
    return [enriquecer_empresa(driver, business) for business in businesses]


def coletar_buscas(driver, cidades: Iterable[str], termos: Iterable[str], max_results: int) -> list[Business]:
    cities = [value.strip() for value in cidades if value.strip()]
    keywords = [value.strip() for value in termos if value.strip()]
    if not cities or not keywords:
        raise ValueError("Informe ao menos uma cidade e um termo de busca.")
    if not 1 <= max_results <= MAX_RESULTS:
        raise ValueError(f"max_results deve estar entre 1 e {MAX_RESULTS}.")
    businesses: list[Business] = []
    for term in keywords:
        for city in cities:
            businesses = deduplicar_empresas(businesses)
            remaining = max_results - len(businesses)
            if remaining <= 0:
                return businesses[:max_results]
            businesses.extend(buscar_empresas(city, term, driver, max_results=remaining))
    return deduplicar_empresas(businesses)[:max_results]


def _excel_safe(value: str) -> str:
    value = value or ""
    if re.match(r"^[\s\u0000-\u001f]*[=+@-]", value):
        return "'" + value
    return value


def exportar_excel(empresas: Iterable[Business], caminho: Path) -> int:
    rows = list(empresas)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Empresas"
    headers = ("Nome", "Telefone", "Tipo de empresa", "Endereço", "Cidade", "Termo", "Google Maps")
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
    for business in rows:
        sheet.append(tuple(_excel_safe(value) for value in (
            business.name, business.phone, business.business_type, business.address,
            business.city, business.search_term, business.maps_url,
        )))
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for column, width in {"A": 36, "B": 20, "C": 28, "D": 42, "E": 20, "F": 28, "G": 64}.items():
        sheet.column_dimensions[column].width = width
    workbook.save(caminho)
    return len(rows)


def caminho_saida_unico(caminho: Path, overwrite: bool = False) -> Path:
    if overwrite or not caminho.exists():
        return caminho
    for index in range(1, 10000):
        candidate = caminho.with_name(f"{caminho.stem}_{index}{caminho.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError("Não foi possível gerar um nome de arquivo exclusivo.")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PoC Selenium para busca pequena no Google Maps.")
    parser.add_argument("--cities", default=",".join(DEFAULT_CITIES), help="Cidades separadas por vírgula.")
    parser.add_argument("--terms", default=",".join(DEFAULT_TERMS), help="Termos separados por vírgula.")
    parser.add_argument("--max-results", type=int, default=10, help=f"Limite global (1–{MAX_RESULTS}).")
    parser.add_argument("--output", type=Path, default=Path("empresas_logistica.xlsx"))
    parser.add_argument("--overwrite", action="store_true", help="Permite sobrescrever --output.")
    parser.add_argument("--headless", action="store_true", help="Executa Chrome sem janela.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    driver = None
    try:
        output = caminho_saida_unico(args.output, overwrite=args.overwrite)
        driver = iniciar_navegador(headless=args.headless)
        businesses = coletar_buscas(
            driver,
            args.cities.split(","),
            args.terms.split(","),
            max_results=args.max_results,
        )
        count = exportar_excel(businesses, output)
        print(f"{count} resultados únicos salvos em {output}")
        return 0
    except (ValueError, RuntimeError, OSError, WebDriverException) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2
    finally:
        if driver is not None:
            driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
