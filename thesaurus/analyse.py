'''
Created on 27 mrt. 2018

@author: Gebruiker
'''

import xml.etree.ElementTree as ET
#import pandas as pd
import os
# from lxml import objectify
# from pylab import *
from datetime import datetime
import random
from sets import Set
#import matplotlib.pyplot as plt
#from matplotlib.pyplot import show


def list_concepts(dom):
    # Create a list with the id's of the SKOS concepts
    concept_identifiers = []
    root = dom.childNodes.item(0)

    for node in root.childNodes:
        if (node.nodeType == node.ELEMENT_NODE
        and node.nodeName == 'skos:Concept'):
            concept_id = node.attributes.items()[0][1]
            concept_identifiers.append(concept_id)
    return concept_identifiers


def referenced_concept_schemes(dom):
    # List all concept schemes referenced in the thesaurus
    concept_schemes = []
    root = dom.childNodes.item(0)

    for node in root.childNodes:
        for property in node.childNodes:
            if (property.nodeType == property.ELEMENT_NODE
            and property.nodeName == 'skos:inScheme'):
                concept_scheme = property.attributes.items()[0][1]
                if concept_scheme not in concept_schemes:
                    concept_schemes.append(concept_scheme)
    return concept_schemes


def list_schemeless_concepts(dom):
    # List all concepts without that do not reference a concept scheme
    schemeless_concepts = []
    root = dom.childNodes.item(0)

    for node in root.childNodes:
        if (node.nodeType == node.ELEMENT_NODE
        and node.nodeName == 'skos:Concept'):
            concept_id = node.attributes.items()[0][1]
            in_scheme = False

            for property in node.childNodes:
                if property.nodeName == 'skos:inScheme':
                    in_scheme = True
            if not in_scheme:
                schemeless_concepts.append(concept_id)
    return schemeless_concepts


def create_inverse_hierarchy(dom):
    # The inverse of every hierarchical skos relation is added to a dictionary:
    # {'http://concept.net/2': {'skos:broader': ['http://concept.net/1']}}
    hierarchy_dict = {}
    hierarchy_labels = ['skos:broader', 'skos:narrower', 'skos:related']
    root = dom.childNodes.item(0)

    for node in root.childNodes:
        for property in node.childNodes:
            if (property.nodeType == property.ELEMENT_NODE
            and (property.nodeName in hierarchy_labels)):
                concept_id = node.attributes.items()[0][1]
                prop_name = property.nodeName
                prop_inv = inverse_property(prop_name)
                object_id = property.attributes.items()[0][1]

                if object_id not in hierarchy_dict:
                    hierarchy_dict[object_id] = {}
                    hierarchy_dict[object_id][prop_inv] = [concept_id]
                elif prop_inv not in hierarchy_dict[object_id]:
                    hierarchy_dict[object_id][prop_inv] = [concept_id]
                else:
                    hierarchy_dict[object_id][prop_inv].append(concept_id)
    return hierarchy_dict


def inverse_property(property_name):
    if property_name == 'skos:broader':
        return 'skos:narrower'
    elif property_name == 'skos:narrower':
        return 'skos:broader'
    else:
        return 'skos:related'


def missing_outward_references(dom):
    inverse_hierarchy = create_inverse_hierarchy(dom)
    missing_references = []

    # Iterate through all concepts in inverse_hierarchy to check whether
    # all deduced references are present for the concept in question
    for concept_id in inverse_hierarchy:
        concept = get_concept(dom, concept_id)
        if concept is not None:
            properties = hierarchical_properties_dict(concept)
            i_properties = inverse_hierarchy[concept_id]
            missing = outward_difference(concept_id, properties, i_properties)
            if missing != []:
                missing_references.append(missing)
    return missing_references


