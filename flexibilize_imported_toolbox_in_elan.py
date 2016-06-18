# Program to make words time-alignable after importing a Toolbox
# file into ELAN.
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
parser = argparse.ArgumentParser(description="Make words in an ELAN file time-alignable after importing a Toolbox file.")

# Add arguments with sensible defaults to parser
parser.add_argument("inputfilename", help="the name of the input ELAN file (created by importing a Toolbox file)")
parser.add_argument("outputfilename", help="the name of the output flexibilized ELAN file")

# Parse command-line arguments
args = vars(parser.parse_args())

# Process obligatory command-line arguments
input_file_name = args["inputfilename"]
output_file_name = args["outputfilename"]

# Safety check
if input_file_name == output_file_name:
    print("Input and output file name are the same. Cannot overwrite input file.")
    sys.exit()

print("Opening input file:", input_file_name)

# Try to open the input file
elan_file = elan.ELANFile.read_elan_file(input_file_name)

# Get original time order
original_time_order = elan_file.get_time_order()

# Print status message
print("Number of time slots in the original time order:", len(original_time_order))

# Create a new time order
new_time_order = elan.ELANTimeOrder(elan_file)

# Mapping from the old time order to the new
time_order_mapping = {}

# Go through linguistic types to find those with the constraint Included_In
relevant_linguistic_types = []
time_alignable_types = []

for linguistic_type in elan_file.get_linguistic_types():
    
    if linguistic_type.get_constraints() == "Included_In":
        
        relevant_linguistic_types.append(linguistic_type.get_linguistic_type_id())
    
    if linguistic_type.is_time_alignable():

        time_alignable_types.append(linguistic_type.get_linguistic_type_id())

# Status message
print("Linguistic types that need to be flexibilized:", " ".join(relevant_linguistic_types))
print("Linguistic types that are timealignable:", " ".join(time_alignable_types))

relevant_tiers = []
time_alignable_tiers = []

# Look up tiers that need to be flexibilized
for tier in elan_file.get_tiers():
    
    # Does the tier belong to a relevant linguistic type?
    if tier.get_linguistic_type() in relevant_linguistic_types:

        relevant_tiers.append(tier.get_tier_id())
    
    if tier.get_linguistic_type() in time_alignable_types:
        
        time_alignable_tiers.append(tier.get_tier_id())

# Status message
print("Tiers that need to be flexibilized:", " ".join(relevant_tiers))

# Original start and end times of parent annotations
original_annotation_times = {}

# Go through all time alignable tiers
for tier_id in time_alignable_tiers:
    
    # Get tier
    tier = elan_file.get_tier_by_id(tier_id)
    
    # Go through annotations
    for annotation in tier:
        
        # Get ID
        annotation_id = annotation.get_annotation_id()
        
        # Get start time
        annotation_start_time = annotation.get_start_time()
        
        # Get end time
        annotation_end_time = annotation.get_end_time()
        
        # Save original times in dictionary
        # if the annotations were time aligned
        if annotation_start_time is not None or annotation_end_time is not None:
            
            original_annotation_times[annotation_id] = (annotation_start_time, annotation_end_time)

# Mapping from annotations to parent annotations
annotation_to_parent_annotation = {}

# Mapping from parent annotations to daughter annotations
parent_annotation_to_daughter_annotations = {}

# Mapping from time slots to annotations
time_slots_to_annotations = {}

# Remember position of daughter annotations
daughter_positions = {}

# Look up the time values that need to be split
# Go through the relevant tiers
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
    
    # Produce a mapping from time slots to parent annotations
    parent_time_slots = {}
    
    # Go through parent annotations
    for parent_annotation in parent_annotations:
        
        # Get id
        parent_id = parent_annotation.get_annotation_id()
        
        # Get start time slot
        parent_start_time_slot = parent_annotation.get_start_time_slot()
        
        # Get end time slot
        parent_end_time_slot = parent_annotation.get_end_time_slot()
        
        # Save time slots in mapping from time slots to annotations
        if parent_start_time_slot in time_slots_to_annotations:
            
            time_slots_to_annotations[parent_start_time_slot].append((parent_id, "parent", "start"))
        
        else:
            
            time_slots_to_annotations[parent_start_time_slot] = [(parent_id, "parent", "start")]

        if parent_end_time_slot in time_slots_to_annotations:
            
            time_slots_to_annotations[parent_end_time_slot].append((parent_id, "parent", "end"))
        
        else:
            
            time_slots_to_annotations[parent_end_time_slot] = [(parent_id, "parent", "end")]
            
            # Add parent time slots to dictionary
            parent_time_slots[parent_start_time_slot] = parent_id
            parent_time_slots[parent_end_time_slot] = parent_id
        
