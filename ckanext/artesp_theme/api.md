# **Manual Detalhado da API do CKAN**

Este manual fornece um guia completo sobre como interagir com a API do CKAN, com exemplos práticos utilizando o domínio https\://dadosabertos.artesp.sp.gov.br. A API Action do CKAN é uma interface poderosa no estilo RPC (Remote Procedure Call) que expõe todas as funcionalidades principais do CKAN, permitindo que aplicações externas gerenciem datasets, recursos, grupos, organizações e muito mais.


## **Sumário**

- [1. Introdução à API Action](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.rixets6mwyzg)

* [Estrutura da Resposta JSON](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.z6j97ayfuvhy)

- [2. Versão da API](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.ivdddfphpazx)

- [3. Autenticação](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.5gpy9s9kejzs)

- [4. Ações Comuns da API (Exemplos)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.sglhmekwt5cd)

* [4.1. Listar Objetos](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.s9eiyz2ufcri)

- [a) Listar Datasets (Pacotes) (package\_list)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.pac0egcmo17c)

- [b) Listar Grupos (group\_list)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.jdzyhtl3kcib)

- [c) Listar Organizações (organization\_list)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.g9ubqbdokdfw)

- [d) Listar Tags (tag\_list)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.ld26lt9i5tbm)

* [4.2. Mostrar Detalhes de um Objeto](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.twklyf2z51xt)

- [a) Mostrar Detalhes de um Dataset (package\_show)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.d7jz72a2i2vr)

- [b) Mostrar Detalhes de um Recurso (resource\_show)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.kvkchksflamn)

* [4.3. Pesquisar Objetos](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.996z3k17lwds)

- [a) Pesquisar Datasets (package\_search)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.1h119hos9zep)

* [4.4. Criar Objetos (Requer Autenticação)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.3bc34r1zuux9)

- [a) Criar um Dataset (package\_create)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.z20al71kcj4q)

* [4.5. Atualizar Objetos (Requer Autenticação)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.l6hrld6tvmzh)

- [a) Atualizar um Dataset (package\_update)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.7vwmqcrzu0va)

- [b) Atualizar Parcialmente um Dataset (package\_patch)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.hp56mp7yb5mg)

- [c) Atualizar um Recurso (resource\_update ou resource\_patch)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.7ts23g7a3dvg)

* [4.6.](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.a558o9jzykzf) Deletar Objetos[ (Requer Autenticação)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.a558o9jzykzf)

- [a)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.o8imu3cm3ur5) Deletar[ um Dataset (package\_delete)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.o8imu3cm3ur5)

- [b)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.dbwicl5wu2b8) Deletar um[ Recurso (resource\_delete)](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.dbwicl5wu2b8)

* [5. Upload de Arquivos para Recursos](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.s2tiylld42g)

* [6. CLI ckanapi e Módulo Python](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.hb7tma4t82bt)

* [7. Dicas e Boas Práticas](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.uzntw6rxrbpb)

* [8. Guia Rápido de Ações da API](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.afok0vacp72t)

