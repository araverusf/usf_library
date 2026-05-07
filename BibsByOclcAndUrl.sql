SELECT DISTINCT
-- Builds the bib number by concatenating 'b' + the record number + 'a' (Sierra's standard bib ID format)
    'b' || b.record_num || 'a' AS bibnumber, 
-- Grabs the OCLC number from the 035 MARC field
    v_035.field_content AS oclcnumber,
-- Grabs the URL from the 856 MARC field
    v_856.field_content AS url,
-- Grabs the bib location code
    bibloc.location_code AS locationcode
FROM sierra_view.bib_view b
INNER JOIN sierra_view.varfield v_035 ON b.id = v_035.record_id
INNER JOIN sierra_view.varfield v_856 ON b.id = v_856.record_id
INNER JOIN sierra_view.bib_record_location bibloc ON b.id = bibloc.bib_record_id
-- Only returns records assigned to the 'gint' location code
WHERE bibloc.location_code = 'gint'
    AND v_035.marc_tag = '035'
    AND v_856.marc_tag = '856'
    AND (
        (
-- RECORD 1: Match records whose 035 field contains any of these OCLC numbers (% is a wildcard)...
            (v_035.field_content LIKE '%952493480%' OR v_035.field_content LIKE '%793538109%' OR v_035.field_content LIKE '%808385848%' OR v_035.field_content LIKE '%994601527%' OR v_035.field_content LIKE '%1058234573%' OR v_035.field_content LIKE '%1410149190%')
-- ...AND whose 856 field contains any of these URLs (ESCAPE '\' allows literal backslashes in the pattern if needed)
            AND (v_856.field_content LIKE '%https://library.oapen.org/handle/20.500.12657/37268%' ESCAPE '\' OR v_856.field_content LIKE '%https://openresearchlibrary.org/viewer/6fcad061-e254-4b2b-b30c-289870c3e8de%' ESCAPE '\' OR v_856.field_content LIKE '%https://directory.doabooks.org/handle/20.500.12854/33678%' ESCAPE '\')
        )
        OR
        (
-- RECORD 2: Match records whose 035 field contains any of these OCLC numbers...
            (v_035.field_content LIKE '%1525618859%' OR v_035.field_content LIKE '%1526863387%' OR v_035.field_content LIKE '%1528968178%' OR v_035.field_content LIKE '%1535975997%')
-- ...AND whose 856 field contains any of these URLs
            AND (v_856.field_content LIKE '%https://www.jstor.org/stable/10.2307/jj.31464686%' ESCAPE '\' OR v_856.field_content LIKE '%https://muse.jhu.edu/book/138301%' ESCAPE '\')
        )
 
    );