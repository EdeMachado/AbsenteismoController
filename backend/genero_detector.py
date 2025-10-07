"""
Detector de gênero por nome
"""

class GeneroDetector:
    """Detecta gênero baseado no primeiro nome"""
    
    # Listas de nomes comuns brasileiros
    NOMES_MASCULINOS = {
        'joao', 'jose', 'antonio', 'francisco', 'carlos', 'paulo', 'pedro', 'lucas', 'luiz', 'marcos',
        'luis', 'gabriel', 'rafael', 'daniel', 'marcelo', 'bruno', 'eduardo', 'felipe', 'fabricio',
        'rodrigo', 'fernando', 'gustavo', 'andre', 'julio', 'cesar', 'sergio', 'ricardo', 'roberto',
        'diego', 'vitor', 'mateus', 'henrique', 'thiago', 'leandro', 'alexandre', 'mauricio', 'renato',
        'anderson', 'wellington', 'adriano', 'leonardo', 'renan', 'vinicius', 'igor', 'caio', 'enzo',
        'samuel', 'nicolas', 'miguel', 'arthur', 'davi', 'bernardo', 'heitor', 'ruan', 'erick',
        'ednaldo', 'edson', 'ademir', 'ademar', 'aldair', 'alex', 'aluisio', 'amilton', 'angelo',
        'aparecido', 'benito', 'carlos', 'celso', 'claudemir', 'claudio', 'cleber', 'cristiano',
        'dalton', 'darlan', 'davidson', 'denis', 'edimar', 'edinaldo', 'edivaldo', 'edmilson',
        'edson', 'elias', 'elton', 'emerson', 'evaldo', 'everton', 'ezequiel', 'fabiano', 'flavio',
        'geovane', 'geraldo', 'gilberto', 'gilmar', 'gilson', 'glauco', 'hamilton', 'humberto',
        'isaac', 'ismael', 'ivan', 'jair', 'jeferson', 'jefferson', 'jhonatan', 'jonas', 'jorge',
        'osvaldo', 'otavio', 'rafael', 'raul', 'reinaldo', 'rogerio', 'ronaldo', 'sebastiao',
        'silvio', 'valdemar', 'valdenir', 'valdir', 'vanderlei', 'wagner', 'waldemar', 'walter',
        'washington', 'wesley', 'william', 'wilson'
    }
    
    NOMES_FEMININOS = {
        'maria', 'ana', 'francisca', 'antonia', 'adriana', 'juliana', 'marcia', 'fernanda', 'patricia',
        'aline', 'amanda', 'bruna', 'camila', 'carla', 'carolina', 'claudia', 'cristina', 'daniela',
        'debora', 'denise', 'elaine', 'fabiana', 'fernanda', 'gabriela', 'gisele', 'helena', 'isabel',
        'jessica', 'julia', 'juliana', 'karina', 'larissa', 'leticia', 'luana', 'luciana', 'mariana',
        'michele', 'monica', 'natalia', 'paula', 'priscila', 'raquel', 'renata', 'roberta', 'sandra',
        'silvia', 'simone', 'sonia', 'tatiana', 'vanessa', 'vera', 'viviane', 'alice', 'beatriz',
        'cecilia', 'clara', 'elisa', 'emilia', 'ester', 'heloisa', 'iris', 'ivone', 'lais', 'lidia',
        'lorena', 'luisa', 'marta', 'miriam', 'nair', 'olivia', 'regina', 'rita', 'rosa', 'rosana',
        'rosangela', 'rose', 'rosilene', 'sabrina', 'solange', 'sueli', 'suzana', 'tais', 'tereza',
        'valeria', 'vania', 'vitoria', 'alessandra', 'andrea', 'andreia', 'angelica', 'barbara',
        'bianca', 'celia', 'cintia', 'clelia', 'cleusa', 'cris', 'cristiane', 'dalva', 'daiana',
        'diana', 'edna', 'eliane', 'elisabete', 'elizabeth', 'erica', 'erika', 'eugenia', 'eunice',
        'fatima', 'flavia', 'geovana', 'giovana', 'gilda', 'gisela', 'graziele', 'ingrid', 'iracema',
        'irene', 'joana', 'josefa', 'jaqueline', 'katia', 'keila', 'kelly', 'lara', 'leila', 'lilian',
        'lourdes', 'lucia', 'luciane', 'luciene', 'maira', 'marcela', 'margarete', 'marina', 'marlene',
        'mayara', 'meire', 'melissa', 'neuza', 'nilda', 'nilza', 'noemi', 'nora', 'olga', 'pamela',
        'poliana', 'quiteria', 'raissa', 'rebeca', 'roseli', 'rosileia', 'sheila', 'shirley', 'silmara',
        'talita', 'tamara', 'tania', 'teresinha', 'thais', 'vera', 'veronica', 'vilma', 'zelia'
    }
    
    @staticmethod
    def detectar(nome_completo: str) -> str:
        """
        Detecta gênero baseado no primeiro nome
        Retorna: 'M', 'F' ou ''
        """
        if not nome_completo or not isinstance(nome_completo, str):
            return ''
        
        # Pega o primeiro nome
        nome_completo = nome_completo.strip()
        if not nome_completo:
            return ''
        
        primeiro_nome = nome_completo.split()[0].lower()
        
        # Remove acentos simples
        primeiro_nome = primeiro_nome.replace('á', 'a').replace('é', 'e').replace('í', 'i')
        primeiro_nome = primeiro_nome.replace('ó', 'o').replace('ú', 'u').replace('ã', 'a')
        primeiro_nome = primeiro_nome.replace('õ', 'o').replace('ç', 'c')
        
        # Verifica nas listas
        if primeiro_nome in GeneroDetector.NOMES_MASCULINOS:
            return 'M'
        elif primeiro_nome in GeneroDetector.NOMES_FEMININOS:
            return 'F'
        
        # Heurística simples: nomes terminados em 'a' geralmente são femininos
        if len(primeiro_nome) > 2 and primeiro_nome[-1] == 'a' and primeiro_nome not in ['garcia', 'costa', 'silva']:
            return 'F'
        
        return ''


