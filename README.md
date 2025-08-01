# Sistema de Envio de Comunicados via Evolution API

Este aplicativo permite ao RH enviar comunicados gerais (imagens ou PDFs) para colaboradores selecionados via Evolution API, usando uma interface web construída com Streamlit.

## Funcionalidades

- 📋 **Gerenciamento de Colaboradores**: Cadastro e visualização de colaboradores com informações de nome, telefone, setor e obra
- 📤 **Envio de Comunicados**: Upload de arquivos (imagem ou PDF) e envio para colaboradores selecionados
- 🎯 **Seleção Flexível**: Selecione destinatários individualmente, por setor, por obra ou todos os colaboradores
- 📊 **Monitoramento em Tempo Real**: Acompanhe o status de envio de cada colaborador
- 🔄 **Controle de Execução**: Sistema de status para evitar execuções simultâneas

## Estrutura de Arquivos

```
├── app_comunicados.py              # Interface principal Streamlit
├── send_comunicados_evolution.py   # Script de envio via Evolution API
├── status_manager.py               # Gerenciador de status
├── requirements.txt                # Dependências Python
├── .env.example                    # Exemplo de configuração
└── README.md                       # Esta documentação
```

## Instalação

1. **Clone ou baixe os arquivos do projeto**

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure as variáveis de ambiente:**
   - Copie o arquivo `.env.example` para `.env`
   - Edite o arquivo `.env` com suas configurações da Evolution API:
   ```
   EVOLUTION_SERVER_URL=https://sua-evolution-api.com
   EVOLUTION_API_KEY=sua_api_key_aqui
   EVOLUTION_INSTANCE_NAME=nome_da_instancia
   ```

## Como Usar

1. **Inicie o aplicativo:**
   ```bash
   streamlit run app_comunicados.py
   ```

2. **Gerencie Colaboradores:**
   - Use a aba "Adicionar/Editar" para cadastrar colaboradores manualmente
   - Ou use a aba "Upload de Planilha" para importar uma planilha Excel
   - A planilha deve conter as colunas: Nome, Telefone, Setor, Obra

3. **Envie Comunicados:**
   - Faça upload do arquivo de comunicado (PDF, JPG, PNG)
   - Selecione os destinatários (individual, por setor, por obra ou todos)
   - Digite a mensagem que acompanhará o arquivo
   - Clique em "Enviar Comunicado via Evolution API"

4. **Monitore o Envio:**
   - Acompanhe o progresso em tempo real
   - Veja o status detalhado de cada colaborador
   - Consulte os logs de erro se necessário

## Estrutura da Planilha de Colaboradores

A planilha Excel deve conter as seguintes colunas:

| Nome | Telefone | Setor | Obra |
|------|----------|-------|------|
| João Silva | 11999999999 | Administrativo | Obra A |
| Maria Santos | 11888888888 | Operacional | Obra B |

## Diferenças do Sistema de Holerites

Este sistema foi adaptado do sistema de envio de holerites com as seguintes modificações:

- **Estrutura de Colaboradores**: Simplificada para incluir apenas Nome, Telefone, Setor e Obra
- **Arquivos Genéricos**: Suporta qualquer tipo de imagem ou PDF (não apenas holerites)
- **Seleção Flexível**: Permite seleção por diferentes critérios
- **Mensagem Personalizada**: O usuário define a mensagem que acompanha o arquivo
- **Status Separado**: Usa arquivo de status independente (`comunicados_status.json`)

## Arquivos Gerados

- `colaboradores/colaboradores.xlsx`: Planilha com dados dos colaboradores
- `uploads_comunicados/`: Arquivos de comunicado enviados pelo usuário
- `enviados_comunicados/`: Cópias dos arquivos enviados com sucesso
- `comunicados_status.json`: Status da execução atual
- `envio_comunicados_evolution_YYYYMMDD_HHMMSS.log`: Logs detalhados de cada execução

## Solução de Problemas

### Erro 401 Unauthorized
- Verifique se a `EVOLUTION_API_KEY` está correta no arquivo `.env`

### Erro 404 Instance Not Found
- Verifique se o `EVOLUTION_INSTANCE_NAME` está correto no arquivo `.env`
- Certifique-se de que a instância está criada e ativa na Evolution API

### Instância não conectada
- Verifique se o WhatsApp está conectado na instância
- Use o QR Code para conectar se necessário

### Timeout ou Rate Limit
- O sistema já possui delays automáticos entre envios
- Em caso de rate limit, aguarde alguns minutos antes de tentar novamente

## Segurança

- Mantenha o arquivo `.env` seguro e não o compartilhe
- As credenciais da API são sensíveis e devem ser protegidas
- Os logs podem conter informações sensíveis, revise antes de compartilhar

## Suporte

Este sistema foi desenvolvido baseado no sistema de envio de holerites existente, mantendo a mesma estrutura e confiabilidade, mas adaptado para comunicados gerais.

Para dúvidas sobre a Evolution API, consulte a documentação oficial da API.