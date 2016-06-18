# encoding=utf-8

# Extracts the transcription from a BAS Partitur file with a MAU tier
# and converts it into Toolbox file with the tiers \ELANBegin
# and \ELANEnd containing utterance start and end times for import in ELAN.
# Optionally also adds tiers with the start and end times of words.
#
# Usage:
# python MAUS2Toolbox.py BASFILE ORIGINALBASFILE OUTPUTFILE
#
# Optional arguments are:
# --toolboxfile ...           Original Toolbox file to which the time information
#                             should be added (if none is given, a new Toolbox
#                             file is created)
# --toolboxtype ...           Toolbox database type to use when creating a new Toolbox file from scratch
#                             (defaults to "Text")
# --inputenc ...              Character encoding of the input file
# --origenc ...               Character encoding of the original BAS Partitur file
# --toolboxenc ...            Character encoding of the original Toolbox file
# --outputenc ...             Character encoding of the output file
# --wave ...                  Tries to automatically determine the attributes
#                             of a wave file in order to convert samples to seconds
# --samplerate ...            Sample rate in Hz
# --outputwordtimes           Output word start and end times into the Toolbox file
# --keeputterancetimes        Do not overwrite the original utterance start and end times
# --wordstarttier ...         Name of the tier to which word start times should be written
#                             (defaults to "WordsBegin")
# --wordendtier ...           Name of the tier to which word end times should be written
#                             (defaults to "WordsEnd")
# --utterancestarttier ...    Name of the tier to which utterance start times should be written
#                             (defaults to "ELANBegin")
# --utteranceendtier ...      Name of the tier to which utterance end times should be written
#                             (defaults to "ELANEnd")
# --outputwordtimesafter ...  Name of the tier after which the tiers for word start and end times should be added
# --reftier ...               Name of the reference tier (under which utterance start and end times
#                             will be added)
# --texttier ...              Name of the tier to write the words to when creating a new Toolbox
#                             file from scratch
#
# Jan Strunk (jan_strunk@eva.mpg.de)
# September 2012

# Codecs for handling character encodings
import codecs

# Use regular expressions
import re

# Nice command line argument parsing
import argparse

# Module to check the properties of wave files
import wave

# Modules to check files and paths
import os.path
import sys

# Module for working with Toolbox files

# Create an command-line argument parser
parser = argparse.ArgumentParser(description="Convert the transcription in a BAS Partitur file with a MAU tier to the Toolbox format.")

# Add arguments with sensible defaults to parser
parser.add_argument("inputfilename", help="the name of the input BAS Partitur file with MAU tier")
parser.add_argument("originalfilename", help="the name of the original BAS Partitur file")
parser.add_argument("outputfilename", help="the name of the output Toolbox file")
parser.add_argument("-toolboxfile", "--toolboxfile", required=False, default=None, help="the name of a Toolbox file to which the time information should be added (defaults to None)")
parser.add_argument("-toolboxtype", "--toolboxtype", required=False, default="Text", help="Toolbox database type to be used when creating a new Toolbox file from scratch (defaults to Text)")
parser.add_argument("-inputenc", "--inputenc", required=False, default="utf-8", help="the input character encoding to be used for the BAS Partitur file with MAU tier (defaults to UTF-8)")
parser.add_argument("-origenc", "--origenc", required=False, default="utf-8", help="the input character encoding to be used for the original BAS Partitur file (defaults to UTF-8)")
parser.add_argument("-toolboxenc", "--toolboxenc", required=False, default="utf-8", help="the character encoding to be used for the original Toolbox file (defaults to UTF-8)")
parser.add_argument("-outputenc", "--outputenc", required=False, default="utf-8", help="the output character encoding to be used (defaults to UTF-8)")
parser.add_argument("-wave", "--wave", required=False, help="the file name of the associated wave file")
parser.add_argument("-samplerate", "--samplerate", required=False, type=int, help="the sample rate of the associated wave file in Hz")
parser.add_argument("-debuglevel", "--debuglevel", required=False, default=1, type=int, choices=[0,1], help="the debug level to be used (0 --> no status messages, 1 --> print status messages)")
parser.add_argument("-outputwordtimes", "--outputwordtimes", required=False, action="store_true", help="output word start and end times into the Toolbox file (otherwise they are omitted)")
parser.add_argument("-keeputterancetimes", "--keeputterancetimes", required=False, action="store_true", help="keep the original utterance start and end times from the Toolbox file (otherwise they are overwritten)")
parser.add_argument("-wordstarttier", "--wordstarttier", required=False, default="WordBegin", help="the name of the tier to store the start times of words (defaults to WordBegin)")
parser.add_argument("-wordendtier", "--wordendtier", required=False, default="WordEnd", help="the name of the tier to store the end times of words (defaults to WordEnd)")
parser.add_argument("-reftier", "--reftier", required=False, default="ref", help="the name of the reference tier (under which utterance start and end times will be added) (defaults to ref)")
parser.add_argument("-texttier", "--texttier", required=False, default="t", help="the name of the tier to write the words to when creating a new Toolbox file from scratch (defaults to t)")
parser.add_argument("-utterancestarttier", "--utterancestarttier", required=False, default="ELANBegin", help="the name of the tier to store the start times of utterances (defaults to ELANBegin)")
parser.add_argument("-utteranceendtier", "--utteranceendtier", required=False, default="ELANEnd", help="the name of the tier to store the end times of utterances (defaults to ELANEnd)")