def outward_difference(concept_id, props, i_props):
    missing_references = []

    for h_label in i_props:
        if h_label in i_props and h_label in props:
            diff = list(set(i_props[h_label]) - set(props[h_label]))
        else:
            diff = i_props[h_label]
        if diff != []:
            missing = [concept_id, h_label, diff]
            missing_references.append(missing)
    return missing_references


def get_concept(dom, concept_id):
    root = dom.childNodes.item(0)

    for node in root.childNodes:
        if (node.nodeType == node.ELEMENT_NODE
        and node.nodeName == 'skos:Concept'):
            if concept_id == node.attributes.items()[0][1]:
                return node
    return None


def undefined_concept_references(dom):
    missing_references = []
    concepts = list_concepts(dom)
    root = dom.childNodes.item(0)
    hierarchy_labels = ['skos:broader', 'skos:narrower', 'skos:related']

    # Iterate through all concepts to check if they include references
    # to concepts that do not exist
    for node in root.childNodes:
        if (node.nodeType == node.ELEMENT_NODE
        and node.nodeName == 'skos:Concept'):
            concept_id = node.attributes.items()[0][1]

            for property in node.childNodes:
                if (property.nodeType == property.ELEMENT_NODE
                and property.nodeName in hierarchy_labels):
                    object_id = property.attributes.items()[0][1]
                    h_label = property.nodeName

                    if object_id not in concepts:
                        missing = [concept_id, h_label, object_id]
                        missing_references.append(missing)
    return missing_references


def hierarchical_properties_dict(node):
    # Each hierarchical property is stored in a dictionary with the name of the
    # property and its value.
    hierarchical_properties = {}
    hierarchy_labels = ['skos:broader', 'skos:narrower', 'skos:related']

    for property in node.childNodes:
        if (property.nodeType == property.ELEMENT_NODE
        and property.nodeName in hierarchy_labels):
            prop_name = property.nodeName
            object_id = property.attributes.items()[0][1]

            if prop_name in hierarchical_properties:
                hierarchical_properties[prop_name].append(object_id)
            else:
                hierarchical_properties[prop_name] = [object_id]
    return hierarchical_properties

