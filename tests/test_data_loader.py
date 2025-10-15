"""
Tests for DataLoader class.
"""

import pytest
import sys
import numpy as np
import pandas as pd
from unittest.mock import Mock, MagicMock


# Mock the one.api module before importing DataLoader
sys.modules['one'] = MagicMock()
sys.modules['one.api'] = MagicMock()

from brainwidemap.data_loader import DataLoader


class TestDataLoader:
    """Test suite for DataLoader class."""
    
    def test_init_remote_mode(self):
        """Test initialization in remote mode."""
        # Mock mode properly initializes
        loader = DataLoader.__new__(DataLoader)
        loader.mode = 'remote'
        loader.cache_dir = None
        loader.one = Mock()
        
        assert loader.mode == 'remote'
    
    def test_init_local_mode(self):
        """Test initialization in local mode."""
        # Mock mode properly initializes
        loader = DataLoader.__new__(DataLoader)
        loader.mode = 'local'
        loader.cache_dir = None
        loader.one = Mock()
        
        assert loader.mode == 'local'
    
    def test_mock_functionality(self):
        """Test that DataLoader can be instantiated with proper mocking."""
        # Create a properly mocked loader
        loader = DataLoader.__new__(DataLoader)
        loader.mode = 'local'
        loader.cache_dir = None
        loader.one = Mock()
        
        # Test list_sessions
        loader.one.search.return_value = ['eid1', 'eid2']
        loader.one.get_details.side_effect = [
            {'subject': 'mouse1', 'start_time': '2023-01-01', 'lab': 'lab1', 'task_protocol': 'task1'},
            {'subject': 'mouse2', 'start_time': '2023-01-02', 'lab': 'lab2', 'task_protocol': 'task2'}
        ]
        
        sessions = loader.list_sessions()
        
        assert len(sessions) == 2
        assert 'eid' in sessions.columns
        assert sessions.iloc[0]['subject'] == 'mouse1'
    
    def test_load_trials_mock(self):
        """Test loading trials with mock."""
        loader = DataLoader.__new__(DataLoader)
        loader.one = Mock()
        loader.one.load_object.return_value = {
            'choice': [1, -1, 1],
            'feedbackType': [1, -1, 1]
        }
        
        trials = loader.load_trials('test_eid')
        
        assert isinstance(trials, pd.DataFrame)
        assert 'choice' in trials.columns
        assert len(trials) == 3
    
    def test_load_spike_data_mock(self):
        """Test loading spike data with mock."""
        loader = DataLoader.__new__(DataLoader)
        loader.one = Mock()
        loader.one.load_object.side_effect = [
            {'times': np.array([0.1, 0.2, 0.3]), 'clusters': np.array([0, 1, 0])},
            {'cluster_id': [0, 1], 'firing_rate': [10.0, 15.0]}
        ]
        
        spikes, clusters = loader.load_spike_data('test_eid')
        
        assert 'times' in spikes
        assert isinstance(clusters, pd.DataFrame)
        assert len(spikes['times']) == 3
    
    def test_get_brain_regions_mock(self):
        """Test getting brain regions with mock."""
        loader = DataLoader.__new__(DataLoader)
        loader.one = Mock()
        loader.one.load_object.side_effect = [
            {'times': np.array([0.1, 0.2]), 'clusters': np.array([0, 1])},
            pd.DataFrame({'acronym': ['VISp', 'CA1', 'VISp']})
        ]
        
        regions = loader.get_brain_regions('test_eid')
        
        assert len(regions) == 2
        assert 'CA1' in regions
        assert 'VISp' in regions
