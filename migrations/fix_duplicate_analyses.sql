-- Миграция: Удаление дубликатов анализов и добавление UNIQUE constraint
-- Дата создания: 2026-03-03

-- Удаляем дубликаты, оставляя самую свежую запись для каждого photo_id
DELETE FROM photo_defect_analysis a
USING photo_defect_analysis b
WHERE a.photo_id = b.photo_id
  AND a.id < b.id;

-- Добавляем UNIQUE constraint на photo_id
ALTER TABLE photo_defect_analysis
  ADD CONSTRAINT uq_photo_defect_analysis_photo_id UNIQUE (photo_id);
