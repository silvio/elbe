# ELBE - Debian Based Embedded Rootfilesystem Builder
# Copyright (C) 2013  Linutronix GmbH
#
# This file is part of ELBE.
#
# ELBE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ELBE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ELBE.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys

from elbepack.treeutils import etree
from elbepack import virtapt

from optparse import OptionParser
from datetime import datetime
from elbepack.validate import validate_xml
from elbepack.xmldefaults import ElbeDefaults
import apt_pkg

def run_command( argv ):

    oparser = OptionParser(usage="usage: %prog check_updates [options] <source-xmlfile>")
    oparser.add_option( "-s", "--script", dest="script",
                        help="filename of script to run when an update is required" )
    oparser.add_option( "--skip-validation", action="store_true",
                        dest="skip_validation", default=False,
                        help="Skip xml schema validation" )
    (opt,args) = oparser.parse_args(argv)

    if len(args) != 1:
        print "Wrong number of arguments"
        oparser.print_help()
        sys.exit(20)

    if not opt.skip_validation:
        if not validate_xml( args[0] ):
            print "xml validation failed. Bailing out"
            sys.exit(20)

    print "checking %s" % args[0]

    xml = etree( args[0] )

    if xml.has( "project/buildtype" ):
        buildtype = xml.text( "/project/buildtype" )
    else:
        buildtype = "nodefaults"

    defs = ElbeDefaults( buildtype )

    arch  = xml.text("project/buildimage/arch", default=defs, key="arch")
    suite = xml.text("project/suite")

    name  = xml.text("project/name")

    apt_sources = xml.text("sources_list").replace("10.0.2.2", "localhost")
    apt_prefs   = xml.text("apt_prefs")

    fullp = xml.node("fullpkgs")

    v = virtapt.VirtApt( name, arch, suite, apt_sources, apt_prefs )

    d = virtapt.apt_pkg.DepCache(v.cache)
    d.read_pinfile( v.projectpath + "/etc/apt/preferences" )

    for p in fullp:
        pname = p.et.text
        pver  = p.et.get('version')
        pauto = p.et.get('auto')

        if pauto != "true":
            d.mark_install( v.cache[pname] )

    errors = 0
    required_updates = 0

    for p in fullp:
        pname = p.et.text
        pver  = p.et.get('version')
        pauto = p.et.get('auto')

        if not pname in v.cache:
            if pauto == 'false':
                print pname, "does not exist in cache but is specified in pkg-list"
                errors += 1
            else:
                print pname, "is no more required"
                required_updates += 1

            continue

        centry = v.cache[pname]

        if d.marked_install( centry ):
            cver = d.get_candidate_ver( v.cache[pname] ).ver_str
            if pver != cver:
                print pname, "%s != %s" % (pver, cver)
                required_updates += 1

    if errors > 0:
        print errors, "Errors occured, xml files needs fixing"
        if opt.script:
            os.system( "%s ERRORS %s" % (opt.script, args[0]) )
    elif required_updates > 0:
        print required_updates, "updates required"
        if opt.script:
            os.system( "%s UPDATE %s" % (opt.script, args[0]) )
    else:
        print "No Updates available"









