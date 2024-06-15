INSERT INTO fundub_synonym (fundub_id, synonym)
SELECT master_id, slave.name
FROM fundub AS slave
JOIN (
    SELECT 1483 AS slave_id, 1482 AS master_id UNION ALL
    SELECT 1488, 1482 UNION ALL
    SELECT 1348, 1229 UNION ALL
    SELECT 1366, 1195 UNION ALL
    SELECT 1373, 1134 UNION ALL
    SELECT 1384, 1175 UNION ALL
    SELECT 1359, 1105 UNION ALL
    SELECT 1425, 1220 UNION ALL
    SELECT 1432, 1431 UNION ALL
    SELECT 1190, 1398 UNION ALL
    SELECT 1455, 1406 UNION ALL
    SELECT 1349, 1141 UNION ALL
    SELECT 1147, 1142 UNION ALL
    SELECT 1379, 1335 UNION ALL
    SELECT 1356, 1115 UNION ALL
    SELECT 1347, 1170 UNION ALL
    SELECT 1367, 1414 UNION ALL
    SELECT 1409, 1137 UNION ALL
    SELECT 1444, 1388 UNION ALL
    SELECT 1167, 1388 UNION ALL
    SELECT 1376, 1140 UNION ALL
    SELECT 1466, 1185 UNION ALL
    SELECT 1382, 1185 UNION ALL
    SELECT 1362, 1163 UNION ALL
    SELECT 1396, 1116 UNION ALL
    SELECT 1371, 1184 UNION ALL
    SELECT 1178, 1100 UNION ALL
    SELECT 1368, 1434 UNION ALL
    SELECT 1126, 1143 UNION ALL
    SELECT 1166, 1446 UNION ALL
    SELECT 1172, 1179
) AS mapping ON slave.id = mapping.slave_id
WHERE slave.name != (SELECT name FROM fundub WHERE id = mapping.master_id)
ON CONFLICT DO NOTHING;

UPDATE fundub
SET telegram = (
    SELECT slave.telegram
    FROM fundub AS slave
    JOIN (
        SELECT 1483 AS slave_id, 1482 AS master_id UNION ALL
        SELECT 1488, 1482 UNION ALL
        SELECT 1348, 1229 UNION ALL
        SELECT 1366, 1195 UNION ALL
        SELECT 1373, 1134 UNION ALL
        SELECT 1384, 1175 UNION ALL
        SELECT 1359, 1105 UNION ALL
        SELECT 1425, 1220 UNION ALL
        SELECT 1432, 1431 UNION ALL
        SELECT 1190, 1398 UNION ALL
        SELECT 1455, 1406 UNION ALL
        SELECT 1349, 1141 UNION ALL
        SELECT 1147, 1142 UNION ALL
        SELECT 1379, 1335 UNION ALL
        SELECT 1356, 1115 UNION ALL
        SELECT 1347, 1170 UNION ALL
        SELECT 1367, 1414 UNION ALL
        SELECT 1409, 1137 UNION ALL
        SELECT 1444, 1388 UNION ALL
        SELECT 1167, 1388 UNION ALL
        SELECT 1376, 1140 UNION ALL
        SELECT 1466, 1185 UNION ALL
        SELECT 1382, 1185 UNION ALL
        SELECT 1362, 1163 UNION ALL
        SELECT 1396, 1116 UNION ALL
        SELECT 1371, 1184 UNION ALL
        SELECT 1178, 1100 UNION ALL
        SELECT 1368, 1434 UNION ALL
        SELECT 1126, 1143 UNION ALL
        SELECT 1166, 1446 UNION ALL
        SELECT 1172, 1179
    ) AS mapping ON slave.id = mapping.slave_id
    WHERE fundub.id = mapping.master_id AND slave.id = mapping.slave_id AND fundub.telegram IS NULL
)
WHERE EXISTS (
    SELECT 1
    FROM (
        SELECT 1483 AS slave_id, 1482 AS master_id UNION ALL
        SELECT 1488, 1482 UNION ALL
        SELECT 1348, 1229 UNION ALL
        SELECT 1366, 1195 UNION ALL
        SELECT 1373, 1134 UNION ALL
        SELECT 1384, 1175 UNION ALL
        SELECT 1359, 1105 UNION ALL
        SELECT 1425, 1220 UNION ALL
        SELECT 1432, 1431 UNION ALL
        SELECT 1190, 1398 UNION ALL
        SELECT 1455, 1406 UNION ALL
        SELECT 1349, 1141 UNION ALL
        SELECT 1147, 1142 UNION ALL
        SELECT 1379, 1335 UNION ALL
        SELECT 1356, 1115 UNION ALL
        SELECT 1347, 1170 UNION ALL
        SELECT 1367, 1414 UNION ALL
        SELECT 1409, 1137 UNION ALL
        SELECT 1444, 1388 UNION ALL
        SELECT 1167, 1388 UNION ALL
        SELECT 1376, 1140 UNION ALL
        SELECT 1466, 1185 UNION ALL
        SELECT 1382, 1185 UNION ALL
        SELECT 1362, 1163 UNION ALL
        SELECT 1396, 1116 UNION ALL
        SELECT 1371, 1184 UNION ALL
        SELECT 1178, 1100 UNION ALL
        SELECT 1368, 1434 UNION ALL
        SELECT 1126, 1143 UNION ALL
        SELECT 1166, 1446 UNION ALL
        SELECT 1172, 1179
    ) AS mapping
    WHERE fundub.id = mapping.master_id
);

