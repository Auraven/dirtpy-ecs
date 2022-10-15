# dirtpy-ecs

get it with: pip install dirtpy

Check out the examples.

This ECS makes use of 4 classes, Entity, EntityComponent, EntityInstance, and EntitySystem to manage data and runtime operations.

The EntityComponent and EntityInstance class inherit from pydantic allowing all spawned instances and their components to be saved to and loaded from a .json file.

The Entity class is the blueprint for the entity instance and defines the component types to added to the instance. The Entity class can also contain global EntityComponents that are accessible by all of their instances.

EntityInstances can be named or tagged to reference a single, or group of instances

EntitySystems can be updated every frame or in intervals by setting the tickrate as well as being given priority to easily arrange execution order
