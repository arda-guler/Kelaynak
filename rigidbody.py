import numpy as np
from scipy.spatial.transform import Rotation

class RigidBody:
    def __init__(self, model, CoM, pos, vel, accel, orient, ang_vel, ang_accel, mass, inertia):
        self.model = model
        for idx_v, v in enumerate(self.model.vertices):
            self.model.vertices[idx_v] = v - CoM
        self.CoM = CoM
        self.pos = pos
        self.vel = vel
        self.accel = accel
        self.orient = orient
        self.ang_vel = ang_vel
        self.ang_accel = ang_accel
        self.mass = mass
        self.inertia = inertia

    # shifts center of mass
    def shift_CoM(self, shift):
        for idx_v, v in enumerate(self.model.vertices):
            self.model.vertices[idx_v] = v - shift

        self.CoM = self.CoM - shift

    def update_mass(self, mdot, dt):
        self.mass += mdot * dt

    def apply_torque(self, torque):
        inertia_inverse = np.linalg.inv(self.inertia)
        accel = np.dot(inertia_inverse, torque)
        self.ang_accel = self.ang_accel + accel

    def apply_force(self, force):
        accel = force / self.mass
        self.accel = self.accel + accel

    def apply_accel(self, accel):
        self.accel = self.accel + accel

    def rotate(self, dt):
        if np.linalg.norm(self.ang_vel) > 0:
            # Ensure the angular velocity is a column vector
            # angular_velocity = self.ang_vel.reshape(3, 1)
            axis = self.ang_vel / np.linalg.norm(self.ang_vel)
            angle_rad = np.linalg.norm(self.ang_vel) * dt

            rotation = Rotation.from_rotvec(angle_rad * axis)
    
            # Convert the rotation to a rotation matrix
            rotation_matrix = rotation.as_matrix()
    
            # Multiply the original orientation matrix by the rotation matrix
            self.orient = np.dot(rotation_matrix, self.orient)

            self.orient[0] = self.orient[0] / np.linalg.norm(self.orient[0])
            self.orient[1] = self.orient[1] / np.linalg.norm(self.orient[1])
            self.orient[2] = self.orient[2] / np.linalg.norm(self.orient[2])

    def clear_accels(self):
        self.accel = np.array([0, 0, 0])
        self.ang_accel = np.array([0, 0, 0])

    def update(self, dt):
        self.vel = self.vel + self.accel * dt
        self.pos = self.pos + self.vel * dt
        self.ang_vel = self.ang_vel + self.ang_accel * dt
        self.rotate(dt)
        self.clear_accels()

class Rocket(RigidBody):
    def __init__(self, model, CoM, pos, vel, accel, orient, ang_vel, ang_accel, mass, inertia,
                 max_thrust, throttle_range, throttle, prop_mass, mass_flow):
        super(Rocket, self).__init__(model, CoM, pos, vel, accel, orient, ang_vel, ang_accel, mass, inertia)
        self.max_thrust = max_thrust
        self.throttle_range = throttle_range
        self.throttle = throttle
        self.prop_mass = prop_mass
        self.mass_flow = mass_flow

        self.thrust = self.throttle / 100 * self.max_thrust

    def drain_fuel(self, dt):
        self.update_mass(-self.mass_flow * self.throttle / 100, dt)

    def apply_thrust(self):
        self.apply_force(self.orient[1] * self.thrust)

    def set_thrust_percent(self, percentage):
        if not percentage == 0:
            percentage = max(min(self.throttle_range[1], percentage), self.throttle_range[0])
        self.throttle = percentage
        self.thrust = self.max_thrust * percentage / 100