# Parse command-line arguments
args = vars(parser.parse_args())

# Process obligatory command-line arguments
input_file_name = args["inputfilename"]
original_file_name = args["originalfilename"]
output_file_name = args["outputfilename"]

# Process optional command-line arguments
original_toolbox_file_name = args["toolboxfile"]
toolbox_type = args["toolboxtype"]
input_encoding = args["inputenc"]
original_encoding = args["origenc"]
toolbox_encoding = args["toolboxenc"]
output_encoding = args["outputenc"]
sample_rate = args["samplerate"]
debug_level = args["debuglevel"]
word_start_tier_name = args["wordstarttier"]
word_end_tier_name = args["wordendtier"]
utterance_start_tier_name = args["utterancestarttier"]
utterance_end_tier_name = args["utteranceendtier"]
output_word_times = args["outputwordtimes"]
keep_utterance_times = args["keeputterancetimes"]
reference_tier_name = args["reftier"]
text_tier_name = args["texttier"]

# Compile a regular expression for Toolbox tier and database type names
valid_toolbox_name_re = re.compile(r"^\w+$")

# Make sure that the given reference and text tier names are valid Toolbox tier names
# Check whether the word start tier name is a valid tier name
if not valid_toolbox_name_re.search(reference_tier_name):
    print("The reference tier name", reference_tier_name, "is not a valid tier name.")
    print("Tier names can only contain ASCII letters, digits and the underscore _.")
    print("Tier names cannot contain whitespace.")
    sys.exit()

if not valid_toolbox_name_re.search(text_tier_name):
    print("The text tier name", reference_tier_name, "is not a valid tier name.")
    print("Tier names can only contain ASCII letters, digits and the underscore _.")
    print("Tier names cannot contain whitespace.")
    sys.exit()

# Print status report
if debug_level == 1:
    print("Converting BAS Partitur file", input_file_name, "to Toolbox file", output_file_name, "using the ORT, KAN, and RID tiers from", original_file_name + ".")
    if original_toolbox_file_name is not None:
        print("Adding the time information to the original Toolbox file", original_toolbox_file_name + ".")
    else:
        print("Creating a completely new Toolbox file.")
        print("Using the reference tier name", reference_tier_name)
        print("Using the text tier name", text_tier_name)

# Output word start and end times after the text tier if a new Toolbox file
# is created from scratch
if output_word_times is False:
    
    # Print status 
    if debug_level == 1:
        print("Omitting word start and end times.")
    
    if word_start_tier_name != "WordBegin":
        print("Ignoring word start tier name", word_start_tier_name, "because the option outputwordtimes has not been set.")
    
    if word_end_tier_name != "WordEnd":
        print("Ignoring word end tier name", word_end_tier_name, "because the option outputwordtimes has not been set.")

else:
    
    # Check whether the word start tier name is a valid tier name
    if not valid_toolbox_name_re.search(word_start_tier_name):
        print("The word start tier name", word_start_tier_name, "is not a valid tier name.")
        print("Tier names can only contain ASCII letters, digits and the underscore _.")
        print("Tier names cannot contain whitespace.")
        sys.exit()
    
    # Check whether the word end tier name is a valid tier name
    if not re.search(r"^\w+$", word_end_tier_name):
        print("The word end tier name", word_end_tier_name, "is not a valid tier name.")
        print("Tier names can only contain ASCII letters, digits and the underscore _.")
        print("Tier names cannot contain whitespace.")
        sys.exit()
    
    # Print status message
    if debug_level == 1:
        print("Also adding tiers for word start and end times to the output Toolbox file.")
        print("Using word start tier name", word_start_tier_name)
        print("Using word end tier name", word_end_tier_name)

if original_toolbox_file_name is not None:
    
    # If both an original Toolbox file and a Toolbox database type have been specified,
    # ignore the latter
    if toolbox_type:
        
        if debug_level == 1 and toolbox_type != "Text":

            print("Adding information to original Toolbox file", original_toolbox_file_name, " and therefore ignoring the supplied Toolbox database type", toolbox_type + ".")

else:
    
    # If no existing Toolbox file has been provided, make sure that a valid
    # Toolbox database type has been supplied
    if toolbox_type:
        
        if not re.search(r"^\w+$", toolbox_type):
            
            print(toolbox_type, "is not a valid Toolbox database type name.")
            print("Toolbox database type names can only contain ASCII letters, digits and the underscore _.")
            print("Toolbox database type names cannot contain whitespace.")
            sys.exit()
    
    else:
        
        print("No existing Toolbox file has been supplied.")
        print("Therefore you have to provide the name of the Toolbox database type for the newly created Toolbox file.")
        sys.exit()
    
    if keep_utterance_times is True:
        
        print("Cannot keep original utterance start and end times when creating a Toolbox file from scratch.")
        sys.exit()

# If a wave file was specified, test whether it exists
if "wave" in args and args["wave"] is not None:
    
    wave_file_name = args["wave"]

    if os.path.exists(wave_file_name) and os.path.isfile(wave_file_name):

        # Try to open it with wave module
        wave_file = wave.open(wave_file_name, "r")
        
        # Try to determine its properties
        sample_rate = wave_file.getframerate()

else:
    wave_file_name = None
    if sample_rate is None:
        print("You either have to provide the path to the wave file or to specify the sample rate manually.")
        sys.exit()


