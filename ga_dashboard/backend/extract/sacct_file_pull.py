# sacct_file_pull.py
#
# Run the sacct command on a remote server, store the results in a file, then download that file
# to the local machine where this script is running.

import logging
import subprocess

logger = logging.getLogger(__name__)
logging_level = logging.DEBUG  # Select logging.INFO or logging.DEBUG as required.
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)


def capture_sacct_output():

    # We want to run the sacct command on the remote server, save the result in a file on the server,
    # then download it and use it.
    #
    # Alternatively, we could ssh into the server, run the sacct command, disconnect, and save the data locally

    bash_com = [
        "sacct",
        "--starttime",
        "2025-04-14",  #self.args.startDay,  # format YYYY-MM-DD 2025-04-14 --endtime 2025-04-15
        "--endtime",
        "2025-04-18",  #self.args.endDay,  # format YYYY-MM-DD
        "--format",
        "UID,User,JobID,JobName,Submit,Elapsed,Partition,NNodes,NCPUS,TotalCPU,CPUTime,ReqMem,MaxRSS,WorkDir,State,Account,AllocTres",
        "-P",
        "-L"  # All clusters
    ]

    filename = "matt_sacct.txt"

    use_as_admin = True
                
    if use_as_admin:
        bash_com.append('--allusers')


    logger.debug("info SACCT CMD: " + str(bash_com))

    completed_processs = subprocess.run(bash_com, capture_output=True)  #, text=True)
    data = completed_processs.stdout
    logger.debug("Output captured:")
    logger.debug(data)

    # Save the binary data into a file.
    with open(filename, 'wb') as f: ## File
        f.write(data)



def main():

    capture_sacct_output()



if __name__ == "__main__":
    main()