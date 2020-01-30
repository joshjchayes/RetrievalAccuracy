'''
The MetricCalculator acts as an interface for all metric calculation

'''


from scipy.optimize import fsolve
from scipy.spatial import distance
import numpy as np

from ._scaler import Scaler


class MetricCalculator:
    def __init__(self, parameter_limits):
        '''
        The MetricCalculator generates metrics which can be used to
        quantify quality of retrieval. The two main metrics are the accuracy
        metric, which is a dimensionless distance between two points
        (assumed to be true values and retrieved values), and the precision
        metric M2, which is defined as the number of standard deviations
        away from the true value a retrieved value is. For more information
        see Hayes et. al. (2019) - https://arxiv.org/abs/1909.00718.

        Parameters
        ----------
        parameter_limits : array_like, shape (n_variables, 2)
            The physical values of the limits on each parameter, provided in
            (lower, upper) pairs.
        '''
        # set up the scaler
        self.scaler = Scaler(parameter_limits)
        self.n_variables = len(parameter_limits)

    def calculate_accuracy_metric(self, true_parameters, retrieved_parameters):
        '''
        Calculates the accuracy metric, M1, defined as the Euclidean distance
        between two points in unit-normalised physical parameter space.

        Parameters
        ----------
        true_parameters : array_like, shape (n_parameters, )
            The accepted 'true' values of the parameters, provided in physical
            space (i.e. with units)
        retrieved_parameters : array_like, shape (n_parameters, )
            The retrieved values of the parameters, provided in physical space
            (i.e. with units)

        Returns
        -------
        accuracy_metric : float
            The Euclidean distance between the two given points
        components : array_like, shape (n_parameters, )
            The components of the accuracy metric.
        '''
        dimensionless_true = self.scaler.point_to_dimensionless(true_parameters)
        dimensionless_retrieved = self.scaler.point_to_dimensionless(retrieved_parameters)

        metric = distance.euclidean(dimensionless_true, dimensionless_retrieved)

        return metric, dimensionless_true - dimensionless_retrieved

    def calculate_precision_metric(self, true_parameters, retrieved_parameters,
                                   uncertainty):
        '''
        Calculates the precision metric, M2, defined as

        M2^2 = sum((M1_i/uncertainty_i)^2)

        where M1_i are components of the accuracy metric

        Parameters
        ----------
        true_parameters : array_like, shape (n_parameters, )
            The accepted 'true' values of the parameters, provided in physical
            space (i.e. with units)
        retrieved_parameters : array_like, shape (n_parameters, )
            The retrieved values of the parameters, provided in physical space
            (i.e. with units)
        uncertainty : array_like, shape (n_parameters, ) or (n_parameters, 2)
            The uncertainy associated with each retrieved parameter value.
            If 1D array is provided, assumes uniform upper and lower errors.
            If 2D array provided, assumes errors are provided as(lower, upper)
            pairs.

        Returns
        -------
        precision_metric : float
            The precision metric associated with the retrieval results
        metric_components : array_like, shape (n_parameters, )
            The components of the precision metric.
        sigma : float
            The 1 sigma value in the direction of the vector between the true
            and retrieved parameters.
        '''
        # Scale the points and errors
        dimensionless_true = self.scaler.point_to_dimensionless(true_parameters)
        dimensionless_retrieved = self.scaler.point_to_dimensionless(retrieved_parameters)
        dimensionless_errors = self.scaler.errors_to_dimensionless(uncertainty)

        # which values of error to use based on direction of the true value
        # compared to the retrieved one. Note that we default to the upper
        # error in the event that the retrieval is exact.
        delta = dimensionless_true - dimensionless_retrieved
        mask = np.vstack((delta < 0, delta >= 0)).T

        # get the principal semi-axes which define the error ellipse
        sigma_components = dimensionless_errors[mask]

        # UPDATE - since the redefinition of the precision metric, we no longer
        # need to find the intercept to calculate the precision metric
        # Find the intercept between the error ellipse and the line joining
        # the true and retrieved position
        #intercept = _find_intercept(dimensionless_true, dimensionless_retrieved, sigma_components)

        # The 1 sigma distance is the distance between this intercept and the
        # retrieved parameter values (note dropping the scale factor from
        # intercept)
        #sigma = distance.euclidean(dimensionless_retrieved, intercept[:-1])

        # Calculate the precision metric
        metric = np.sqrt(sum(((dimensionless_true - dimensionless_retrieved)/sigma_components) ** 2))
        metric_components = (dimensionless_true - dimensionless_retrieved)/sigma_components

        return metric, metric_components, #sigma

    def calculate_metrics(self, true_parameters, retrieved_parameters,
                          uncertainty):
        '''
        Calculates the accuracy and precision metrics

        Parameters
        ----------
        true_parameters : array_like, shape (n_parameters, )
            The accepted 'true' values of the parameters, provided in physical
            space (i.e. with units)
        retrieved_parameters : array_like, shape (n_parameters, )
            The retrieved values of the parameters, provided in physical space
            (i.e. with units)
        uncertainty : array_like, shape (n_parameters, ) or (n_parameters, 2)
            The uncertainy associated with each retrieved parameter value.
            If 1D array is provided, assumes uniform upper and lower errors.
            If 2D array provided, assumes errors are provided as(lower, upper)
            pairs.

        Returns
        -------
        accuracy_metric : float
            The Euclidean distance between the two given points
        precision_metric : float
            The precision metric associated with the retrieval results
        sigma : float
            The 1 sigma value in the direction of the vector between the true
            and retrieved parameters.

        '''
        accuracy, accuracy_components = self.calculate_accuracy_metric(true_parameters, retrieved_parameters)
        precision, precision_components, sigma = self.calculate_precision_metric(true_parameters, retrieved_parameters, uncertainty)

        return accuracy, accuracy_components, precision, precision_components, #sigma


def _intercept_eqn(p, true_pos, retr_pos, errors):
    '''
    Function to pass to fsolve to find the intercept between the
    line between the retrieved and true position and the one sigma
    error ellipsoid around the retrieved position
    '''

    A = p[-1] # Get the scalar
    p = np.array(p[:-1]) # Get the variable coordinates

    true_pos = np.asarray(true_pos)
    retr_pos = np.asarray(retr_pos)
    errors = np.asarray(errors)

    diff = retr_pos - true_pos

    line_results = p - true_pos - A*diff

    ellipsoid_result = sum((p - retr_pos)**2 / errors**2) - 1

    return tuple(line_results) + (ellipsoid_result, )


def _find_intercept(true_position, retrieved_position, errors):
    '''
    Finds the intercept between the line joining the true position
    and the retrieved position in parameter space and the error ellipsoid
    surrounding the retrieved position

    Parameters
    ----------
    true_position : array_like, shape (n_variables, )
        The set of accepted 'true' values for the variables
    retrieved_position : array_like, shape (n_variables, )
        The set of values for the variables found through retrieval

    '''
    start_pos = np.array(tuple(true_position) + (0.3,))

    return fsolve(_intercept_eqn, start_pos, args=(true_position, retrieved_position, errors))