#         # Extract start number
#         parent_start_time_number = int(re.sub("^ts", "", parent_start_time_slot))
# 
#         # Extract end number
#         parent_end_time_number = int(re.sub("^ts", "", parent_end_time_slot))
#         
#         for number in range(parent_start_time_number, parent_end_time_number + 1):
# 
#             # TODO: Correct?
# 
#             # Add entry to the mapping
#             parent_time_slots["ts" + str(number)] = parent_id
    
    # Go through annotations and save information about start and end time slots
    for annotation in annotations:
        
        # Get annotation id
        annotation_id = annotation.get_annotation_id()
        
        # Get start time slot
        annotation_start_time_slot = annotation.get_start_time_slot()
        
        # Get end time slot
        annotation_end_time_slot = annotation.get_end_time_slot()

        # Save time slots in mapping from time slots to annotations
        if annotation_start_time_slot in time_slots_to_annotations:
            
            time_slots_to_annotations[annotation_start_time_slot].append((annotation_id, "daughter", "start"))
        
        else:
            
            time_slots_to_annotations[annotation_start_time_slot] = [(annotation_id, "daughter", "start")]

        if annotation_end_time_slot in time_slots_to_annotations:
            
            time_slots_to_annotations[annotation_end_time_slot].append((annotation_id, "daughter", "end"))
        
        else:
            
            time_slots_to_annotations[annotation_end_time_slot] = [(annotation_id, "daughter", "end")]
    
    # Go through annotations and save information which annotations belong
    # together under one parent annotation
    preceding_first_daughter_annotations = {}
    
    for annotation in annotations:
        
        # Get annotation id
        annotation_id = annotation.get_annotation_id()
        
        # Get start time slot
        annotation_start_time_slot = annotation.get_start_time_slot()
        
        # Get end time slot
        annotation_end_time_slot = annotation.get_end_time_slot()
        
        # Position
        position = 0
        
        # Look for preceding annotations
        current_annotation_id = annotation_id
        current_annotation_start_time_slot = annotation_start_time_slot
        current_annotation_start_time = annotation.get_start_time()
        
        while (current_annotation_start_time is None):
        
            if current_annotation_start_time_slot in time_slots_to_annotations:
                
                # Look at other annotations starting or ending at the current time slot
                for other_annotation in time_slots_to_annotations[current_annotation_start_time_slot]:
                    
                    (other_annotation_id, other_annotation_type, other_annotation_part) = other_annotation
                    
                    # Found a preceding annotation
                    if other_annotation_id != current_annotation_id \
                    and other_annotation_type == "daughter" \
                    and other_annotation_part == "end":
                    
                        current_annotation = elan_file.get_annotation_by_id(other_annotation_id)
                        current_annotation_id = other_annotation_id
                        current_annotation_start_time_slot = current_annotation.get_start_time_slot()
                        current_annotation_start_time = current_annotation.get_start_time()
                        position += 1
            
        # Have we found a preceding first daughter annotation
        if current_annotation_start_time is not None:
            
            # Only enter non-reflexive relations into the dictionary
            if current_annotation_id != annotation_id:
                
                preceding_first_daughter_annotations[annotation_id] = current_annotation_id
                
            # Also save position
            daughter_positions[annotation_id] = position
        
        else:
            
            raise RuntimeError("Cannot find preceding first daughter annotation for annotation", annotation_id + ".")

    # Find parent annotations for first daughters and last daughters
    for annotation in annotations:

        # Get annotation id
        annotation_id = annotation.get_annotation_id()
        
        # Get start time slot
        annotation_start_time_slot = annotation.get_start_time_slot()
        
        # Get end time slot
        annotation_end_time_slot = annotation.get_end_time_slot()
        
        # Look up parent annotation        
        # For first daughter annotation
        if annotation_start_time_slot in parent_time_slots:
            
            # Get parent annotation
            parent_annotation_id = parent_time_slots[annotation_start_time_slot]
            
            # Add mapping from annotations to parent annotations
            annotation_to_parent_annotation[annotation_id] = parent_annotation_id

            # Add mapping from parent annotation to daughter annotations
            if parent_annotation_id in parent_annotation_to_daughter_annotations:
                
                parent_annotation_to_daughter_annotations[parent_annotation_id].append(annotation_id)
            
            else:
                
                parent_annotation_to_daughter_annotations[parent_annotation_id] = [annotation_id]

        # For last daughter annotation
        elif annotation_end_time_slot in parent_time_slots:
            
            # Get parent annotation
            parent_annotation_id = parent_time_slots[annotation_end_time_slot]
            
            # Add mapping from annotations to parent annotations
            annotation_to_parent_annotation[annotation_id] = parent_annotation_id

            # Add mapping from parent annotation to daughter annotations
            if parent_annotation_id in parent_annotation_to_daughter_annotations:
                
                parent_annotation_to_daughter_annotations[parent_annotation_id].append(annotation_id)
            
            else:
                
                parent_annotation_to_daughter_annotations[parent_annotation_id] = [annotation_id]
    
    # Find parent annotations for middle daughters
    for annotation in annotations:

        # Get annotation id
        annotation_id = annotation.get_annotation_id()
        
        # Get start time slot
        annotation_start_time_slot = annotation.get_start_time_slot()
        
        # Get end time slot
        annotation_end_time_slot = annotation.get_end_time_slot()
        
        # For daughter annotations in the middle
        if annotation_start_time_slot not in parent_time_slots \
        and annotation_end_time_slot not in parent_time_slots:

            # Find the preceding first daughter annotation
            if annotation_id in preceding_first_daughter_annotations:
                
                preceding_first_daughter_annotation_id = preceding_first_daughter_annotations[annotation_id]
                
                if preceding_first_daughter_annotation_id in annotation_to_parent_annotation:
                    
                    parent_annotation_id = annotation_to_parent_annotation[preceding_first_daughter_annotation_id]
                
                else:
                    
                    raise RuntimeError("Cannot identify parent annotation for middle daughter annotation", annotation_id + ".")
                
            else:
                
                raise RuntimeError("Cannot determine parent annotation for middle daughter annotation", annotation_id + ".")
            
            # Add mapping from annotations to parent annotations
            annotation_to_parent_annotation[annotation_id] = parent_annotation_id

            # Add mapping from parent annotation to daughter annotations
            if parent_annotation_id in parent_annotation_to_daughter_annotations:
                
                parent_annotation_to_daughter_annotations[parent_annotation_id].append(annotation_id)
            
            else:
                
                parent_annotation_to_daughter_annotations[parent_annotation_id] = [annotation_id]
            
