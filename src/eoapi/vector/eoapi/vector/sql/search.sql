CREATE OR REPLACE FUNCTION search_items(
    IN geom geometry,
    IN queryhash text,
    IN epsg int,
    IN items_limit int DEFAULT 10000,
    IN tile_resolution int DEFAULT 4096,
    IN tile_buffer int DEFAULT 256,
    IN _scanlimit int DEFAULT 10000,
    IN _timelimit interval DEFAULT '5 seconds'::interval,
    OUT mvtgeom geometry,
    OUT id text
) RETURNS setof RECORD AS $$
DECLARE
    search searches%ROWTYPE;
    curs refcursor;
    _where text;
    query text;
    iter_record items%ROWTYPE;
    exit_flag boolean := FALSE;
    counter int := 1;
    scancounter int := 1;
    remaining_limit int := _scanlimit;
BEGIN
    SELECT * INTO search FROM searches WHERE hash=queryhash;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Search with Query Hash % Not Found', queryhash;
    END IF;

    _where := format('%s AND ST_Intersects(geometry, %L::geometry)', search._where, ST_Transform(geom, 4326));

    FOR query IN SELECT * FROM partition_queries(_where, search.orderby) LOOP
        query := format('%s LIMIT %L', query, remaining_limit);
        curs = create_cursor(query);
        LOOP
            FETCH curs INTO iter_record;
            EXIT WHEN NOT FOUND;

            mvtgeom := ST_ASMVTGeom(
                ST_Transform(iter_record.geometry, epsg),
                geom,
                tile_resolution,
                tile_buffer
            );

            id := iter_record.id;

            RETURN NEXT;

            IF counter >= items_limit
                OR scancounter > _scanlimit
                OR ftime() > _timelimit
            THEN
                exit_flag := TRUE;
                EXIT;
            END IF;
            counter := counter + 1;
            scancounter := scancounter + 1;

        END LOOP;
        EXIT WHEN exit_flag;
        remaining_limit := _scanlimit - scancounter;
    END LOOP;
    RETURN;
END;
$$ LANGUAGE PLPGSQL;

CREATE OR REPLACE FUNCTION search_mvt(
    -- mandatory parameters
    xmin float,
    ymin float,
    xmax float,
    ymax float,
    epsg integer,
    -- additional parameters
    query_params json
)
RETURNS bytea AS $$
DECLARE
    result bytea;
    geom geometry;
    queryhash text;
    items_limit int;
    tile_resolution int;
    tile_buffer int;
BEGIN
    geom := ST_Segmentize(
        ST_MakeEnvelope(xmin, ymin, xmax, ymax, epsg), xmax - xmin
    );
    queryhash := query_params ->> 'searchid';
    items_limit := coalesce((query_params ->> 'limit')::int, 10000);
    tile_resolution := coalesce((query_params ->> 'resolution')::int, 4096);
    tile_buffer := coalesce((query_params ->> 'buffer')::int, 256);

    WITH mvtgeom AS (
        SELECT * FROM search_items(
            geom,
            queryhash,
            epsg,
            items_limit,
            tile_resolution,
            tile_buffer
        )
    )
    SELECT ST_AsMVT(mvtgeom.*, 'default')

    -- Put the query result into the result variale.
    INTO result FROM mvtgeom;

    -- Return the answer
    RETURN result;
END;
$$
LANGUAGE 'plpgsql'
STRICT -- Null input gets null output
PARALLEL SAFE;
