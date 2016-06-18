# encoding=utf-8

# Extracts the transcription from a BAS Partitur file with a MAU tier
# and converts it into a Praat TextGrid file for use with Praat or ELAN.
#
# Usage:
# python MAUS2TextGrid.py BASFILE ORIGINALBASFILE OUTPUTFILE
#
# Optional arguments are:
# --inputenc ...           Character encoding of the input file
# --origenc ...            Character encoding of the original BAS Partitur file
# --outputenc ...          Character encoding of the output file
# --wave ...               Tries to automatically determine the attributes
#                          of a wave file in order to convert samples to seconds
# --samplerate             Sample rate in Hz
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

# Module to check files and paths
import os.path

import sys

# Create an command-line argument parser
parser = argparse.ArgumentParser(description="Convert the transcription in a BAS Partitur file with a MAU tier to the Praat TextGrid format.")

# Add arguments with sensible defaults to parser
parser.add_argument("inputfilename", help="the name of the input BAS Partitur file with MAU tier")
parser.add_argument("originalfilename", help="the name of the original BAS Partitur file")
parser.add_argument("outputfilename", help="the name of the output Praat TextGrid file")
parser.add_argument("-inputenc", "--inputenc", required=False, default="utf-8", help="the input character encoding to be used for the BAS Partitur file with MAU tier (defaults to UTF-8)")
parser.add_argument("-origenc", "--origenc", required=False, default="utf-8", help="the input character encoding to be used for the original BAS Partitur file (defaults to UTF-8)")
parser.add_argument("-outputenc", "--outputenc", required=False, default="utf-8", help="the output character encoding to be used (defaults to UTF-8)")
parser.add_argument("-wave", "--wave", required=False, help="the file name of the associated wave file")
parser.add_argument("-samplerate", "--samplerate", required=False, type=int, help="the sample rate of the associated wave file in Hz")
parser.add_argument("-debuglevel", "--debuglevel", required=False, default=1, type=int, choices=[0,1], help="the debug level to be used (0 --> no status messages, 1 --> print status messages)")

# Parse command-line arguments
args = vars(parser.parse_args())

# Process obligatory command-line arguments
input_file_name = args["inputfilename"]
original_file_name = args["originalfilename"]
output_file_name = args["outputfilename"]

# Process optional command-line arguments
input_encoding = args["inputenc"]
original_encoding = args["origenc"]
output_encoding = args["outputenc"]

sample_rate = args["samplerate"]
debug_level = args["debuglevel"]

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
            sys.exit()

        if last_word_id in words:
            (last_word_start_time, last_word_end_time) = words[last_word_id]
            
        else:           
            print("Could not find word id", last_word_id, "contained in utterance id", utterance_id)
            sys.exit()
        
        # Combine start time of first word and end time of last word into
        # utterance start and end times
        utterance_start_time = first_word_start_time
        utterance_end_time = last_word_end_time
        
        # Put the utterance start and end times into the utterance dictionary
        utterance_ids[utterance_id] = (utterance_start_time, utterance_end_time)

    # Return the dictionary of start and end times for utterances
    return utterance_ids


# Function to determine the minimal start time for words or utterances
# Argument:
# 1. A dictionary of ids with values of (start time, end time)
# returns the minimal start time
def getMinimalStartTime(id_dict):
    
    # Current minimal start time
    min_start_time = -1
    
    # Go through all entries in the dictionary
    for entry in id_dict:
        
        cur_start_time = id_dict[entry][0]
        
        # If no start time has been looked at yet
        if min_start_time == -1:
            min_start_time = cur_start_time
        
        else:
            
            # Is the current start time lower than the lowest value seen yet
            if cur_start_time < min_start_time:
                
                # Then take it as the new minimal start time
                min_start_time = cur_start_time
    
    # Return the minimal start time found
    return min_start_time


# Function to determine the maximal end time for words or utterances
# Argument:
# 1. A dictionary of ids with values of (start time, end time)
# returns the maximal end time
def getMaximalEndTime(id_dict):
    
    # Current maximal end time
    max_end_time = -1
    
    # Go through all entries in the dictionary
    for entry in id_dict:
        
        cur_end_time = id_dict[entry][1]
        
        # If no end time has been looked at yet
        if max_end_time == -1:
            max_end_time = cur_end_time
        
        else:
            
            # Is the current end time higher than the highest value seen yet
            if cur_end_time > max_end_time:
                
                # Then take it as the new maximal end time
                max_end_time = cur_end_time
    
    # Return the maximal end time found
    return max_end_time


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


