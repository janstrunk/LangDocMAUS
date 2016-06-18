# encoding=utf-8

# Extracts the transcription from a Toolbox file
# and converts it into a BAS Partitur file
# for use with MAUS / webMAUS.
#
# Usage:
# python Toolbox2BASPartitur.py INPUTFILE OUTPUTFILE TRANSLITERATIONFILE --t TRANSCRIPTIONTIERNAME --r REFERENCETIERNAME
#
# Optional arguments are:
# --inputenc ...           Character encoding of the input file
# --outputenc ...          Character encoding of the output file
# --transenc ...           Character encoding of the transliteration table file
# --start ...              Number of the first record to be processed
# --end ...                Number of the last record to be processed
# --startid ...            Record id of the first record to be processed
# --endid ...              Record id of the last record to be processed
# --wave ...               Tries to automatically determine the attributes
#                          of a wave file and writes them into the header
#                          of the BAS Partitur file
# --samplerate             Sample rate in Hz
# --channels               Number of channels
# --bitdepth               Bit depth
#
# Jan Strunk (jan_strunk@eva.mpg.de)
# August 2012

# Codecs for handling character encodings
import codecs

# Use regular expressions
import re

# Nice command line argument parsing
import argparse

# Module to check the properties of wave files
import wave

# Module to check files and paths
import os.path

import sys

# Create an command-line argument parser
parser = argparse.ArgumentParser(description="Convert the transcription in a Toolbox file (or parts thereof) to the BAS Partitur format.")

# Add arguments with sensible defaults to parser
parser.add_argument("inputfilename", help="the name of the input Toolbox file")
parser.add_argument("outputfilename", help="the name of the output BAS Partitur file")
parser.add_argument("transliterationfilename", help="the name of the transliteration table file")
parser.add_argument("-t", "--t", required=True, help="the name of the transcription tier marker in the Toolbox file")
parser.add_argument("-r", "--r", required=True, help="the name of the record marker in the Toolbox file")
parser.add_argument("-inputenc", "--inputenc", required=False, default="utf-8", help="the input character encoding to be used (defaults to UTF-8)")
parser.add_argument("-outputenc", "--outputenc", required=False, default="utf-8", help="the output character encoding to be used (defaults to UTF-8)")
parser.add_argument("-transenc", "--transenc", required=False, default="utf-8", help="the character encoding to be used for the transliteration table (defaults to UTF-8)")
startgroup = parser.add_mutually_exclusive_group()
startgroup.add_argument("-start", "--start", required=False, default=1, type=int, help="the number of the first record to be processed")
startgroup.add_argument("-startid", "--startid", required=False, help="the record ID of the first record to be processed")
endgroup = parser.add_mutually_exclusive_group()
endgroup.add_argument("-end", "--end", required=False, type=int, help="the number of the last record to be processed")
endgroup.add_argument("-endid", "--endid", required=False, help="the record ID of the last record to be processed")
parser.add_argument("-wave", "--wave", required=False, help="the file name of the associated wave file")
parser.add_argument("-samplerate", "--samplerate", required=False, default=44100, type=int, help="the sample rate of the associated wave file in Hz")
parser.add_argument("-channels", "--channels", required=False, default=1, type=int, choices=[1,2], help="the number of channels of the associated wave file (1=mono or 2=stereo)")
parser.add_argument("-bitdepth", "--bitdepth", required=False, default=2, type=int, help="the bit depth of the associated wave file (in bytes)")
parser.add_argument("-debuglevel", "--debuglevel", required=False, default=1, type=int, choices=[0,1], help="the debug level to be used (0 --> no status messages, 1 --> print status messages)")
parser.add_argument("-starttimemarker", "--starttimemarker", required=False, help="the name of the Toolbox tier containing the start times of utterances, which will be used to constrain the automatic time alignment")
parser.add_argument("-endtimemarker", "--endtimemarker", required=False, help="the name of the Toolbox tier containing the end times of utterances, which will be used to constrain the automatic time alignment")

