# ------------------------------------------------------------------
# Mock Data Generator for Green Algorithms Dashboard Tests
# This script generates a synthetic enriched logs dataset. i.e. with energy consumption and carbon footprint data,
# simulating job records for multiple mock users. 
# The generated data is saved as a pickle file to serve as static test data for backend dashboard unit tests.
#
# Run this from the project root:
#    $ python tests/pickle_it.py --workload_manager slurm
# ------------------------------------------------------------------

import argparse
from ga_dashboard.backend.helpers import utils

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Generate and pickle synthetic, enriched HPC job logs for dashboard testing."
    )
    argparser.add_argument(
        "--workload_manager", 
        help="Name of the workload manager to simulate (e.g., 'slurm')", 
        required=True, 
        metavar="WORKLOAD_MANAGER", 
        dest="workload_manager"
    )

    args = argparser.parse_args()
    wm = args.workload_manager.lower()

    match wm:
        case "slurm":
            print("Simulating mock enriched Slurm jobs...")
            df2 = utils.simulate_mock_enriched_jobs()
            
            # Save the simulated data to a test fixture
            output_path = "tests/testdata/df_enriched_mockMultiUsers.pkl"
            df2.to_pickle(output_path)
            print(f"Success! Mock data saved to: {output_path}")
            
        case _:
            print(f"Error: Workload manager '{args.workload_manager}' is not recognized or supported.")