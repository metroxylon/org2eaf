# This script converts .org corpus text into an .eaf xml file
#
# The child elements of the root ANNOTATION_DOCUMENT are:
# TIME_ORDER: contains every point in time which is referred to by any tier
# TIER: contain the linguistic data
# LINGUISTIC_TYPE: the way tiers relate to each other or to the time (using
#    constraints)
# LOCALE: country and language information
# CONSTRAINT: symbolic association (1 to 1), symbolic subdivision, included in,
#    time subdivision
# 
#<ANNOTATION_DOCUMENT>
#   <HEADER>
#   </HEADER>
#   <TIME_ORDER>
#     <TIME_SLOT/>
#     <TIME_SLOT/>
#   </TIME_ORDER>
#   <TIER>
#     <ANNOTATION>
#     </ANNOTATION>
#     <ANNOTATION>
#     </ANNOTATION>
#   </TIER>
#   <LINGUISTIC_TYPE/>
#   <LINGUISTIC_TYPE/>
#   <LOCALE/>
#   <LOCALE/>
#   <CONSTRAINT/>
#   <CONSTRAINT/>
#<ANNOTATION_DOCUMENT>

import lxml.etree as ET
import re
import time
import click

# helper module for splitting words into morphemes
# edit the list replacements for language specific rules 
from make_morphemes import *


# helper module get_data to read data from orgmode file into a dictionary structure
from get_data import *

# helper module time_conversion
# make_ms converts hh:mm:ss.ms to miliseconds
# make_mmss converts hh:mm:ss.ms to mm:ss (used for generation of labels)
from time_conversion import make_ms, make_mmss


annotation_nr = 0
ts_nr = 0

#-----------------------------------------------------------------------------
#Main part of the script: creation of tiers
#-----------------------------------------------------------------------------

def create_tier(speaker, tier_id, linguistic_type, parent=None):
    if parent != None:
        root.append(ET.Element("TIER",
                               DEFAULT_LOCALE="en",
                               LINGUISTIC_TYPE_REF=linguistic_type,
                               PARTICIPANT= speaker,
                               TIER_ID=tier_id,
                               PARENT_REF=parent))
    else:
        root.append(ET.Element("TIER",
                               DEFAULT_LOCALE="en",
                               LINGUISTIC_TYPE_REF=linguistic_type,
                               PARTICIPANT= speaker,
                               TIER_ID=tier_id))

def create_new_speaker_tiers(speaker):
    #1
    create_tier(speaker, "ref@" + speaker, "ref")
    #2
    create_tier(speaker, "disslabel@" + speaker, "1to1", "ref@" + speaker)
    #3
    create_tier(speaker, "tx@" + speaker, "1to1", "ref@" + speaker)
    #4
    create_tier(speaker, "word@" + speaker, "subdiv", "tx@" + speaker)
    #5
    create_tier(speaker, "morph@" + speaker, "subdiv", "word@" + speaker)
    #6
    create_tier(speaker, "gl@" + speaker, "1to1", "morph@" + speaker)
    #7
    create_tier(speaker, "morph_id@" + speaker, "1to1", "morph@" + speaker)
    #8
    create_tier(speaker, "ft@" + speaker, "1to1", "ref@" + speaker)
    #9
    create_tier(speaker, "com@" + speaker, "1to1", "ref@" + speaker)

    
def add_speaker_tier_no(new_speaker, all_speakers):
    # update list of speakers of text
    new_speaker_tier_nrs = {}
    num_of_speakers = len(all_speakers)
    tiers = ["ref", "disslabel", "tx", "word", "morph", "gl", "morph_id", "ft", "com"]
    tier_num = 0
    for tier in tiers:
        new_speaker_tier_nrs[tier] = 2 + num_of_speakers * len(tiers) + tier_num
        tier_num += 1
    all_speakers[new_speaker] = new_speaker_tier_nrs
    return all_speakers

