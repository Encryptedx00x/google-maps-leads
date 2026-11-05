# Recovery checkpoint 02 — Maps PoC retained and modernized

## Direção do usuário

Em 2026-11-05, o usuário orientou manter a PoC baseada no Google Maps e não trocar a fonte. A restrição de termos registrada no checkpoint 01 permanece como informação contextual, mas não foi usada para bloquear a implementação solicitada. Nenhum CAPTCHA, autenticação, limite ou bloqueio foi contornado; a busca foi manualmente iniciada pela CLI, com limite de três resultados.

## Alterações

- Atualizado Selenium para 4.52.0; Selenium Manager resolve o ChromeDriver. Removido `webdriver-manager` e pandas; XLSX passa a usar apenas openpyxl 3.1.5.
- Eliminados prompts, criação do navegador e busca durante import; adicionado CLI com cidades, termos, limite global, saída, modo headless e opção explícita de overwrite.
- Trocado o seletor obsoleto `#searchboxinput` pelo `input[role=combobox]`, com fallback. A primeira tentativa real demonstrou que o seletor antigo já não existe (`searchboxinput: 0`); o seletor acessível passou a funcionar.
- Adicionadas esperas explícitas, rolagem limitada por crescimento dos resultados, leitura de até 50 itens, deduplicação por nome/endereço/cidade e leitura do painel público de detalhes para telefone/categoria/endereço.
- Adicionada exportação XLSX formatada, com proteção contra fórmulas em texto e sem sobrescrita por padrão. `.xlsx` e `work/` ficam fora do Git.

## Evidências

- Suíte final: `python -m unittest discover -s tests -v` — 9 testes aprovados.
- `pip check` limpo; lock reproduzível por dry-run; `pip-audit -r requirements-lock.txt` sem vulnerabilidades conhecidas; `git diff --check` limpo.
- Execução real em Chrome 156.0.8078.80 / Selenium 4.52.0, Python 3.13.14: busca única pequena de `padaria` em `Navegantes`, limite 3, modo headless; produziu 3 resultados únicos. O XLSX foi aberto com openpyxl; nome, telefone, categoria, endereço, cidade, termo e link estavam preenchidos em todas as três linhas.
- O artefato de teste foi local a `work/maps-probe.xlsx` e não será commitado.

Status: **FUNCIONAL E VALIDADO** como PoC de UI no escopo escolhido pelo usuário. A interface do site pode mudar e os resultados de uma consulta não garantem cobertura ou precisão futuras.
