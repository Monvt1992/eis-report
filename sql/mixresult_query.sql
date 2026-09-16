WITH mix_data AS (
    SELECT DISTINCT
        [ElementNEBatch],
        [MIXNO],
        [SH],
        [WtAvgEis1],
        [WtAvgEis2],
        [WtAvgEis3],
        [WtAvgEis4],
        ISNULL([WtAvgEis5], 0) AS WtAvgEis5,
        ISNULL([WtAvgEis6], 0) AS WtAvgEis6,
        [ElementNEMaterialNumber],
        [MIXCreatime]
    FROM [DB_DATAMART_SQL].[MSE].[MSE1_MixResult_Info]
)
SELECT
    ElementNEMaterialNumber AS MatNo,
    MIXNO AS MixNo,
    AVG(SH) AS SaddleHeight,
    SUM(WtAvgEis1) AS WtAvgEis1,
    SUM(WtAvgEis2) AS WtAvgEis2,
    SUM(WtAvgEis3) AS WtAvgEis3,
    SUM(WtAvgEis4) AS WtAvgEis4,
    SUM(WtAvgEis5) AS WtAvgEis5,
    SUM(WtAvgEis6) AS WtAvgEis6,
    SUM(
        CASE WHEN ElementNEMaterialNumber IN ('0320800451','0320800453')
            THEN (WtAvgEis4 + ABS(WtAvgEis1) - ABS(WtAvgEis2))
            ELSE 0
        END
    ) AS WtAvgEis14,
    CASE
        WHEN YEAR(MIXCreatime) = YEAR(GETDATE()) THEN 'Current Year'
        ELSE CAST(YEAR(MIXCreatime) AS VARCHAR(4))
    END AS Createyear,
    FORMAT(MIXCreatime, 'MM') AS Createmonth
FROM mix_data
GROUP BY ElementNEMaterialNumber, MIXNO, MIXCreatime
HAVING ElementNEMaterialNumber = '0320800451'
AND LEFT(MIXNO,2) in ('C2','C3','C4','C5','C6','C7','C8','C9')
ORDER BY MixNo ASC