UPDATE anime_fundub
SET fundub_id = CASE
    WHEN fundub_id = 1483 THEN 1482
    WHEN fundub_id = 1488 THEN 1482
    WHEN fundub_id = 1348 THEN 1229
    WHEN fundub_id = 1366 THEN 1195
    WHEN fundub_id = 1373 THEN 1134
    WHEN fundub_id = 1384 THEN 1175
    WHEN fundub_id = 1359 THEN 1105
    WHEN fundub_id = 1425 THEN 1220
    WHEN fundub_id = 1432 THEN 1431
    WHEN fundub_id = 1190 THEN 1398
    WHEN fundub_id = 1455 THEN 1406
    WHEN fundub_id = 1349 THEN 1141
    WHEN fundub_id = 1147 THEN 1142
    WHEN fundub_id = 1379 THEN 1335
    WHEN fundub_id = 1356 THEN 1115
    WHEN fundub_id = 1347 THEN 1170
    WHEN fundub_id = 1367 THEN 1414
    WHEN fundub_id = 1409 THEN 1137
    WHEN fundub_id = 1444 THEN 1388
    WHEN fundub_id = 1167 THEN 1388
    WHEN fundub_id = 1376 THEN 1140
    WHEN fundub_id = 1466 THEN 1185
    WHEN fundub_id = 1382 THEN 1185
    WHEN fundub_id = 1362 THEN 1163
    WHEN fundub_id = 1396 THEN 1116
    WHEN fundub_id = 1371 THEN 1184
    WHEN fundub_id = 1178 THEN 1100
    WHEN fundub_id = 1368 THEN 1434
    WHEN fundub_id = 1126 THEN 1143
    WHEN fundub_id = 1166 THEN 1446
    WHEN fundub_id = 1172 THEN 1179
END
WHERE fundub_id IN (1483, 1488, 1348, 1366, 1373, 1384, 1359, 1425, 1432, 1190, 1455, 1349, 1147, 1379, 1356, 1347, 1367, 1409, 1444, 1167, 1376, 1466, 1382, 1362, 1396, 1371, 1178, 1368, 1126, 1166, 1172);

UPDATE fundub_synonym
SET fundub_id = CASE
    WHEN fundub_id = 1483 THEN 1482
    WHEN fundub_id = 1488 THEN 1482
    WHEN fundub_id = 1348 THEN 1229
    WHEN fundub_id = 1366 THEN 1195
    WHEN fundub_id = 1373 THEN 1134
    WHEN fundub_id = 1384 THEN 1175
    WHEN fundub_id = 1359 THEN 1105
    WHEN fundub_id = 1425 THEN 1220
    WHEN fundub_id = 1432 THEN 1431
    WHEN fundub_id = 1190 THEN 1398
    WHEN fundub_id = 1455 THEN 1406
    WHEN fundub_id = 1349 THEN 1141
    WHEN fundub_id = 1147 THEN 1142
    WHEN fundub_id = 1379 THEN 1335
    WHEN fundub_id = 1356 THEN 1115
    WHEN fundub_id = 1347 THEN 1170
    WHEN fundub_id = 1367 THEN 1414
    WHEN fundub_id = 1409 THEN 1137
    WHEN fundub_id = 1444 THEN 1388
    WHEN fundub_id = 1167 THEN 1388
    WHEN fundub_id = 1376 THEN 1140
    WHEN fundub_id = 1466 THEN 1185
    WHEN fundub_id = 1382 THEN 1185
    WHEN fundub_id = 1362 THEN 1163
    WHEN fundub_id = 1396 THEN 1116
    WHEN fundub_id = 1371 THEN 1184
    WHEN fundub_id = 1178 THEN 1100
    WHEN fundub_id = 1368 THEN 1434
    WHEN fundub_id = 1126 THEN 1143
    WHEN fundub_id = 1166 THEN 1446
    WHEN fundub_id = 1172 THEN 1179
END
WHERE fundub_id IN (1483, 1488, 1348, 1366, 1373, 1384, 1359, 1425, 1432, 1190, 1455, 1349, 1147, 1379, 1356, 1347, 1367, 1409, 1444, 1167, 1376, 1466, 1382, 1362, 1396, 1371, 1178, 1368, 1126, 1166, 1172);

