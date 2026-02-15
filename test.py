from flask import Flask, jsonify, render_template, request, redirect 
from pymavlink import  mavutil
from dronekit import connect, Command, LocationGlobalRelative, VehicleMode
import math

app = Flask(__name__)
try:
    vehicle = connect("tcp:127.0.0.1:14550", wait_ready=True)
    vehicle.wait_ready("autopilot_version")
    print("Berhasil Connect!")
except Exception as e:
    print(f"Gagal Connect, {e}")
    

@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        param1 = request.form.get('min_acc')
        try:
            if param1:
                vehicle.parameters['TKOFF_THR_MINACC'] = float(param1)
            print("Parameter berhasil diupdate ke Drone via MAVLink!")
        except Exception as e:
            print(f"Gagal update parameter: {e}")
        return render_template('app.html', param1=param1, mode=vehicle.mode.name, arm=vehicle.armed)
    else:
        p1 = vehicle.parameters.get('TKOFF_THR_MINACC', 0)
        return render_template("app.html", param1=p1, mode=vehicle.mode.name, arm=vehicle.armed)
    

@app.route("/get_all_params", methods=['GET'])
def get_all_params():
    try:
        params = {param: value for param, value in vehicle.parameters.items()}        
        return jsonify(params), 402
    except Exception as e:
        return jsonify(ok=False)

@app.route("/plane_status", methods=['GET'])
def cek_params():
    print(f"Autopilot Firmware version: {vehicle.version}")
    print(f"Autopilot capabilities (supports ftp): {vehicle.capabilities.ftp}")
    print(f"Global Location: {vehicle.location.global_frame}")
    print(f"Global Location (relative altitude): {vehicle.location.global_relative_frame}")
    print(f"Local Location: {vehicle.location.local_frame}") # NED
    print(f"Attitude: {vehicle.attitude}")
    print(f"Velocity: {vehicle.velocity}")
    print(f"GPS: {vehicle.gps_0}")
    print(f"Groundspeed: {vehicle.groundspeed}")
    print(f"Airspeed: {vehicle.airspeed}")
    print(f"Gimbal status: {vehicle.gimbal}")
    print(f"Battery: {vehicle.battery}")
    print(f"EKF OK?: {vehicle.ekf_ok}")
    print(f"Last Heartbeat: {vehicle.last_heartbeat}")
    print(f"Heading: {vehicle.heading}")
    print(f"Is Armable?: {vehicle.is_armable}")
    print(f"System status: {vehicle.system_status.state}")
    print(f"Current WP: {vehicle._current_waypoint}")
    print(f"Type: {vehicle.version.vehicle_type}")
    print(f"Mode: {vehicle.mode.name}")
    print(f"Armed: {vehicle.armed}")
    
    return redirect("/")

# Mengubah meter -> koordinat
def get_location_metres(original_location, dNorth, dEast):
    """
    Menghitung lokasi baru berdasarkan jarak (meter) dari lokasi awal.
    """
    earth_radius = 6378137.0 # Radius bumi dalam meter
    
    # Pergeseran koordinat dalam radian
    dLat = dNorth / earth_radius
    dLon = dEast / (earth_radius * math.cos(math.pi * original_location.lat / 180))

    # Lokasi baru dalam derajat
    newlat = original_location.lat + (dLat * 180 / math.pi)
    newlon = original_location.lon + (dLon * 180 / math.pi)
    
    return LocationGlobalRelative(newlat, newlon, original_location.alt)

@app.route("/wp", methods=['GET', 'POST'])
def wp():
    if request.method == 'POST':
        cmds = vehicle.commands
        cmds.download()
        cmds.wait_ready()
        cmds.clear()

        # Parameter: (target_sys, target_comp, seq, frame, command, current, autocontinue, p1, p2, p3, p4, lat, lon, alt)
        home_point = vehicle.home_location 
        # lon, lat
        cmd1 = Command(0, 0, 0, 
                    mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, 
                    mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 
                    0, 0, 0, 0, 0, 0, home_point.lat, home_point.lon, 10)

        target_wp = get_location_metres(home_point, -200, -300)
        cmd2 = Command(0, 0, 0, 
                    mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, 
                    mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 
                    0, 0, 0, 0, 0, 0, target_wp.lat, target_wp.lon, 20)
        
        target_wp = get_location_metres(home_point, 200, 100)
        
        cmd3 = Command(0, 0, 0, 
                        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, 
                        mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 
                        0, 0, 0, 0, 0, 0, 
                        target_wp.lat, target_wp.lon, 10)
        
        target_wp = get_location_metres(home_point, 0, 100)
        
        cmd4 = Command(0, 0, 0, 
                        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, 
                        mavutil.mavlink.MAV_CMD_NAV_LAND, 
                        0, 0, 0, 0, 0, 0, 
                        target_wp.lat, target_wp.lon, 5)
        cmds.add(cmd1)
        cmds.add(cmd2)
        cmds.add(cmd3)
        cmds.add(cmd4)

        print("Uploading missions...")
        cmds.upload() 

        try:
            return redirect('/')
        except Exception as e:
            return redirect('/')
    else:
        return redirect('/')

@app.route("/arm", methods=['GET', 'POST'])
def arm():
    if request.method == "POST":
        if vehicle.armed:
            vehicle.disarm()
            print("Berhasil Disarming!")
        else:
            vehicle.arm()
            print("Berhasil Arming!")
        return redirect('/')
    else:
        return redirect('/')
    
@app.route('/switch', methods=['GET', 'POST'])
def ganti_mode():
    if request.method == "POST":
        if vehicle.mode.name == "MANUAL":
            vehicle.mode = VehicleMode("AUTO")
            print("Berhasil AUTO!")
        else:
            vehicle.mode = VehicleMode("MANUAL")
            print("Berhasil MANUAL!")
        return redirect('/')
    else:
        return redirect('/')
    
app.run(debug=True)
