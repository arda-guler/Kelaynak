import numpy as np
import OpenGL
from OpenGL.GL import *
from OpenGL.GLU import *
import glfw
import time
import random
import keyboard as kbd

from rigidbody import *
from model import *
from graphics import *
from camera import *
from terrain import *
from ui import *
from scenery_objects import *
from sound import *
from alerts import *

def main():
    
    def window_resize(window, width, height):
        try:
            # glfw.get_framebuffer_size(window)
            glViewport(0, 0, width, height)
            glLoadIdentity()
            gluPerspective(fov, width/height, near_clip, far_clip)
            glTranslate(main_cam.pos[0], main_cam.pos[1], main_cam.pos[2])
            main_cam.orient = np.eye(3)
            main_cam.rotate([0, 180, 0])
        except ZeroDivisionError:
            # if the window is minimized it makes height = 0, but we don't need to update projection in that case anyway
            pass

    # INIT VESSELS
    print("Initializing vessels...")
    init_pos = np.array([0.0, 100.0, 0.0])          # m
    init_vel = np.array([0.0, 20.0, 0.0])            # m s-1
    init_accel = np.array([0.0, 0.0, 0.0])          # m s-2
    init_orient = np.array([[1.0, 0.0, 0.0],
                            [0.0, 1.0, 0.0],
                            [0.0, 0.0, 1.0]])
    init_ang_vel = np.array([0.0, 0.0, 0.0])        # rad s-1
    init_ang_accel = np.array([0.0, 0.0, 0.0])      # rad s-2
    init_mass = 1000                                # kg
    init_inertia = np.array([[5.0, 0.0, 0.0],
                             [0.0, 5.0, 0.0],
                             [0.0, 0.0, 10.0]])     # kg m2
    max_thrust = 20e3                               # N
    throttle_range = [60, 100]                      # %
    throttle = 100                                  # %
    prop_mass = 800                                 # kg
    mass_flow = 3                                   # kg s-1

    rocket_model = Model("rocket")
    init_CoM = np.array([0.0, 2.5, 0.0])

    KS = Rocket(rocket_model, init_CoM,
                init_pos, init_vel, init_accel,
                init_orient, init_ang_vel, init_ang_accel,
                init_mass, init_inertia,
                max_thrust, throttle_range, throttle,
                prop_mass, mass_flow)

    init_pos = np.array([0.0, 2000.0, 0.0])         # m
    init_vel = np.array([0.0, 0.0, 100.0])          # m s-1
    init_accel = np.array([0.0, 0.0, 0.0])          # m s-2
    init_orient = np.array([[1.0, 0.0, 0.0],
                            [0.0, 1.0, 0.0],
                            [0.0, 0.0, 1.0]])
    init_ang_vel = np.array([0.0, 0.0, 0.0])        # rad s-1
    init_ang_accel = np.array([0.0, 0.0, 0.0])      # rad s-2
    init_mass = 800                                 # kg
    init_inertia = np.array([[6000.0, 0.0, 0.0],
                             [0.0, 6000.0, 0.0],
                             [0.0, 0.0, 3000.0]])   # kg m2
    max_thrust = 5e3                               # N
    throttle_range = [0, 100]                       # %
    throttle = 100                                  # %
    prop_mass = 150                                 # kg
    mass_flow = 0.001                                # kg s-1

    plane_model = Model("plane_cockpit")
    init_CoM = np.array([0.0, 0.0, 2.0])

    cross_sections = np.array([8, 10, 2])            # m2
    Cds = np.array([0.6, 0.8, 0.1])
    Cl = 1.2
    
    # aileron, elevator, rudder
    control_effectiveness = np.array([0.6, 0.4, 0.15])
    
    AP = SimpleAircraft(plane_model, init_CoM,
                        init_pos, init_vel, init_accel,
                        init_orient, init_ang_vel, init_ang_accel,
                        init_mass, init_inertia,
                        max_thrust, throttle_range, throttle,
                        prop_mass, mass_flow,
                        cross_sections, Cds, Cl, control_effectiveness)
    AP.set_thrust_percent(80)

    bodies = [AP]

    # SCENERY OBJECTS
    print("Initializing scenery objects...")
    pylon_model = Model("pylon")
    pylon1 = SceneryObject(pylon_model, np.array([10,0,500]))
    pylon2 = SceneryObject(pylon_model, np.array([-10,0,500]))

    # scenery_objects = [pylon1, pylon2]
    scenery_objects = []

    # RANDOM BUILDINGS
    Nx = 100
    Nz = 100
    chance = 0.01
    building_spacing_x = 50
    building_spacing_z = 50

    building_area_corner_x = Nx / 2 * building_spacing_x
    building_area_corner_z = Nz / 2 * building_spacing_z

    buildings = []

    for idx_x in range(Nx):
        for idx_z in range(Nz):
            if random.uniform(0, 1) < chance:
                c_x = -building_area_corner_x + idx_x * building_spacing_x
                c_z = -building_area_corner_z + idx_z * building_spacing_z
                new_pos = np.array([c_x, 0, c_z])
                new_building = RandomBuilding(new_pos)
                scenery_objects.append(new_building)

    # TERRAIN
    print("Initializing terrain...")
    floor = Flatland(0, Color(0.1, 0.8, 0.1))

    # MISC PHYSICS
    gravity = np.array([0.0, -9.81, 0])

    # GRAPHICS
    print("Initializing graphics (OpenGL, glfw)...")
    window_x, window_y = 1600, 900
    fov = 70
    near_clip = 0.1
    far_clip = 10e6
    
    glfw.init()
    window = glfw.create_window(window_x, window_y, "Kelaynak Flight Simulator", None, None)
    glfw.set_window_pos(window, 100, 100)
    glfw.make_context_current(window)
    glfw.set_window_size_callback(window, window_resize)

    gluPerspective(fov, window_x/window_y, near_clip, far_clip)
    glClearColor(0, 0, 0.3, 1)

    # SOUND
    print("Initializing sound (pygame.mixer)...")
    init_sound()

    # CAMERA
    cam_pos = np.array([0, 0, 0])
    cam_orient = np.array([[-1, 0, 0],
                           [0, 1, 0],
                           [0, 0, -1]])
    main_cam = Camera("main_cam", cam_pos, cam_orient, True)

    glRotate(-180, 0, 1, 0)    
    main_cam.lock_to_target(bodies[0])

    def move_cam(movement):
        main_cam.move(movement)

    def rotate_cam(rotation):
        main_cam.rotate(rotation)

    # CAMERA CONTROLS
    cam_pitch_up = "K"
    cam_pitch_dn = "I"
    cam_yaw_left = "J"
    cam_yaw_right = "L"
    cam_roll_cw = "O"
    cam_roll_ccw = "U"

    cam_move_fwd = "Y"
    cam_move_bck = "H"
    cam_move_left = "N"
    cam_move_right = "M"
    cam_move_up = "Y"
    cam_move_dn = "H"

    plane_pitch_up = "S"
    plane_pitch_dn = "W"
    plane_roll_ccw = "Q"
    plane_roll_cw = "E"
    plane_yaw_right = "D"
    plane_yaw_left = "A"
    plane_throttle_up = "Z"
    plane_throttle_dn = "X"

    first_person_ui = True

    cam_speed = 100
    cam_rot_speed = 100

    play_sfx("turbojet_fan", -1, 1, 0)
    play_sfx("wind1", -1, 2, 0)
    play_sfx("rumble", -1, 3, 0)

    print("Starting...")
    dt = 0
    while not glfw.window_should_close(window):
        t_cycle_start = time.perf_counter()
        glfw.poll_events()

        ctrl_state = [0, 0, 0]

        # CONTROLS
        if kbd.is_pressed(cam_move_fwd):
            move_cam([0, 0, cam_speed * dt])
        if kbd.is_pressed(cam_move_bck):
            move_cam([0, 0, -cam_speed * dt])
        if kbd.is_pressed(cam_move_up):
            move_cam([0, -cam_speed * dt, 0])
        if kbd.is_pressed(cam_move_dn):
            move_cam([0, cam_speed * dt, 0])
        if kbd.is_pressed(cam_move_right):
            move_cam([-cam_speed * dt, 0, 0])
        if kbd.is_pressed(cam_move_left):
            move_cam([cam_speed * dt, 0, 0])

        if kbd.is_pressed(cam_pitch_up):
            rotate_cam([cam_rot_speed * dt, 0, 0])
        if kbd.is_pressed(cam_pitch_dn):
            rotate_cam([-cam_rot_speed * dt, 0, 0])
        if kbd.is_pressed(cam_yaw_left):
            rotate_cam([0, cam_rot_speed * dt, 0])
        if kbd.is_pressed(cam_yaw_right):
            rotate_cam([0, -cam_rot_speed * dt, 0])
        if kbd.is_pressed(cam_roll_cw):
            rotate_cam([0, 0, cam_rot_speed * dt])
        if kbd.is_pressed(cam_roll_ccw):
            rotate_cam([0, 0, -cam_rot_speed * dt])

        if kbd.is_pressed(plane_pitch_up):
            AP.elevator(1)
            ctrl_state[1] = 1
        elif kbd.is_pressed(plane_pitch_dn):
            AP.elevator(-1)
            ctrl_state[1] = -1

        if kbd.is_pressed(plane_roll_ccw):
            AP.aileron(1)
            ctrl_state[0] = 1
        elif kbd.is_pressed(plane_roll_cw):
            AP.aileron(-1)
            ctrl_state[0] = -1

        if kbd.is_pressed(plane_yaw_right):
            AP.rudder(1)
            ctrl_state[2] = 1
        elif kbd.is_pressed(plane_yaw_left):
            AP.rudder(-1)
            ctrl_state[2] = -1

        if kbd.is_pressed(plane_throttle_up):
            AP.update_throttle(30, dt)
        elif kbd.is_pressed(plane_throttle_dn):
            AP.update_throttle(-30, dt)

        # PHYSICS
        
        AP.drain_fuel(dt)
        AP.apply_aero_torque()
        AP.apply_angular_drag()
        AP.apply_drag()
        AP.apply_lift()
        AP.apply_thrust()
        G = np.linalg.norm(AP.accel) / 10
        AP.apply_accel(gravity)
        AP.update(dt)

        AoA = np.arccos(max(min(np.dot(AP.vel, AP.orient[2]) / np.linalg.norm(AP.vel), 1), -1))
        AoA = np.rad2deg(AoA)

        # hit flat ground
        for b in bodies:
            if b.pos[1] < floor.height:
                b.pos[1] = 0
                b.vel[1] = 0
                b.vel = b.vel - b.vel * 0.05 * dt

        main_cam.move_with_lock(dt)
        main_cam.rotate_with_lock(dt)

        # GRAPHICS
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        drawScene(main_cam, floor, bodies, scenery_objects, ctrl_state, first_person_ui)
        
        alt_string = "Alt: " + str(int(AP.pos[1]))
        vel_string = "Vel: " + str(int(np.linalg.norm(AP.vel)))
        throttle_str = "Throttle: " + str(int(AP.throttle))
        AoA_str = "AOA: " + str(round(AoA, 2))
        G_str = "G: " + str(round(G, 2))

        magenta = Color(1, 0, 1)
        red = Color(1, 0, 0)
        
        AoA_color = magenta
        G_color = magenta
        vel_color = magenta
        alt_color = magenta
        throttle_color = magenta

        if np.linalg.norm(AP.vel) < 50 and AoA > 10:
            vel_color = red
            AoA_color = red
            if AP.throttle < 100:
                throttle_color = red

        if G > 9:
            G_color = red

        if AP.pos[1] < 1000 and AP.vel[1] < 0 and AP.pos[1] / -AP.vel[1] < 3:
            alt_color = red
        
        render_AN(alt_string, alt_color, [4, 5], main_cam, fpu=first_person_ui)
        render_AN(vel_string, vel_color, [-7, 5], main_cam, fpu=first_person_ui)
        render_AN(throttle_str, throttle_color, [-7, -4.5], main_cam, fpu=first_person_ui)
        render_AN(AoA_str, AoA_color, [-7, -5.5], main_cam, fpu=first_person_ui)
        render_AN(G_str, G_color, [-7, -5], main_cam, fpu=first_person_ui)
        
        glfw.swap_buffers(window)
        
        set_channel_volume(1, AP.throttle / 100 * 0.5) # engine
        set_channel_volume(2, min(np.linalg.norm(AP.vel) / 500, 1) * 0.5) # airflow
        set_channel_volume(3, min(G / 10, 1) * 0.5) # airflow disturbance

        do_warnings(AP, AoA, G)

        dt = time.perf_counter() - t_cycle_start

    glfw.destroy_window(window)
    stop_channel(1)
    stop_channel(2)
    stop_channel(3)

main()
