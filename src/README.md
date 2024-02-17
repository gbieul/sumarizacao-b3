# Procedimentos para execução dos processos de extração textual

Esse trabalho atuou em duas etapas: a primeira se voltou a converter os arquivos PDFs obtidos originalmente em JSONs, com o uso da API Extract PDF da Adobe.

A segunda se tratou de transformar esses JSONs em arquivos formato texto puro (txt).

Recomenda-se usar um ambiente virtual para esta etapa:

1. `python -m venv /path/para/virtual/environment`

2. Ative o ambiente virtual de acordo com seu SO:

| SO        | Shell     | Comando para ativação                          |
|-----------|-----------|------------------------------------------------|
| POSIX     | bash/zsh  | `$ source /path/para/virtual/environment/bin/activate`                 |
|           | fish      | `$ source /path/para/virtual/environment/bin/activate.fish`            |
|           | csh/tcsh  | `$ source /path/para/virtual/environment/bin/activate.csh`             |
| PowerShell|           | `$ /path/para/virtual/environment/bin/Activate.ps1`                    |
| Windows   | cmd.exe   | `C:\> \path\para\virtual\environment\Scripts\activate.bat`             |
|           | PowerShell| `PS C:\> \path\para\virtual\environment\Scripts\Activate.ps1`          |

3. Instale os requerimentos com `pip install -r ./requirements_extract.txt`

## Extração dos PDFs para JSON
A fim de se executar o processo para extrair textos dos PDFs obtidos, pode-se executar o comando:
`python extract_pdf.py pdf-to-json -i <diretorio_dos_pdfs> -o <diretorio_para_saida_dos_jsons>`

## Extração dos JSONs para TXT
A fim de se executar o processo para extrair textos dos PDFs obtidos, pode-se executar o comando:
`python extract_pdf.py json-to-txt -i <diretorio_de_saida_dos_jsons> -o <diretorio_para_saida_dos_txt>`