# Program to set word start and end times in an ELAN file
# by extracting the relevant information from a Toolbox file.
#
# Jan Strunk
# January 2013

# Import module to parse ELAN files
import elan

import codecs

# Regular expressions
import re

import sys

# Nice command line argument parsing
import argparse

# Create an command-line argument parser
parser = argparse.ArgumentParser(description="Set word start and end times in an ELAN file using information supplied in a Toolbox file.")

# Add arguments with sensible defaults to parser
parser.add_argument("inputfilename", help="the name of the input ELAN file (created by importing a Toolbox file)")
parser.add_argument("toolboxfilename", help="the name of the imported Toolbox file containing information about word start and end times")
parser.add_argument("outputfilename", help="the name of the output ELAN file")
parser.add_argument("-reftier", "--reftier", required=False, default="ref", help="the name of the reference tier (defaults to ref)")
parser.add_argument("-texttier", "--texttier", required=False, default="t", help="the name of the transcription tier containing the words (defaults to t)")
parser.add_argument("-wordstarttier", "--wordstarttier", required=False, default="WordBegin", help="the name of the tier containing the word start times (defaults to WordBegin)")
parser.add_argument("-wordendtier", "--wordendtier", required=False, default="WordEnd", help="the name of the tier containing the word end times (defaults to WordEnd)")


# Parse command-line arguments
args = vars(parser.parse_args())

# Process obligatory command-line arguments
input_file_name = args["inputfilename"]
output_file_name = args["outputfilename"]
toolbox_file_name = args["toolboxfilename"]
reference_tier_name = args["reftier"]
text_tier_name = args["texttier"]
word_start_tier_name = args["wordstarttier"]
word_end_tier_name = args["wordendtier"]


# Function to read in an existing Toolbox file
# Arguments:
# 1. file name
# 2. encoding (defaults to utf-8)
# Returns a list of Toolbox lines as tuples (tier marker, line, line ending)
def readToolboxFile(file_name, encoding="utf-8"):

    # Compile a regular expression to find Toolbox tier markers
    tier_marker_re = re.compile("^" + r"\\(\S+)(?=($|\s+))")
    
    # Compile a regular expression to find line endings
    line_ending_re = re.compile(r"([\r\n]+)$")
    
    # A list of Toolbox lines
    toolbox_lines = []
    
    # Open Toolbox file
    toolbox_file = codecs.open(file_name, "r", encoding)
    
    # Go through the lines in the file
    for line in toolbox_file:
        
        # Tier marker in current line
        cur_tier_marker = None
        
        # Line ending in current line
        cur_line_ending = ""
        
        # Search for a tier marker in the current line
        match = tier_marker_re.search(line)
        if match:
            cur_tier_marker = match.group(1)
        
        # Search for a line ending in the current line
        match = line_ending_re.search(line)
        if match:
            cur_line_ending = match.group(1)
        
        # Put together tuple for the current line
        cur_line_tuple = (cur_tier_marker, line, cur_line_ending)
        
        # Add current line to the list of lines
        toolbox_lines.append(cur_line_tuple)
    
    # Return the list of lines
    return toolbox_lines

# Function to extract information about word start and end times
# from a Toolbox file
# Arguments:
# 1. The Toolbox as read in by readToolboxFile
# returns a dictionary from Toolbox references
# to a list of two lists (one with word start times
# and one with word end times)
def extractWordTimes(toolbox_file):

    # Dictionary from Toolbox annotation unit IDs to word start and end times
    toolbox_refs_to_word_times = {}

    # Compile a regular expression to extract the tier contents
    tier_contents_re = re.compile("^" + r"\\(\S+)\s+(.+)$")

    # Current utterance ID
    cur_utterance_id = None
    cur_word_start_times = []
    cur_word_end_times = []
    
    line_number = 0

    # Go through Toolbox file to find annotation units with word start and end times
    for line in toolbox_file:
        
        # Increase line number
        line_number += 1
        
        # Unpack line contents
        (cur_toolbox_marker, cur_line, cur_line_ending) = line
        
        # Check whether we have found the reference tier
        if cur_toolbox_marker == reference_tier_name:
                    
            # Save current word start and end times of preceding utterance
            if cur_utterance_id is not None:
                
                if len(cur_word_start_times) > 0 and len(cur_word_end_times) > 0:
        
                    # Save information in dictionary
                    toolbox_refs_to_word_times[cur_utterance_id] = [cur_word_start_times, cur_word_end_times]

                    cur_utterance_id = None
                    cur_word_start_times = []
                    cur_word_end_times = []
                
                else:
                    
                    print("Warning: Did not find word start and end times for the following, possibly empty utterance:", cur_utterance_id)
            
            # Extract the contents of the reference tier
            match = tier_contents_re.search(cur_line)

            if match:

                cur_utterance_id = match.group(2).strip()

            else:

                print("Something is wrong. I cannot extract the reference from the reference tier in line " + str(line_number) +".")
                print(line)
                sys.exit()
    
        elif cur_toolbox_marker == word_start_tier_name:
        
            # Extract the contents of the tier
            match = tier_contents_re.search(cur_line)

            if match:

                cur_word_start_times.extend(match.group(2).strip().split())

            else:

                print("Something is wrong. I cannot extract the word start times from the tier in line " + str(line_number) +".")
                print(line)
                sys.exit()

        elif cur_toolbox_marker == word_end_tier_name:
        
            # Extract the contents of the tier
            match = tier_contents_re.search(cur_line)

            if match:

                cur_word_end_times.extend(match.group(2).strip().split())

            else:

                print("Something is wrong. I cannot extract the word start times from the tier in line " + str(line_number) +".")
                print(line)
                sys.exit()
            
    # Save current word start and end times
    if cur_utterance_id is not None:
        
        if len(cur_word_start_times) > 0 and len(cur_word_end_times) > 0:
        
            # Save information in dictionary
            toolbox_refs_to_word_times[cur_utterance_id] = [cur_word_start_times, cur_word_end_times]

            cur_utterance_id = None
            cur_word_start_times = []
            cur_word_end_times = []
        
        else:
            
            print("Warning: Did not find word start and end times for the following, possibly empty utterance:", cur_utterance_id)

    return toolbox_refs_to_word_times