# Function to print a Praat TextGrid header
# Arguments:
# 1. Filehandle of the file to print to
# 2. The number of tiers to be printed
# 3. The start time (usually 0)
# 4. The end time
# 5. The sample rate (in order to convert MAU times into seconds)
def printPraatTextGridHeader(file_handle, num_tiers, start_time, end_time, sample_rate=sample_rate):
    
    # Print the TextGrid header
    print("File type = \"ooTextFile\"", file=file_handle)
    print("Object class = \"TextGrid\"", file=file_handle)
    
    # Print empty line
    print(file=file_handle)
    
    # Calculate start time in seconds
    start_time_seconds = round(start_time / sample_rate, 3)
    
    # Calculate end time in seconds
    end_time_seconds = round(end_time / sample_rate, 3)
    
    print("xmin =", "%.3f" % start_time_seconds, file=file_handle)
    print("xmax =", "%.3f" % end_time_seconds, file=file_handle)
    print("tiers? <exists>", file=file_handle)
    print("size =", str(num_tiers), file=file_handle)
    
    # Print first line of tiers list
    print("item []:", file=file_handle)    
    
    # Print status report
    if debug_level == 1:
        print("Printing Praat TextGrid header to output file", output_file_name)


# Function to print the UTT(erance) tier
# Arguments:
# 1. The file handle
# 2. The list of UTTERANCES words as produced by readRIDFromOriginalBASFile
# 3. A dictionary from utterance ids to start and end times
# 4. A dictionary from word ids to orthographic word forms
# 5. The number of the tier in the TextGrid file
# 6. The start time (usually 0)
# 7. The end time
# 8. The sample rate (in order to convert MAU times into seconds)
def printUTT(file_handle, utterance_list, utterance_times, word_dict, tier_number, start_time, end_time, sample_rate = sample_rate):
    
    # Print status report
    if debug_level == 1:
        print("Printing UTT (utterances) tier.")

    # Output header for current tier
    print("\titem [" + str(tier_number) + "]:", file=file_handle)
    print("\t\tclass = \"IntervalTier\"", file=file_handle)
    print("\t\tname = \"UTT\"", file=file_handle)
        
    # Calculate start time in seconds
    start_time_seconds = round(start_time / sample_rate, 3)
    
    # Calculate end time in seconds
    end_time_seconds = round(end_time / sample_rate, 3)
    
    print("\t\txmin =", "%.3f" % start_time_seconds, file=file_handle)
    print("\t\txmax =", "%.3f" % end_time_seconds, file=file_handle)
    
    # Determine the number of utterances
    number_of_utterances = len(utterance_list)
    
    print("\t\tintervals: size =", str(number_of_utterances), file=file_handle)
    
    # Output the individual intervals
    interval_number = 0
    
    # Go through the list of utterances
    for utterance in utterance_list:
        
        # Increase interval number
        interval_number += 1

        utterance_id = utterance[0]
        word_ids = utterance[1]
        
        # Look up the utterance start and end times
        if utterance_id in utterance_times:
            
            utterance_start_time = utterance_times[utterance_id][0]
            utterance_end_time = utterance_times[utterance_id][1]
            
            # Calculate start time in seconds
            utterance_start_time_seconds = round(utterance_start_time / sample_rate, 3)
    
            # Calculate end time in seconds
            utterance_end_time_seconds = round(utterance_end_time / sample_rate, 3)
            
        else:
            print("Could not determine utterance start and end times for utterance", utterance_id)
            sys.exit()
        
        # Look up the words in the utterance
        words = []
        for word_id in word_ids:
            
            # Look up the word_id in the dictionary
            if word_id in word_dict:
                words.append(word_dict[word_id])
            
            else:
                print("Could not found orthographic form of word id", word_id)
                sys.exit()
        
        # Combine words into utterance text
        utterance_text = " ".join(words)
        
        # Output the interval for the current utterance
        print("\t\tintervals [" + str(interval_number) + "]:", file=file_handle)
        print("\t\t\txmin =", "%.3f" % utterance_start_time_seconds, file=file_handle)
        print("\t\t\txmax =", "%.3f" % utterance_end_time_seconds, file=file_handle)
        print("\t\t\ttext =", utterance_text, file=file_handle)