# Function to convert time code hours:minutes:seconds to seconds
# Arguments:
# 1. time code as string
def timecode2seconds(time_code):

    # Compile regular expressions for different time format
    hours_minutes_seconds_re = re.compile(r"^(\d+):(\d+):(\d+\.\d+)$")
    seconds_re = re.compile(r"^(0|(\d+)\.(\d+))$")
    
    # Test what kind of time code we are dealing with
    match = hours_minutes_seconds_re.search(time_code)
    if match:
        hours = match.group(1)
        minutes = match.group(2)
        seconds = match.group(3)
        
        # Convert complex time code to seconds
        try:
            seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)

        except:
            print("Could not convert time code", time_code, " to seconds.")
            sys.exit()
    
    elif seconds_re.search(time_code):
        
        # Convert simple time code to seconds
        try:
            seconds = float(time_code)

        except:
            print("Could not convert time code", time_code, " to seconds.")
            sys.exit()
    
    else:
        print("Could not match time code", time_code)
        sys.exit()

    return float(seconds)

# Function to read in the ORT tier from a BAS Partitur file
# Arguments:
# 1. file name
# 2. encoding (defaults to utf-8)
# Returns a list of words as tuples (word_id, word)
def readORTFromOriginalBASFile(file_name, encoding="utf-8"):
    bas_file = codecs.open(file_name,"r",encoding)
    
    # Print status message
    if debug_level == 1:
        print("Extracting ORT tier from original BAS Partitur file", file_name)
    
    # Make a new list of words
    words = []
    
    # Count line numbers for error reporting
    line_number = 0
    
    # Read the BAS Partitur file line by line
    for line in bas_file:
        
        # Increase line number
        line_number += 1

        # Remove superfluous whitespace
        line = line.strip()
        
        # Skip empty lines
        if line == "": continue
        
        # Test if the line contains information in the ORT tier
        if line.startswith("ORT:"):
            
            # Test whether the line can be divided into 3 elements:
            # tier marker, word_id and word
            elements = line.split()
            if len(elements) != 3:
                print("Found an ORT tier that does not contain 3 elements (tier marker, number, phoneme) in line:", line_number)
                sys.exit()
            
            # Unpack elements into separate variables    
            (tier_marker, word_id, word) = elements
                        
            # Append the current word into the list of words
            # (also include the line number)
            words.append((word_id, word))
    
    # Close the file
    bas_file.close()
    
    # Return the list of words
    return words


# Function to read in the KAN tier from a BAS Partitur file
# Arguments:
# 1. file name
# 2. encoding (defaults to utf-8)
# Returns a list of words as tuples (word_id, word)
def readKANFromOriginalBASFile(file_name, encoding="utf-8"):
    bas_file = codecs.open(file_name,"r",encoding)
    
    # Print status message
    if debug_level == 1:
        print("Extracting KAN tier from original BAS Partitur file", file_name)
    
    # Make a new list of words
    words = []
    
    # Count line numbers for error reporting
    line_number = 0
    
    # Read the BAS Partitur file line by line
    for line in bas_file:
        
        # Increase line number
        line_number += 1

        # Remove superfluous whitespace
        line = line.strip()
        
        # Skip empty lines
        if line == "": continue
        
        # Test if the line contains information in the ORT tier
        if line.startswith("KAN:"):
            
            # Test whether the line can be divided into 3 elements:
            # tier marker, word_id and word
            elements = line.split()
            if len(elements) < 3:
                print("Found a KAN tier that does not contain at least 3 elements (tier marker, number, phoneme) in line:", line_number)
                sys.exit()

            if len(elements) == 3:
            
                # Unpack elements into separate variables    
                (tier_marker, word_id, word) = elements
            
            else:
                
                # Unpack elements into separate variables    
                tier_marker = elements.pop(0)
                word_id = elements.pop(0)
                word = " ".join(elements)
                        
            # Append the current word into the list of words
            # (also include the line number)
            words.append((word_id, word))
    
    # Close the file
    bas_file.close()
    
    # Return the list of words
    return words


# Function to read in the MAU tier from a BAS Partitur file
# Arguments:
# 1. file name
# 2. encoding (defaults to utf-8)
# Returns a list of phonemes as tuples (phoneme_id, phoneme)
def readMAUFromBASFile(file_name, encoding="utf-8"):
    bas_file = codecs.open(file_name,"r",encoding)
    
    # Print status message
    if debug_level == 1:
        print("Extracting MAU tier from BAS Partitur file", file_name)
    
    # Make a new list of words
    phonemes = []
    
    # Count line numbers for error reporting
    line_number = 0
    
    # Read the BAS Partitur file line by line
    for line in bas_file:
        
        # Increase line number
        line_number += 1

        # Remove superfluous whitespace
        line = line.strip()
        
        # Skip empty lines
        if line == "": continue
        
        # Test if the line contains information in the ORT tier
        if line.startswith("MAU:"):
            
            # Test whether the line can be divided into 5 elements:
            # tier marker, start, duration, word_id, and phoneme
            elements = line.split()
            if len(elements) != 5:
                print("Found a MAU tier that does not contain 5 elements (tier marker, start time, duration, word id, phoneme) in line:", line_number)
                sys.exit()
            
            # Unpack elements into separate variables    
            (tier_marker, start, duration, word_id, phoneme) = elements
                        
            # Append the current word into the list of words
            # (also include the line number)
            phonemes.append((start, duration, word_id, phoneme))
    
    # Close the file
    bas_file.close()
    
    # Return the list of phonemes
    return phonemes


