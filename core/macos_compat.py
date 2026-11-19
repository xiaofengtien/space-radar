"""
macOS 原生兼容层：注入进程显示名、Cocoa Bundle 标识与 Dock 提示
"""
import sys
import os

def setup_macos_app_identity(display_name: str, app_name: str = "SpaceRadar"):
    """
    在 macOS 运行时无侵入注入应用显示名，使 Dock 悬浮提示与活动监视器显示真实产品名而非 python3.12
    """
    if sys.platform != "darwin":
        return

    # 1. Carbon / ApplicationServices: CPSSetProcessName (最关键：直接决定 Dock 悬停名与 WindowServer ASN 识别名)
    try:
        import ctypes
        from ctypes import Structure, c_uint32, c_int32, byref, c_char_p

        class ProcessSerialNumber(Structure):
            _fields_ = [('highLongOfPSN', c_uint32), ('lowLongOfPSN', c_uint32)]

        app_services = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        psn = ProcessSerialNumber()
        if app_services.GetCurrentProcess(byref(psn)) == 0:
            app_services.CPSSetProcessName.restype = c_int32
            app_services.CPSSetProcessName.argtypes = [ctypes.POINTER(ProcessSerialNumber), c_char_p]
            app_services.CPSSetProcessName(byref(psn), display_name.encode('utf-8'))
    except Exception:
        pass

    # 2. Cocoa: NSProcessInfo processName & NSBundle infoDictionary (影响菜单栏首项与 Cocoa 原生反射)
    try:
        import ctypes
        from ctypes import c_void_p, c_char_p

        objc = ctypes.cdll.LoadLibrary('/usr/lib/libobjc.A.dylib')
        objc.objc_getClass.restype = c_void_p
        objc.objc_getClass.argtypes = [c_char_p]
        objc.sel_registerName.restype = c_void_p
        objc.sel_registerName.argtypes = [c_char_p]

        def _msg(target, sel_str, *args, argtypes=None):
            sel = objc.sel_registerName(sel_str.encode('utf-8'))
            if argtypes is None:
                argtypes = [c_void_p, c_void_p] + [c_void_p] * len(args)
            objc.objc_msgSend.restype = c_void_p
            objc.objc_msgSend.argtypes = argtypes
            return objc.objc_msgSend(target, sel, *args)

        NSString = objc.objc_getClass(b'NSString')
        ns_disp = _msg(NSString, 'stringWithUTF8String:', display_name.encode('utf-8'), argtypes=[c_void_p, c_void_p, c_char_p])
        ns_name = _msg(NSString, 'stringWithUTF8String:', app_name.encode('utf-8'), argtypes=[c_void_p, c_void_p, c_char_p])

        # NSProcessInfo
        NSProcessInfo = objc.objc_getClass(b'NSProcessInfo')
        pinfo = _msg(NSProcessInfo, 'processInfo')
        _msg(pinfo, 'setProcessName:', ns_name)

        # NSBundle mainBundle infoDictionary
        NSBundle = objc.objc_getClass(b'NSBundle')
        bundle = _msg(NSBundle, 'mainBundle')
        info = _msg(bundle, 'infoDictionary')
        if info:
            k_name = _msg(NSString, 'stringWithUTF8String:', b'CFBundleName', argtypes=[c_void_p, c_void_p, c_char_p])
            k_disp = _msg(NSString, 'stringWithUTF8String:', b'CFBundleDisplayName', argtypes=[c_void_p, c_void_p, c_char_p])
            _msg(info, 'setObject:forKey:', ns_name, k_name)
            _msg(info, 'setObject:forKey:', ns_disp, k_disp)
    except Exception:
        pass
