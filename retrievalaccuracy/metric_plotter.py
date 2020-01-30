'''
Class to produce plots of multiple retrieval runs

Can produce plots of individual parameters,

'''
import numpy as np
import matplotlib.pyplot as plt
import corner

from .metric_calculator import MetricCalculator

class MetricPlotter:
    def __init__(self, parameter_limits, parameter_labels=None):
        '''
        An object to produce visualisations of retrieval quality through
        plotting histograms, marginalised distributions and corner plots of
        metric values for multiple retrieval runs.

        Parameters
        ----------
        parameter_limits : array_like, shape (n_variables, 2)
            The physical values of the limits on each parameter, provided in
            (lower, upper) pairs.
        parameter_labels : array_like, shape (n_variables, ) or ``None``
            The label to use for each parameter in plotting. If ``None``, will
            default to using indices. Default is None.
        '''
        self.metric_calculator = MetricCalculator(parameter_limits)
        self.n_variables = len(parameter_limits)

        if parameter_labels is None:
            self.parameter_labels = np.arange(self.n_variables)
        else:
            if not len(parameter_labels) == self.n_variables:
                raise ValueError('Incorrect number of parameter labels provided')
            self.parameter_labels = parameter_labels

    def corner_plot(self, true_results, retrieved_results, uncertainty,
                    metric_type='all', rescale_axes=True, figsize=(15,15),
                    bins=10, histtype='stepfilled', show=True):
        '''
        Plots a corner plot of different metric values with marginalised
        distributions for multiple results and known values.

        Parameters
        ----------
        true_results : array_like, shape (n_samples, n_variables)
            The known (true) results of each retrieval run
        retrieved_results : array_like, shape (n_samples, n_variables)
            The results of each retrieval
        uncertainty : array_like, shape (n_samples, n_variables, 2)
            The lower and upper uncertainty on each retrieved parameter
        metric_type : str, optional
            The metric type to plot. Accepted are
                - 'accuracy' or 'm1' - the accuracy metric
                - 'precision' or 'm2' - the precision metric
                - 'all' - plots all metrics
            Default is 'all'
        figsize : tuple, optional
            The figure size to use. Default is (15, 15)
        rescale_axes : bool, optional
            If True, all axes will be rescaled to show the full possible range
            of each parameter, rather than just the range of the provided data.
            Default is True.
        '''
        # TODO: sanity checks on shapes etc
        true_results = np.array(true_results)
        retrieved_results = np.array(retrieved_results)

        if not true_results.shape == retrieved_results.shape:
            raise ValueError('Shapes of true {} and retrieved {} results do not match!'.format(true_results.shape, retrieved_results.shape))

        if metric_type.lower() == in ['accuracy', 'm1']:
            plot_type_indices = [0]
        elif metric_type.lower() == in ['precision', 'm2']:
            plot_type_indices = [1]
        elif metric_type.lower() == in ['all']:
            plot_type_indices = [0, 1]
        else:
            raise ValueError('Unrecognised metric_type {}'.format(metric_type))

        n_samples = len(true_results)

        # Set up arrays and initialise to np.inf for error catching
        accuracy_metrics = np.ones(n_samples) * np.inf
        precision_metrics = np.ones(n_samples) * np.inf
        # Components array. index 0 is accuracy, 1 is precision
        components = np.ones((2, n_samples, self.n_variables)) * np.inf

        for i in range(n_samples):
            # Loop through and calculate metric values
            a, ac, p, pc = self.metric_calculator.calculate_metrics(true_results[i], retrieved_results[i], uncertainty[i])

            # store the results
            accuracy_metrics[i] = a
            components[0, i] = ac
            precision_metrics[i] = p
            components[1, i] = pc

        figures = []

        # Now we have the values, we can make the plots!
        for type_idx in plot_type_indices:
            # Loop for each metric type we are interested in.
            vals = components[type_idx]
            figure = corner.corner(vals, bins=bins, labels=self.parameter_labels)
            figures.append(figure)

        if show:
            plt.show()

        return figures