# Function to read in the RID tier from a BAS Partitur file
# Arguments:
# 1. file name
# 2. encoding (defaults to utf-8)
# Returns a list of utterances as lists of [utterance_id, list of word_ids]
def readRIDFromOriginalBASFile(file_name, encoding="utf-8"):
    bas_file = codecs.open(file_name,"r",encoding)
    
    # Print status message
    if debug_level == 1:
        print("Extracting RID tier from Original BAS Partitur file", file_name)

    # Make a new list of words
    utterances = []
    
    # Count line numbers for error reporting
    line_number = 0
    
    # Read the BAS Partitur file line by line
    for line in bas_file:
        
        # Increase line number
        line_number += 1

        # Remove superfluous whitespace
        line = line.strip()
        
        # Skip empty lines
        if line == "": continue
        
        # Test if the line contains information in the ORT tier
        if line.startswith("RID:"):
            
            # Test whether the line can be divided into 3 elements:
            # tier marker, start, duration, word_id, and phoneme
            elements = line.split()

            if len(elements) < 3:
                
                print("Found a RID tier that does not contain at least 3 elements (tier marker, word ids, utterance id) in line:", line_number)
                sys.exit()
            
            elif len(elements) == 3:
            
                # Unpack elements into separate variables    
                (tier_marker, word_ids, utterance_id) = elements
            
            else:
                
                tier_marker = elements[0]
                word_ids = elements[1]
                utterance_id = " ".join(elements[2:])
            
            # Split the word ids
            list_of_word_ids = word_ids.split(",")
                        
            # Append the current utterance into the list of utterances
            utterances.append([utterance_id, list_of_word_ids])
    
    # Close the file
    bas_file.close()
    
    # Return the list of utterances
    return utterances


# Function to combine the start and end times of phonemes into those for words
# Argument:
# 1. A list of phonemes as created by readMAUFromBASFile
# returns a dictionary from word ids to pairs of (start_time, end_time)
def combinePhonemesIntoWords(phonemes):

    # Print status report
    if debug_level == 1:
        print("Combining phoneme start and end times into word start and end times.")
    
    # Dictionary of word ids
    word_ids = {}
    
    # Go through list of phonemes
    for (start, duration, word_id, phoneme) in phonemes:
        
        # Ignore pauses, etc.
        if word_id == "-1":
            continue
        
        # Determine whether phonemes of the current word have already been processed
        if word_id in word_ids:
            
            # Old start and end time
            (old_start_time, old_end_time) = word_ids[word_id]
            
            # Calculate the start and end times of the current phoneme
            cur_start_time = int(start)
            cur_end_time = int(start) + int(duration)
            
            # Is the current phoneme's start time lower than the old word start time?
            if cur_start_time < old_start_time:
                new_start_time = cur_start_time
            else:
                new_start_time = old_start_time
                
            # Is the current phoneme's end time higher than the old word end time?
            if cur_end_time > old_end_time:
                new_end_time = cur_end_time
            else:
                new_end_time = old_end_time
                
            # Put updated start and end time into dictionary
            word_ids[word_id] = (new_start_time, new_end_time)                
            
        else:
            new_start_time = int(start)
            new_end_time = int(start) + int(duration)
            
            # Put initial start and end time into dictionary
            word_ids[word_id] = (new_start_time, new_end_time)
    
    # Return the dictionary of start and end times for words
    return word_ids


# Function to combine the start and end times of words into those for utterances
# Arguments:
# 1. A list of utterances as created by readRIDFromOriginalBASFile
# 2. A dictionary of word start and end times as created by combinePhonemesIntoWords
# returns a dictionary from utterance ids to pairs of (start_time, end_time)
def combineWordsIntoUtterances(utterances, words):

    # Print status report
    if debug_level == 1:
        print("Combining word start and end times into utterance start and end times.")
    
    # Dictionary of utterance ids
    utterance_ids = {}

    # Test
#    first_word_id = None
#    last_word_id = None
#    first_word_start_time = None
#    last_word_end_time = None
    
    # Go trough the list of utterances
    for utterance in utterances:
        utterance_id = utterance[0]
        list_of_word_ids = utterance[1]
        
#        print("Utterance id is", utterance_id)
#        print("List of word ids is", list_of_word_ids)
        
        # Look up the start time of the first and last words in the utterance
        first_word_id = list_of_word_ids[0]
        last_word_id = list_of_word_ids[-1]
        
        # Determine the start and end times of these words
        if first_word_id in words:
            (first_word_start_time, first_word_end_time) = words[first_word_id]
            
        else:           
            print("Could not find word id", first_word_id, "contained in utterance id", utterance_id)
#            sys.exit()

        if last_word_id in words:
            (last_word_start_time, last_word_end_time) = words[last_word_id]
            
        else:           
            print("Could not find word id", last_word_id, "contained in utterance id", utterance_id)
#            sys.exit()
        
        # Combine start time of first word and end time of last word into
        # utterance start and end times
        utterance_start_time = first_word_start_time
        utterance_end_time = last_word_end_time
        
        # Put the utterance start and end times into the utterance dictionary
        utterance_ids[utterance_id] = (utterance_start_time, utterance_end_time)

    # Return the dictionary of start and end times for utterances
    return utterance_ids


# Function to produce a dictionary from word ids to the orthographic forms of words
# Argument:
# 1. A list of words as produced by readORTFromOriginalBASFile
# returns a dictionary from word ids to ortographic word forms
def makeWordDictionary(list_of_words):
    
    # A dictionary of words
    word_dict = {}
    
    # Go through the list of words
    for (word_id, word) in list_of_words:
        
        # Put the word into the dictionary
        word_dict[word_id] = word
    
    # Return the dictionary
    return word_dict