# Safety check
if input_file_name == output_file_name:
    print("Input and output file name are the same. Cannot overwrite input file.")
    sys.exit()

print("Opening input ELAN file:", input_file_name)

# Try to open the input file
elan_file = elan.ELANFile.read_elan_file(input_file_name)

# Get the time order
time_order = elan_file.get_time_order()

print("Opening input Toolbox file:", toolbox_file_name)

# Try to open the Toolbox file
toolbox_file = readToolboxFile(toolbox_file_name)

print("Extracting word start and end times from Toolbox file.")

toolbox_refs_to_word_times = extractWordTimes(toolbox_file)

print("Searching for relevant tiers in the ELAN file.")

relevant_tiers = []

for tier in elan_file.get_tiers():
    
    linguistic_type = tier.get_linguistic_type()
    
    # The linguistic type of the tier has to have the same
    # name as the Toolbox marker for the text tier
    if linguistic_type == text_tier_name:
        
        relevant_tiers.append(tier.get_tier_id())

# Status message
print("Tiers that need to be processed:", " ".join(relevant_tiers))

# Mapping from annotations to parent annotations
annotation_to_parent_annotation = {}

# Mapping from parent annotations to daughter annotations
parent_annotation_to_daughter_annotations = {}

# Go through the relevant tiers
# and determine which annotation is included in which
# annotation unit
for tier_name in relevant_tiers:
    
    # Status message
    print("Processing tier:", tier_name)
    
    # Get tier
    tier = elan_file.get_tier_by_id(tier_name)
    
    # Get annotations in the tier
    annotations = tier.get_annotations()
    
    # Get the parent tier
    parent_tier_name = tier.get_parent_tier_ref()

    # Get tier from ELANFile
    parent_tier = elan_file.get_tier_by_id(parent_tier_name)
    
    # Annotations on the parent tier
    parent_annotations = parent_tier.get_annotations()
    
    # Go through annotations
    for annotation in annotations:
        
        # Get annotation id
        annotation_id = annotation.get_annotation_id()
        
        # Get start time
        annotation_start_time = annotation.get_start_time()
        
        # Get end time
        annotation_end_time = annotation.get_end_time()
        
        for parent_annotation in parent_annotations:
            
            # Get id
            parent_annotation_id = parent_annotation.get_annotation_id()
            
            # Get parent annotation value
            parent_annotation_value = parent_annotation.get_annotation_value()
            
            # Make sure that there are word times for the current parent annotation
            # Otherwise ignore it
            if parent_annotation_value not in toolbox_refs_to_word_times:
                
#                print("No word times for annotation id", parent_annotation_value)
                continue
        
            # Get start time
            parent_start_time = parent_annotation.get_start_time()
        
            # Get end time
            parent_end_time = parent_annotation.get_end_time()
            
            # Is the current annotation included in the current parent annotation?
            if annotation_start_time >= parent_start_time and annotation_end_time <= parent_end_time:
                
                annotation_to_parent_annotation[annotation_id] = parent_annotation_id
                
                if parent_annotation_id in parent_annotation_to_daughter_annotations:
                    
                    parent_annotation_to_daughter_annotations[parent_annotation_id].append(annotation_id)
                
                else:
                    
                    parent_annotation_to_daughter_annotations[parent_annotation_id] = [annotation_id]

        # Have we found a parent annotation?
        if annotation_id not in annotation_to_parent_annotation:
                
            raise RuntimeError("Cannot find parent annotation of annotation", annotation_id + ".")

