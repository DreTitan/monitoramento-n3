-- =====================================================
-- Migration: Authentication & Authorization
-- =====================================================

-- Criar tipo enum para roles
CREATE TYPE user_role AS ENUM ('admin', 'engenheiro', 'n3', 'n2');

-- Criar tabela de usuários do app
CREATE TABLE IF NOT EXISTS app_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    nome_completo VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'n3',
    is_active BOOLEAN DEFAULT TRUE,
    totp_secret VARCHAR(255),
    totp_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Criar tabela de audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    user_email VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para audit_logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

-- Função para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para app_users
DROP TRIGGER IF EXISTS update_app_users_updated_at ON app_users;
CREATE TRIGGER update_app_users_updated_at
    BEFORE UPDATE ON app_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Habilitar RLS
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Políticas RLS para app_users (permissivas para desenvolvimento)
DROP POLICY IF EXISTS "Allow all operations on app_users" ON app_users;
CREATE POLICY "Allow all operations on app_users"
    ON app_users FOR ALL
    TO public
    USING (true)
    WITH CHECK (true);

-- Políticas RLS para audit_logs
DROP POLICY IF EXISTS "Allow all operations on audit_logs" ON audit_logs;
CREATE POLICY "Allow all operations on audit_logs"
    ON audit_logs FOR ALL
    TO public
    USING (true)
    WITH CHECK (true);

-- =====================================================
-- Seed: Criar usuário admin inicial
-- A senha é: Admin@123
-- Hash bcrypt: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYWPQFZS3JqS
-- =====================================================
INSERT INTO app_users (email, nome_completo, password_hash, role)
VALUES (
    'admin@goair.com.br',
    'André Souza',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYWPQFZS3JqS',
    'admin'
) ON CONFLICT (email) DO NOTHING;