# Function to produce a dictionary from utterance ids to the ids
# of the words contained in the utterance (stored as a list)
# Argument:
# 1. A list of utterances as produced by readRIDFromOriginalBASFile
# returns a dictionary from utterance ids to the word contained in that utterance
def makeUtteranceDictionary(list_of_utterances):
    
    # A dictionary of utterances
    utterance_dict = {}
    
    # Go through the list of utterances
    for (utterance_id, words) in list_of_utterances:
        
        # Put the list of word ids into the dictionary under the utterance id
        utterance_dict[utterance_id] = words
    
    # Return the dictionary
    return utterance_dict


# Function to read in an existing Toolbox file
# Arguments:
# 1. file name
# 2. encoding (defaults to utf-8)
# Returns a list of Toolbox lines as tuples (tier marker, line, line ending)
def readToolboxFile(file_name, encoding="utf-8"):

    # Print status message
    if debug_level == 1:
        print("Reading original Toolbox file", file_name)

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


# Function to annotate an original Toolbox file with additional time information
# Arguments:
# 1. The output file name
# 2. The output file encoding
# 3. The original Toolbox file as read in by readToolboxFile
# 4. The name of the reference tier
# 5. Whether to keep the original utterance start and end times or not (Boolean)
# 6. Whether to output word start and end times or not (Boolean)
# 7. The utterance start and end times (as a dictionary from utterance id to (start, end)
# 8. The Toolbox marker for utterance start times
# 9. The Toolbox marker for utterance end times
# 10. The word start and end times (as a dictionary from word id to (start, end)
# 11. The Toolbox marker for word start times
# 12. The Toolbox marker for word end times
# 13. A dictionary from utterance ids to word ids contained in them as produced by makeUtteranceDictionary
# 14. A dictionary from utterance ids to the original utterance start and end times
# 15. The sample rate to be used to convert samples to seconds
def annotateOriginalToolboxFile(output_file_name, output_encoding, original_toolbox_file, reference_tier_name, keep_utterance_times, output_word_times, utterance_times, utterance_start_marker, utterance_end_marker, word_times, word_start_marker, word_end_marker, utterance_dict, original_utterance_times_dict, sample_rate):
    
    # Compile a regular expression to extract the tier contents
    tier_contents_re = re.compile("^" + r"\\(\S+)\s+(.+)$")

    # Check that the reference marker actually occurs in the file
    reference_tier_encountered = False

    # Test
#    first_word_start_time = None
#    last_word_end_time = None

    for line in original_toolbox_file:
        
        # Unpack line contents
        (cur_toolbox_marker, cur_line, cur_line_ending) = line
        
        if cur_toolbox_marker == reference_tier_name:
            reference_tier_encountered = True
    
    if reference_tier_encountered is False:
        print("The supplied reference tier marker", reference_tier_name, "does not occur in the original Toolbox file.")
        sys.exit()

    # Count line numbers for error reporting
    line_number = 0
    
    # Remember whether utterance times were output
    utterance_times_output = True
    cur_utterance_id = None

    # Open the output file
    output_file = codecs.open(output_file_name, "w", output_encoding)
    
    # Go through all lines in the original Toolbox file
    for line in original_toolbox_file:
        
        # Increase line number
        line_number += 1
        
        # Unpack line contents
        (cur_toolbox_marker, cur_line, cur_line_ending) = line
        
        # Flags indicating whether utterance times have been output
        utterance_start_time_seconds = None
        utterance_end_time_seconds = None
                
        # Check whether we have found the reference tier
        if cur_toolbox_marker == reference_tier_name:
            
            # Only utterance start time or utterance end time were output
            # but not both
            if utterance_times_output == "start" or utterance_times_output == "end":
                
                utterance_times_output = False
            
            # Check whether utterance times were output for preceding utterance
            if utterance_times_output is False and cur_utterance_id is not None:
                
                print("Could not output any utterance times for utterance", cur_utterance_id)
