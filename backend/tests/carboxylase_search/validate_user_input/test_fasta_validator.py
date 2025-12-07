from backend.carboxylase_search.validate_user_input.fasta_validator import is_valid_fasta

invalid_fasta1 = "/home/eva/PycharmProjects/Carboxylase_Server/backend/tests/carboxylase_search/validate_user_input/resources/invalid_fasta1.fasta"
invalid_fasta2 = "/home/eva/PycharmProjects/Carboxylase_Server/backend/tests/carboxylase_search/validate_user_input/resources/invalid_fasta2.fasta"
invalid_fasta3 = "/home/eva/PycharmProjects/Carboxylase_Server/backend/tests/carboxylase_search/validate_user_input/resources/invalid_fasta3.fasta"

valid_fasta = "/home/eva/PycharmProjects/Carboxylase_Server/backend/tests/carboxylase_search/validate_user_input/resources/valid_fasta.fasta"

def test_invalid_fasta_formats():
    return_value1 = "The first line doesn't start with the '>' character"
    return_value2 = "Your fasta file contains duplicate identifiers"
    return_value3 = "Your sequences may only contain the characters 'A-Z'"
    result1 = is_valid_fasta(invalid_fasta1)
    result2 = is_valid_fasta(invalid_fasta2)
    result3 = is_valid_fasta(invalid_fasta3)
    assert return_value1 == result1
    assert return_value2 == result2
    assert return_value3 == result3

def test_valid_fasta_format():
    return_value = True
    result = is_valid_fasta(valid_fasta)
    assert return_value == result