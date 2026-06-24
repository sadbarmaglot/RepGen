-- Стрелки замера: координаты концов и флаг видимости
ALTER TABLE marks ADD COLUMN IF NOT EXISTS measure_points JSONB;
ALTER TABLE marks ADD COLUMN IF NOT EXISTS show_measure_arrow BOOLEAN NOT NULL DEFAULT TRUE;

-- Существующие метки-замеры без геометрии получают стрелку отключённой
-- (зеркалит логику backfillMeasureArrows() на iOS)
UPDATE marks SET show_measure_arrow = FALSE
WHERE type = 'measurement' AND measure_points IS NULL;