# Function to print the ORT(hography) tier
# Arguments:
# 1. The file handle
# 2. The list of ORT words as produced by readORTFromOriginalBASFile
# 3. A dictionary from word ids to start and end times
# 4. The number of the tier in the TextGrid file
# 5. The start time (usually 0)
# 6. The end time
# 7. The sample rate (in order to convert MAU times into seconds)
def printORT(file_handle, ort_list, word_times, tier_number, start_time, end_time, sample_rate = sample_rate):
    
    # Print status report
    if debug_level == 1:
        print("Printing ORT (orthography) tier.")

    # Output header for current tier
    print("\titem [" + str(tier_number) + "]:", file=file_handle)
    print("\t\tclass = \"IntervalTier\"", file=file_handle)
    print("\t\tname = \"ORT\"", file=file_handle)

    # Calculate start time in seconds
    start_time_seconds = round(start_time / sample_rate, 3)
    
    # Calculate end time in seconds
    end_time_seconds = round(end_time / sample_rate, 3)
    
    print("\t\txmin =", "%.3f" % start_time_seconds, file=file_handle)
    print("\t\txmax =", "%.3f" % end_time_seconds, file=file_handle)
    
    # Determine the number of words
    number_of_words = len(ort_list)
    
    print("\t\tintervals: size =", str(number_of_words), file=file_handle)
    
    # Output the individual intervals
    interval_number = 0
    
    # Go through the list of words
    for word in ort_list:
        
        # Increase interval number
        interval_number += 1

        word_id = word[0]
        word_ort = word[1]
        
        # Look up the word start and end times
        if word_id in word_times:
            
            word_start_time = word_times[word_id][0]
            word_end_time = word_times[word_id][1]
            
            # Calculate start time in seconds
            word_start_time_seconds = round(word_start_time / sample_rate, 3)
    
            # Calculate end time in seconds
            word_end_time_seconds = round(word_end_time / sample_rate, 3)
            
        else:
            print("Could not determine word start and end times for word", word_id)
            sys.exit()
                
        # Output the interval for the current word
        print("\t\tintervals [" + str(interval_number) + "]:", file=file_handle)
        print("\t\t\txmin =", "%.3f" % word_start_time_seconds, file=file_handle)
        print("\t\t\txmax =", "%.3f" % word_end_time_seconds, file=file_handle)
        print("\t\t\ttext =", word_ort, file=file_handle)


# Function to print the KAN (canonical transcription) tier
# Arguments:
# 1. The file handle
# 2. The list of KAN words as produced by readKANFromOriginalBASFile
# 3. A dictionary from word ids to start and end times
# 4. The number of the tier in the TextGrid file
# 5. The start time (usually 0)
# 6. The end time
# 7. The sample rate (in order to convert MAU times into seconds)
def printKAN(file_handle, kan_list, word_times, tier_number, start_time, end_time, sample_rate = sample_rate):
    
    # Print status report
    if debug_level == 1:
        print("Printing KAN (canonical transcription) tier.")

    # Output header for current tier
    print("\titem [" + str(tier_number) + "]:", file=file_handle)
    print("\t\tclass = \"IntervalTier\"", file=file_handle)
    print("\t\tname = \"KAN\"", file=file_handle)

    # Calculate start time in seconds
    start_time_seconds = round(start_time / sample_rate, 3)
    
    # Calculate end time in seconds
    end_time_seconds = round(end_time / sample_rate, 3)
    
    print("\t\txmin =", "%.3f" % start_time_seconds, file=file_handle)
    print("\t\txmax =", "%.3f" % end_time_seconds, file=file_handle)
    
    # Determine the number of words
    number_of_words = len(kan_list)
    
    print("\t\tintervals: size =", str(number_of_words), file=file_handle)
    
    # Output the individual intervals
    interval_number = 0
    
    # Go through the list of words
    for word in kan_list:
        
        # Increase interval number
        interval_number += 1

        word_id = word[0]
        word_kan = word[1]
        
        # Look up the word start and end times
        if word_id in word_times:
            
            word_start_time = word_times[word_id][0]
            word_end_time = word_times[word_id][1]
            
            # Calculate start time in seconds
            word_start_time_seconds = round(word_start_time / sample_rate, 3)
    
            # Calculate end time in seconds
            word_end_time_seconds = round(word_end_time / sample_rate, 3)
            
        else:
            print("Could not determine word start and end times for word", word_id)
            sys.exit()
                
        # Output the interval for the current word
        print("\t\tintervals [" + str(interval_number) + "]:", file=file_handle)
        print("\t\t\txmin =", "%.3f" % word_start_time_seconds, file=file_handle)
        print("\t\t\txmax =", "%.3f" % word_end_time_seconds, file=file_handle)
        print("\t\t\ttext =", word_kan, file=file_handle)


