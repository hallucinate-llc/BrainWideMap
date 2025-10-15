"""
Data loading utilities for Brain Wide Map dataset.

This module provides the DataLoader class for accessing IBL Brain Wide Map data
through the ONE-api.
"""

import warnings
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
import pandas as pd


class DataLoader:
    """
    Load data from the IBL Brain Wide Map dataset.
    
    This class provides convenient methods to access neural and behavioral data
    from the Brain Wide Map project using the ONE-api.
    
    Attributes:
        one: ONE-api client instance
        mode: Connection mode ('local', 'remote', or 'auto')
    """
    
    def __init__(self, mode: str = 'auto', cache_dir: Optional[str] = None):
        """
        Initialize the DataLoader.
        
        Args:
            mode: Connection mode - 'local', 'remote', or 'auto'
            cache_dir: Optional directory for caching downloaded data
        """
        self.mode = mode
        self.cache_dir = cache_dir
        self.one = None
        self._connect()
    
    def _connect(self):
        """
        Connect to the ONE-api.
        
        Attempts to establish connection based on the specified mode.
        """
        try:
            from one.api import ONE
            
            if self.mode == 'auto':
                # Try remote first, fallback to local
                try:
                    self.one = ONE(base_url='https://openalyx.internationalbrainlab.org',
                                   password='international', silent=True)
                    self.mode = 'remote'
                except Exception:
                    warnings.warn("Remote connection failed, using local mode")
                    self.one = ONE(mode='local', cache_dir=self.cache_dir)
                    self.mode = 'local'
            elif self.mode == 'remote':
                self.one = ONE(base_url='https://openalyx.internationalbrainlab.org',
                               password='international', silent=True)
            else:  # local
                self.one = ONE(mode='local', cache_dir=self.cache_dir)
                
        except ImportError:
            raise ImportError(
                "ONE-api not installed. Install with: pip install one-api"
            )
    
    def list_sessions(self, 
                     project: str = 'brainwide',
                     **kwargs) -> pd.DataFrame:
        """
        List available sessions from the Brain Wide Map project.
        
        Args:
            project: Project name (default: 'brainwide')
            **kwargs: Additional filters (date_range, subject, lab, etc.)
            
        Returns:
            DataFrame containing session information
        """
        if self.one is None:
            raise RuntimeError("Not connected to ONE-api")
        
        # Search for sessions
        eids = self.one.search(project=project, **kwargs)
        
        if len(eids) == 0:
            return pd.DataFrame()
        
        # Get session details
        sessions = []
        for eid in eids:
            try:
                session_info = self.one.get_details(eid)
                sessions.append({
                    'eid': eid,
                    'subject': session_info.get('subject', None),
                    'date': session_info.get('start_time', None),
                    'lab': session_info.get('lab', None),
                    'task_protocol': session_info.get('task_protocol', None),
                })
            except Exception as e:
                warnings.warn(f"Could not load details for session {eid}: {e}")
        
        return pd.DataFrame(sessions)
    
    def load_trials(self, eid: str) -> pd.DataFrame:
        """
        Load trial data for a session.
        
        Args:
            eid: Experiment ID (session identifier)
            
        Returns:
            DataFrame containing trial information
        """
        if self.one is None:
            raise RuntimeError("Not connected to ONE-api")
        
        try:
            trials = self.one.load_object(eid, 'trials')
            return pd.DataFrame(trials)
        except Exception as e:
            raise RuntimeError(f"Failed to load trials for {eid}: {e}")
    
    def load_spike_data(self, eid: str, 
                       probe: Optional[str] = None) -> Tuple[Dict, pd.DataFrame]:
        """
        Load spike times and cluster information.
        
        Args:
            eid: Experiment ID (session identifier)
            probe: Specific probe name (e.g., 'probe00'), or None for all probes
            
        Returns:
            Tuple of (spikes dict, clusters DataFrame)
        """
        if self.one is None:
            raise RuntimeError("Not connected to ONE-api")
        
        try:
            # Load spikes
            spikes = self.one.load_object(eid, 'spikes', collection=probe)
            
            # Load clusters
            clusters = self.one.load_object(eid, 'clusters', collection=probe)
            
            return spikes, pd.DataFrame(clusters)
            
        except Exception as e:
            raise RuntimeError(f"Failed to load spikes for {eid}: {e}")
    
    def load_wheel_data(self, eid: str) -> Dict[str, np.ndarray]:
        """
        Load wheel movement data.
        
        Args:
            eid: Experiment ID (session identifier)
            
        Returns:
            Dictionary containing wheel data (position, timestamps, velocity)
        """
        if self.one is None:
            raise RuntimeError("Not connected to ONE-api")
        
        try:
            wheel = self.one.load_object(eid, 'wheel')
            return wheel
        except Exception as e:
            raise RuntimeError(f"Failed to load wheel data for {eid}: {e}")
    
    def load_behavior_data(self, eid: str) -> Dict[str, Any]:
        """
        Load comprehensive behavioral data for a session.
        
        Args:
            eid: Experiment ID (session identifier)
            
        Returns:
            Dictionary containing trials, wheel, and other behavioral data
        """
        behavior = {}
        
        try:
            behavior['trials'] = self.load_trials(eid)
        except Exception as e:
            warnings.warn(f"Could not load trials: {e}")
        
        try:
            behavior['wheel'] = self.load_wheel_data(eid)
        except Exception as e:
            warnings.warn(f"Could not load wheel: {e}")
        
        return behavior
    
    def get_brain_regions(self, eid: str) -> List[str]:
        """
        Get list of brain regions recorded in a session.
        
        Args:
            eid: Experiment ID (session identifier)
            
        Returns:
            List of brain region acronyms
        """
        try:
            _, clusters = self.load_spike_data(eid)
            if 'acronym' in clusters.columns:
                return sorted(clusters['acronym'].unique().tolist())
            elif 'brain_region' in clusters.columns:
                return sorted(clusters['brain_region'].unique().tolist())
            else:
                return []
        except Exception:
            return []
