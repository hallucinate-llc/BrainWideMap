"""
Data exploration utilities for Brain Wide Map dataset.

This module provides the Explorer class for querying and filtering
Brain Wide Map data.
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np


class Explorer:
    """
    Explore and query Brain Wide Map data.
    
    This class provides methods to search, filter, and explore sessions,
    brain regions, and neural units from the Brain Wide Map dataset.
    
    Attributes:
        loader: DataLoader instance for accessing data
    """
    
    def __init__(self, loader):
        """
        Initialize the Explorer.
        
        Args:
            loader: DataLoader instance
        """
        self.loader = loader
    
    def list_sessions(self, 
                     n_trials_min: Optional[int] = None,
                     n_trials_max: Optional[int] = None,
                     date_range: Optional[List[str]] = None,
                     subject: Optional[str] = None,
                     lab: Optional[str] = None) -> pd.DataFrame:
        """
        List sessions with filtering options.
        
        Args:
            n_trials_min: Minimum number of trials
            n_trials_max: Maximum number of trials
            date_range: Date range [start_date, end_date] in 'YYYY-MM-DD' format
            subject: Subject identifier
            lab: Lab name
            
        Returns:
            DataFrame of filtered sessions
        """
        # Build search kwargs
        kwargs = {}
        if date_range:
            kwargs['date_range'] = date_range
        if subject:
            kwargs['subject'] = subject
        if lab:
            kwargs['lab'] = lab
        
        # Get sessions
        sessions = self.loader.list_sessions(**kwargs)
        
        # Filter by trial count if specified
        if n_trials_min or n_trials_max:
            filtered_sessions = []
            for _, session in sessions.iterrows():
                try:
                    trials = self.loader.load_trials(session['eid'])
                    n_trials = len(trials)
                    
                    if n_trials_min and n_trials < n_trials_min:
                        continue
                    if n_trials_max and n_trials > n_trials_max:
                        continue
                    
                    session_dict = session.to_dict()
                    session_dict['n_trials'] = n_trials
                    filtered_sessions.append(session_dict)
                except Exception:
                    continue
            
            sessions = pd.DataFrame(filtered_sessions)
        
        return sessions
    
    def get_session_summary(self, eid: str) -> Dict[str, Any]:
        """
        Get comprehensive summary of a session.
        
        Args:
            eid: Experiment ID (session identifier)
            
        Returns:
            Dictionary with session summary information
        """
        summary = {'eid': eid}
        
        try:
            # Load trials
            trials = self.loader.load_trials(eid)
            summary['n_trials'] = len(trials)
            
            if 'choice' in trials.columns:
                # Calculate performance
                correct_trials = trials['feedbackType'] == 1 if 'feedbackType' in trials.columns else None
                if correct_trials is not None:
                    summary['performance'] = correct_trials.mean()
            
            # Load spikes
            spikes, clusters = self.loader.load_spike_data(eid)
            summary['n_units'] = len(clusters) if len(clusters) > 0 else 0
            
            # Brain regions
            brain_regions = self.loader.get_brain_regions(eid)
            summary['n_brain_regions'] = len(brain_regions)
            summary['brain_regions'] = brain_regions
            
        except Exception as e:
            summary['error'] = str(e)
        
        return summary
    
    def find_sessions_by_region(self, 
                                region: str,
                                min_units: int = 10) -> pd.DataFrame:
        """
        Find sessions containing recordings from a specific brain region.
        
        Args:
            region: Brain region acronym (e.g., 'VISp', 'CA1')
            min_units: Minimum number of units from that region
            
        Returns:
            DataFrame of matching sessions
        """
        sessions = self.loader.list_sessions()
        matching_sessions = []
        
        for _, session in sessions.iterrows():
            try:
                _, clusters = self.loader.load_spike_data(session['eid'])
                
                # Check if region exists in this session
                if 'acronym' in clusters.columns:
                    region_col = 'acronym'
                elif 'brain_region' in clusters.columns:
                    region_col = 'brain_region'
                else:
                    continue
                
                region_units = clusters[clusters[region_col] == region]
                
                if len(region_units) >= min_units:
                    session_dict = session.to_dict()
                    session_dict['n_units_in_region'] = len(region_units)
                    matching_sessions.append(session_dict)
                    
            except Exception:
                continue
        
        return pd.DataFrame(matching_sessions)
    
    def get_brain_region_coverage(self, eid: str) -> pd.DataFrame:
        """
        Get brain region coverage for a session.
        
        Args:
            eid: Experiment ID (session identifier)
            
        Returns:
            DataFrame with brain regions and unit counts
        """
        try:
            _, clusters = self.loader.load_spike_data(eid)
            
            if 'acronym' in clusters.columns:
                region_col = 'acronym'
            elif 'brain_region' in clusters.columns:
                region_col = 'brain_region'
            else:
                return pd.DataFrame()
            
            region_counts = clusters[region_col].value_counts().reset_index()
            region_counts.columns = ['brain_region', 'n_units']
            
            return region_counts.sort_values('n_units', ascending=False)
            
        except Exception as e:
            raise RuntimeError(f"Failed to get brain region coverage: {e}")
    
    def filter_units_by_quality(self, 
                                clusters: pd.DataFrame,
                                quality_threshold: float = 0.9,
                                isi_violations_max: float = 0.5) -> pd.DataFrame:
        """
        Filter neural units by quality metrics.
        
        Args:
            clusters: DataFrame of cluster information
            quality_threshold: Minimum quality score (if available)
            isi_violations_max: Maximum ISI violation rate
            
        Returns:
            Filtered DataFrame of high-quality units
        """
        filtered = clusters.copy()
        
        # Filter by label if available
        if 'label' in filtered.columns:
            filtered = filtered[filtered['label'] == 1]  # 1 = good
        
        # Filter by ISI violations if available
        if 'isi_viol' in filtered.columns:
            filtered = filtered[filtered['isi_viol'] <= isi_violations_max]
        
        return filtered
    
    def get_all_brain_regions(self) -> List[str]:
        """
        Get list of all brain regions in the dataset.
        
        Returns:
            List of unique brain region acronyms
        """
        sessions = self.loader.list_sessions()
        all_regions = set()
        
        for _, session in sessions.iterrows():
            try:
                regions = self.loader.get_brain_regions(session['eid'])
                all_regions.update(regions)
            except Exception:
                continue
        
        return sorted(list(all_regions))