class SimpleAircraft(RigidBody):
    def __init__(self, model, CoM, pos, vel, accel, orient, ang_vel, ang_accel, mass, inertia,
                 max_thrust, throttle_range, throttle, prop_mass, mass_flow,
                 cross_sections, Cds, Cdas, angular_damping, Cl, 
                 control_effectiveness):
        super(SimpleAircraft, self).__init__(model, CoM, pos, vel, accel, orient, ang_vel, ang_accel, mass, inertia)
        self.max_thrust = max_thrust
        self.throttle_range = throttle_range
        self.throttle = throttle
        self.prop_mass = prop_mass
        self.mass_flow = mass_flow
        self.cross_sections = cross_sections
        self.Cds = Cds
        self.Cdas = Cdas
        self.angular_damping = angular_damping # this is for the complicated aero effects which I can not simulate using the single body model
        self.Cl = Cl
        self.control_effectiveness = control_effectiveness

        self.aero_resistance = np.multiply(self.cross_sections, self.Cds)
        self.angular_resistance = np.multiply(self.cross_sections, self.Cdas)

        self.thrust = self.throttle / 100 * self.max_thrust

    def drain_fuel(self, dt):
        self.update_mass(-self.mass_flow * self.throttle / 100, dt)
        self.prop_mass = self.prop_mass - self.mass_flow * self.throttle / 100 * dt
        if self.prop_mass <= 0:
            self.prop_mass = 0
            self.thrust = 0

    def apply_thrust(self):
        self.apply_force(self.orient[2] * self.thrust)

    def set_thrust_percent(self, percentage):
        if not percentage == 0:
            percentage = max(min(self.throttle_range[1], percentage), self.throttle_range[0])
        self.throttle = percentage
        self.thrust = self.max_thrust * percentage / 100

    def apply_aero_torque(self):
        vel_mag = np.linalg.norm(self.vel)
        if vel_mag:
            torque_x = np.dot(self.orient[1], self.vel) * vel_mag * self.Cdas[0]
            torque_y = -np.dot(self.orient[0], self.vel) * vel_mag * self.Cdas[1]

            self.apply_torque(np.array([torque_x, torque_y, 0]))

    def apply_angular_drag(self, dt):
        drag_vector = self.ang_vel * np.linalg.norm(self.ang_vel)
        drag_multiplier = abs(np.dot(drag_vector, self.orient[0] * self.angular_resistance[1])) + abs(np.dot(drag_vector, self.orient[1] * self.angular_resistance[0])) + abs(np.dot(drag_vector, self.orient[2] * self.angular_resistance[2]))
        drag_vector = -drag_vector * drag_multiplier**2
        self.apply_torque(drag_vector)

        # this is placeholder for the complicated aero effects which I can not simulate using the single body model
        self.ang_vel[0] = self.ang_vel[0] * (1 - self.angular_damping[0] * dt)
        self.ang_vel[1] = self.ang_vel[1] * (1 - self.angular_damping[1] * dt)
        self.ang_vel[2] = self.ang_vel[2] * (1 - self.angular_damping[2] * dt)

    def apply_lift(self):
        if np.linalg.norm(self.vel) > 0:
            vel_mag = np.linalg.norm(self.vel)
            AoA = np.arccos(max(min(np.dot(self.vel, self.orient[2]) / vel_mag, 1), -1))
            AoA = np.rad2deg(AoA)

            if abs(AoA) < 20:
                lift_multiplier = AoA / 20
                if np.dot(self.orient[1], self.vel) > 0:
                    lift_multiplier = lift_multiplier * -1
            elif abs(AoA) < 40:
                lift_multiplier = abs(AoA - 20) / 20
                if np.dot(self.orient[1], self.vel) > 0:
                    lift_multiplier = lift_multiplier * -1
            else:
                return

            force_vec = self.orient[1] - (self.vel / vel_mag) * np.dot(self.orient[1], self.vel / vel_mag)
            if np.linalg.norm(force_vec) > 0:
                force_vec = force_vec / np.linalg.norm(force_vec)
                force =  lift_multiplier * self.Cl * 0.5 * self.cross_sections[1] * vel_mag**2

                force_vec = force_vec * force

                self.apply_force(force_vec)
                
    def apply_drag(self):
        if np.linalg.norm(self.vel) > 0:
            drag_vector = -self.vel / np.linalg.norm(self.vel)
            drag_multiplier = abs(np.dot(drag_vector, self.orient[0] * self.aero_resistance[0])) + abs(np.dot(drag_vector, self.orient[1] * self.aero_resistance[1])) + abs(np.dot(drag_vector, self.orient[2] * self.aero_resistance[2]))
            drag_amount = 0.5 * drag_multiplier * np.linalg.norm(self.vel)**2
            force_vec = drag_vector * drag_amount
            self.apply_force(force_vec)

    def aileron(self, direction):
        self.apply_torque(np.array([0, 0, 1]) * direction * np.linalg.norm(self.vel)**2 * self.control_effectiveness[0])

    def elevator(self, direction):
        self.apply_torque(np.array([1, 0, 0]) * direction * np.linalg.norm(self.vel)**2 * self.control_effectiveness[1])

    def rudder(self, direction):
        self.apply_torque(np.array([0, 1, 0]) * direction * np.linalg.norm(self.vel)**2 * self.control_effectiveness[2])

    def update_throttle(self, direction, dt):
        self.throttle = self.throttle + direction * dt
        self.throttle = max(min(self.throttle_range[1], self.throttle), self.throttle_range[0])
        self.thrust = self.throttle / 100 * self.max_thrust
