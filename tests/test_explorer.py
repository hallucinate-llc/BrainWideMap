"""
Tests for Explorer class.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
from brainwidemap.explorer import Explorer


class TestExplorer:
    """Test suite for Explorer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_loader = Mock()
        self.explorer = Explorer(self.mock_loader)
    
    def test_init(self):
        """Test Explorer initialization."""
        assert self.explorer.loader is self.mock_loader
    
    def test_list_sessions_basic(self):
        """Test basic session listing."""
        mock_sessions = pd.DataFrame({
            'eid': ['eid1', 'eid2'],
            'subject': ['mouse1', 'mouse2'],
            'date': ['2023-01-01', '2023-01-02']
        })
        self.mock_loader.list_sessions.return_value = mock_sessions
        
        sessions = self.explorer.list_sessions()
        
        assert len(sessions) == 2
        assert 'eid' in sessions.columns
    
    def test_get_session_summary(self):
        """Test getting session summary."""
        # Setup mocks
        self.mock_loader.load_trials.return_value = pd.DataFrame({
            'choice': [1, -1, 1],
            'feedbackType': [1, -1, 1]
        })
        self.mock_loader.load_spike_data.return_value = (
            {'times': np.array([0.1, 0.2, 0.3])},
            pd.DataFrame({'cluster_id': [0, 1]})
        )
        self.mock_loader.get_brain_regions.return_value = ['VISp', 'CA1']
        
        summary = self.explorer.get_session_summary('test_eid')
        
        assert 'eid' in summary
        assert 'n_trials' in summary
        assert 'n_units' in summary
        assert 'n_brain_regions' in summary
        assert summary['n_trials'] == 3
        assert summary['n_units'] == 2
        assert summary['n_brain_regions'] == 2
    
    def test_get_brain_region_coverage(self):
        """Test getting brain region coverage."""
        clusters = pd.DataFrame({
            'cluster_id': [0, 1, 2, 3],
            'acronym': ['VISp', 'VISp', 'CA1', 'VISp']
        })
        self.mock_loader.load_spike_data.return_value = (
            {'times': np.array([0.1, 0.2])},
            clusters
        )
        
        coverage = self.explorer.get_brain_region_coverage('test_eid')
        
        assert isinstance(coverage, pd.DataFrame)
        assert 'brain_region' in coverage.columns
        assert 'n_units' in coverage.columns
        assert len(coverage) == 2  # VISp and CA1
    
    def test_filter_units_by_quality(self):
        """Test filtering units by quality."""
        clusters = pd.DataFrame({
            'cluster_id': [0, 1, 2, 3],
            'label': [1, 0, 1, 1],  # 1 = good, 0 = noise
            'isi_viol': [0.1, 0.3, 0.8, 0.2]
        })
        
        filtered = self.explorer.filter_units_by_quality(
            clusters,
            isi_violations_max=0.5
        )
        
        assert len(filtered) < len(clusters)
        assert all(filtered['label'] == 1)
        assert all(filtered['isi_viol'] <= 0.5)
    
    def test_filter_units_by_quality_no_columns(self):
        """Test filtering when quality columns are missing."""
        clusters = pd.DataFrame({
            'cluster_id': [0, 1, 2]
        })
        
        filtered = self.explorer.filter_units_by_quality(clusters)
        
        # Should return original dataframe if no quality columns
        assert len(filtered) == len(clusters)
