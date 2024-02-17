# Sumarização de documentos do arcabouço regulatório financeiro brasileiro
Autor: Gabriel Benvegmi  
Orientador: Prof. Dr. Marcos Lopes  
São Paulo, 2024

Esse repositório contém conteúdos relacionados à monografia apresentada ao Programa de Educação Continuada em Engenharia da Escola Politécnica da Universidade de São Paulo como parte dos requisitos para conclusão do curso de Especialização em Inteligência Artificial.

## Como navegar no repositório
- Em `/data` encontram-se os dados usados nesse trabalho, tanto aqueles usados como entrada, quanto aqueles gerados como saída;
- Em `/notebooks` estão os notebooks em formato ipynb, gerados no Google Colab, que facilitaram a realização desse trabalho;
- E em `/src` estão presentes os códigos-fonte para os processos de web-scraping e extração dos textos a partir dos PDFs.

Detalhamentos maiores estão nas Seções abaixo.

### Notebooks
Os arquivos presentes em `/notebooks` estão numerados de acordo com a ordem lógica de seu uso ao longo deste trabalho e, portanto, podem ser entendidos como partes sequenciais deste. Os notebooks que estão aqui apresentados são:

0. Webscraping dos dados da B3
1. Preparação dos dados da B3
2. Análises de Convergência e Índice de Coleman Liau
3. Treinamento e geração

### Scripts
Os arquivos com a lógica de partes do processamento estão em `/src`. Eles são:
- scraper_pdf.py
  - Esse arquivo contém a lógica de funcionamento dos processos de webscraping mas aqui sem necessariamente depender de um notebook para sua execução.
- extract_pdf.py
  - Já aqui estão os processos para extração e processamento dos textos a partir dos PDFs para JSON, e a partir de JSON para TXT. 

Instruções para execução da extração textual estão no README dentro do diretório `/src`.

### Dados
O dataset padrão ouro consolidado a partir da atuação de avaliadores humados com a criação de sumários de referência encontra-se em `/data/dataset.csv`. As saídas geradas pelos modelos estão em `/data/outputs`, com cada arquivo representando um dos modelos Bode, Mistral e T5, respectivamente.

- PDF
  - Aqui estão os arquivos em formato PDF baixados a partir do site da B3. 
- JSON
  - Já neste diretório estão as correspondências dos arquivos baixados em PDF, mas agora convertidos pela API Extract PDF da Adobe. 
- txt
  - Finalmente aqui estão os JSONs pós-processados de forma a consolidar um único txt para cada documento original. 

### Citações
Esse trabalho pode ser referenciado no formato Bibtex conforme a seguir.
```
@monography{benvegmi2024,
 address={São Paulo},
 author={Gabriel Benvegmi},
 pages={49},
 pagename={f.},
 school={Universidade de São Paulo},
 title={Sumarização de documentos do arcabouço regulatório financeiro brasileiro},
 type={Especialização},
 year={2024},
 url={https://github.com/gbieul/sumarizacao-b3}
}
```
