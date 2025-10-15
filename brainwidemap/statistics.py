"""
Statistical analysis utilities for Brain Wide Map dataset.

This module provides the Statistics class for computing various statistical
measures on neural and behavioral data.
"""

from typing import Optional, Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from scipy import stats, signal


class Statistics:
    """
    Compute statistics on Brain Wide Map data.
    
    This class provides methods for statistical analysis of neural activity,
    including firing rates, population statistics, and trial-aligned analysis.
    """
    
    def __init__(self):
        """Initialize the Statistics analyzer."""
        pass
    
    def compute_firing_rates(self, 
                            spikes: Dict[str, np.ndarray],
                            clusters: pd.DataFrame,
                            time_window: Optional[Tuple[float, float]] = None) -> pd.DataFrame:
        """
        Compute firing rates for all units.
        
        Args:
            spikes: Dictionary with 'times' and 'clusters' arrays
            clusters: DataFrame with cluster information
            time_window: Optional (start, end) time window in seconds
            
        Returns:
            DataFrame with firing rate statistics per unit
        """
        spike_times = spikes.get('times', spikes.get('spike_times', None))
        spike_clusters = spikes.get('clusters', spikes.get('spike_clusters', None))
        
        if spike_times is None or spike_clusters is None:
            raise ValueError("Spike data must contain 'times' and 'clusters'")
        
        # Apply time window if specified
        if time_window:
            mask = (spike_times >= time_window[0]) & (spike_times <= time_window[1])
            spike_times = spike_times[mask]
            spike_clusters = spike_clusters[mask]
            duration = time_window[1] - time_window[0]
        else:
            duration = spike_times.max() - spike_times.min()
        
        # Compute firing rates
        firing_rates = []
        for cluster_id in clusters.index:
            cluster_spikes = spike_times[spike_clusters == cluster_id]
            n_spikes = len(cluster_spikes)
            fr = n_spikes / duration
            
            # Compute additional statistics
            if n_spikes > 0:
                isi = np.diff(cluster_spikes)
                cv = np.std(isi) / np.mean(isi) if len(isi) > 0 and np.mean(isi) > 0 else np.nan
            else:
                cv = np.nan
            
            firing_rates.append({
                'cluster_id': cluster_id,
                'firing_rate': fr,
                'n_spikes': n_spikes,
                'cv': cv
            })
        
        fr_df = pd.DataFrame(firing_rates)
        
        # Merge with cluster info
        if len(clusters) > 0:
            fr_df = fr_df.merge(clusters.reset_index(), 
                               left_on='cluster_id', 
                               right_on='cluster_id' if 'cluster_id' in clusters.columns else clusters.index.name,
                               how='left')
        
        return fr_df
    
    def compute_psth(self,
                    spike_times: np.ndarray,
                    spike_clusters: np.ndarray,
                    cluster_id: int,
                    event_times: np.ndarray,
                    window: Tuple[float, float] = (-0.5, 1.0),
                    bin_size: float = 0.01) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute peri-stimulus time histogram (PSTH).
        
        Args:
            spike_times: Array of spike times
            spike_clusters: Array of cluster IDs for each spike
            cluster_id: Cluster ID to compute PSTH for
            event_times: Array of event times to align to
            window: (start, end) time window around events in seconds
            bin_size: Bin size in seconds
            
        Returns:
            Tuple of (time_bins, psth) arrays
        """
        # Get spikes for this cluster
        cluster_mask = spike_clusters == cluster_id
        cluster_spike_times = spike_times[cluster_mask]
        
        # Create bins
        bins = np.arange(window[0], window[1] + bin_size, bin_size)
        psth = np.zeros(len(bins) - 1)
        
        # Compute PSTH
        for event_time in event_times:
            aligned_spikes = cluster_spike_times - event_time
            counts, _ = np.histogram(aligned_spikes, bins=bins)
            psth += counts
        
        # Normalize by number of trials and bin size
        psth = psth / (len(event_times) * bin_size)
        
        # Get bin centers
        time_bins = (bins[:-1] + bins[1:]) / 2
        
        return time_bins, psth
    
    def compute_trial_firing_rates(self,
                                   spike_times: np.ndarray,
                                   spike_clusters: np.ndarray,
                                   cluster_id: int,
                                   trial_windows: List[Tuple[float, float]]) -> np.ndarray:
        """
        Compute firing rate for each trial.
        
        Args:
            spike_times: Array of spike times
            spike_clusters: Array of cluster IDs for each spike
            cluster_id: Cluster ID to analyze
            trial_windows: List of (start, end) time windows for each trial
            
        Returns:
            Array of firing rates per trial
        """
        cluster_mask = spike_clusters == cluster_id
        cluster_spike_times = spike_times[cluster_mask]
        
        trial_rates = []
        for start, end in trial_windows:
            trial_spikes = cluster_spike_times[(cluster_spike_times >= start) & 
                                               (cluster_spike_times <= end)]
            duration = end - start
            rate = len(trial_spikes) / duration if duration > 0 else 0
            trial_rates.append(rate)
        
        return np.array(trial_rates)
    
    def compute_fano_factor(self,
                           spike_counts: np.ndarray) -> float:
        """
        Compute Fano factor (variance/mean ratio) of spike counts.
        
        Args:
            spike_counts: Array of spike counts across trials
            
        Returns:
            Fano factor value
        """
        if len(spike_counts) == 0:
            return np.nan
        
        mean_count = np.mean(spike_counts)
        if mean_count == 0:
            return np.nan
        
        return np.var(spike_counts) / mean_count
    
    def compute_correlation_matrix(self,
                                   firing_rates_matrix: np.ndarray) -> np.ndarray:
        """
        Compute pairwise correlation matrix between neurons.
        
        Args:
            firing_rates_matrix: Matrix of firing rates (neurons x time_bins)
            
        Returns:
            Correlation matrix (neurons x neurons)
        """
        return np.corrcoef(firing_rates_matrix)
    
    def compute_population_statistics(self,
                                     spikes: Dict[str, np.ndarray],
                                     clusters: pd.DataFrame,
                                     brain_region: Optional[str] = None) -> Dict[str, Any]:
        """
        Compute population-level statistics.
        
        Args:
            spikes: Dictionary with spike data
            clusters: DataFrame with cluster information
            brain_region: Optional brain region to filter by
            
        Returns:
            Dictionary with population statistics
        """
        # Filter by brain region if specified
        if brain_region:
            if 'acronym' in clusters.columns:
                region_col = 'acronym'
            elif 'brain_region' in clusters.columns:
                region_col = 'brain_region'
            else:
                region_col = None
            
            if region_col:
                clusters = clusters[clusters[region_col] == brain_region]
        
        # Compute firing rates
        fr_df = self.compute_firing_rates(spikes, clusters)
        
        stats_dict = {
            'n_units': len(fr_df),
            'mean_firing_rate': fr_df['firing_rate'].mean(),
            'median_firing_rate': fr_df['firing_rate'].median(),
            'std_firing_rate': fr_df['firing_rate'].std(),
            'mean_cv': fr_df['cv'].mean(),
        }
        
        return stats_dict
    
    def perform_anova(self,
                     data_groups: List[np.ndarray]) -> Tuple[float, float]:
        """
        Perform one-way ANOVA test.
        
        Args:
            data_groups: List of arrays, one per group
            
        Returns:
            Tuple of (F-statistic, p-value)
        """
        f_stat, p_val = stats.f_oneway(*data_groups)
        return f_stat, p_val
    
    def perform_ttest(self,
                     group1: np.ndarray,
                     group2: np.ndarray,
                     paired: bool = False) -> Tuple[float, float]:
        """
        Perform t-test between two groups.
        
        Args:
            group1: First group data
            group2: Second group data
            paired: Whether to perform paired t-test
            
        Returns:
            Tuple of (t-statistic, p-value)
        """
        if paired:
            t_stat, p_val = stats.ttest_rel(group1, group2)
        else:
            t_stat, p_val = stats.ttest_ind(group1, group2)
        
        return t_stat, p_val
    
    def smooth_data(self,
                   data: np.ndarray,
                   window_size: int = 5,
                   method: str = 'gaussian') -> np.ndarray:
        """
        Smooth data using various methods.
        
        Args:
            data: Input data array
            window_size: Size of smoothing window
            method: Smoothing method ('gaussian', 'boxcar', 'savgol')
            
        Returns:
            Smoothed data array
        """
        if method == 'gaussian':
            window = signal.windows.gaussian(window_size, std=window_size/6)
            window = window / window.sum()
            smoothed = np.convolve(data, window, mode='same')
        elif method == 'boxcar':
            window = np.ones(window_size) / window_size
            smoothed = np.convolve(data, window, mode='same')
        elif method == 'savgol':
            smoothed = signal.savgol_filter(data, window_size, 3)
        else:
            raise ValueError(f"Unknown smoothing method: {method}")
        
        return smoothed
