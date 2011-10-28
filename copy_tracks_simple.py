#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# OpenStreetMap hike&bike / OSMapa-topo route extraction tool
# based on script written by Radek Barton / www.opentrackmap.cz and pbabik
# refactored/optimised by andrew.zaborowski@intel.com

from getopt import *
from sys import exit, argv
from psycopg2 import *

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
connection = connect("dbname='%s' user='osm' " % (db_name));
cursor = connection.cursor()

# Clean previous tracks.
cursor.execute("BEGIN")
cursor.execute("DROP TABLE IF EXISTS planet_osm_track CASCADE")

colours = [ "yellow", "red", "green", "blue", "black" ]

# Create temporary table that selects only relevant rows and columns and
# transforms Slovak and German style tagging to Czech style tagging.
# TODO: Could use HAVING instead of the outter SELECT with WHERE?
print("SELECTing all coloured route IDs")
cursor.execute("CREATE TEMPORARY TABLE tmp_planet_osm_track AS \
  (SELECT osm_id, route, name, ref, network, complete, abandoned, \
    kct_yellow, kct_red, kct_green, kct_blue, kct_black FROM \
    (SELECT -osm_id AS osm_id, route, name, ref, network, complete, abandoned, \
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
        WHEN (colour = 'green' OR colour='#00FF00' OR colour='#00ff00') AND route='bicycle' THEN 'bicycle' \
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
            WHEN 'black:white:black_bar' THEN 'yes' \
            WHEN 'black:white:black_circle' THEN 'yes' \
            WHEN 'black:white:black_corner' THEN 'yes' \
            WHEN 'black:white:black_backslash' THEN 'learning' \
            WHEN 'black:white:black_L' THEN 'ruin' \
            WHEN 'black:white:black_triangle' THEN 'peak' \
            WHEN 'black:white:black_bowl' THEN 'spring' \
            WHEN 'black:white:black_turned_T' THEN 'interesting_object' \
            WHEN 'black:white:black_dot' THEN 'horse' \
            WHEN 'black:orange:black_bar' THEN 'bicycle' \
            WHEN 'black:yellow:black_bar' THEN 'ski' \
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
  WHERE (COALESCE(t.kct_yellow, t.kct_red, t.kct_green, t.kct_blue, t.kct_black) IS NOT \
    NULL) OR ((route='foot' OR route='hiking' OR route='horse' OR route='ski' OR route='bicycle') \
    AND (network IN ('e-road', 'iwn', 'rwn', 'icn','ncn', 'rcn', 'lcn'))))")
#cursor.execute("CREATE INDEX tmp_idx ON tmp_planet_osm_track(osm_id);")

print("Now finding relation parts")
cursor.execute("CREATE TEMPORARY TABLE tmp2_planet_osm_track AS " +
  "SELECT osm_id, route, name, complete, abandoned, " +
    "kct_yellow, kct_red, kct_green, kct_blue, kct_black, parts " +
  "FROM tmp_planet_osm_track, planet_osm_rels WHERE osm_id = id")
#cursor.execute("CREATE INDEX tmp2_idx ON tmp2_planet_osm_track USING gin (parts);")

print("Grouping colours by ways")
cursor.execute("CREATE TEMPORARY TABLE tmp3_planet_osm_track AS " +
  "SELECT osm_id, " +
  # Note: this magically correctly skips over NULLs:
  "array_to_string(array_agg(relln.name), ' - ') as name, " +
  # CASE WHEN count(relln.complete = 'no') > 0 THEN 'no' END AS complete,
  # CASE WHEN count(relln.abandoned = 'yes') > 0 THEN 'yes' END AS abandoned,
  ', '.join([
    # TODO: OR ln.kct_ + c + = 'bicycle' except ln has not been converted
    # to "Czech" tagging as relln has
    "CASE WHEN bool_or(bic_" + c + ") THEN 'bicycle' " +
         "WHEN bool_or(" + c + ") THEN 'yes' " +
    "END AS kct_" + c for c in colours ]) +
" FROM (SELECT unnest(parts) as osm_id, name, " +
    ', '.join([
      "kct_" + c + " IS NOT NULL AS " + c + ", kct_" + c +
      " = 'bicycle' AS bic_" + c for c in colours ]) +
  " FROM tmp2_planet_osm_track) AS relln" +
" GROUP BY osm_id")
print("Analyzing the ways table")
cursor.execute("ANALYZE tmp3_planet_osm_track")

cursor.execute("DELETE FROM geometry_columns WHERE f_table_name = \
  'planet_osm_track'")
cursor.execute("INSERT INTO geometry_columns (f_table_catalog, f_table_schema, \
  f_table_name, f_geometry_column, coord_dimension, srid, type) SELECT \
  f_table_catalog, f_table_schema, 'planet_osm_track', f_geometry_column, \
  coord_dimension, srid, type FROM geometry_columns WHERE f_table_name = \
  'planet_osm_line'")

print("Adding geometries to ways")
# TODO: add the potential routes tagged as ways here? RIGHT OUTER JOIN(?)
cursor.execute("CREATE TABLE planet_osm_track AS " +
  "SELECT way, tmp3_planet_osm_track.* " +
  "FROM tmp3_planet_osm_track JOIN planet_osm_line USING (osm_id)")

print("Indexing the geometries")
cursor.execute("CREATE INDEX planet_osm_track_idx ON planet_osm_track " +
  "USING GIST (way)")
cursor.execute("ANALYZE planet_osm_track")

cursor.execute("COMMIT")
cursor.close()
connection.commit()