# Parse command-line arguments
args = vars(parser.parse_args())

# Process obligatory command-line arguments
input_file_name = args["inputfilename"]
output_file_name = args["outputfilename"]
transliteration_file_name = args["transliterationfilename"]
transcription_tier_name = args["t"]
reference_tier_name = args["r"]

# Process optional command-line arguments
input_encoding = args["inputenc"]
output_encoding = args["outputenc"]
transliteration_encoding = args["transenc"]

if "startid" in args:
    start_id = args["startid"]
    start_number = None
else:
    start_id = None
    if "start" in args:
        start_number = args["start"]
    else:
        start_number = None

if "endid" in args:
    end_id = args["endid"]
    end_number = None
else:
    end_id = None
    if "end" in args:
        end_number = args["end"]
    else:
        end_number = None

# Sanity check
if not start_number is None and not end_number is None:
    if start_number > end_number:
        print("The number of the first record to be processed is higher than number of the last record to be processed.")
        sys.exit()

sample_rate = args["samplerate"]
channels = args["channels"]
bit_depth = args["bitdepth"]
debug_level = args["debuglevel"]

# If a wave file was specified, test whether it exists
if "wave" in args and args["wave"] is not None:
    wave_file_name = args["wave"]

    if os.path.exists(wave_file_name) and os.path.isfile(wave_file_name):

        # Try to open it with wave module
        wave_file = wave.open(wave_file_name, "r")
        
        # Try to determine its properties
        channels = wave_file.getnchannels()
        sample_rate = wave_file.getframerate()
        bit_depth = wave_file.getsampwidth()
    
    else:
        
        print("Could not find wave file:", wave_file_name)
        sys.exit()

else:
    wave_file_name = None

if "starttimemarker" in args and args["starttimemarker"] is not None:
    if "endtimemarker" in args and args["endtimemarker"] is not None:
        start_time_marker = args["starttimemarker"]
        end_time_marker = args["endtimemarker"]
        constrain_alignment = True
    else:
        print("You have to specify both a tier for utterance start times and a tier for utterance end times in order to constrain the automatic time alignment.")
        sys.exit()
else:
    print("Starttimemarker not given")
    if "endtimemarker" in args and args["endtimemarker"] is not None:
        print("You have to specify both a tier for utterance start times and a tier for utterance end times in order to constrain the automatic time alignment.")
        sys.exit()
    else:
        constrain_alignment = False


# Function to convert time code hours:minutes:seconds to samples
# Arguments:
# 1. time code as string
# 2. sample rate
def timecode2samples(time_code, sample_rate):

    # Compile regular expressions for different time format
    hours_minutes_seconds_re = re.compile(r"^(\d+):(\d+):(\d+(\.\d+)?)$")
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

    return int(seconds * sample_rate)
    

