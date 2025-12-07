import subprocess


def run_blastp(seq_file_location, blast_db, output_file, num_threads="1", evalue="0.001", outfmt="6"):
    """
        Function runs protein blast

        Args:
            seq_file_location: The FASTA file with sequences to use.
            blast_db: Which database to use.
            output_file: The path to safe the output file.
            num_threads: Specifies the number of threads blast can use.
            evalue: Specifies the evalue threshold for a hit.
            outfmt: Specifies the wanted format of the output file.

        Returns:
            output_file: Writes results to the output file.
        """

    cmd = "blastp -query " + seq_file_location + " -db " + blast_db + " -out " + output_file
    cmd += " -num_threads " + num_threads + " -evalue " + evalue + " -outfmt " + outfmt

    subprocess.run(cmd, shell=True)