#                sys.exit()
            
            # No utterance times output for current utterance yet
            utterance_times_output = False

            # Remember start time of first word and end time of last word
            # to perform sanity checks
            first_word_start_time = None
            last_word_end_time = None
            
            # Extract the contents of the reference tier
            match = tier_contents_re.search(cur_line)

            if match:

                cur_utterance_id = match.group(2).strip()

            else:

                print("Something is wrong. I cannot extract the reference from the reference tier in line " + str(line_number) +".")
                print(line)
                sys.exit()
            
            # Output the current reference tier line
            output_file.write(cur_line)
            
            # Try to find the utterance id in the dictionary with utterance
            # start and end times
            if cur_utterance_id in utterance_times:

                utterance_start_time = utterance_times[cur_utterance_id][0]
                utterance_end_time = utterance_times[cur_utterance_id][1]
                
                # Calculate start time in seconds
                utterance_start_time_seconds = round(utterance_start_time / sample_rate, 3)
    
                # Calculate end time in seconds
                utterance_end_time_seconds = round(utterance_end_time / sample_rate, 3)
                
                # If the original utterance are to be overwritten
                if keep_utterance_times is False:

                    # Output the current utterance start time
                    output_line = "\\" + utterance_start_marker + " " + "%.3f" % utterance_start_time_seconds + cur_line_ending
                    output_file.write(output_line)
            
                    # Output the current utterance end time
                    output_line = "\\" + utterance_end_marker + " " + "%.3f" % utterance_end_time_seconds + cur_line_ending
                    output_file.write(output_line)
                    
                    # Remember that utterance times were output for current utterance
                    utterance_times_output = True

                # If word times should be output, too
                if output_word_times:

                    # Could all word times be output
                    erroneous_unit = False
                                    
                    # Look up word ids
                    if cur_utterance_id in utterance_dict:
                        
                        cur_words = utterance_dict[cur_utterance_id]
                        
                        # Lists of word start and end times
                        word_start_times = []
                        word_end_times = []
                    
                        # Go through words
                        for word in cur_words:
                        
                            # Look up that word's start and end times
                            if word in word_times:
                                
                                word_start_time = word_times[word][0]
                                word_end_time = word_times[word][1]
                            
                                # Calculate start time in seconds
                                word_start_time_seconds = round(word_start_time / sample_rate, 3)
                            
                                # Calculate end time in seconds
                                word_end_time_seconds = round(word_end_time / sample_rate, 3)
                            
                                # Add them to the lists after converting them to strings
                                word_start_times.append("%.3f" % word_start_time_seconds)
                                word_end_times.append("%.3f" % word_end_time_seconds)
                                
                                # Remember word times for sanity checks
                                if first_word_start_time is None:
                                    
                                    first_word_start_time = word_start_time_seconds
                                
                                last_word_end_time = word_end_time_seconds
                        
                            else:
                                
                                print("Could not find word start or end time for word", word + ".")
                                erroneous_unit = True
                        
                        # All word times were output correctly?
                        if erroneous_unit is False:

                            # Output the start times of the words in the current utterance
                            output_line = "\\" + word_start_marker + " " + " ".join(word_start_times) + cur_line_ending
                            output_file.write(output_line)

                            # Output the end times of the words in the current utterance
                            output_line = "\\" + word_end_marker + " " + " ".join(word_end_times) + cur_line_ending
                            output_file.write(output_line)

                        # Output regular intervals
                        else:

                            if cur_utterance_id in original_utterance_times_dict:
                                
                                if "start" in original_utterance_times_dict[cur_utterance_id] and "end" in original_utterance_times_dict[cur_utterance_id]:

                                    original_utterance_start_time_seconds = original_utterance_times_dict[cur_utterance_id]["start"]
                                    original_utterance_end_time_seconds = original_utterance_times_dict[cur_utterance_id]["end"]
                                
                                else:
                                    
                                    print("Could not determine original utterance start and end times for erroneous utterance", cur_utterance_id)
                                    sys.exit()
                                                                        
                            else:
                                    
                                print("Could not determine original utterance start and end times for erroneous utterance", cur_utterance_id)
                                sys.exit()
                                

                            number_of_words = len(cur_words)
                            utterance_length = original_utterance_end_time_seconds - original_utterance_start_time_seconds
                            word_length = utterance_length/number_of_words

                            word_start_times = []
                            word_end_times = []
                            
                            for index in range(number_of_words):
                                
                                word_start_time_seconds = original_utterance_start_time_seconds + index * word_length + 0.010
                                word_end_time_seconds = original_utterance_start_time_seconds + (index + 1) * word_length - 0.010

                                # Add them to the lists after converting them to strings
                                word_start_times.append("%.3f" % word_start_time_seconds)
                                word_end_times.append("%.3f" % word_end_time_seconds)
                            
                            # Output the start times of the words in the current utterance
                            output_line = "\\" + word_start_marker + " " + " ".join(word_start_times) + cur_line_ending
                            output_file.write(output_line)

                            # Output the end times of the words in the current utterance
                            output_line = "\\" + word_end_marker + " " + " ".join(word_end_times) + cur_line_ending
                            output_file.write(output_line)
                            
                            print("Outputting regular intervals for utterance", cur_utterance_id)
                        
                        if (keep_utterance_times is False) and (utterance_start_time_seconds is not None) and (utterance_end_time_seconds is not None):
                        
                            if utterance_start_time_seconds > first_word_start_time:
                            
                                print("Start time of first word in the utterance is before start time of the utterance.")
                                print("Start time of utterance:", utterance_start_time_seconds)
                                print("Start time of first word:", first_word_start_time)
                                sys.exit()

                            if utterance_end_time_seconds < last_word_end_time:
                            
                                print("End time of last word in the utterance is after end time of the utterance.")
                                print("End time of utterance:", utterance_end_time_seconds)
                                print("End time of last word:", last_word_end_time)
                                sys.exit()

                    else:
                        
                        print("No word times output for empty utterance", cur_utterance_id)

            else:
 
                # Utterance contains no words
                if cur_utterance_id not in utterance_dict:
                    
                    utterance_start_time_seconds = None
                    utterance_end_time_seconds = None
                    
                    # Warning
                    print("Warning: Could not determine utterance start and end times for empty utterance", cur_utterance_id)
                    print("Will keep original start and end times if present.")
                
                else:
                    
                    print("Could not determine utterance start and end times for utterance", cur_utterance_id)
                    sys.exit()

        # Toolbox line except for the reference line encountered
        else:
            
            # Normally ignore the original utterance start and end markers
            # unless the current utterance is empty
            if (cur_toolbox_marker == utterance_start_marker) or (cur_toolbox_marker == utterance_end_marker):
                
                # Current utterance seems to be empty
                # Therefore output original utterance start or end
                # marker anyway
                if keep_utterance_times is True or utterance_times_output is not True:
                    
                    output_file.write(cur_line)
                    
                    # Check that word times are within utterance times
                    if cur_toolbox_marker == utterance_start_marker:
                        
                        cur_line_contents = cur_line.strip().split()[-1]
                        
                        try:
                            
                            utterance_start_time_seconds = timecode2seconds(cur_line_contents)
                        
                        except:
                            
                            print("Could not determine utterance start time from existing utterance time tier.")
                            print("Current utterance", cur_utterance_id)
                            print(cur_line)
                            sys.exit()
                        
                        if first_word_start_time is not None:
                            
                            if utterance_start_time_seconds > first_word_start_time:
                            
                                print("Start time of first word in the utterance is before start time of the utterance.")
                                print("Start time of utterance:", utterance_start_time_seconds)
                                print("Start time of first word:", first_word_start_time)
                                sys.exit()
                        
                        # Remember that utterance times were output for current utterance
                        if utterance_times_output == "end":
                            
                            utterance_times_output = True
                        
                        else:
                            
                            utterance_times_output = "start"

                    if cur_toolbox_marker == utterance_end_marker:

                        cur_line_contents = cur_line.strip().split()[-1]
                        
                        try:
                            
                            utterance_end_time_seconds = timecode2seconds(cur_line_contents)
                        
                        except:
                            
                            print("Could not determine utterance end time from existing utterance time tier.")
                            print("Current utterance", cur_utterance_id)
                            print(cur_line)
                            sys.exit()
                        
                        if last_word_end_time is not None:
                            
                            if utterance_end_time_seconds < last_word_end_time:
                            
                                print("End time of last word in the utterance is after end time of the utterance.")
                                print("End time of utterance:", utterance_end_time_seconds)
                                print("End time of last word:", last_word_end_time)
                                sys.exit()

                        # Remember that utterance times were output for current utterance
                        if utterance_times_output == "start":
                            
                            utterance_times_output = True
                        
                        else:
                            
                            utterance_times_output = "end"
            
            # Output any other lines unchanged
            else:
                
                output_file.write(cur_line)
    
    # Close the output file
    output_file.close()    
    