UPDATE fundub_episode
SET fundub_id = CASE
    WHEN fundub_id = 1483 THEN 1482
    WHEN fundub_id = 1488 THEN 1482
    WHEN fundub_id = 1348 THEN 1229
    WHEN fundub_id = 1366 THEN 1195
    WHEN fundub_id = 1373 THEN 1134
    WHEN fundub_id = 1384 THEN 1175
    WHEN fundub_id = 1359 THEN 1105
    WHEN fundub_id = 1425 THEN 1220
    WHEN fundub_id = 1432 THEN 1431
    WHEN fundub_id = 1190 THEN 1398
    WHEN fundub_id = 1455 THEN 1406
    WHEN fundub_id = 1349 THEN 1141
    WHEN fundub_id = 1147 THEN 1142
    WHEN fundub_id = 1379 THEN 1335
    WHEN fundub_id = 1356 THEN 1115
    WHEN fundub_id = 1347 THEN 1170
    WHEN fundub_id = 1367 THEN 1414
    WHEN fundub_id = 1409 THEN 1137
    WHEN fundub_id = 1444 THEN 1388
    WHEN fundub_id = 1167 THEN 1388
    WHEN fundub_id = 1376 THEN 1140
    WHEN fundub_id = 1466 THEN 1185
    WHEN fundub_id = 1382 THEN 1185
    WHEN fundub_id = 1362 THEN 1163
    WHEN fundub_id = 1396 THEN 1116
    WHEN fundub_id = 1371 THEN 1184
    WHEN fundub_id = 1178 THEN 1100
    WHEN fundub_id = 1368 THEN 1434
    WHEN fundub_id = 1126 THEN 1143
    WHEN fundub_id = 1166 THEN 1446
    WHEN fundub_id = 1172 THEN 1179
END
WHERE fundub_id IN (1483, 1488, 1348, 1366, 1373, 1384, 1359, 1425, 1432, 1190, 1455, 1349, 1147, 1379, 1356, 1347, 1367, 1409, 1444, 1167, 1376, 1466, 1382, 1362, 1396, 1371, 1178, 1368, 1126, 1166, 1172);

DELETE FROM fundub
WHERE id IN (1483, 1488, 1348, 1366, 1373, 1384, 1359, 1425, 1432, 1190, 1455, 1349, 1147, 1379, 1356, 1347, 1367, 1409, 1444, 1167, 1376, 1466, 1382, 1362, 1396, 1371, 1178, 1368, 1126, 1166, 1172);

UPDATE fundub
SET telegram = CASE id
    WHEN 1464 THEN 'https://t.me/channel3737'
    WHEN 1173 THEN 'https://t.me/TO_48Volts'
    WHEN 1446 THEN 'https://t.me/foryouanime_4ua'
    WHEN 1393 THEN 'https://t.me/AIDsubStudio'
    WHEN 1481 THEN 'https://t.me/AniCoin_official'
    WHEN 1473 THEN 'https://t.me/AniFanUa'
    WHEN 1358 THEN 'https://t.me/Anikoe_studio'
    WHEN 1405 THEN 'https://t.me/anitube_in_ua'
    WHEN 1351 THEN 'https://t.me/AniUnion'
    WHEN 1233 THEN 'https://t.me/arteamko'
    WHEN 1354 THEN 'https://t.me/Bambooua2022'
    WHEN 1 THEN 'https://t.me/bitari_territory'
    WHEN 1117 THEN 'https://t.me/CrystalVoicesUA'
    WHEN 1395 THEN 'https://t.me/dlggsub'
    WHEN 1184 THEN 'https://t.me/EspadaDub'
    WHEN 1412 THEN 'https://t.me/fairydub'
    WHEN 1389 THEN 'https://t.me/flamestudioua'
    WHEN 1459 THEN 'https://t.me/fomalhaut_dub'
    WHEN 1355 THEN 'https://t.me/subfukuronachi'
    WHEN 1458 THEN 'https://t.me/liben_s'
    WHEN 1403 THEN 'https://t.me/kagawaua'
    WHEN 1415 THEN 'https://t.me/Legat_translate'
    WHEN 1177 THEN 'https://t.me/Legat_translate'
    WHEN 1410 THEN 'https://t.me/otakoi_studio'
    WHEN 1385 THEN 'https://t.me/uamax_dub'
    WHEN 1141 THEN 'https://t.me/animriya_team'
    WHEN 1483 THEN 'https://t.me/inariokami58'
    WHEN 1105 THEN 'https://t.me/robotaholosom'
    WHEN 1134 THEN 'https://t.me/realCossackdubbing'
    WHEN 1129 THEN 'https://t.me/+U75ZKIbxj68QKIM8'
    WHEN 1171 THEN 'https://t.me/kutochok_anime'
    WHEN 1249 THEN 'https://t.me/HatinaDubera'
END
WHERE id IN (1464, 1173, 1446, 1393, 1481, 1473, 1358, 1405, 1351, 1233, 1354, 1, 1117, 1395, 1184, 1412, 1389, 1459, 1355, 1458, 1403, 1415, 1177, 1410, 1385, 1141, 1483, 1105, 1134, 1129, 1171, 1249);
