# Google Maps Leads (recuperação pendente)

Este repositório contém um protótipo antigo de Selenium que pesquisa no Google Maps, copia listagens de empresas e as grava em Excel. **Não execute o coletor atual.** A coleta/exportação pretendida não foi validada como compatível com os termos atuais do serviço.

## Estado da coleta

Os [termos adicionais do Google Maps](https://www.google.com/help/terms_maps/) proíbem copiar conteúdo e criar downloads em massa. Os [termos do Google Maps Platform](https://cloud.google.com/maps-platform/terms) também proíbem scraping e copiar/salvar nomes e endereços de empresas fora dos serviços. Uma API oficial não autoriza automaticamente exportar esses dados para uma planilha.

Para retomar o projeto, substitua a origem por um provedor ou conjunto de dados cuja licença permita expressamente a extração e a exportação pretendidas. Até lá, a busca real está pendente. Nenhuma consulta ao Google Maps foi executada nesta recuperação.

## Estado técnico conhecido

- O script usa seletores internos sujeitos a mudanças e não implementa rolagem/paginação confiável.
- A execução começa durante a importação do arquivo Python, abrindo prompts e inicializando o navegador.
- A saída XLSX ainda não foi validada quanto a duplicatas, conteúdo interpretado como fórmula ou abertura em leitores de planilha.
- As dependências não têm lockfile nem testes automatizados.

Esses pontos deverão ser tratados após a escolha de uma origem de dados permitida. Não foi feita atualização de Selenium nem ajustes nos seletores porque isso operacionalizaria a extração de listagens do Maps.

## Uso responsável

Use apenas fontes e dados que você tenha autorização para coletar e exportar. Dados disponíveis publicamente não estão automaticamente liberados para cópia ou criação de listas. Respeite os termos do provedor, a legislação de proteção de dados (LGPD) e não utilize dados para spam ou finalidade abusiva.
