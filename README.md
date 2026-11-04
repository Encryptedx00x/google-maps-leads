# Prospecção automática no Google Maps

Ferramenta em Python que automatiza a busca de estabelecimentos no Google Maps a partir de
palavras-chave e cidades, e exporta os resultados (nome, telefone, tipo e endereço) para uma
planilha Excel. Útil para montar listas de prospecção comercial a partir de dados públicos.

## Como funciona

1. Abre o Google Maps no navegador (Selenium + Chrome).
2. Para cada combinação de **palavra-chave × cidade**, pesquisa e lê os resultados visíveis.
3. Extrai nome, telefone (quando exibido), tipo de estabelecimento e endereço.
4. Salva tudo em um arquivo `.xlsx` com nome único.

## Requisitos

- Python 3.10+
- Google Chrome instalado
- Dependências: `pip install -r requirements.txt`
  (o driver do Chrome é baixado automaticamente pelo `webdriver-manager`)

## Como usar

```bash
python scraper_google_maps.py
```

O script pergunta se você quer usar as **cidades** e as **palavras-chave** padrão (exemplo do
ramo de logística em Santa Catarina) ou digitar as suas, separadas por vírgula. Para mudar os
padrões, edite as listas `termos_busca_padrao` e `cidades_padrao` no fim do arquivo.

## Limitações conhecidas

- Lê apenas os primeiros resultados carregados de cada busca (não rola a lista automaticamente).
- Depende dos nomes internos de classe do Google Maps, que mudam com frequência e podem exigir ajuste nos seletores.
- É uma ferramenta de automação de navegador, não a API oficial do Google.

## Uso responsável

Use apenas para fins legítimos de prospecção, respeitando os
[Termos de Serviço do Google](https://policies.google.com/terms) e a legislação de proteção de
dados (LGPD). Os dados coletados são públicos; trate-os com responsabilidade e não os utilize
para spam ou qualquer finalidade abusiva.
