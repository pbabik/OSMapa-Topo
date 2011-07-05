#!/usr/bin/env python
# -*- coding: utf-8 -*-
# OpenStreetMap hike&bike route extraction tool
# based on script written by Radek Barton / www.opentrackmap.cz
# modified by pbabik to support black coloured routes, hex colour codes and bike routes

from getopt import *
from sys import exit, argv
from psycopg2 import *
from progressbar import *


def usage():
    print "copy_tracks.py [-n <db_name>]"

# Parse script arguments.
try:
    opts, args = getopt(argv[1:], "n:", ["db-name"])
except GetoptError, error:
    print str(error)
    usage()
    exit(2)

# Default script argumetns values.
db_name = "osm"

for opt, val in opts:
    if opt in ("-n", "--db-name"):
        db_name = val
    else:
        assert False, "unhandled option"

# Create connection to DB server.
connection = connect("dbname='%s' host='localhost' port='5432' user='postgres' password='geo' " % (db_name));
cursor = connection.cursor()
relation_cursor = connection.cursor()

# Clean previous tracks.
cursor.execute("BEGIN")
cursor.execute("DROP TABLE IF EXISTS planet_osm_track")

# Create temporary table that selects only relevant rows and columns and
# transforms Slovak and German style tagging to Czech style tagging.
cursor.execute("DELETE FROM geometry_columns WHERE f_table_name = \
  'tmp_planet_osm_track'")
cursor.execute("INSERT INTO geometry_columns (f_table_catalog, f_table_schema, \
  f_table_name, f_geometry_column, coord_dimension, srid, type) SELECT \
  f_table_catalog, f_table_schema, 'tmp_planet_osm_track', f_geometry_column, \
  coord_dimension, srid, type FROM geometry_columns WHERE f_table_name = \
  'planet_osm_line'")
