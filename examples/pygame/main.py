from dirtpy import ecs as world
from dirtpy.ecs import Entity, EntityComponent, EntityInstance, EntitySystem

import pygame
import sys
from pygame.locals import *
import random
import math

#pygame Setup
pygame.init()

FPS = 60
FramePerSec = pygame.time.Clock()

# Predefined some colors
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Screen information
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600

DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
DISPLAYSURF.fill(BLACK)
pygame.display.set_caption("dirtpy")

#ECS Setup
class Transform(EntityComponent):
    x: float
    y: float

class Velocity(EntityComponent):
    x: float
    y: float

class Square(EntityComponent):
    layer: int
    color: tuple
    width: float
    height: float

class Spawner(EntityComponent):
    entity_name: str
    spawn_rate: float
    spawn_clock: float

class RenderSystem(EntitySystem):
    def __init__(self, *component_types: type[EntityComponent], surface: pygame.Surface):
        self.render_layers: dict[int, list[str]] = None
        self.surface: pygame.Surface = surface
        super().__init__(*component_types)

    def update(self, entity_instances: dict[Entity, list[EntityInstance]], delta_time: float):
        self.surface.fill(BLACK)
        for layer, entity_names in self.render_layers.items():
            for entity_name in entity_names:
                entity = world.entity_dict[entity_name]        
                square: Square = entity.get_global_component(Square)                    
                for instance in entity_instances[entity]:
                    trans: Transform = instance.get_component(Transform)                  
                    pygame.draw.rect(self.surface, square.color, [trans.x, trans.y, square.width, square.height])
        
        font = pygame.font.SysFont(None, 24)
        img = font.render(f'FPS: {int(FramePerSec.get_fps())}, Bullet Instances: {len(world.get_tagged("bullet"))}', True, WHITE)
        self.surface.blit(img, (20, 20))

    def on_enable(self, entity_names: list[str]):         
        if self.render_layers is None:
            self.render_layers = {}
            for entity_name in entity_names:
                entity: Entity = world.entity_dict[entity_name]
                square: Square = entity.get_global_component(Square)
                if square.layer not in self.render_layers:
                    self.render_layers[square.layer] = []
                self.render_layers[square.layer].append(entity_name)

class MovementSystem(EntitySystem):
    def update(self, entity_instances: dict[Entity, list[EntityInstance]], delta_time: float):
        for entity, instances in entity_instances.items():
            for instance in instances:
                trans: Transform = instance.get_component(Transform)
                vel: Velocity = instance.get_component(Velocity)
                trans.x += vel.x*delta_time
                trans.y += vel.y*delta_time

class SpawnSystem(EntitySystem):
    def update(self, entity_instances: dict[Entity, list[EntityInstance]], delta_time: float):
        for entity, instances in entity_instances.items():
            for instance in instances:
                trans: Transform = instance.get_component(Transform)
                spawner: Spawner = instance.get_component(Spawner)

                spawner.spawn_clock += delta_time
                if spawner.spawn_clock >= spawner.spawn_rate:
                    spawner.spawn_clock = 0
                    world.spawn(spawner.entity_name).get_component(Transform).copy(trans)

def bullet_on_spawn(entity: Entity, instance: EntityInstance):
    vel: Velocity = instance.get_component(Velocity)
    angle: float = math.radians((random.random()*360))
    vel.x = math.cos(angle)*100
    vel.y = math.sin(angle)*100

#register
world.register_component(Transform(x=0, y=0))
world.register_component(Velocity(x=0, y=0))
world.register_component(Square(layer=4, color=RED, width=32, height=32))
world.register_component(Spawner(entity_name='bullet', spawn_rate=1, spawn_clock=0))

world.register_entity(Entity('bullet', Transform, Velocity, global_components=[Square(layer=4, color=RED, width=32, height=32)], on_spawn=bullet_on_spawn))
world.register_entity(Entity('bullet_spawner', Transform, Spawner))

world.register_system(RenderSystem(Transform, Square, surface=DISPLAYSURF), tickrate=(1/FPS), priority=0)
world.register_system(SpawnSystem(Transform, Spawner))
world.register_system(MovementSystem(Transform, Velocity))

world.pool()

bullet_spawner = world.spawn('bullet_spawner')
spawner: Spawner = bullet_spawner.get_component(Spawner)
spawner.spawn_rate = 0
trans: Transform = bullet_spawner.get_component(Transform)
trans.x = SCREEN_WIDTH/2 - 16
trans.y = SCREEN_WIDTH/2 - 16

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
            
    time_ms = FramePerSec.tick()
    world.update(time_ms/1000)
    pygame.display.update()    