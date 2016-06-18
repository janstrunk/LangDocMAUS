# encoding=utf-8

# Checks that a BASPartitur file only contains phonemes from the specified inventory
#
# Usage:
# python CheckBASPartiturPhonemeInventory.py BASPARTITURFILE INVENTORYFILE
#
# Optional arguments are:
#
# Jan Strunk (jan_strunk@eva.mpg.de)
# September 2012

# Module to check files and paths
import os.path
import sys

# Codecs for handling character encodings
import codecs

# Module for regular expressions
import re

# Make sure the script has been called with at least two arguments
if len(sys.argv) < 3:
    print("Please provide the name BASPartitur file and the name of the KANINVENTAR file (the list of allowed phonemes).")
    sys.exit()

# Check that the supplied files exist
bas_file_name = os.path.normpath(sys.argv[1])
inventory_file_name = os.path.normpath(sys.argv[2])

if not os.path.exists(bas_file_name):
    print("Cannot find the BASPartitur file you specified:", bas_file_name)
    sys.exit()

if not os.path.isfile(bas_file_name):
    print("The BASPartitur file name you specified does not refer to a file", bas_file_name)
    sys.exit()

if not os.path.exists(inventory_file_name):
    print("Cannot find the KANINVENTAR (phoneme inventory) file you specified:", inventory_file_name)
    sys.exit()

if not os.path.isfile(inventory_file_name):
    print("The KANINVENTAR (phoneme inventory) file name you specified does not refer to a file", inventory_file_name)
    sys.exit()

# Reads a BAS partitur file and returns a list of the words (transcriptions)
# occurring in the KAN tier
# Arguments:
# 1. file name of the BASPartitur file
# 2. optional: encoding
# returns a list of pairs (word, line_number)
def read_bas_file(file_name, encoding="utf-8"):
    bas_file = codecs.open(file_name, "r", encoding)
    
    # The list of occurring words (transcriptions)
    words = []
    
    # Count line numbers for error messages
    line_number = 1
    
    # Go through the file line by line
    for line in bas_file:
        
        # Delete preceding or trailing white space
        line = line.strip()
        
        # If the line starts with the key word "KAN:",
        # it contains phonological information
        if line.startswith("KAN:"):
            
            # Split line at white space
            elements = line.split()

            if len(elements) < 3:
                print("Found a KAN tier that does not contain at least 3 elements (tier marker, number, phoneme) in line:", line_number)
                sys.exit()

            if len(elements) == 3:
            
                # Unpack elements into separate variables    
                (tier_marker, number, word) = elements
            
            else:
                
                # Unpack elements into separate variables    
                tier_marker = elements.pop(0)
                number = elements.pop(0)
                word = " ".join(elements)
                        
            # Append the current word into the list of words
            # (also include the line number)
            words.append((word, line_number))
            
        # Increase line number
        line_number += 1
    
    # Close file
    bas_file.close()
    
    return words
        
# Reads a KANINVENTAR file containing a phoneme inventory
# (which should be ordered with longer phonemes before shorter phonemes)
# and returns a list of the phonemes 
# Arguments:
# 1. file name of the BASPartitur file
# 2. optional: encoding
# returns a set of phonemes
def read_inventory_file(file_name, encoding="utf-8"):
    inventory_file = codecs.open(file_name, "r", encoding)
    
    # The set of phonemes
    phonemes = list()
    
    # Go through the file line by line
    for line in inventory_file:
        
        # Delete preceding or trailing white space
        line = line.strip()
        
        # Add phoneme to inventory
        if not line in phonemes:
            phonemes.append(line)
    
    # Close file
    inventory_file.close()
    
    # Return the list of phonemes
    return phonemes

# Checks whether the phonemes occurring in the BAS file
# are all included in the set of allowed phonemes
# Arguments:
# 1. a list of (word, line_number) pairs from the BASPartitur file
# 2. a list of allowed phonemes (ordered by length, longest first)
# returns a dictionary of illegal phonemes with a list of line numbers where
# they occur as values.
def check_phonemes(list_of_words, allowed_phonemes):
    
    # A dictionary for the results of the check
    results = {}
    
    # Go through the list of (word, line number) pairs
    for (word, line_number) in list_of_phonemes:
        
        # If the word contains whitespace, split it at white space
        # (New style KAN tier for maus.trn)
        if re.search(r"\s", word):
            
            characters = word.split()
            
            # Go through all characters
            for character in characters:
                
                # Test whether it is an allowed phoneme or not
                if character not in allowed_phonemes:
                    
                    illegal_phoneme = character
                    
                    # Add the illegal phoneme to the result dictionary
                    if illegal_phoneme in results:
                        results[illegal_phoneme].append(str(line_number))
            
                    else:
                        results[illegal_phoneme] = [str(line_number)]
        
        # Old style KAN-tier
        else:
            
            # Split the word into characters
            characters = list(word)
        
            # Because phonemes can be more than one character long,
            # we need a little more complicated procedure
            # Perform a left to right greedy search
        
            # Start at position 0
            position = 0
        
            # Length of word
            length_of_word = len(characters)
        
            while position < length_of_word:
            
                # Was a matching phoneme found?
                phoneme_found = False
            
                # Go through phonemes
                for phoneme in allowed_phonemes:
                
                    # Determine length of phoneme
                    phoneme_length = len(phoneme)
                
                    # If there are not enough characters left in the word
                    # skip current phoneme
                    if position + phoneme_length > length_of_word:
                        continue
                
                    # Test whether the current phoneme occurs at the current position
                    possible_segment = "".join(characters[position:position+phoneme_length])
                    if possible_segment == phoneme:
                    
                        # We found a valid phoneme
                        # Increase the current position and stop searching
                        # for phonemes at the current position
                        phoneme_found = True
                        position += phoneme_length
                        break
            
                # Test whether a phoneme was found at the current position
                if not phoneme_found:
                    # Assume the current character is an illegal phoneme
                    illegal_phoneme = characters[position]
                
                    # Add the illegal phoneme to the result dictionary
                    if illegal_phoneme in results:
                        results[illegal_phoneme].append(str(line_number))
            
                    else:
                        results[illegal_phoneme] = [str(line_number)]
                
                # Increase the position in the word by one
                position += 1
    
    # Return the result dictionary
    return results

# Read the BASPartitur file
list_of_phonemes = read_bas_file(bas_file_name)

# Read the KANINVENTAR file
allowed_phonemes = read_inventory_file(inventory_file_name)

# Check whether all occurring phonemes are included
# in the set of allowed phonemes
results = check_phonemes(list_of_phonemes, allowed_phonemes)

if len(results) == 0:
    print("No illegal phonemes found in:", bas_file_name)

else:
    
    # Output a sorted list of illegal phonemes and the corresponding
    # lines in the BASPartitur file where they occurred
    for phoneme in sorted(results):
        
        # Try to output the illegal phoneme to the console
        try:
            print("Illegal phoneme", phoneme, "occuring in lines:\t\t" + " ".join(results[phoneme]))
        
        # If there is a character encoding problem,
        # output a safe represenation of the phoneme
        except UnicodeEncodeError:
            print("Illegal phoneme", repr(phoneme), "occuring in lines:\t\t" + " ".join(results[phoneme]))