cursor.execute("CREATE TEMPORARY TABLE tmp_planet_osm_track AS \
  (SELECT osm_id, way, route, name, ref, network, complete, abandoned, \
    kct_yellow, kct_red, kct_green, kct_blue, kct_black FROM \
    (SELECT osm_id, way, route, name, ref, network, complete, abandoned, \
      CASE \
        WHEN kct_yellow IS NOT NULL THEN kct_yellow \
        WHEN marked_trail_yellow IS NOT NULL THEN marked_trail_yellow \
        WHEN marked_trail = 'yellow' AND NOT route='bicycle' THEN 'yes' \
        WHEN marked_trail = 'yellow' AND route='bicycle' THEN 'bicycle' \
        WHEN \"osmc:symbol\" IS NOT NULL THEN \
          CASE \"osmc:symbol\" \
            WHEN 'yellow:white:yellow_bar' THEN 'yes' \
            WHEN 'yellow:white:yellow_circle' THEN 'yes' \
            WHEN 'yellow:white:yellow_corner' THEN 'yes' \
            WHEN 'yellow:white:yellow_backslash' THEN 'learning' \
            WHEN 'yellow:white:yellow_L' THEN 'ruin' \
            WHEN 'yellow:white:yellow_triangle' THEN 'peak' \
            WHEN 'yellow:white:yellow_bowl' THEN 'spring' \
            WHEN 'yellow:white:yellow_turned_T' THEN 'interesting_object' \
            WHEN 'yellow:white:yellow_dot' THEN 'horse' \
            WHEN 'white:orange:white_bar' THEN 'bicycle' \
            WHEN 'white:yellow:white_bar' THEN 'ski' \
          END \
        WHEN (colour = 'yellow' OR colour='#FFFF00' OR colour='#ffff00') AND NOT route='bicycle' THEN 'yes' \
	WHEN (colour = 'yellow' OR colour='#FFFF00' OR colour='#ffff00') AND route='bicycle' THEN 'bicycle' \
      END AS kct_yellow, \
      CASE \
        WHEN kct_red IS NOT NULL THEN kct_red \
        WHEN marked_trail_red IS NOT NULL THEN marked_trail_red \
        WHEN marked_trail = 'red' AND NOT route='bicycle' THEN 'yes' \
        WHEN \"osmc:symbol\" IS NOT NULL THEN \
          CASE \"osmc:symbol\" \
            WHEN 'red:white:red_bar' THEN 'yes' \
            WHEN 'red:white:red_circle' THEN 'yes' \
            WHEN 'red:white:red_corner' THEN 'yes' \
            WHEN 'red:white:red_backslash' THEN 'learning' \
            WHEN 'red:white:red_L' THEN 'ruin' \
            WHEN 'red:white:red_triangle' THEN 'peak' \
            WHEN 'red:white:red_bowl' THEN 'spring' \
            WHEN 'red:white:red_turned_T' THEN 'interesting_object' \
            WHEN 'red:white:red_dot' THEN 'horse' \
            WHEN 'red:orange:red_bar' THEN 'bicycle' \
            WHEN 'red:yellow:red_bar' THEN 'ski' \
          END \
        WHEN (colour = 'red' OR colour ='#FF0000' OR colour='#ff0000') AND NOT route='bicycle' THEN 'yes' \
        WHEN (colour = 'red' OR colour ='#FF0000' OR colour='#ff0000') AND route='bicycle' THEN 'bicycle' \
      END AS kct_red, \
      CASE \
        WHEN kct_green IS NOT NULL THEN kct_green \
        WHEN marked_trail_green IS NOT NULL THEN marked_trail_green \
        WHEN marked_trail = 'green' AND NOT route='bicycle' THEN 'yes' \
        WHEN marked_trail = 'green' AND route='bicycle' THEN 'bicycle' \
        WHEN \"osmc:symbol\" IS NOT NULL THEN \
          CASE \"osmc:symbol\" \
            WHEN 'green:white:green_bar' THEN 'yes' \
            WHEN 'green:white:green_circle' THEN 'yes' \
            WHEN 'green:white:green_corner' THEN 'yes' \
            WHEN 'green:white:green_backslash' THEN 'learning' \
            WHEN 'green:white:green_L' THEN 'ruin' \
            WHEN 'green:white:green_triangle' THEN 'peak' \
            WHEN 'green:white:green_bowl' THEN 'spring' \
            WHEN 'green:white:green_turned_T' THEN 'interesting_object' \
            WHEN 'green:white:green_dot' THEN 'horse' \
            WHEN 'green:orange:green_bar' THEN 'bicycle' \
            WHEN 'green:yellow:green_bar' THEN 'ski' \
          END \
        WHEN (colour = 'green' OR colour='#00FF00' OR colour='#00ff00') AND NOT route='bicycle' THEN 'yes' \
        WHEN (colour = 'green' OR colour='#00FF00' OR colour='#00FF00') AND route='bicycle' THEN 'bicycle' \
      END AS kct_green, \
      CASE \
        WHEN kct_blue IS NOT NULL THEN kct_blue \
        WHEN marked_trail_blue IS NOT NULL THEN marked_trail_blue \
        WHEN marked_trail = 'blue' AND NOT route='bicycle' THEN 'yes' \
        WHEN marked_trail = 'blue' AND route='bicycle' THEN 'bicycle' \
        WHEN \"osmc:symbol\" IS NOT NULL THEN \
          CASE \"osmc:symbol\" \
            WHEN 'blue:white:blue_bar' THEN 'yes' \
            WHEN 'blue:white:blue_circle' THEN 'yes' \
            WHEN 'blue:white:blue_corner' THEN 'yes' \
            WHEN 'blue:white:blue_backslash' THEN 'learning' \
            WHEN 'blue:white:blue_L' THEN 'ruin' \
            WHEN 'blue:white:blue_triangle' THEN 'peak' \
            WHEN 'blue:white:blue_bowl' THEN 'spring' \
            WHEN 'blue:white:blue_turned_T' THEN 'interesting_object' \
            WHEN 'blue:white:blue_dot' THEN 'horse' \
            WHEN 'blue:orange:blue_bar' THEN 'bicycle' \
            WHEN 'blue:yellow:blue_bar' THEN 'ski' \
        END \
        WHEN (colour = 'blue' OR colour='#0000FF' OR colour='#0000ff') AND NOT route='bicycle' THEN 'yes' \
        WHEN (colour = 'blue' OR colour='#0000FF' OR colour='#0000ff') AND route='bicycle' THEN 'bicycle' \
      END AS kct_blue, \
      CASE \
        WHEN kct_black IS NOT NULL THEN kct_black \
        WHEN marked_trail_black IS NOT NULL THEN marked_trail_black \
        WHEN marked_trail = 'black' AND NOT route='bicycle' THEN 'yes' \
        WHEN marked_trail = 'black' AND route='bicycle' THEN 'bicycle' \
        WHEN \"osmc:symbol\" IS NOT NULL THEN \
          CASE \"osmc:symbol\" \
            WHEN 'blue:white:black_bar' THEN 'yes' \
            WHEN 'blue:white:black_circle' THEN 'yes' \
            WHEN 'blue:white:black_corner' THEN 'yes' \
            WHEN 'blue:white:black_backslash' THEN 'learning' \
            WHEN 'blue:white:black_L' THEN 'ruin' \
            WHEN 'blue:white:black_triangle' THEN 'peak' \
            WHEN 'blue:white:black_bowl' THEN 'spring' \
            WHEN 'blue:white:black_turned_T' THEN 'interesting_object' \
            WHEN 'blue:white:black_dot' THEN 'horse' \
            WHEN 'blue:orange:black_bar' THEN 'bicycle' \
            WHEN 'blue:yellow:black_bar' THEN 'ski' \
        END \
        WHEN (colour = 'black' OR colour='#000000') AND NOT route = 'bicycle' THEN 'yes' \
        WHEN (colour = 'black' OR colour='#000000') AND route = 'bicycle' THEN 'bicycle' \
      END AS kct_black \
    FROM planet_osm_line \
    WHERE (COALESCE(kct_red, kct_green, kct_blue, kct_yellow, kct_black, marked_trail, \
      marked_trail_red, marked_trail_green, marked_trail_blue, \
      marked_trail_yellow, \"osmc:symbol\", colour) IS NOT NULL) OR \
      ((route='foot' OR route='hiking' OR route='horse' OR route='ski' OR route='bicycle') AND \
      (network IN ('e-road', 'iwn', 'rwn', 'icn','ncn', 'rcn', 'lcn')))) AS t \
  WHERE (COALESCE(t.kct_yellow, t.kct_red, t.kct_green, t.kct_blue) IS NOT \
    NULL) OR ((route='foot' OR route='hiking' OR route='horse' OR route='ski' OR route='bicycle') \
    AND (network IN ('e-road', 'iwn', 'rwn', 'icn','ncn', 'rcn', 'lcn'))))")