# Function to remove "ann" before annotation IDs
def remove_ann(annotation_id):

    return int(re.sub("^ann", "", annotation_id))

def remove_ts(time_slot_id):
    
    return int(re.sub("^ts", "", time_slot_id))

# Status message
#for parent_annotation_id in sorted(parent_annotation_to_daughter_annotations, key=remove_ann):
#    
#    print("[" + parent_annotation_id + ":", " ".join(parent_annotation_to_daughter_annotations[parent_annotation_id]) + "]")

#for time_slot_id in sorted(time_slots_to_annotations, key=remove_ts):
#    
#    print(time_slot_id + ":")
#    
#    for annotation_tuple in time_slots_to_annotations[time_slot_id]:
#        
#        print(annotation_tuple)

# Offset for new time slots
offset = 0

# Go through time slots to produce a new time order
for time_slot in original_time_order:
    
    time_slot_id = time_slot.get_id()
    
    # Status message
#    print("Processing time slot:", time_slot_id)
    
    # Look up the relevant annotations
    if time_slot_id in time_slots_to_annotations:
        
        # Get the relevant annotations
        relevant_annotations = time_slots_to_annotations[time_slot_id]
        
        # Is there a pair of relevant annotations?
        if len(relevant_annotations) == 2:

            # Determine their relationship
            # Parent and daughter annotation
            if relevant_annotations[0][1] == "parent" and relevant_annotations[1][1] == "daughter":
                
                parent_annotation_id = relevant_annotations[0][0]
                
                annotation_id = relevant_annotations[1][0]
                
                # Add normal offset to current time slot
                new_parent_time_slot_id = "ts" + str(remove_ts(time_slot_id) + offset)
                
                # Add entry to mapping
                time_order_mapping[time_slot_id] = new_parent_time_slot_id

                # Increase offset by one for daughter annotation
                offset += 1

                # Add normal offset to current time slot
                new_daughter_time_slot_id = "ts" + str(remove_ts(time_slot_id) + offset)
                
                # Update parent annotation directly
                parent_annotation = elan_file.get_annotation_by_id(parent_annotation_id)

                # Update daughter annotation directly
                annotation = elan_file.get_annotation_by_id(annotation_id)
                
                # Determine if the time slot serves as start or end of the annotations
                if relevant_annotations[0][2] == "start" and relevant_annotations[1][2] == "start":

                    # Sanity check: Make sure that the two annotations
                    # share the same time slot
                    if parent_annotation.get_start_time_slot() != annotation.get_start_time_slot():
                        print("Parent and first daughter annotation did not share the same start time slot:")
                        print(parent_annotation_id, parent_annotation.get_start_time_slot())
                        print(annotation_id, annotation.get_start_time_slot())
                        sys.exit()
                    
                    parent_annotation.set_start_time_slot(new_parent_time_slot_id)

                    annotation.set_start_time_slot(new_daughter_time_slot_id)
                
                elif relevant_annotations[0][2] == "end" and relevant_annotations[1][2] == "end":

                    # Sanity check: Make sure that the two annotations
                    # share the same time slot
                    if parent_annotation.get_end_time_slot() != annotation.get_end_time_slot():
                        print("Parent and last daughter annotation did not share the same end time slot:")
                        print(parent_annotation_id, parent_annotation.get_end_time_slot())
                        print(annotation_id, annotation.get_end_time_slot())
                        sys.exit()
                    
                    parent_annotation.set_end_time_slot(new_parent_time_slot_id)
                    annotation.set_end_time_slot(new_daughter_time_slot_id)
                
                else:
                    print("Something went wrong: Parent and daughter annotation do not share the same kind of time slot:", parent_annotation_id, annotation_id)
                    sys.exit()
                
                # Add time slot to new time order for parent annotation
                new_time_order.add_time_slot(elan.ELANTimeSlot(new_parent_time_slot_id, time_slot.get_time_value()))
                
                # Add time slot to new time order for daughter annotation
                new_time_order.add_time_slot(elan.ELANTimeSlot(new_daughter_time_slot_id, time_slot.get_time_value()))
            
            # Two daughter annotations
            elif relevant_annotations[0][1] == "daughter" and relevant_annotations[0][2] == "end" and relevant_annotations[1][1] == "daughter" and relevant_annotations[1][2] == "start":
                
                first_annotation_id = relevant_annotations[0][0]
                
                second_annotation_id = relevant_annotations[1][0]
                
                # Get parent annotation
                if first_annotation_id in annotation_to_parent_annotation:
    
                    parent_annotation_id = annotation_to_parent_annotation[first_annotation_id]

