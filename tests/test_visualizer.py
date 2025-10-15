"""
Tests for Visualizer class.
"""

import pytest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from brainwidemap.visualizer import Visualizer


class TestVisualizer:
    """Test suite for Visualizer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.viz = Visualizer()
        plt.ioff()  # Turn off interactive mode for testing
    
    def teardown_method(self):
        """Clean up after tests."""
        plt.close('all')
    
    def test_init(self):
        """Test Visualizer initialization."""
        assert self.viz.default_figsize == (10, 6)
    
    def test_plot_firing_rates_by_region(self):
        """Test plotting firing rates by region."""
        firing_rates = pd.DataFrame({
            'firing_rate': [10.0, 15.0, 12.0, 8.0, 20.0],
            'acronym': ['VISp', 'CA1', 'VISp', 'CA1', 'VISp']
        })
        
        fig = self.viz.plot_firing_rates_by_region(firing_rates, top_n=2)
        
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) > 0
    
    def test_plot_raster(self):
        """Test plotting spike raster."""
        spike_times = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        spike_clusters = np.array([0, 1, 0, 1, 0])
        
        fig = self.viz.plot_raster(spike_times, spike_clusters)
        
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) > 0
    
    def test_plot_raster_with_cluster_filter(self):
        """Test plotting spike raster with cluster filter."""
        spike_times = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        spike_clusters = np.array([0, 1, 0, 1, 0])
        
        fig = self.viz.plot_raster(
            spike_times, 
            spike_clusters,
            cluster_ids=[0]
        )
        
        assert isinstance(fig, plt.Figure)
    
    def test_plot_psth(self):
        """Test plotting PSTH."""
        time_bins = np.linspace(-0.5, 1.0, 100)
        psth = np.sin(time_bins) + 10
        
        fig = self.viz.plot_psth(time_bins, psth, event_name='Stimulus')
        
        assert isinstance(fig, plt.Figure)
        assert len(fig.axes) > 0
    
    def test_plot_trial_activity(self):
        """Test plotting trial activity."""
        trial_rates = np.random.rand(50) * 10
        
        fig = self.viz.plot_trial_activity(trial_rates)
        
        assert isinstance(fig, plt.Figure)
    
    def test_plot_trial_activity_with_types(self):
        """Test plotting trial activity with trial types."""
        trial_rates = np.random.rand(50) * 10
        trial_types = np.array([0] * 25 + [1] * 25)
        
        fig = self.viz.plot_trial_activity(trial_rates, trial_types)
        
        assert isinstance(fig, plt.Figure)
    
    def test_plot_correlation_matrix(self):
        """Test plotting correlation matrix."""
        corr_matrix = np.random.rand(5, 5)
        corr_matrix = (corr_matrix + corr_matrix.T) / 2  # Make symmetric
        np.fill_diagonal(corr_matrix, 1.0)
        
        fig = self.viz.plot_correlation_matrix(corr_matrix)
        
        assert isinstance(fig, plt.Figure)
    
    def test_plot_behavioral_performance(self):
        """Test plotting behavioral performance."""
        trials = pd.DataFrame({
            'feedbackType': [1, -1, 1, 1, -1, 1, 1, 1] * 10
        })
        
        fig = self.viz.plot_behavioral_performance(trials, window_size=5)
        
        assert isinstance(fig, plt.Figure)
    
    def test_plot_brain_region_distribution(self):
        """Test plotting brain region distribution."""
        clusters = pd.DataFrame({
            'acronym': ['VISp'] * 10 + ['CA1'] * 5 + ['MOs'] * 3
        })
        
        fig = self.viz.plot_brain_region_distribution(clusters, top_n=3)
        
        assert isinstance(fig, plt.Figure)
    
    def test_save_figure(self, tmp_path):
        """Test saving figure to file."""
        fig = plt.figure()
        plt.plot([1, 2, 3], [1, 2, 3])
        
        output_file = tmp_path / "test_figure.png"
        self.viz.save_figure(fig, str(output_file), dpi=100)
        
        assert output_file.exists()
