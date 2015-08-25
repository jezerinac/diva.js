#!/usr/bin/env python
# Converts a set of MEI files (generated by the Gamera Classifier) to a set of IIIF/OpenAnnotation annotation lists.

import os
import re
import sys
import json
import xml.etree.ElementTree as etree
from optparse import OptionParser


class ParseMEIAnnotations(object):
    def __tryint(self, s):
        try:
            return int(s)
        except:
            return s

    def __alphanum_key(self, s):
        """ Turn a string into a list of string and number chunks.
            "z23a" -> ["z", 23, "a"]
        """
        return [self.__tryint(c) for c in re.split('([0-9]+)', s)]

    def _parse_mei(self, filetree, file_name):
        tree = filetree
        zones = tree.findall('//{http://www.music-encoding.org/ns/mei}zone')
        neumes = tree.findall('//{http://www.music-encoding.org/ns/mei}neume')

        page_data = []

        for i, neume in enumerate(neumes):
            # in our data files, neumes and zones correspond 1-1 (in order), which speeds things up
            zone = zones[i]

            if neume.attrib['facs'] != zone.attrib['{http://www.w3.org/XML/1998/namespace}id']:
                print 'neume/zone mismatch: facs ' + neume.attrib['facs'] + ' != zone id ' + zone.attrib['id']
                for j, z in zones:
                    if z.attrib['{http://www.w3.org/XML/1998/namespace}id'] == neume.attrib['facs']:
                        zone = z

            anno_id = i + 1

            # get attributes
            name = neume.attrib['name']
            ulx = int(zone.attrib['ulx'])
            uly = int(zone.attrib['uly'])
            w = int(zone.attrib['lry']) - uly
            h = int(zone.attrib['lrx']) - ulx

            page_data.append({
                '@context': 'http://iiif.io/api/presentation/2/context.json',
                '@id': 'http://dev.simssa.ca/iiif/csg-' + file_name + '/' + str(anno_id),
                '@type': 'oa:Annotation',
                'motivation': 'oa:classifying',
                'resource': {
                    '@type': 'cnt:ContentAsText',
                    'chars': name,
                    'format': 'text/plain',
                    'language': 'en'
                },
                'on': 'http://www.e-codices.unifr.ch/metadata/iiif/csg-0390/canvas/csg-' + file_name + '.json#xywh='
                      + str(ulx) + ',' + str(uly) + ',' + str(w) + ',' + str(h)
            })

        return page_data

    def parse(self, input_directory, output_directory):
        mei_documents = []

        files = os.listdir(input_directory)
        files.sort(key=self.__alphanum_key)  # sort alphabetical, not asciibetical

        for i, f in enumerate(files):
            ignore, ext = os.path.splitext(f)
            if f.startswith("."):
                continue    # ignore hidden files

            if ext == '.mei':
                mei_document = {
                    'tree': etree.parse(os.path.join(input_directory, f)),
                    'filename': f[:-4]
                }
                mei_documents.append(mei_document)
            else:
                continue    # ignore anything else.

        # parse MEI
        for i, mei_document in enumerate(mei_documents):
            annotation_list = self._parse_mei(mei_document['tree'], mei_document['filename'])
            print 'processing ' + mei_document['filename']
            f = open(os.path.join(output_directory, "{0}.json".format(mei_document['filename'])), 'w')
            json.dump(annotation_list, f)
            f.close()

if __name__ == "__main__":
    usage = "%prog [options] input_directory output_directory"
    parser = OptionParser(usage)
    options, args = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        parser.error("You must specify a directory to process.")

    gen = ParseMEIAnnotations()
    sys.exit(gen.parse(args[0], args[1]))