# Function to read in a Toolbox file
# Arguments:
# 1. file name
# 2. name of the tier in which the transcription is stored
# 3. name of the tier which contains the utterance id
# 4. sample rate of the wave file
# 4. name of the tier containing the utterance start times (if they already exist)
# 5. name of the tier containing the utterance end times (if they already exist)
# 6. encoding (defaults to utf-8)
# Returns a list of utterances/sentences as tuples (recordid, utterance)
def readToolboxFile(file_name, transcription_tier_name, reference_tier_name, sample_rate, start_time_tier_name=None, end_time_tier_name=None, encoding="utf-8"):
    toolbox_file = codecs.open(file_name,"r",encoding)

    # Print status message
    if debug_level == 1:
        print("Reading input file", file_name)
    
    # Compile necessary regular expression
    is_transcription_tier = re.compile("^" + r"\\" + re.escape(transcription_tier_name) + r"\s+(.+)$")
    is_reference_tier = re.compile("^" + r"\\" + re.escape(reference_tier_name) + r"\s+(.+)$")
    
    # Also compile regular expressions for utterance start and end time tiers if given
    if start_time_tier_name is not None:
        is_start_time_tier = re.compile("^" + r"\\" + re.escape(start_time_tier_name) + r"\s+(.+)$")
        is_end_time_tier = re.compile("^" + r"\\" + re.escape(end_time_tier_name) + r"\s+(.+)$")
    
    # Make a new list
    utterances = []
    
    # Variable to store the current utterance id
    cur_utterance = ""
    
    # Variable to accumulate the transcription
    # of the current utterace (which can stretch
    # over more than one line)
    cur_utterance_text = ""
    
    # Variable to store start and end time of utterance in samples
    cur_start_sample = None
    cur_end_sample = None

    # Read toolbox file line by line
    for line in toolbox_file:
        # Remove superfluous whitespace
        line = line.strip()
        
        # Skip empty lines
        if line == "": continue
        
        # Test if line contains a reference marker
        reference_match = is_reference_tier.search(line)
        if reference_match:
            # Add transcription of previous utterance to list
            if cur_utterance != "" and cur_utterance_text != "":
                
                # Determine start and end time of current utterance if already specified
                if start_time_tier_name:
                    if cur_start_sample is None or cur_end_sample is None:
                        print("Could not determine utterance start and/or end time for utterance", cur_utterance)
                        sys.exit()
                else:
                    cur_start_sample = None
                    cur_end_sample = None
                
                utterances.append((cur_utterance, cur_utterance_text, cur_start_sample, cur_end_sample))
                cur_utterance_text = ""
                cur_start_sample = None
                cur_end_sample = None

            # Update current utterance id
            cur_utterance = reference_match.group(1)
            
            # Normalize white space
            cur_utterance = cur_utterance.strip()
            cur_utterance = re.sub(r"\s+", " ", cur_utterance)
            
            # Print status message
            if debug_level == 1:
                print("Processing utterance", cur_utterance)
                
            # Go to next line in the input file
            continue
        
        # Test if line contains a transcription tier
        transcription_match = is_transcription_tier.search(line)
        if transcription_match:
            transcription_text = transcription_match.group(1)
            
            # Normalize white space
            transcription_text = transcription_text.strip()
            transcription_text = re.sub(r"\s+", " ", transcription_text)
            
            # Add transcription text to text already accumulated
            if cur_utterance_text == "":
                cur_utterance_text = transcription_text
            else:
                cur_utterance_text = cur_utterance_text + " " + transcription_text
            
            transcription_text = ""

        # If utterance start and end times already exist
        if start_time_tier_name:
            
            # Test if line contains an utterance start time
            start_time_match = is_start_time_tier.search(line)
            if start_time_match:
                start_time_text = start_time_match.group(1)
                cur_start_sample = timecode2samples(start_time_text, sample_rate)

            # Test if line contains an utterance end time
            end_time_match = is_end_time_tier.search(line)
            if end_time_match:
                end_time_text = end_time_match.group(1)
                cur_end_sample = timecode2samples(end_time_text, sample_rate)
        
    # Fully process the last utterance
    if cur_utterance != "" and cur_utterance_text != "":
        
        # Determine start and end time of current utterance if already specified
        if start_time_tier_name:
            if cur_start_sample is None or cur_end_sample is None:
                print("Could not determine utterenace start and/or end time for utterance", cur_utterance)
                sys.exit()
        else:
            cur_start_sample = None
            cur_end_sample = None
                
        utterances.append((cur_utterance, cur_utterance_text, cur_start_sample, cur_end_sample))
        cur_utterance_text = ""
    
    # Close file
    toolbox_file.close()
    
    return utterances