# Function to print the MAU (time-aligned phoneme) tier
# Arguments:
# 1. The file handle
# 2. The list of MAU phonemes as produced by readMAUFromBASFile
# 3. The number of the tier in the TextGrid file
# 4. The start time (usually 0)
# 5. The end time
# 6. The sample rate (in order to convert MAU times into seconds)
def printMAU(file_handle, mau_list, tier_number, start_time, end_time, sample_rate = sample_rate):
    
    # Print status report
    if debug_level == 1:
        print("Printing MAU (time-aligned phoneme) tier.")

    # Output header for current tier
    print("\titem [" + str(tier_number) + "]:", file=file_handle)
    print("\t\tclass = \"IntervalTier\"", file=file_handle)
    print("\t\tname = \"MAU\"", file=file_handle)

    # Calculate start time in seconds
    start_time_seconds = round(start_time / sample_rate, 3)
    
    # Calculate end time in seconds
    end_time_seconds = round(end_time / sample_rate, 3)
    
    print("\t\txmin =", "%.3f" % start_time_seconds, file=file_handle)
    print("\t\txmax =", "%.3f" % end_time_seconds, file=file_handle)
    
    # Determine the number of phonemes
    number_of_phonemes = len(mau_list)
    
    print("\t\tintervals: size =", str(number_of_phonemes), file=file_handle)
    
    # Output the individual intervals
    interval_number = 0
    
    # Go through the list of phonemes
    for phoneme in mau_list:
        
        # Increase interval number
        interval_number += 1

        phoneme_start_time = int(phoneme[0])
        phoneme_end_time = phoneme_start_time + int(phoneme[1])
        phoneme_text = phoneme[3]
        
        # Calculate start time in seconds
        phoneme_start_time_seconds = round(phoneme_start_time / sample_rate, 3)
    
        # Calculate end time in seconds
        phoneme_end_time_seconds = round(phoneme_end_time / sample_rate, 3)
                
        # Output the interval for the current phoneme
        print("\t\tintervals [" + str(interval_number) + "]:", file=file_handle)
        print("\t\t\txmin =", "%.3f" % phoneme_start_time_seconds, file=file_handle)
        print("\t\t\txmax =", "%.3f" % phoneme_end_time_seconds, file=file_handle)
        print("\t\t\ttext =", str(phoneme_text), file=file_handle)


# Print status report
if debug_level == 1:
    print("Converting BAS Partitur file", input_file_name, "to Praat TextGrid file", output_file_name, "using the ORT, KAN, and RID tiers from", original_file_name + ".")

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

# Determine start time of the first word and the end time of the last word
min_word_start_time = getMinimalStartTime(word_times)
max_word_end_time = getMaximalEndTime(word_times)

# Determine start time of the first utterance and the end time of the last utterance
min_utterance_start_time = getMinimalStartTime(utterance_times)
max_utterance_end_time = getMaximalEndTime(utterance_times)

# Make a dictionary from word ids to word forms
word_dict = makeWordDictionary(ort_tier)

# Create output file
output_file = codecs.open(output_file_name, "w", output_encoding)

# Determine absolute start and end times
# Start time of the first phoneme
first_phoneme = mau_tier[0]
absolute_start_time = int(first_phoneme[0])
last_phoneme = mau_tier[-1]
absolute_end_time = int(last_phoneme[0]) + int(last_phoneme[1])

# Print Praat TextGrid header
printPraatTextGridHeader(output_file, start_time = absolute_start_time, end_time = absolute_end_time, num_tiers = 4)

# Print utterance tier (UTT)
printUTT(output_file, rid_tier, utterance_times, word_dict, tier_number = 1, start_time = min_utterance_start_time, end_time = max_utterance_end_time)

# Print orthography tier (ORT)
printORT(output_file, ort_tier, word_times, tier_number = 2, start_time = min_word_start_time, end_time = max_word_end_time)

# Print canonical transcription tier (KAN)
printKAN(output_file, kan_tier, word_times, tier_number = 3, start_time = min_word_start_time, end_time = max_word_end_time)

# Print automatically time-aligned phoneme tier (MAU)
printMAU(output_file, mau_tier, tier_number = 4, start_time = absolute_start_time, end_time = absolute_end_time)

# Close output file
output_file.close()
