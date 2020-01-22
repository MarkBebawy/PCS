## Class HodgkinHuxley implementing functions for setting all variables,
## and for creating, solving and plotting the corresponding
## differential equation (of the Hodgkin-Huxley model).

import numpy as np
import matplotlib.pyplot as plt
import tools

class HodgkinHuxley:
    """
    Class which stores parameters of HH model.

    Attributes:
    C: Membrane capacitance (uF/cm^2)
    I: Applied current, assumed constant (nA)
    V0: Applied voltage at starting time (mV)
    n0: Initial probability of K gate being open
    m0: Initial probability of Na gate being open
    h0: Initial probability of Na gate being inactivated
    V_Na, v_K, v_L: Reverse potential of Na / K / leakage channel (mV)
    g_Na, g_K, g_L: Maximum Na / K / leakage conductance (mS/cm^2)
    phi: Factor for temperature correction
    a_n, a_m, a_h: Opening rate of m, n, h gates (ms)^-1
    b_n, b_m, b_h: Closing rate om m, n, h gates (ms)^-1
    """
    def __init__(self, T=6.3):
        """Initialises variables of model, takes temperature as input with T = 6.3 as standard temperature."""
        self.C = 1
        self.V0 = -65
        self.n0 = 0.317
        self.m0 = 0.05
        self.h0 = 0.6
        self.V_Na = 50
        self.V_K = -77
        self.V_L = -54.4
        self.g_Na = 120
        self.g_K = 36
        self.g_L = 0.3
        self.V_eq = -65

        # Set parameters that can be changed by GUI.
        self.run_time = 10
        self.quick = False
        self.num_method_time_steps = 0.0001

        # Set parameters that can be changed by GUI and are meant for simulating
        # one aciton potential.
        self.temperature = T
        self.inject_current = 20
        self.inj_start_time = 3
        self.inj_end_time = 4

        # Calculate factor for temperature correction which is used for opening and closing rates.
        self.phi = 3 ** ((self.temperature - 6.3) / 10)
        self.a_n = lambda V : self.phi * (0.01 * (-V + self.V_eq + 10) / (np.exp((-V + self.V_eq + 10)/10) - 1))
        self.a_m = lambda V : self.phi * (0.1 * (-V + self.V_eq + 25) / (np.exp((-V + self.V_eq + 25)/10) - 1))
        self.a_h = lambda V : self.phi * 0.07 * np.exp((-V + self.V_eq)/20)
        self.b_n = lambda V : self.phi * 0.125 * np.exp((-V + self.V_eq)/80)
        self.b_m = lambda V : self.phi * 4 * np.exp((-V + self.V_eq)/18)
        self.b_h = lambda V : self.phi / (np.exp(((-V + self.V_eq) + 30)/10) + 1)
        self.I_L = lambda V : self.g_L * (V - self.V_L)
        self.I_K = lambda V, n :  self.g_K * n ** 4 * (V - self.V_K)
        self.I_Na = lambda V, m, h : self.g_Na * m ** 3 * h * (V - self.V_Na)

        # Results, to be plotted...
        self.results = ([], [])

    def I(self, t):
        """Injected current as a function of time in nA/cm^2. """
        return self.inject_current * (self.inj_start_time < t and t < self.inj_end_time)

    def diff_eq(self):
        """Returns function f such that the differential equations can be described as x' = f(t, x),
        where x = [V, n, m, h]. Note that the first argument is not used (rk4 requires f to be a function of time, but
        we do not need this)."""
        def f(t, x):
            V, n, m, h = x
            y = np.zeros(4)
            y[0] = (self.I(t) - self.I_K(V, n) - self.I_Na(V, m, h) - self.I_L(V)) / self.C
            y[1] = self.a_n(V) * (1 - n) - self.b_n(V) * n
            y[2] = self.a_m(V) * (1 - m) - self.b_m(V) * m
            y[3] = self.a_h(V) * (1 - h) - self.b_h(V) * h
            return y
        return f

    def set_temperature(self, T):
        """Setter for the temperature of the model."""
        self.temperature = T
        self.phi = 3 ** ((self.temperature - 6.3) / 10)
        self.a_n = lambda V : self.phi * (0.01 * (-V + self.V_eq + 10) / (np.exp((-V + self.V_eq + 10)/10) - 1))
        self.a_m = lambda V : self.phi * (0.1 * (-V + self.V_eq + 25) / (np.exp((-V + self.V_eq + 25)/10) - 1))
        self.a_h = lambda V : self.phi * 0.07 * np.exp((-V + self.V_eq)/20)
        self.b_n = lambda V : self.phi * 0.125 * np.exp((-V + self.V_eq)/80)
        self.b_m = lambda V : self.phi * 4 * np.exp((-V + self.V_eq)/18)
        self.b_h = lambda V : self.phi / (np.exp(((-V + self.V_eq) + 30)/10) + 1)
        self.I_L = lambda V : self.g_L * (V - self.V_L)
        self.I_K = lambda V, n :  self.g_K * n ** 4 * (V - self.V_K)
        self.I_Na = lambda V, m, h : self.g_Na * m ** 3 * h * (V - self.V_Na)

    def set_run_time(self, time):
        """Setter for the run time of the model."""
        self.run_time = time

    def set_injection_data(self, inj_current, inj_start, inj_end):
        """Setter for inject_current, inj_start_time, inj_end_time."""
        self.inject_current = inj_current
        self.inj_start_time = inj_start
        self.inj_end_time = inj_end

    def set_num_method(self, quick, steps):
        """Setter for numerical method (quick=False --> RK4, quick=True --> Forward Euler)
        and for time steps used by that method."""
        self.quick = quick
        self.num_method_time_steps = steps

    def solve_model(self, h=None, t=None, quick=None):
        """Solves the model using RK4 with step size h, for time (at least) t.
        If quick paramter is true then forward Euler is used."""
        # Default values for parameters.
        if h is None:
            h = self.num_method_time_steps
        if t is None:
            t = self.run_time
        if quick is None:
            quick = self.quick

        # Calculate number of steps, differential equation and solve it.
        N = np.int(np.ceil(t/h))
        f = self.diff_eq()
        y0 = np.array([self.V0, self.n0, self.m0, self.h0])
        if quick:
            sol = tools.fe(f, 0, y0, h, N)
        else:
            sol = tools.rk4(f, 0, y0, h, N)

        self.results = sol
        return sol

    def plot_results(self):
        """This function plots the results of an action potential plot."""
        t, y = self.results
        assert len(t) == len(y[:,0])
        title = (f"One neuron action potential. Voltage plotted against "
        f"time, using temperature {self.temperature} degrees, "
        f"injecting {self.inject_current} mV current "
        f"from {self.inj_start_time} ms to {self.inj_end_time} ms. "
        f"Numerical method {'Runge-Kutta-4' if self.quick == 0 else 'Forward-Euler'} "
        f"with time steps {self.num_method_time_steps}.")

        plt.title(title, wrap=True)
        plt.xlabel("Time (ms)")
        plt.ylabel("Voltage (mV)")
        plt.plot(t, y[:,0], c='red')
        plt.show()