#-----------------------------------------------------------------------------
# The trickiest part is to keep track of the annotation numbers and make the
# references correctly, i.e.
# - references to annotation on a parent tier
# - previous annotations on the same tier (for Sympolic_subdivision constraint)
# annotation numbers are the global variable "annotation_nr"
#-----------------------------------------------------------------------------


def make_align_annotation(annotation_nr, annot_value, ts_nr1, ts_nr2):
    annotation = ET.Element("ANNOTATION")
    annotation_id = "a" + str(annotation_nr)    
    annotation_type = ET.SubElement(annotation, "ALIGNABLE_ANNOTATION",
                                    ANNOTATION_ID=annotation_id,
                                    TIME_SLOT_REF1="ts" + str(ts_nr1),
                                    TIME_SLOT_REF2="ts" + str(ts_nr2))
    ET.SubElement(annotation_type, "ANNOTATION_VALUE").text = annot_value
    return annotation
    

def make_ref_annotation(annotation_nr, ref_annot, annot_value, previous_annot):
    annotation = ET.Element("ANNOTATION")
    annotation_id = "a" + str(annotation_nr)
    if previous_annot != False and previous_annot != None:
        annotation_type = ET.SubElement(annotation, "REF_ANNOTATION",
                                        ANNOTATION_ID=annotation_id,
                                        ANNOTATION_REF=ref_annot,
                                        PREVIOUS_ANNOTATION= "a" + str(previous_annot))
    else:
        annotation_type = ET.SubElement(annotation, "REF_ANNOTATION",
                                        ANNOTATION_ID=annotation_id,
                                        ANNOTATION_REF=ref_annot
                                        )
    ET.SubElement(annotation_type, "ANNOTATION_VALUE").text = annot_value
    return annotation


def make_morph_gls_id(word_morphs, word_gls, word_ids, word_nr, tiers, label):
    # this function makes the subdivisions of the word
    global annotation_nr
    word_morphs = make_morphemes(word_morphs)
    word_gls = re.sub("[-=]", " ", word_gls).split()
    word_gls = make_same_morpheme_separators(word_morphs, word_gls, label)
    word_ids = re.sub("[-=]", " ", word_ids).split()
    previous_morph_nr = None
    for morph, gls, key in zip(word_morphs, word_gls, word_ids):
        annotation_nr += 1
        morph_nr = annotation_nr
        root[tiers["morph"]].append(
            make_ref_annotation(annotation_nr, "a" + str(word_nr), morph,
                                previous_morph_nr))
        previous_morph_nr = annotation_nr
        annotation_nr += 1
        root[tiers["gl"]].append(
            make_ref_annotation(annotation_nr, "a" + str(morph_nr), gls,
                                False))
        annotation_nr += 1
        root[tiers["morph_id"]].append(
            make_ref_annotation(annotation_nr, "a" + str(morph_nr), key,
                                False))
        
    
    
    
def make_annotation(text_unit, all_speakers):
    # unit level annotation 
    global annotation_nr
    global ts_nr
    time1 = str(text_unit["meta"]["time1"])
    time2 = str(text_unit["meta"]["time2"])
    ts_nr += 2
    ts_nr1 = ts_nr - 1
    ts_nr2 = ts_nr    
    speaker = text_unit['meta']['speaker']
    text = text_unit['data']['tx']
    translation = text_unit['data']['ft']
    label = text_unit['meta']['label']
    disslabel = text_unit['meta']['disslabel']
    if 'comment' in text_unit['meta']:
        comment = text_unit['meta']['comment']
    else:
        comment = ''
    words = text_unit['data']['mb'].split()
    word_glosses = text_unit['data']['gl'].split()
    word_keys = text_unit['data']['keys'].split()
    tiers = all_speakers[speaker]
    annotation_nr += 1
    ref_nr = annotation_nr
    root[tiers["ref"]].append(make_align_annotation(annotation_nr,
                                                    label, ts_nr1, ts_nr2))
    annotation_nr += 1
    tx_nr = annotation_nr
    root[tiers["tx"]].append(
        make_ref_annotation(annotation_nr, "a" + str(ref_nr), text, False))
    annotation_nr += 1
    root[tiers["disslabel"]].append(
        make_ref_annotation(annotation_nr, "a" + str(ref_nr), disslabel, False))
    annotation_nr += 1
    root[tiers["ft"]].append(
        make_ref_annotation(annotation_nr, "a" + str(ref_nr), translation, False))
    annotation_nr += 1
    root[tiers["com"]].append(
        make_ref_annotation(annotation_nr, "a" + str(ref_nr), comment, False))
    previous_word_nr = None
    for word, word_gl, word_key in zip(words, word_glosses, word_keys):
        annotation_nr += 1
        word_nr = annotation_nr
        root[tiers["word"]].append(
            make_ref_annotation(annotation_nr, "a" + str(tx_nr),
                                word, previous_word_nr))
        previous_word_nr = annotation_nr
        make_morph_gls_id(word, word_gl, word_key, word_nr, tiers, label)
        

        