#TODO: update code to match current folder structure
# break code in smaller defs.
# def create_concept_list(root):
#
#     a_list = ['altLabel','prefLabel', 'broader', 'narrower', 'related', 'schemes', 'matches', 'change dates', 'notes']
#     concept_list = []
#
#     for a_element in root:
#         if a_element.tag[38:] == 'Concept':
#             concept_dict = {}
#             concept_id = str(a_element.attrib.items()[0][1][42:])
#             concept_dict['id'] = concept_id
#             topConcept_count = 0
#             for item in a_list:
#                 concept_dict[item] = []
#             for prop in a_element:
#                 prop_label = str(prop.tag[38:])
#                 if prop_label == 'prefLabel':
#                     prefLabel_dict = {}
#                     lang = str(prop.attrib.items()[0][1])
#                     label = str(prop.text.encode('utf-8'))
#                     prefLabel_dict['language'] = lang
#                     prefLabel_dict['Label'] = label
#                     concept_dict['prefLabel'].append(prefLabel_dict)
#                 elif prop_label == 'broader':
#                     the_id = prop.attrib.items()[0][1][42:]
#                     concept_dict['broader'].append(the_id)
#                 elif prop_label == 'narrower':
#                     the_id = prop.attrib.items()[0][1][42:]
#                     concept_dict['narrower'].append(the_id)
#                 elif prop_label == 'related':
#                     the_id = prop.attrib.items()[0][1][42:]
#                     concept_dict['related'].append(the_id)
#                 elif prop_label == 'inScheme':
#                     the_scheme = prop.attrib.items()[0][1][42:]
#                     concept_dict['schemes'].append(the_scheme)
#                 elif prop_label == 'exactMatch':
#                     match = prop.attrib.items()[0][1]
#                     concept_dict['matches'].append(match)
#                 elif prop_label == 'altLabel':
#                     altLabel_dict = {}
#                     lang = str(prop.attrib.items()[0][1])
#                     label = str(prop.text.encode('utf-8'))
#                     altLabel_dict['language'] = lang
#                     altLabel_dict['Label'] = label
#                     if 'altLabel' in concept_dict:
#                         concept_dict['altLabel'].append(altLabel_dict)
#                     else:
#                         concept_dict['altLabel'] = []
#                         concept_dict['altLabel'].append(altLabel_dict)
#                 elif prop_label == 'changeNote':
#                     for item in prop:
#                         for a_date in item:
#                             change_date = a_date.text
#                             concept_dict['change dates'].append(change_date)
#                 elif prop_label == 'scopeNote':
#                     the_note = prop.text
#                     concept_dict['notes'].append(the_note)
#                 elif prop_label == 'topConceptOf':
#                     topConcept_count += 1
#                 concept_dict['#Top Concepts'] = topConcept_count
#             concept_list.append(concept_dict)
#     return concept_list
#
# def average_label (language):
#     total_concepts = 0
#     all_label_length = 0
#     for concept in concept_list:
#         number_of_labels = 0
#         total_label_length = 0
#         for label in concept['prefLabel']:
#             if label['language'] == language:
#                 number_of_labels += 1
#                 total_label_length += len(label['Label'])
#         if number_of_labels > 0:
#             total_concepts += 1
#             average_label_length = total_label_length/float(number_of_labels)
#             all_label_length += average_label_length
#
#     final_average = all_label_length/float(total_concepts)
#     return final_average
#
# def plot_dates(dictionary, list):
#     df = pd.DataFrame(dictionary)
#     if len(list) == 1:
#         item = list[0]
#         if item == 'day':
#             df.groupby(df['date'].dt.day).count().plot(kind="bar")
#         elif item == 'month':
#             df.groupby(df['date'].dt.month).count().plot(kind="bar")
#         elif item == 'year':
#             df.groupby(df['date'].dt.year).count().plot(kind="bar")
#     elif len(list) == 2:
#         list.sort()
#         item1 = list[0]
#         item2 = list[1]
#         if item1 == 'day' and item2 == 'month':
#             df.groupby([df['date'].dt.day, df['date'].dt.month]).count().plot(kind="bar")
#         elif item1 == 'day' and item2 == 'year':
#             df.groupby([df['date'].dt.day, df['date'].dt.year]).count().plot(kind="bar")
#         elif item1 == 'month' and item2 == 'year':
#             df.groupby([df['date'].dt.month, df['date'].dt.year]).count().plot(kind="bar")
#     elif len(list) == 3:
#         list.sort()
#         df.groupby([df['date'].dt.day, df['date'].dt.month, df['date'].dt.year]).count().plot(kind="bar")
#     else:
#         if len(list) < 1:
#             print 'Too few list inputs'
#         else:
#             print 'Too many list inputs'
#         return
#     show()
#
# def hex_code_colors():
#     a = hex(random.randrange(0,256))
#     b = hex(random.randrange(0,256))
#     c = hex(random.randrange(0,256))
#     a = a[2:]
#     b = b[2:]
#     c = c[2:]
#     if len(a)<2:
#         a = "0" + a
#     if len(b)<2:
#         b = "0" + b
#     if len(c)<2:
#         c = "0" + c
#     z = a + b + c
#     return "#" + z.upper()
#
# def average_rel(dict):
#     average = 0
#     total = 0
#     for i in dict:
#         if i == 0:
#             j = -1
#         else:
#             j = i
#         total += dict[i]
#         average += dict[i] * j
# #         print average, total
#     return average/float(total)
#
# def create_relation_dict(list):
#     relations_dict = {}
#     no_rel = 0
#     total_broader = {}
#     total_narrower = {}
#     total_related = {}
#     for concept in list:
#         broader = concept['broader']
#         narrower = concept['narrower']
#         related = concept['related']
#         number_broader = len(broader)
#         number_narrower = len(narrower)
#         number_related = len(related)
#         relations_dict[concept['id']] = [number_broader, number_narrower, number_related]
#         total = number_broader + number_narrower + number_related
#         if total == 0:
#             no_rel += 1
#         else:
#             if number_broader in total_broader:
#                 total_broader[number_broader] += 1
#             else:
#                 total_broader[number_broader] = 1
#             if number_narrower in total_narrower:
#                 total_narrower[number_narrower] += 1
#             else:
#                 total_narrower[number_narrower] = 1
#             if number_related in total_related:
#                 total_related[number_related] += 1
#             else:
#                 total_related[number_related] = 1
#     return relations_dict, no_rel, total_broader, total_narrower, total_related
#
# def create_relation_dict2(dict):
#     relation_dict2 = {}
#     for concept in dict:
#         relations = dict[concept]
#         string_relations = ""
#         for i in relations:
#             string_relations += str(i)
#             string_relations += '-'
#         string_relations = ''.join(string_relations.split())[:-1].upper()
#         if string_relations in relation_dict2:
#             relation_dict2[string_relations] += 1
#         else:
#             relation_dict2[string_relations] = 1
#     # print len(relation_dict2), relation_dict2
#     return relation_dict2
#
# def is_number(s):
#     try:
#         float(s)
#         return True
#     except ValueError:
#         return False
#
# startTime = datetime.now()
#
# os.chdir('../thesaurus_export')
#
# tree = ET.parse('full_skos.rdf')
# root = tree.getroot()
#
# writer = pd.ExcelWriter('Adlib_full.xlsx', engine='xlsxwriter')
#
# concept_list = create_concept_list(root)
# # print concept_list[0]['matches']
#
# print len(concept_list)
#
# df_full = pd.DataFrame.from_dict(concept_list)
# df_full.to_excel(writer, sheet_name='Full')
# # print df_full[:1]
#
# relations_dict, no_rel, total_broader, total_narrower, total_related = create_relation_dict(concept_list)
# relation_df = pd.DataFrame([total_broader, total_narrower, total_related], index=['Broader', 'Narrower', 'Related'])
# # print relation_df
# relation_df.to_excel(writer, sheet_name='Relation1')
#
# relation_dict2 = create_relation_dict2(relations_dict)
#
# # Print a table with the number of relations
# relation_df2 = pd.DataFrame(relation_dict2.items(), columns=['B-N-R', '#'])
# relation_df2 = relation_df2.sort_values(by=['#'], ascending=False)
# # print relation_df2
# relation_df2.to_excel(writer, sheet_name='Relation2')
#
# matches_dict = {}
# concept_label_dict = {}
# count_preflabel_dict = {}
# count_altlabel_dict = {}
# pref_language_dict = {}
# alt_language_dict = {}
# for concept in concept_list:
#     concept_id = concept['id']
#     matches = concept['matches']
#     matches_dict[concept_id] = matches
#     label_dict = {}
#     pref = concept['prefLabel']
#     alt = concept['altLabel']
#     label_dict['pref'] = pref
#     label_dict['alt'] = alt
#     if len(pref) in count_preflabel_dict:
#         count_preflabel_dict[len(pref)] += 1
#     else:
#         count_preflabel_dict[len(pref)] = 1
#     if len(alt) in count_altlabel_dict:
#         count_altlabel_dict[len(alt)] += 1
#     else:
#         count_altlabel_dict[len(alt)] = 1
#     label_dict['#pref'] = len(pref)
#     label_dict['#alt'] = len(alt)
#     pref_language_list = []
#     for i in pref:
#         language = i['language']
#         pref_language_list.append(language)
#         if language in pref_language_dict:
#             pref_language_dict[language] += 1
#         else:
#             pref_language_dict[language] = 1
#     label_dict['Pref languages'] = pref_language_list
#     alt_language_list = []
#     for i in alt:
#         language = i['language']
#         alt_language_list.append(language)
#         if language in alt_language_dict:
#             alt_language_dict[language] += 1
#         else:
#             alt_language_dict[language] = 1
#     label_dict['Alt languages'] = alt_language_list
#     concept_label_dict[concept['id']] = label_dict
# # print concept_label_dict
# print count_preflabel_dict
# print count_altlabel_dict
# print alt_language_dict, pref_language_dict
#
# label_df = pd.DataFrame.from_dict(concept_label_dict, orient='index')
# label_df.to_excel(writer, sheet_name='Labels')
# oC = 0
# tC = 0
# qC = 0
# for concept in concept_label_dict:
#     concept = concept_label_dict[concept]
#     if concept['#pref'] == 2:
#         prefs = concept['pref']
#         label1 = ''
#         for label in prefs:
#             if label1 == '':
#                 label1 = label['Label']
#             else:
#                 label2 = label['Label']
#         difference1 = len(label1) - len(label2)
#         difference2 = len(label2) - len(label1)
#         if difference1 > 5 or difference2 > 5:
#             if '(' in label1:
#                 oC +=1
# #                 print 'one', label1, label2
#             elif '(' in label2:
#                 tC += 1
# #                 print 'two', label2, label1
#             else:
#                 qC += 1
# print oC, tC, qC
#
#
#
#
# # print "The average length of a Dutch label is", average_label('nl')
# # print "The average length of an English label is", average_label('en')
# # print "Average amount of broader relations =", average_rel(total_broader)
# # print "Average amount of narrower relations =", average_rel(total_narrower)
# # print "Average amount of related relations =", average_rel(total_related)
#
#
# no_matches = 0
# aat_matches = 0
# tgn_matches = 0
# mimo_matches = 0
# wiki_matches = 0
# number_match = 0
# geoname_matches =0
# other_matches = 0
# for concept in concept_list:
#     if len(concept['matches']) == 0:
#         no_matches += 1
#     else:
#         for match in concept['matches']:
#             if 'aat' in match:
#                 aat_matches += 1
#             elif 'tgn' in match or 'TGN' in match:
#                 tgn_matches += 1
#             elif 'mimo' in match:
#                 mimo_matches += 1
#             elif 'wiki' in match:
#                 wiki_matches += 1
#             elif is_number(match):
#                 number_match += 1
#             elif 'geonames' in match:
#                 geoname_matches += 1
#             else:
# #                 print concept['prefLabel'], match
#                 other_matches += 1
# number_matches_dict ={}
# number_matches_dict['none'] = no_matches
# number_matches_dict['AAT'] = aat_matches
# number_matches_dict['TGN'] = tgn_matches
# number_matches_dict['MIMO'] = mimo_matches
# number_matches_dict['Wiki'] = wiki_matches
# number_matches_dict['Numbers'] = number_match
# number_matches_dict['Geonames'] = geoname_matches
# number_matches_dict['other'] = other_matches
# matches_df = pd.DataFrame(number_matches_dict.items(), columns=['Matches', '#'])
# matches_df.to_excel(writer, sheet_name='Matches')
#
# # # Data to plot
# # labels = 'AAT', 'TGN', 'MIMO', 'Wiki', 'Number','Geonames' ,'Other'
# # matches = [aat_matches, tgn_matches, mimo_matches, wiki_matches, number_match, geoname_matches, other_matches]
# # colors = ['blue', 'red', 'yellow', 'green', 'orange', 'purple', 'pink']
# # # for i in range(len(matches)):
# # #     colors.append(hex_code_colors())
# # plt.pie(matches, colors=colors,autopct='%1.1f%%', shadow=True, startangle=140)
# # plt.axis('equal')
# # plt.legend(labels)
# # plt.title('Matches with external sources')
# # plt.show()
#
#
#
# print datetime.now() - startTime
