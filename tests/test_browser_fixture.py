"""Optional real-Chrome test; all application navigation stays on localhost."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import tempfile
from threading import Thread
import unittest

from openpyxl import load_workbook

from scraper_google_maps import Business, buscar_empresas, enriquecer_empresa, exportar_excel, iniciar_navegador


HOME = '''<!doctype html><html><body><input role="combobox"><div role="feed" style="display:none;height:120px;overflow:auto"></div>
<script>
const input=document.querySelector('input'),feed=document.querySelector('[role=feed]');
const card=id=>`<article role="article" style="height:100px"><a href="/maps/place/${id}" aria-label="Empresa Audit">Empresa Audit</a></article>`;
let appended=false;
input.addEventListener('keydown',event=>{if(event.key==='Enter'){feed.style.display='block';feed.innerHTML=card('a')+card('a')+card('b')}});
feed.addEventListener('scroll',()=>{if(!appended){appended=true;feed.insertAdjacentHTML('beforeend',card('c'))}});
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/maps/place/'):
            branch = self.path.rsplit('/', 1)[-1].upper()
            body = f'<h1>Café: Unidade {branch}</h1><div aria-label="Endereço: Rua Audit {branch}"></div><div aria-label="Telefone: +55 47 3333-1234"></div><div aria-label="Categoria: Cafeteria"></div>'
        elif self.path == '/blocked':
            body = '<h1>Unusual traffic</h1><form id="captcha-form">Our systems have detected unusual traffic from your computer network.</form>'
        else:
            body = HOME
        encoded = body.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *_):
        pass


@unittest.skipUnless(os.getenv('MAPS_BROWSER_FIXTURE') == '1', 'set MAPS_BROWSER_FIXTURE=1 for local Chrome integration')
class BrowserFixtureTests(unittest.TestCase):
    def test_search_scroll_details_export_and_blocking(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        browser = iniciar_navegador(headless=True)

        class LocalDriver:
            def get(self, url):
                if url == 'https://www.google.com/maps':
                    url = base + '/'
                if not url.startswith(base + '/'):
                    raise AssertionError('External navigation is forbidden in the fixture')
                browser.get(url)

            def __getattr__(self, name):
                return getattr(browser, name)

        try:
            driver = LocalDriver()
            records = buscar_empresas('Synthetic City', 'Synthetic Term', driver, max_results=3)
            self.assertEqual([r.name for r in records], ['Café: Unidade A', 'Café: Unidade B', 'Café: Unidade C'])
            self.assertTrue(all(r.phone == '(47) 3333-1234' and r.address and r.business_type for r in records))
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'fixture.xlsx'
                self.assertEqual(exportar_excel(records, path), 3)
                workbook = load_workbook(path)
                self.assertEqual(workbook.active.max_row, 4)
                workbook.close()
            with self.assertRaises(RuntimeError):
                enriquecer_empresa(driver, Business('old', '', '', '', '', '', base + '/blocked'))
        finally:
            browser.quit()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