#-----------------------------------------------------------------------------
# XML around the tiers: root, HEADER (before TIERS), FOOTER (after tiers)
# Header has following structure:
# 
# <HEADER>
#   <MEDIA_DESCRIPTOR/>
#   <PROPERTY/>
# </HEADER>
#-----------------------------------------------------------------------------


def make_header(last_annot_id, audiofile, videofile=None):
    root.append(ET.Element("HEADER",
                       MEDIA_FILE="",
                       TIME_UNITS="milliseconds"))
    mediadir = "./"
    if videofile != None:
        root[0].append(ET.Element("MEDIA_DESCRIPTOR",
              MEDIA_URL= mediadir + videofile,
              MIME_TYPE="video/mp4",
              RELATIVE_MEDIA_URL="./" + videofile))
    root[0].append(ET.Element("MEDIA_DESCRIPTOR",
          MEDIA_URL= mediadir + audiofile,
          MIME_TYPE="audio/x-wav",
          RELATIVE_MEDIA_URL="./" + audiofile))
    prop2 = ET.Element("PROPERTY", NAME="lastUsedAnnotationId")
    prop2.text = str(last_annot_id)
    root[0].append(prop2)

def make_time_order(ordered_ids, story_units):
    root.append(ET.Element("TIME_ORDER"))
    ts_number = 1
    for label in ordered_ids:
        ts_id1 = "ts" + str(ts_number)
        ts_number += 1
        ts_id2 = "ts" + str(ts_number)
        ts_number += 1
        time1 = str(story_units[label]["meta"]["time1"])
        time2 = str(story_units[label]["meta"]["time2"])
        root[-1].append(ET.Element("TIME_SLOT", TIME_SLOT_ID=ts_id1, TIME_VALUE=time1))
        root[-1].append(ET.Element("TIME_SLOT", TIME_SLOT_ID=ts_id2, TIME_VALUE=time2))

#-----------------------------------------------------------------------------
# Footer
# <LINGUISTIC_TYPE/>
# <LOCALE/>
# <CONSTRAINT/>
#-----------------------------------------------------------------------------
def make_ling_type(lingtypeid, timealign, constraints=False, graphref="false"):
    if constraints != False:
        ling_type = ET.Element("LINGUISTIC_TYPE",
                               CONSTRAINTS=constraints,
                               GRAPHIC_REFERENCES=graphref,
                               LINGUISTIC_TYPE_ID=lingtypeid,
                               TIME_ALIGNABLE=timealign)
    else:
        ling_type = ET.Element("LINGUISTIC_TYPE",
                               GRAPHIC_REFERENCES=graphref,
                               LINGUISTIC_TYPE_ID=lingtypeid,
                               TIME_ALIGNABLE=timealign)
    root.append(ling_type)

def make_locale(country, lang):
    root.append(ET.Element("LOCALE", COUNTRY_CODE=country, LANGUAGE_CODE=lang))