# Function to write a new Toolbox file from scratch
# Arguments:
# 1. The output file name
# 2. The output file encoding
# 3. The name of the reference tier
# 4. The name of the text tier
# 5. The name of the Toolbox database type
# 6. Whether to output word start and end times or not (Boolean)
# 7. The utterances from the BAS Partitur file as read in by readRIDFromOriginalBASFile
# 8. The utterance start and end times (as a dictionary from utterance id to (start, end)
# 9. The Toolbox marker for utterance start times
# 10. The Toolbox marker for utterance end times
# 11. The word start and end times (as a dictionary from word id to (start, end)
# 12. The Toolbox marker for word start times
# 13. The Toolbox marker for word end times
# 14. A dictionary from word ids to orthographic word forms
# 15. The sample rate to be used to convert samples to seconds
def writeNewToolboxFile(output_file_name, output_encoding, reference_tier_name, text_tier_name, toolbox_type, output_word_times, utterances, utterance_times, utterance_start_marker, utterance_end_marker, word_times, word_start_marker, word_end_marker, word_dict, sample_rate):

    # Open the output file
    output_file = codecs.open(output_file_name, "w", output_encoding)
    
    # Use Windows line endings \r\n throughout because Toolbox
    # is a Windows program
    
    # Write the Toolbox header
    # TODO: Look up what the number in the Toolbox header means!
    output_line = "\\_sh v3.0  400  " + toolbox_type + "\r\n"
    output_file.write(output_line)
    
    # Output empty line
    output_file.write("\r\n")
    
    # Go through all utterances
    for utterance in utterances:
        
        # Unpack values
        (utterance_id, words) = utterance
        
        # Output the reference tier with the utterance ID
        output_line = "\\" + reference_tier_name + " " + utterance_id + "\r\n"
        output_file.write(output_line)
        
        # Output the utterance start and end time
        if utterance_id in utterance_times:
            utterance_start_time = utterance_times[utterance_id][0]
            utterance_end_time = utterance_times[utterance_id][1]
            
            # Calculate start time in seconds
            utterance_start_time_seconds = round(utterance_start_time / sample_rate, 3)
            
            # Calculate end time in seconds
            utterance_end_time_seconds = round(utterance_end_time / sample_rate, 3)

            # Output the current utterance start time
            output_line = "\\" + utterance_start_marker + " " + "%.3f" % utterance_start_time_seconds + "\r\n"
            output_file.write(output_line)
            
            # Output the current utterance end time
            output_line = "\\" + utterance_end_marker + " " + "%.3f" % utterance_end_time_seconds + "\r\n"
            output_file.write(output_line)

        else:

            print("Could not determine utterance start and end times for utterance", utterance_id)
            sys.exit()
        
        # Build information about the words in the utterance
        word_forms = []

        for word in words:
            
            # Look up the word form
            if word in word_dict:
                word_form = word_dict[word]
                word_forms.append(word_form.strip())
            
            else:
                print("Could not determine orthographic word form for word", word + ".")
                sys.exit()

        # Build text tier line
        text_line = "\\" + text_tier_name + " " + " ".join(word_forms) + "\r\n"
        
        # Output the text tier directly if no word start and end times
        # are output
        if output_word_times is False:
            
            # Output empty line
            output_file.write("\r\n")
            
            # Output text tier
            output_file.write(text_line)
        
        # Should word start and end times also be output?
        else:

            word_start_times = []
            word_end_times = []
            
            for word in words:
                
                # Look up the start and end times
                if word in word_times:
                    
                    word_start_time = word_times[word][0]
                    word_end_time = word_times[word][1]
                
                    # Calculate start time in seconds
                    word_start_time_seconds = round(word_start_time / sample_rate, 3)
                
                    # Calculate end time in seconds
                    word_end_time_seconds = round(word_end_time / sample_rate, 3)
                
                    # Add them to the lists after converting them to strings
                    word_start_times.append("%.3f" % word_start_time_seconds)
                    word_end_times.append("%.3f" % word_end_time_seconds)

                else:

                    print("Could not find word start or end time for word", word + ".")
                    sys.exit()
            
            # Output tiers for word start and end times
            output_line = "\\" + word_start_marker + " " + " ".join(word_start_times) + "\r\n"
            output_file.write(output_line)
            output_line = "\\" + word_end_marker + " " + " ".join(word_end_times) + "\r\n"
            output_file.write(output_line)
                
            # Output empty line
            output_file.write("\r\n")
                
            # Output text tier
            output_file.write(text_line)

        # Output empty lines
        output_file.write("\r\n")
        output_file.write("\r\n")
    
    # Close the output file
    output_file.close()