# Go through all relevant tiers in the ELAN file
for tier_id in relevant_tiers:
    
    print("Setting word start and end times in tier", tier_id)
    
    tier = elan_file.get_tier_by_id(tier_id)
    
    # Go through all annotations in the tier
    for annotation in tier:
        
        # Get annotation ID
        annotation_id = annotation.get_annotation_id()
        
        # Get annotation value
        annotation_value = annotation.get_annotation_value()
        
        # Determine parent annotation, i.e. the annotation unit
        if annotation_id in annotation_to_parent_annotation:
            
            parent_annotation_id = annotation_to_parent_annotation[annotation_id]
            
            parent_annotation = elan_file.get_annotation_by_id(parent_annotation_id)
            
            # Determine Toolbox reference
            parent_reference = parent_annotation.get_annotation_value()
            
            # Determine parent start and end times
            parent_start_time = parent_annotation.get_start_time()
            parent_end_time = parent_annotation.get_end_time()
            
#            print("Processing annotation unit", parent_reference)
        
        else:
            
            print("Cannot find the parent annotation of annotation", annotation_id)

        # Determine the position of the current daughter annotations
        # within the parent annotation
        
        # Sorting numerically according to annotation id, here
        # because sorting by start_times did not work
        position = 0
        
        def remove_ann(ann_id):
            return int(re.sub("^a(nn)?", "", ann_id))
        
        for other_annotation_id in sorted(parent_annotation_to_daughter_annotations[parent_annotation_id], key=remove_ann):
            
#            print("annotation_id", annotation_id)
#            print("other_annotation_id", other_annotation_id)
            
            if other_annotation_id == annotation_id:
                        
                break
    
            position += 1
        
        # Get relevant word start and end times
        if parent_reference in toolbox_refs_to_word_times:
            
            if position < len(toolbox_refs_to_word_times[parent_reference][0]):
                
                # Get start and end time from Toolbox file for current word
                # Convert seconds to milliseconds by deleting the dot (avoid floating point problems)
                start_time = int(re.sub(r"\.", "", toolbox_refs_to_word_times[parent_reference][0][position]))
                end_time = int(re.sub(r"\.", "", toolbox_refs_to_word_times[parent_reference][1][position]))
                
                # Make sure that the start time and end time is within the parent annotation
                if start_time < parent_start_time:
                    print("Start time", start_time, "of annotation unit", annotation_id,"is smaller than the annotation time", parent_start_time, "of its parent annotation", parent_annotation_id, "(" + parent_reference + ")")
                    
                    # Adjust parent start time
                    parent_start_time_slot_id = parent_annotation.get_start_time_slot()
                    parent_start_time_slot = time_order.get_time_slot_by_id(parent_start_time_slot_id)
                    parent_start_time_slot.set_time_value(start_time)

                if end_time > parent_end_time:
                    print("End time", end_time, "of annotation unit", annotation_id,"is greater than the annotation time", parent_end_time, "of its parent annotation", parent_annotation_id, "(" + parent_reference + ")")

                    # Adjust parent end time
                    parent_end_time_slot_id = parent_annotation.get_end_time_slot()
                    parent_end_time_slot = time_order.get_time_slot_by_id(parent_end_time_slot_id)
                    parent_end_time_slot.set_time_value(end_time)
                
                # Set the times in the time order directly
                start_time_slot_id = annotation.get_start_time_slot()
                start_time_slot = time_order.get_time_slot_by_id(start_time_slot_id)
                start_time_slot.set_time_value(start_time)
                end_time_slot_id = annotation.get_end_time_slot()
                end_time_slot = time_order.get_time_slot_by_id(end_time_slot_id)
                end_time_slot.set_time_value(end_time)
            
            else:
                
                print("Could not determine position of word", annotation_value, "in parent unit", parent_reference)
                print("Position:", position)
                print("Annotation ID:", annotation_id)
                print(len(toolbox_refs_to_word_times[parent_reference][0]))
                print(toolbox_refs_to_word_times[parent_reference][0])
                print(" ".join(sorted(parent_annotation_to_daughter_annotations[parent_annotation_id], key=remove_ann)))
                input()
                sys.exit()
        
        else:
            
            print("Could not determine annotation unit of word", annotation_value)
            sys.exit()

# Output the modified ELAN file
output_file = codecs.open(output_file_name, "w", "utf-8")
output_file.write(elan_file.to_xml())
output_file.close()
