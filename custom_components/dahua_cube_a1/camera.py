"""Dahua Cube A1 camera class using the NetSDK wrapper."""

import ctypes
import time
from queue import Queue

from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Struct import *
from NetSDK.SDK_Enum import *
from NetSDK.SDK_Callback import fDisConnect, fHaveReConnect, CB_FUNCTYPE


# Dahua alarm constants for SmartMotionHuman (only these two will be processed)
DH_ALARM_SMARTMOTION_HUMAN_START = 0x3015
DH_ALARM_SMARTMOTION_HUMAN_STOP  = 0x218F


class Camera:
    """Represents a single Dahua Cube A1 camera."""

    def __init__(self, ip: str, username: str, password: str, name: str = "Dahua Camera", index: int = 0):
        self.ip = ip
        self.username = username
        self.password = password
        self.name = name
        self.index = index
        self.port = 37777
        self.login_id = 0
        self.sdk = NetClient()
        self.event_queue = Queue()
        self._running = False
        self._userdata = ctypes.py_object(self)  # strong reference

        # Register callbacks
        disconnect_cb = fDisConnect(self._disconnect_callback)
        reconnect_cb = fHaveReConnect(self._reconnect_callback)
        self.sdk.InitEx(disconnect_cb)
        self.sdk.SetAutoReconnect(reconnect_cb)

        dw_user = ctypes.cast(ctypes.byref(self._userdata), ctypes.c_void_p).value
        self.sdk.SetDVRMessCallBackEx1(self._message_callback, dw_user)
        print(f"Camera {self.name} initialized (IP: {self.ip})")

    def _disconnect_callback(self, l_login_id, pch_dvr_ip, n_dvr_port, dw_user):
        print(f"Camera {self.name} disconnected")

    def _reconnect_callback(self, l_login_id, pch_dvr_ip, n_dvr_port, dw_user):
        print(f"Camera {self.name} reconnected")

    @CB_FUNCTYPE(None, ctypes.c_long, ctypes.c_longlong, ctypes.POINTER(ctypes.c_char), ctypes.c_ulong,
                 ctypes.POINTER(ctypes.c_char), ctypes.c_long, ctypes.c_int, ctypes.c_long, ctypes.c_ulonglong)
    def _message_callback(l_command, l_login_id, p_buf, dw_buf_len, pch_dvr_ip, n_dvr_port,
                          b_alarm_ack_flag, n_event_id, dw_user):
        """Process ONLY SmartMotionHuman Start (0x3015) and Stop (0x2815)."""
        print(f"Callback triggered! Command: 0x{l_command:X}")
        if not dw_user:
            return
        try:
            py_obj = ctypes.cast(dw_user, ctypes.POINTER(ctypes.py_object)).contents.value

            if l_command == DH_ALARM_SMARTMOTION_HUMAN_START:
                code = "SmartMotionHuman"
                action = "Start"
                print(f"✅ SmartMotionHuman Start on {py_obj.name}")
            elif l_command == DH_ALARM_SMARTMOTION_HUMAN_STOP:
                code = "SmartMotionHuman"
                action = "Stop"
                print(f"✅ SmartMotionHuman Stop on {py_obj.name}")
            else:
                return  # ignore everything else (including 0x2102)

            event = {
                "code": code,
                "action": action,
                "index": py_obj.index,
                "data": {
                    "LocaleTime": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "Name": py_obj.name
                }
            }
            py_obj.event_queue.put(event)
        except Exception as e:
            print(f"Callback error: {e}")

    def login(self) -> bool:
        stu_in = NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stu_in.dwSize = ctypes.sizeof(NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY)
        stu_in.szIP = self.ip.encode()
        stu_in.nPort = self.port
        stu_in.szUserName = self.username.encode()
        stu_in.szPassword = self.password.encode()
        stu_in.emSpecCap = EM_LOGIN_SPAC_CAP_TYPE.TCP

        stu_out = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stu_out.dwSize = ctypes.sizeof(NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY)

        self.login_id, _, error = self.sdk.LoginWithHighLevelSecurity(stu_in, stu_out)
        if self.login_id == 0:
            print(f"❌ Login failed for {self.name}: {error}")
            return False

        print(f"✅ Login successful for {self.name}")
        self._running = True
        success = self.sdk.StartListenEx(self.login_id) > 0
        print(f"Alarm listening started: {success}")
        return success

    def logout(self):
        if self.login_id == 0:
            return
        self.sdk.StopListen(self.login_id)
        self.sdk.Logout(self.login_id)
        self.login_id = 0
        self._running = False