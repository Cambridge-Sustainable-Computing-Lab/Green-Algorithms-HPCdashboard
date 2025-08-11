# Run this from GA4HPCdashboard/ga_dashboard directory:
# python tests/pickle_it.py

# Add the module's path:
import sys
sys.path.append('src')
from ga_dashboard.backend.utils import simulate_mock_jobs

df2 = simulate_mock_jobs()
df2.to_pickle("tests/testdata/df_agg_X_mockMultiUsers_1.pkl")