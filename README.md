# Prospecção local com Google Maps (PoC)

Protótipo Python/Selenium que pesquisa pequenos lotes de estabelecimentos por termo e cidade no Google Maps e grava os campos visíveis em XLSX. O escopo continua sendo pesquisa manual e volume baixo; não tenta contornar CAPTCHA, autenticação, limites ou bloqueios do site.

## Requisitos

- Python 3.10 ou superior (validado com Python 3.13.14 no Windows).
- Google Chrome instalado.
- Dependências bloqueadas em `requirements-lock.txt`.

## Instalação no Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
```

Selenium Manager resolve o driver compatível com o Chrome quando o navegador inicia pela primeira vez. Não é necessário instalar ChromeDriver manualmente nem usar `webdriver-manager`.

## Executar uma busca pequena

```powershell
python scraper_google_maps.py `
  --cities Navegantes `
  --terms padaria `
  --max-results 5 `
  --output output\padarias.xlsx `
  --headless
```

`--cities` e `--terms` aceitam listas separadas por vírgulas. `--max-results` é um limite global por execução, de 1 a 50. Se o arquivo de saída já existir, o programa escolhe um nome com sufixo numérico; use `--overwrite` para substituir deliberadamente. Sem argumentos, usa termos e cidades de exemplo definidos no script.

O navegador aguarda a caixa de pesquisa e o painel de resultados por condições explícitas. A lista rola até atingir o limite ou deixar de carregar novos cartões. Os resultados são deduplicados por nome/endereço/cidade. Tipo, endereço e telefone ficam em branco quando a interface não expõe um rótulo reconhecível. Dados iniciados por caracteres que planilhas tratam como fórmula são gravados como texto.

## Validação real desta revisão

Em 2026-11-05 foi executada uma busca pequena em `padaria` / `Navegantes`, com limite de 3 resultados, no Chrome headless. O XLSX abriu corretamente e continha 3 empresas únicas; nome, telefone, categoria, endereço, cidade, termo e link estavam preenchidos nos três registros. Essa execução comprova apenas essa consulta e os rótulos presentes naquele momento.
## Testes locais

```powershell
python -m unittest discover -s tests -v
```

Os testes usam cartões sintéticos e não navegam até o Google Maps. Uma busca real pequena depende da disponibilidade da interface e da rede; se a página solicitar intervenção humana, o programa encerra sem tentar contorná-la.

## Limitações da PoC

- A interface interna do Maps pode mudar; seletores e rótulos acessíveis podem deixar de corresponder.
- Os campos disponíveis variam entre estabelecimentos e resultados.
- O protótipo lê resultados visíveis do site e não oferece garantia de cobertura, precisão ou estabilidade.
- Os termos de uso do provedor podem restringir extração, armazenamento e exportação. Este projeto não representa uma integração oficial nem uma avaliação de conformidade; revise as condições aplicáveis ao seu uso antes de operar.
- Não grave arquivos de resultados no Git. `.xlsx` está ignorado pelo repositório.
