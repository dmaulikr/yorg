from ya2.gameobject import Logic
from panda3d.core import Vec3, Vec2, deg2Rad, Point3
import math


#camera constants
cam_speed = 50
cam_dist_min = 12
cam_dist_max = 18
cam_z_max = 5
cam_z_min = 3
look_dist_min = 2
look_dist_max = 6
look_z_max = 2
look_z_min = 0


class _Logic(Logic):
    '''This class manages the events of the Car class.'''

    def __init__(self, mdt):
        Logic.__init__(self, mdt)
        self.__steering = 0  # degrees
        self.last_time_start = 0
        self.last_roll_ok_time = None
        self.last_roll_ko_time = None
        self.lap_times = []
        self.start_left = None
        self.start_right = None

    def update(self, input_dct):
        '''This callback method is invoked on each frame.'''
        eng_frc = brake_frc = 0
        d_t = globalClock.getDt()
        steering_inc = d_t * self.mdt.phys.steering_inc
        steering_dec = d_t * self.mdt.phys.steering_dec

        speed_ratio = self.mdt.phys.speed_ratio
        steering_range = self.mdt.phys.steering_min_speed - self.mdt.phys.steering_max_speed
        steering_clamp = self.mdt.phys.steering_min_speed - speed_ratio * steering_range

        if input_dct['forward'] and input_dct['reverse']:
            eng_frc = self.mdt.phys.engine_acc_frc if self.mdt.phys.speed < self.mdt.phys.curr_max_speed else 0
            brake_frc = self.mdt.phys.brake_frc

        if input_dct['forward'] and not input_dct['reverse']:
            eng_frc = self.mdt.phys.engine_acc_frc if self.mdt.phys.speed < self.mdt.phys.curr_max_speed else 0
            brake_frc = 0

        if input_dct['reverse'] and not input_dct['forward']:
            eng_frc = self.mdt.phys.engine_dec_frc if self.mdt.phys.speed < .05 else 0
            brake_frc = self.mdt.phys.brake_frc

        if not input_dct['forward'] and not input_dct['reverse']:
            brake_frc = self.mdt.phys.eng_brk_frc

        if input_dct['left']:
            if self.start_left is None:
                self.start_left = globalClock.getFrameTime()
            dt = globalClock.getFrameTime() - self.start_left
            mul = min(1, dt / .1)
            self.__steering += steering_inc * mul
            self.__steering = min(self.__steering, steering_clamp)
        else:
            self.start_left = None

        if input_dct['right']:
            if self.start_right is None:
                self.start_right = globalClock.getFrameTime()
            dt = globalClock.getFrameTime() - self.start_right
            mul = min(1, dt / .1)
            self.__steering -= steering_inc * mul
            self.__steering = max(self.__steering, -steering_clamp)
        else:
            self.start_right = None

        if not input_dct['left'] and not input_dct['right']:
            if abs(self.__steering) <= steering_dec:
                self.__steering = 0
            else:
                steering_sign = (-1 if self.__steering > 0 else 1)
                self.__steering += steering_sign * steering_dec

        self.mdt.phys.set_forces(eng_frc, brake_frc, self.__steering)
        if game.track.fsm.getCurrentOrNextState() == 'Race':
            self.mdt.gui.speed_txt.setText(str(round(self.mdt.phys.speed, 2)))
        if not self.mdt.event.has_just_started:
            self.mdt.gui.time_txt.setText(str(round(
                globalClock.getFrameTime() - self.last_time_start, 2)))
        self.__update_roll_info()
        if game.track.gfx.waypoints:
            self.__update_wp()

    def __update_roll_info(self):
        if -45 <= self.mdt.gfx.nodepath.getR() < 45:
            self.last_roll_ok_time = globalClock.getFrameTime()
        else:
            self.last_roll_ko_time = globalClock.getFrameTime()

    def pt_line_dst(self, pt, line_pt1, line_pt2):
        diff1 = line_pt2.get_pos() - line_pt1.get_pos()
        diff2 = line_pt1.get_pos() - pt.get_pos()
        diff = abs(diff1.cross(diff2).length())
        return diff / abs((line_pt2.get_pos() - line_pt1.get_pos()).length())

    def closest_wp(self, pos=None):
        if pos:
            node = render.attachNewNode('pos node')
            node.set_pos(pos)
        else:
            node = self.mdt.gfx.nodepath
        waypoints = game.track.gfx.waypoints
        distances = [node.getDistance(wp) for wp in waypoints.keys()]
        curr_wp_idx = distances.index(min(distances))
        curr_wp = waypoints.keys()[curr_wp_idx]

        may_prev = waypoints[curr_wp]
        distances = []
        for wp in may_prev:
            distances += [self.pt_line_dst(node, wp, curr_wp)]
        prev_idx = distances.index(min(distances))
        prev_wp = may_prev[prev_idx]

        may_succ = [wp for wp in waypoints if curr_wp in waypoints[wp]]
        distances = []
        for wp in may_succ:
            distances += [self.pt_line_dst(node, curr_wp, wp)]
        next_idx = distances.index(min(distances))
        next_wp = may_succ[next_idx]

        curr_vec = Vec2(node.getPos(curr_wp).xy)
        curr_vec.normalize()
        prev_vec = Vec2(node.getPos(prev_wp).xy)
        prev_vec.normalize()
        next_vec = Vec2(node.getPos(next_wp).xy)
        next_vec.normalize()
        prev_angle = prev_vec.signedAngleDeg(curr_vec)
        next_angle = next_vec.signedAngleDeg(curr_vec)

        if abs(prev_angle) > abs(next_angle):
            start_wp = prev_wp
            end_wp = curr_wp
        else:
            start_wp = curr_wp
            end_wp = next_wp
        return start_wp, end_wp

    @property
    def current_wp(self):
        return self.closest_wp()

    @property
    def car_vec(self):
        car_rad = deg2Rad(self.mdt.gfx.nodepath.getH())
        car_vec = Vec3(-math.sin(car_rad), math.cos(car_rad), 1)
        car_vec.normalize()
        return car_vec

    @property
    def direction(self):
        start_wp, end_wp = self.current_wp
        wp_vec = Vec3(end_wp.getPos(start_wp).xy, 0)
        wp_vec.normalize()

        return self.car_vec.dot(wp_vec)

    def __update_wp(self):
        way_str = _('wrong way') if self.direction < -.6 else ''
        game.track.gui.way_txt.setText(way_str)

    def get_closest(self, pos, tgt=None):
        tgt = tgt or self.mdt.gfx.nodepath.getPos()
        result = eng.world_phys.rayTestClosest(pos, tgt)
        if result.hasHit():
            return result

    def update_cam(self):
        #eng.camera.setPos(self.mdt.gfx.nodepath.getPos())
        self.update_cam_fp()

    def update_cam_fp(self):
        speed_ratio = self.mdt.phys.speed_ratio
        cam_dist_diff = cam_dist_max - cam_dist_min
        look_dist_diff = look_dist_max - look_dist_min
        cam_z_diff = cam_z_max - cam_z_min
        look_z_diff = look_z_max - look_z_min
        #car_np = self.mdt.gfx.nodepath
        #car_rad = deg2Rad(car_np.getH())
        #car_vec = Vec3(-math.sin(car_rad), math.cos(car_rad), 1)
        #car_vec.normalize()

        fwd_vec = eng.render.getRelativeVector(self.mdt.gfx.nodepath, Vec3(0, 1, 0))
        fwd_vec.normalize()

        car_pos = self.mdt.gfx.nodepath.getPos()
        #cam_vec = -car_vec * (cam_dist_min + cam_dist_diff * speed_ratio)
        #tgt_vec = car_vec * (look_dist_min + look_dist_diff * speed_ratio)
        cam_vec = -fwd_vec * (cam_dist_min + cam_dist_diff * speed_ratio)
        tgt_vec = fwd_vec * (look_dist_min + look_dist_diff * speed_ratio)
        delta_pos_z = cam_z_max - cam_z_diff * speed_ratio
        delta_cam_z = look_z_min + look_z_diff * speed_ratio

        curr_pos = Point3(car_pos.x + cam_vec.x,
                          car_pos.y + cam_vec.y,
                          car_pos.z + cam_vec.z + delta_pos_z)
        curr_cam_fact = cam_dist_min + cam_dist_diff * speed_ratio
        def cam_cond(curr_pos):
            closest = self.get_closest(curr_pos)
            if closest:
                closest_str = closest.getNode().getName()
            if closest and closest_str not in ['Vehicle', 'Goal'] and \
                    curr_cam_fact > .1:
                return closest
        curr_hit = cam_cond(curr_pos)
        if curr_hit:
            hit_pos = curr_hit.getHitPos()
            cam_vec = Vec3(
                hit_pos.x - car_pos.x,
                hit_pos.y - car_pos.y,
                hit_pos.z - car_pos.z)

        #game.track.gui.debug_txt.setText(curr_hit.getNode().getName() if curr_hit else '')

        self.tgt_x = car_pos.x + cam_vec.x
        self.tgt_y = car_pos.y + cam_vec.y
        self.tgt_z = car_pos.z + cam_vec.z + delta_pos_z

        self.tgt_look_x = car_pos.x + tgt_vec.x
        self.tgt_look_y = car_pos.y + tgt_vec.y
        self.tgt_look_z = car_pos.z + tgt_vec.z

        curr_incr = cam_speed * globalClock.getDt()
        def new_pos(cam_pos, tgt):
            if abs(cam_pos - tgt) <= curr_incr:
                return tgt
            else:
                sign = 1 if tgt > cam_pos else -1
                return cam_pos + sign * curr_incr
        new_x = new_pos(eng.camera.getX(), self.tgt_x)
        new_y = new_pos(eng.camera.getY(), self.tgt_y)
        new_z = new_pos(eng.camera.getZ(), self.tgt_z)

        # overwrite camera's position to set the physics
        #new_x = car_pos.x + 10
        #new_y = car_pos.y - 5
        #new_z = car_pos.z + 5

        if not self.is_rolling:
            eng.camera.setPos(new_x, new_y, new_z)
        eng.camera.look_at(
            self.tgt_look_x, self.tgt_look_y, self.tgt_look_z + delta_cam_z)

    @property
    def is_upside_down(self):
        return globalClock.getFrameTime() - self.last_roll_ok_time > 5.0

    @property
    def is_rolling(self):
        try:
            return globalClock.getFrameTime() - self.last_roll_ko_time < 1.0
        except TypeError:
            return False