#                 # Is this clause correct?
#                 elif second_annotation_id in annotation_to_parent_annotation:
#                     
#                     parent_annotation_id = annotation_to_parent_annotation[second_annotation_id]
#                 
                else:
                    
                    print("Cannot determine parent annotation for annotation", first_annotation_id + ".")
                    sys.exit()
                
                parent_annotation = elan_file.get_annotation_by_id(parent_annotation_id)
                
                # Get parent start and end time
                if parent_annotation_id in original_annotation_times:
                    
                    parent_start_time = original_annotation_times[parent_annotation_id][0]
                    parent_end_time = original_annotation_times[parent_annotation_id][1]
                
                else:
                    
                    print("Could not determine original annotation times for parent annotation", parent_annotation_id + ".")
                    sys.exit()
                
                # Calculate length of parent annotation
                parent_length = parent_end_time - parent_start_time
                
                # Determine the number of daughter annotations inside the parent annotation
                if parent_annotation_id in parent_annotation_to_daughter_annotations:
                    
                    number_of_daughters = len(parent_annotation_to_daughter_annotations[parent_annotation_id])
                
                else:
                    
                    print("Cannot determine the number of daughter annotations for annotation", parent_annotation_id + ".")
                    sys.exit()
                
                # Calculate mean length of daughter annotations
                daughter_length = parent_length / number_of_daughters
                
                # Determine the position of the current daughter annotations
                # within the parent annotation
                if first_annotation_id in daughter_positions:
                    
                    position = daughter_positions[first_annotation_id]
                
                else:
                    
                    raise RuntimeError("Could not determine position of daughter annotation", first_annotation_id, "in parent annotation", annotation_to_parent_annotation[first_annotation_id] + ".")
                