- [8.1. Tabela Resumo das Ações](https://docs.google.com/document/d/1q4hwxE_xmAyFPz0Q1jrLHZfGfAYMwJRsEBcJkj73y6M/edit#bookmark=id.i30jsy1yvhkp)


## **1. Introdução à API Action**

A API Action é a forma recomendada e mais poderosa para interagir programaticamente com uma instância CKAN. Todas as funcionalidades principais acessíveis pela interface web do CKAN (e algumas adicionais) estão disponíveis através desta API.

As interações com a API geralmente envolvem o envio de um dicionário JSON num pedido HTTP POST para um dos URLs da API do CKAN. Os parâmetros para a função da API devem ser fornecidos no dicionário JSON. O CKAN também retornará a sua resposta num dicionário JSON.

**URL** Base para **os Exemplos:** https\://dadosabertos.artesp.sp.gov.br

**Caminho Padrão da API Action:** /api/3/action/{nome\_da\_acao}

Por exemplo, para listar os pacotes (datasets), o URL completo seria:

https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_list


### **Estrutura da Resposta JSON**

Uma resposta típica da API CKAN terá a seguinte estrutura:

{\
  "help": "Texto de ajuda para a ação chamada...",\
  "success": true, // ou false em caso de erro\
  "result": \[ /\* ...dados retornados pela ação... \*/ ],\
  "error": { // Presente apenas se "success" for false\
    "message": "Mensagem de erro",\
    "\_\_type": "Tipo do Erro"\
  }\
}

- **help**: Uma string de documentação para a função da API que você chamou.

- **success**: Um booleano indicando se a chamada foi bem-sucedida (true) ou não (false). **Sempre verifique este campo.**

- **result**: O resultado retornado pela função que você chamou. O tipo e o valor do resultado dependem da função.

- **error**: Se success for false, este campo conterá um objeto com detalhes sobre o erro.


## **2. Versão da API**

A API do CKAN é versionada. A versão atual e recomendada é a **v3**. É uma boa prática especificar a versão da API nas suas requisições para garantir compatibilidade futura.

Exemplo: https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_list

Se nenhuma versão for especificada, o CKAN geralmente usará a versão mais recente, mas para garantir a estabilidade do seu cliente API, inclua sempre o /3/.


## **3. Autenticação**

Algumas funções da API exigem autorização (por exemplo, criar, atualizar ou excluir datasets). Para se autenticar, você deve fornecer uma **Chave de API (API Token)**.

Você pode encontrar sua chave de API na sua página de perfil de usuário no site CKAN.

A chave de API deve ser incluída no cabeçalho Authorization (ou X-CKAN-API-Key em algumas configurações mais antigas, mas Authorization é o padrão) do seu pedido HTTP.

Exemplo de cabeçalho:

Authorization: SUA\_CHAVE\_DE\_API\_AQUI

Se uma ação que requer autorização for chamada sem uma chave de API válida, ou com uma chave que não tem as permissões necessárias, a API retornará "success": false e um erro de autorização.


## **4. Ações Comuns da API (Exemplos)**

A seguir, apresentamos exemplos de como usar algumas das ações mais comuns da API. Para ações que modificam dados (criar, atualizar, excluir), você precisará de uma chave de API válida com as permissões apropriadas.

O domínio base para todos os exemplos é https\://dadosabertos.artesp.sp.gov.br.


### **4.1. Listar Objetos**

#### **a) Listar Datasets (Pacotes) (package\_list)**

Retorna uma lista dos nomes (IDs) de todos os datasets no site.

**cURL:**

curl -X GET "\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_list]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_list)"

**JavaScript (Navegador/Node.js com node-fetch):**

async function listarDatasets() {\
  try {\
    const response = await fetch('\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_list]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_list)');\
    if (!response.ok) {\
      throw new Error(\`Erro HTTP! status: ${response.status}\`);\
    }\
    const data = await response.json();\
    if (data.success) {\
      console.log('Datasets:', data.result);\
    } else {\
      console.error('Erro ao listar datasets:', data.error);\
    }\
  } catch (error) {\
    console.error('Falha na requisição:', error);\
  }\
}\
\
listarDatasets();

**Python (com requests):**

import requests\
import json\
\
try:\
    response = requests.get('\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_list]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_list)')\
    response.raise\_for\_status()  # Lança uma exceção para códigos de erro HTTP\
    data = response.json()\
    if data.get('success'):\
        print('Datasets:', data.get('result'))\
    else:\
        print('Erro ao listar datasets:', data.get('error'))\
except requests.exceptions.RequestException as e:\
    print(f'Falha na requisição: {e}')\
except json.JSONDecodeError:\
    print('Erro ao decodificar JSON da resposta.')

**Go:**

package main\
\
import (\
"encoding/json"\
"fmt"\
"net/http"\
"io/ioutil"\
)\
\
type CKANResponse struct {\
Help    string          \`json:"help"\`\
Success bool            \`json:"success"\`\
Result  \[]string        \`json:"result"\` // Para package\_list, o resultado é uma lista de strings\
Error   json.RawMessage \`json:"error,omitempty"\`\
}\
\
func main() {\
resp, err := http.Get("\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_list]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_list)")\
if err != nil {\
fmt.Println("Erro ao fazer a requisição:", err)\
return\
}\
defer resp.Body.Close()\
\
body, err := ioutil.ReadAll(resp.Body)\
if err != nil {\
fmt.Println("Erro ao ler o corpo da resposta:", err)\
return\
}\
\
var ckanResp CKANResponse\
err = json.Unmarshal(body, \&ckanResp)\
if err != nil {\
fmt.Println("Erro ao decodificar JSON:", err)\
return\
}\
\
if ckanResp.Success {\
fmt.Println("Datasets:", ckanResp.Result)\
} else {\
fmt.Println("Erro da API CKAN:", string(ckanResp.Error))\
}\
}


#### **b) Listar Grupos (group\_list)**

Retorna uma lista dos nomes (IDs) de todos os grupos.

**cURL:**

curl -X GET "\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/group\_list]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/group\_list)"

_(Exemplos em JavaScript, Python e Go seriam semelhantes ao package\_list, apenas mudando o nome da ação no URL.)_


#### **c) Listar Organizações (organization\_list)**

Retorna uma lista dos nomes (IDs) de todas as organizações.

**cURL:**

curl -X GET "\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/organization\_list]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/organization\_list)"

_(Exemplos em JavaScript, Python e Go seriam semelhantes ao package\_list.)_


#### **d) Listar Tags (tag\_list)**

Retorna uma lista de todas as tags.

**cURL:**

curl -X GET "\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/tag\_list]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/tag\_list)"

_(Exemplos_ em JavaScript, Python e Go seriam semelhantes ao _package\_list.)_


### **4.2. Mostrar Detalhes de um Objeto**

#### **a) Mostrar Detalhes de um Dataset (package\_show)**

Retorna a informação completa sobre um dataset específico, incluindo seus recursos.

**Parâmetros:**

- id (string): O nome (ID) ou o UUID do dataset.

**cURL:**

\# Substitua 'nome-do-dataset' pelo ID real de um dataset\
curl -X GET "\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_show?id=nome-do-dataset]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_show?id=nome-do-dataset)"

**JavaScript:**

async function mostrarDataset(datasetId) {\
  try {\
    const response = await fetch(\`https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_show?id=${datasetId}\`);\
    if (!response.ok) {\
      throw new Error(\`Erro HTTP! status: ${response.status}\`);\
    }\
    const data = await response.json();\
    if (data.success) {\
      console.log('Detalhes do Dataset:', data.result);\
    } else {\
      console.error(\`Erro ao mostrar dataset ${datasetId}:\`, data.error);\
    }\
  } catch (error) {\
    console.error('Falha na requisição:', error);\
  }\
}\
\
// Substitua 'nome-do-dataset' pelo ID real de um dataset\
mostrarDataset('nome-do-dataset');

**Python:**

import requests\
import json\
\
def mostrar\_dataset(dataset\_id):\
    try:\
        params = {'id': dataset\_id}\
        response = requests.get('\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_show]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_show)', params=params)\
        response.raise\_for\_status()\
        data = response.json()\
        if data.get('success'):\
            print(f'Detalhes do Dataset ({dataset\_id}):', json.dumps(data.get('result'), indent=2, ensure\_ascii=False))\
        else:\
            print(f'Erro ao mostrar dataset {dataset\_id}:', data.get('error'))\
    except requests.exceptions.RequestException as e:\
        print(f'Falha na requisição: {e}')\
    except json.JSONDecodeError:\
        print('Erro ao decodificar JSON da resposta.')\
\
\# Substitua 'nome-do-dataset' pelo ID real de um dataset\
mostrar\_dataset('nome-do-dataset')

**Go:**

package main\
\
import (\
"encoding/json"\
"fmt"\
"net/http"\
"io/ioutil"\
)\
\
// CKANObjectResponse é uma estrutura genérica para respostas de 'show' onde 'result' é um objeto\
type CKANObjectResponse struct {\
Help    string          \`json:"help"\`\
Success bool            \`json:"success"\`\
Result  json.RawMessage \`json:"result"\` // Usar RawMessage para resultado genérico\
Error   json.RawMessage \`json:"error,omitempty"\`\
}\
\
func main() {\
datasetID := "nome-do-dataset" // Substitua pelo ID real\
url := fmt.Sprintf("\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_show?id=%s]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_show?id=%s)", datasetID)\
\
resp, err := http.Get(url)\
if err != nil {\
fmt.Println("Erro ao fazer a requisição:", err)\
return\
}\
defer resp.Body.Close()\
\
body, err := ioutil.ReadAll(resp.Body)\
if err != nil {\
fmt.Println("Erro ao ler o corpo da resposta:", err)\
return\
}\
\
var ckanResp CKANObjectResponse\
err = json.Unmarshal(body, \&ckanResp)\
if err != nil {\
fmt.Println("Erro ao decodificar JSON:", err)\
return\
}\
\
if ckanResp.Success {\
// Para imprimir de forma formatada (pretty print)\
var prettyJSON map\[string]interface{}\
json.Unmarshal(ckanResp.Result, \&prettyJSON)\
formatted, \_ := json.MarshalIndent(prettyJSON, "", "  ")\
fmt.Println("Detalhes do Dataset:", string(formatted))\
} else {\
fmt.Println("Erro da API CKAN:", string(ckanResp.Error))\
}\
}


#### **b) Mostrar Detalhes de um Recurso (resource\_show)**

Retorna metadados de um recurso específico.

**Parâmetros:**

- id (string): O UUID do recurso.

**cURL:**

\# Substitua 'uuid-do-recurso' pelo UUID real de um recurso\
curl -X GET "\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/resource\_show?id=uuid-do-recurso]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/resource\_show?id=uuid-do-recurso)"

_(Exemplos_ em JavaScript, Python e Go seriam semelhantes ao package\_show, adaptando o _nome da ação e o parâmetro.)_


### **4.3. Pesquisar Objetos**

#### **a) Pesquisar Datasets (package\_search)**

Permite pesquisar datasets com base em vários critérios.

**Parâmetros Comuns:**

- q (string): Termo de busca. Ex: q=educacao

- fq (string): Filtro de query (Solr syntax). Ex: fq=tags:economia organization:nome-da-organizacao

- rows (int): Número de resultados por página (padrão 10).

- start (int): Offset para paginação.

- sort (string): Critério de ordenação. Ex: sort=score desc, metadata\_modified desc

- facet.field (list of strings): Campos para facetar. Ex: facet.field=\["tags", "organization"]

- facet.limit (int): Número máximo de valores por faceta.

- include\_private (boolean): Incluir datasets privados (requer autenticação e permissão).

**cURL (pesquisando por "rodovias" e facetando por organização):**

curl -X GET "\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_search?q=rodovias\&facet.field=]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_search?q=rodovias\&facet.field=)\[\\"organization\\"]\&rows=5"

**JavaScript:**

async function pesquisarDatasets(termo) {\
  try {\
    const params = new URLSearchParams({\
      q: termo,\
      'facet.field': '\["organization","tags"]', // Precisa ser string JSON\
      rows: 5\
    });\
    const response = await fetch(\`https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_search?${params.toString()}\`);\
    if (!response.ok) {\
      throw new Error(\`Erro HTTP! status: ${response.status}\`);\
    }\
    const data = await response.json();\
    if (data.success) {\
      console.log('Resultados da Pesquisa:', data.result.results);\
      console.log('Facetas:', data.result.search\_facets);\
    } else {\
      console.error('Erro na pesquisa de datasets:', data.error);\
    }\
  } catch (error) {\
    console.error('Falha na requisição:', error);\
  }\
}\
\
pesquisarDatasets('rodovias');

**Python:**

import requests\
import json\
\
def pesquisar\_datasets(termo):\
    try:\
        params = {\
            'q': termo,\
            'facet.field': '\["organization", "tags"]', # String JSON\
            'rows': 5\
        }\
        response = requests.get('\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_search]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_search)', params=params)\
        response.raise\_for\_status()\
        data = response.json()\
        if data.get('success'):\
            print(f'Resultados da Pesquisa por "{termo}":')\
            for pkg in data\['result']\['results']:\
                print(f"  - {pkg\['title']} (ID: {pkg\['name']})")\
            print('Facetas:', json.dumps(data\['result']\['search\_facets'], indent=2, ensure\_ascii=False))\
        else:\
            print('Erro na pesquisa de datasets:', data.get('error'))\
    except requests.exceptions.RequestException as e:\
        print(f'Falha na requisição: {e}')\
    except json.JSONDecodeError:\
        print('Erro ao decodificar JSON da resposta.')\
\
pesquisar\_datasets('rodovias')

**Go:**

package main\
\
import (\
"encoding/json"\
"fmt"\
"net/http"\
"net/url"\
"io/ioutil"\
)\
\
type CKANSearchResponse struct {\
Help    string          \`json:"help"\`\
Success bool            \`json:"success"\`\
Result  SearchResult    \`json:"result"\`\
Error   json.RawMessage \`json:"error,omitempty"\`\
}\
\
type SearchResult struct {\
Count        int               \`json:"count"\`\
Sort         string            \`json:"sort"\`\
Facets       json.RawMessage   \`json:"facets"\` // Pode ser mais específico\
Results      \[]Dataset         \`json:"results"\`\
SearchFacets map\[string]Facet  \`json:"search\_facets"\`\
}\
\
type Dataset struct {\
ID    string \`json:"id"\`\
Name  string \`json:"name"\`\
Title string \`json:"title"\`\
// Adicionar outros campos conforme necessário\
}\
\
type Facet struct {\
Title string      \`json:"title"\`\
Items \[]FacetItem \`json:"items"\`\
}\
\
type FacetItem struct {\
DisplayName string \`json:"display\_name"\`\
Count       int    \`json:"count"\`\
Name        string \`json:"name"\`\
}\
\
\
func main() {\
termoPesquisa := "rodovias"\
baseURL := "\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_search]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_search)"\
\
params := url.Values{}\
params.Add("q", termoPesquisa)\
params.Add("facet.field", \`\["organization", "tags"]\`) // String JSON\
params.Add("rows", "5")\
\
reqURL := fmt.Sprintf("%s?%s", baseURL, params.Encode())\
\
resp, err := http.Get(reqURL)\
if err != nil {\
fmt.Println("Erro ao fazer a requisição:", err)\
return\
}\
defer resp.Body.Close()\
\
body, err := ioutil.ReadAll(resp.Body)\
if err != nil {\
fmt.Println("Erro ao ler o corpo da resposta:", err)\
return\
}\
\
var ckanResp CKANSearchResponse\
err = json.Unmarshal(body, \&ckanResp)\
if err != nil {\
fmt.Println("Erro ao decodificar JSON:", err, string(body))\
return\
}\
\
if ckanResp.Success {\
fmt.Printf("Encontrados %d datasets para '%s':\n", ckanResp.Result.Count, termoPesquisa)\
for \_, pkg := range ckanResp.Result.Results {\
fmt.Printf("  - %s (ID: %s)\n", pkg.Title, pkg.Name)\
}\
fmt.Println("Facetas:")\
for facetName, facetData := range ckanResp.Result.SearchFacets {\
fmt.Printf("  %s (%s):\n", facetData.Title, facetName)\
for \_, item := range facetData.Items {\
fmt.Printf("    - %s: %d\n", item.DisplayName, item.Count)\
}\
}\
} else {\
fmt.Println("Erro da API CKAN:", string(ckanResp.Error))\
}\
}


### **4.4. Criar Objetos (Requer Autenticação)**

#### **a) Criar um Dataset (package\_create)**

Cria um novo dataset.

**Corpo da Requisição (JSON):**

{\
  "name": "meu-novo-dataset-unico", // ID único, letras minúsculas, números, hífens e underscores\
  "title": "Meu Novo Dataset de Exemplo",\
  "notes": "Uma descrição detalhada sobre este dataset.",\
  "owner\_org": "id-da-sua-organizacao", // ID da organização proprietária\
  "tags": \[{"name": "exemplo"}, {"name": "teste"}],\
  "resources": \[\
    {\
      "name": "Meu primeiro recurso",\
      "url": "\[https\://example.com/data.csv]\(https\://example.com/data.csv)",\
      "format": "CSV",\
      "description": "Dados de exemplo em CSV."\
    }\
  ]\
  // Outros campos opcionais: author, author\_email, license\_id, etc.\
}

**cURL:**

\# Substitua SUA\_CHAVE\_DE\_API\_AQUI e os dados do dataset\
curl -X POST "\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_create]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_create)" \\\
&#x20;    -H "Authorization: SUA\_CHAVE\_DE\_API\_AQUI" \\\
&#x20;    -H "Content-Type: application/json" \\\
&#x20;    -d '{\
&#x20;          "name": "meu-dataset-teste-001",\
&#x20;          "title": "Dataset de Teste 001",\
&#x20;          "owner\_org": "id-da-sua-organizacao",\
&#x20;          "notes": "Criado via API.",\
&#x20;          "tags": \[{"name": "api\_test"}]\
&#x20;        }'

**JavaScript:**

async function criarDataset(apiKey, datasetData) {\
  try {\
    const response = await fetch('\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_create]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_create)', {\
      method: 'POST',\
      headers: {\
        'Authorization': apiKey,\
        'Content-Type': 'application/json'\
      },\
      body: JSON.stringify(datasetData)\
    });\
    // Não lançar erro imediatamente para poder ler o corpo da resposta do CKAN\
    const data = await response.json();\
   \
    if (response.ok && data.success) { // CKAN pode retornar 200 OK mas success: false\
      console.log('Dataset criado com sucesso:', data.result);\
    } else {\
      // Se data.error existir, use-o, senão crie um erro genérico\
      const errorMessage = data.error ? JSON.stringify(data.error) : \`Erro HTTP: ${response.status}\`;\
      console.error('Erro ao criar dataset:', errorMessage);\
      throw new Error(errorMessage);\
    }\
  } catch (error) {\
    console.error('Falha na requisição:', error.message);\
  }\
}\
\
const minhaChaveApi = "SUA\_CHAVE\_DE\_API\_AQUI";\
const novoDataset = {\
  name: "dataset-js-exemplo-002",\
  title: "Dataset Exemplo via JS 002",\
  owner\_org: "id-da-sua-organizacao", // Substitua pelo ID da sua organização\
  notes: "Este é um dataset de exemplo criado via API com JavaScript.",\
  tags: \[{name: "javascript"}, {name: "api"}],\
  resources: \[\
    {\
      name: "Arquivo CSV de Exemplo",\
      url: "\[https\://example.com/dados.csv]\(https\://example.com/dados.csv)",\
      format: "CSV",\
      description: "Um arquivo CSV de exemplo."\
    }\
  ]\
};\
\
// criarDataset(minhaChaveApi, novoDataset); // Descomente para rodar

Python (com ckanapi):

A biblioteca ckanapi simplifica as interações, especialmente com autenticação e uploads.

Instale com pip install ckanapi.

from ckanapi import RemoteCKAN, NotAuthorized, ValidationError\
import json # Adicionado para o print\
\
\# Substitua pela sua chave de API e ID da organização\
API\_KEY = 'SUA\_CHAVE\_DE\_API\_AQUI'\
ORG\_ID = 'id-da-sua-organizacao'\
CKAN\_URL = '\[https\://dadosabertos.artesp.sp.gov.br]\(https\://dadosabertos.artesp.sp.gov.br)'\
\
ckan = RemoteCKAN(CKAN\_URL, apikey=API\_KEY)\
\
novo\_dataset\_data = {\
    "name": "meu-dataset-python-003",\
    "title": "Meu Dataset Python 003",\
    "owner\_org": ORG\_ID,\
    "notes": "Dataset criado via API com a biblioteca ckanapi em Python.",\
    "tags": \[{"name": "python"}, {"name": "ckanapi"}],\
    "resources": \[\
        {\
            "name": "Dados de Exemplo (JSON)",\
            "url": "\[https\://example.com/data.json]\(https\://example.com/data.json)",\
            "format": "JSON",\
            "description": "Recurso de dados JSON."\
        }\
    ]\
}\
\
try:\
    pacote\_criado = ckan.action.package\_create(\*\*novo\_dataset\_data)\
    print("Dataset criado com sucesso:")\
    print(json.dumps(pacote\_criado, indent=2, ensure\_ascii=False))\
except NotAuthorized:\
    print("Erro: Não autorizado. Verifique sua chave de API e permissões.")\
except ValidationError as e:\
    print(f"Erro de validação: {e.error\_dict}")\
except Exception as e:\
    print(f"Ocorreu um erro inesperado: {e}")

**Go:**

package main\
\
import (\
"bytes"\
"encoding/json"\
"fmt"\
"io/ioutil"\
"net/http"\
)\
\
type DatasetCreatePayload struct {\
Name       string        \`json:"name"\`\
Title      string        \`json:"title"\`\
OwnerOrg   string        \`json:"owner\_org"\`\
Notes      string        \`json:"notes,omitempty"\`\
Tags       \[]TagPayload  \`json:"tags,omitempty"\`\
Resources  \[]ResourcePayload \`json:"resources,omitempty"\`\
// Adicione outros campos conforme necessário\
}\
\
type TagPayload struct {\
Name string \`json:"name"\`\
}\
\
type ResourcePayload struct {\
Name        string \`json:"name"\`\
URL         string \`json:"url"\`\
Format      string \`json:"format,omitempty"\`\
Description string \`json:"description,omitempty"\`\
}\
\
// Resposta genérica para criação\
type CKANCreateResponse struct {\
Help    string          \`json:"help"\`\
Success bool            \`json:"success"\`\
Result  json.RawMessage \`json:"result"\` // O dataset criado\
Error   json.RawMessage \`json:"error,omitempty"\`\
}\
\
func main() {\
apiKey := "SUA\_CHAVE\_DE\_API\_AQUI" // Substitua\
orgID := "id-da-sua-organizacao"    // Substitua\
\
payload := DatasetCreatePayload{\
Name:     "meu-dataset-go-exemplo-001",\
Title:    "Meu Dataset de Exemplo em Go 001",\
OwnerOrg: orgID,\
Notes:    "Criado via API usando Go.",\
Tags:     \[]TagPayload{{Name: "golang"}, {Name: "api"}},\
Resources: \[]ResourcePayload{\
{\
Name:        "Arquivo TXT",\
URL:         "\[https\://example.com/data.txt]\(https\://example.com/data.txt)",\
Format:      "TXT",\
Description: "Um recurso de arquivo de texto.",\
},\
},\
}\
\
payloadBytes, err := json.Marshal(payload)\
if err != nil {\
fmt.Println("Erro ao serializar payload:", err)\
return\
}\
\
req, err := http.NewRequest("POST", "\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_create]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_create)", bytes.NewBuffer(payloadBytes))\
if err != nil {\
fmt.Println("Erro ao criar requisição:", err)\
return\
}\
\
req.Header.Set("Authorization", apiKey)\
req.Header.Set("Content-Type", "application/json")\
\
client := \&http.Client{}\
resp, err := client.Do(req)\
if err != nil {\
fmt.Println("Erro ao enviar requisição:", err)\
return\
}\
defer resp.Body.Close()\
\
body, err := ioutil.ReadAll(resp.Body)\
if err != nil {\
fmt.Println("Erro ao ler resposta:", err)\
return\
}\
\
var ckanResp CKANCreateResponse\
err = json.Unmarshal(body, \&ckanResp)\
if err != nil {\
fmt.Println("Erro ao decodificar JSON da resposta:", err, string(body))\
return\
}\
\
if ckanResp.Success {\
var prettyResult map\[string]interface{}\
json.Unmarshal(ckanResp.Result, \&prettyResult)\
formatted, \_ := json.MarshalIndent(prettyResult, "", "  ")\
fmt.Println("Dataset criado com sucesso:", string(formatted))\
} else {\
fmt.Println("Erro da API CKAN:", string(ckanResp.Error))\
fmt.Println("Status Code:", resp.StatusCode)\
fmt.Println("Resposta completa:", string(body))\
}\
}


### **4.5. Atualizar Objetos (Requer Autenticação)**

#### **a) Atualizar um Dataset (package\_update)**

Atualiza um dataset existente. Similar ao package\_create, mas você fornece o id ou name do dataset a ser atualizado. **Importante:** package\_update substitui todo o metadado do dataset. Se você quer atualizar apenas alguns campos, é melhor primeiro fazer um package\_show, modificar o dicionário resultante, e então enviar o dicionário modificado para package\_update. Para atualizações parciais, veja package\_patch.

**cURL:**

\# Substitua SUA\_CHAVE\_DE\_API\_AQUI e os dados do dataset\
curl -X POST "\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_update]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_update)" \\\
&#x20;    -H "Authorization: SUA\_CHAVE\_DE\_API\_AQUI" \\\
&#x20;    -H "Content-Type: application/json" \\\
&#x20;    -d '{\
&#x20;          "id": "meu-dataset-teste-001", // Ou "name": "meu-dataset-teste-001"\
&#x20;          "title": "Dataset de Teste 001 (Atualizado)",\
&#x20;          "notes": "Notas atualizadas via API.",\
&#x20;          "owner\_org": "id-da-sua-organizacao" \
&#x20;          // É importante reenviar todos os campos que devem ser mantidos\
&#x20;        }'

_(Exemplos em JavaScript, Python e Go seriam semelhantes ao package\_create, usando a ação package\_update e incluindo o id ou name do dataset no payload.)_


#### **b) Atualizar Parcialmente um Dataset (package\_patch)**

Atualiza apenas os campos especificados de um dataset, deixando os outros inalterados. Isso é útil para modificar um ou dois campos sem precisar reenviar todo o objeto do dataset.

**Corpo da Requisição (JSON):**

{\
  "id": "meu-dataset-teste-001", // ID ou nome do dataset a ser atualizado\
  "notes": "Esta nota foi atualizada usando package\_patch.",\
  "title": "Título Atualizado com Patch"\
  // Apenas os campos que você quer modificar\
}

**cURL:**

curl -X POST "\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_patch]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_patch)" \\\
&#x20;    -H "Authorization: SUA\_CHAVE\_DE\_API\_AQUI" \\\
&#x20;    -H "Content-Type: application/json" \\\
&#x20;    -d '{\
&#x20;          "id": "meu-dataset-teste-001",\
&#x20;          "notes": "Nota atualizada com patch."\
&#x20;        }'

_(Exemplos em JavaScript, Python e Go seriam semelhantes, usando a ação package\_patch e um payload contendo apenas os campos a serem alterados junto com o id.)_


#### **c) Atualizar um Recurso (resource\_update ou resource\_patch)**

Assim como datasets, recursos podem ser atualizados completamente com resource\_update ou parcialmente com resource\_patch. Você precisará do id do recurso.

**Corpo da Requisição para resource\_patch (JSON):**

{\
  "id": "uuid-do-recurso-a-atualizar",\
  "description": "Descrição do recurso atualizada.",\
  "name": "Novo nome para o recurso"\
}

_(Exemplos em cURL, JavaScript, Python e Go seguem o padrão dos datasets, ajustando a ação e o payload.)_


### **4.6. Deletar Objetos (Requer Autenticação)**

#### **a) Deletar um Dataset (package\_delete)**

Marca um dataset como deletado. Ele não aparecerá mais nas listagens públicas, mas ainda existe no banco de dados e pode ser purgado por um administrador.

**Corpo da Requisição (JSON):**

{\
  "id": "nome-do-dataset-a-deletar"\
}

**cURL:**

curl -X POST "\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_delete]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/package\_delete)" \\\
&#x20;    -H "Authorization: SUA\_CHAVE\_DE\_API\_AQUI" \\\
&#x20;    -H "Content-Type: application/json" \\\
&#x20;    -d '{"id": "meu-dataset-teste-001"}'

_(Exemplos em JavaScript, Python e Go seguem o padrão de criação/atualização, usando a ação package\_delete e o payload com id.)_


#### **b) Deletar um Recurso (resource\_delete)**

Remove um recurso de um dataset.

**Corpo da Requisição (JSON):**

{\
  "id": "uuid-do-recurso-a-deletar"\
}

_(Exemplos seguem o padrão de package\_delete.)_


## **5. Upload de Arquivos para Recursos**

Ao criar (resource\_create) ou atualizar (resource\_update/resource\_patch) um recurso, você pode fazer o upload de um arquivo diretamente para o FileStore do CKAN (se configurado). Isso é feito através de uma requisição multipart/form-data.

O campo para o arquivo geralmente é upload.

**cURL (criando um novo recurso com upload):**

\# Substitua SUA\_CHAVE\_DE\_API\_AQUI, ID\_DO\_PACOTE e caminho/para/seu/arquivo.csv\
curl -X POST "\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/resource\_create]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/resource\_create)" \\\
&#x20;    -H "Authorization: SUA\_CHAVE\_DE\_API\_AQUI" \\\
&#x20;    -F "package\_id=ID\_DO\_PACOTE" \\\
&#x20;    -F "name=Recurso com Upload" \\\
&#x20;    -F "format=CSV" \\\
&#x20;    -F "upload=@/caminho/para/seu/arquivo.csv" \\\
&#x20;    -F "url=dummy-value" # Obrigatório em versões mais antigas do CKAN, ignorado se upload presente

Python (com ckanapi):

A biblioteca ckanapi lida com uploads de forma transparente.

from ckanapi import RemoteCKAN\
import json # Adicionado para o print\
\
\# ... (configuração do RemoteCKAN como antes) ...\
\# ckan = RemoteCKAN(CKAN\_URL, apikey=API\_KEY)\
\
ID\_DO\_PACOTE = 'meu-dataset-python-003' # Exemplo de ID de pacote existente\
CAMINHO\_ARQUIVO = '/caminho/para/seu/arquivo.csv' # Substitua pelo caminho real\
\
try:\
    with open(CAMINHO\_ARQUIVO, 'rb') as f\_upload:\
        recurso\_com\_upload = ckan.action.resource\_create(\
            package\_id=ID\_DO\_PACOTE,\
            name="Recurso Upload Python CSV",\
            description="Arquivo CSV enviado via ckanapi.",\
            upload=f\_upload, # Passa o objeto do arquivo\
            format="CSV",\
            url='ignored\_when\_uploading' # Necessário para compatibilidade <2.6\
        )\
    print("Recurso com upload criado:", json.dumps(recurso\_com\_upload, indent=2))\
except Exception as e:\
    print(f"Erro ao fazer upload do recurso: {e}")

**JavaScript (Navegador com FormData):**

async function criarRecursoComUpload(apiKey, packageId, fileName, fileObject) {\
  const formData = new FormData();\
  formData.append('package\_id', packageId);\
  formData.append('name', \`Recurso Upload JS - ${fileName}\`);\
  formData.append('format', fileObject.type.split('/')\[1] || 'unknown'); // Tenta pegar a extensão\
  formData.append('upload', fileObject, fileName);\
  formData.append('url', 'ignored\_when\_uploading'); // Para compatibilidade\
\
  try {\
    const response = await fetch('\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/resource\_create]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/resource\_create)', {\
      method: 'POST',\
      headers: {\
        'Authorization': apiKey,\
        // 'Content-Type' é definido automaticamente pelo FormData\
      },\
      body: formData\
    });\
    const data = await response.json();\
    if (response.ok && data.success) {\
      console.log('Recurso com upload criado:', data.result);\
    } else {\
      console.error('Erro ao criar recurso com upload:', data.error || \`Erro HTTP ${response.status}\`);\
    }\
  } catch (error) {\
    console.error('Falha na requisição de upload:', error);\
  }\
}\
\
// Exemplo de uso (geralmente a partir de um \<input type="file">)\
// const minhaChaveApi = "SUA\_CHAVE\_DE\_API\_AQUI";\
// const idDoPacote = "meu-dataset-js-exemplo-002";\
// const inputElement = document.getElementById('meuUploadDeArquivo'); // Supondo que exista\
// inputElement.onchange = function(event) {\
//   const file = event.target.files\[0];\
//   if (file) {\
//     criarRecursoComUpload(minhaChaveApi, idDoPacote, file.name, file);\
//   }\
// };

**Go (com multipart/form-data):**

package main\
\
import (\
"bytes"\
"encoding/json"\
"fmt"\
"io"\
"io/ioutil"\
"mime/multipart"\
"net/http"\
"os"\
"path/filepath"\
)\
\
// Reutilize CKANCreateResponse ou defina uma específica para resource\_create\
// type CKANResourceCreateResponse CKANCreateResponse\
\
func main() {\
apiKey := "SUA\_CHAVE\_DE\_API\_AQUI"\
packageID := "meu-dataset-go-exemplo-001" // ID do dataset onde o recurso será adicionado\
filePath := "/caminho/para/seu/arquivo.txt" // Substitua pelo caminho do seu arquivo\
\
file, err := os.Open(filePath)\
if err != nil {\
fmt.Println("Erro ao abrir arquivo:", err)\
return\
}\
defer file.Close()\
\
body := \&bytes.Buffer{}\
writer := multipart.NewWriter(body)\
\
// Campo package\_id\
\_ = writer.WriteField("package\_id", packageID)\
// Campo name\
\_ = writer.WriteField("name", "Recurso Upload Go "+filepath.Base(filePath))\
// Campo format (opcional, pode ser inferido ou especificado)\
\_ = writer.WriteField("format", "TXT") // Ajuste conforme o tipo do arquivo\
    // Campo URL (dummy)\
    \_ = writer.WriteField("url", "ignored\_when\_uploading")\
\
\
// Campo upload (arquivo)\
part, err := writer.CreateFormFile("upload", filepath.Base(filePath))\
if err != nil {\
fmt.Println("Erro ao criar form file:", err)\
return\
}\
\_, err = io.Copy(part, file)\
if err != nil {\
fmt.Println("Erro ao copiar arquivo para o form:", err)\
return\
}\
\
err = writer.Close() // Fecha o writer multipart ANTES de enviar a requisição\
if err != nil {\
fmt.Println("Erro ao fechar writer:", err)\
return\
}\
\
req, err := http.NewRequest("POST", "\[https\://dadosabertos.artesp.sp.gov.br/api/3/action/resource\_create]\(https\://dadosabertos.artesp.sp.gov.br/api/3/action/resource\_create)", body)\
if err != nil {\
fmt.Println("Erro ao criar requisição:", err)\
return\
}\
\
req.Header.Set("Authorization", apiKey)\
req.Header.Set("Content-Type", writer.FormDataContentType()) // Importante!\
\
client := \&http.Client{}\
resp, err := client.Do(req)\
if err != nil {\
fmt.Println("Erro ao enviar requisição:", err)\
return\
}\
defer resp.Body.Close()\
\
respBody, err := ioutil.ReadAll(resp.Body)\
if err != nil {\
fmt.Println("Erro ao ler resposta:", err)\
return\
}\
\
var ckanResp CKANCreateResponse // Reutilizando a struct\
err = json.Unmarshal(respBody, \&ckanResp)\
if err != nil {\
fmt.Println("Erro ao decodificar JSON da resposta:", err, string(respBody))\
return\
}\
\
if ckanResp.Success {\
var prettyResult map\[string]interface{}\
json.Unmarshal(ckanResp.Result, \&prettyResult)\
formatted, \_ := json.MarshalIndent(prettyResult, "", "  ")\
fmt.Println("Recurso com upload criado com sucesso:", string(formatted))\
} else {\
fmt.Println("Erro da API CKAN:", string(ckanResp.Error))\
fmt.Println("Status Code:", resp.StatusCode)\
fmt.Println("Resposta completa:", string(respBody))\
}\
}


## **6. CLI ckanapi e Módulo Python**

Para usuários de Python e administradores de sistema, a ferramenta ckanapi oferece uma interface de linha de comando e um módulo Python que simplificam muitas operações, incluindo:

- Chamada de qualquer ação da API.

- Operações em lote (bulk dump/load/delete de datasets, grupos, etc.).

- Exportação de datasets no formato DataPackage.

**Instalação:**

pip install ckanapi

**Exemplo de uso da CLI (listar datasets):**

ckanapi action package\_list -r \[https\://dadosabertos.artesp.sp.gov.br]\(https\://dadosabertos.artesp.sp.gov.br)

**Exemplo de uso da CLI (mostrar dataset, requerendo ID do dataset):**

ckanapi action package\_show id=NOME\_OU\_ID\_DO\_DATASET -r \[https\://dadosabertos.artesp.sp.gov.br]\(https\://dadosabertos.artesp.sp.gov.br)

Exemplo de uso da CLI (criar dataset, requer chave API e arquivo JSON):

Primeiro, crie um arquivo meu\_dataset.json com o conteúdo do dataset:

{\
  "name": "meu-dataset-cli-001",\
  "title": "Dataset via CLI",\
  "owner\_org": "id-da-sua-organizacao",\
  "notes": "Criado com ckanapi CLI"\
}

Então, execute o comando (substitua SUA\_CHAVE\_DE\_API):

ckanapi action package\_create -a SUA\_CHAVE\_DE\_API -r \[https\://dadosabertos.artesp.sp.gov.br]\(https\://dadosabertos.artesp.sp.gov.br) -I meu\_dataset.json

Consulte a documentação do ckanapi para mais detalhes sobre suas funcionalidades avançadas.


## **7. Dicas e Boas Práticas**

- **Verifique Sempre success**: Não confie apenas no código de status HTTP 200.

- **Rate Limiting**: Esteja ciente de que algumas instâncias CKAN podem ter limites de taxa para chamadas de API.

- **Tratamento de Erros**: Implemente um tratamento de erros robusto, analisando o objeto error quando success for false.

- **Paginação**: Para ações que retornam listas longas (ex: package\_search, package\_list), use os parâmetros rows e start (ou limit e offset para algumas ações mais antigas) para paginar os resultados.

- **IDs vs Nomes**: Muitas ações aceitam tanto o nome amigável (slug) quanto o UUID de um objeto. O UUID é garantidamente único.

- **Sensibilidade a Maiúsculas/Minúsculas**: Nomes de datasets (IDs) geralmente são case-insensitive na criação, mas são armazenados e referenciados em minúsculas. IDs (UUIDs) são case-sensitive.

- **Documentação Oficial**: Para a lista completa de ações e seus parâmetros, consulte sempre a documentação oficial do CKAN (geralmente acessível em \<URL\_DO\_CKAN>/api/3).

Este manual deve fornecer uma base sólida para começar a trabalhar com a API do CKAN. Explore as diversas ações disponíveis para aproveitar ao máximo o potencial da plataforma!


## **8. Guia Rápido de Ações da API**

Esta seção fornece um resumo das ações mais comuns da API do CKAN, seus métodos HTTP e parâmetros chave. A URL base para todas as ações é https\://dadosabertos.artesp.sp.gov.br/api/3/action/. Para ações que modificam dados, a autenticação via Chave de API no cabeçalho Authorization é necessária.


### **Ações de Leitura (Datasets/Pacotes)**

**Nome da Ação:** package\_list

- **Descrição:** Retorna uma lista dos nomes (IDs) de todos os datasets públicos.

- **Método HTTP:** GET ou POST (com corpo JSON vazio ou com parâmetros de paginação)

- **Parâmetros (para GET na URL ou no corpo JSON para POST):**

* limit (int, opcional): Número de resultados a retornar.

* offset (int, opcional): Posição inicial da lista.

- **Autenticação:** Não.

**Nome da Ação:** package\_show

- **Descrição:** Retorna os metadados detalhados de um dataset.

- **Método HTTP:** GET ou POST

- **Parâmetros (para GET na URL ou no corpo JSON para POST):**

* id (string, obrigatório): O ID ou nome do dataset.

* include\_tracking (boolean, opcional): Incluir informações de rastreamento de visualizações.

- **Autenticação:** Não (para datasets públicos). Sim (para datasets privados).

**Nome da Ação:** package\_search

- **Descrição:** Busca datasets com base em critérios de pesquisa.

- **Método HTTP:** GET ou POST

- **Parâmetros (para GET na URL ou no corpo JSON para POST):**

* q (string, opcional): Termo de busca (ex: name:my\_dataset, title:My Dataset).

* fq (string, opcional): Filtro de query (Solr syntax, ex: tags:economia organization:my\_org).

* rows (int, opcional): Número de resultados (padrão: 10).

* start (int, opcional): Offset para paginação.

* sort (string, opcional): Critério de ordenação (ex: score desc, metadata\_modified desc).

* facet.field (lista de strings JSON, opcional): Campos para facetamento (ex: \["tags", "organization"]).

* include\_private (boolean, opcional): Se true, inclui datasets privados aos quais o usuário tem acesso.

- **Autenticação:** Não (para busca em datasets públicos). Sim (se include\_private=true).


### **Ações de Leitura (Recursos)**

**Nome da Ação:** resource\_show

- **Descrição:** Retorna os metadados detalhados de um recurso.

- **Método HTTP:** GET ou POST

- **Parâmetros (para GET na URL ou no corpo JSON para POST):**

* id (string, obrigatório): O ID do recurso.

- **Autenticação:** Não (para recursos de datasets públicos). Sim (para recursos de datasets privados).


### **Ações de Leitura (Organizações)**

**Nome da Ação:** organization\_list

- **Descrição:** Retorna uma lista dos nomes (IDs) de todas as organizações públicas.

- **Método HTTP:** GET ou POST

- **Parâmetros (para GET na URL ou no corpo JSON para POST):**

* limit (int, opcional), offset (int, opcional): Para paginação.

* all\_fields (boolean, opcional): Se true, retorna todos os campos, não apenas nomes.

* include\_dataset\_count (boolean, opcional): Inclui a contagem de datasets (se all\_fields=true).

- **Autenticação:** Não.

**Nome da Ação:** organization\_show

- **Descrição:** Retorna os metadados detalhados de uma organização.

- **Método HTTP:** GET ou POST

- **Parâmetros (para GET na URL ou no corpo JSON para POST):**

* id (string, obrigatório): O ID ou nome da organização.

* include\_datasets (boolean, opcional): Se true, inclui uma lista (limitada) dos datasets da organização.

- **Autenticação:** Não.


### **Ações de Leitura (Grupos)**

**Nome da Ação:** group\_list

- **Descrição:** Retorna uma lista dos nomes (IDs) de todos os grupos públicos.

- **Método HTTP:** GET ou POST

- **Parâmetros:** Similar a organization\_list.

- **Autenticação:** Não.

**Nome da Ação:** group\_show

- **Descrição:** Retorna os metadados detalhados de um grupo.

- **Método HTTP:** GET ou POST

- **Parâmetros:** Similar a organization\_show.

- **Autenticação:** Não.


### **Ações de Leitura (Tags)**

**Nome da Ação:** tag\_list

- **Descrição:** Retorna uma lista dos nomes de todas as tags.

- **Método HTTP:** GET ou POST

- **Parâmetros (para GET na URL ou no corpo JSON para POST):**

* query (string, opcional): Filtra tags por um termo de busca.

* vocabulary\_id (string, opcional): Filtra tags por vocabulário.

* all\_fields (boolean, opcional): Retorna detalhes completos da tag.

- **Autenticação:** Não.

**Nome da Ação:** tag\_show

- **Descrição:** Retorna os metadados detalhados de uma tag.

- **Método HTTP:** GET ou POST

- **Parâmetros (para GET na URL ou no corpo JSON para POST):**

* id (string, obrigatório): O ID ou nome da tag.

* vocabulary\_id (string, opcional): ID do vocabulário (se aplicável).

* include\_datasets (boolean, opcional): Inclui uma lista de datasets associados à tag.

- **Autenticação:** Não.


### **Ações de Escrita (Criação - Requerem Autenticação)**

**Nome da Ação:** package\_create

- **Descrição:** Cria um novo dataset (pacote).

- **Método HTTP:** POST

- **Corpo da Requisição (JSON - Parâmetros Obrigatórios):**

* name (string): Nome/ID único para o dataset (ex: meu-dataset-novo).

* owner\_org (string): ID da organização proprietária.

- **Corpo da Requisição (JSON - Parâmetros Opcionais Comuns):**

* title (string): Título legível.

* notes (string): Descrição.

* tags (lista de objetos, ex: \[{"name": "tag1"}, {"name": "tag2"}]).

* resources (lista de objetos, definindo os recursos do dataset).

* license\_id (string): ID da licença.

* private (boolean): Define se o dataset é privado.

- **Autenticação:** Sim.

**Nome da Ação:** resource\_create

- **Descrição:** Adiciona um novo recurso a um dataset existente.

- **Método HTTP:** POST (Pode ser multipart/form-data para uploads de arquivo, ou application/json para links).

- **Corpo da Requisição (JSON ou FormData - Parâmetros Obrigatórios):**

* package\_id (string): ID do dataset ao qual o recurso pertence.

* url (string): URL do recurso (se não for upload direto). Ou omitido se upload for usado.

- **Corpo da Requisição (JSON ou FormData - Parâmetros Opcionais Comuns):**

* name (string): Nome do recurso.

* description (string): Descrição.

* format (string): Formato do arquivo (ex: CSV, JSON).

* upload (arquivo): Usado para upload direto de arquivo (requer multipart/form-data).

- **Autenticação:** Sim.

**Nome da Ação:** organization\_create / group\_create

- **Descrição:** Cria uma nova organização ou grupo.

- **Método HTTP:** POST

- **Corpo da Requisição (JSON - Parâmetros Obrigatórios):**

* name (string): Nome/ID único para a organização/grupo.

- **Corpo da Requisição (JSON - Parâmetros Opcionais Comuns):**

* title (string): Título legível.

* description (string): Descrição.

* image\_url (string): URL para uma imagem/logo.

- **Autenticação:** Sim.


### **Ações de Escrita (Atualização - Requerem Autenticação)**

**Nota:** Ações \_update geralmente substituem todo o objeto, enquanto ações \_patch atualizam apenas os campos fornecidos.

**Nome da Ação:** package\_update / package\_patch

- **Descrição:** Atualiza um dataset existente (total ou parcialmente).

- **Método HTTP:** POST

- **Corpo da Requisição (JSON - Parâmetros Obrigatórios):**

* id (string) ou name (string): Identificador do dataset a ser atualizado.

- **Corpo da Requisição (JSON - Outros Parâmetros):** Qualquer campo do dataset que se deseja modificar (ex: title, notes, tags, resources). Para package\_update, todos os campos não fornecidos podem ser removidos ou redefinidos para o padrão. Para package\_patch, apenas os campos fornecidos são alterados.

- **Autenticação:** Sim.

**Nome da Ação:** resource\_update / resource\_patch

- **Descrição:** Atualiza um recurso existente (total ou parcialmente).

- **Método HTTP:** POST

- **Corpo** da Requisição (JSON **- Parâmetros Obrigatórios):**

* id (string): ID do recurso a ser atualizado.

- **Corpo da Requisição (JSON - Outros Parâmetros):** Campos do recurso a modificar (ex: name, url, format, description).

- **Autenticação:** Sim.

**Nome da Ação:** organization\_update / group\_update (e suas variantes \_patch)

- **Descrição:** Atualiza uma organização ou grupo existente.

- **Método HTTP:** POST

- **Corpo** da Requisição (JSON - Parâmetros **Obrigatórios):**

* id (string) ou name (string): Identificador da organização/grupo.

- **Corpo da Requisição (JSON - Outros Parâmetros):** Campos a modificar.

- **Autenticação:** Sim.


### **Ações de Escrita (Exclusão - Requerem Autenticação)**

**Nome da Ação:** package\_delete

- **Descrição:** Marca um dataset como deletado (não o remove permanentemente do banco de dados).

- **Método HTTP:** POST

- **Corpo da Requisição (JSON - Parâmetros Obrigatórios):**

* id (string): ID ou nome do dataset a ser deletado.

- **Autenticação:** Sim.

**Nome da Ação:** resource\_delete

- **Descrição:** Remove um recurso de um dataset.

- **Método HTTP:** POST

- **Corpo da Requisição (JSON - Parâmetros Obrigatórios):**

* id (string): ID do recurso a ser deletado.

- **Autenticação:** Sim.

**Nome da Ação:** organization\_delete / group\_delete

- **Descrição:** Marca uma organização ou grupo como deletado.

- **Método HTTP:** POST

- **Corpo da Requisição (JSON - Parâmetros Obrigatórios):**

* id (string): ID ou nome da organização/grupo a ser deletado.

- **Autenticação:** Sim.

Este guia rápido não é exaustivo. Para detalhes completos, parâmetros opcionais e outras ações disponíveis, consulte a documentação oficial da API do CKAN ou as seções anteriores deste manual.