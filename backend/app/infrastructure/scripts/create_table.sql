CREATE TABLE subchamados (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente VARCHAR(255) NOT NULL,
    numero_serie VARCHAR(100) NOT NULL,
    hgid VARCHAR(50) NOT NULL,
    data_fabricacao TIMESTAMP,
    quantidade_exames INTEGER,
    go_premium BOOLEAN DEFAULT FALSE,
    descricao TEXT NOT NULL,
    prioridade VARCHAR(20) DEFAULT 'media',
    status VARCHAR(30) DEFAULT 'aberto',
    analise TEXT,
    imagens JSONB DEFAULT '[]',
    criado_por VARCHAR(255) NOT NULL,
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    prazo_sla TIMESTAMP NOT NULL
);

ALTER TABLE subchamados ENABLE ROW LEVEL SECURITY;

CREATE POLICY permitir_tudo ON subchamados FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY permitir_tudo_servico ON subchamados FOR ALL TO service_role USING (true) WITH CHECK (true);
