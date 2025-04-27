-- 1. Commence une transaction pour tout faire proprement
BEGIN TRANSACTION;

-- 2. Crée une colonne temporaire pour stocker le timestamp en entier
ALTER TABLE stats ADD COLUMN timestamp_temp INTEGER;

-- 3. Remplis cette colonne en convertissant l'ancien texte
UPDATE stats
SET timestamp_temp = strftime('%s', timestamp);

-- 4. Supprime l'ancienne colonne (SQLite ne supporte pas DROP COLUMN directement, on devra recréer)
-- Donc, on crée une nouvelle table avec la bonne structure
CREATE TABLE stats_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guide_id INTEGER,
    timestamp INTEGER, -- attention : maintenant c'est un entier
    likes INTEGER,
    visitors INTEGER,
    favorites INTEGER,
    FOREIGN KEY (guide_id) REFERENCES guides(id)
);

-- 5. Copie les données dans la nouvelle table
INSERT INTO stats_new (id, guide_id, timestamp, likes, visitors, favorites)
SELECT id, guide_id, timestamp_temp, likes, visitors, favorites
FROM stats;

-- 6. Supprime l'ancienne table
DROP TABLE stats;

-- 7. Renomme la nouvelle table
ALTER TABLE stats_new RENAME TO stats;

-- 8. Fin de la transaction
COMMIT;