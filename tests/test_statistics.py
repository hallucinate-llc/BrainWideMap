"""
Tests for Statistics class.
"""

import pytest
import numpy as np
import pandas as pd
from brainwidemap.statistics import Statistics


class TestStatistics:
    """Test suite for Statistics class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.stats = Statistics()
        
        # Create sample spike data
        self.spikes = {
            'times': np.array([0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3]),
            'clusters': np.array([0, 0, 1, 1, 1, 0, 0, 1])
        }
        
        self.clusters = pd.DataFrame({
            'cluster_id': [0, 1],
            'acronym': ['VISp', 'CA1']
        })
    
    def test_compute_firing_rates(self):
        """Test firing rate computation."""
        fr_df = self.stats.compute_firing_rates(self.spikes, self.clusters)
        
        assert isinstance(fr_df, pd.DataFrame)
        assert 'firing_rate' in fr_df.columns
        assert 'n_spikes' in fr_df.columns
        assert len(fr_df) == 2
        assert all(fr_df['firing_rate'] > 0)
    
    def test_compute_firing_rates_with_time_window(self):
        """Test firing rate computation with time window."""
        fr_df = self.stats.compute_firing_rates(
            self.spikes, 
            self.clusters, 
            time_window=(0.0, 0.6)
        )
        
        assert isinstance(fr_df, pd.DataFrame)
        assert len(fr_df) == 2
    
    def test_compute_psth(self):
        """Test PSTH computation."""
        spike_times = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 1.1, 1.2, 1.3, 2.1, 2.2])
        spike_clusters = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        event_times = np.array([0.0, 1.0, 2.0])
        
        time_bins, psth = self.stats.compute_psth(
            spike_times, 
            spike_clusters, 
            cluster_id=0,
            event_times=event_times,
            window=(-0.1, 0.5),
            bin_size=0.1
        )
        
        assert len(time_bins) == len(psth)
        assert len(time_bins) > 0
        assert all(psth >= 0)
    
    def test_compute_trial_firing_rates(self):
        """Test trial-by-trial firing rate computation."""
        spike_times = np.array([0.1, 0.2, 0.3, 1.1, 1.2, 2.1])
        spike_clusters = np.array([0, 0, 0, 0, 0, 0])
        trial_windows = [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0)]
        
        trial_rates = self.stats.compute_trial_firing_rates(
            spike_times,
            spike_clusters,
            cluster_id=0,
            trial_windows=trial_windows
        )
        
        assert len(trial_rates) == 3
        assert all(trial_rates >= 0)
    
    def test_compute_fano_factor(self):
        """Test Fano factor computation."""
        spike_counts = np.array([5, 6, 4, 7, 5, 6])
        fano = self.stats.compute_fano_factor(spike_counts)
        
        assert isinstance(fano, (float, np.floating))
        assert fano > 0
    
    def test_compute_fano_factor_empty(self):
        """Test Fano factor with empty input."""
        spike_counts = np.array([])
        fano = self.stats.compute_fano_factor(spike_counts)
        
        assert np.isnan(fano)
    
    def test_compute_correlation_matrix(self):
        """Test correlation matrix computation."""
        firing_rates = np.random.rand(5, 100)  # 5 neurons, 100 time bins
        corr_matrix = self.stats.compute_correlation_matrix(firing_rates)
        
        assert corr_matrix.shape == (5, 5)
        assert np.allclose(np.diag(corr_matrix), 1.0)  # Diagonal should be 1
        assert np.allclose(corr_matrix, corr_matrix.T)  # Should be symmetric
    
    def test_compute_population_statistics(self):
        """Test population statistics computation."""
        pop_stats = self.stats.compute_population_statistics(
            self.spikes,
            self.clusters
        )
        
        assert isinstance(pop_stats, dict)
        assert 'n_units' in pop_stats
        assert 'mean_firing_rate' in pop_stats
        assert pop_stats['n_units'] > 0
    
    def test_perform_ttest(self):
        """Test t-test."""
        group1 = np.random.randn(20) + 1
        group2 = np.random.randn(20)
        
        t_stat, p_val = self.stats.perform_ttest(group1, group2)
        
        assert isinstance(t_stat, (float, np.floating))
        assert isinstance(p_val, (float, np.floating))
        assert 0 <= p_val <= 1
    
    def test_smooth_data_gaussian(self):
        """Test data smoothing with Gaussian kernel."""
        data = np.random.randn(100)
        smoothed = self.stats.smooth_data(data, window_size=5, method='gaussian')
        
        assert len(smoothed) == len(data)
        assert not np.array_equal(smoothed, data)
    
    def test_smooth_data_boxcar(self):
        """Test data smoothing with boxcar kernel."""
        data = np.random.randn(100)
        smoothed = self.stats.smooth_data(data, window_size=5, method='boxcar')
        
        assert len(smoothed) == len(data)
    
    def test_smooth_data_savgol(self):
        """Test data smoothing with Savitzky-Golay filter."""
        data = np.random.randn(100)
        smoothed = self.stats.smooth_data(data, window_size=7, method='savgol')
        
        assert len(smoothed) == len(data)
