# ------------------------------------------------------------------
# Implements Green Algorithms carbon calculation methodology
# This module contains the CarbonCalculator class, which calculates the carbon footprint of jobs based on energy usage. Energy is estimated in a different class.
# ------------------------------------------------------------------

import pandas as pd
from datetime import datetime, time, timedelta
from Green_Algorithms_core.src.ga_core.data_models.cluster_info_model import ClusterInfo
from Green_Algorithms_core.src.ga_core.data_models.job_emissions_record import JobEmissionRecord

class CarbonCalculator:
    def __init__(self, cluster_info: ClusterInfo, daily_avg_CI: dict = None):
        self.cluster_info = cluster_info
        self.daily_avg_CI = daily_avg_CI

    @staticmethod
    def calc_carbon_emission(records: list['JobEmissionRecord'], energy_per_hr: float) -> float:
        '''
        Calculate the total carbon emission for a job spanning multiple time periods.

        A job is split into periods (e.g. daily, hourly).
        For each period we know how long the job ran and the average CI for that period.

        Since energy consumption is assumed constant throughout the job,
        each period's emission is:
            energy_per_hr * hours_in_period * CI_of_period

        Summing across all periods gives the total carbon emission for the job.

        :param records: time period slices of the job, each with duration and CI
        :param energy_per_hr: energy consumed per hour (total_energy / total_duration)
        :return: total carbon emission in gCO2
        '''
        if not records:
            print("calc_carbon_emission(): No records provided.")
            return 0.0

        weighted_CI = sum(r.hours_of_work * r.carbon_intensity for r in records if r.carbon_intensity is not None)

        return energy_per_hr * weighted_CI

    @staticmethod
    def calc_carbonFootprint_default(energy: float, CI: float):
        '''
        Calculate the carbon footprint, given a static carbon intensity
        '''
        return energy * CI
    
    def _calc_carbonFootprint_by_row(self, row: pd.Series, suffix: str, daily_avg_CI: dict) -> pd.DataFrame:
        '''
        Expand a job record (1 row) into per day records with energy usage on that day, hours of work on that day, and daily avg CI.
        Calculate the total carbon emissions for the job.
        :param row: a row from the job dataframe
        :param suffix: suffix for energy column (e.g. '', '_memoryNeededOnly', '_failedJobs')
        :param daily_avg_CI: dictionary mapping dates to their average carbon intensity values
        '''

        start = row['StartDatetimeX']
        end = row['EndDatetimeX']
        energy = row[f'energy{suffix}']
        tot_duration_hours = row['WallclockTimeX'].total_seconds() / 3600
        # Assuming energy is consumed uniformly across the job duration
        energy_per_hr = energy / tot_duration_hours if tot_duration_hours > 0 else 0 # Avoid division by zero

        day_job_emissions = []
        current_day = start

        # Per day energy use, hours of work, and CI
        while current_day.date() <= end.date():
            day_start = max(current_day, datetime.combine(current_day.date(), time.min))
            day_end = min(end, datetime.combine(current_day.date(), time.max))
            hours = (day_end - day_start).total_seconds() / 3600
            day_avg_CI = daily_avg_CI.get(current_day.strftime('%d-%m-%Y'), None)

            day_job_emissions.append(JobEmissionRecord(current_day, energy_per_hr, hours, day_avg_CI))
            
            # Advance to midnight of next day
            current_day = datetime.combine(current_day.date() + timedelta(days=1), time.min)

        return CarbonCalculator.calc_carbon_emission(day_job_emissions, energy_per_hr)
    
    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        '''
        Entry point for the carbon emissions calculation process for HPC jobs.
        :param df: [pd.DataFrame] the dataframe containing the cleaned job details
        :return: [pd.DataFrame] the same dataframe with carbon emissions added
        '''
        for suffix in ['', '_memoryNeededOnly', '_failedJobs']:
            if self.daily_avg_CI:
                df[f'carbonFootprint{suffix}'] = df.apply(
                    lambda row: self._calc_carbonFootprint_by_row(row, suffix, self.daily_avg_CI), axis=1
                )
            else: #use default CI value from cluster yaml
                df[f'carbonFootprint{suffix}'] = self.calc_carbonFootprint_default(df[f'energy{suffix}'], self.cluster_info.CI)
        return df
