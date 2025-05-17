import subprocess

ps_scan_file_location = "resources/carboxylases/prosite/ps_scan/ps_scan.pl"
ps_scan_database_file_location = "resources/carboxylases/prosite/ps_scan/prosite.dat"


def run_ps_scan_with_custom_profile(base_dir, seq_file_location, pattern, ps_scan_output_directory, output_file_name):
    """
        Function runs prosite scan (ps_scan)

        Args:
            base_dir: base directory of the project as defined in main.py
            seq_file_location: The FASTA file with sequences to use.
            pattern: the prosite accession number of the prosite motif to look for
            ps_scan_output_directory: path to output directory in the project
            output_file_name: name of the file that is written as an output

        Returns:
            writes a file to the output directory
        """
    ps_scan_file_location_absolute_path = base_dir + ps_scan_file_location
    ps_database_file_location_absolute_path = base_dir + ps_scan_database_file_location
    ps_output_directory_absolute_path = ps_scan_output_directory

    cmd = ("perl " + ps_scan_file_location_absolute_path + " -d " + ps_database_file_location_absolute_path + " -p "+ pattern + " "
           + seq_file_location + " > " + ps_output_directory_absolute_path + "/" + output_file_name)

    subprocess.run(cmd, shell=True)