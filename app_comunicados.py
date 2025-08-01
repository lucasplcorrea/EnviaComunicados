import streamlit as st
import subprocess
import os
import pandas as pd
from datetime import datetime
import sys
import time
from status_manager import StatusManager
import base64

# Diretórios
UPLOAD_DIR = "uploads_comunicados"
COLABORADORES_DIR = "colaboradores"
ENVIADOS_DIR = "enviados_comunicados"

# Garante que as pastas existem
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(COLABORADORES_DIR, exist_ok=True)
os.makedirs(ENVIADOS_DIR, exist_ok=True)

# Configurações da página
st.set_page_config(page_title="Envio de Comunicados", page_icon="📢")
st.title("📢 Sistema de Envio de Comunicados")

# Inicializar StatusManager
status_manager = StatusManager("comunicados_status.json")

# Função para carregar colaboradores
def load_colaboradores():
    """Carrega a planilha de colaboradores"""
    colaboradores_file = os.path.join(COLABORADORES_DIR, "colaboradores.xlsx")
    if os.path.exists(colaboradores_file):
        try:
            return pd.read_excel(colaboradores_file)
        except Exception as e:
            st.error(f"Erro ao carregar colaboradores: {e}")
            return None
    return None

# Função para salvar colaboradores
def save_colaboradores(df):
    """Salva a planilha de colaboradores"""
    colaboradores_file = os.path.join(COLABORADORES_DIR, "colaboradores.xlsx")
    try:
        df.to_excel(colaboradores_file, index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar colaboradores: {e}")
        return False

# Função para criar template de colaboradores
def create_template():
    """Cria um template de colaboradores"""
    template_data = {
        'Nome': ['João Silva', 'Maria Santos', 'Pedro Oliveira'],
        'Telefone': ['11999999999', '11888888888', '11777777777'],
        'Setor': ['Administrativo', 'Operacional', 'Técnico'],
        'Obra': ['Obra A', 'Obra B', 'Obra A']
    }
    return pd.DataFrame(template_data)

# Seção de Status de Execução
st.subheader("📊 Status de Execução")
status = status_manager.get_status()

if status["is_running"]:
    st.warning("🔄 **Execução em andamento!**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Progresso", f"{status['processed_employees']}/{status['total_employees']}")
    with col2:
        st.metric("Sucessos", status['successful_sends'])
    with col3:
        st.metric("Falhas", status['failed_sends'])
    
    # Barra de progresso
    progress = status_manager.get_progress_percentage()
    st.progress(progress / 100)
    st.text(f"Progresso: {progress:.1f}%")
    
    # Status atual
    if status["current_step"]:
        st.info(f"**Etapa atual:** {status['current_step']}")
    
    if status["current_employee"]:
        st.info(f"**Funcionário atual:** {status['current_employee']}")
    
    # Botão para atualizar status
    if st.button("🔄 Atualizar Status", key="refresh_status"):
        st.rerun()
    
    # Botão para resetar (emergência)
    if st.button("🛑 Parar Execução (Emergência)", key="stop_execution"):
        status_manager.reset_status()
        st.success("Execução interrompida!")
        st.rerun()

else:
    if status["end_time"]:
        st.success("✅ **Última execução finalizada**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Processado", status['processed_employees'])
        with col2:
            st.metric("Sucessos", status['successful_sends'])
        with col3:
            st.metric("Falhas", status['failed_sends'])
    else:
        st.info("ℹ️ **Nenhuma execução em andamento**")

st.markdown("---")

# Seção de gerenciamento de colaboradores
st.subheader("👥 Gerenciamento de Colaboradores")

# Tabs para diferentes funcionalidades
tab1, tab2, tab3 = st.tabs(["📋 Visualizar Colaboradores", "➕ Adicionar", "📊 Upload de Planilha"])

with tab1:
    st.markdown("### Lista de Colaboradores")
    df_colaboradores = load_colaboradores()
    
    if df_colaboradores is not None and not df_colaboradores.empty:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            setor_filter = st.selectbox(
                "Filtrar por setor:",
                ["Todos"] + list(df_colaboradores['Setor'].unique()),
                key="setor_filter"
            )
        with col2:
            obra_filter = st.selectbox(
                "Filtrar por obra:",
                ["Todos"] + list(df_colaboradores['Obra'].unique()),
                key="obra_filter"
            )
        
        # Aplicar filtros
        filtered_df = df_colaboradores.copy()
        if setor_filter != "Todos":
            filtered_df = filtered_df[filtered_df['Setor'] == setor_filter]
        if obra_filter != "Todos":
            filtered_df = filtered_df[filtered_df['Obra'] == obra_filter]
        
        st.dataframe(filtered_df, use_container_width=True)
        st.info(f"Total de colaboradores: {len(filtered_df)}")
        
    else:
        st.warning("Nenhum colaborador cadastrado. Use a aba 'Adicionar' ou 'Upload de Planilha' para adicionar colaboradores.")

with tab2:
    st.markdown("### Adicionar Colaboradores")
    
    # Formulário para adicionar colaborador
    with st.form("add_colaborador"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome completo")
            telefone = st.text_input("Telefone (com DDD)")
        with col2:
            setor = st.text_input("Setor")
            obra = st.text_input("Obra")
        
        submitted = st.form_submit_button("Adicionar Colaborador")
        
        if submitted:
            if nome and telefone and setor and obra:
                df_colaboradores = load_colaboradores()
                if df_colaboradores is None:
                    df_colaboradores = pd.DataFrame(columns=['Nome', 'Telefone', 'Setor', 'Obra'])
                
                # Adicionar novo colaborador
                new_row = pd.DataFrame({
                    'Nome': [nome],
                    'Telefone': [telefone],
                    'Setor': [setor],
                    'Obra': [obra]
                })
                df_colaboradores = pd.concat([df_colaboradores, new_row], ignore_index=True)
                
                if save_colaboradores(df_colaboradores):
                    st.success(f"Colaborador {nome} adicionado com sucesso!")
                    st.rerun()
            else:
                st.error("Todos os campos são obrigatórios!")
    
    # Opção para criar template
    if st.button("📄 Criar Template de Exemplo"):
        template_df = create_template()
        if save_colaboradores(template_df):
            st.success("Template criado com sucesso!")
            st.rerun()

with tab3:
    st.markdown("### Upload de Planilha de Colaboradores")
    st.info("A planilha deve conter as colunas: Nome, Telefone, Setor, Obra")
    
    uploaded_file = st.file_uploader(
        "📎 Enviar planilha Excel (.xlsx)",
        type="xlsx",
        key="upload_colaboradores"
    )
    
    if uploaded_file:
        try:
            df_uploaded = pd.read_excel(uploaded_file)
            
            # Verificar se tem as colunas necessárias
            required_columns = ['Nome', 'Telefone', 'Setor', 'Obra']
            if all(col in df_uploaded.columns for col in required_columns):
                st.success("✅ Planilha válida!")
                st.dataframe(df_uploaded)
                
                if st.button("💾 Salvar Colaboradores"):
                    if save_colaboradores(df_uploaded):
                        st.success("Colaboradores salvos com sucesso!")
                        st.rerun()
            else:
                st.error(f"A planilha deve conter as colunas: {', '.join(required_columns)}")
                st.write("Colunas encontradas:", list(df_uploaded.columns))
                
        except Exception as e:
            st.error(f"Erro ao ler planilha: {e}")

st.markdown("---")

# Seção de envio de comunicados
st.subheader("📤 Envio de Comunicados")

st.markdown("""
### 📝 Etapas:
1️⃣ Faça upload do arquivo de comunicado (imagem ou PDF)  
2️⃣ Selecione os colaboradores que irão receber  
3️⃣ Digite a mensagem que acompanhará o arquivo  
4️⃣ Clique em **Enviar Comunicado** para usar a Evolution API
""")

# Upload do arquivo de comunicado
st.markdown("### 📎 Upload do Comunicado")
uploaded_comunicado = st.file_uploader(
    "Enviar arquivo de comunicado (PDF, JPG, PNG)",
    type=['pdf', 'jpg', 'jpeg', 'png'],
    key="upload_comunicado"
)

comunicado_path = None
if uploaded_comunicado:
    comunicado_path = os.path.join(UPLOAD_DIR, uploaded_comunicado.name)
    with open(comunicado_path, "wb") as f:
        f.write(uploaded_comunicado.read())
    st.success(f"✅ {uploaded_comunicado.name} salvo!")
    
    # Mostrar preview do arquivo
    if uploaded_comunicado.type.startswith('image'):
        st.image(comunicado_path, caption="Preview do comunicado", width=300)
    else:
        st.info("📄 Arquivo PDF carregado com sucesso")

# Seleção de destinatários
st.markdown("### 👥 Seleção de Destinatários")
df_colaboradores = load_colaboradores()

if df_colaboradores is not None and not df_colaboradores.empty:
    # Opções de seleção
    selection_mode = st.radio(
        "Como deseja selecionar os destinatários?",
        ["Selecionar individualmente", "Por setor", "Por obra", "Todos os colaboradores"],
        key="selection_mode"
    )
    
    selected_colaboradores = pd.DataFrame()
    
    if selection_mode == "Selecionar individualmente":
        selected_names = st.multiselect(
            "Selecione os colaboradores:",
            df_colaboradores['Nome'].tolist(),
            key="individual_selection"
        )
        selected_colaboradores = df_colaboradores[df_colaboradores['Nome'].isin(selected_names)]
        
    elif selection_mode == "Por setor":
        selected_setores = st.multiselect(
            "Selecione os setores:",
            df_colaboradores['Setor'].unique().tolist(),
            key="setor_selection"
        )
        selected_colaboradores = df_colaboradores[df_colaboradores['Setor'].isin(selected_setores)]
        
    elif selection_mode == "Por obra":
        selected_obras = st.multiselect(
            "Selecione as obras:",
            df_colaboradores['Obra'].unique().tolist(),
            key="obra_selection"
        )
        selected_colaboradores = df_colaboradores[df_colaboradores['Obra'].isin(selected_obras)]
        
    elif selection_mode == "Todos os colaboradores":
        selected_colaboradores = df_colaboradores.copy()
    
    # Mostrar seleção
    if not selected_colaboradores.empty:
        st.success(f"✅ {len(selected_colaboradores)} colaborador(es) selecionado(s)")
        with st.expander("Ver colaboradores selecionados"):
            st.dataframe(selected_colaboradores)
    else:
        st.warning("Nenhum colaborador selecionado")

else:
    st.warning("Nenhum colaborador cadastrado. Adicione colaboradores primeiro.")

# Mensagem do comunicado
st.markdown("### 💬 Mensagem do Comunicado")
mensagem_comunicado = st.text_area(
    "Digite a mensagem que acompanhará o arquivo:",
    placeholder="Ex: Prezados colaboradores, segue comunicado importante sobre...",
    height=100,
    key="mensagem_comunicado"
)

# Botão de envio
if st.button(
    "📤 Enviar Comunicado via Evolution API", 
    key="btn_enviar_comunicado",
    disabled=status_manager.is_running()
):
    # Validações
    if status_manager.is_running():
        st.error("❌ Já existe uma execução em andamento. Aguarde a conclusão.")
    elif not comunicado_path and not mensagem_comunicado.strip():
        st.error("❌ Digite uma mensagem ou faça upload de um arquivo para enviar.")
    elif df_colaboradores is None or selected_colaboradores.empty:
        st.error("❌ Nenhum colaborador foi selecionado.")
    else:
        # Salvar dados temporários para o script de envio
        temp_data = {
            'colaboradores': selected_colaboradores.to_dict('records'),
            'comunicado_path': comunicado_path if comunicado_path and os.path.exists(comunicado_path) else None,
            'mensagem': mensagem_comunicado.strip() if mensagem_comunicado.strip() else None
        }
        
        import json
        with open('temp_comunicado_data.json', 'w', encoding='utf-8') as f:
            json.dump(temp_data, f, ensure_ascii=False, indent=2)
        
        with st.status("📤 Enviando comunicado via API...", expanded=True) as status_widget:
            result = subprocess.run(
                [sys.executable, "send_comunicados_evolution.py"],
                capture_output=True,
                text=True
            )
            st.code(result.stdout)
            if result.stderr:
                st.error(result.stderr)
                status_widget.update(label="❌ Erro no envio.", state="error")
            else:
                st.success("✅ Comunicado enviado com sucesso!")
                status_widget.update(label="✅ Envio concluído.", state="complete")

# Status detalhado por funcionário (se houver execução)
if status["employees_status"]:
    st.subheader("📋 Status Detalhado por Funcionário")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "Filtrar por status:",
            ["Todos", "✅ Enviado", "❌ Falha", "🔄 Processando", "⏳ Aguardando"],
            key="detailed_status_filter"
        )
    
    with col2:
        search_name = st.text_input("Buscar por nome:", key="detailed_search_name")
    
    # Mostrar status dos funcionários
    for emp_id, emp_data in status["employees_status"].items():
        # Aplicar filtros
        status_emoji = {
            "success": "✅ Enviado",
            "failed": "❌ Falha", 
            "processing": "🔄 Processando"
        }.get(emp_data["status"], "⏳ Aguardando")
        
        if status_filter != "Todos" and status_emoji != status_filter:
            continue
            
        if search_name and search_name.lower() not in emp_data["name"].lower():
            continue
        
        with st.expander(f"{status_emoji} {emp_data['name']} (Tel: {emp_data['phone']})"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Status:** {emp_data['status']}")
                st.write(f"**Mensagem:** {emp_data['message']}")
            with col2:
                if emp_data.get('timestamp'):
                    timestamp = datetime.fromisoformat(emp_data['timestamp'])
                    st.write(f"**Última atualização:** {timestamp.strftime('%d/%m/%Y %H:%M:%S')}")

# Visualizar arquivos enviados
with st.expander("📄 Ver arquivos de comunicado enviados"):
    files = []
    if os.path.exists(ENVIADOS_DIR):
        files = os.listdir(ENVIADOS_DIR)
    
    if files:
        for f in sorted(files):
            st.text(f)
    else:
        st.info("Nenhum arquivo de comunicado enviado ainda.")