# Function to print a BAS Partitur header
# Arguments:
# 1. filehandle of the file to print to
# 2. BAS Partitur attributes
#    (see http://www.bas.uni-muenchen.de/forschung/Bas/BasFormatsdeu.html#Partitur)
def printBASPartiturHeader(file_handle, lhd="Partitur 1.2", rep="unknown", snb=bit_depth, sam=sample_rate, sbf="01", ssb=bit_depth*8, nch=channels, spn="unknown", dbn=os.path.basename(input_file_name), src=os.path.basename(wave_file_name), spa="SAM-PA", beg=None, end=None):
    
    # print BAS Partitur header
    print("LHD:", lhd, file=file_handle)
    print("REP:", rep, file=file_handle)
    print("SNB:", str(snb), file=file_handle)
    print("SAM:", str(sam), file=file_handle)
    print("SBF:", sbf, file=file_handle)
    print("SSB:", str(ssb), file=file_handle)
    print("NCH:", str(nch), file=file_handle)
    print("SPN:", spn, file=file_handle)
    print("DBN:", dbn, file=file_handle)
    
    if not beg is None:
        print("BEG:", str(beg), file=file_handle)

    if not end is None:
        print("END:", str(end), file=file_handle)
    
    if not src is None:
        print("SRC:", src, file=file_handle)
    
    print("SPA:", spa, file=file_handle)

    # Print body label
    print("LBD:", file=file_handle)
    
    # Print status report
    if debug_level == 1:
        print("Printing BAS Partitur header to output file", output_file_name)

# Function to convert Toolbox transcription into BAS Partitur ORT tier
# Arguments:
# 1. A Toolbox text as read in by readToolboxFile
# returns a list of utterances as tuples (recordid, list(tuple(number, word)))
def convertToORT(toolbox_text):
    # Build up a new list of utterances
    ort_utterances = []

    # Print status message
    if debug_level == 1:
        print("Converting Toolbox text to ORT tier.")
    
    # Running number
    word_number = 0
    
    # Go through Toolbox text
    for unit in toolbox_text:
        record_id = unit[0]
        utterance = unit[1]
        
        # Possibly also contains utterance start and end times
        start_sample = unit[2]
        end_sample = unit[3]
        
        # Split utterance into words at whitespace
        words = utterance.strip().split()
        
        # List of words
        word_list = []
        
        # Iterate through words
        for word in words:
            # Append a tuple of running number and word to the list of words
            word_list.append((word_number, word))
            # Increase the running number
            word_number += 1
        
        # Append utterance, tuple of record id and word_list, to list of utterances
        ort_utterances.append((record_id, word_list, start_sample, end_sample))
    
    return ort_utterances

# Function to read in a transliteration table
# (Format:
#  Source_Symbol(s) --> Target_Symbol(s)
#  one entry per line)
# Arguments:
# 1. Name of the file
# 2. Character encoding to use (defaults to UTF-8)
# returns a list of transliteration pairs (tuples)
def readTransliterationTable(file_name, encoding="utf-8"):

    # Make a new transliteration table
    transliteration_table = []
    
    # Print status message
    if debug_level == 1:
        print("Reading in transliteration table from file", file_name)
    
    # Compile regular expression for deletion lines
    deletion_re = re.compile(r"^(\S+)\s+\-\-\s*$")
    
    # Open file
    table_file = codecs.open(file_name, "r", encoding)
    
    # Read in table
    for line in table_file:
        
        # Normalize whitespace
        line = line.rstrip("\r\n")
        # line = re.sub(r"\s+", " ", line)
        
        # Skip empty lines
        if line == "": continue
        
        # Skip comments, starting with #
        if re.search(r"^\#", line):
            continue        
        
        # Split line at arrow
        line_split = line.split(" --> ")
        
        if len(line_split) == 2:
            (source, destination) = line_split
        else:
            match = deletion_re.search(line)
            if match:
                source = match.group(1)
                destination = ""
            else:
                print("Line in transliteration table is not well-formed:", line)
                sys.exit()
        
        # Insert entry into transliteration dictionary
        transliteration_table.append((source, destination))
    
    # Print status message
    if debug_level == 1:
        print(len(transliteration_table), "transliteration pairs read in.")
    
    return transliteration_table

