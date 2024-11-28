import FastaValidator

def is_valid_fasta(file_name):
    code = FastaValidator.fasta_validator(file_name)
    if code == 0:
        return True
    elif code == 1:
        return "The first line doesn't start with the '>' character"
    elif code == 2:
        return "Your fasta file contains duplicate identifiers"
    elif code == 4:
        return "Your sequences may only contain the characters 'A-Z'"
    return "There was an error reading your fasta input, please check if it is in the right file format."