# Insert all regular lines from temporary table to the track table. That are
# all tracks that are not tagged using relations.
cursor.execute("DELETE FROM geometry_columns WHERE f_table_name = \
  'planet_osm_track'")
cursor.execute("INSERT INTO geometry_columns (f_table_catalog, f_table_schema, \
  f_table_name, f_geometry_column, coord_dimension, srid, type) SELECT \
  f_table_catalog, f_table_schema, 'planet_osm_track', f_geometry_column, \
  coord_dimension, srid, type FROM geometry_columns WHERE f_table_name = \
  'planet_osm_line'")
cursor.execute("CREATE TABLE planet_osm_track AS \
  SELECT osm_id, way, route, name, ref, network, complete, abandoned, \
    kct_yellow, kct_red, kct_green, kct_blue, kct_black \
  FROM tmp_planet_osm_track \
  WHERE osm_id > 0")

# Select parts IDs of all track relations.
relation_cursor.execute("SELECT t.osm_id, r.parts \
  FROM planet_osm_rels r, tmp_planet_osm_track t \
  WHERE (r.id = -t.osm_id) AND (t.osm_id < 0)")



progress_bar = ProgressBar(relation_cursor.rowcount).start()
count = 0

while True:
    # Fetch something of the result.
    rows = relation_cursor.fetchmany(100)

    # Empty result means end of the query.
    if not len(rows):
        break;

    # Copy ways of all track relation from line table to the track table.
    way_ids = []
    for row in rows:
       way_ids.extend(row[1])
    where_statement = ", ".join([str(way_id) for way_id in way_ids])
    cursor.execute("INSERT INTO planet_osm_track \
      SELECT osm_id, way, route, name, ref, network, complete, abandoned, \
        kct_yellow, kct_red, kct_green, kct_blue, kct_black \
      FROM planet_osm_line l \
      WHERE l.osm_id IN (%s) AND NOT EXISTS \
        (SELECT osm_id \
        FROM planet_osm_track t \
        WHERE t.osm_id = l.osm_id)" % (where_statement))

    # Overwrite tracks with important tags from track relations.
    # TODO Make this query batched.
    for row in rows:
        cursor.execute("UPDATE planet_osm_track t \
          SET route = \
            (CASE \
              WHEN tt.network IN ('e-road', 'iwn', 'rwn') \
              THEN tt.route \
              ELSE t.route \
            END), \
            name = (CASE \
              WHEN tt.network IN ('e-road', 'iwn', 'rwn') \
              THEN tt.name \
              ELSE t.name \
            END), \
            ref = (CASE \
              WHEN tt.network IN ('e-road', 'iwn', 'rwn') \
              THEN tt.ref \
              ELSE t.ref \
            END), \
            network = (CASE \
              WHEN tt.network IN ('e-road', 'iwn', 'rwn') \
              THEN tt.network \
              ELSE t.network \
            END), \
            complete = (CASE \
              WHEN tt.complete = 'no' \
              THEN tt.complete \
              ELSE t.complete \
            END), \
            abandoned = (CASE \
              WHEN tt.abandoned = 'yes' \
              THEN tt.abandoned \
              ELSE t.abandoned \
            END), \
            kct_yellow = (CASE \
              WHEN (tt.kct_yellow IS NOT NULL)\
              THEN tt.kct_yellow \
              ELSE t.kct_yellow \
            END), \
            kct_red = (CASE \
              WHEN (tt.kct_red IS NOT NULL)\
              THEN tt.kct_red \
              ELSE t.kct_red \
            END), \
            kct_green = (CASE \
              WHEN (tt.kct_green IS NOT NULL)\
              THEN tt.kct_green \
              ELSE t.kct_green \
            END), \
            kct_blue = (CASE \
              WHEN (tt.kct_blue IS NOT NULL)\
              THEN tt.kct_blue \
              ELSE t.kct_blue \
            END), \
     kct_black = (CASE \
              WHEN (tt.kct_black IS NOT NULL)\
              THEN tt.kct_black \
              ELSE t.kct_black \
            END) \
          FROM tmp_planet_osm_track tt WHERE tt.osm_id = %s AND t.osm_id \
            IN (%s)" % (row[0], ",".join([str(way_id) for way_id in row[1]])))

    count = count + len(rows)
    progress_bar.update(count)

cursor.execute("COMMIT") 
cursor.execute("UPDATE planet_osm_track SET kct_red = 'yes' WHERE kct_red = 'major' OR kct_red = 'local'; ")
cursor.execute("UPDATE planet_osm_track SET kct_blue = 'yes' WHERE kct_blue = 'major' OR kct_blue = 'local'; ")
cursor.execute("UPDATE planet_osm_track SET kct_green = 'yes' WHERE kct_green = 'major' OR kct_green = 'local'; ")
cursor.execute("UPDATE planet_osm_track SET kct_yellow = 'yes' WHERE kct_yellow = 'major' OR kct_yellow = 'local'; ")
cursor.execute("UPDATE planet_osm_track SET kct_black = 'yes' WHERE kct_black = 'major' OR kct_black = 'local'; ")
progress_bar.finish()
cursor.close()
relation_cursor.close()
connection.commit()