# Function to transliterate a single orthographic word to SAMPA
# Arguments:
# 1. An orthographic word
# 2. A transliteration table dictionary as produced by readTransliterationTable
# returns a transliteration of the word to SAMPA
def transliterate(word, transliteration_table):
    # SAMPA transcription
    sampa_word = word
    
    # Iterate through all rules
    for pair in transliteration_table:
        source = pair[0]
        destination = pair[1]
        
        # Status report
        # print("Replacing '" + source + "' with '" + destination + "'.")

        # Transliterate single grapheme
#        sampa_word = re.sub(source, destination, sampa_word)
        sampa_word = sampa_word.replace(source, destination)
        
        # Normalize white space
        sampa_word = re.sub(r"\s+", " ", sampa_word)
        sampa_word = sampa_word.strip()
    
    return sampa_word


# Function to transliterate orthographic words to SAMPA
# Arguments:
# 1. A list of ORT utterances as produced by convertToORT
# 2. A transliteration table dictionary as produced by readTransliterationTable
# returns a list of utterances as tuples (recordid, list(tuple(number, SAMPA-word)))
def transliterateORT(ort_utterances, transliteration_table):
    # Build up a new list of utterances
    sampa_utterances = []
    
    # Print status message
    if debug_level == 1:
        print("Converting ORT (orthographic) tier to KAN (canonical transcription) tier.")
    
    # Go through Toolbox text
    for utterance in ort_utterances:
        record_id = utterance[0]
        utterance = utterance[1]
        
        # New list of transliterated words
        sampa_utterance = []

        # Go through all words in the utterance        
        for word in utterance:
            word_id = word[0]
            word_ORT = word[1]
            
            # Transliterate ORT to SAMPA
            word_SAMPA = transliterate(word_ORT, transliteration_table)
            
            # If the transliteration produces an empty token,
            # leave out this token 
            if word_SAMPA.strip() == "":
                word_SAMPA = "<nib>"
                print("Transliteration led to empty word:")
                print("ORT:", word_ORT)
                print("KAN:", word_SAMPA)
            
            # Append newly transliterated word
            sampa_utterance.append((word_id, word_SAMPA))
        
        # Append SAMPA utterance to list of utterances
        sampa_utterances.append((record_id, sampa_utterance))
    
    # Print status message
    if debug_level == 1:
        print("Transliterated", len(sampa_utterances), "utterances from ORT to SAMPA.")
    
    return sampa_utterances


# Function to print the ORT tier
# Arguments:
# 1. the file handle
# 2. the list of ORT utterances as produced by convertToORT
def printORT(file_handle, ort_utterances):
    # Print status report
    if debug_level == 1:
        print("Printing ORT (orthography) tier.")
    
    # Go through list of utterances
    for ort_utterance in ort_utterances:
        utterance = ort_utterance[1]
        
        # Go through list of words
        for word in utterance:
            word_id = word[0]
            ort_word = word[1]
            
            # Print ORT tier line to file
            print("ORT:", word_id, ort_word, file=file_handle)


# Function to print the KAN (canonical transliteration) tier
# Arguments:
# 1. the file handle
# 2. the list of transliterated utterances as produced by transliterateORT
def printKAN(file_handle, kan_utterances):
    # Print status report
    if debug_level == 1:
        print("Printing KAN (canonical transcription) tier.")
    
    # Go through list of utterances
    for kan_utterance in kan_utterances:
        utterance = kan_utterance[1]
        
        # Go through list of words
        for word in utterance:
            word_id = word[0]
            kan_word = word[1]
            
            # Print KAN tier line to file
            print("KAN:", word_id, kan_word, file=file_handle)


