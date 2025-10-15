"""
Visualization utilities for Brain Wide Map dataset.

This module provides the Visualizer class for creating plots and visualizations
of neural and behavioral data.
"""

from typing import Optional, List, Tuple, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


class Visualizer:
    """
    Visualize Brain Wide Map data.
    
    This class provides methods for creating various plots and visualizations
    of neural activity and behavioral data.
    """
    
    def __init__(self, style: str = 'seaborn-v0_8-darkgrid'):
        """
        Initialize the Visualizer.
        
        Args:
            style: Matplotlib style to use
        """
        try:
            plt.style.use(style)
        except:
            # Fallback if style not available
            sns.set_theme()
        
        self.default_figsize = (10, 6)
    
    def plot_firing_rates_by_region(self,
                                    firing_rates: pd.DataFrame,
                                    top_n: int = 20,
                                    figsize: Optional[Tuple[int, int]] = None) -> plt.Figure:
        """
        Plot firing rates grouped by brain region.
        
        Args:
            firing_rates: DataFrame with firing rates and brain regions
            top_n: Number of top regions to show
            figsize: Figure size (width, height)
            
        Returns:
            Matplotlib figure object
        """
        if figsize is None:
            figsize = self.default_figsize
        
        # Determine region column
        region_col = None
        for col in ['acronym', 'brain_region', 'region']:
            if col in firing_rates.columns:
                region_col = col
                break
        
        if region_col is None:
            raise ValueError("No brain region column found in firing_rates")
        
        # Group by region and compute statistics
        region_stats = firing_rates.groupby(region_col)['firing_rate'].agg(['mean', 'std', 'count'])
        region_stats = region_stats.sort_values('mean', ascending=False).head(top_n)
        
        # Create plot
        fig, ax = plt.subplots(figsize=figsize)
        
        x_pos = np.arange(len(region_stats))
        ax.bar(x_pos, region_stats['mean'], yerr=region_stats['std'], 
               alpha=0.7, capsize=5)
        
        ax.set_xlabel('Brain Region')
        ax.set_ylabel('Mean Firing Rate (Hz)')
        ax.set_title(f'Firing Rates by Brain Region (Top {top_n})')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(region_stats.index, rotation=45, ha='right')
        
        plt.tight_layout()
        return fig
    
    def plot_raster(self,
                   spike_times: np.ndarray,
                   spike_clusters: np.ndarray,
                   cluster_ids: Optional[List[int]] = None,
                   time_range: Optional[Tuple[float, float]] = None,
                   figsize: Optional[Tuple[int, int]] = None) -> plt.Figure:
        """
        Create a raster plot of spike times.
        
        Args:
            spike_times: Array of spike times
            spike_clusters: Array of cluster IDs for each spike
            cluster_ids: Optional list of specific clusters to plot
            time_range: Optional (start, end) time range
            figsize: Figure size (width, height)
            
        Returns:
            Matplotlib figure object
        """
        if figsize is None:
            figsize = (12, 8)
        
        # Filter by time range
        if time_range:
            mask = (spike_times >= time_range[0]) & (spike_times <= time_range[1])
            spike_times = spike_times[mask]
            spike_clusters = spike_clusters[mask]
        
        # Filter by cluster IDs
        if cluster_ids is None:
            cluster_ids = np.unique(spike_clusters)
        else:
            mask = np.isin(spike_clusters, cluster_ids)
            spike_times = spike_times[mask]
            spike_clusters = spike_clusters[mask]
        
        # Create plot
        fig, ax = plt.subplots(figsize=figsize)
        
        for i, cluster_id in enumerate(cluster_ids):
            cluster_spike_times = spike_times[spike_clusters == cluster_id]
            ax.scatter(cluster_spike_times, 
                      np.ones_like(cluster_spike_times) * i,
                      marker='|', s=50, alpha=0.5)
        
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Unit ID')
        ax.set_title('Spike Raster Plot')
        ax.set_ylim([-1, len(cluster_ids)])
        
        plt.tight_layout()
        return fig
    
    def plot_psth(self,
                 time_bins: np.ndarray,
                 psth: np.ndarray,
                 event_name: str = 'Event',
                 figsize: Optional[Tuple[int, int]] = None) -> plt.Figure:
        """
        Plot peri-stimulus time histogram (PSTH).
        
        Args:
            time_bins: Array of time bin centers
            psth: Array of firing rates
            event_name: Name of the event for plot title
            figsize: Figure size (width, height)
            
        Returns:
            Matplotlib figure object
        """
        if figsize is None:
            figsize = self.default_figsize
        
        fig, ax = plt.subplots(figsize=figsize)
        
        ax.plot(time_bins, psth, linewidth=2)
        ax.axvline(x=0, color='r', linestyle='--', alpha=0.5, label='Event')
        
        ax.set_xlabel('Time from event (s)')
        ax.set_ylabel('Firing rate (Hz)')
        ax.set_title(f'PSTH aligned to {event_name}')
        ax.legend()
        
        plt.tight_layout()
        return fig
    
    def plot_trial_activity(self,
                           trial_rates: np.ndarray,
                           trial_types: Optional[np.ndarray] = None,
                           figsize: Optional[Tuple[int, int]] = None) -> plt.Figure:
        """
        Plot firing rates across trials.
        
        Args:
            trial_rates: Array of firing rates per trial
            trial_types: Optional array of trial type labels
            figsize: Figure size (width, height)
            
        Returns:
            Matplotlib figure object
        """
        if figsize is None:
            figsize = self.default_figsize
        
        fig, ax = plt.subplots(figsize=figsize)
        
        if trial_types is None:
            ax.plot(trial_rates, alpha=0.7)
        else:
            unique_types = np.unique(trial_types)
            for trial_type in unique_types:
                mask = trial_types == trial_type
                trials = np.where(mask)[0]
                ax.scatter(trials, trial_rates[mask], 
                          label=f'Type {trial_type}', alpha=0.7)
            ax.legend()
        
        ax.set_xlabel('Trial Number')
        ax.set_ylabel('Firing Rate (Hz)')
        ax.set_title('Neural Activity Across Trials')
        
        plt.tight_layout()
        return fig
    
    def plot_correlation_matrix(self,
                               correlation_matrix: np.ndarray,
                               labels: Optional[List[str]] = None,
                               figsize: Optional[Tuple[int, int]] = None) -> plt.Figure:
        """
        Plot correlation matrix as a heatmap.
        
        Args:
            correlation_matrix: Square correlation matrix
            labels: Optional labels for rows/columns
            figsize: Figure size (width, height)
            
        Returns:
            Matplotlib figure object
        """
        if figsize is None:
            figsize = (10, 8)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        sns.heatmap(correlation_matrix, 
                   xticklabels=labels if labels else False,
                   yticklabels=labels if labels else False,
                   cmap='coolwarm', center=0, 
                   vmin=-1, vmax=1,
                   square=True, ax=ax)
        
        ax.set_title('Neural Correlation Matrix')
        
        plt.tight_layout()
        return fig
    
    def plot_behavioral_performance(self,
                                   trials: pd.DataFrame,
                                   window_size: int = 50,
                                   figsize: Optional[Tuple[int, int]] = None) -> plt.Figure:
        """
        Plot behavioral performance over trials.
        
        Args:
            trials: DataFrame with trial data
            window_size: Window size for rolling average
            figsize: Figure size (width, height)
            
        Returns:
            Matplotlib figure object
        """
        if figsize is None:
            figsize = self.default_figsize
        
        # Check for performance column
        if 'feedbackType' in trials.columns:
            performance = (trials['feedbackType'] == 1).astype(int)
        elif 'correct' in trials.columns:
            performance = trials['correct'].astype(int)
        else:
            raise ValueError("No performance column found in trials")
        
        # Compute rolling average
        rolling_perf = performance.rolling(window=window_size, min_periods=1).mean()
        
        fig, ax = plt.subplots(figsize=figsize)
        
        ax.plot(performance.values, alpha=0.3, label='Trial outcome')
        ax.plot(rolling_perf.values, linewidth=2, label=f'{window_size}-trial average')
        ax.axhline(y=0.5, color='k', linestyle='--', alpha=0.5, label='Chance')
        
        ax.set_xlabel('Trial Number')
        ax.set_ylabel('Performance (fraction correct)')
        ax.set_title('Behavioral Performance')
        ax.set_ylim([0, 1])
        ax.legend()
        
        plt.tight_layout()
        return fig
    
    def plot_brain_region_distribution(self,
                                      clusters: pd.DataFrame,
                                      top_n: int = 20,
                                      figsize: Optional[Tuple[int, int]] = None) -> plt.Figure:
        """
        Plot distribution of units across brain regions.
        
        Args:
            clusters: DataFrame with cluster information
            top_n: Number of top regions to show
            figsize: Figure size (width, height)
            
        Returns:
            Matplotlib figure object
        """
        if figsize is None:
            figsize = self.default_figsize
        
        # Determine region column
        region_col = None
        for col in ['acronym', 'brain_region', 'region']:
            if col in clusters.columns:
                region_col = col
                break
        
        if region_col is None:
            raise ValueError("No brain region column found in clusters")
        
        # Count units per region
        region_counts = clusters[region_col].value_counts().head(top_n)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        ax.barh(range(len(region_counts)), region_counts.values, alpha=0.7)
        ax.set_yticks(range(len(region_counts)))
        ax.set_yticklabels(region_counts.index)
        ax.set_xlabel('Number of Units')
        ax.set_ylabel('Brain Region')
        ax.set_title(f'Unit Distribution Across Brain Regions (Top {top_n})')
        ax.invert_yaxis()
        
        plt.tight_layout()
        return fig
    
    def save_figure(self, fig: plt.Figure, filename: str, dpi: int = 300):
        """
        Save figure to file.
        
        Args:
            fig: Matplotlib figure object
            filename: Output filename
            dpi: Resolution in dots per inch
        """
        fig.savefig(filename, dpi=dpi, bbox_inches='tight')
        print(f"Figure saved to {filename}")
