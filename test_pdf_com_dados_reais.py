"""
Teste de PDF com dados reais da Roda de Ouro
Para identificar exatamente onde está o problema
"""
import os
import sys
import traceback

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from backend.database import get_db, engine
from backend.models import Client, Upload, Atestado
from backend.analytics import Analytics
from backend.insights import InsightsEngine
from backend.report_generator import ReportGenerator

def testar_pdf_com_dados_reais():
    """Testa geração de PDF com dados reais da Roda de Ouro"""
    try:
        print("=" * 60)
        print("TESTE DE PDF COM DADOS REAIS - RODA DE OURO")
        print("=" * 60)
        print()
        
        # Conecta ao banco
        db = next(get_db())
        
        # Busca cliente Roda de Ouro (ID = 4)
        cliente = db.query(Client).filter(Client.id == 4).first()
        if not cliente:
            print("❌ Cliente Roda de Ouro (ID=4) não encontrado!")
            return False
        
        print(f"✅ Cliente encontrado: {cliente.nome}")
        
        # Busca uploads
        uploads = db.query(Upload).filter(Upload.client_id == 4).all()
        if not uploads:
            print("❌ Nenhum upload encontrado para Roda de Ouro!")
            return False
        
        print(f"✅ {len(uploads)} upload(s) encontrado(s)")
        
        # Busca dados como o dashboard faz
        print("\n📊 Buscando dados do dashboard...")
        analytics = Analytics(db)
        insights_engine = InsightsEngine(db)
        
        # Métricas básicas
        try:
            metricas = analytics.metricas_gerais(4)
            print(f"✅ Métricas: {metricas.get('total_atestados', 0)} atestados")
        except Exception as e:
            print(f"❌ Erro ao buscar métricas: {e}")
            traceback.print_exc()
            return False
        
        # Dados básicos
        dados_relatorio = {}
        
        try:
            top_cids = analytics.top_cids(4, 10)
            dados_relatorio['top_cids'] = top_cids
            print(f"✅ TOP CIDs: {len(top_cids)} registros")
        except Exception as e:
            print(f"⚠️ Erro ao buscar TOP CIDs: {e}")
            dados_relatorio['top_cids'] = []
        
        try:
            top_setores = analytics.top_setores(4, 5)
            dados_relatorio['top_setores'] = top_setores
            print(f"✅ TOP Setores: {len(top_setores)} registros")
        except Exception as e:
            print(f"⚠️ Erro ao buscar TOP Setores: {e}")
            dados_relatorio['top_setores'] = []
        
        try:
            evolucao = analytics.evolucao_mensal(4, 12)
            dados_relatorio['evolucao_mensal'] = evolucao
            print(f"✅ Evolução Mensal: {len(evolucao)} meses")
        except Exception as e:
            print(f"⚠️ Erro ao buscar Evolução: {e}")
            dados_relatorio['evolucao_mensal'] = []
        
        try:
            distribuicao_genero = analytics.distribuicao_genero(4)
            dados_relatorio['distribuicao_genero'] = distribuicao_genero
            print(f"✅ Distribuição Gênero: {len(distribuicao_genero)} registros")
        except Exception as e:
            print(f"⚠️ Erro ao buscar Distribuição Gênero: {e}")
            dados_relatorio['distribuicao_genero'] = []
        
        # Dados específicos da Roda de Ouro
        print("\n📊 Buscando dados específicos da Roda de Ouro...")
        
        try:
            classificacao_funcionarios_ro = analytics.classificacao_funcionarios_roda_ouro(4, 15)
            dados_relatorio['classificacao_funcionarios_ro'] = classificacao_funcionarios_ro
            print(f"✅ Classificação Funcionários: {len(classificacao_funcionarios_ro)} registros")
        except Exception as e:
            print(f"⚠️ Erro ao buscar Classificação Funcionários: {e}")
            traceback.print_exc()
            dados_relatorio['classificacao_funcionarios_ro'] = []
        
        try:
            classificacao_setores_ro = analytics.classificacao_setores_roda_ouro(4, 15)
            dados_relatorio['classificacao_setores_ro'] = classificacao_setores_ro
            print(f"✅ Classificação Setores: {len(classificacao_setores_ro)} registros")
        except Exception as e:
            print(f"⚠️ Erro ao buscar Classificação Setores: {e}")
            traceback.print_exc()
            dados_relatorio['classificacao_setores_ro'] = []
        
        try:
            classificacao_doencas_ro = analytics.classificacao_doencas_roda_ouro(4, 15)
            dados_relatorio['classificacao_doencas_ro'] = classificacao_doencas_ro
            print(f"✅ Classificação Doenças: {len(classificacao_doencas_ro)} registros")
        except Exception as e:
            print(f"⚠️ Erro ao buscar Classificação Doenças: {e}")
            traceback.print_exc()
            dados_relatorio['classificacao_doencas_ro'] = []
        
        try:
            dias_ano_coerencia = analytics.dias_atestados_por_ano_coerencia(4)
            dados_relatorio['dias_ano_coerencia'] = dias_ano_coerencia
            print(f"✅ Dias por Ano Coerência: {type(dias_ano_coerencia)}")
            if isinstance(dias_ano_coerencia, dict):
                print(f"   - Anos: {len(dias_ano_coerencia.get('anos', []))}")
        except Exception as e:
            print(f"⚠️ Erro ao buscar Dias por Ano Coerência: {e}")
            traceback.print_exc()
            dados_relatorio['dias_ano_coerencia'] = {}
        
        try:
            analise_coerencia = analytics.analise_atestados_coerencia(4)
            dados_relatorio['analise_coerencia'] = analise_coerencia
            print(f"✅ Análise Coerência: {type(analise_coerencia)}")
        except Exception as e:
            print(f"⚠️ Erro ao buscar Análise Coerência: {e}")
            traceback.print_exc()
            dados_relatorio['analise_coerencia'] = {}
        
        # Gera PDF
        print("\n📄 Gerando PDF com dados reais...")
        exports_dir = "exports"
        os.makedirs(exports_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(exports_dir, f"teste_pdf_dados_reais_{timestamp}.pdf")
        
        report_gen = ReportGenerator(db=db, client_id=4)
        
        # Busca insights
        insights = []
        try:
            insights = insights_engine.gerar_insights(4)
            print(f"✅ Insights: {len(insights)} gerados")
        except Exception as e:
            print(f"⚠️ Erro ao gerar insights: {e}")
            insights = []
        
        # Gera PDF
        try:
            periodo = "Teste - Dados Reais"
            sucesso = report_gen.generate_pdf_report(
                output_path,
                dados_relatorio,
                metricas,
                insights,
                periodo,
                insights_engine,
                client_id=4
            )
            
            if sucesso:
                if os.path.exists(output_path):
                    tamanho = os.path.getsize(output_path)
                    print(f"\n✅ PDF gerado com sucesso!")
                    print(f"   Arquivo: {output_path}")
                    print(f"   Tamanho: {tamanho} bytes")
                    
                    # Valida header
                    with open(output_path, 'rb') as f:
                        header = f.read(8)
                        if header.startswith(b'%PDF'):
                            print(f"   Header: {header[:8]} ✅")
                        else:
                            print(f"   Header: {header[:8]} ❌ INVÁLIDO!")
                    
                    print(f"\n📋 TESTE: Abra o arquivo no Adobe Acrobat Reader")
                    return True
                else:
                    print(f"❌ PDF não foi criado!")
                    return False
            else:
                print(f"❌ Erro ao gerar PDF (retornou False)")
                return False
                
        except Exception as e:
            print(f"❌ ERRO ao gerar PDF: {e}")
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        traceback.print_exc()
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    from datetime import datetime
    sucesso = testar_pdf_com_dados_reais()
    
    print()
    print("=" * 60)
    if sucesso:
        print("✅ Teste concluído")
    else:
        print("❌ Teste falhou - Verifique os erros acima")
    print("=" * 60)

