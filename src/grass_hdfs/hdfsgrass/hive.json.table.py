#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       v.hdfs.hive.table
# AUTHOR(S):    Matej Krejci (matejkrejci@gmail.com
#
# PURPOSE:      Reproject the entire mapset
# COPYRIGHT:    (C) 2016 by the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

#%module
#% description: Creating spatial tables based on ESRI spatial framework
#% keyword: database
#% keyword: hdfs
#% keyword: hive
#%end

#%option
#% key: driver
#% type: string
#% required: yes
#% answer: hiveserver2
#% description: Type of database driver
#% options: hive_cli,hiveserver2
#% guisection: table
#%end
#%option
#% key: table
#% type: string
#% required: yes
#% description: name of table
#% guisection: table
#%end
#%option
#% key: attributes
#% type: string
#% description: python dictionary {attribute:datatype}
#% guisection: table
#%end
#%option
#% key: struct
#% type: string
#% description: structure of json, see https://github.com/krejcmat/bdutil-spatial#hive-serde-schema-generator
#% guisection: table
#%end
#%option
#% key: stored
#% type: string
#% required: no
#% description: output
#% guisection: table
#%end
#%flag
#% key: e
#% description: The EXTERNAL keyword lets you create a table and provide a LOCATION so that Hive does not use a default location for this table. This comes in handy if you already have data generated. When dropping an EXTERNAL table, data in the table is NOT deleted from the file system.
#% guisection: table
#%end
#%option
#% key: serde
#% type: string
#% required: yes
#% answer: org.openx.data.jsonserde.JsonSerDe
#% description: java class for serialization of json
#% guisection: table
#%end
#%option
#% key: outformat
#% type: string
#% description: java class for handling output format
#% guisection: table
#%end
#%option
#% key: jsonpath
#% type: string
#% description: hdfs path specifying input data
#% guisection: data
#%end
#%flag
#% key: o
#% description: Possible if filepath for loading data is delcared. True-overwrite all data in table.
#% guisection: data
#%end
#%flag
#% key: d
#% description: Firstly drop table if exists
#% guisection: table
#%end

from hdfs_grass_lib import ConnectionManager
import grass.script as grass


def main():
    if not options['attributes'] and not options['struct']:
        grass.fatal("Must be defined <attributes> or <struct> parameter")

    conn=ConnectionManager()
    conn.get_current_connection(options["driver"])
    hive = conn.get_hook()
    hive.create_geom_table( table=options['table'],
                            field_dict=options['attributes'],
                            struct=options['struct'],
                            stored=options['stored'],
                            serde=options['serde'],
                            outputformat=options['outformat'],
                            external=flags['e'],
                            recreate=flags['d'],
                            filepath=options['jsonpath'],
                            overwrite=flags['o'])

if __name__ == "__main__":
    options, flags = grass.parser()
    main()