# Function to print an additional tier with information about utterances
# Arguments:
# 1. the file handle
# 2. the list of transliterated utterances as produced by transliterateORT
def printUtteranceIDs(file_handle, ort_utterances):
    # Print status report
    if debug_level == 1:
        print("Printing additional utterance ID tier.")
    
    # Go through list of utterances
    for ort_utterance in ort_utterances:
        record_id = ort_utterance[0]
        utterance = ort_utterance[1]
        
        # Assemble list of words
        word_id_list = []
        
        # Go through list of words
        for word in utterance:
            word_id = word[0]
            word_id_list.append(str(word_id))
        
        # Concatenate list of words with commas
        # and output a symbolic association between words and record id
        print("RID:", ",".join(word_id_list), record_id, file=file_handle)


# Function to print an additional tier with utterance start and end times
# in order to constrain automatic time alignment
# Arguments:
# 1. the file handle
# 2. the list of utterances as produced by convertToORT
def printUtteranceTimes(file_handle, ort_utterances):
    
    # Print status report
    if debug_level == 1:
        print("Printing additional utterance start and end times tier.")
    
    # Remember end time of last utterance
    last_end_sample = 0
    
    # Go through list of utterances
    for ort_utterance in ort_utterances:
        record_id = ort_utterance[0]
        utterance = ort_utterance[1]
        start_sample = ort_utterance[2]
        end_sample = ort_utterance[3]
        
        # Only output a TRN tier if the begin and end times
        # for the current utterance have been found
        if start_sample is not None and end_sample is not None:
            
            # Sanity check
            if start_sample >= end_sample:
                
                print("Start time of utterance", record_id, "is greater or equal than end time.")
                sys.exit()
            
            if start_sample < last_end_sample:
                
                print("Warning: Overlapping utterance", record_id)
            
            duration = end_sample - start_sample

            # Remember end time of last utterance
            last_end_sample = end_sample
        
            # Assemble list of words
            word_id_list = []
        
            # Go through list of words
            for word in utterance:
                word_id = word[0]
                word_id_list.append(str(word_id))
        
            # Concatenate list of words with commas
            # and output the start and duration of the current utterance
            # in samples and a symbolic association between words and record id
            print("TRN:", str(start_sample), str(duration), ",".join(word_id_list), record_id, file=file_handle)
            
#            if (duration < 10000):
              
#                print("Very short TRN:", str(start_sample), str(duration), ",".join(word_id_list), record_id)


# Print status report
if debug_level == 1:
    print("Converting Toolbox file", input_file_name, "to", output_file_name)

# Read in Toolbox file
if constrain_alignment:
    toolbox_text = readToolboxFile(input_file_name, transcription_tier_name, reference_tier_name, sample_rate, start_time_marker, end_time_marker, input_encoding)
else:
    toolbox_text = readToolboxFile(input_file_name, transcription_tier_name, reference_tier_name, sample_rate, None, None, input_encoding)
    
# Read transliteration table
transliteration_table = readTransliterationTable(transliteration_file_name, transliteration_encoding)

# Create orthographic tier (ORT)
ort_tier = convertToORT(toolbox_text)

# Perform transliteration to KAN tier
kan_tier = transliterateORT(ort_tier, transliteration_table)

# Create output file
output_file = codecs.open(output_file_name, "w", output_encoding)

# Print BAS Partitur header
printBASPartiturHeader(output_file)

# Insert empty line
print(file=output_file)

# Print orthographic tier (ORT)
printORT(output_file, ort_tier)

# Insert empty line
print(file=output_file)

# Print canonical transcription tier (KAN)
printKAN(output_file, kan_tier)

# Insert empty line
print(file=output_file)

# Print additional information about utterances
printUtteranceIDs(output_file, ort_tier)

# Optionally also output a tier with known utterance start
# and end times in order to constraint the automatic alignment
if constrain_alignment:
    
    # Insert empty line
    print(file=output_file)

    # Print additional information about utterance start and end times
    printUtteranceTimes(output_file, ort_tier)

# Close output file
output_file.close()