def readUtteranceTimesFromOriginalToolboxFile(toolbox_file, reference_tier_name, utterance_start_tier_name, utterance_end_tier_name):
    
    cur_utterance_id = None
    
    original_utterance_times = dict()
    
    for line in toolbox_file:
        
        # Unpack line contents
        (cur_toolbox_marker, cur_line, cur_line_ending) = line
        
        # Reference tier?
        if cur_toolbox_marker == reference_tier_name:
            
            cur_utterance_id = None
            
            # Remember current utterance id
            cur_utterance_id = cur_line.strip()
            
            match = re.search(r"\s+(.+)$", cur_utterance_id)
            if match:
                
                cur_utterance_id = match.group(1)                
        
        # Extract utterance start time
        if cur_toolbox_marker == utterance_start_tier_name:
                        
            cur_utterance_start_time = cur_line.strip().split()[-1]
            cur_utterance_start_time_seconds = timecode2seconds(cur_utterance_start_time)
            
            if cur_utterance_id is not None:
                
                if cur_utterance_id not in original_utterance_times:
                    
                    original_utterance_times[cur_utterance_id] = {}
                
                original_utterance_times[cur_utterance_id]["start"] = cur_utterance_start_time_seconds
                
            cur_utterance_start_time = None
            cur_utterance_start_time_seconds = None

        # Extract utterance end time
        if cur_toolbox_marker == utterance_end_tier_name:
            
            cur_utterance_end_time = cur_line.strip().split()[-1]
            cur_utterance_end_time_seconds = timecode2seconds(cur_utterance_end_time)

            if cur_utterance_id is not None:

                if cur_utterance_id not in original_utterance_times:
                    
                    original_utterance_times[cur_utterance_id] = {}
                
                original_utterance_times[cur_utterance_id]["end"] = cur_utterance_end_time_seconds

            cur_utterance_end_time = None
            cur_utterance_end_time_seconds = None
        
    return original_utterance_times

# Read in the ORT tier from the original BAS Partitur file
ort_tier = readORTFromOriginalBASFile(original_file_name, original_encoding)

# Read in the KAN tier from the original BAS Partitur file
kan_tier = readKANFromOriginalBASFile(original_file_name, original_encoding)

# Read in the RID tier from the original BAS Partitur file
rid_tier = readRIDFromOriginalBASFile(original_file_name, original_encoding)

# Read in the MAU tier from the BAS Partitur file
mau_tier = readMAUFromBASFile(input_file_name, input_encoding)

# Combine phoneme start and end times into word start and end times
word_times = combinePhonemesIntoWords(mau_tier)

# Combine word start and end times into utterance start and end times
utterance_times = combineWordsIntoUtterances(rid_tier, word_times)

# Make a dictionary from word ids to word forms
word_dict = makeWordDictionary(ort_tier)

# Make a dictionary from utterance ids to the words contained in the utterances
utterance_dict = makeUtteranceDictionary(rid_tier)

# Print status message
if debug_level == 1:
    print("Writing Toolbox file.")

# Add time annotation to an original Toolbox file
if original_toolbox_file_name:
    original_toolbox_file = readToolboxFile(original_toolbox_file_name, toolbox_encoding)
    original_utterance_times_dict = readUtteranceTimesFromOriginalToolboxFile(original_toolbox_file, reference_tier_name, utterance_start_tier_name, utterance_end_tier_name)
    annotateOriginalToolboxFile(output_file_name, output_encoding, original_toolbox_file, reference_tier_name, keep_utterance_times, output_word_times, utterance_times, utterance_start_tier_name, utterance_end_tier_name, word_times, word_start_tier_name, word_end_tier_name, utterance_dict, original_utterance_times_dict, sample_rate)

# Write a new Toolbox file from scratch
else:
    writeNewToolboxFile(output_file_name, output_encoding, reference_tier_name, text_tier_name, toolbox_type, output_word_times, rid_tier, utterance_times, utterance_start_tier_name, utterance_end_tier_name, word_times, word_start_tier_name, word_end_tier_name, word_dict, sample_rate)

if debug_level == 1:
    print("Done.")
