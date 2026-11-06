# Auditoria final do PR #1

Comparado com `origin/master`; commit de recuperação `8ceb71b` preservado.

## Defeitos reproduzidos e corrigidos

- Filiais com mesmo nome e sem endereço eram fundidas antes da leitura dos detalhes. A chave agora considera identidade da URL, preservando filiais distintas.
- O mesmo lugar retornado em cidades de busca diferentes podia ser duplicado. URLs normalizadas e parâmetros de tracking conhecidos não geram duplicatas.
- Nomes com `:` perdiam o prefixo na leitura do h1. O nome completo é preservado.
- Bloqueio com h1 podia ser exportado como nome de empresa. Sinais de intervenção são verificados antes e durante esperas/extração; o fluxo encerra sem interação com a proteção.
- Controles XML inválidos causavam `IllegalCharacterError` no XLSX. São removidos antes da proteção contra fórmulas.
- Cartões presentes mas ilegíveis geram erro de seletor em vez de resultado vazio silencioso.

## Evidências

- Testes originais + regressões: **15 aprovados**.
- `MAPS_BROWSER_FIXTURE=1` e `python -m unittest discover -s tests -p test_browser_fixture.py -v`: **1 integração Chrome headless aprovada**, somente localhost. Fixture com cartões duplicados, duas filiais com mesmo nome, terceira filial carregada após scroll, painéis de detalhe, exportação XLSX lida de volta e bloqueio sintético.
- Todas as navegações da fixture são restringidas pelo teste a localhost; nenhuma nova coleta no Maps foi executada.
- `pip check` e `git diff --check`: aprovados; dependências preservadas.
- A consulta real de três registros é evidência histórica do checkpoint 02, não foi tratada como teste atual da interface.

## Restrições e decisão

[Termos adicionais do Maps](https://www.google.com/help/terms_maps/), consultados em 2026-11-05: seção 2 restringe copiar conteúdo salvo permissões/exceções e downloads em massa. A ausência de bypass não demonstra autorização para copiar/exportar listagens. Não foi demonstrada permissão específica para esta finalidade.

**GO técnico para merge como PoC**, seguindo a direção de manter o projeto. **Sem GO de conformidade para operação de coleta/exportação**: essa ressalva permanece explícita no README e PR. A fixture não garante estabilidade dos seletores ao vivo. Nenhum CAPTCHA, bloqueio ou autenticação foi contornado. PR permanece draft para decisão do proprietário.

## Preparação para integração

O CI executa os testes locais sem acessar o Maps; a fixture opcional com Chrome não é executada no CI. Seletores atuais e conformidade de coleta/exportação não são homologados por esse CI.