#                 position = 1
#                 
#                 for annotation_id in parent_annotation_to_daughter_annotations[parent_annotation_id]:
#                     
#                     if annotation_id == first_annotation_id:
#                         
#                         break
#     
#                     position += 1
                
                # Calculate the new time value for the end time
                # of the first daughter annotation and for the start time
                # of the second daughter annotation
                first_annotation_end_time = parent_start_time + daughter_length * (position + 1)
                second_annotation_start_time = parent_start_time + daughter_length * (position + 1) + 1
                
                # Add time slot for end of the first daughter annotation
                new_time_slot_id = "ts" + str(remove_ts(time_slot_id) + offset)
                
                # Add entry to mapping
                time_order_mapping[time_slot_id] = new_time_slot_id
                
                # Add time slot to new time order
                new_time_order.add_time_slot(elan.ELANTimeSlot(new_time_slot_id, first_annotation_end_time))
                
                # Update first annotation directly
                first_annotation = elan_file.get_annotation_by_id(first_annotation_id)
                first_annotation.set_end_time_slot(new_time_slot_id)
    
                # Add time slot for the start of the second daughter annotation
                offset += 1
                new_time_slot_id = "ts" + str(remove_ts(time_slot_id) + offset)
                
                # Add time slot to new time order
                new_time_order.add_time_slot(elan.ELANTimeSlot(new_time_slot_id, first_annotation_end_time))
                
                # Update second annotation directly
                second_annotation = elan_file.get_annotation_by_id(second_annotation_id)
                second_annotation.set_start_time_slot(new_time_slot_id)
            
            else:
                print("Unknown relationship between two annotations sharing a time slot.")
                print(relevant_annotations)
                sys.exit()
        
        # Is there just one relevant annotation?
        # Parent annotation containing no words, e.g. for comments
        elif len(relevant_annotations) == 1:
            
            # Get annotation ID
            annotation_id = relevant_annotations[0][0]
            
            # Make sure it really is a parent annotation
            if relevant_annotations[0][1] == "parent":
                
                # Beginning or end of annotation?
                if relevant_annotations[0][2] == "start":
                    
                    # Update time slot for annotation
                    new_time_slot_id = "ts" + str(remove_ts(time_slot_id) + offset)
                
                    # Add entry to mapping
                    time_order_mapping[time_slot_id] = new_time_slot_id
                
                    # Add time slot to new time order
                    new_time_order.add_time_slot(elan.ELANTimeSlot(new_time_slot_id, time_slot.get_time_value()))
                    
                    # Update annotation directly
                    annotation = elan_file.get_annotation_by_id(annotation_id)
                    annotation.set_start_time_slot(new_time_slot_id)
                
                elif relevant_annotations[0][2] == "end":

                    # Update time slot for annotation
                    new_time_slot_id = "ts" + str(remove_ts(time_slot_id) + offset)
                
                    # Add entry to mapping
                    time_order_mapping[time_slot_id] = new_time_slot_id
                
                    # Add time slot to new time order
                    new_time_order.add_time_slot(elan.ELANTimeSlot(new_time_slot_id, time_slot.get_time_value()))
                    
                    # Update annotation directly
                    annotation = elan_file.get_annotation_by_id(annotation_id)
                    annotation.set_end_time_slot(new_time_slot_id)

            # Something is wrong
            else:
                print("Only one annotation found for time slot.")
                print(relevant_annotations)
                sys.exit()
        
        # Something is wrong
        else:
            
            print("Incorrect number of relevant annotations found for time slot.")
            print(relevant_annotations)
            sys.exit()
                
    # No relevant annotations for the current time slot
    else:
        
        # Add updated time slot
        new_time_slot_id = "ts" + str(remove_ts(time_slot_id) + offset)
            
        # Add entry to mapping
        time_order_mapping[time_slot_id] = new_time_slot_id
        
        print("No relevant annotations for time slot", time_slot_id)

# Update time order
elan_file.set_time_order(new_time_order)

# Output the modified ELAN file
output_file = codecs.open(output_file_name, "w", "utf-8")
output_file.write(elan_file.to_xml())
output_file.close()