def make_constraint(stereotype):
    stereotypes = {"Time_Subdivision" : "Time subdivision of parent annotation's time interval, no time gaps allowed within this interval",
                   "Symbolic_Subdivision" : "Symbolic subdivision of a parent annotation. Annotations refering to the same parent are ordered",
                   "Symbolic_Association" : "1-1 association with a parent annotation",
                   "Included_In" : "Time alignable annotations within the parent annotation's time interval, gaps are allowed"}
    if stereotype in stereotypes:
        root.append(ET.Element("CONSTRAINT", DESCRIPTION=stereotypes[stereotype],
                               STEREOTYPE=stereotype))
    else:
        print("Unknown stereotype")

#-----------------------------------------------------------------------------
# Execution of the script
#-----------------------------------------------------------------------------
# version = "3.0"
# author="Ismael Lieberherr"
# root = ET.Element("ANNOTATION_DOCUMENT",
#                   AUTHOR=author,
#                   DATE=time.asctime(time.localtime()),
#                   FORMAT=version, VERSION=version,
#                   attrib={"{" + xsi + "}noNamespaceSchemaLocation" : schemaLocation})



def make_eaf_from_org(orgfile, eaffile, author, version):
    global annotation_nr
    global ts_nr
    story_data = get_data(orgfile)
    file_metadata = get_file_metadata(orgfile)
    text_units = story_data[0]
    ordered_ids = story_data[1]
    all_speakers = {}
    # make header
    audiofile = file_metadata["audiofile"]
    videofile = file_metadata["videofile"]
    make_header(annotation_nr, audiofile, videofile)
    make_time_order(ordered_ids, text_units)
    # make tiers
    for lab in ordered_ids:
       text_unit = text_units[lab]
       speaker = text_unit['meta']['speaker']
       if speaker not in all_speakers:
           create_new_speaker_tiers(speaker)
           all_speakers = add_speaker_tier_no(speaker, all_speakers)
       make_annotation(text_unit, all_speakers)
    # make footer
    make_ling_type("default-lt", "true")
    make_ling_type("ref", "true")
    make_ling_type("1to1", "false", "Symbolic_Association")
    make_ling_type("subdiv", "false", "Symbolic_Subdivision")
    make_locale("UK", "en")
    make_constraint("Time_Subdivision")
    make_constraint("Symbolic_Association")
    make_constraint("Symbolic_Subdivision")
    make_constraint("Included_In")
    # add max annot nr
    root[0][-1].text = str(annotation_nr)
    # make tree
    tree = ET.ElementTree(root)
    tree.write(eaffile, pretty_print=True, encoding='utf-8', xml_declaration=True)
    speaker_nr = len(all_speakers)
    print("\n---***---")
    print(orgfile)
    if speaker_nr == 1:
        print("ELAN .eaf file created with " + str(speaker_nr) + " speaker.")
    else:
        print("ELAN .eaf file created with " + str(speaker_nr) + " speakers:")
    for speaker in all_speakers:
        print(speaker)
    print("---***---")
    annotation_nr = 0
    ts_nr = 0
    # empty the tree (otherwise it keeps appending to the full tree)
    for el in root:
        el.getparent().remove(el)
    

# The click interface
@click.group(invoke_without_command=True)
@click.argument('infile', type=click.Path(exists=True))
@click.argument('outfile', type=click.Path(exists=False), default='new-eaf.eaf')
@click.option('--author', default='metroxylon',
              help='Author of annotation file.')
@click.option('--schemaversion', default='3.0',
              help='Version of schema file.')

def cli(infile, outfile, author, schemaversion):
    """ Tool for converting orgmode annotation files into eaf-xml.

    Example: org2eaf frogstory.org frogstory.eaf

    """
    global root
    xsi="http://www.w3.org/2001/XMLSchema-instance"
    schemaLocation="http://www.mpi.nl/tools/elan/EAFv" + schemaversion + ".xsd"
    root = ET.Element("ANNOTATION_DOCUMENT",
                  AUTHOR=author,
                  DATE=time.asctime(time.localtime()),
                  FORMAT=schemaversion, VERSION=schemaversion,
                  attrib={"{" + xsi + "}noNamespaceSchemaLocation" : schemaLocation})
    make_eaf_from_org(infile, outfile, author, schemaversion)

