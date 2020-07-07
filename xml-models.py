import pandas as pd
import sqlalchemy
from xml.sax.saxutils import escape
import sys

header = '''<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
'''

footer = '''
</rss>'''

def xmlescape(data):
    return escape(str(data), entities = { "'": "&apos;", '"': "&quot;" })

def convert_xml(row):
    xml = ['  <item>']
    for field in row.index:
        xml.append('    <{0}>{1}</{0}>'.format(field, xmlescape(row[field])))
    xml.append('  </item>')
    return '\n'.join(xml)

def generate_xml(dataframe):
    return '\n'.join(dataframe.apply(convert_xml, axis = 1))

def get_xml_models(db_file):
    engine = sqlalchemy.create_engine('sqlite:///' + db_file)

    showcase_query = '''
                    SELECT s.showcase_id AS showcase_id
                        ,s.category AS section
                        ,s.poster_large AS poster
                        ,s.poster_small AS poster_small
                        ,s.poster_medium AS poster_medium
                        ,s.poster_large AS poster_large
                        ,si.title AS title
                    FROM showcase s
                    JOIN showcase_info si ON s.showcase_id = si.showcase_id
                    WHERE si.language_id = 25
                        AND s.showcase_type = 'home'
                        AND s.category NOT IN ('ad', 'application')
                    GROUP BY s.showcase_id
                    ORDER BY s.display_order_row, s.display_order_cell
    '''

    listen_query = '''
                    SELECT a.poster_small AS poster_small
                        ,a.poster_medium AS poster_medium
                        ,a.poster_large AS poster_large
                        ,ai.title AS title
                        ,ai.artist_name AS subheader
                    FROM aod a
                    JOIN aod_info ai ON a.aod_id = ai.aod_id
                    JOIN aod_has_genre hg ON a.aod_id = hg.aod_id
                    JOIN genre g ON hg.genre_id = g.genre_id
                        AND ai.language_id = g.language_id
                    WHERE ai.language_id = 25
                        AND g.genre_type = 'listen'
                    GROUP BY g.genre_id, a.aod_id
                    ORDER BY g.display_order, a.display_order
    '''

    watch_query = '''
                    SELECT c.poster_small AS poster_small
                        ,c.poster_medium AS poster_medium
                        ,c.poster_large AS poster_large
                        ,c.title AS title
                        ,c.content_id AS content_id
                        ,c.series_id AS series_id
                        ,c.content_type AS content_type
                    FROM (
                        SELECT 'movie' AS content_type
                            ,vi.language_id AS language_id
                            ,v.display_order AS display_order
                            ,v.poster_small AS poster_small
                            ,v.poster_medium AS poster_medium
                            ,v.poster_large AS poster_large
                            ,vi.title AS title
                            ,CAST(v.vod_id AS TEXT) AS content_id
                            ,CAST(0 AS TEXT) AS series_id
                            ,g.genre_id AS genre_id
                            ,g.genre_type AS genre_type
                            ,g.display_order AS genre_display_order
                        FROM vod_has_genre vhg
                        JOIN vod v ON vhg.vod_id = v.vod_id
                        JOIN vod_info vi ON v.vod_id = vi.vod_id
                        JOIN genre g ON vhg.genre_id = g.genre_id
                            AND vi.language_id = g.language_id
                        LEFT JOIN vod_track vt ON v.vod_id = vt.vod_id AND vt.is_preview = 1
                    UNION
                        SELECT 'tv' AS content_type
                            ,tvi.language_id AS language_id
                            ,COALESCE(tvs.display_order, tv.episode_number) AS display_order
                            ,COALESCE(tvs.poster_small, tv.poster_small) AS poster_small
                            ,COALESCE(tvs.poster_medium, tv.poster_medium) AS poster_medium
                            ,COALESCE(tvs.poster_large, tv.poster_large) AS poster_large
                            ,COALESCE(tvsi.title, tvi.title) AS title
                            ,CASE tv.series_id
                                WHEN 0 THEN CAST(tv.episode_id AS TEXT)
                                ELSE CAST(0 AS TEXT)
                             END AS content_id
                            ,CAST(tv.series_id AS TEXT) AS series_id
                            ,g.genre_id AS genre_id
                            ,g.genre_type AS genre_type
                            ,g.display_order AS genre_display_order
                        FROM tv_has_genre tvhg
                        JOIN tv_episode tv ON tvhg.episode_id = tv.episode_id
                        JOIN tv_episode_info tvi ON tv.episode_id = tvi.episode_id
                        JOIN genre g ON tvhg.genre_id = g.genre_id
                            AND tvi.language_id = g.language_id
                        LEFT JOIN tv_series tvs ON tv.series_id = tvs.series_id
                        LEFT JOIN tv_series_info tvsi ON tvs.series_id = tvsi.series_id
                            AND tvi.language_id = tvsi.language_id
                    ) AS c
                    WHERE c.language_id = 25
                        AND c.genre_type = 'watch'
                    GROUP BY c.genre_id, CASE c.series_id
                        WHEN 0 THEN c.content_id
                        ELSE c.series_id
                    END
                    ORDER BY c.genre_display_order, c.display_order
    '''

    watch_model = pd.read_sql_query(watch_query, con = engine)
    for i in range(len(watch_model)):
        if watch_model.loc[i]['content_type'] == 'movie':
            first_content_id = watch_model.loc[i]['content_id']
            break

    watch_synopsis_query = '''
                SELECT c.genre_id AS genre_id
                    ,c.genre_type AS category
                    ,c.content_type AS content_type
                    ,c.genre_name AS genre_name
                    ,c.poster_small AS poster_small
                    ,c.poster_medium AS poster_medium
                    ,c.title AS title
                    ,c.description AS description
                    ,c.content_id AS content_id
                    ,c.series_id AS series_id
                FROM (
                    SELECT 'movie' AS content_type
                        ,vi.language_id AS language_id
                        ,v.display_order AS display_order
                        ,v.poster_small AS poster_small
                        ,v.poster_medium AS poster_medium
                        ,vi.title AS title
                        ,vi.description AS description
                        ,CAST(v.vod_id AS TEXT) AS content_id
                        ,CAST(0 AS TEXT) AS series_id
                        ,0 AS season_id
                        ,g.genre_id AS genre_id
                        ,g.genre_type AS genre_type
                        ,g.genre_name AS genre_name
                        ,g.display_order AS genre_display_order
                    FROM vod_has_genre vhg
                    JOIN vod v ON vhg.vod_id = v.vod_id
                    JOIN vod_info vi ON v.vod_id = vi.vod_id
                    JOIN genre g ON vhg.genre_id = g.genre_id
                        AND vi.language_id = g.language_id
                    LEFT JOIN vod_track vt ON v.vod_id = vt.vod_id AND vt.is_preview = 1
                UNION
                    SELECT 'tv' AS content_type
                        ,tvi.language_id AS language_id
                        ,COALESCE(tvs.display_order, tv.episode_number) AS display_order
                        ,COALESCE(tvs.poster_small, tv.poster_small) AS poster_small
                        ,COALESCE(tvs.poster_medium, tv.poster_medium) AS poster_medium
                        ,COALESCE(tvsi.title, tvi.title) AS title
                        ,COALESCE(tvsi.description, tvi.description) AS description
                        ,CASE tv.series_id
                            WHEN 0 THEN CAST(tv.episode_id AS TEXT)
                            ELSE CAST(0 AS TEXT)
                         END AS content_id
                        ,CAST(tv.series_id AS TEXT) AS series_id
                        ,0 AS season_id
                        ,g.genre_id AS genre_id
                        ,g.genre_type AS genre_type
                        ,g.genre_name AS genre_name
                        ,g.display_order AS genre_display_order
                    FROM tv_has_genre tvhg
                    JOIN tv_episode tv ON tvhg.episode_id = tv.episode_id
                    JOIN tv_episode_info tvi ON tv.episode_id = tvi.episode_id
                    JOIN genre g ON tvhg.genre_id = g.genre_id
                        AND tvi.language_id = g.language_id
                    LEFT JOIN tv_series tvs ON tv.series_id = tvs.series_id
                    LEFT JOIN tv_series_info tvsi ON tvs.series_id = tvsi.series_id
                        AND tvi.language_id = tvsi.language_id
                ) AS c
                WHERE c.language_id = 25
                    AND c.genre_type = 'watch'
                    AND c.content_id = {}
                GROUP BY CASE c.series_id
                    WHEN 0 THEN c.content_id
                    ELSE c.series_id
                END
    '''.format(first_content_id)

    watch_related_query = '''
                SELECT r.category AS section
                ,r.content_type AS content_type
                ,c.poster_small AS poster_small
                ,c.poster_small AS poster_medium
                ,c.title AS title
                ,r.relation_content_id AS content_id
                ,r.relation_series_id AS series_id
                ,NULL AS season_id
                FROM object_relationship r
                JOIN (
                    SELECT v.vod_id AS content_id
                        ,v.cms_id AS cms_id
                        ,0 AS series_id
                        ,v.poster_small AS poster_small
                        ,vi.title AS title
                        ,vi.language_id AS language_id
                    FROM vod v JOIN vod_info vi ON v.vod_id = vi.vod_id
                    UNION
                    SELECT a.aod_id AS content_id
                        ,a.cms_id AS cms_id
                        ,0 AS series_id
                        ,a.poster_small AS poster_small
                        ,ai.title AS title
                        ,ai.language_id AS language_id
                    FROM aod a JOIN aod_info ai ON a.aod_id = ai.aod_id
                    UNION
                    SELECT g.game_id AS content_id
                        ,g.cms_id AS cms_id
                        ,0 AS series_id
                        ,g.poster_small AS poster_small
                        ,gi.title AS title
                        ,gi.language_id AS language_id
                    FROM game g JOIN game_info gi ON g.game_id = gi.game_id
                    UNION
                    SELECT CASE tv.series_id WHEN 0 THEN tv.episode_id ELSE 0 END AS content_id
                        ,tv.cms_id AS cms_id
                        ,tv.series_id AS series_id
                        ,COALESCE(tvs.poster_small, tv.poster_small) AS poster_small
                        ,COALESCE(tvsi.title, tvi.title) AS title
                        ,tvi.language_id AS language_id
                    FROM tv_episode tv JOIN tv_episode_info tvi ON tv.episode_id = tvi.episode_id
                    LEFT JOIN tv_series tvs ON tv.series_id = tvs.series_id
                    LEFT JOIN tv_series_info tvsi ON tvs.series_id = tvsi.series_id
                        AND tvi.language_id = tvsi.language_id
                    UNION
                    SELECT ad.ad_id AS content_id
                        ,ad.cms_id AS cms_id
                        ,0 AS series_id
                        ,ad.poster_small_square AS poster_small
                        ,'' AS title
                        ,l.language_id AS language_id
                    FROM ad, gui_language l
                ) c ON r.relation_content_id = c.content_id
                    AND r.relation_series_id = c.series_id
                WHERE c.language_id = 25
                GROUP BY CASE r.relation_series_id
                    WHEN 0 THEN r.relation_content_id
                    ELSE r.relation_series_id
                END
                LIMIT 4
    '''

    queries = {'showcase': showcase_query,
               'listen': listen_query,
               'watch': watch_query,
               'watch-synopsis-query': watch_synopsis_query,
               'watch-related-query': watch_related_query
              }

    for k,v in queries.items():
        with open(k + '.xml', 'w', encoding="utf-8") as f:
            f.write(header)
            df = pd.read_sql_query(v, con = engine)
            f.write( generate_xml(df) )
            f.write(footer)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: generate-xml-models.py sqlite-file')
    else:
        get_xml_models(sys.argv[-1])



