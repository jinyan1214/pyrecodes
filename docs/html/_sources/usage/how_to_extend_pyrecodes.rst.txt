How to extend pyrecodes?
========================

pyrecodes is designed to be extensible and modular. Developers can extend the functionality of pyrecodes in the following ways:

- Connect pyrecodes to third-party damage simulators
- Add new components
- Add new component recovery models
- Add new or connect to existing third-party resource distribution models
- Add new resource allocation strategies
- Add new resilience calculators

This section details how to extend pyrecodes to:

- Connect pyrecodes to third-party damage simulators
- Connect pyrecodes to third-party resource distribution models

Connect pyrecodes to third-party damage simulators
---------------------------------------------------

To run pyrecodes recovery and resilience assessment, the user needs to provide damage states of components in the system. These damage states can be provided by a damage simulator. The term "damage simulator" refers to the software that follows the traditional regional risk assessment workflow, where hazard, exposure and vulnerability modules are combined to assess the damage states of components in the system following a scenario disaster. 

Several open-source damage simulators have been developed and are available for use (e.g., SimCenter's R2D, OpenQuake, CLIMADA). This section presents an overview of how pyrecodes is connected to SimCenter's R2D damage simulator using the damage_to_recovery API and points to the relevant pyrecodes modules. The aim is to detail the R2D-pyrecodes connection and provide a template for developers to connect pyrecodes to other damage simulators.

The damage simulator needs to provide two files to pyrecodes:

- **file containing component damage states** (e.g., damage.json)
- **file containing component characteristics** (e.g., exposure.json)

The two files are passed to the pyrecodes subsystem creator class to create components in the pyrecodes system. The subsystem creator class defined for R2D is in the pyrecodes/subsystem_creator/r2d_subsystem_creator.py module. JSON format is used to define the damage and exposure files for the R2D-pyrecodes API.

In addition to the subsystem creator class, a damage simulator needs to have its pyrecodes damage input class defined. This class assigns the damage states to the components once the recovery simulation is initiated. The damage input class for R2D is is in the pyrecodes/damage_input/r2d_damage_input.py module.

`Example 3 <./examples/example_3.html>`_, `Example 4 <./examples/example_4.html>`_ and `Example 5 <./examples/example_5.html>`_ illustrate how pyrecodes uses the output provided by the R2D's damage simulator.

.. figure:: ../figures/damage_recovery_api.png
        :alt: Connect pyrecodes to third-party damage simulators

        Third-party damage simulators can be connected to pyrecodes using the damage_to_recovery API. pyrecodes modules used to connect to the SimCenter's R2D damage simulator are outlined in the figure.


Connect pyrecodes to third-party resource distribution models
--------------------------------------------------------------

pyrecodes captures the interdependencies between components in the system by assessing how much of components' operation and recovery resource demand can be met by the components that provide the resources at each time step of the recovery simulation. To assess components' resource demand fulfillment, pyrecodes employes resource distribution models.

pyrecodes allows the integration of third-party resource distribution models using the "system to systems" API. The term "system" refers to a single subsystem (e.g., the water network) which is connected to the model containing multiple interdependent systems (e.g., a model of a city with the building stock, power system, transportation system, etc.).

Multiple terms are used interchangably to describe the resource distribution model, such as resource flow simulator or infrastructure simulator. They all serve the same purpose - assessing the component's resource demand fulfillment at a time step of the recovery simulation.

Resource distribution models are called at the "distribute resources" step of the pyrecodes recovery simulation. To call a third-party resource distribution model using the "system to systems" API, several classes need to be implemented connecting pyrecodes to the third-party resource distribution model. These are divided into simulator-independent and simulator-dependent classes. Although simulator-independent classes need to be defined for each third-party simulator they are almost identical and are used to instantiate and set up the third-party simulator in the pyrecodes model. The simulator-dependent class or classes need to be written for each third-party simulator and can be seen as wrappers around the third-party simulator.

Modules used to integrate the REWET water distribution model and the residual demand traffic distribution model are outlined in the figure below. Note that each resource distribution model in pyrecodes also requires a resource distribution model constructor class. The dictionary used to exchange information between simulator-independent and simulator-dependent modules follows the same structure as the exposure JSON file used in the damage-to-recovery API with a few minor modifications to fully capture the dynamic component's supply and demand.

`Example 5 <./examples/example_5.html>`_ illustrates the application of third-party infrastructure models in pyrecodes.


.. figure:: ../figures/system_to_systems_api.png
        :alt: Connect pyrecodes to third-party infrastructure simulators

        Third-party resource distribution models can be connected to pyrecodes using the system_to_systems API.