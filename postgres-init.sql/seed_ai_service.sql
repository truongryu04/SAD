-- Seed data for ai_service_db (PostgreSQL)
-- Run on ai_service_db

INSERT INTO app_airequest (
    id, prompt, response, model_name, status, created_at
)
SELECT
    g,
    'Prompt mẫu số ' || g,
    'Response mẫu số ' || g,
    CASE WHEN g % 2 = 0 THEN 'llama3.1' ELSE 'demo-model' END,
    CASE WHEN g % 5 = 0 THEN 'queued' ELSE 'completed' END,
    NOW() - (g || ' minutes')::interval
FROM generate_series(1, 200) AS g
ON CONFLICT (id) DO UPDATE SET
    prompt = EXCLUDED.prompt,
    response = EXCLUDED.response,
    model_name = EXCLUDED.model_name,
    status = EXCLUDED.status;

-- 120 vector index rows (embedding dim=256)
INSERT INTO app_productvectorindex (
    id, item_type, item_id, name, brand, price, stock, description,
    content_text, metadata, embedding, updated_at
)
SELECT
    g,
    CASE WHEN g % 2 = 0 THEN 'mobile' ELSE 'laptop' END,
    g,
    'Indexed item ' || g,
    CASE WHEN g % 2 = 0 THEN 'Samsung' ELSE 'Dell' END,
    (10000000 + g * 12345)::text,
    5 + (g % 70),
    'Vectorized product ' || g,
    'Content text for semantic retrieval item ' || g,
    jsonb_build_object('source', 'seed', 'index', g),
    ('[0.1' || repeat(',0.1', 255) || ']')::vector,
    NOW() - (g || ' minutes')::interval
FROM generate_series(1, 120) AS g
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    brand = EXCLUDED.brand,
    price = EXCLUDED.price,
    stock = EXCLUDED.stock,
    description = EXCLUDED.description,
    content_text = EXCLUDED.content_text,
    metadata = EXCLUDED.metadata,
    embedding = EXCLUDED.embedding,
    updated_at = NOW();

SELECT setval(pg_get_serial_sequence('app_airequest', 'id'), (SELECT GREATEST(MAX(id), 1) FROM app_airequest));
SELECT setval(pg_get_serial_sequence('app_productvectorindex', 'id'), (SELECT GREATEST(MAX(id), 1) FROM app_productvectorindex));
